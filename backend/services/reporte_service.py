"""Dashboard institucional (RF02, HU 1.2) y reporte semanal para profesores jefes (RF03, HU 1.3)."""
import smtplib
from collections import defaultdict
from datetime import datetime
from email.message import EmailMessage

import config
from database import tabla
from services import academico_service as acad
from services import notificacion_service, riesgo_service

NIVELES_RIESGO = ["Rojo", "Amarillo", "Verde"]


def _tasas(registros: list[dict]) -> dict:
    r = acad.resumen_asistencia(registros)
    total = r["total_dias"] or 1
    return {"tasa_asistencia": r["porcentaje_asistencia"],
            "tasa_inasistencia": round(100 * r["ausentes"] / total, 1) if r["total_dias"] else None,
            "tasa_atraso": round(100 * r["atrasos"] / total, 1) if r["total_dias"] else None}


def dashboard() -> dict:
    """Indicadores agregados: no expone el riesgo individual de ningún estudiante (RNF07)."""
    estudiantes = acad.estudiantes()
    asistencia = acad.asistencia_por_estudiante()
    riesgos = riesgo_service.evaluar_todos()
    todos = [a for regs in asistencia.values() for a in regs]

    def agrupar(clave, nombre):
        grupos = defaultdict(list)
        for e in estudiantes:
            if e[clave] is not None:
                grupos[(e[clave], e[nombre])].append(e)
        filas = []
        for (id_grupo, etiqueta), miembros in sorted(grupos.items()):
            pcts = [riesgos[e["rut_estudiante"]]["indicadores"]["porcentaje_asistencia"] for e in miembros]
            pcts = [p for p in pcts if p is not None]
            registros = [a for e in miembros for a in asistencia.get(e["rut_estudiante"], [])]
            filas.append({"id": id_grupo, "nombre": etiqueta, "estudiantes": len(miembros),
                          "asistencia_promedio": round(sum(pcts) / len(pcts), 1) if pcts else None,
                          **_tasas(registros),
                          "riesgo": {n: sum(1 for e in miembros if riesgos[e["rut_estudiante"]]["nivel_riesgo"] == n)
                                     for n in NIVELES_RIESGO}})
        return filas

    por_mes = defaultdict(list)
    for a in todos:
        por_mes[a["fecha"][:7]].append(a)
    return {
        "total_estudiantes": len(estudiantes),
        **_tasas(todos),
        "periodo": {"desde": min((a["fecha"] for a in todos), default=None),
                    "hasta": max((a["fecha"] for a in todos), default=None)},
        "riesgo": {n: sum(1 for r in riesgos.values() if r["nivel_riesgo"] == n) for n in NIVELES_RIESGO},
        "por_nivel": agrupar("id_nivel", "nombre_nivel"),
        "por_especialidad": agrupar("id_especialidad", "nombre_especialidad"),
        "por_mes": [{"mes": m, **_tasas(r)} for m, r in sorted(por_mes.items())],
    }


def semana_actual(ahora: datetime | None = None) -> str:
    anio, semana, _ = (ahora or datetime.now()).isocalendar()
    return f"{anio}-S{semana:02d}"


def existe_reporte(semana: str) -> bool:
    return any(r["semana"] == semana for r in tabla("REPORTE_SEMANAL").todos())


