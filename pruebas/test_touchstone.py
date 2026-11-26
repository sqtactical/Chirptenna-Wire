"""S11 simulado en Touchstone para Chirptenna VNA."""

import pytest

from wire import escritorio, motor, touchstone
from wire.diseno import disenar

pytestmark = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def _leer(texto):
    datos = [l.split() for l in texto.splitlines() if l and l[0] not in "!#"]
    return [(float(f), complex(float(a), float(b))) for f, a, b in datos]


def test_s1p_del_dipolo():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    t = touchstone.s1p(d, 135.0, 155.0, 41)
    assert "# MHz S RI R 50" in t and "NO es una medida" in t
    pts = _leer(t)
    assert len(pts) == 41 and pts[0][0] == pytest.approx(135.0) and pts[-1][0] == pytest.approx(155.0)
    assert all(abs(g) <= 1.0 + 1e-9 for _, g in pts)
    f_min = min(pts, key=lambda p: abs(p[1]))[0]
    assert 135.0 < f_min < 155.0                       # el mínimo de |S11| cae dentro del barrido


def test_rango_por_defecto_y_validacion():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    assert touchstone.rango_MHz(d) == pytest.approx((130.5, 159.5))
    with pytest.raises(ValueError):
        touchstone.s1p(d, 150.0, 140.0)


def test_escritorio_s1p():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    assert len(_leer(escritorio.s1p(d.a_json()))) == touchstone.PUNTOS
