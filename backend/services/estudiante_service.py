"""Estudiantes: lista con filtros (RF04) y visibilidad por curso."""
from permisos import ROLES_CON_CURSO, VER_RIESGO, tiene_permiso
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
