"""Pruebas unitarias del contacto rápido por WhatsApp (HU 3.2)."""
from urllib.parse import unquote

import pytest

from services import notificacion_service
from services.errores import ErrorNegocio


@pytest.fixture
def un_estudiante(datos_vacios):
    t = datos_vacios.tabla
    t("NIVEL").agregar({"id_nivel": 1, "nombre_nivel": "1M"})
    t("APODERADO").agregar({"rut_apoderado": "9-9", "nombre": "Ana", "apellido_apoderado": "Rojas",
                            "telefono": "912345678"})
    t("ESTUDIANTE").agregar({"rut_estudiante": "1-1", "nombre": "Luis", "apellido_paterno": "Soto",
                             "apellido_materno": "Paz", "rut_apoderado": "9-9", "id_nivel": 1, "id_especialidad": ""})
    return t


def test_enlace_whatsapp_usa_wa_me_y_mensaje_predefinido(un_estudiante):
    enlace = notificacion_service.enlace_whatsapp("1-1", "Profesor jefe 1M")
    assert enlace["url"].startswith("https://wa.me/56912345678?text=")
    texto = unquote(enlace["url"].split("text=")[1])
    assert "Ana" in texto and "Luis" in texto
    assert "riesgo" not in texto.lower()  # el mensaje no etiqueta al estudiante


def test_whatsapp_sin_telefono_responde_404(un_estudiante):
    un_estudiante("APODERADO").actualizar(lambda a: True, {"telefono": ""})
    with pytest.raises(ErrorNegocio) as error:
        notificacion_service.enlace_whatsapp("1-1", "x")
    assert error.value.codigo == 404
