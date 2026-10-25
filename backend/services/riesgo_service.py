"""Identificación de riesgo (RF13, RF14, RF15).

Reglas configurables (HU 4.2):
- umbral_asistencia: porcentaje mínimo de asistencia (R13: 85 %).
- nota_deficiente: una nota bajo este valor se considera deficiente ("nota roja").
- min_notas_deficientes: cantidad mínima de notas deficientes que activa el factor.
- operador: cómo se combinan asistencia y notas en la regla crítica ("Y" / "O").
- ausencias_consecutivas: días seguidos ausente que constituyen un quiebre crítico (HU 4.4).
- min_anotaciones_negativas: anotaciones negativas que activan el factor de convivencia (0 = desactivado).

Clasificación (semáforo, HU 4.1):
- Rojo: se cumple la regla combinada, hay un quiebre crítico de asistencia o hay 2 o más factores.
- Amarillo: hay exactamente un factor.
- Verde: no hay factores.
"""
from datetime import datetime

from database import tabla
from services import academico_service as acad
from services.errores import ErrorNegocio

REGLAS_POR_DEFECTO = {
    "umbral_asistencia": "85",
    "nota_deficiente": "4.0",
    "min_notas_deficientes": "1",
    "operador": "Y",
    "ausencias_consecutivas": "3",
    "min_anotaciones_negativas": "0",
}

DESCRIPCION_REGLAS = {
    "umbral_asistencia": "Porcentaje mínimo de asistencia (%)",
    "nota_deficiente": "Nota bajo la cual una calificación es deficiente",
    "min_notas_deficientes": "Cantidad mínima de calificaciones deficientes",
    "operador": "Operador lógico entre asistencia y calificaciones",
    "ausencias_consecutivas": "Ausencias consecutivas que generan alerta crítica",
    "min_anotaciones_negativas": "Anotaciones negativas que activan el factor (0 = desactivado)",
}

def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def inicializar_reglas() -> None:
    t = tabla("REGLA_RIESGO")
    existentes = {r["parametro"] for r in t.todos()}
    for parametro, valor in REGLAS_POR_DEFECTO.items():
        if parametro not in existentes:
            t.agregar({"parametro": parametro, "valor": valor, "fecha_actualizacion": _ahora(), "id_usuario": ""})


def obtener_reglas() -> dict:
    filas = {r["parametro"]: r for r in tabla("REGLA_RIESGO").todos()}
    valores = {p: filas.get(p, {}).get("valor", v) for p, v in REGLAS_POR_DEFECTO.items()}
    return {
        "umbral_asistencia": float(valores["umbral_asistencia"]),
        "nota_deficiente": float(valores["nota_deficiente"]),
        "min_notas_deficientes": int(valores["min_notas_deficientes"]),
        "operador": valores["operador"],
        "ausencias_consecutivas": int(valores["ausencias_consecutivas"]),
        "min_anotaciones_negativas": int(valores["min_anotaciones_negativas"]),
    }


def detalle_reglas() -> dict:
    filas = {r["parametro"]: r for r in tabla("REGLA_RIESGO").todos()}
    return {
        "reglas": obtener_reglas(),
        "descripciones": DESCRIPCION_REGLAS,
        "ultima_actualizacion": max((f["fecha_actualizacion"] for f in filas.values()), default=None),
    }


def guardar_reglas(nuevas: dict, id_usuario: int) -> dict:
    """Valida y persiste las reglas. Si algo es inválido no se guarda nada (HU 4.2, escenarios 4 y 5)."""
    errores = []
    if not 0 <= nuevas["umbral_asistencia"] <= 100:
        errores.append("El porcentaje de asistencia debe encontrarse entre 0 y 100")
    if not 1.0 <= nuevas["nota_deficiente"] <= 7.0:
        errores.append("La nota deficiente debe encontrarse entre 1.0 y 7.0")
    if nuevas["min_notas_deficientes"] < 1:
        errores.append("La cantidad mínima de calificaciones deficientes debe ser al menos 1")
    if nuevas["operador"] not in ("Y", "O"):
        errores.append("El operador lógico debe ser 'Y' u 'O'")
    if nuevas["ausencias_consecutivas"] < 1:
        errores.append("Las ausencias consecutivas deben ser al menos 1")
    if nuevas["min_anotaciones_negativas"] < 0:
        errores.append("Las anotaciones negativas no pueden ser negativas")
    if errores:
        raise ErrorNegocio(400, "La configuración no fue guardada", errores)
    fecha = _ahora()
    filas = [{"parametro": p, "valor": str(nuevas[p]), "fecha_actualizacion": fecha, "id_usuario": id_usuario}
             for p in REGLAS_POR_DEFECTO]
    tabla("REGLA_RIESGO").reemplazar_todo(filas)
    return detalle_reglas()


