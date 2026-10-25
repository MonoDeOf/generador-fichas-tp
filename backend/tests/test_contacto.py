"""Pruebas unitarias de contacto con el apoderado: HU 2.2 (teléfono de 9 dígitos)."""
import pytest

from services import estudiante_service
from services.errores import ErrorNegocio

DIRECTOR = {"id_usuario": 2, "rol": "director", "id_nivel": None}


@pytest.fixture
def un_estudiante(datos_vacios):
    t = datos_vacios.tabla
    t("NIVEL").agregar({"id_nivel": 1, "nombre_nivel": "1M"})
    t("APODERADO").agregar({"rut_apoderado": "9-9", "nombre": "Ana", "apellido_apoderado": "Rojas",
                            "telefono": "912345678"})
    t("ESTUDIANTE").agregar({"rut_estudiante": "1-1", "nombre": "Luis", "apellido_paterno": "Soto",
                             "apellido_materno": "Paz", "rut_apoderado": "9-9", "id_nivel": 1, "id_especialidad": ""})
    return t


def cambio(telefono):
    return {"nombre": "Ana", "apellido_apoderado": "Rojas", "telefono": telefono}


def test_actualiza_telefono_valido(un_estudiante):
    estudiante_service.actualizar_apoderado(DIRECTOR, "1-1", cambio("987654321"))
    assert un_estudiante("APODERADO").todos()[0]["telefono"] == "987654321"


@pytest.mark.parametrize("telefono", ["98765432", "9876543210", "98765432a", "",
                                      "٩٨٧٦٥٤٣٢١",  # dígitos arábigo-índicos (Unicode)
                                      "987654321\n"])
def test_rechaza_telefono_invalido_y_no_guarda(un_estudiante, telefono):
    with pytest.raises(ErrorNegocio) as error:
        estudiante_service.actualizar_apoderado(DIRECTOR, "1-1", cambio(telefono))
    assert error.value.codigo == 400
    assert un_estudiante("APODERADO").todos()[0]["telefono"] == "912345678"


def test_nombre_vacio_es_rechazado(un_estudiante):
    with pytest.raises(ErrorNegocio):
        estudiante_service.actualizar_apoderado(DIRECTOR, "1-1", {**cambio("987654321"), "nombre": "  "})
