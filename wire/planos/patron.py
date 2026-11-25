"""Patrón del coaxial a escala 1:1: el trozo de cable con sus pelados, para ponerlo encima y marcar dónde cortar y pelar.

Se dibuja horizontal; si es más largo que una hoja se reparte en un mosaico de A4 (o en una A3), como cualquier plantilla.
"""

from __future__ import annotations

from ..diseno import Diseno
from ..i18n import tr
from .comun import fmt, longitud, unidad
from .hoja import BLANCO, COBRE, CUBIERTA, DIELECTRICO, GRIS, TINTA, VERDE, Cota, Linea, Rect, Texto, rayado
from .paginacion import RELLENO_PLANTILLA, hojas_plantilla

# Pelado de cada extremo (mm), orientativo; el mismo de la hoja de detalle de la CoCo.
VIVO, DIELECTRICO_MM, MALLA = 14.0, 6.0, 12.0
VIVO_DIAMETRO = 0.9


def _diametros(diseno: Diseno) -> tuple[float, float, float]:
    from ..cables import cable
    c = cable(diseno.cable["nombre"])
    return c.diametro_exterior_mm, c.diametro_malla_mm, c.diametro_dielectrico_mm


def plantilla_coaxial(diseno: Diseno, trozos: list[tuple[str, float]], largo_final: float | None = None, sobrante: float = 0.0,
                      nota_final: str = "") -> tuple[list, float, float]:
    """Primitivas (mm, y hacia abajo) de un cable formado por `trozos` [(tipo, largo)] de izquierda a derecha.

    Tipos: «vivo» (conductor central a la vista), «dielectrico» (con el vivo dentro), «malla» (trenza a la vista) y «cubierta».
    `largo_final` marca con una raya la longitud final si lleva `sobrante` mm de más (el sobrante sale rayado a la derecha).
    """
    od, dm, dd = _diametros(diseno)
    pad = RELLENO_PLANTILLA + 8.0
    total = sum(l for _, l in trozos)
    y = pad + 32.0
    alto = y + od / 2 + 30.0
    ancho = total + 2 * pad
    prims: list = []
    x = pad
    marcas = [x]
    for tipo, largo in trozos:
        if tipo == "cubierta":
            prims.append(Rect(x, y - od / 2, largo, od, None, 0.1, CUBIERTA, "plantilla:coax_cubierta"))
        elif tipo == "malla":
            prims.append(Rect(x, y - dm / 2, largo, dm, None, 0.1, COBRE, "plantilla:coax_malla"))
            prims.extend(rayado(x, y - dm / 2, largo, dm, 2.4, TINTA, 0.1))
        elif tipo == "dielectrico":
            prims.append(Rect(x, y - dd / 2, largo, dd, None, 0.1, DIELECTRICO, "plantilla:coax_dielectrico"))
            prims += [Linea(x, y - dd / 2, x + largo, y - dd / 2, TINTA, 0.12), Linea(x, y + dd / 2, x + largo, y + dd / 2, TINTA, 0.12),
                      Rect(x, y - VIVO_DIAMETRO / 2, largo, VIVO_DIAMETRO, None, 0.1, COBRE, "plantilla:coax_vivo")]
        elif tipo == "vivo":
            prims.append(Rect(x, y - VIVO_DIAMETRO / 2, largo, VIVO_DIAMETRO, None, 0.1, COBRE, "plantilla:coax_vivo"))
        x += largo
        marcas.append(x)
    ya = y - od / 2 - 7
    for a, b, (tipo, largo) in zip(marcas, marcas[1:], trozos):
        prims.append(Linea(a, y - od / 2 - 2, a, ya - 2, GRIS, 0.12))
        if largo >= 3.0 and tipo != "cubierta":
            prims.append(Cota(a, ya, b, ya, longitud(largo, diseno, 0), tam=5.2))
    prims.append(Linea(marcas[-1], y - od / 2 - 2, marcas[-1], ya - 2, GRIS, 0.12))
    prims.append(Cota(marcas[0], y - od / 2 - 18, marcas[-1], y - od / 2 - 18, tr("cortar a {0}", longitud(total, diseno, 0)), tam=6.0,
                      ref1=(marcas[0], y - od / 2 - 2), ref2=(marcas[-1], y - od / 2 - 2)))
    if largo_final is not None and sobrante > 0:
        xf = pad + largo_final
        prims += [Linea(xf, y - od / 2 - 4, xf, y + od / 2 + 12, VERDE, 0.3, (1.5, 0.8), "plantilla:final"),
                  Texto(xf - 1.5, y + od / 2 + 17, tr("largo final {0}", longitud(largo_final, diseno, 0)), 5.8, VERDE, ancla="derecha"),
                  Texto(xf + 1.5, y + od / 2 + 17, tr("sobrante {0}", longitud(sobrante, diseno, 0)), 5.8, GRIS)]
    prims.append(Texto(pad, y + od / 2 + 8, nota_final or tr("Pon el cable encima: alinea el extremo con la raya de la izquierda."), 5.8))
    return prims, ancho, alto


def hojas_patron(diseno: Diseno, titulo: str, trozos: list[tuple[str, float]], largo_final: float | None = None,
                 sobrante: float = 0.0) -> list:
    prims, ancho, alto = plantilla_coaxial(diseno, trozos, largo_final, sobrante)
    hojas, _ = hojas_plantilla(diseno, titulo, tr("Patrón del coaxial a 1:1: pon el cable encima para marcar los cortes y los pelados"),
                               prims, ancho, alto)
    return hojas


def patrones_coco(diseno: Diseno) -> list:
    """Dos patrones: el tramo (pelado en los dos extremos) y la punta."""
    g = diseno.geometria
    sobrante = diseno.sobrante_mm
    pelado = VIVO + DIELECTRICO_MM + MALLA
    tramo = g["tramo_mm"] + sobrante
    punta = g["punta_mm"] + sobrante
    hojas = hojas_patron(
        diseno, tr("Patrón del tramo de coaxial · {0} MHz", fmt(diseno.f_MHz, 1)),
        [("vivo", VIVO), ("dielectrico", DIELECTRICO_MM), ("malla", MALLA), ("cubierta", tramo - 2 * pelado), ("malla", MALLA),
         ("dielectrico", DIELECTRICO_MM), ("vivo", VIVO)], g["tramo_mm"], sobrante)
    hojas += hojas_patron(
        diseno, tr("Patrón de la punta · {0} MHz", fmt(diseno.f_MHz, 1)),
        [("dielectrico", punta - MALLA - 40.0), ("malla", MALLA), ("cubierta", 40.0)], g["punta_mm"], sobrante)
    return hojas


def patron_manga(diseno: Diseno) -> list:
    """El extremo del cable: el vivo con su dieléctrico (radiador), la malla que se dobla (manga) y la cubierta."""
    g = diseno.geometria
    return hojas_patron(
        diseno, tr("Patrón del extremo del cable · {0} MHz", fmt(diseno.f_MHz, 1)),
        [("dielectrico", g["radiador_mm"] + diseno.sobrante_mm), ("malla", g["manga_mm"]), ("cubierta", 40.0)])
