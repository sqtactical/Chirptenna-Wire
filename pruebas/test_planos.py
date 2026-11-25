"""Generador de planos: escala, plantillas 1:1, cajetín, salidas SVG/PDF y configuración. No necesita PyNEC."""

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zlib

import pytest

from wire import planos
from wire.__main__ import main
from wire.diseno import ConfigPlano, Diseno, disenar
from wire.planos.comun import REGLA_MM
from wire.planos.hoja import Linea, Rect, Texto, dentro, se_solapan

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EJEMPLOS = os.path.join(RAIZ, "docs", "ejemplos")
PT_POR_MM = 72 / 25.4


def _ejemplo(nombre):
    with open(os.path.join(EJEMPLOS, nombre), encoding="utf-8") as f:
        return Diseno.desde_json(f.read())


DISENOS = {
    "dipolo_145": lambda: _ejemplo("dipolo_145.json"),
    "jpole_145": lambda: _ejemplo("jpole_145.json"),
    "jpole_435": lambda: _ejemplo("jpole_435.json"),
    "manga_145": lambda: _ejemplo("manga_145.json"),
    "coco_145": lambda: _ejemplo("coco_145.json"),
    "jpole_koch_434": lambda: _ejemplo("jpole_koch_434.json"),
    "discone_145": lambda: _ejemplo("discone_145.json"),
    "jpole_koch_868_sin_motor": lambda: disenar("jpole_koch", 868.0, 1.5, ajustar=False),
    "gp_145_N": lambda: disenar("gp", 145.0, 3.0, ajustar=False, conector="N"),
    "vinv_145": lambda: disenar("vinv", 145.0, 3.0, ajustar=False),
    "yagi_145": lambda: disenar("yagi", 145.0, 3.0, ajustar=False),
    "biconica_145": lambda: disenar("biconica", 145.0, 3.0, ajustar=False),
    "coco_sin_motor_vf_medido": lambda: disenar("coco", 433.0, 2.0, ajustar=False, cable="RG-316", vf_medido=0.7),
    "jpole_868_sin_motor": lambda: disenar("jpole", 868.0, 1.5, ajustar=False),
    "dipolo_pulgadas": lambda: disenar("dipolo", 433.0, 2.0, ajustar=False, unidades="pulgadas"),
}


@pytest.fixture(params=sorted(DISENOS))
def plano(request):
    return planos.generar(DISENOS[request.param](), fecha="25-11-2026")


def _por_etiqueta(hoja, etiqueta):
    return [p for p in hoja.primitivas() if getattr(p, "etiqueta", "") == etiqueta]


# ---------------------------------------------------------------- escala

def test_regla_mide_80_mm_en_la_descripcion(plano):
    for hoja in plano.hojas:
        barras = _por_etiqueta(hoja, "regla:barra")
        if hoja.escala.startswith("Sin escala"):
            assert not barras
        else:
            assert len(barras) == 1 and barras[0].ancho == REGLA_MM


def test_regla_mide_80_mm_en_el_pdf():
    datos = planos.a_pdf(planos.generar(_ejemplo("dipolo_145.json"), fecha="25-11-2026"), comprimir=False)
    texto = datos.decode("latin-1")
    assert "/MediaBox [0 0 595.28 841.89]" in texto  # A4 exacto, en puntos
    rects = [tuple(float(v) for v in m) for m in re.findall(r"([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) re", texto)]
    barra = [r for r in rects if abs(r[2] - REGLA_MM * PT_POR_MM) < 0.02]
    assert barra, "no está la barra de la regla"
    assert abs(abs(barra[0][3]) - 0.8 * PT_POR_MM) < 0.02
    cuadro = [r for r in rects if abs(r[2] - 20 * PT_POR_MM) < 0.02 and abs(abs(r[3]) - 7 * PT_POR_MM) < 0.02]
    assert cuadro
    # El detalle 1:1 del centro: el aislador de 60 × 25 mm y los brazos del diámetro real, también en el PDF.
    aislador = [r for r in rects if abs(r[2] - 60 * PT_POR_MM) < 0.02 and abs(abs(r[3]) - 25 * PT_POR_MM) < 0.02]
    assert len(aislador) == 1
    brazos = [r for r in rects if abs(abs(r[3]) - 2.0 * PT_POR_MM) < 0.02 and r[2] > 40 * PT_POR_MM]
    assert len(brazos) == 2  # diámetro 2 mm
    izq, der = sorted(brazos, key=lambda r: r[0])
    assert (der[0] - (izq[0] + izq[2])) / PT_POR_MM == pytest.approx(10.0, abs=0.01)  # hueco del aislador


