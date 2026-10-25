from fastapi import APIRouter, Depends

from permisos import VER_ESTUDIANTES, VER_RIESGO
from routers.dependencias import requiere
from services import estudiante_service, riesgo_service

router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


@router.get("")
def listar_estudiantes(id_nivel: int | None = None, id_especialidad: int | None = None,
                       nivel_riesgo: str | None = None, busqueda: str | None = None,
                       usuario: dict = Depends(requiere(VER_ESTUDIANTES))):
    """RF04 / HU 1.4: lista con filtros por nivel, especialidad, riesgo y búsqueda por nombre o RUT."""
    return estudiante_service.listar(usuario, id_nivel, id_especialidad, nivel_riesgo, busqueda)


@router.get("/{rut}/riesgo")
def riesgo(rut: str, usuario: dict = Depends(requiere(VER_RIESGO))):
    """RF13 / RF15 / HU 4.3: nivel de riesgo y factores que lo provocan."""
    estudiante_service.obtener_visible(usuario, rut)
    return riesgo_service.evaluar(rut)
