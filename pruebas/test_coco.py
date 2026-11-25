"""W2.5: colineal de coaxial (CoCo). El modelo está SIN VALIDAR contra un caso publicado: estas pruebas solo vigilan que
la estructura sea la esperada y que la ganancia suba con los tramos, no que las cifras sean las de una CoCo real."""

import pytest

from wire import motor, nec
from wire.cables import cable
from wire.coaxial import colineal_coco

RG58 = cable("RG-58")
pynec = pytest.mark.skipif(not motor.disponible(), reason="no hay PyNEC")


def test_estructura():
    m = colineal_coco(145.0, RG58, tramos=4)
    assert len(m.lineas) == 4 and all(l.cruzada for l in m.lineas)
    assert len(m.hilos) == 1 + 4 * 2 + 1                       # hueco inicial, 4 × (tramo + hueco), punta
    assert m.lineas[0].hilo1 == m.puerto.hilo                  # la fuente y la primera línea comparten el hueco
    assert m.lineas[0].longitud_electrica == pytest.approx(299.792458 / 145.0 / 2)   # λ/2 eléctrico
    tl = [t for t in nec.leer(nec.exportar(m)) if t.nombre == "TL"]
    assert len(tl) == 4 and all(t.reales[0] < 0 for t in tl)  # Z0 negativa: línea cruzada


def test_con_bajada_y_choke():
    m = colineal_coco(145.0, RG58, tramos=2, bajada_m=0.5, choke_ohm=2000.0)
    assert len(m.cargas) == 1 and m.hilos[0].inicio[2] == -0.5


@pynec
def test_la_ganancia_sube_con_los_tramos():
    g = {n: motor.simular(colineal_coco(145.0, RG58, tramos=n)).ganancia_max[0] for n in (1, 2, 4)}
    assert g[1] < g[2] < g[4] and g[4] - g[1] > 2.0, g
