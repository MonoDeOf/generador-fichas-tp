"""Información académica: estudiantes, asistencia, calificaciones y convivencia.

Lee las tablas originales de BD_organizada sin alterar sus campos.
"""
from collections import defaultdict
from datetime import date

from database import tabla
from services.errores import ErrorNegocio


def niveles() -> dict[str, str]:
    return {n["id_nivel"]: n["nombre_nivel"] for n in tabla("NIVEL").todos()}


def especialidades() -> dict[str, str]:
    return {e["id_especialidad"]: e["nombre_especialidad"] for e in tabla("ESPECIALIDAD").todos()}


def asignaturas() -> dict[str, dict]:
    return {a["id_asignatura"]: a for a in tabla("ASIGNATURA").todos()}


def apoderados() -> dict[str, dict]:
    return {a["rut_apoderado"]: a for a in tabla("APODERADO").todos()}


def estudiantes() -> list[dict]:
    """Estudiantes con el nombre de su nivel y especialidad."""
    nv, esp = niveles(), especialidades()
    filas = []
    for e in tabla("ESTUDIANTE").todos():
        filas.append({
            **e,
            "id_nivel": int(e["id_nivel"]),
            "id_especialidad": int(e["id_especialidad"]) if e["id_especialidad"] else None,
            "nombre_nivel": nv.get(e["id_nivel"]),
            "nombre_especialidad": esp.get(e["id_especialidad"]) if e["id_especialidad"] else None,
        })
    return filas


def estudiante(rut: str) -> dict:
    e = next((e for e in estudiantes() if e["rut_estudiante"] == rut), None)
    if not e:
        raise ErrorNegocio(404, "Estudiante no encontrado")
    return e


def cantidad_notas(horas: int) -> int:
    """R7: 2–3 h → 3 notas, 4 h → 4, 6 h → 6, 8 h → 6 (mínimo 3, máximo 6)."""
    return max(3, min(6, horas))


def asignaturas_permitidas(e: dict, plan_comun=None, elige=None, modulos=None) -> set[str]:
    """R5: plan común de su nivel, electivos elegidos y módulos de su especialidad en su nivel.

    Las filas pueden entregarse (por ejemplo, durante una importación aún no guardada).
    """
    nivel = str(e["id_nivel"])
    especialidad = str(e["id_especialidad"] or "")
    plan_comun = tabla("PLAN_COMUN").todos() if plan_comun is None else plan_comun
    elige = tabla("ELIGE").todos() if elige is None else elige
    modulos = tabla("MODULO").todos() if modulos is None else modulos
    permitidas = {p["id_asignatura"] for p in plan_comun if p["id_nivel"] == nivel}
    permitidas |= {x["id_asignatura"] for x in elige if x["rut_estudiante"] == e["rut_estudiante"]}
    permitidas |= {m["id_asignatura"] for m in modulos
                   if m["id_nivel"] == nivel and m["id_especialidad"] == especialidad}
    return permitidas


def asistencia_por_estudiante() -> dict[str, list[dict]]:
    por_rut = defaultdict(list)
    for a in tabla("ASISTENCIA").todos():
        por_rut[a["rut_estudiante"]].append(a)
    for registros in por_rut.values():
        registros.sort(key=lambda a: a["fecha"])
    return por_rut


def resumen_asistencia(registros: list[dict]) -> dict:
    """El atraso se cuenta como día asistido (el estudiante llegó al establecimiento)."""
    total = len(registros)
    ausentes = sum(1 for a in registros if a["estado"] == "ausente")
    atrasos = sum(1 for a in registros if a["estado"] == "atraso")
    presentes = total - ausentes - atrasos
    return {
        "total_dias": total,
        "presentes": presentes,
        "ausentes": ausentes,
        "atrasos": atrasos,
        "porcentaje_asistencia": round(100 * (total - ausentes) / total, 1) if total else None,
    }


def rachas_ausencia(registros: list[dict]) -> list[dict]:
    """Secuencias de días registrados consecutivos con estado 'ausente'."""
    rachas, actual = [], []
    for a in registros:
        if a["estado"] == "ausente":
            actual.append(a["fecha"])
        else:
            if actual:
                rachas.append(actual)
            actual = []
    if actual:
        rachas.append(actual)
    return [{"inicio": r[0], "fin": r[-1], "dias": len(r)} for r in rachas]


