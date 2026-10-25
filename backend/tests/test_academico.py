"""Pruebas unitarias de academico_service: asistencia, rachas y regla R7."""
import pytest

from conftest import registro
from services import academico_service as acad


def test_resumen_asistencia_caso_normal():
    registros = [registro("2026-03-02", "presente"), registro("2026-03-03", "ausente"),
                 registro("2026-03-04", "atraso"), registro("2026-03-05", "presente")]
    resumen = acad.resumen_asistencia(registros)
    assert resumen["total_dias"] == 4
    assert resumen["ausentes"] == 1
    assert resumen["atrasos"] == 1
    assert resumen["porcentaje_asistencia"] == 75.0


def test_resumen_asistencia_atraso_cuenta_como_asistido():
    registros = [registro("2026-03-02", "atraso"), registro("2026-03-03", "atraso")]
    assert acad.resumen_asistencia(registros)["porcentaje_asistencia"] == 100.0


def test_resumen_asistencia_sin_registros_devuelve_none():
    """Caso límite: sin registros no se puede calcular un porcentaje (no se divide por cero)."""
    assert acad.resumen_asistencia([])["porcentaje_asistencia"] is None


def test_porcentaje_se_redondea_a_un_decimal():
    registros = [registro(f"2026-03-0{i}", "presente") for i in range(1, 3)] + [registro("2026-03-09", "ausente")]
    assert acad.resumen_asistencia(registros)["porcentaje_asistencia"] == pytest.approx(66.7)


@pytest.mark.parametrize("estados, esperado", [
    (["presente", "presente"], []),
    (["ausente", "ausente", "ausente"], [3]),
    (["ausente", "presente", "ausente", "ausente"], [1, 2]),
    (["ausente", "atraso", "ausente"], [1, 1]),  # un atraso corta la racha
])
def test_rachas_ausencia(estados, esperado):
    registros = [registro(f"2026-04-{d:02d}", e) for d, e in enumerate(estados, start=1)]
    assert [r["dias"] for r in acad.rachas_ausencia(registros)] == esperado


def test_racha_informa_inicio_y_fin():
    registros = [registro("2026-04-06", "ausente"), registro("2026-04-07", "ausente"),
                 registro("2026-04-08", "ausente")]
    assert acad.rachas_ausencia(registros) == [{"inicio": "2026-04-06", "fin": "2026-04-08", "dias": 3}]


@pytest.mark.parametrize("horas, notas", [(2, 3), (3, 3), (4, 4), (6, 6), (8, 6)])
def test_cantidad_notas_regla_r7(horas, notas):
    assert acad.cantidad_notas(horas) == notas
