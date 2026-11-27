"""Halo y dos Yagis apiladas."""

import pytest

from wire import generadores, planos
from wire.diseno import Diseno, disenar

try:
    from wire import motor
    HAY_MOTOR = motor.disponible()
except Exception:                                    # noqa: BLE001
    HAY_MOTOR = False
PYNEC = pytest.mark.skipif(not HAY_MOTOR, reason="sin PyNEC")


def test_halo_cotas_y_modelo():
    a, b = generadores.halo_por_defecto(145.0), generadores.halo_por_defecto(433.0)
    assert 2.5 < a["radio_mm"] / b["radio_mm"] < 3.2
    d = disenar("halo", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.lineas) == 1 and m.lineas[0].z0 == 25.0
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos
    with pytest.raises(ValueError):
        generadores.halo(145.0, 2.0, abertura=1.0)
    with pytest.raises(ValueError):
        disenar("halo", 145.0, 2.0, ajustar=False, elementos=3)


def test_halo_plano():
    p = planos.generar(disenar("halo", 145.0, 2.0, ajustar=False))
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert len(p.hojas) == 1 and "Halo" in texto and "LISTA DE CORTE" in texto


def test_yagi_apilada_cotas_y_modelo():
    d = disenar("yagi_apilada", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.lineas) == 2 and m.lineas[0].longitud == m.lineas[1].longitud
    assert len(m.hilos) == 2 * 8 + 1                            # dos Yagis de 5 elementos (3 + 2 de plegado y 2 de cierre) y la fuente
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos
    p = d.resultados or {}
    with pytest.raises(ValueError):
        generadores.yagi_apilada(145.0, 2.0, **{**{k: v for k, v in d.geometria.items() if k in (
            "reflector_mm", "excitado_mm", "sep_reflector_mm", "sep_plegado_mm", "directores_mm", "seps_directores_mm")},
            "separacion_mm": 1000.0, "linea_mm": 100.0})


def test_yagi_apilada_plano():
    p = planos.generar(disenar("yagi_apilada", 145.0, 2.0, ajustar=False))
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert len(p.hojas) == 2 and "Dos Yagis de 5 elementos apiladas" in texto and "LISTA DE CORTE" in texto


@PYNEC
def test_halo_adapta():
    d = disenar("halo", 433.0, 2.0, ajustar=True)
    assert d.estado == "Simulado" and d.resultados["roe"] < 1.3


@PYNEC
def test_yagi_apilada_adapta_y_gana_mas_que_una_sola():
    d = disenar("yagi_apilada", 433.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.3
    assert r["ganancia_frente_dBi"] > 11.0 and r["relacion_delante_detras_dB"] > 6
