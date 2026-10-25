from fastapi import APIRouter, Depends

from permisos import CONFIGURAR_REGLAS
from routers.dependencias import requiere
from schemas.modelos import ReglasEntrada
from services import riesgo_service

router = APIRouter(prefix="/config/reglas", tags=["Identificación de riesgos"])


@router.get("")
def reglas_vigentes(_: dict = Depends(requiere(CONFIGURAR_REGLAS))):
    """HU 4.2, escenario 1: configuración vigente."""
    return riesgo_service.detalle_reglas()


@router.put("")
def guardar_reglas(datos: ReglasEntrada, usuario: dict = Depends(requiere(CONFIGURAR_REGLAS))):
    """RF14 / HU 4.2: valida y persiste; el riesgo se calcula al consultar."""
    resultado = riesgo_service.guardar_reglas(datos.model_dump(), usuario["id_usuario"])
    return {**resultado, "mensaje": "Configuración actualizada correctamente"}
