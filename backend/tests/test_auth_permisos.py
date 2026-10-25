"""Pruebas unitarias de autenticación (contraseñas y tokens) y de la matriz de permisos."""
import time

import pytest

import permisos
from services import auth_service


def test_hash_y_verificacion_de_contrasena():
    almacenado = auth_service.hash_contrasena("demo1234")
    assert almacenado.startswith("pbkdf2_sha256$")
    assert "demo1234" not in almacenado
    assert auth_service.verificar_contrasena("demo1234", almacenado)
    assert not auth_service.verificar_contrasena("otra", almacenado)


def test_mismo_texto_genera_hash_distinto_por_la_sal():
    assert auth_service.hash_contrasena("x") != auth_service.hash_contrasena("x")


def test_hash_con_formato_invalido_no_se_acepta():
    assert auth_service.verificar_contrasena("demo1234", "texto-sin-formato") is False


def test_token_valido_devuelve_el_usuario():
    assert auth_service.leer_token(auth_service.crear_token("7")) == "7"


def test_token_alterado_es_rechazado():
    carga, firma = auth_service.crear_token("7").split(".")
    assert auth_service.leer_token(f"{carga}.x{firma[1:]}") is None
    assert auth_service.leer_token("basura") is None


def test_token_expirado_es_rechazado(monkeypatch):
    token = auth_service.crear_token("7")
    monkeypatch.setattr(time, "time", lambda: 10**12)
    assert auth_service.leer_token(token) is None


@pytest.mark.parametrize("rol, permiso, esperado", [
    ("administrador", permisos.CONFIGURAR_REGLAS, True),
    ("director", permisos.CONFIGURAR_REGLAS, False),
    ("profesor", permisos.VER_RIESGO, False),        # RNF07
    ("inspector", permisos.EDITAR_CONTACTO, True),   # HU 2.2
    ("profesor_jefe", permisos.DERIVAR_CASOS, True), # HU 3.4
    ("encargado_convivencia", permisos.RECIBIR_ALERTAS, True),  # HU 4.4
    ("rol_inexistente", permisos.VER_FICHA, False),
])
def test_matriz_de_permisos(rol, permiso, esperado):
    assert permisos.tiene_permiso(rol, permiso) is esperado
