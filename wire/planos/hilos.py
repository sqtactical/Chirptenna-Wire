"""Hojas de las antenas de alambre sencillas: ground plane, dipolo en V invertida, Yagi de 3 elementos y bicónica.

Cada una lleva una hoja A4: vista general (la proyección del modelo, sin escala), lista de corte, resultados simulados y un
detalle a 1:1 de lo que se pone a mano (el conector, el vértice, el centro del dipolo plegado, la pieza central).
"""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..i18n import N_, tr
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import BLANCO, COBRE, CUBIERTA, GRIS, PVC, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto
from .jpole import _simulacion as _simulacion_roe

X_VISTA, Y_VISTA, ANCHO_VISTA, ALTO_VISTA = 20.0, 38.0, 170.0, 48.0
HUECO_CENTRO = 10.0   # mm entre los dos brazos en el centro del dipolo plegado


def _proyectar(diseno: Diseno, proyeccion, margen_x: float = 0.0):
    """Dibuja la proyección del modelo en la caja de la vista general y devuelve (escala, función punto3 → hoja)."""
    modelo = diseno.modelo()
    segs = [(proyeccion(h.inicio), proyeccion(h.fin)) for h in modelo.hilos]
    us = [p[0] for s in segs for p in s]
    vs = [p[1] for s in segs for p in s]
    du, dv = max(max(us) - min(us), 1e-9), max(max(vs) - min(vs), 1e-9)
    esc = min((ANCHO_VISTA - margen_x) / du, ALTO_VISTA / dv)
    ox = X_VISTA + ((ANCHO_VISTA - margen_x) - du * esc) / 2 + margen_x
    oy = Y_VISTA + (ALTO_VISTA - dv * esc) / 2

    def punto(p3):
        u, v = proyeccion(p3)
        return ox + (u - min(us)) * esc, oy + (max(vs) - v) * esc

    return modelo, esc, punto


def _vista(hoja: Hoja, diseno: Diseno, proyeccion, saltar: tuple[int, ...] = (), margen_x: float = 0.0):
    modelo, esc, punto = _proyectar(diseno, proyeccion, margen_x)
    for i, h in enumerate(modelo.hilos, start=1):
        if i in saltar:
            continue
        a, b = punto(h.inicio), punto(h.fin)
        hoja.anadir(Linea(a[0], a[1], b[0], b[1], COBRE, 0.85))
    return modelo, esc, punto


