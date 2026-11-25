"""Salida PDF con fpdf2 (Python puro; carga en Pyodide con micropip). Página del tamaño exacto del papel y todo en mm
reales, para que lo marcado «Escala 1:1» mida lo que dice al imprimir al 100 %.
"""

from __future__ import annotations

import io
import re
from functools import lru_cache

from .hoja import FUENTES, PT, Arco, Circulo, Imagen, Linea, Plano, Polilinea, Rect, Texto, recurso, ruta_recurso


def _rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


@lru_cache(maxsize=None)
def _imagen(nombre: str) -> bytes:
    datos = recurso(nombre)
    if nombre.endswith(".svg"):
        datos = re.sub(rb"<metadata>.*?</metadata>", b"", datos, flags=re.S)
    return datos


def _estilo(color, relleno) -> str | None:
    if color and relleno:
        return "DF"
    if relleno:
        return "F"
    if color:
        return "D"
    return None


def a_pdf(plano: Plano, comprimir: bool = True) -> bytes:
    from fpdf import FPDF

    pdf = FPDF(unit="mm")
    pdf.set_compression(comprimir)
    pdf.set_auto_page_break(False)
    pdf.set_margins(0, 0, 0)
    pdf.set_creator("Chirptenna Wire")
    pdf.set_title(plano.nombre)
    for estilo, archivo in FUENTES.items():
        pdf.add_font("DejaVu", {"normal": "", "negrita": "B", "cursiva": "I"}[estilo], ruta_recurso(archivo))

    for hoja in plano.hojas:
        pdf.add_page(format=hoja.tamano)
        for p in hoja.primitivas():
            _dibujar(pdf, p)
    return bytes(pdf.output())


def _preparar(pdf, color, grosor, relleno=None, discontinua=None):
    if color:
        pdf.set_draw_color(*_rgb(color))
        pdf.set_line_width(grosor)
    if relleno:
        pdf.set_fill_color(*_rgb(relleno))
    if discontinua:
        pdf.set_dash_pattern(dash=discontinua[0], gap=discontinua[1])
    else:
        pdf.set_dash_pattern()


def _dibujar(pdf, p) -> None:
    if isinstance(p, Linea):
        _preparar(pdf, p.color, p.grosor, discontinua=p.discontinua)
        pdf.line(p.x1, p.y1, p.x2, p.y2)
    elif isinstance(p, (Polilinea, Arco)):
        puntos = p.puntos() if isinstance(p, Arco) else p.puntos
        relleno = p.relleno if isinstance(p, Polilinea) else None
        _preparar(pdf, p.color, p.grosor, relleno)
        estilo = _estilo(p.color, relleno)
        if isinstance(p, Polilinea) and p.cerrada:
            pdf.polygon(list(puntos), style=estilo)
        else:
            pdf.polyline(list(puntos), style="D")
    elif isinstance(p, Rect):
        _preparar(pdf, p.color, p.grosor, p.relleno)
        pdf.rect(p.x, p.y, p.ancho, p.alto, style=_estilo(p.color, p.relleno))
    elif isinstance(p, Circulo):
        _preparar(pdf, p.color, p.grosor, p.relleno, p.discontinua)
        pdf.circle(x=p.cx, y=p.cy, radius=p.r, style=_estilo(p.color, p.relleno))
    elif isinstance(p, Texto):
        _texto(pdf, p)
    elif isinstance(p, Imagen):
        pdf.image(io.BytesIO(_imagen(p.recurso)), x=p.x, y=p.y, w=p.ancho, h=p.alto, keep_aspect_ratio=True)
    else:
        raise TypeError(f"primitiva desconocida: {type(p).__name__}")


def _texto(pdf, t: Texto) -> None:
    if t.fondo:
        x0, y0, x1, y1 = t.caja
        _preparar(pdf, None, 0, t.fondo)
        pdf.rect(x0 - 0.4, y0 - 0.3, x1 - x0 + 0.8, y1 - y0 + 0.6, style="F")
    pdf.set_font("DejaVu", {"normal": "", "negrita": "B", "cursiva": "I"}[t.estilo], size=t.tam)
    pdf.set_text_color(*_rgb(t.color))
    alto = t.tam * PT

    def escribir():
        for i, linea in enumerate(t.lineas):
            ancho = pdf.get_string_width(linea)
            x = t.x - {"izquierda": 0.0, "centro": ancho / 2, "derecha": ancho}[t.ancla]
            pdf.text(x, t.y + i * Texto.INTERLINEA * alto, linea)

    if t.rotacion:
        with pdf.rotation(angle=t.rotacion, x=t.x, y=t.y):
            escribir()
    else:
        escribir()
