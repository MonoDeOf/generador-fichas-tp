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

# Código de país usado para el enlace wa.me (los teléfonos del material tienen 9 dígitos).
CODIGO_PAIS_WHATSAPP = os.getenv("CODIGO_PAIS_WHATSAPP", "56")

# Servidor SMTP para el reporte semanal (HU 1.3). Si no se configura, el reporte
# se genera y se notifica dentro de la plataforma, pero no se envía por correo.
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USUARIO = os.getenv("SMTP_USUARIO", "")
SMTP_CONTRASENA = os.getenv("SMTP_CONTRASENA", "")
SMTP_REMITENTE = os.getenv("SMTP_REMITENTE", SMTP_USUARIO)

# Programación del reporte semanal: viernes (4) a las 14:00 (HU 1.3, escenario 1).
REPORTE_DIA_SEMANA = int(os.getenv("REPORTE_DIA_SEMANA", "4"))
REPORTE_HORA = int(os.getenv("REPORTE_HORA", "14"))
