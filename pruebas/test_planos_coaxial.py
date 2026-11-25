"""W2.6: planos de las antenas de coaxial (manga y CoCo): cable y VF en el cajetín, tramos y pelados, pulgadas."""

import json
import os

import pytest

from wire import planos
from wire.diseno import Diseno, disenar
from wire.planos.hoja import Rect, Texto

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _textos(plano, etiqueta=None):
    return [p for h in plano.hojas for p in h.primitivas()
            if isinstance(p, Texto) and (etiqueta is None or p.etiqueta == etiqueta)]


def test_hojas_por_tipo():
    assert len(planos.generar(disenar("manga", 145.0, 2.0, ajustar=False)).hojas) == 1
    assert len(planos.generar(disenar("coco", 145.0, 2.0, ajustar=False)).hojas) == 2


@pytest.mark.parametrize("tipo", ["manga", "coco"])
def test_cajetin_con_cable_y_vf(tipo):
    d = disenar(tipo, 145.0, 2.0, ajustar=False)
    texto = " ".join(t.texto for t in _textos(planos.generar(d), "cajetin"))
    assert "RG-58" in texto and "VF 0,66 (catálogo)" in texto
    medido = disenar(tipo, 145.0, 2.0, ajustar=False, vf_medido=0.68)
    texto = " ".join(t.texto for t in _textos(planos.generar(medido), "cajetin"))
    assert "VF 0,68 (medido)" in texto
    # El aviso de VF de catálogo solo sale cuando es de catálogo.
    assert any("catálogo; el del cable" in t.texto for t in _textos(planos.generar(d)))
    assert not any("catálogo; el del cable" in t.texto for t in _textos(planos.generar(medido)))


def test_el_vf_medido_cambia_el_largo_de_los_tramos_de_la_coco():
    a = disenar("coco", 145.0, 2.0, ajustar=False)
    b = disenar("coco", 145.0, 2.0, ajustar=False, vf_medido=0.8)
    assert b.geometria["tramo_mm"] / a.geometria["tramo_mm"] == pytest.approx(0.8 / 0.66)
    # La longitud eléctrica (física / VF) es λ/2 en los dos.
    assert a.geometria["tramo_mm"] / 0.66 == pytest.approx(299792.458 / 145.0 / 2)


def test_pelado_a_escala_1_a_1_de_la_manga():
    d = disenar("manga", 145.0, 2.0, ajustar=False)
    hoja = planos.generar(d).hojas[0]
    pelado = {p.etiqueta: p for p in hoja.primitivas() if isinstance(p, Rect) and p.etiqueta.startswith("plantilla:")}
    assert pelado["plantilla:cubierta"].alto == pytest.approx(d.diametro_mm)
    assert pelado["plantilla:vivo"].alto == pytest.approx(0.9)


def test_diseno_coaxial_ida_y_vuelta_y_modelo():
    for tipo in ("manga", "coco"):
        d = disenar(tipo, 145.0, 2.0, ajustar=False, cable="RG-213")
        assert Diseno.desde_json(d.a_json()) == d
        assert d.cable["nombre"] == "RG-213" and d.material == "coaxial RG-213"
        assert d.modelo().hilos


def test_ejemplos_guardados_son_coherentes():
    for nombre in ("manga_145", "coco_145"):
        with open(os.path.join(RAIZ, "docs", "ejemplos", nombre + ".json"), encoding="utf-8") as f:
            d = Diseno.desde_json(f.read())
        assert d.estado == "Simulado" and d.resultados and d.cable["vf_origen"] == "catálogo"
        assert json.loads(d.a_json())["cable"]["nombre"] == "RG-58"
