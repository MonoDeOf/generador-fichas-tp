"""Configuración común de las pruebas unitarias (pytest).

Las pruebas usan una carpeta de datos temporal para no tocar backend/data.
"""
import os
import sys
import tempfile
from pathlib import Path

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="datos_pytest_")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

import database  # noqa: E402


@pytest.fixture
def datos_vacios():
    """Deja todas las tablas vacías (solo encabezados) antes de cada prueba que la use."""
    database.inicializar()
    for nombre in [*database.TABLAS_BASE, *database.TABLAS_NUEVAS]:
        database.tabla(nombre).reemplazar_todo([])
    return database


def registro(fecha, estado):
    return {"fecha": fecha, "estado": estado}
