"""Dashboard institucional (RF02, HU 1.2)."""
from collections import defaultdict

from services import academico_service as acad
from services import riesgo_service

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
