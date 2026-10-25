"""Pruebas unitarias de la validación de importaciones (HU 1.1)."""
import pytest

from services import importacion_service as imp


def test_lee_csv_con_bom_y_separador_punto_y_coma():
    columnas, filas = imp._leer_csv("x.csv", "﻿RUT_ESTUDIANTE;Estado\n1-9;presente\n")
    assert columnas == ["rut_estudiante", "estado"]
    assert filas == [{"rut_estudiante": "1-9", "estado": "presente"}]


def test_csv_vacio_es_rechazado():
    with pytest.raises(Exception) as error:
        imp._leer_csv("VACIO.csv", "   ")
    assert "vacío" in str(error.value.mensaje)


def test_identifica_tabla_por_nombre_y_por_columnas():
    assert imp._identificar_tabla("ESTUDIANTE.csv", []) == "ESTUDIANTE"
    assert imp._identificar_tabla("planilla.csv", ["fecha", "estado", "rut_estudiante"]) == "ASISTENCIA"
    assert imp._identificar_tabla("planilla.csv", ["fecha", "estado"]) is None  # falta RUT (HU 1.1 E2)


@pytest.mark.parametrize("estado, valido", [("presente", True), ("ausente", True), ("atraso", True),
                                            ("Presente", False), ("falta", False)])
def test_estado_de_asistencia_regla_r16(estado, valido):
    errores = imp._validar_dominio("ASISTENCIA", {"fecha": "2026-03-02", "estado": estado}, 2, {})
    assert (errores == []) is valido


def test_fecha_invalida_informa_linea():
    errores = imp._validar_dominio("ASISTENCIA", {"fecha": "02/03/2026", "estado": "presente"}, 5, {})
    assert errores == ["Línea 5: fecha '02/03/2026' no válida (formato AAAA-MM-DD)"]


@pytest.mark.parametrize("nota, valida", [("1.0", True), ("7.0", True), ("4,5", True),
                                          ("0.9", False), ("7.1", False), ("abc", False)])
def test_rango_de_nota(nota, valida):
    fila = {"nota": nota, "semestre": "1"}
    assert (imp._validar_dominio("CALIFICACION", fila, 2, {}) == []) is valida


def test_nota_con_coma_se_normaliza():
    fila = {"nota": "4,5", "semestre": "1"}
    imp._validar_dominio("CALIFICACION", fila, 2, {})
    assert fila["nota"] == "4.5"


@pytest.mark.parametrize("telefono, valido", [
    ("912345678", True), ("12345678", False), ("9123456789", False), ("91234567a", False),
    ("９１２３４５６７８", False),  # dígitos de ancho completo (Unicode)
])
def test_telefono_de_apoderado_en_importacion(telefono, valido):
    fila = {"rut_apoderado": "1-9", "nombre": "A", "apellido_apoderado": "B", "telefono": telefono}
    assert (imp._validar_dominio("APODERADO", fila, 2, {}) == []) is valido


def test_estudiante_de_1m_con_especialidad_viola_r10():
    estado = {"NIVEL": {("1",): {"nombre_nivel": "1M"}}}
    fila = {"id_nivel": "1", "id_especialidad": "2"}
    assert "R10" in imp._validar_dominio("ESTUDIANTE", fila, 3, estado)[0]
