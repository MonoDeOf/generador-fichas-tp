"""Gestión de usuarios y roles por el administrador (Hito 1: gestión de usuarios y permisos)."""
import re

from database import tabla
from permisos import ROLES, ROLES_CON_CURSO
from services.auth_service import hash_contrasena, usuario_publico
from services.errores import ErrorNegocio

NOMBRE_USUARIO = re.compile(r"^[a-z0-9._-]{3,30}$")
CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def listar() -> list[dict]:
    return [usuario_publico(u) for u in tabla("USUARIO").todos()]


def _validar(datos: dict) -> None:
    if datos["rol"] not in ROLES:
        raise ErrorNegocio(400, "Rol no válido")
    if datos["rol"] in ROLES_CON_CURSO and not datos.get("id_nivel"):
        raise ErrorNegocio(400, "El profesor jefe debe tener un curso (nivel) asignado")
    if datos.get("id_nivel") and str(datos["id_nivel"]) not in {n["id_nivel"] for n in tabla("NIVEL").todos()}:
        raise ErrorNegocio(400, "Nivel no válido")
    if datos.get("correo") and not CORREO.match(datos["correo"]):
        raise ErrorNegocio(400, "Correo electrónico no válido")


def crear(datos: dict) -> dict:
    nombre_usuario = datos["nombre_usuario"].strip().lower()
    if not NOMBRE_USUARIO.match(nombre_usuario):
        raise ErrorNegocio(400, "El nombre de usuario debe tener entre 3 y 30 caracteres (letras, números, . _ -)")
    _validar(datos)
    t = tabla("USUARIO")
    if any(u["nombre_usuario"] == nombre_usuario for u in t.todos()):
        raise ErrorNegocio(409, "Ya existe un usuario con ese nombre de usuario")
    fila = t.agregar({"id_usuario": t.siguiente_id("id_usuario"), "nombre_usuario": nombre_usuario,
                      "nombre": datos["nombre"].strip(), "rol": datos["rol"],
                      "id_nivel": datos.get("id_nivel") if datos["rol"] in ROLES_CON_CURSO else "",
                      "correo": datos.get("correo") or "", "contrasena_hash": hash_contrasena(datos["contrasena"]),
                      "activo": "1"})
    return usuario_publico(fila)


def actualizar(id_usuario: int, datos: dict, id_admin: int) -> dict:
    _validar(datos)
    if id_usuario == id_admin and (datos["rol"] != "administrador" or not datos["activo"]):
        raise ErrorNegocio(409, "No puede quitarse a sí mismo el rol de administrador ni desactivarse")
    cambios = {"nombre": datos["nombre"].strip(), "rol": datos["rol"],
               "id_nivel": datos.get("id_nivel") if datos["rol"] in ROLES_CON_CURSO else "",
               "correo": datos.get("correo") or "", "activo": "1" if datos["activo"] else "0"}
    if datos.get("contrasena"):
        cambios["contrasena_hash"] = hash_contrasena(datos["contrasena"])
    if not tabla("USUARIO").actualizar(lambda u: u["id_usuario"] == str(id_usuario), cambios):
        raise ErrorNegocio(404, "Usuario no encontrado")
    return usuario_publico(next(u for u in tabla("USUARIO").todos() if u["id_usuario"] == str(id_usuario)))
