"""Ganancia teórica de cada diseño: tabla, texto, cajetín y web."""

import json

import pytest

from wire import ganancias, planos, web_api
from wire.diseno import TIPOS, disenar
from wire.planos.comun import fmt


def test_tabla_cubre_todos_los_tipos():
    t = ganancias.tabla()
    assert set(t) == set(TIPOS)
    assert t["abanico"] is None and t["dipolo"] == pytest.approx(2.1, abs=0.1)
    assert sorted(t["yagi"], key=int) == [str(n) for n in range(3, 16)]
    assert sorted(t["colineal"], key=int) == ["2", "3", "4", "5", "6"]


def test_la_colineal_gana_con_cada_seccion():
    g = [ganancias.valores(disenar("colineal", 433.0, 2.0, ajustar=False, elementos=n))[0][0] for n in range(2, 7)]
    assert g == sorted(g) and g[-1] >= 6.5


def test_textos():
    d = disenar("yagi", 145.0, 2.0, ajustar=False, elementos=5)
    assert ganancias.texto(d, fmt) == "10,2 dBi · referencia simulada"
    b = disenar("colineal_bibanda", 145.0, 3.0, ajustar=False, elementos=4)
    assert "4,7 dBi en 433 MHz" in ganancias.texto(b, fmt)
    assert ganancias.texto(disenar("abanico", 7.1, 2.0, ajustar=False), fmt) is None


def test_la_simulacion_del_diseno_manda_sobre_la_tabla():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    d.resultados = {"ganancia_dBi": 2.14}
    assert ganancias.texto(d, fmt) == "2,1 dBi · simulada"


def test_cajetin_y_catalogo_llevan_la_ganancia():
    d = disenar("colineal", 433.0, 2.0, ajustar=False, elementos=6)
    textos = [p.texto for h in planos.generar(d).hojas for p in h.primitivas() if hasattr(p, "texto")]
    assert "Ganancia" in textos and any(t.startswith("6,7 dBi") for t in textos)
    cat = {t["clave"]: t for t in json.loads(web_api.catalogo())["tipos"]}
    assert cat["yagi"]["ganancia"] == "8,7–13,6 dBi" and cat["abanico"]["ganancia"] is None
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "gp", "f_MHz": 145, "diametro_mm": 3})))
    assert r["ganancia"] == "2,2 dBi · referencia simulada"
