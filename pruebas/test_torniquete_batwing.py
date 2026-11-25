"""Torniquete (polarización circular por la línea de λ/4) y batwing (más banda que el dipolo), con PyNEC."""

from dataclasses import replace

import pytest

from wire import generadores, motor
from wire.modelo import Barrido

pytestmark = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def test_el_torniquete_con_su_linea_es_casi_circular_y_sin_ella_lineal():
    f = 137.5
    m = generadores.torniquete(f, 3.0)
    assert motor.razon_axial_dB(m, f) < 2.0
    # Sin la línea no hay segundo dipolo alimentado: queda el dipolo de arriba parásito y la polarización es lineal.
    sin_linea = replace(m, lineas=())
    assert motor.razon_axial_dB(sin_linea, f) > 10.0


def test_el_torniquete_adapta_a_50_ohm_sin_ajustar():
    f = 137.5
    r = motor.simular(generadores.torniquete(f, 3.0, barrido=Barrido(f, f, 1)), diagrama=True)
    assert r.roe[0] < 1.6
    assert 1.5 < r.ganancia_max[0] < 3.0       # un par de dipolos cruzados: ~2 dBi


def test_el_ajuste_conserva_la_circularidad():
    from wire.ajuste import ajustar_torniquete
    r = ajustar_torniquete(137.5, 3.0)["resultados"]
    assert r["razon_axial_cenit_dB"] < 3.0 and r["roe"] < 2.0


def _ancho_roe2(modelo, f):
    r = motor.simular(modelo, Barrido(0.7 * f, 1.4 * f, 71), diagrama=False)
    k = min(range(len(r.roe)), key=lambda i: r.roe[i])
    assert r.roe[k] < 2.0
    i0 = i1 = k
    while i0 > 0 and r.roe[i0 - 1] < 2.0:
        i0 -= 1
    while i1 < len(r.roe) - 1 and r.roe[i1 + 1] < 2.0:
        i1 += 1
    return (r.frecuencias[i1] - r.frecuencias[i0]) / r.frecuencias[k]


def test_el_batwing_ajustado_tiene_mas_banda_que_el_dipolo():
    from wire.ajuste import ajustar_batwing, ajustar_dipolo
    f = 145.0
    bat = ajustar_batwing(f, 3.0)
    assert bat["resultados"]["roe"] < 2.0
    g = bat["geometria"]
    ancho_bat = _ancho_roe2(generadores.batwing(f, 3.0, ala_mm=g["ala_mm"], ancho_mm=g["ancho_mm"], hueco_mm=g["hueco_mm"],
                                                radios=int(g["radios"])), f)
    dip = ajustar_dipolo(f, 3.0)
    ancho_dip = _ancho_roe2(generadores.dipolo(f, 1.5, longitud_mm=dip["geometria"]["largo_total_mm"]), f)
    assert ancho_bat > 1.5 * ancho_dip


def test_el_modelo_del_diseno_coincide_con_el_generador():
    from wire.diseno import disenar
    d = disenar("batwing", 145.0, 3.0, ajustar=False)
    assert len(d.modelo().hilos) == 1 + 2 * (5 + 4)
    t = disenar("torniquete", 137.5, 3.0, ajustar=False)
    assert len(t.modelo().lineas) == 1 and len(t.modelo().hilos) == 2