def _titulo(clave: str, diseno: Diseno, extra: str = "") -> str:
    return tr(clave, frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


# ---------------------------------------------------------------- ground plane

CONECTORES = {                       # (lado de la brida, taladro central, separación de los 4 tornillos), en mm; orientativo
    "SO-239": (25.4, 15.9, 17.2),
    "N": (24.0, 15.9, 18.5),
}


def hojas_gp(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    rad, radial, ang, n = g["radiador_mm"], g["radial_mm"], g["angulo"], int(g["radiales"])
    conector = g.get("conector", "SO-239")
    d = diseno.diametro_mm
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo(N_("Ground plane · {0} MHz ({1})"), diseno),
                   tr("Radiador vertical y {0} radiales a {1}° · conector {2} · alimentado con coaxial de 50 Ω", n, fmt(ang, 0), conector))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje del alambre", u))
    giro = math.radians(25)
    modelo, esc, P = _vista(hoja, diseno, lambda p: (p[0] * math.cos(giro) + p[1] * math.sin(giro), p[2]), margen_x=20)
    base, tope = P((0, 0, 0)), P((0, 0, rad / 1000))
    hoja.anadir(
        Cota(base[0] - 8, base[1], base[0] - 8, tope[1], tr("radiador {0}", longitud(rad, diseno)), tam=5.6),
        Texto(base[0] + 4, base[1] + 5, tr("radial {0} a {1}°", longitud(radial, diseno), fmt(ang, 0)), 5.6),
        Texto(base[0] - 8, base[1] + 6, tr("conector {0}", conector), 5.6, ancla="derecha"),
    )
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    sob = diseno.sobrante_mm
    filas = [
        [tr("Radiador, alambre Ø {0} mm", fmt(d, 1)), "1", f"{longitud(rad, diseno)} {u}", f"{longitud(rad + sob, diseno, 0)} {u}"],
        [tr("Radial, alambre Ø {0} mm", fmt(d, 1)), str(n), f"{longitud(radial, diseno)} {u}", f"{longitud(radial + sob, diseno, 0)} {u}"],
        [tr("Conector {0} de panel", conector), "1", "—", "—"],
        [tr("Terminales de ojal M3 y tornillos"), str(n), "—", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 138, tr("Ajuste: recorta el radiador; los radiales a 45° dan ~50 Ω."), 6.0, VERDE))
    _simulacion_roe(hoja, diseno)

    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("CONECTOR Y ÁNGULO DE LOS RADIALES"), tr("Escala 1:1 · cotas orientativas: comprueba con tu conector"), VERDE)
    lado, centro, sep = CONECTORES.get(conector, CONECTORES["SO-239"])
    cx, cy = 52.0, 195.0
    hoja.anadir(Rect(cx - lado / 2, cy - lado / 2, lado, lado, TINTA, 0.25, None, etiqueta="plantilla:brida"),
                Circulo(cx, cy, centro / 2, TINTA, 0.25, None, etiqueta="plantilla:taladro_central"))
    for sx in (-1, 1):
        for sy in (-1, 1):
            hoja.anadir(Circulo(cx + sx * sep / 2, cy + sy * sep / 2, 1.6, TINTA, 0.2, BLANCO, etiqueta="plantilla:tornillo"))
    hoja.anadir(
        Cota(cx - lado / 2, cy + lado / 2 + 8, cx + lado / 2, cy + lado / 2 + 8, tr("brida {0}", longitud(lado, diseno, 1)), tam=5.6,
             ref1=(cx - lado / 2, cy + lado / 2), ref2=(cx + lado / 2, cy + lado / 2)),
        Texto(cx, cy - lado / 2 - 5, tr("4 tornillos a {0} · taladro Ø {1}", longitud(sep, diseno, 1), longitud(centro, diseno, 1)), 5.6, ancla="centro"),
    )
    vx, vy, L = 125.0, 190.0, 45.0
    a = math.radians(ang)
    hoja.anadir(Linea(vx, vy, vx, vy - 25, GRIS, 0.15, (1.5, 1.0), "plantilla:vertical"),
                Linea(vx, vy, vx + L, vy, GRIS, 0.15, (1.5, 1.0), "plantilla:horizontal"),
                Linea(vx, vy, vx + L * math.cos(a), vy + L * math.sin(a), COBRE, max(d, 0.6), None, "plantilla:radial"),
                Texto(vx + 8, vy + 12, f"{fmt(ang, 0)}°", 7),
                Texto(vx + L - 2, vy - 1.5, tr("horizontal"), 5.6, ancla="derecha"),
                Texto(vx + L * math.cos(a) + 2, vy + L * math.sin(a) + 2, tr("radial"), 5.6))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- V invertida


