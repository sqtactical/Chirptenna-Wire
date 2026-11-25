"""Patrón del coaxial a 1:1 (CoCo y antenas de coaxial): medidas, escala y reparto en hojas."""

import pytest

from wire import planos
from wire.diseno import disenar
from wire.planos import patron
from wire.planos.hoja import Rect


def _rects(prims, etiqueta):
    return [p for p in prims if isinstance(p, Rect) and p.etiqueta == etiqueta]


def test_el_patron_del_tramo_mide_lo_que_dice_la_lista_de_corte():
    d = disenar("coco", 145.0, 2.0, ajustar=False)
    g = d.geometria
    trozos = [("vivo", patron.VIVO), ("dielectrico", patron.DIELECTRICO_MM), ("malla", patron.MALLA),
              ("cubierta", g["tramo_mm"] + d.sobrante_mm - 2 * (patron.VIVO + patron.DIELECTRICO_MM + patron.MALLA)),
              ("malla", patron.MALLA), ("dielectrico", patron.DIELECTRICO_MM), ("vivo", patron.VIVO)]
    prims, ancho, alto = patron.plantilla_coaxial(d, trozos, g["tramo_mm"], d.sobrante_mm)
    cubierta = _rects(prims, "plantilla:coax_cubierta")[0]
    assert cubierta.alto == pytest.approx(4.95)                      # el diámetro del RG-58, a 1:1
    mallas = _rects(prims, "plantilla:coax_malla")
    assert len(mallas) == 2 and mallas[0].ancho == pytest.approx(patron.MALLA)
    extremo_izq = min(p.x for p in prims if isinstance(p, Rect))
    extremo_der = max(p.x + p.ancho for p in prims if isinstance(p, Rect))
    assert extremo_der - extremo_izq == pytest.approx(g["tramo_mm"] + d.sobrante_mm)     # «cortar a»


def test_la_coco_lleva_los_patrones_del_tramo_y_de_la_punta_a_partir_de_la_hoja_3():
    d = disenar("coco", 433.92, 2.0, ajustar=False)
    p = planos.generar(d, fecha="x")
    titulos = [h.titulo for h in p.hojas]
    assert "tramo" in titulos[2] and any("punta" in t for t in titulos[3:])
    assert all(h.escala.startswith("1:1") for h in p.hojas[2:])
    # El patrón largo se reparte en más hojas que el corto.
    largo = planos.generar(disenar("coco", 145.0, 2.0, ajustar=False), fecha="x")
    assert len(largo.hojas) > len(p.hojas)


def test_la_manga_lleva_el_patron_del_extremo_del_cable():
    p = planos.generar(disenar("manga", 145.0, 2.0, ajustar=False), fecha="x")
    assert len(p.hojas) > 1 and "extremo del cable" in p.hojas[1].titulo
    assert all(h.escala.startswith("1:1") for h in p.hojas[1:])


def test_el_patron_se_traduce():
    d = disenar("coco", 433.92, 2.0, ajustar=False, idioma="en")
    p = planos.generar(d, fecha="x")
    assert "Coax section template" in p.hojas[2].titulo
