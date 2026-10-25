from fastapi import APIRouter, Depends

from routers.dependencias import usuario_actual
from schemas.modelos import LoginEntrada
from services import auth_service

router = APIRouter(prefix="/auth", tags=["Usuarios y acceso"])


@router.post("/login")
def iniciar_sesion(datos: LoginEntrada):
    return auth_service.iniciar_sesion(datos.nombre_usuario, datos.contrasena)


@router.get("/me")
def sesion_actual(usuario: dict = Depends(usuario_actual)):
    return usuario
