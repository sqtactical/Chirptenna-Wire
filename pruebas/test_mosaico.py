"""W4.3: mosaico de A4, A3 y marcas de registro."""

import math

import pytest

from wire import planos
from wire.diseno import ConfigPlano, disenar
from wire.planos import paginacion as pg
from wire.planos.hoja import Circulo, Linea, Rect, Texto, se_solapan


def _plano(f=433.92, **cfg):
    return planos.generar(disenar("jpole_koch", f, 2.0, ajustar=False, **cfg), fecha="25-11-2026")


def _hilos(hoja):
    return [p for p in hoja.primitivas() if isinstance(p, Linea) and p.etiqueta.startswith("plantilla:")]


def test_433_sale_en_mosaico_de_dos_hojas_y_la_primera_es_el_resumen():
    p = _plano()
    assert len(p.hojas) == 3
    assert p.hojas[1].titulo == p.hojas[2].titulo
    etiquetas = [t.texto for h in p.hojas[1:] for t in h.primitivas() if isinstance(t, Texto) and t.tam == 12 and t.texto in ("A1", "B1")]
    assert etiquetas == ["A1", "B1"]


def test_el_mosaico_cubre_la_plantilla_sin_huecos_ni_hojas_de_mas():
    d = disenar("jpole_koch", 145.0, 2.0, ajustar=False)
    from wire.planos import koch
    prims, ancho, alto = koch.plantilla(d)
    dec = pg.decidir_papel(ancho, alto, d.plano)
    columnas, filas = dec["hojas"]
    w, h = pg.area_util("A4", dec["apaisada"])
    paso_x, paso_y = w - d.plano.solape_mm, h - d.plano.solape_mm
    assert (columnas - 1) * paso_x + w >= ancho and (filas - 1) * paso_y + h >= alto
    assert (columnas - 2) * paso_x + w < ancho or columnas == 1
    assert (filas - 2) * paso_y + h < alto or filas == 1


def test_todo_el_alambre_sale_en_alguna_hoja_a_1_a_1():
    """Puntos del alambre de la plantilla, uno cada 4 mm: cada uno cae sobre un trazo de alguna hoja del mosaico."""
    d = disenar("jpole_koch", 145.0, 2.0, ajustar=False)
    from wire.planos import koch
    prims, ancho, alto = koch.plantilla(d)
    plano = planos.generar(d, fecha="x")
    dec = pg.decidir_papel(ancho, alto, d.plano)
    w, h = pg.area_util("A4", dec["apaisada"])
    columnas, filas = dec["hojas"]
    solape = d.plano.solape_mm
    faltan = 0
    for p in prims:
        if not isinstance(p, pg.Polilinea):
            continue
        for a, b in zip(p.puntos, p.puntos[1:]):
            n = max(1, int(math.dist(a, b) // 4))
            for k in range(n + 1):
                x, y = a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n
                c, r = min(columnas - 1, int(x // (w - solape))), min(filas - 1, int(y // (h - solape)))
                hoja = plano.hojas[1 + r * columnas + c]
                xs, ys = x - c * (w - solape) + pg.MARGEN, y - r * (h - solape) + pg.MARGEN + pg.CABECERA
                if not any(_dist(xs, ys, l) < 0.3 for l in _hilos(hoja)):
                    faltan += 1
    assert faltan == 0


def _dist(x, y, l: Linea) -> float:
    dx, dy = l.x2 - l.x1, l.y2 - l.y1
    n2 = dx * dx + dy * dy
    t = 0.0 if n2 == 0 else max(0.0, min(1.0, ((x - l.x1) * dx + (y - l.y1) * dy) / n2))
    return math.hypot(x - l.x1 - t * dx, y - l.y1 - t * dy)


@pytest.mark.parametrize("f", [145.0, 433.92])
def test_las_marcas_de_registro_no_pisan_el_alambre(f):
    p = _plano(f)
    for hoja in p.hojas[1:]:
        hilos = _hilos(hoja)
        for c in hoja.primitivas():
            if isinstance(c, Circulo) and c.etiqueta == "registro":
                assert all(_dist(c.cx, c.cy, l) > l.grosor / 2 + 3 for l in hilos)


def test_las_marcas_coinciden_en_hojas_vecinas():
    """Cada marca de una franja de solape aparece, en la misma posición de la plantilla, en las dos hojas que la comparten."""
    p = _plano(145.0)
    d = disenar("jpole_koch", 145.0, 2.0, ajustar=False)
    from wire.planos import koch
    prims, ancho, alto = koch.plantilla(d)
    dec = pg.decidir_papel(ancho, alto, d.plano)
    w, h = pg.area_util("A4", dec["apaisada"])
    columnas, filas = dec["hojas"]
    marcas = pg.marcas_registro(ancho, alto, columnas, filas, w - 10, h - 10, 10, prims, 2.0)
    for x, y in marcas:
        en = 0
        for r in range(filas):
            for c in range(columnas):
                x0, y0 = c * (w - 10), r * (h - 10)
                if x0 + 3 <= x <= x0 + w - 3 and y0 + 3 <= y <= y0 + h - 3:
                    hoja = p.hojas[1 + r * columnas + c]
                    xs, ys = x - x0 + pg.MARGEN, y - y0 + pg.MARGEN + pg.CABECERA
                    assert any(abs(q.cx - xs) < 1e-6 and abs(q.cy - ys) < 1e-6 for q in hoja.primitivas()
                               if isinstance(q, Circulo) and q.etiqueta == "registro")
                    en += 1
        assert en >= 1


def test_a3_cuando_no_cabe_en_a4_pero_si_en_a3():
    d = disenar("jpole", 145.0, 2.0, ajustar=False)
    cfg = ConfigPlano(grandes="A3")
    dec = pg.decidir_papel(250.0, 300.0, cfg)
    assert dec["modo"] == "A3" and dec["papel"] == "A3"
    prims = [Linea(10, 10, 240, 290, "#000000", 2.0, None, "plantilla:x")]
    hojas, _ = pg.hojas_plantilla(d, "t", "s", prims, 250.0, 300.0, dec)
    assert len(hojas) == 1 and hojas[0].papel == "A3" and hojas[0].tamano == (297.0, 420.0)


def test_sin_escala_cuando_son_demasiadas_hojas():
    dec = pg.decidir_papel(4000.0, 60.0, ConfigPlano())
    assert dec["modo"] == "sin_escala"
    d = disenar("jpole", 145.0, 2.0, ajustar=False)
    assert pg.hojas_plantilla(d, "t", "s", [], 4000.0, 60.0, dec)[0] == []


def test_jpole_koch_con_papel_a3():
    p = planos.generar(disenar("jpole_koch", 868.0, 2.0, ajustar=False, grandes="A3"), fecha="x")
    assert all(h.papel in ("A4", "A3") for h in p.hojas)


def test_los_textos_de_las_hojas_del_mosaico_no_se_pisan():
    for h in _plano(145.0).hojas:
        textos = [t for t in h.primitivas() if isinstance(t, Texto) and t.texto.strip()]
        for i, a in enumerate(textos):
            for b in textos[i + 1:]:
                assert not se_solapan(a.caja, b.caja, holgura=0.3), (a.texto, b.texto)
