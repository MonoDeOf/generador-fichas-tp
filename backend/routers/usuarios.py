from fastapi import APIRouter, Depends

from permisos import GESTIONAR_USUARIOS
from routers.dependencias import requiere
from schemas.modelos import UsuarioCambios, UsuarioNuevo
from services import usuario_service

router = APIRouter(prefix="/usuarios", tags=["Usuarios y acceso"])


@router.get("")
def listar(_: dict = Depends(requiere(GESTIONAR_USUARIOS))):
    return usuario_service.listar()


@router.post("", status_code=201)
def crear(datos: UsuarioNuevo, _: dict = Depends(requiere(GESTIONAR_USUARIOS))):
    return usuario_service.crear(datos.model_dump())


@router.put("/{id_usuario}")
def actualizar(id_usuario: int, datos: UsuarioCambios, admin: dict = Depends(requiere(GESTIONAR_USUARIOS))):
    return usuario_service.actualizar(id_usuario, datos.model_dump(), admin["id_usuario"])