def test_pdf_comprimido_tiene_todas_las_paginas():
    datos = planos.a_pdf(planos.generar(_ejemplo("jpole_435.json"), fecha="25-11-2026"))
    assert datos.startswith(b"%PDF")
    assert len(re.findall(rb"/Type\s*/Page[^s]", datos)) == 2
    assert b"/MediaBox [0 0 841.89 595.28]" in datos  # el detalle de 70 cm va en A4 apaisada


# ---------------------------------------------------------------- plantillas 1:1 frente al modelo

def test_plantilla_jpole_coincide_con_la_geometria():
    for nombre in ("jpole_145.json", "jpole_435.json"):
        d = _ejemplo(nombre)
        g = d.geometria
        hoja = planos.generar(d).hojas[1]
        largo, = _por_etiqueta(hoja, "plantilla:eje_largo")
        corto, = _por_etiqueta(hoja, "plantilla:eje_corto")
        u, = _por_etiqueta(hoja, "plantilla:eje_u")
        toma, = _por_etiqueta(hoja, "plantilla:toma")
        assert corto.y1 - largo.y1 == pytest.approx(g["separacion_mm"])
        assert u.longitud == pytest.approx(g["separacion_mm"])
        assert toma.x1 - u.x1 == pytest.approx(g["toma_mm"])
        assert largo.x1 == corto.x1 == u.x1
        # Lo que sí se corta en el modelo: el brazo corto de NEC mide lo mismo que la plantilla cuando cabe.
        modelo = d.modelo()
        corto_modelo = (modelo.hilos[3].longitud + modelo.hilos[4].longitud) * 1000
        assert corto_modelo == pytest.approx(g["corto_mm"])
        if nombre == "jpole_435.json":
            assert hoja.apaisada and corto.longitud == pytest.approx(g["corto_mm"])
        else:
            assert corto.longitud < g["corto_mm"]  # 2 m: solo el fondo de la U y la toma
        # El alambre se dibuja con su diámetro real.
        cobre = [p for p in hoja.primitivas() if isinstance(p, Rect) and p.relleno and p.alto == d.diametro_mm]
        assert cobre


def test_plantilla_dipolo_hueco_y_diametro():
    d = _ejemplo("dipolo_145.json")
    hoja = planos.generar(d).hojas[0]
    izq, = _por_etiqueta(hoja, "plantilla:brazo_izq")
    der, = _por_etiqueta(hoja, "plantilla:brazo_der")
    assert der.x - (izq.x + izq.ancho) == pytest.approx(10.0)
    assert izq.alto == der.alto == pytest.approx(d.diametro_mm)
    aislador, = _por_etiqueta(hoja, "plantilla:aislador")
    assert (aislador.ancho, aislador.alto) == (60.0, 25.0)
    t1, t2 = _por_etiqueta(hoja, "plantilla:taladro")
    assert abs(t2.cx - t1.cx) == pytest.approx(28.0)


# ---------------------------------------------------------------- composición

def test_ningun_texto_pisa_el_cajetin_ni_se_sale(plano):
    for hoja in plano.hojas:
        assert hoja.cajetin is not None
        for p in hoja.primitivas():
            if getattr(p, "etiqueta", "") == "cajetin":
                assert dentro(p.caja, hoja.cajetin)
                continue
            if isinstance(p, Texto):
                assert not se_solapan(p.caja, hoja.cajetin), f"«{p.texto}» pisa el cajetín"
            if isinstance(p, Texto) or isinstance(p, Linea):
                x0, y0, x1, y1 = hoja.marco
                c = p.caja
                assert c[0] >= x0 - 0.01 and c[1] >= y0 - 0.01 and c[2] <= x1 + 0.01 and c[3] <= y1 + 0.01, \
                    f"{p} se sale del marco"


def test_textos_no_se_pisan_entre_si(plano):
    for hoja in plano.hojas:
        textos = [p for p in hoja.primitivas() if isinstance(p, Texto) and p.texto.strip()]
        for i, a in enumerate(textos):
            for b in textos[i + 1:]:
                assert not se_solapan(a.caja, b.caja, holgura=0.3), f"«{a.texto}» pisa «{b.texto}»"


def test_cajetin_completo(plano):
    for n, hoja in enumerate(plano.hojas, start=1):
        textos = " ".join(p.texto for p in _por_etiqueta(hoja, "cajetin") if isinstance(p, Texto))
        for clave in ("Diseño", "Frecuencia", "Escala", "Estado", "Licencia", "CC BY-NC 4.0", "Chirptenna Wire",
                      f"{n} de {len(plano.hojas)}"):
            assert clave in textos
        assert any(type(p).__name__ == "Imagen" for p in hoja.primitivas())


def test_svg_bien_formado(plano):
    for hoja in plano.hojas:
        raiz = ET.fromstring(planos.a_svg(hoja))
        ancho, alto = hoja.tamano
        assert raiz.get("width") == f"{ancho:g}mm" and raiz.get("viewBox") == f"0 0 {ancho:g} {alto:g}"


