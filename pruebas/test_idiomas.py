"""Idiomas: los catálogos están completos, los planos salen en cada idioma sin pisarse y el castellano no cambia."""

import json
import os
import subprocess
import sys

import pytest

from wire import i18n, planos, web_api
from wire.diseno import disenar
from wire.planos.hoja import Texto, se_solapan

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODIGOS = ("en", "fr", "de")


def _herramienta():
    sys.path.insert(0, os.path.join(RAIZ, "herramientas"))
    try:
        import i18n as herramienta
        return herramienta
    finally:
        sys.path.pop(0)


@pytest.mark.parametrize("codigo", CODIGOS)
def test_no_falta_ninguna_traduccion(codigo):
    h = _herramienta()
    assert h.faltan(codigo) == []
    assert h.sobran(codigo) == []


@pytest.mark.parametrize("codigo", CODIGOS)
def test_las_traducciones_conservan_marcas_y_saltos(codigo):
    import re
    for clave, texto in i18n.catalogo(codigo).items():
        assert sorted(re.findall(r"\{\d+[^}]*\}", clave)) == sorted(re.findall(r"\{\d+[^}]*\}", texto)), clave
        assert clave.count("\n") == texto.count("\n"), clave
    assert i18n.catalogo(codigo)  # no vacío


DISENOS = {
    "dipolo": lambda i: disenar("dipolo", 145.0, 2.0, ajustar=False, idioma=i),
    "jpole": lambda i: disenar("jpole", 435.0, 2.0, ajustar=False, idioma=i),
    "manga": lambda i: disenar("manga", 145.0, 2.0, ajustar=False, idioma=i),
    "coco": lambda i: disenar("coco", 145.0, 2.0, ajustar=False, idioma=i),
}


@pytest.mark.parametrize("codigo", CODIGOS)
@pytest.mark.parametrize("tipo", sorted(DISENOS))
def test_planos_en_cada_idioma_sin_textos_pisados(tipo, codigo):
    plano = planos.generar(DISENOS[tipo](codigo), fecha="25-11-2026")
    for hoja in plano.hojas:
        textos = [p for p in hoja.primitivas() if isinstance(p, Texto) and p.texto.strip()]
        for t in textos:
            if getattr(t, "etiqueta", "") != "cajetin":
                assert not se_solapan(t.caja, hoja.cajetin), f"«{t.texto}» pisa el cajetín"
            x0, y0, x1, y1 = hoja.marco
            c = t.caja
            assert c[0] >= x0 - 0.01 and c[2] <= x1 + 0.01, f"«{t.texto}» se sale del marco"
        for i, a in enumerate(textos):
            for b in textos[i + 1:]:
                assert not se_solapan(a.caja, b.caja, holgura=0.3), f"«{a.texto}» pisa «{b.texto}»"


def test_el_plano_en_otro_idioma_cambia_los_textos_y_no_la_geometria():
    es = planos.descripcion(planos.generar(DISENOS["jpole"]("es"), fecha="25-11-2026"))
    en = planos.descripcion(planos.generar(DISENOS["jpole"]("en"), fecha="25-11-2026"))
    textos = lambda d: [p["texto"] for h in d for p in h["primitivas"] if p["tipo"] == "Texto"]  # noqa: E731
    assert textos(es) != textos(en)
    assert any("Cut list".lower() in t.lower() or "CUT LIST" in t for t in textos(en))
    forma = lambda d: [(p["tipo"], p.get("etiqueta", "")) for h in d for p in h["primitivas"]]  # noqa: E731
    assert forma(es) == forma(en)


def test_el_decimal_depende_del_idioma():
    cotas = lambda i: " ".join(t.texto for h in planos.generar(DISENOS["dipolo"](i), fecha="25-11-2026").hojas  # noqa: E731
                               for t in h.primitivas() if isinstance(t, Texto))
    assert "Ø 2.0 mm" in cotas("en") and "· 145 MHz" in cotas("en")
    assert "Ø 2,0 mm" in cotas("es") and "Ø 2,0 mm" in cotas("fr") and "Ø 2,0 mm" in cotas("de")


def test_el_estado_de_la_cabecera_se_traduce():
    textos = " ".join(t.texto for h in planos.generar(DISENOS["dipolo"]("en"), fecha="25-11-2026").hojas
                      for t in h.primitivas() if isinstance(t, Texto))
    assert "UNVALIDATED" in textos and "SIN VALIDAR" not in textos


def test_la_api_traduce_el_catalogo_y_el_plano():
    c = json.loads(web_api.catalogo("de"))
    assert [t["nombre"] for t in c["tipos"]][0] == "Halbwellendipol"
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "dipolo", "f_MHz": 145, "idioma": "fr"})))
    assert "LISTE DE COUPE" in r["hojas"][0]
    assert r["diseno"]["plano"]["idioma"] == "fr"
    # Un diseno.json de escritorio (en castellano) se ve en el idioma pedido.
    en = json.loads(web_api.plano_svg(json.dumps({"diseno": r["diseno"], "idioma": "en"})))
    assert "CUT LIST" in en["hojas"][0]


def test_cli_idioma(tmp_path):
    svg = tmp_path / "d.svg"
    r = subprocess.run([sys.executable, "-m", "wire", "plano", "dipolo", "145", "--sin-motor", "--idioma", "de",
                        "--salida", str(svg)], cwd=RAIZ, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    assert "ZUSCHNITTLISTE" in svg.read_text(encoding="utf-8")
