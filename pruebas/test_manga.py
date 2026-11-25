"""W2.4: dipolo de manga de coaxial (modelo B: dos hilos del mismo radio y choke como reactancia de la línea manga–cable)."""

import dataclasses

import pytest

from wire import motor
from wire.cables import cable
from wire.coaxial import dipolo_manga
from wire.modelo import Barrido

pynec = pytest.mark.skipif(not motor.disponible(), reason="no hay PyNEC")
RG58 = cable("RG-58")


def _resonancia(**kw):
    """(f de resonancia, R en ella, ganancia máxima) con un barrido de 130 a 160 MHz."""
    r = motor.simular(dipolo_manga(145.0, RG58, barrido=Barrido(130.0, 160.0, 31), **kw))
    x = [z.imag for z in r.z]
    for k in range(len(x) - 1):
        if x[k] <= 0 < x[k + 1]:
            t = -x[k] / (x[k + 1] - x[k])
            f = r.frecuencias[k] + (r.frecuencias[k + 1] - r.frecuencias[k]) * t
            g = r.ganancia_max[k] + (r.ganancia_max[k + 1] - r.ganancia_max[k]) * t
            return f, r.z[k].real + (r.z[k + 1].real - r.z[k].real) * t, g
    raise AssertionError("sin resonancia en 130–160 MHz")


def test_geometria_y_carga():
    m = dipolo_manga(145.0, RG58)
    assert len(m.hilos) == 5 and m.puerto.hilo == 1 and len(m.cargas) == 1
    assert len(dipolo_manga(145.0, RG58, resto_m=0).hilos) == 3
    assert dipolo_manga(145.0, RG58, resto_m=0).cargas == ()


@pynec
def test_converge_al_duplicar_los_segmentos():
    f50, r50, _ = _resonancia(div=50)
    f100, r100, _ = _resonancia(div=100)
    assert abs(f100 - f50) / f50 < 0.01
    assert abs(r100 - r50) / r50 < 0.1


@pynec
def test_resonancia_y_resistencia_de_dipolo():
    f, r, g = _resonancia(div=100)
    assert 143 < f < 147            # diseñado para 145 MHz (±1,5 %)
    assert 60 < r < 95              # dipolo de media onda
    assert 1.4 < g < 3.2            # dBi, haz de dipolo con el cable colgando


@pynec
def test_la_manga_aisla_del_largo_del_cable():
    def z(**kw):
        return motor.simular(dipolo_manga(145.0, RG58, **kw)).z[0]
    largos = (0.3, 0.7, 1.2)
    con = [z(resto_m=r) for r in largos]
    variacion = max(abs(a - b) for a in con for b in con)
    # Sin el choke de la manga (carga quitada) la impedancia cambia mucho más con el cable.
    sin = []
    for r in largos:
        m = dipolo_manga(145.0, RG58, resto_m=r)
        sin.append(motor.simular(dataclasses.replace(m, cargas=())).z[0])
    assert variacion < 20.0, variacion
    assert variacion < max(abs(a - b) for a in sin for b in sin) / 3
