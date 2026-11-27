"""Cuatro dipolos apilados en fase."""

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
    d = disenar("apilados", 145.0, 2.0, ajustar=False)
    m = d.modelo()
    assert len(m.hilos) == 4 + 1 and len(m.lineas) == 4 and {l.longitud for l in m.lineas} == {m.lineas[0].longitud}
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_las_lineas_tienen_que_llegar_al_dipolo_mas_lejano():
    p = generadores.apilados_por_defecto(145.0)
    with pytest.raises(ValueError):
        generadores.apilados(145.0, 2.0, linea_mm=0.5 * p["separacion_mm"])
    with pytest.raises(ValueError):
        disenar("apilados", 145.0, 2.0, ajustar=False, elementos=2)


def test_plano():
    d = disenar("apilados", 145.0, 2.0, ajustar=False)
    p = planos.generar(d)
    assert len(p.hojas) == 1
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Dipolos apilados" in texto and "LISTA DE CORTE" in texto


@PYNEC
def test_adapta_con_la_ganancia_de_cuatro_dipolos():
    d = disenar("apilados", 433.0, 2.0, ajustar=True)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.3 and r["ganancia_dBi"] > 8.5
