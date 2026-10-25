from fastapi import APIRouter, Depends

from permisos import EDITAR_CONTACTO, VER_CONVIVENCIA, VER_ESTUDIANTES, VER_FICHA, VER_RIESGO
from routers.dependencias import requiere
from schemas.modelos import ApoderadoEntrada
from services import academico_service as acad
from services import estudiante_service, riesgo_service

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


@router.get("")
def listar_estudiantes(id_nivel: int | None = None, id_especialidad: int | None = None,
                       nivel_riesgo: str | None = None, busqueda: str | None = None,
                       usuario: dict = Depends(requiere(VER_ESTUDIANTES))):
    """RF04 / HU 1.4: lista con filtros por nivel, especialidad, riesgo y búsqueda por nombre o RUT."""
    return estudiante_service.listar(usuario, id_nivel, id_especialidad, nivel_riesgo, busqueda)


@router.get("/{rut}")
def ficha_estudiante(rut: str, usuario: dict = Depends(requiere(VER_FICHA))):
    """RF05 / HU 2.1: ficha integral."""
    return estudiante_service.ficha(usuario, rut)


@router.get("/{rut}/asistencia")
def historial_asistencia(rut: str, usuario: dict = Depends(requiere(VER_FICHA))):
    """RF07 / HU 2.3: historial de asistencias, inasistencias y atrasos."""
    estudiante_service.obtener_visible(usuario, rut)
    return acad.asistencia_de(rut)


@router.get("/{rut}/calificaciones")
def calificaciones(rut: str, usuario: dict = Depends(requiere(VER_FICHA))):
    estudiante_service.obtener_visible(usuario, rut)
    return acad.calificaciones_de(rut)


@router.get("/{rut}/anotaciones")
def anotaciones(rut: str, usuario: dict = Depends(requiere(VER_CONVIVENCIA))):
    """RF08 / HU 2.4: anotaciones en orden de registro."""
    estudiante_service.obtener_visible(usuario, rut)
    return acad.anotaciones_de(rut)


@router.get("/{rut}/riesgo")
def riesgo(rut: str, usuario: dict = Depends(requiere(VER_RIESGO))):
    """RF13 / RF15 / HU 4.3: nivel de riesgo y factores que lo provocan."""
    estudiante_service.obtener_visible(usuario, rut)
    return riesgo_service.evaluar(rut)


@router.put("/{rut}/apoderado")
def actualizar_apoderado(rut: str, datos: ApoderadoEntrada, usuario: dict = Depends(requiere(EDITAR_CONTACTO))):
    """RF06 / HU 2.2: modifica el contacto del apoderado titular."""
    apoderado = estudiante_service.actualizar_apoderado(usuario, rut, datos.model_dump())
    return {"apoderado": apoderado,
            "otros_estudiantes_afectados": estudiante_service.estudiantes_que_comparten_apoderado(rut)}
