"""Salida SVG de una hoja (vista previa y descarga). Unidades del SVG = mm del papel."""

from __future__ import annotations

import base64
import re
from functools import lru_cache
from xml.sax.saxutils import escape

from .hoja import PT, Arco, Circulo, Hoja, Imagen, Linea, Polilinea, Rect, Texto, recurso

FAMILIA = "'DejaVu Sans', Verdana, sans-serif"


def _n(x: float) -> str:
    return f"{x:.3f}".rstrip("0").rstrip(".")


def _trazo(color, grosor, discontinua=None) -> str:
    if color is None:
        return 'stroke="none"'
    s = f'stroke="{color}" stroke-width="{_n(grosor)}"'
    if discontinua:
        s += f' stroke-dasharray="{_n(discontinua[0])} {_n(discontinua[1])}"'
    return s


@lru_cache(maxsize=None)
def _imagen_datos(nombre: str) -> str:
    datos = recurso(nombre)
    if nombre.endswith(".svg"):
        datos = re.sub(rb"<metadata>.*?</metadata>", b"", datos, flags=re.S)
        return "data:image/svg+xml;base64," + base64.b64encode(datos).decode("ascii")
    return "data:image/png;base64," + base64.b64encode(datos).decode("ascii")


def _texto(t: Texto) -> list[str]:
    out = []
    alto = t.tam * PT
    if t.fondo:
        x0, y0, x1, y1 = t.caja
        out.append(f'<rect x="{_n(x0 - 0.4)}" y="{_n(y0 - 0.3)}" width="{_n(x1 - x0 + 0.8)}" '
                   f'height="{_n(y1 - y0 + 0.6)}" fill="{t.fondo}"/>')
    ancla = {"izquierda": "start", "centro": "middle", "derecha": "end"}[t.ancla]
    peso = ' font-weight="bold"' if t.estilo == "negrita" else ""
    cursiva = ' font-style="oblique"' if t.estilo == "cursiva" else ""
    giro = f' transform="rotate({_n(-t.rotacion)} {_n(t.x)} {_n(t.y)})"' if t.rotacion else ""
    for i, linea in enumerate(t.lineas):
        y = t.y + i * Texto.INTERLINEA * alto
        out.append(f'<text x="{_n(t.x)}" y="{_n(y)}" font-size="{_n(alto)}" fill="{t.color}" '
                   f'text-anchor="{ancla}"{peso}{cursiva}{giro}>{escape(linea)}</text>')
    return out


def a_svg(hoja: Hoja) -> str:
    ancho, alto = hoja.tamano
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_n(ancho)}mm" height="{_n(alto)}mm" '
        f'viewBox="0 0 {_n(ancho)} {_n(alto)}" font-family="{FAMILIA}">',
        f'<rect width="{_n(ancho)}" height="{_n(alto)}" fill="#ffffff"/>',
    ]
    for p in hoja.primitivas():
        if isinstance(p, Linea):
            out.append(f'<line x1="{_n(p.x1)}" y1="{_n(p.y1)}" x2="{_n(p.x2)}" y2="{_n(p.y2)}" '
                       f'{_trazo(p.color, p.grosor, p.discontinua)} stroke-linecap="butt"/>')
        elif isinstance(p, (Polilinea, Arco)):
            puntos = p.puntos() if isinstance(p, Arco) else p.puntos
            pts = " ".join(f"{_n(x)},{_n(y)}" for x, y in puntos)
            cerrada = isinstance(p, Polilinea) and p.cerrada
            relleno = p.relleno if isinstance(p, Polilinea) and p.relleno else "none"
            etiqueta = "polygon" if cerrada else "polyline"
            out.append(f'<{etiqueta} points="{pts}" fill="{relleno}" {_trazo(p.color, p.grosor)} '
                       f'stroke-linejoin="round"/>')
        elif isinstance(p, Rect):
            out.append(f'<rect x="{_n(p.x)}" y="{_n(p.y)}" width="{_n(p.ancho)}" height="{_n(p.alto)}" '
                       f'fill="{p.relleno or "none"}" {_trazo(p.color, p.grosor)}/>')
        elif isinstance(p, Circulo):
            out.append(f'<circle cx="{_n(p.cx)}" cy="{_n(p.cy)}" r="{_n(p.r)}" fill="{p.relleno or "none"}" '
                       f'{_trazo(p.color, p.grosor, p.discontinua)}/>')
        elif isinstance(p, Texto):
            out.extend(_texto(p))
        elif isinstance(p, Imagen):
            out.append(f'<image x="{_n(p.x)}" y="{_n(p.y)}" width="{_n(p.ancho)}" height="{_n(p.alto)}" '
                       f'href="{_imagen_datos(p.recurso)}"/>')
        else:
            raise TypeError(f"primitiva desconocida: {type(p).__name__}")
    out.append("</svg>")
    return "\n".join(out) + "\n"
