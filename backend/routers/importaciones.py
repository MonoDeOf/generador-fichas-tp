from fastapi import APIRouter, BackgroundTasks, Depends

from permisos import IMPORTAR_DATOS
from routers.dependencias import requiere
from schemas.modelos import ImportacionEntrada
from services import importacion_service, riesgo_service

router = APIRouter(prefix="/importaciones", tags=["Información académica"])


@router.get("/estado")
def estado_tablas(_: dict = Depends(requiere(IMPORTAR_DATOS))):
    """Registros cargados en cada tabla de la base de datos."""
    return importacion_service.estado_tablas()


@router.post("")
def importar(datos: ImportacionEntrada, tareas: BackgroundTasks, _: dict = Depends(requiere(IMPORTAR_DATOS))):
    """RF01 / HU 1.1: carga manual de uno o varios CSV. Valida todo el lote, sincroniza y recalcula el riesgo."""
    resultado = importacion_service.importar([a.model_dump() for a in datos.archivos])
    tareas.add_task(riesgo_service.recalcular_y_alertar)
    return {**resultado, "mensaje": "Archivos importados correctamente"}