def asistencia_de(rut: str) -> dict:
    estudiante(rut)
    registros = asistencia_por_estudiante().get(rut, [])
    por_mes = defaultdict(list)
    for a in registros:
        por_mes[a["fecha"][:7]].append(a)
    return {
        "resumen": resumen_asistencia(registros),
        "por_mes": [{"mes": m, **resumen_asistencia(r)} for m, r in sorted(por_mes.items())],
        "registros": [{"id_asistencia": int(a["id_asistencia"]), "fecha": a["fecha"], "estado": a["estado"],
                       "dia_semana": date.fromisoformat(a["fecha"]).weekday()} for a in registros],
        "rachas_ausencia": [r for r in rachas_ausencia(registros) if r["dias"] > 1],
    }


def calificaciones_por_estudiante() -> dict[str, list[dict]]:
    por_rut = defaultdict(list)
    for c in tabla("CALIFICACION").todos():
        por_rut[c["rut_estudiante"]].append(c)
    return por_rut


def calificaciones_de(rut: str) -> list[dict]:
    """Calificaciones agrupadas por asignatura y semestre, con su promedio."""
    estudiante(rut)
    asg = asignaturas()
    grupos = defaultdict(lambda: {1: [], 2: []})
    for c in calificaciones_por_estudiante().get(rut, []):
        grupos[c["id_asignatura"]][int(c["semestre"])].append(
            {"numero_evaluacion": int(c["numero_evaluacion"]), "nota": float(c["nota"])})
    resultado = []
    for id_asig, semestres in grupos.items():
        a = asg.get(id_asig, {})
        fila = {"id_asignatura": id_asig, "nombre_asignatura": a.get("nombre_asignatura", id_asig),
                "horas": int(a.get("horas", 0) or 0), "semestres": []}
        for s in (1, 2):
            notas = sorted(semestres[s], key=lambda n: n["numero_evaluacion"])
            fila["semestres"].append({
                "semestre": s, "notas": notas,
                "promedio": round(sum(n["nota"] for n in notas) / len(notas), 1) if notas else None,
            })
        resultado.append(fila)
    return sorted(resultado, key=lambda f: f["nombre_asignatura"])


def anotaciones_por_estudiante() -> dict[str, list[dict]]:
    en_aula = {x["id_anotacion"]: x["id_asignatura"] for x in tabla("ANOTACION_AULA").todos()}
    asg = asignaturas()
    por_rut = defaultdict(list)
    for a in tabla("ANOTACION").todos():
        id_asig = en_aula.get(a["id_anotacion"])
        por_rut[a["rut_estudiante"]].append({
            "id_anotacion": int(a["id_anotacion"]),
            "descripcion_anotacion": a["descripcion_anotacion"],
            "tipo_anotacion": a["tipo_anotacion"],
            "ambito": "En aula" if id_asig else "Fuera de aula",
            "id_asignatura": id_asig,
            "nombre_asignatura": asg.get(id_asig, {}).get("nombre_asignatura") if id_asig else None,
        })
    return por_rut


def anotaciones_de(rut: str) -> list[dict]:
    """ANOTACION no tiene fecha; el orden cronológico se aproxima por id_anotacion (orden de registro)."""
    estudiante(rut)
    return sorted(anotaciones_por_estudiante().get(rut, []), key=lambda a: a["id_anotacion"])


def electivos_de(rut: str) -> list[dict]:
    asg = asignaturas()
    combo_por_asig = {e["id_asignatura"]: e["id_combo"] for e in tabla("ELECTIVO").todos()}
    numero_combo = {c["id_combo"]: int(c["numero_combo"]) for c in tabla("COMBO").todos()}
    return [{"id_asignatura": x["id_asignatura"],
             "nombre_asignatura": asg.get(x["id_asignatura"], {}).get("nombre_asignatura"),
             "numero_combo": numero_combo.get(combo_por_asig.get(x["id_asignatura"]))}
            for x in tabla("ELIGE").todos() if x["rut_estudiante"] == rut]