def _evaluar(e: dict, reglas: dict, asistencia: list, calificaciones: list, anotaciones: list, asg: dict) -> dict:
    factores = []
    resumen = acad.resumen_asistencia(asistencia)
    pct = resumen["porcentaje_asistencia"]
    f_asistencia = pct is not None and pct < reglas["umbral_asistencia"]
    if f_asistencia:
        factores.append({"tipo": "asistencia",
                         "descripcion": f"Asistencia de {pct}% bajo el umbral de {reglas['umbral_asistencia']:g}%"})

    deficientes = [c for c in calificaciones if float(c["nota"]) < reglas["nota_deficiente"]]
    f_notas = len(deficientes) >= reglas["min_notas_deficientes"]
    if f_notas:
        por_asig = {}
        for c in deficientes:
            nombre = asg.get(c["id_asignatura"], {}).get("nombre_asignatura", c["id_asignatura"])
            por_asig[nombre] = por_asig.get(nombre, 0) + 1
        detalle = ", ".join(f"{n} ({k})" for n, k in sorted(por_asig.items(), key=lambda x: -x[1]))
        factores.append({"tipo": "calificaciones",
                         "descripcion": f"{len(deficientes)} calificaciones bajo {reglas['nota_deficiente']:g}: {detalle}"})

    rachas = [r for r in acad.rachas_ausencia(asistencia) if r["dias"] >= reglas["ausencias_consecutivas"]]
    if rachas:
        mayor = max(rachas, key=lambda r: r["dias"])
        factores.append({"tipo": "ausencias_consecutivas", "critico": True,
                         "descripcion": f"{mayor['dias']} ausencias consecutivas ({mayor['inicio']} a {mayor['fin']})"})

    negativas = sum(1 for a in anotaciones if a["tipo_anotacion"] == "Negativa")
    if reglas["min_anotaciones_negativas"] > 0 and negativas >= reglas["min_anotaciones_negativas"]:
        factores.append({"tipo": "convivencia", "descripcion": f"{negativas} anotaciones negativas"})

    combinada = (f_asistencia and f_notas) if reglas["operador"] == "Y" else (f_asistencia or f_notas)
    if combinada:
        conector = "y" if reglas["operador"] == "Y" else "o"
        factores.insert(0, {"tipo": "regla_combinada", "critico": True,
                            "descripcion": f"Cumple la regla combinada: asistencia bajo {reglas['umbral_asistencia']:g}% "
                                           f"{conector} {reglas['min_notas_deficientes']} o más calificaciones deficientes"})
    contables = [f for f in factores if f["tipo"] != "regla_combinada"]
    if combinada or rachas or len(contables) >= 2:
        nivel = "Rojo"
    elif contables:
        nivel = "Amarillo"
    else:
        nivel = "Verde"
    return {
        "rut_estudiante": e["rut_estudiante"],
        "nivel_riesgo": nivel,
        "factores": factores,
        "indicadores": {
            "porcentaje_asistencia": pct,
            "calificaciones_deficientes": len(deficientes),
            "anotaciones_negativas": negativas,
            "mayor_racha_ausencias": max((r["dias"] for r in acad.rachas_ausencia(asistencia)), default=0),
        },
        "rachas_criticas": rachas,
    }


def evaluar_todos() -> dict[str, dict]:
    reglas = obtener_reglas()
    asistencia = acad.asistencia_por_estudiante()
    calificaciones = acad.calificaciones_por_estudiante()
    anotaciones = acad.anotaciones_por_estudiante()
    asg = acad.asignaturas()
    return {e["rut_estudiante"]: _evaluar(e, reglas, asistencia.get(e["rut_estudiante"], []),
                                          calificaciones.get(e["rut_estudiante"], []),
                                          anotaciones.get(e["rut_estudiante"], []), asg)
            for e in acad.estudiantes()}


def evaluar(rut: str) -> dict:
    acad.estudiante(rut)
    return evaluar_todos()[rut]
