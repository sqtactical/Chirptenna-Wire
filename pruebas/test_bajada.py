"""W2.3: el cable de bajada cambia la impedancia del dipolo de coaxial y el choke la devuelve cerca de la aislada."""

import pytest

from wire import motor, nec
from wire.cables import cable
from wire.coaxial import dipolo_con_bajada

F = 145.0
pynec = pytest.mark.skipif(not motor.disponible(), reason="no hay PyNEC")


def _z(**kw):
    return motor.simular(dipolo_con_bajada(F, cable("RG-58"), **kw)).z[0]


def test_la_geometria_y_el_choke_van_al_nec():
    m = dipolo_con_bajada(F, cable("RG-58"))
    assert len(m.hilos) == 5 and m.puerto.hilo == 2 and len(m.cargas) == 1
    tarjetas = nec.leer(nec.exportar(m))
    assert [t.nombre for t in tarjetas].count("GW") == 5
    assert not dipolo_con_bajada(F, cable("RG-58"), choke_ohm=None).cargas
    assert len(dipolo_con_bajada(F, cable("RG-58"), bajada_m=0).hilos) == 3


@pynec
def test_sin_bajada_es_un_dipolo_normal():
    z = _z(bajada_m=0.0)
    assert 60 < z.real < 90 and abs(z.imag) < 60, z


def _variacion(**kw):
    zs = [_z(bajada_m=0.1, resto_m=r, **kw) for r in (0.3, 0.7, 1.0, 1.5)]
    return max(abs(a - b) for a in zs for b in zs)


@pynec
@pytest.mark.parametrize("axial", [False, True])
def test_el_choke_hace_la_impedancia_independiente_del_largo_del_cable(axial):
    """Lo que hace un choke: sin él, la impedancia cambia con lo que cuelga; con él, casi no. (145 MHz, RG-58;
    medido el 25-11: en axial 1216 Ω sin choke frente a 25–53 Ω con 2–10 kΩ; en perpendicular 22 Ω frente a 0,6.)"""
    sin_choke = _variacion(choke_ohm=None, axial=axial)
    con_choke = _variacion(choke_ohm=2000.0, axial=axial)
    assert con_choke < sin_choke / 4, (sin_choke, con_choke)


@pynec
def test_el_cable_axial_sin_choke_perturba_mucho_mas_que_el_perpendicular():
    assert abs(_z(choke_ohm=None, axial=True) - _z(bajada_m=0.0)) > 3 * abs(_z(choke_ohm=None) - _z(bajada_m=0.0))
