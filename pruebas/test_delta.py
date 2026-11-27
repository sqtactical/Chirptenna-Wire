"""Delta loop."""

import math

import pytest

from wire import generadores, planos
from wire.diseno import Diseno, disenar

try:
    from wire import motor
    HAY_MOTOR = motor.disponible()
except Exception:                                    # noqa: BLE001
    HAY_MOTOR = False
PYNEC = pytest.mark.skipif(not HAY_MOTOR, reason="sin PyNEC")


def test_cotas_de_partida_y_modelo():
    p = generadores.delta_por_defecto(145.0)
    lam = 299792.458 / 145.0
    perimetro = p["base_mm"] + 2 * math.hypot(p["base_mm"] / 2, p["alto_mm"])
    assert 1.0 < perimetro / lam < 1.2                         # el lazo mide algo más de una longitud de onda
    d = disenar("delta", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.hilos) == 5
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_validaciones():
    with pytest.raises(ValueError):
        generadores.delta(145.0, 2.0, base_mm=10.0, centro_mm=20.0)
    with pytest.raises(ValueError):
        disenar("delta", 145.0, 2.0, ajustar=False, elementos=3)


def test_plano():
    d = disenar("delta", 145.0, 2.0, ajustar=False)
    p = planos.generar(d)
    assert len(p.hojas) == 1
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Delta loop" in texto and "LISTA DE CORTE" in texto


@PYNEC
def test_adapta_sin_adaptador():
    d = disenar("delta", 433.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.3 and r["ganancia_dBi"] > 3.5
