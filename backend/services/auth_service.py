"""Autenticación: contraseñas con PBKDF2 y tokens firmados con HMAC (biblioteca estándar)."""
import base64
import hashlib
import hmac
import json
import secrets
import time

from config import SECRET_KEY, TOKEN_HORAS_VALIDEZ
from database import tabla
from services.errores import ErrorNegocio

ITERACIONES = 200_000


def hash_contrasena(contrasena: str) -> str:
    sal = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), ITERACIONES)
    return f"pbkdf2_sha256${ITERACIONES}${sal}${digest.hex()}"


def verificar_contrasena(contrasena: str, almacenado: str) -> bool:
    try:
        _, iteraciones, sal, esperado = almacenado.split("$")
    except ValueError:
        return False
    digest = hashlib.pbkdf2_hmac("sha256", contrasena.encode(), bytes.fromhex(sal), int(iteraciones))
    return hmac.compare_digest(digest.hex(), esperado)


def _b64(datos: bytes) -> str:
    return base64.urlsafe_b64encode(datos).decode().rstrip("=")


def _desde_b64(texto: str) -> bytes:
    return base64.urlsafe_b64decode(texto + "=" * (-len(texto) % 4))


def crear_token(id_usuario: str) -> str:
    carga = _b64(json.dumps({"sub": id_usuario, "exp": int(time.time()) + TOKEN_HORAS_VALIDEZ * 3600}).encode())
    firma = _b64(hmac.new(SECRET_KEY.encode(), carga.encode(), hashlib.sha256).digest())
    return f"{carga}.{firma}"


def leer_token(token: str) -> str | None:
    """Devuelve el id de usuario si el token es válido y no expiró."""
    try:
        carga, firma = token.split(".")
        esperada = _b64(hmac.new(SECRET_KEY.encode(), carga.encode(), hashlib.sha256).digest())
        if not hmac.compare_digest(firma, esperada):
            return None
        datos = json.loads(_desde_b64(carga))
        if datos["exp"] < time.time():
            return None
        return str(datos["sub"])
    except (ValueError, KeyError, json.JSONDecodeError):
        return None


def usuario_publico(u: dict) -> dict:
    from permisos import ROLES, permisos_de
    return {
        "id_usuario": int(u["id_usuario"]),
        "nombre_usuario": u["nombre_usuario"],
        "nombre": u["nombre"],
        "rol": u["rol"],
        "nombre_rol": ROLES.get(u["rol"], u["rol"]),
        "id_nivel": int(u["id_nivel"]) if u.get("id_nivel") else None,
        "correo": u.get("correo") or None,
        "activo": u.get("activo") == "1",
        "permisos": permisos_de(u["rol"]),
    }


def buscar_usuario(id_usuario: str) -> dict | None:
    return next((u for u in tabla("USUARIO").todos() if u["id_usuario"] == str(id_usuario)), None)


def iniciar_sesion(nombre_usuario: str, contrasena: str) -> dict:
    usuario = next((u for u in tabla("USUARIO").todos()
                    if u["nombre_usuario"].lower() == nombre_usuario.strip().lower()), None)
    if not usuario or not verificar_contrasena(contrasena, usuario["contrasena_hash"]):
        raise ErrorNegocio(401, "Usuario o contraseña incorrectos")
    if usuario["activo"] != "1":
        raise ErrorNegocio(403, "El usuario está desactivado")
    return {"token": crear_token(usuario["id_usuario"]), "usuario": usuario_publico(usuario)}


CONTRASENA_DEMO = "demo1234"


def crear_usuarios_iniciales() -> None:
    """Crea una cuenta de demostración por rol si la tabla USUARIO está vacía.

    El material no entrega usuarios reales; estas cuentas permiten probar cada perfil
    y deben reemplazarse por los usuarios reales del establecimiento.
    """
    t = tabla("USUARIO")
    if t.todos():
        return
    from permisos import ROLES
    cuentas = []
    for rol, nombre in ROLES.items():
        if rol == "profesor_jefe":
            for id_nivel, nivel in [(1, "1M"), (2, "2M"), (3, "3M"), (4, "4M")]:
                cuentas.append((f"profejefe{nivel.lower()}", f"Profesor jefe {nivel}", rol, id_nivel))
        else:
            cuentas.append((rol.replace("_", ""), nombre, rol, ""))
    for i, (usuario, nombre, rol, id_nivel) in enumerate(cuentas, start=1):
        t.agregar({"id_usuario": i, "nombre_usuario": usuario, "nombre": nombre, "rol": rol,
                   "id_nivel": id_nivel, "correo": "", "contrasena_hash": hash_contrasena(CONTRASENA_DEMO),
                   "activo": "1"})
