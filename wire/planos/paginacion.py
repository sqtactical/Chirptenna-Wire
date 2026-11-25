"""Cómo imprimir una plantilla 1:1 según su tamaño y el bloque `plano` (docs/PLANOS.md §3).

`decidir_papel` elige hoja, A3, mosaico de A4 o «sin escala»; `hojas_plantilla` dibuja la plantilla a 1:1 en lo que
se haya elegido (fase 4).
"""

from __future__ import annotations

from ..diseno import ConfigPlano, Diseno
from ..i18n import tr
from .hoja import (BLANCO, COBRE, GRIS, GRIS_CLARO, PAPELES, TINTA, VERDE, Circulo, Hoja, Linea, Polilinea, Rect, Texto,
                   _recortar)

MARGEN = 10.0  # mm, marco de la hoja
ALTO_CAJETIN = 44.0  # mm, lo que el cajetín quita al área útil por abajo
CABECERA = 30.0  # mm, título y rótulo de la sección
MAX_HOJAS_MOSAICO = 12  # más de ~4 × 3 hojas: mejor sin escala


def area_util(papel: str, apaisada: bool) -> tuple[float, float]:
    a, b = PAPELES[papel]
    ancho, alto = (b, a) if apaisada else (a, b)
    return ancho - 2 * MARGEN, alto - 2 * MARGEN - ALTO_CAJETIN - CABECERA


