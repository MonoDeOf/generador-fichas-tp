"""Pruebas unitarias del motor de riesgo (HU 4.1, 4.2 y 4.3)."""
import pytest

from conftest import registro
from services import riesgo_service
from services.errores import ErrorNegocio

REGLAS = {"umbral_asistencia": 85.0, "nota_deficiente": 4.0, "min_notas_deficientes": 1, "operador": "Y",
          "ausencias_consecutivas": 3, "min_anotaciones_negativas": 0}
ESTUDIANTE = {"rut_estudiante": "11111111-1"}
ASIGNATURAS = {"MAT1": {"nombre_asignatura": "Matemática"}}


def asistencia(presentes, ausentes):
    """Genera registros intercalando cada ausencia después de un día presente (sin rachas)."""
    estados = []
    for i in range(presentes):
        estados.append("presente")
        if i < ausentes:
            estados.append("ausente")
    return [registro(f"2026-05-{d:02d}", e) for d, e in enumerate(estados, start=1)]


def notas(*valores):
    return [{"nota": str(v), "id_asignatura": "MAT1"} for v in valores]


def evaluar(asis, cal, reglas=REGLAS, anot=()):
    return riesgo_service._evaluar(ESTUDIANTE, reglas, asis, cal, list(anot), ASIGNATURAS)


def test_sin_factores_es_verde():
    r = evaluar(asistencia(20, 0), notas(6.0, 5.5))
    assert r["nivel_riesgo"] == "Verde"
    assert r["factores"] == []


def test_un_factor_es_amarillo():
    r = evaluar(asistencia(20, 0), notas(3.5, 6.0))
    assert r["nivel_riesgo"] == "Amarillo"
    assert [f["tipo"] for f in r["factores"]] == ["calificaciones"]


def test_regla_combinada_y_es_rojo_y_explica_motivos():
    r = evaluar(asistencia(8, 2), notas(3.0))  # 80 % de asistencia y una nota roja
    assert r["nivel_riesgo"] == "Rojo"
    tipos = [f["tipo"] for f in r["factores"]]
    assert tipos[0] == "regla_combinada"
    assert "asistencia" in tipos and "calificaciones" in tipos
    assert "80.0%" in r["factores"][1]["descripcion"]


def test_operador_o_dispara_con_una_sola_condicion():
    reglas = {**REGLAS, "operador": "O"}
    assert evaluar(asistencia(20, 0), notas(3.0), reglas)["nivel_riesgo"] == "Rojo"
    assert evaluar(asistencia(20, 0), notas(3.0), REGLAS)["nivel_riesgo"] == "Amarillo"


def test_tres_ausencias_consecutivas_es_rojo_critico():
    asis = [registro("2026-05-04", "presente")] + [registro(f"2026-05-0{d}", "ausente") for d in (5, 6, 7)] + \
           [registro(f"2026-05-{d:02d}", "presente") for d in range(8, 28)]
    r = evaluar(asis, notas(6.0))
    assert r["nivel_riesgo"] == "Rojo"
    assert r["rachas_criticas"][0]["dias"] == 3
    assert any(f.get("critico") and f["tipo"] == "ausencias_consecutivas" for f in r["factores"])


def test_anotaciones_desactivadas_por_defecto():
    anot = [{"tipo_anotacion": "Negativa"}] * 5
    assert evaluar(asistencia(20, 0), notas(6.0), anot=anot)["nivel_riesgo"] == "Verde"
    reglas = {**REGLAS, "min_anotaciones_negativas": 3}
    assert evaluar(asistencia(20, 0), notas(6.0), reglas, anot)["nivel_riesgo"] == "Amarillo"


def test_umbral_configurado_cambia_el_resultado():
    """HU 4.2 E3: con umbral 85 % un 84 % activa el factor; con umbral 80 % no."""
    asis = asistencia(21, 4)  # 84 %
    assert evaluar(asis, [])["indicadores"]["porcentaje_asistencia"] == 84.0
    assert evaluar(asis, [])["nivel_riesgo"] == "Amarillo"
    assert evaluar(asis, [], {**REGLAS, "umbral_asistencia": 80.0})["nivel_riesgo"] == "Verde"


@pytest.mark.parametrize("cambio, mensaje", [
    ({"umbral_asistencia": 120}, "entre 0 y 100"),
    ({"umbral_asistencia": -1}, "entre 0 y 100"),
    ({"nota_deficiente": 8.0}, "entre 1.0 y 7.0"),
    ({"min_notas_deficientes": 0}, "al menos 1"),
    ({"operador": "XOR"}, "'Y' u 'O'"),
    ({"ausencias_consecutivas": 0}, "al menos 1"),
])
def test_guardar_reglas_rechaza_valores_invalidos(datos_vacios, cambio, mensaje):
    riesgo_service.inicializar_reglas()
    with pytest.raises(ErrorNegocio) as error:
        riesgo_service.guardar_reglas({**REGLAS, **cambio}, id_usuario=1)
    assert error.value.codigo == 400
    assert any(mensaje in d for d in error.value.detalles)
    assert riesgo_service.obtener_reglas()["umbral_asistencia"] == 85.0  # se conserva la anterior


def test_guardar_reglas_validas_persiste(datos_vacios):
    riesgo_service.inicializar_reglas()
    riesgo_service.guardar_reglas({**REGLAS, "umbral_asistencia": 90}, id_usuario=1)
    assert riesgo_service.obtener_reglas()["umbral_asistencia"] == 90.0
