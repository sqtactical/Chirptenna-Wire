"""W4.1: geometría de Koch (4^n tramos, longitud (4/3)^n veces la cuerda, extremos exactos)."""

import math

import pytest

from wire import geometria as g


@pytest.mark.parametrize("n,tramos", [(0, 1), (1, 4), (2, 16), (3, 64)])
def test_tramos_y_longitud(n, tramos):
    p0, p1 = (3.0, -2.0), (3.0, 118.0)
    pts = g.koch(n, p0, p1)
    assert len(pts) == tramos + 1 and pts[0] == p0 and pts[-1] == p1
    cuerda = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    assert g.longitud(pts) == pytest.approx(cuerda * (4 / 3) ** n, rel=1e-9)
    largos = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(pts, pts[1:])]
    assert max(largos) == pytest.approx(min(largos), rel=1e-6) == pytest.approx(cuerda / 3 ** n, rel=1e-6)


def test_la_curva_no_se_sale_de_la_cuerda_en_su_proyeccion():
    pts = g.koch(3, (0.0, 0.0), (0.0, 100.0))
    assert all(-1e-6 <= y <= 100 + 1e-6 for _, y in pts)


def test_hacia_fuera_pone_las_muescas_a_la_izquierda():
    pts = g.koch_hacia_fuera(2, (0.0, 0.0), (0.0, 100.0))
    assert sum(x for x, _ in pts) / len(pts) <= 0 and min(x for x, _ in pts) < -5
    # un punto que no se pasa de la raya por el otro lado más de lo que se mete por este
    assert max(x for x, _ in pts) < -min(x for x, _ in pts)
