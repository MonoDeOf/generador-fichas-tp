"""Estudiantes: lista con filtros (RF04), ficha integral (RF05) y contacto del apoderado (RF06)."""
import re

from database import tabla
from permisos import ROLES_CON_CURSO, VER_CONVIVENCIA, VER_RIESGO, tiene_permiso
from services import academico_service as acad
from services import riesgo_service
from services.errores import ErrorNegocio


def puede_ver_estudiante(usuario: dict, e: dict) -> bool:
    if usuario["rol"] in ROLES_CON_CURSO:
        return usuario.get("id_nivel") is not None and e["id_nivel"] == usuario["id_nivel"]
    return True


def obtener_visible(usuario: dict, rut: str) -> dict:
    e = acad.estudiante(rut)
    if not puede_ver_estudiante(usuario, e):
        raise ErrorNegocio(403, "No tiene acceso a estudiantes fuera de su curso")
    return e


def listar(usuario: dict, id_nivel: int | None, id_especialidad: int | None,
           nivel_riesgo: str | None, busqueda: str | None) -> list[dict]:
    ver_riesgo = tiene_permiso(usuario["rol"], VER_RIESGO)
    riesgos = riesgo_service.evaluar_todos() if ver_riesgo else {}
    texto = (busqueda or "").strip().lower()
    filas = []
    for e in acad.estudiantes():
        if not puede_ver_estudiante(usuario, e):
            continue
        if id_nivel and e["id_nivel"] != id_nivel:
            continue
        if id_especialidad and e["id_especialidad"] != id_especialidad:
            continue
        nombre = f"{e['nombre']} {e['apellido_paterno']} {e['apellido_materno']}"
        if texto and texto not in nombre.lower() and texto not in e["rut_estudiante"].lower():
            continue
        fila = {
            "rut_estudiante": e["rut_estudiante"], "nombre": e["nombre"],
            "apellido_paterno": e["apellido_paterno"], "apellido_materno": e["apellido_materno"],
            "id_nivel": e["id_nivel"], "nombre_nivel": e["nombre_nivel"],
            "id_especialidad": e["id_especialidad"], "nombre_especialidad": e["nombre_especialidad"],
        }
        if ver_riesgo:
            r = riesgos[e["rut_estudiante"]]
            if nivel_riesgo and r["nivel_riesgo"] != nivel_riesgo:
                continue
            fila["nivel_riesgo"] = r["nivel_riesgo"]
            fila["factores"] = r["factores"]
            fila["porcentaje_asistencia"] = r["indicadores"]["porcentaje_asistencia"]
        filas.append(fila)
    return sorted(filas, key=lambda f: (f["id_nivel"], f["apellido_paterno"], f["nombre"]))


def ficha(usuario: dict, rut: str) -> dict:
    e = obtener_visible(usuario, rut)
    apoderado = acad.apoderados().get(e["rut_apoderado"])
    calificaciones = acad.calificaciones_de(rut)
    resultado = {
        "estudiante": {k: e[k] for k in ("rut_estudiante", "nombre", "apellido_paterno", "apellido_materno",
                                         "id_nivel", "nombre_nivel", "id_especialidad", "nombre_especialidad")},
        "apoderado": apoderado,
        "electivos": acad.electivos_de(rut),
        "asistencia": acad.asistencia_de(rut)["resumen"],
        "promedios": [{"id_asignatura": c["id_asignatura"], "nombre_asignatura": c["nombre_asignatura"],
                       "promedio_s1": c["semestres"][0]["promedio"], "promedio_s2": c["semestres"][1]["promedio"]}
                      for c in calificaciones],
    }
    if tiene_permiso(usuario["rol"], VER_CONVIVENCIA):
        anotaciones = acad.anotaciones_de(rut)
        resultado["resumen_convivencia"] = {t: sum(1 for a in anotaciones if a["tipo_anotacion"] == t)
                                            for t in ("Negativa", "Neutra", "Positiva")}
    if tiene_permiso(usuario["rol"], VER_RIESGO):
        resultado["riesgo"] = riesgo_service.evaluar(rut)
    return resultado


TELEFONO = re.compile(r"^\d{9}$")


def actualizar_apoderado(usuario: dict, rut: str, datos: dict) -> dict:
    """Modifica nombre, apellido y teléfono del apoderado titular (HU 2.2, RNF-13: 9 dígitos)."""
    e = obtener_visible(usuario, rut)
    if not TELEFONO.match(datos["telefono"]):
        raise ErrorNegocio(400, "El teléfono debe tener exactamente 9 dígitos numéricos")
    cambios = {"nombre": datos["nombre"].strip(), "apellido_apoderado": datos["apellido_apoderado"].strip(),
               "telefono": datos["telefono"]}
    if not cambios["nombre"] or not cambios["apellido_apoderado"]:
        raise ErrorNegocio(400, "El nombre y el apellido del apoderado son obligatorios")
    n = tabla("APODERADO").actualizar(lambda a: a["rut_apoderado"] == e["rut_apoderado"], cambios)
    if not n:
        raise ErrorNegocio(404, "Apoderado no encontrado")
    return acad.apoderados()[e["rut_apoderado"]]


def estudiantes_que_comparten_apoderado(rut: str) -> list[str]:
    e = acad.estudiante(rut)
    return [x["rut_estudiante"] for x in acad.estudiantes()
            if x["rut_apoderado"] == e["rut_apoderado"] and x["rut_estudiante"] != rut]
