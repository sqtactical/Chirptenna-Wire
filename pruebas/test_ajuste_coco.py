"""W2.5: ajuste de la CoCo. La red en L es matemática pura (no necesita motor); el ajuste completo, sí."""

import pytest

from wire import motor
from wire.ajuste import ajustar_coco, red_adaptacion, z_con_red
from wire.cables import cable

pynec = pytest.mark.skipif(not motor.disponible(), reason="no hay PyNEC")


@pytest.mark.parametrize("z", [30 + 10j, 10 - 40j, 101 + 133j, 260 + 286j, 50 + 80j, 75 - 20j, 200 - 150j])
def test_la_red_en_l_adapta_a_50_ohm(z):
    red = red_adaptacion(z, 145.0)
    assert abs(z_con_red(z, red) - 50.0) < 1e-6
    assert any(k in red for k in ("l_serie_nH", "c_serie_pF")) and any(k in red for k in ("c_paralelo_pF", "l_paralelo_nH"))


@pynec
def test_ajuste_de_la_coco_adapta_sin_tocar_la_ganancia():
    r = ajustar_coco(145.0, cable("RG-58"), tramos=2)
    x = r["resultados"]
    assert x["roe_con_red"] < 1.05 and x["roe_sin_red"] > 3
    assert x["ganancia_dBi"] == pytest.approx(x["ganancia_sin_ajustar_dBi"])
    assert r["geometria"]["factor_tramo"] == 1.0 and r["geometria"]["punta_lambda"] == 0.25
