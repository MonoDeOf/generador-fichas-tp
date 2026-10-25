from fastapi import APIRouter, Depends

from permisos import GENERAR_REPORTES, VER_DASHBOARD, VER_REPORTES
from routers.dependencias import requiere
from services import reporte_service

router = APIRouter(tags=["Visualización y reportes"])


@router.get("/dashboard")
def dashboard(_: dict = Depends(requiere(VER_DASHBOARD))):
    """RF02 / HU 1.2: indicadores generales del establecimiento."""
    return reporte_service.dashboard()


@router.get("/reportes/semanales")
def reportes_semanales(usuario: dict = Depends(requiere(VER_REPORTES))):
    """RF03 / HU 1.3: el profesor jefe ve sus reportes; dirección ve todos."""
    return reporte_service.reportes_de(usuario, todos=usuario["rol"] != "profesor_jefe")


@router.post("/reportes/semanales/generar")
def generar_reporte(_: dict = Depends(requiere(GENERAR_REPORTES))):
    """Ejecución manual de la tarea programada (administrador)."""
    return reporte_service.generar_reporte_semanal()
