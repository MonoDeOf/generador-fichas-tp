"""Configuración del backend leída desde variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Carpeta con los CSV que actúan como base de datos del proyecto.
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))

# Clave para firmar los tokens de sesión. Debe cambiarse fuera del entorno de desarrollo.
SECRET_KEY = os.getenv("SECRET_KEY", "cambiar-esta-clave-en-produccion")
TOKEN_HORAS_VALIDEZ = int(os.getenv("TOKEN_HORAS_VALIDEZ", "8"))

# Orígenes permitidos para el frontend (Vite usa el puerto 5173 por defecto).
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
