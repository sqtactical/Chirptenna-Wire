"""Vertical de HF de λ/4 con radiales elevados sobre suelo real."""

import pytest

from wire import generadores as G
from wire import motor
from wire.diseno import disenar


def test_geometria_por_defecto():
    m = G.vertical_hf(7.1, 3.0)
    assert len(m.hilos) == 1 + G.VERT_RADIALES and m.suelo is not None
    assert m.hilos[0].inicio[2] == pytest.approx(2.0) and m.hilos[0].longitud == pytest.approx(0.245 * 299.792458 / 7.1, rel=0.01)
    assert all(h.inicio == (0, 0, 2.0) and h.fin[2] == pytest.approx(2.0) for h in m.hilos[1:])     # radiales horizontales


def test_validaciones():
    with pytest.raises(ValueError):
        G.vertical_hf(7.1, 3.0, radiales=1)
    with pytest.raises(ValueError):
        G.vertical_hf(7.1, 3.0, suelo="roca")
    with pytest.raises(ValueError):
        disenar("vertical_hf", 7.1, 3.0, ajustar=False, relacion=49)
    d = disenar("vertical_hf", 7.1, 3.0, ajustar=False)
    assert d.geometria["altura_mm"] == 2000.0 and d.estado == "Sin validar"


@pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")
def test_ajuste_da_buena_roe():
    d = disenar("vertical_hf", 7.1, 3.0)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.5 and 30 < r["r_ohm"] < 60
    assert -3.0 < r["ganancia_dBi"] < 3.0                      # sobre suelo normal pierde en el suelo: sin ser una locura


def test_el_plano_lleva_radiales_y_lista_de_corte():
    from wire import planos
    d = disenar("vertical_hf", 7.1, 3.0, ajustar=False)
    textos = [p.texto for h in planos.generar(d).hojas for p in h.primitivas() if hasattr(p, "texto")]
    assert any("Radial" in t for t in textos) and any("Radiador" in t for t in textos)
