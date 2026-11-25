"""Piezas comunes de las hojas: cabecera, secciones, cajetín, regla de comprobación, gráfica de ROE y formato."""

from __future__ import annotations

import math
from dataclasses import replace

from .. import __version__
from ..diseno import Diseno, banda_de
from ..i18n import separador_decimal, tr
from .hoja import (BLANCO, COBRE, GRIS, GRIS_CLARO, PT, ROJO, TINTA, VERDE, Hoja, Imagen, Linea, Polilinea, Rect,
                   Texto, ancho_texto)

URL = "github.com/sqtactical/Chirptenna-Wire"
LICENCIA = "CC BY-NC 4.0"
REGLA_MM = 80.0  # cabe junto al cajetín en A4 vertical


def fmt(v: float, decimales: int = 1) -> str:
    return f"{v:.{decimales}f}".replace(".", separador_decimal()).replace("-", "−")


def frecuencia(f_MHz: float) -> str:
    """145 → «145», 433,92 → «433,92»."""
    return fmt(f_MHz, 3).rstrip("0").rstrip(separador_decimal())


def longitud(mm: float, diseno: Diseno, decimales: int = 1) -> str:
    """Cota en las unidades del plano (la escala 1:1 no cambia, solo el texto)."""
    if diseno.plano.unidades == "pulgadas":
        return tr("{0} in", fmt(mm / 25.4, 2))
    return fmt(mm, decimales)


def unidad(diseno: Diseno) -> str:
    return tr("pulgadas") if diseno.plano.unidades == "pulgadas" else "mm"


def texto_banda(f_MHz: float) -> str:
    b = banda_de(f_MHz)
    return tr("banda {0}", tr(b[0])) if b else tr("fuera de las bandas iniciales")


def hoja_a4(diseno: Diseno, titulo: str, subtitulo: str, apaisada: bool = False) -> Hoja:
    """Hoja A4 con marco, cabecera y el hueco del cajetín abajo a la derecha (96 × 44 mm)."""
    ancho, alto = (297.0, 210.0) if apaisada else (210.0, 297.0)
    hoja = Hoja("A4", apaisada=apaisada, titulo=titulo, marco=(10.0, 10.0, ancho - 10, alto - 10),
                cajetin=(ancho - 106, alto - 54, ancho - 10, alto - 10))
    hoja.anadir(
        Rect(10, 10, ancho - 20, alto - 20, TINTA, 0.28),
        Texto(14, 19, titulo, 12, estilo="negrita"),
        Texto(14, 24.5, subtitulo, 7.5, GRIS),
        Linea(10, 27, ancho - 10, 27, TINTA, 0.18),
    )
    if diseno.estado != "Medido":
        hoja.anadir(Texto(ancho - 14, 18, tr(diseno.estado).upper(), 6, ROJO, "negrita", "derecha"))
    return hoja


def seccion(hoja: Hoja, x: float, y: float, titulo: str, subtitulo: str, color: str = GRIS) -> None:
    hoja.anadir(Texto(x, y, titulo, 7.5, estilo="negrita"), Texto(x, y + 4.5, subtitulo, 6.3, color, "cursiva"))


