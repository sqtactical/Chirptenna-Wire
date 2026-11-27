"""Yagi de dos bandas (145 / 433 MHz) con el excitado en abanico."""

import pytest

from wire import generadores, ganancias, planos
from wire.diseno import Diseno, disenar
from wire.planos.comun import fmt

try:
    from wire import motor
    HAY_MOTOR = motor.disponible()
except Exception:                                    # noqa: BLE001
    HAY_MOTOR = False
PYNEC = pytest.mark.skipif(not HAY_MOTOR, reason="sin PyNEC")


def test_cotas_de_partida_y_modelo():
    d = disenar("yagi_bibanda", 145.0, 2.0, ajustar=False)
    g = d.geometria
    assert d.estado == "Sin validar" and abs(g["f_alta_MHz"] - 433.0) < 0.1
    m = d.modelo()
    assert len(m.hilos) == 1 + 4 + 2 + 1 + 2                # alimentación, 4 brazos, 2 reflectores, 1 + 2 directores
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_validaciones():
    with pytest.raises(ValueError):
        disenar("yagi_bibanda", 7.1, 2.0, ajustar=False)                     # fuera de la banda baja admitida
    with pytest.raises(ValueError):
        disenar("yagi_bibanda", 145.0, 2.0, ajustar=False, elementos=5)
    with pytest.raises(ValueError):
        disenar("yagi_bibanda", 145.0, 2.0, ajustar=False, f_alta_MHz=433.0)
    with pytest.raises(ValueError):
        disenar("yagi_bibanda", 145.0, 2.0, ajustar=False, altura_m=10.0)


def test_plano_y_ganancia_de_referencia():
    d = disenar("yagi_bibanda", 145.0, 2.0, ajustar=False)
    p = planos.generar(d)
    assert len(p.hojas) == 1
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Yagi bibanda" in texto and "LISTA DE CORTE" in texto and "SIN SIMULAR" in texto
    assert "6,2 dBi en 145 MHz y 6,3 dBi en 433 MHz" in ganancias.texto(d, fmt).replace(".", ",")


@PYNEC
def test_adapta_en_las_dos_bandas_y_con_el_haz_hacia_delante():
    d = disenar("yagi_bibanda", 145.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.5 and r["alta"]["roe"] < 1.5
    assert r["ganancia_frente_dBi"] > 5.0 and r["alta"]["ganancia_frente_dBi"] > 5.0      # el haz sale hacia delante (φ 90°) en las dos
    assert r["alta"]["ganancia_dBi"] - r["alta"]["ganancia_frente_dBi"] < 1.0
