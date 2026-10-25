from fastapi import APIRouter, Depends

from permisos import VER_DASHBOARD
from routers.dependencias import requiere
from services import reporte_service

router = APIRouter(tags=["Visualización y reportes"])


@router.get("/dashboard")
def dashboard(_: dict = Depends(requiere(VER_DASHBOARD))):
    """RF02 / HU 1.2: indicadores generales del establecimiento."""
    return reporte_service.dashboard()
