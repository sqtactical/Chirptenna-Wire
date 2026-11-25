"""Motor contra la teoría: dipolo λ/2 de hilo fino. Se salta si PyNEC no está instalado."""

import math

import pytest

from wire import Barrido, Hilo, Modelo, Puerto, dipolo, longitud_onda_m
from wire import motor, nec

pytestmark = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")

F = 145.0
LAMBDA = longitud_onda_m(F)


def _dipolo_fino():
    return dipolo(F, radio_mm=0.001 * LAMBDA * 1000)  # radio 0,001 λ


@pytest.fixture(scope="module")
def resonancia():
    m = _dipolo_fino()
    f, z = motor.resonancia(m, 0.9 * F, 1.1 * F)
    return m, f, z


def test_resonancia_a_047_048_lambda(resonancia):
    m, f, z = resonancia
    relacion = m.hilos[0].longitud / longitud_onda_m(f)
    assert 0.47 <= relacion <= 0.48
    assert abs(z.imag) < 0.01


def test_resistencia_a_la_resonancia(resonancia):
    _, _, z = resonancia
    assert 70.0 <= z.real <= 73.0


def test_ganancia_de_dipolo():
    r = motor.simular(_dipolo_fino())
    assert r.ganancia_max[0] == pytest.approx(2.15, abs=0.1)  # dBi teóricos del dipolo λ/2


def test_barrido_s11_y_roe():
    m = _dipolo_fino()
    r = motor.simular(m, Barrido(130.0, 160.0, 31), diagrama=False)
    assert len(r.z) == 31 and r.ganancia_max is None
    assert r.frecuencias[0] == pytest.approx(130.0) and r.frecuencias[-1] == pytest.approx(160.0)
    # X crece con la frecuencia alrededor de la resonancia serie.
    assert all(b.imag > a.imag for a, b in zip(r.z, r.z[1:]))
    # ROE coherente con S11 y mínima cerca de la resonancia (R ≈ 72 Ω contra 50 Ω: ROE ≈ 1,44).
    k = min(range(31), key=lambda i: r.roe[i])
    assert 140.0 <= r.frecuencias[k] <= 146.0
    assert r.roe[k] == pytest.approx(1.44, abs=0.05)
    g = abs(r.s11[k])
    assert r.roe[k] == pytest.approx((1 + g) / (1 - g))
    assert r.s11_dB[k] == pytest.approx(20 * math.log10(g))


def test_convergencia_con_los_segmentos():
    """Duplicar los segmentos mueve la resonancia menos de un 0,2 %."""
    f1, _ = motor.resonancia(dipolo(F, 0.001 * LAMBDA * 1000, segmentos=25), 130, 160)
    f2, _ = motor.resonancia(dipolo(F, 0.001 * LAMBDA * 1000, segmentos=51), 130, 160)
    assert abs(f2 - f1) / f1 < 0.002


def test_monopolo_sobre_suelo_perfecto_es_medio_dipolo():
    """Comprueba GN/GE: Z del monopolo λ/4 = Z del dipolo λ/2 / 2."""
    d = _dipolo_fino()
    h = d.hilos[0]
    n = h.segmentos // 2 + 1  # el segmento de alimentación del dipolo pasa a ser la base del monopolo
    largo = h.longitud / 2
    mono = Modelo("Monopolo", F, (Hilo((0, 0, 0), (0, 0, largo), h.radio, n),), Puerto(1, 1), plano_masa=True)
    zd = motor.simular(d, diagrama=False).z[0]
    zm = motor.simular(mono, diagrama=False).z[0]
    assert abs(zm - zd / 2) / abs(zd / 2) < 0.05


def test_simular_nec_es_el_mismo_mazo():
    m = _dipolo_fino()
    assert motor.simular_nec(nec.exportar(m)).z == motor.simular(m).z


@pytest.mark.skipif(motor.ruta_nec2c() is None, reason="nec2c no está instalado")
def test_nec2c_coincide_con_pynec():
    m = dipolo(F, 0.001 * LAMBDA * 1000, barrido=Barrido(140.0, 150.0, 5))
    texto = nec.exportar(m)
    z_pynec = motor.simular_nec(texto).z
    z_nec2c = motor.ejecutar_nec2c(texto)
    assert len(z_nec2c) == len(z_pynec)
    for a, b in zip(z_pynec, z_nec2c):
        assert abs(a - b) / abs(a) <= 0.005