def cajetin(hoja: Hoja, diseno: Diseno, escala: str, n: int, total: int, fecha: str) -> None:
    x0, y0, x1, y1 = hoja.cajetin
    xl = x1 - 30  # columna del logo
    hoja.escala = escala
    elementos = [Rect(x0, y0, x1 - x0, y1 - y0, TINTA, 0.28), Rect(xl, y0, x1 - xl, y1 - y0, TINTA, 0.18),
                 Imagen(xl + 2, y0 + 2, 26, 33, etiqueta="cajetin"),
                 Texto((xl + x1) / 2, y1 - 3, tr("Chirptenna Wire"), 5.6, estilo="negrita", ancla="centro")]
    banda = banda_de(diseno.f_MHz)
    if diseno.cable:
        material = tr("Ø {0} mm · coaxial {1}", fmt(diseno.diametro_mm, 1), diseno.cable["nombre"])
    else:
        material = tr("Ø {0} mm · {1}", fmt(diseno.diametro_mm, 1), tr(diseno.material))
    estado = {"Simulado": tr("Simulado, sin medir"), "Medido": tr("Medido"), "Sin validar": tr("Sin validar")}[diseno.estado]
    campos = [
        (tr("Diseño"), diseno.nombre),
        (tr("Tipo"), diseno.nombre_tipo),
        (tr("Frecuencia"), tr("{0} MHz", frecuencia(diseno.f_MHz))
                       + (tr(" · {0} ({1}–{2})", tr(banda[0]), fmt(banda[1], 0), fmt(banda[2], 0)) if banda else "")),
        (tr("Material"), material),
        (tr("Escala"), escala),
        (tr("Hoja"), tr("{0} de {1} · {2}", n, total, hoja.papel)),
        (tr("Fecha"), fecha),
        (tr("Versión"), tr("Chirptenna Wire {0}", __version__)),
        (tr("Estado"), estado),
        (tr("Licencia"), tr("{0} (diseños)", LICENCIA)),
        (tr("Proyecto"), URL),
    ]
    if diseno.cable:
        campos.insert(4, (tr("Cable"), tr("{0} · VF {1} ({2})", diseno.cable['nombre'], fmt(diseno.cable['vf'], 2), tr(diseno.cable['vf_origen']))))
    paso = (y1 - y0 - 2.5) / len(campos)
    for i, (clave, valor) in enumerate(campos):
        yy = y0 + 4.2 + i * paso
        elementos.append(Texto(x0 + 2, yy, clave, 5.3, GRIS))
        elementos.append(Texto(x0 + 18, yy, valor, 5.6))
        if i:
            elementos.append(Linea(x0, yy - 2.7, xl, yy - 2.7, GRIS_CLARO, 0.1))
    hoja.anadir(*(replace(e, etiqueta="cajetin") for e in elementos))


def regla(hoja: Hoja, x: float, y: float) -> None:
    """Regla de comprobación de 80 mm y rectángulo de 20 × 7 mm, con el aviso de imprimir al 100 %."""
    seccion(hoja, x, y, tr("COMPRUEBA LA ESCALA"), tr("Mide antes de usar los detalles 1:1"))
    yb = y + 22
    hoja.anadir(Rect(x, y + 8, 20, 7, TINTA, 0.15, etiqueta="regla:cuadro"),
                Texto(x + 23, y + 12.5, tr("20 × 7 mm"), 5.5, GRIS),
                Rect(x, yb, REGLA_MM, 0.8, None, relleno=TINTA, etiqueta="regla:barra"))
    for mm in range(0, int(REGLA_MM) + 1, 10):
        hoja.anadir(Linea(x + mm, yb - 1.5, x + mm, yb + 0.8, TINTA, 0.15),
                    Texto(x + mm, yb + 4, str(mm), 4.8, GRIS, ancla="centro"))
    hoja.anadir(Texto(x, yb + 10, tr("Si la regla no mide {0:.0f} mm, imprime al 100 % («tamaño real»,\nsin «ajustar a la página») y vuelve a medir.", REGLA_MM), 5.6))


def _paso_bonito(rango: float, divisiones: int = 5) -> float:
    bruto = rango / divisiones
    p = 10 ** math.floor(math.log10(bruto))
    for m in (1, 2, 2.5, 5, 10):
        if m * p >= bruto:
            return m * p
    return 10 * p