def test_pulgadas_solo_cambian_las_cotas():
    mm = planos.generar(disenar("dipolo", 433.0, 2.0, ajustar=False), fecha="x")
    pulgadas = planos.generar(disenar("dipolo", 433.0, 2.0, ajustar=False, unidades="pulgadas"), fecha="x")
    izq_mm, = _por_etiqueta(mm.hojas[0], "plantilla:brazo_izq")
    izq_in, = _por_etiqueta(pulgadas.hojas[0], "plantilla:brazo_izq")
    assert izq_mm == izq_in
    assert any(" in" in p.texto for p in pulgadas.hojas[0].primitivas() if isinstance(p, Texto))


# ---------------------------------------------------------------- mismo plano con y sin PyNEC

def test_misma_descripcion_sin_pynec():
    """El generador no depende del motor: bloqueando PyNEC sale la misma descripción vectorial."""
    codigo = (
        "import sys, json; sys.modules['PyNEC'] = None\n"
        "from wire import planos; from wire.diseno import Diseno\n"
        "d = Diseno.desde_json(open(sys.argv[1], encoding='utf-8').read())\n"
        "print(json.dumps(planos.descripcion(planos.generar(d, fecha='25-11-2026'))))\n"
    )
    for nombre in ("dipolo_145.json", "jpole_145.json"):
        ruta = os.path.join(EJEMPLOS, nombre)
        salida = subprocess.run([sys.executable, "-c", codigo, ruta], cwd=RAIZ, capture_output=True, text=True,
                                check=True, encoding="utf-8").stdout
        local = planos.descripcion(planos.generar(_ejemplo(nombre), fecha="25-11-2026"))
        assert json.loads(salida) == json.loads(json.dumps(local))


# ---------------------------------------------------------------- configuración y paginación

def test_diseno_json_ida_y_vuelta():
    d = _ejemplo("jpole_145.json")
    assert Diseno.desde_json(d.a_json()) == d
    # Un plano generado desde el JSON es igual al del diseño original (W1.5).
    original = planos.descripcion(planos.generar(d, fecha="25-11-2026"))
    desde_json = planos.descripcion(planos.generar(Diseno.desde_json(d.a_json()), fecha="25-11-2026"))
    assert desde_json == original
    datos = json.loads(d.a_json())
    assert set(datos["plano"]) == {"papel", "grandes", "orientacion", "solape_mm", "unidades", "idioma",
                                   "sobrante_mm"}


def test_config_plano_valida():
    assert ConfigPlano.desde_dict(None) == ConfigPlano()
    for malo in ({"papel": "A5"}, {"grandes": "rollo"}, {"solape_mm": 30}, {"otra": 1}, {"unidades": "cm"}):
        with pytest.raises(ValueError):
            ConfigPlano.desde_dict(malo)


def test_decidir_papel():
    c = ConfigPlano()
    assert planos.decidir_papel(150, 100, c)["modo"] == "hoja"
    apaisada = planos.decidir_papel(240, 60, c)
    assert apaisada["modo"] == "hoja" and apaisada["apaisada"]
    assert planos.decidir_papel(240, 60, ConfigPlano(orientacion="vertical"))["modo"] == "mosaico"
    assert planos.decidir_papel(350, 150, ConfigPlano(grandes="A3"))["modo"] == "A3"
    mosaico = planos.decidir_papel(400, 300, c)
    assert mosaico["modo"] == "mosaico" and mosaico["hojas"] == (3, 2)
    assert planos.decidir_papel(4000, 60, c)["modo"] == "sin_escala"  # más de 12 hojas: mejor sin escala


# ---------------------------------------------------------------- línea de comandos

def test_cli_plano_pdf_y_svg(tmp_path):
    pdf = tmp_path / "jpole.pdf"
    assert main(["plano", "jpole", "435", "--diametro", "2", "--sin-motor", "--salida", str(pdf),
                 "--guardar", str(tmp_path / "d.json")]) == 0
    assert pdf.read_bytes().startswith(b"%PDF")
    d = Diseno.desde_json((tmp_path / "d.json").read_text(encoding="utf-8"))
    assert d.estado == "Sin validar" and d.resultados is None
    assert main(["plano", "--desde", str(tmp_path / "d.json"), "--salida", str(tmp_path / "p.svg")]) == 0
    assert (tmp_path / "p_1.svg").exists() and (tmp_path / "p_2.svg").exists()
    assert main(["nec", "--desde", str(tmp_path / "d.json"), "--salida", str(tmp_path / "j.nec")]) == 0
    assert (tmp_path / "j.nec").read_text(encoding="ascii").endswith("EN\n")