def hojas_vinv(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    brazo, ap = g["brazo_mm"], g["apertura"]
    d = diseno.diametro_mm
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo(N_("Dipolo en V invertida · {0} MHz ({1})"), diseno),
                   tr("Dos brazos de alambre de Ø {0} mm con {1}° entre sí, vértice arriba · alimentado con coaxial de 50 Ω", fmt(d, 1), fmt(ap, 0)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje del alambre", u))
    modelo, esc, P = _vista(hoja, diseno, lambda p: (p[0], p[2]), margen_x=30)
    vert, fin = P((0, 0, 0)), P(modelo.hilos[0].fin)
    hoja.anadir(Texto((vert[0] + fin[0]) / 2 + 5, (vert[1] + fin[1]) / 2 - 1, tr("brazo {0}", longitud(brazo, diseno)), 5.6),
                Texto(vert[0] + 6, vert[1] + 1, tr("apertura {0}°", fmt(ap, 0)), 5.6),
                Texto(vert[0], vert[1] - 3, tr("coaxial: vivo a un brazo, malla al otro"), 5.6, ancla="centro"))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    sob = diseno.sobrante_mm
    filas = [
        [tr("Brazo, alambre Ø {0} mm", fmt(d, 1)), "2", f"{longitud(brazo, diseno)} {u}", f"{longitud(brazo + sob, diseno, 0)} {u}"],
        [tr("Aislador central de PVC, 60 × 25 × 5 mm"), "1", "—", "—"],
        [tr("Tornillos M3 × 10 con tuerca"), "2", "—", "—"],
        [tr("Cuerda aislante para los extremos"), "2", tr("a medida"), "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 138, tr("Ajuste: recorta los dos brazos por igual; el vértice va en lo alto de un mástil\n"
                                  "no metálico y los extremos, tensados con cuerda."), 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("VÉRTICE Y ÁNGULO"), tr("Escala 1:1 · el aislador central y los brazos a {0}°", fmt(ap, 0)), VERDE)
    vx, vy, L = 105.0, 175.0, 55.0
    m = math.radians(ap / 2)
    hoja.anadir(Rect(vx - 30, vy - 12.5, 60, 25, TINTA, 0.18, PVC, etiqueta="plantilla:aislador"),
                Linea(vx, vy, vx, vy + L, GRIS, 0.15, (1.5, 1.0), "plantilla:vertical"),
                Linea(vx, vy, vx - L * math.sin(m), vy + L * math.cos(m), COBRE, max(d, 0.6), None, "plantilla:brazo_izq"),
                Linea(vx, vy, vx + L * math.sin(m), vy + L * math.cos(m), COBRE, max(d, 0.6), None, "plantilla:brazo_der"),
                Circulo(vx - 14, vy - 6, 1.6, TINTA, 0.15, BLANCO), Circulo(vx + 14, vy - 6, 1.6, TINTA, 0.15, BLANCO),
                Texto(vx + 4, vy + 20, f"{fmt(ap, 0)}°", 7),
                Texto(vx - 28, vy - 15, tr("aislador 60 × 25 mm, taladros a {0}", longitud(28.0, diseno, 0)), 5.6))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- Yagi


def hojas_yagi(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    refl, exc, dire = g["reflector_mm"], g["excitado_mm"], g["director_mm"]
    s1, s2, sp = g["sep_reflector_mm"], g["sep_director_mm"], g["sep_plegado_mm"]
    d = diseno.diametro_mm
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo(N_("Yagi de 3 elementos · {0} MHz ({1})"), diseno),
                   tr("Reflector, dipolo plegado y director de alambre o varilla de Ø {0} mm sobre un eje aislante · coaxial de 50 Ω", fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista desde arriba, sin escala · medidas en {0}", u))
    modelo, esc, P = _vista(hoja, diseno, lambda p: (p[1], p[0]), saltar=(3, 4, 5))
    yb = P((0, 0, 0))[1]
    x0, x1, x2 = P((0, 0, 0))[0], P((0, s1 / 1000, 0))[0], P((0, (s1 + s2) / 1000, 0))[0]
    hoja.anadir(Linea(x0 - 4, yb, x2 + 4, yb, GRIS, 0.5),
                Texto(x0, yb - esc * refl / 2000 - 3, tr("reflector {0}", longitud(refl, diseno, 0)), 5.4, ancla="centro"),
                Texto(x1, yb - esc * exc / 2000 - 3, tr("plegado {0}", longitud(exc, diseno, 0)), 5.4, ancla="centro"),
                Texto(x2, yb - esc * dire / 2000 - 3, tr("director {0}", longitud(dire, diseno, 0)), 5.4, ancla="centro"),
                Cota(x0, yb + esc * refl / 2000 + 6, x1, yb + esc * refl / 2000 + 6, longitud(s1, diseno, 0), tam=5.4),
                Cota(x1, yb + esc * refl / 2000 + 6, x2, yb + esc * refl / 2000 + 6, longitud(s2, diseno, 0), tam=5.4))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    sob = diseno.sobrante_mm
    cierre = sp + d
    filas = [
        [tr("Reflector, Ø {0} mm", fmt(d, 1)), "1", f"{longitud(refl, diseno)} {u}", f"{longitud(refl + sob, diseno, 0)} {u}"],
        [tr("Dipolo plegado, Ø {0} mm", fmt(d, 1)), "2", f"{longitud(exc, diseno)} {u}", f"{longitud(exc + sob, diseno, 0)} {u}"],
        [tr("Cierres del plegado, Ø {0} mm", fmt(d, 1)), "2", f"{longitud(cierre, diseno)} {u}", f"{longitud(cierre + 6, diseno, 0)} {u}"],
        [tr("Director, Ø {0} mm", fmt(d, 1)), "1", f"{longitud(dire, diseno)} {u}", f"{longitud(dire + sob, diseno, 0)} {u}"],
        [tr("Eje aislante (PVC o madera barnizada)"), "1", f"{longitud(s1 + s2 + 120, diseno, 0)} {u}", "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 138, tr("Ajuste: acorta los extremos de los tres elementos por igual; el director es el más\ncrítico para la ganancia."), 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("CENTRO DEL DIPOLO PLEGADO"), tr("Escala 1:1 · el alambre de abajo se corta en el centro: aquí va el coaxial"), VERDE)
    cx, cy = 105.0, 195.0
    hoja.anadir(Rect(cx - 90, cy, 90 - HUECO_CENTRO / 2, d, None, relleno=COBRE, etiqueta="plantilla:alimentado_izq"),
                Rect(cx + HUECO_CENTRO / 2, cy, 90 - HUECO_CENTRO / 2, d, None, relleno=COBRE, etiqueta="plantilla:alimentado_der"),
                Rect(cx - 90, cy - sp - d, 180, d, None, relleno=COBRE, etiqueta="plantilla:plegado"),
                Linea(cx, cy - sp - d - 6, cx, cy + d + 8, VERDE, 0.2, (1.2, 0.6), "plantilla:centro"),
                Cota(cx - HUECO_CENTRO / 2, cy + d + 6, cx + HUECO_CENTRO / 2, cy + d + 6, longitud(HUECO_CENTRO, diseno, 0), tam=5.6,
                     ref1=(cx - HUECO_CENTRO / 2, cy + d), ref2=(cx + HUECO_CENTRO / 2, cy + d)),
                Cota(cx - 70, cy - sp - d, cx - 70, cy + d, longitud(sp + 2 * d, diseno, 1), tam=5.6),
                Texto(cx - 88, cy - sp - d - 4, tr("alambre plegado (continuo)"), 5.6),
                Texto(cx - 88, cy + d + 14, tr("alimentado: vivo a un lado, malla al otro"), 5.6))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- bicónica


def hojas_biconica(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    cono, hueco, alfa, n = g["cono_mm"], g["hueco_mm"], g["semiangulo"], int(g["varillas"])
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, tr("Bicónica · {0} MHz mínimo ({1} varillas por cono)", frecuencia(diseno.f_MHz), n),
                   tr("Dos conos de varillas de Ø {0} mm vértice con vértice · alimentado con coaxial de 50 Ω", fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje de la varilla", u))
    _vista(hoja, diseno, lambda p: (p[0], p[2]), saltar=(1,))
    hoja.anadir(Texto(150, 62, tr("generatriz {0}", longitud(cono, diseno)), 5.6), Texto(150, 68, tr("semiángulo {0}°", fmt(alfa, 0)), 5.6, GRIS),
                Texto(150, 74, tr("hueco {0}", longitud(hueco, diseno, 0)), 5.6))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Medidas desde el centro de la pieza; corta con el sobrante"), VERDE)
    sob = diseno.sobrante_mm
    filas = [
        [tr("Varilla del cono, Ø {0} mm", fmt(d, 1)), str(2 * n), f"{longitud(cono, diseno)} {u}", f"{longitud(cono + sob, diseno, 0)} {u}"],
        [tr("Placa de aluminio Ø 30 × 8 mm"), "2", "—", "—"],
        [tr("Aislador de PVC, {0} mm entre placas", longitud(hueco, diseno, 0)), "1", "—", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 134, tr("Ajuste: la banda baja si alargas los dos conos por igual."), 6.0, VERDE))
    if r:
        seccion(hoja, 128, 91, tr("SIMULADO (NEC2) · SIN MEDIR"), tr("Espacio libre, sin mástil ni cable de bajada"))
        hoja.anadir(Texto(128, 103, tr("ROE < 2 de {0} a {1} MHz ({2}:1)\n{3} dBi a {4} MHz",
                                       fmt(r["f_inferior_roe2_MHz"], 0), fmt(r["f_superior_roe2_MHz"], 0), fmt(r["relacion_banda"], 1),
                                       fmt(r["ganancia_dBi"], 1), fmt(r["f_ganancia_MHz"], 0)), 6.3))
        grafica_roe(hoja, 138, 113, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], (r["f_inferior_roe2_MHz"], r["f_superior_roe2_MHz"]))
    else:
        seccion(hoja, 128, 91, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(128, 103, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("PIEZA CENTRAL Y ÁNGULO DEL CONO"), tr("Escala 1:1 · marca los taladros y el ángulo sobre el papel"), VERDE)
    cx, cy, R = 52.0, 195.0, 15.0
    hoja.anadir(Circulo(cx, cy, R, TINTA, 0.25, None, etiqueta="plantilla:placa"))
    for i in range(n):
        a = 2 * math.pi * i / n
        hoja.anadir(Circulo(cx + R * math.cos(a), cy - R * math.sin(a), max(d, 1.0) / 2 + 0.2, TINTA, 0.15, BLANCO, etiqueta="plantilla:taladro"))
    hoja.anadir(Texto(cx, cy - R - 9, tr("{0} taladros cada {1}° (uno por varilla)", n, fmt(360 / n, 0)), 5.6, ancla="centro"))
    vx, vy, L = 140.0, 232.0, 60.0
    ra = math.radians(alfa)
    hoja.anadir(Linea(vx, vy, vx, vy - L, GRIS, 0.15, (1.5, 1.0), "plantilla:eje"),
                Linea(vx, vy, vx + L * math.sin(ra), vy - L * math.cos(ra), COBRE, max(d, 0.6), None, "plantilla:varilla_cono"),
                Texto(vx + 5.5, vy - 33, fmt(alfa, 0) + "°", 7), Texto(vx - 3, vy - L - 2, tr("eje del cono"), 5.6, ancla="centro"))
    regla(hoja, 14, 244)
    return [hoja]