def grafica_roe(hoja: Hoja, x: float, y: float, ancho: float, alto: float, f: list[float], roe: list[float],
                banda: tuple[float, float] | None) -> None:
    """ROE frente a frecuencia, con la banda sombreada. Todo vectorial (sin matplotlib)."""
    f0, f1 = min(f), max(f)
    tope = 2.5 if max(roe) <= 2.5 else 3.0
    sx = lambda v: x + (v - f0) / (f1 - f0) * ancho  # noqa: E731
    sy = lambda v: y + alto - (v - 1) / (tope - 1) * alto  # noqa: E731
    if banda:
        b0, b1 = max(banda[0], f0), min(banda[1], f1)
        if b1 > b0:
            hoja.anadir(Rect(sx(b0), y, sx(b1) - sx(b0), alto, None, relleno="#f3e6d3"))
    paso_f = _paso_bonito(f1 - f0)
    decimales = 0 if float(paso_f).is_integer() else 1
    k = math.ceil(f0 / paso_f - 1e-9)
    while k * paso_f <= f1 + 1e-9:
        v = k * paso_f
        hoja.anadir(Linea(sx(v), y, sx(v), y + alto, GRIS_CLARO, 0.1),
                    Texto(sx(v), y + alto + 3, fmt(v, decimales), 4.8, ancla="centro"))
        k += 1
    v = 1.0
    while v <= tope + 1e-9:
        hoja.anadir(Linea(x, sy(v), x + ancho, sy(v), GRIS_CLARO, 0.1),
                    Texto(x - 1, sy(v) + 0.6, fmt(v, 1), 4.8, ancla="derecha"))
        v += 0.5
    tramo: list[tuple[float, float]] = []
    for fi, ri in zip(f, roe):
        if ri <= tope:
            tramo.append((sx(fi), sy(ri)))
        else:
            if len(tramo) > 1:
                hoja.anadir(Polilinea(tuple(tramo), VERDE, 0.35))
            tramo = []
    if len(tramo) > 1:
        hoja.anadir(Polilinea(tuple(tramo), VERDE, 0.35))
    hoja.anadir(Rect(x, y, ancho, alto, TINTA, 0.2),
                Texto(x + ancho / 2, y + alto + 6.5, "MHz", 5, ancla="centro"),
                Texto(x - 7, y + alto / 2, "ROE", 5, ancla="centro", rotacion=90))


def tabla(hoja: Hoja, x: float, y: float, columnas: list[float], cabecera: list[str], filas: list[list[str]],
          ancho: float) -> float:
    """Tabla sencilla; devuelve la y debajo de la última fila. Si un texto no cabe en su columna (otro idioma), baja
    el cuerpo de la letra hasta que quepa."""
    limites = [c - 1.5 for c in columnas[1:]] + [ancho]

    def tam(texto: str, k: int, base: float, estilo: str = "normal") -> float:
        disponible = limites[k] - columnas[k]
        w = ancho_texto(texto, base, estilo)
        return base if w <= disponible else max(4.4, base * disponible / w)

    for k, (c, t) in enumerate(zip(columnas, cabecera)):
        hoja.anadir(Texto(x + c, y, t, tam(t, k, 6.5, "negrita"), estilo="negrita"))
    hoja.anadir(Linea(x, y + 1.5, x + ancho, y + 1.5, TINTA, 0.14))
    yy = y + 6
    for fila in filas:
        for k, (c, t) in enumerate(zip(columnas, fila)):
            hoja.anadir(Texto(x + c, yy, t, tam(t, k, 6.3)))
        yy += 5
    return yy


def alambre(hoja: Hoja, x1: float, y1: float, x2: float, y2: float, diametro: float, etiqueta: str = "") -> None:
    """Alambre a escala 1:1: banda de cobre del diámetro real y su eje (el que se acota)."""
    if y1 == y2:
        hoja.anadir(Rect(min(x1, x2), y1 - diametro / 2, abs(x2 - x1), diametro, None, relleno=COBRE))
    else:
        hoja.anadir(Rect(x1 - diametro / 2, min(y1, y2), diametro, abs(y2 - y1), None, relleno=COBRE))
    hoja.anadir(Linea(x1, y1, x2, y2, TINTA, 0.1, (1.5, 0.8), etiqueta=etiqueta))


__all__ = ["BLANCO", "COBRE", "GRIS", "PT", "TINTA", "VERDE", "alambre", "cajetin", "fmt", "grafica_roe", "hoja_a4",
           "longitud", "regla", "seccion", "tabla", "texto_banda", "unidad"]
