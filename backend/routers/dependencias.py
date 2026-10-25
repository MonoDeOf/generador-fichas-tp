"""Dependencias de autenticación y autorización para las rutas."""
from fastapi import Depends, Header, HTTPException

from permisos import tiene_permiso
from services import auth_service


def usuario_actual(authorization: str = Header(default="")) -> dict:
    """RNF04: toda ruta con datos de estudiantes requiere un token Bearer válido."""
    token = authorization.removeprefix("Bearer ").strip()
    id_usuario = auth_service.leer_token(token) if token else None
    usuario = auth_service.buscar_usuario(id_usuario) if id_usuario else None
    if not usuario:
        raise HTTPException(status_code=401, detail="Sesión no válida o expirada")
    if usuario["activo"] != "1":
        raise HTTPException(status_code=403, detail="El usuario está desactivado")
    return auth_service.usuario_publico(usuario)


def requiere(permiso: str):
    """RNF05: restringe la ruta a los roles que tienen el permiso."""
    def verificar(usuario: dict = Depends(usuario_actual)) -> dict:
        if not tiene_permiso(usuario["rol"], permiso):
            raise HTTPException(status_code=403, detail="Su rol no tiene permiso para esta operación")
        return usuario
    return verificar
