"""Quad cúbica de dos elementos."""

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
    a, b = generadores.quad_por_defecto(145.0), generadores.quad_por_defecto(433.0)
    assert 2.5 < a["lado_excitado_mm"] / b["lado_excitado_mm"] < 3.2
    assert a["lado_reflector_mm"] > a["lado_excitado_mm"]
    d = disenar("quad", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.hilos) == 1 + 5 + 4                           # alimentación, lazo excitado (5 tramos), lazo reflector (4)
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_validaciones():
    with pytest.raises(ValueError):
        generadores.quad(145.0, 2.0, lado_excitado_mm=10.0, centro_mm=20.0)       # el hueco central no cabe
    with pytest.raises(ValueError):
        disenar("quad", 145.0, 2.0, ajustar=False, elementos=3)


def test_plano():
    d = disenar("quad", 145.0, 2.0, ajustar=False)
    p = planos.generar(d)
    assert len(p.hojas) == 1
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Quad cúbica" in texto and "LISTA DE CORTE" in texto


@PYNEC
def test_adapta_y_el_haz_sale_hacia_delante():
    d = disenar("quad", 433.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.3
    assert r["ganancia_frente_dBi"] > 7.0 and r["relacion_delante_detras_dB"] > 6
