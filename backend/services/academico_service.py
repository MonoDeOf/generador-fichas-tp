"""Información académica: estudiantes, asistencia, calificaciones y convivencia.

Lee las tablas originales de BD_organizada sin alterar sus campos.
"""
from collections import defaultdict

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


def calificaciones_por_estudiante() -> dict[str, list[dict]]:
    por_rut = defaultdict(list)
    for c in tabla("CALIFICACION").todos():
        por_rut[c["rut_estudiante"]].append(c)
    return por_rut


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
