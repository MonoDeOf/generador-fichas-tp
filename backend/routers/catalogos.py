from fastapi import APIRouter, Depends

from permisos import ROLES
from routers.dependencias import usuario_actual
from services import academico_service as acad

router = APIRouter(prefix="/catalogos", tags=["Catálogos"])


@router.get("")
def catalogos(_: dict = Depends(usuario_actual)):
    return {
        "niveles": [{"id_nivel": int(k), "nombre_nivel": v} for k, v in acad.niveles().items()],
        "especialidades": [{"id_especialidad": int(k), "nombre_especialidad": v} for k, v in acad.especialidades().items()],
        "roles": [{"rol": k, "nombre": v} for k, v in ROLES.items()],
        "niveles_riesgo": ["Rojo", "Amarillo", "Verde"],
    }
