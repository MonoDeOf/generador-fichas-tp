from fastapi import APIRouter, Depends

from routers.dependencias import usuario_actual
from services import notificacion_service

router = APIRouter(prefix="/notificaciones", tags=["Alertas y comunicaciones"])


@router.get("")
def listar(solo_no_leidas: bool = False, usuario: dict = Depends(usuario_actual)):
    return notificacion_service.listar(usuario["id_usuario"], solo_no_leidas)


@router.get("/no-leidas")
def cantidad_no_leidas(usuario: dict = Depends(usuario_actual)):
    """Consultado periódicamente por el frontend (polling, RNF-10) para la campana."""
    return {"cantidad": notificacion_service.cantidad_no_leidas(usuario["id_usuario"])}


@router.patch("/{id_notificacion}/leida")
def marcar_leida(id_notificacion: int, usuario: dict = Depends(usuario_actual)):
    notificacion_service.marcar_leida(id_notificacion, usuario["id_usuario"])
    return {"mensaje": "Notificación marcada como leída"}


@router.patch("/leidas")
def marcar_todas(usuario: dict = Depends(usuario_actual)):
    return {"marcadas": notificacion_service.marcar_todas_leidas(usuario["id_usuario"])}