def decidir_papel(ancho_mm: float, alto_mm: float, config: ConfigPlano) -> dict:
    """Devuelve {"modo": "hoja" | "A3" | "mosaico" | "sin_escala", "papel", "apaisada", "hojas": (columnas, filas)}."""
    orientaciones = {"auto": (False, True), "vertical": (False,), "apaisada": (True,)}[config.orientacion]

    def cabe(papel: str, apaisada: bool) -> bool:
        w, h = area_util(papel, apaisada)
        return ancho_mm <= w and alto_mm <= h

    for apaisada in orientaciones:
        if cabe(config.papel, apaisada):
            return {"modo": "hoja", "papel": config.papel, "apaisada": apaisada, "hojas": (1, 1)}
    if config.grandes == "A3" and config.papel == "A4":
        for apaisada in orientaciones:
            if cabe("A3", apaisada):
                return {"modo": "A3", "papel": "A3", "apaisada": apaisada, "hojas": (1, 1)}
    if config.grandes == "mosaico":
        w, h = area_util(config.papel, False)
        paso_x, paso_y = w - config.solape_mm, h - config.solape_mm
        columnas = max(1, -int(-(ancho_mm - config.solape_mm) // paso_x))
        filas = max(1, -int(-(alto_mm - config.solape_mm) // paso_y))
        if columnas * filas <= MAX_HOJAS_MOSAICO:
            return {"modo": "mosaico", "papel": config.papel, "apaisada": False, "hojas": (columnas, filas)}
    return {"modo": "sin_escala", "papel": config.papel, "apaisada": False, "hojas": (1, 1)}


LETRAS = "ABCDEFGHIJKL"
RELLENO_PLANTILLA = 6.0  # mm de aire alrededor de la plantilla


def etiqueta_hoja(c: int, r: int) -> str:
    """A1, A2… por fila (letra) y columna (número)."""
    return f"{LETRAS[r]}{c + 1}"


def _cruz(x: float, y: float, brazo: float = 3.0) -> list:
    return [Linea(x - brazo, y, x + brazo, y, TINTA, 0.2, etiqueta="registro"),
            Linea(x, y - brazo, x, y + brazo, TINTA, 0.2, etiqueta="registro"),
            Circulo(x, y, brazo * 0.6, TINTA, 0.15, etiqueta="registro")]


def recortar_primitivas(primitivas: list, ventana: tuple[float, float, float, float], dx: float, dy: float) -> list:
    """La parte de las primitivas (líneas, polilíneas abiertas, rectángulos rellenos, círculos y textos) que cae en
    `ventana`, trasladada (+dx, +dy). Un texto o un círculo que no cabe entero se queda para la hoja que lo contiene."""
    x0, y0, x1, y1 = ventana
    salida: list = []
    for p in primitivas:
        if isinstance(p, Linea):
            seg = _recortar(p.x1, p.y1, p.x2, p.y2, x0, y0, x1, y1)
            if seg:
                salida.append(Linea(seg[0] + dx, seg[1] + dy, seg[2] + dx, seg[3] + dy, p.color, p.grosor, p.discontinua,
                                    p.etiqueta))
        elif isinstance(p, Polilinea) and not p.cerrada:
            for a, b in zip(p.puntos, p.puntos[1:]):
                seg = _recortar(*a, *b, x0, y0, x1, y1)
                if seg:
                    salida.append(Linea(seg[0] + dx, seg[1] + dy, seg[2] + dx, seg[3] + dy, p.color or TINTA, p.grosor,
                                        None, p.etiqueta))
        elif isinstance(p, Rect) and p.relleno is not None:
            ax, ay, bx, by = max(p.x, x0), max(p.y, y0), min(p.x + p.ancho, x1), min(p.y + p.alto, y1)
            if ax < bx and ay < by:
                salida.append(Rect(ax + dx, ay + dy, bx - ax, by - ay, p.color, p.grosor, p.relleno, p.etiqueta))
        elif isinstance(p, Circulo):
            if x0 <= p.cx <= x1 and y0 <= p.cy <= y1:
                salida.append(Circulo(p.cx + dx, p.cy + dy, p.r, p.color, p.grosor, p.relleno, p.discontinua, p.etiqueta))
        elif isinstance(p, Texto):
            c = p.caja
            if c[0] >= x0 and c[1] >= y0 and c[2] <= x1 and c[3] <= y1:
                salida.append(Texto(p.x + dx, p.y + dy, p.texto, p.tam, p.color, p.estilo, p.ancla, p.fondo, p.rotacion,
                                    p.etiqueta))
    return salida


def _distancia_a_hilos(x: float, y: float, primitivas: list) -> float:
    """Distancia del punto al borde del alambre dibujado (líneas gruesas) más cercano."""
    mejor = float("inf")
    segmentos = []
    for p in primitivas:
        if isinstance(p, Linea):
            segmentos.append((p.x1, p.y1, p.x2, p.y2, p.grosor))
        elif isinstance(p, Polilinea) and not p.cerrada:
            segmentos += [(a[0], a[1], b[0], b[1], p.grosor) for a, b in zip(p.puntos, p.puntos[1:])]
    for x1, y1, x2, y2, g in segmentos:
        dx, dy = x2 - x1, y2 - y1
        n2 = dx * dx + dy * dy
        t = 0.0 if n2 == 0 else max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / n2))
        mejor = min(mejor, ((x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2) ** 0.5 - g / 2)
    return mejor


def marcas_registro(ancho: float, alto: float, columnas: int, filas: int, paso_x: float, paso_y: float, solape: float,
                    primitivas: list, d: float) -> list[tuple[float, float]]:
    """Puntos (en coordenadas de la plantilla) donde van las cruces de registro: en el centro de cada franja de solape,
    en los bordes de la plantilla y en los cruces de franjas. Solo se ponen donde no pisan el alambre."""
    xs = [(k + 1) * paso_x + solape / 2 for k in range(columnas - 1)]
    ys = [(k + 1) * paso_y + solape / 2 for k in range(filas - 1)]
    candidatas = [(x, y) for x in xs for y in ys]
    candidatas += [(x, y) for x in xs for y in (5.0, alto - 5.0)]
    candidatas += [(x, y) for y in ys for x in (5.0, ancho - 5.0)]
    for x in xs:                                      # a lo largo de las franjas largas, cada ~80 mm
        y = 85.0
        while y < alto - 40.0:
            candidatas.append((x, y))
            y += 80.0
    for y in ys:
        x = 85.0
        while x < ancho - 40.0:
            candidatas.append((x, y))
            x += 80.0
    return [(x, y) for x, y in candidatas if _distancia_a_hilos(x, y, primitivas) > 4.5]


def hojas_plantilla(diseno: Diseno, titulo: str, subtitulo: str, primitivas: list, ancho: float, alto: float,
                    decision: dict | None = None) -> tuple[list[Hoja], dict]:
    """Plantilla a 1:1 de `ancho` × `alto` mm (con su aire ya incluido) repartida en una hoja, A3 o un mosaico de A4.

    Devuelve (hojas, decisión). Sin escala (no cabe en el mosaico) no devuelve hojas.
    """
    cfg = diseno.plano
    d = decision or decidir_papel(ancho, alto, cfg)
    if d["modo"] == "sin_escala":
        return [], d
    if d["modo"] in ("hoja", "A3"):
        hoja = hoja_papel_plantilla(diseno, titulo, subtitulo, d["papel"], d["apaisada"])
        hoja.anadir(*recortar_primitivas(primitivas, (0, 0, ancho, alto), MARGEN, MARGEN + CABECERA))
        _regla(hoja)
        return [hoja], d
    columnas, filas = d["hojas"]
    w, h = area_util(d["papel"], False)
    solape = cfg.solape_mm
    paso_x, paso_y = w - solape, h - solape
    marcas = marcas_registro(ancho, alto, columnas, filas, paso_x, paso_y, solape, primitivas, diseno.diametro_mm)
    hojas = []
    for r in range(filas):
        for c in range(columnas):
            x0, y0 = c * paso_x, r * paso_y
            etiqueta = etiqueta_hoja(c, r)
            vecinas = []
            if c < columnas - 1:
                vecinas.append("→ " + etiqueta_hoja(c + 1, r))
            if r < filas - 1:
                vecinas.append("↓ " + etiqueta_hoja(c, r + 1))
            if c:
                vecinas.append("← " + etiqueta_hoja(c - 1, r))
            if r:
                vecinas.append("↑ " + etiqueta_hoja(c, r - 1))
            hoja = hoja_papel_plantilla(diseno, titulo, tr("Escala 1:1 · hoja {0} de {1} · solapa {2} mm con {3}",
                                                           etiqueta, columnas * filas, f"{solape:g}", " ".join(vecinas)),
                                        d["papel"], False)
            ventana = (x0, y0, x0 + w, y0 + h)
            dx, dy = MARGEN - x0, MARGEN + CABECERA - y0
            hoja.anadir(*recortar_primitivas(primitivas, ventana, dx, dy))
            # Marcas de registro: las mismas coordenadas de la plantilla en todas las hojas que las contienen.
            for xm, ym in marcas:
                if x0 + 3 <= xm <= x0 + w - 3 and y0 + 3 <= ym <= y0 + h - 3:
                    hoja.anadir(*_cruz(xm + dx, ym + dy))
            # Dónde empieza la hoja vecina (línea de trazos) y su etiqueta en la cabecera.
            if c < columnas - 1:
                xl = x0 + w - solape + dx
                hoja.anadir(Linea(xl, MARGEN + CABECERA, xl, MARGEN + CABECERA + h, GRIS, 0.15, (2.0, 1.5), "solape"),
                            Texto(xl, 36, tr("{0} →", etiqueta_hoja(c + 1, r)), 6, GRIS, ancla="centro"))
            if r < filas - 1:
                yl = y0 + h - solape + dy
                hoja.anadir(Linea(MARGEN, yl, MARGEN + w, yl, GRIS, 0.15, (2.0, 1.5), "solape"))
            hoja.anadir(Texto(PAPELES[d["papel"]][0] - 14, 25.5, etiqueta, 12, VERDE, "negrita", "derecha"))
            _regla(hoja)
            hojas.append(hoja)
    return hojas, d


def _regla(hoja: Hoja) -> None:
    """La regla de comprobación de 80 mm, abajo a la izquierda (junto al cajetín)."""
    from .comun import regla
    regla(hoja, 14, hoja.tamano[1] - 53)


def hoja_papel_plantilla(diseno, titulo, subtitulo, papel, apaisada):
    from .comun import hoja_papel
    return hoja_papel(diseno, titulo, subtitulo, papel, apaisada)


def mapa_montaje(hoja: Hoja, x: float, y: float, max_ancho: float, max_alto: float, d: dict, ancho: float, alto: float,
                 primitivas: list, diseno: Diseno) -> None:
    """Mapa del mosaico: qué hoja va dónde, con la silueta de la antena entera (no solo lo que cae en la hoja 1)."""
    columnas, filas = d["hojas"]
    w, h = area_util(d["papel"], False)
    solape = diseno.plano.solape_mm
    paso_x, paso_y = w - solape, h - solape
    total_w, total_h = (columnas - 1) * paso_x + w, (filas - 1) * paso_y + h
    s = min(max_ancho / total_w, max_alto / total_h)
    for r in range(filas):
        for c in range(columnas):
            hoja.anadir(Rect(x + c * paso_x * s, y + r * paso_y * s, w * s, h * s, GRIS, 0.2, None))
            hoja.anadir(Texto(x + (c * paso_x + w / 2) * s, y + (r * paso_y + h / 2) * s + 1.5, etiqueta_hoja(c, r), 9, GRIS,
                              "negrita", "centro"))
    for p in primitivas:
        if isinstance(p, Linea):
            hoja.anadir(Linea(x + p.x1 * s, y + p.y1 * s, x + p.x2 * s, y + p.y2 * s, COBRE, max(0.35, p.grosor * s * 2)))
        elif isinstance(p, Polilinea) and not p.cerrada:
            for a, b in zip(p.puntos, p.puntos[1:]):
                hoja.anadir(Linea(x + a[0] * s, y + a[1] * s, x + b[0] * s, y + b[1] * s, COBRE, max(0.35, p.grosor * s * 2)))
