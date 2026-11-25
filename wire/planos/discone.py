"""Hoja del discone: vista general, lista de corte, resultados y plantilla a 1:1 de la pieza central y del ángulo del cono."""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..i18n import tr
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, unidad
from .hoja import BLANCO, COBRE, GRIS, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto

R_PIEZA = 15.0     # mm, radio de las placas de la pieza central (Ø 30)
GROSOR_PLACA = 8.0


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    cono, disco, hueco = g["cono_mm"], g["disco_mm"], g["hueco_mm"]
    alfa = g["semiangulo"]
    n = int(g["varillas"])
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, tr("Discone · {0} MHz mínimo ({1} varillas)", frecuencia(diseno.f_MHz), n),
                   tr("Disco y cono de varillas de Ø {0} mm · alimentado con coaxial de 50 Ω por dentro del cono", fmt(d, 1)))

    # 1. Vista general, sin escala
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje de la varilla", u))
    ca, sa = math.cos(math.radians(alfa)), math.sin(math.radians(alfa))
    esc = min(36.0 / (cono * ca), 70.0 / max(cono * sa, disco))
    xc, ya = 105.0, 46.0
    hoja.anadir(
        Linea(xc - disco * esc, ya - 2.5, xc + disco * esc, ya - 2.5, COBRE, 0.85),
        Linea(xc, ya - 2.5, xc, ya, TINTA, 0.5),
        Linea(xc, ya, xc - cono * sa * esc, ya + cono * ca * esc, COBRE, 0.85),
        Linea(xc, ya, xc + cono * sa * esc, ya + cono * ca * esc, COBRE, 0.85),
        Linea(xc, ya, xc, ya + cono * ca * esc, GRIS, 0.12, (1.5, 1.0)),
        Cota(xc - disco * esc, ya - 8, xc, ya - 8, tr("radio del disco {0}", longitud(disco, diseno)), tam=5.6),
        Texto(xc + cono * sa * esc + 3, ya + cono * ca * esc - 4, tr("generatriz {0}", longitud(cono, diseno)), 5.6),
        Texto(xc + 4, ya + 12, tr("semiángulo {0}°", fmt(alfa, 0)), 5.6, GRIS),
        Texto(xc + 4, ya - 4.5, tr("hueco {0}", longitud(hueco, diseno, 0)), 5.6),
    )

    # 2. Lista de corte
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Medidas desde el centro de la pieza; corta con el sobrante"), VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        [tr("Varilla del disco, Ø {0} mm", fmt(d, 1)), str(n), f"{longitud(disco, diseno)} {u}",
         f"{longitud(disco + sobrante, diseno, 0)} {u}"],
        [tr("Varilla del cono, Ø {0} mm", fmt(d, 1)), str(n), f"{longitud(cono, diseno)} {u}",
         f"{longitud(cono + sobrante, diseno, 0)} {u}"],
        [tr("Placa de aluminio Ø 30 × 8 mm"), "2", "—", "—"],
        [tr("Aislador de PVC, {0} mm entre placas", longitud(hueco, diseno, 0)), "1", "—", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 138, tr("Ajuste: la banda baja si alargas el cono y el disco por igual.\n"
                                  "Frecuencia mínima ≈ λ/4 de la generatriz."), 6.0, VERDE))
    _simulacion(hoja, diseno)

    # 3. Plantilla de la pieza central y del ángulo, a escala 1:1
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("PIEZA CENTRAL Y ÁNGULO DEL CONO"), tr("Escala 1:1 · marca los taladros y el ángulo sobre el papel"), VERDE)
    cx, cy = 52.0, 195.0
    hoja.anadir(Circulo(cx, cy, R_PIEZA, TINTA, 0.25, None, etiqueta="plantilla:placa"),
                Circulo(cx, cy, 0.8, TINTA, 0.15, TINTA))
    for i in range(n):
        a = 2 * math.pi * i / n
        x1, y1 = cx + (R_PIEZA - 8) * math.cos(a), cy - (R_PIEZA - 8) * math.sin(a)
        x2, y2 = cx + (R_PIEZA + 6) * math.cos(a), cy - (R_PIEZA + 6) * math.sin(a)
        hoja.anadir(Linea(x1, y1, x2, y2, VERDE, 0.2, etiqueta="plantilla:taladro"),
                    Circulo(cx + R_PIEZA * math.cos(a), cy - R_PIEZA * math.sin(a), max(d, 1.0) / 2 + 0.2, TINTA, 0.15, BLANCO,
                            etiqueta="plantilla:taladro"))
    hoja.anadir(
        Cota(cx - R_PIEZA, cy + R_PIEZA + 9, cx + R_PIEZA, cy + R_PIEZA + 9, tr("placa Ø {0}", longitud(2 * R_PIEZA, diseno, 0)),
             tam=5.6, ref1=(cx - R_PIEZA, cy + R_PIEZA * 0.2), ref2=(cx + R_PIEZA, cy + R_PIEZA * 0.2)),
        Texto(cx, cy - R_PIEZA - 9, tr("{0} taladros cada {1}° (los del disco, horizontales)", n, fmt(360 / n, 0)), 5.6, ancla="centro"),
    )
    vx, vy = 140.0, 232.0                    # vértice de la plantilla del ángulo
    largo_plantilla = 60.0
    ra = math.radians(alfa)
    hoja.anadir(
        Linea(vx, vy, vx, vy - largo_plantilla, GRIS, 0.15, (1.5, 1.0), "plantilla:eje"),
        Linea(vx, vy, vx + largo_plantilla * math.sin(ra), vy - largo_plantilla * math.cos(ra), COBRE, max(d, 0.6),
              etiqueta="plantilla:varilla_cono"),
        Linea(vx, vy, vx + largo_plantilla, vy, GRIS, 0.15, (1.5, 1.0), "plantilla:horizontal"),
        Texto(vx + 5.5, vy - 33, fmt(alfa, 0) + "°", 7, ancla="izquierda"),
        Texto(vx - 3, vy - largo_plantilla - 2, tr("eje del cono"), 5.6, ancla="centro"),
        Texto(vx + largo_plantilla * math.sin(ra) + 2, vy - largo_plantilla * math.cos(ra) + 1, tr("varilla del cono"), 5.6),
    )
    regla(hoja, 14, 244)
    return [hoja]


def _simulacion(hoja: Hoja, diseno: Diseno) -> None:
    r = diseno.resultados
    if not r:
        seccion(hoja, 128, 91, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(128, 103, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
        return
    seccion(hoja, 128, 91, tr("SIMULADO (NEC2) · SIN MEDIR"), tr("Espacio libre, sin mástil ni cable de bajada"))
    hoja.anadir(Texto(128, 103, tr("ROE < 2 de {0} a {1} MHz ({2}:1)\n{3} dBi a {4} MHz",
                                   fmt(r["f_inferior_roe2_MHz"], 0), fmt(r["f_superior_roe2_MHz"], 0), fmt(r["relacion_banda"], 1),
                                   fmt(r["ganancia_dBi"], 1), fmt(r["f_ganancia_MHz"], 0)), 6.3))
    grafica_roe(hoja, 138, 113, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], (r["f_inferior_roe2_MHz"], r["f_superior_roe2_MHz"]))
