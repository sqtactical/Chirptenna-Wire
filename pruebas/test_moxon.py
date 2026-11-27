"""Moxon rectangular de alambre."""

import pytest

from wire import generadores, planos
from wire.diseno import Diseno, disenar

try:
    from wire import motor
    HAY_MOTOR = motor.disponible()
except Exception:                                    # noqa: BLE001
    HAY_MOTOR = False
PYNEC = pytest.mark.skipif(not HAY_MOTOR, reason="sin PyNEC")


def test_cotas_de_partida_escalan_con_la_frecuencia():
    a, b = generadores.moxon_por_defecto(145.0), generadores.moxon_por_defecto(433.0)
    assert 2.5 < a["ancho_mm"] / b["ancho_mm"] < 3.2
    d = disenar("moxon", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.hilos) == 1 + 3 * 2 + 1                       # alimentación, (excitado + 2 puntas) × 2 mitades, reflector
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_validaciones():
    with pytest.raises(ValueError):
        generadores.moxon(145.0, 2.0, hueco_mm=3.0)            # puntas casi tocándose
    with pytest.raises(ValueError):
        disenar("moxon", 145.0, 2.0, ajustar=False, elementos=3)
    with pytest.raises(ValueError):
        disenar("moxon", 145.0, 2.0, ajustar=False, altura_m=10.0)


def test_plano():
    d = disenar("moxon", 145.0, 2.0, ajustar=False)
    p = planos.generar(d)
    assert len(p.hojas) == 1
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Moxon rectangular" in texto and "LISTA DE CORTE" in texto


@PYNEC
def test_adapta_y_el_haz_sale_hacia_delante():
    d = disenar("moxon", 433.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.3
    assert r["ganancia_frente_dBi"] > 5.5 and r["relacion_delante_detras_dB"] > 10