def generar_reporte_semanal(semana: str | None = None) -> dict:
    """Genera el reporte de la semana para cada profesor jefe activo.

    Incluye a los estudiantes de su curso en riesgo Rojo o Amarillo y marca si
    ingresaron esta semana ("nuevo") o venían del reporte anterior ("permanece").
    Si el reporte de la semana ya existía, se reemplaza.
    """
    semana = semana or semana_actual()
    t = tabla("REPORTE_SEMANAL")
    filas = [r for r in t.todos() if r["semana"] != semana]
    riesgos = riesgo_service.evaluar_todos()
    estudiantes = acad.estudiantes()
    fecha = datetime.now().isoformat(timespec="seconds")
    siguiente = t.siguiente_id("id_reporte")
    resumen = []
    profesores = [u for u in tabla("USUARIO").todos() if u["rol"] == "profesor_jefe" and u["activo"] == "1" and u["id_nivel"]]
    for prof in profesores:
        anteriores = [r for r in filas if r["id_usuario_destino"] == prof["id_usuario"] and r["semana"] < semana]
        ultima = max((r["semana"] for r in anteriores), default=None)
        previos = {r["rut_estudiante"] for r in anteriores if r["semana"] == ultima}
        en_riesgo = [e for e in estudiantes if str(e["id_nivel"]) == prof["id_nivel"]
                     and riesgos[e["rut_estudiante"]]["nivel_riesgo"] != "Verde"]
        nuevas = []
        for e in en_riesgo:
            nuevas.append({"id_reporte": siguiente, "semana": semana, "fecha_generacion": fecha,
                           "id_usuario_destino": prof["id_usuario"], "rut_estudiante": e["rut_estudiante"],
                           "nivel_riesgo": riesgos[e["rut_estudiante"]]["nivel_riesgo"],
                           "condicion": "permanece" if e["rut_estudiante"] in previos else "nuevo",
                           "enviado_correo": "0"})
            siguiente += 1
        enviado = _enviar_correo(prof, semana, nuevas, estudiantes, riesgos)
        for f in nuevas:
            f["enviado_correo"] = "1" if enviado else "0"
        filas.extend({k: str(v) for k, v in f.items()} for f in nuevas)
        notificacion_service.crear(prof["id_usuario"], "", "reporte_semanal",
                                   f"Reporte semanal {semana}: {len(nuevas)} estudiantes de su curso requieren atención",
                                   f"reporte:{semana}:{fecha}")
        resumen.append({"id_usuario": int(prof["id_usuario"]), "profesor": prof["nombre"],
                        "estudiantes": len(nuevas), "enviado_correo": enviado})
    t.reemplazar_todo(filas)
    return {"semana": semana, "fecha_generacion": fecha, "destinatarios": resumen,
            "correo_configurado": bool(config.SMTP_HOST)}


def _enviar_correo(prof: dict, semana: str, filas: list[dict], estudiantes: list[dict], riesgos: dict) -> bool:
    """Envía el resumen por SMTP si hay servidor configurado y el profesor tiene correo."""
    if not config.SMTP_HOST or not prof.get("correo"):
        return False
    nombres = {e["rut_estudiante"]: f"{e['nombre']} {e['apellido_paterno']} {e['apellido_materno']}" for e in estudiantes}
    lineas = [f"- {nombres[f['rut_estudiante']]} ({f['nivel_riesgo']}, {f['condicion']}): "
              + "; ".join(x["descripcion"] for x in riesgos[f["rut_estudiante"]]["factores"]) for f in filas]
    mensaje = EmailMessage()
    mensaje["Subject"] = f"Reporte semanal de seguimiento {semana}"
    mensaje["From"] = config.SMTP_REMITENTE
    mensaje["To"] = prof["correo"]
    mensaje.set_content(f"Estimado/a {prof['nombre']}:\n\nEstudiantes de su curso que requieren atención:\n\n"
                        + ("\n".join(lineas) or "Sin estudiantes en riesgo esta semana.")
                        + "\n\nInformación confidencial de uso interno del establecimiento.")
    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT, timeout=20) as smtp:
            smtp.starttls()
            if config.SMTP_USUARIO:
                smtp.login(config.SMTP_USUARIO, config.SMTP_CONTRASENA)
            smtp.send_message(mensaje)
        return True
    except (OSError, smtplib.SMTPException):
        return False


def reportes_de(usuario: dict, todos: bool) -> list[dict]:
    """Reportes agrupados por semana; el profesor jefe solo ve los suyos."""
    estudiantes = {e["rut_estudiante"]: e for e in acad.estudiantes()}
    usuarios = {u["id_usuario"]: u for u in tabla("USUARIO").todos()}
    grupos = defaultdict(list)
    for r in tabla("REPORTE_SEMANAL").todos():
        if todos or r["id_usuario_destino"] == str(usuario["id_usuario"]):
            grupos[(r["semana"], r["id_usuario_destino"])].append(r)
    resultado = []
    for (semana, id_dest), filas in sorted(grupos.items(), reverse=True):
        resultado.append({
            "semana": semana, "fecha_generacion": filas[0]["fecha_generacion"],
            "profesor": usuarios.get(id_dest, {}).get("nombre"),
            "enviado_correo": all(f["enviado_correo"] == "1" for f in filas),
            "estudiantes": sorted([{
                "rut_estudiante": f["rut_estudiante"],
                "nombre": f"{estudiantes[f['rut_estudiante']]['nombre']} {estudiantes[f['rut_estudiante']]['apellido_paterno']}"
                if f["rut_estudiante"] in estudiantes else f["rut_estudiante"],
                "nivel_riesgo": f["nivel_riesgo"], "condicion": f["condicion"]} for f in filas],
                key=lambda x: (x["nivel_riesgo"] != "Rojo", x["condicion"] != "nuevo", x["nombre"])),
        })
    return resultado
