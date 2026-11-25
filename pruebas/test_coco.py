"""W2.5: colineal de coaxial (CoCo). Validado (25-11-2026) contra el circuito equivalente con fuentes iguales en cada
hueco (idéntico a 0,01 dB); **no** contra un caso publicado ni contra una medida: las cifras absolutas siguen sin
comprobar."""

import dataclasses

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


def _con_fuentes_iguales(modelo) -> str:
    """El mismo mazo sin las TL y con 1 V en fase en cada hueco. Es lo que da la teoría de circuitos: una línea de λ/2
    es un inversor 1:1 (V arriba = −V abajo, sea cual sea la carga) y el cruce vuelve a invertir, así que todos los
    huecos ven la misma tensión. Es una comprobación independiente del código de TL de NEC2."""
    huecos = sorted({l.hilo1 for l in modelo.lineas} | {l.hilo2 for l in modelo.lineas})
    lineas = [l for l in nec.exportar(dataclasses.replace(modelo, lineas=())).splitlines() if not l.startswith("EX")]
    i = max(k for k, l in enumerate(lineas) if l.startswith("GN")) + 1
    return "\n".join(lineas[:i] + [f"EX 0 {h} 1 0 1.0 0" for h in huecos] + lineas[i:]) + "\n"


@pynec
@pytest.mark.parametrize("tramos", [2, 4, 6])
def test_las_tl_cruzadas_equivalen_a_fuentes_iguales_en_cada_hueco(tramos):
    m = colineal_coco(145.0, RG58, tramos=tramos)
    con_tl = motor.simular(m).ganancia_max[0]
    con_fuentes = motor.simular_nec(_con_fuentes_iguales(m)).ganancia_max[0]
    assert con_tl == pytest.approx(con_fuentes, abs=0.01)


@pynec
def test_sin_cruzar_no_equivale():
    """La prueba de arriba distingue: con las líneas sin cruzar la ganancia ya no coincide (2 tramos: 3,4 frente a 4,4 dBi)."""
    m = colineal_coco(145.0, RG58, tramos=2)
    sin_cruzar = dataclasses.replace(m, lineas=tuple(dataclasses.replace(l, cruzada=False) for l in m.lineas))
    assert abs(motor.simular(sin_cruzar).ganancia_max[0] - motor.simular_nec(_con_fuentes_iguales(m)).ganancia_max[0]) > 0.5