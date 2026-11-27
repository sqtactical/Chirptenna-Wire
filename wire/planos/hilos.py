"""Hojas de las antenas de alambre sencillas: ground plane, dipolo en V invertida, Yagi de 3 elementos y bicónica.

Cada una lleva una hoja A4: vista general (la proyección del modelo, sin escala), lista de corte, resultados simulados y un
detalle a 1:1 de lo que se pone a mano (el conector, el vértice, el centro del dipolo plegado, la pieza central).
"""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..generadores import correccion_eje_mm
from ..i18n import N_, tr
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import BLANCO, COBRE, CUBIERTA, GRIS, PVC, ROJO, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto
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
    refl, exc = g["reflector_mm"], g["excitado_mm"]
    dires = list(g.get("directores_mm") or [g["director_mm"]])
    seps = list(g.get("seps_directores_mm") or [g["sep_director_mm"]])
    s1, sp = g["sep_reflector_mm"], g["sep_plegado_mm"]
    n = len(dires) + 2
    boom, boom_mm = g.get("boom", "ninguno"), g.get("boom_mm", 0.0)
    corr = correccion_eje_mm(diseno.f_MHz, boom, boom_mm)           # lo que se añade a cada elemento por el eje metálico
    d = diseno.diametro_mm
    u = unidad(diseno)
    ys = [0.0, s1]
    for s in seps:
        ys.append(ys[-1] + s)
    nombres = ["R", "P"] + [f"D{k}" for k in range(1, n - 1)]
    largos = [refl, exc] + dires                                      # los del modelo
    hoja = hoja_a4(diseno, tr("Yagi de {0} elementos · {1} MHz ({2})", n, frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz)),
                   tr("Reflector, dipolo plegado y {0} directores de alambre o varilla de Ø {1} mm sobre un eje · coaxial de 50 Ω", n - 2, fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista desde arriba, sin escala · medidas en {0}", u))
    modelo, esc, P = _vista(hoja, diseno, lambda p: (p[1], p[0]), saltar=(3, 4, 5))
    yb = P((0, 0, 0))[1]
    xs = [P((0, y / 1000, 0))[0] for y in ys]
    hoja.anadir(Linea(xs[0] - 4, yb, xs[-1] + 4, yb, GRIS, 0.5))
    for k, (nom, lg, x) in enumerate(zip(nombres, largos, xs)):
        arriba = yb - esc * lg / 2000 - 3 - (5.5 if k % 2 else 0.0)        # alternos, para que no se pisen
        hoja.anadir(Texto(x, arriba, f"{nom} {longitud(lg + corr, diseno, 0)}", 5.4, ancla="centro"))
    base = yb + esc * max(largos) / 2000 + 6
    for k in range(len(xs) - 1):
        hoja.anadir(Cota(xs[k], base, xs[k + 1], base, longitud(ys[k + 1] - ys[k], diseno, 0), tam=5.0))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    sob = diseno.sobrante_mm
    cierre = sp + d
    filas = [
        [tr("Reflector, Ø {0} mm", fmt(d, 1)), "1", f"{longitud(refl + corr, diseno)} {u}", f"{longitud(refl + corr + sob, diseno, 0)} {u}"],
        [tr("Dipolo plegado, Ø {0} mm", fmt(d, 1)), "2", f"{longitud(exc + corr, diseno)} {u}", f"{longitud(exc + corr + sob, diseno, 0)} {u}"],
        [tr("Cierres del plegado, Ø {0} mm", fmt(d, 1)), "2", f"{longitud(cierre, diseno)} {u}", f"{longitud(cierre + 6, diseno, 0)} {u}"],
    ]
    if n == 3:
        filas.append([tr("Director, Ø {0} mm", fmt(d, 1)), "1", f"{longitud(dires[0] + corr, diseno)} {u}", f"{longitud(dires[0] + corr + sob, diseno, 0)} {u}"])
    else:
        filas.append([tr("Directores, Ø {0} mm", fmt(d, 1)), str(n - 2), tr("hoja 2"), tr("hoja 2")])
    largo_eje = ys[-1] + 120
    eje = {"ninguno": tr("Eje no metálico (PVC o madera barnizada)"), "aislado": tr("Eje metálico Ø {0} mm, elementos aislados", fmt(boom_mm, 0)),
           "unido": tr("Eje metálico Ø {0} mm, elementos unidos", fmt(boom_mm, 0))}[boom]
    filas.append([eje, "1", f"{longitud(largo_eje, diseno, 0)} {u}", "—"])
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    nota = tr("Ajuste: acorta los extremos de todos los elementos por igual; los directores son lo más\ncrítico para la ganancia.")
    r = diseno.resultados
    if r and "ganancia_frente_dBi" in r:
        nota += "\n" + tr("Hacia delante {0} dBi, delante/detrás {1} dB (simulado, en espacio libre).", fmt(r["ganancia_frente_dBi"], 1),
                          fmt(r["relacion_delante_detras_dB"], 0))
    hoja.anadir(Texto(14, 138, nota, 6.0, VERDE))
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
    if n == 3 and boom == "ninguno":
        return [hoja]
    return [hoja, _hoja_elementos_yagi(diseno, nombres, largos, ys, corr, boom, boom_mm, largo_eje)]


def _hoja_elementos_yagi(diseno: Diseno, nombres: list[str], largos: list[float], ys: list[float], corr: float, boom: str,
                         boom_mm: float, largo_eje: float) -> Hoja:
    """Todos los elementos con su posición en el eje y su largo de corte, y lo que se sabe del eje."""
    u = unidad(diseno)
    d = diseno.diametro_mm
    sob = diseno.sobrante_mm
    hoja = hoja_a4(diseno, tr("Yagi · elementos y eje · {0} MHz", frecuencia(diseno.f_MHz)),
                   tr("Posiciones medidas desde el reflector, al eje de cada elemento"))
    seccion(hoja, 14, 33, tr("ELEMENTOS"), tr("Corta con el sobrante; el largo incluye la corrección del eje, si la hay"), VERDE)
    nombre_largo = {"R": tr("Reflector"), "P": tr("Dipolo plegado")}
    filas = []
    for nom, lg, y in zip(nombres, largos, ys):
        filas.append([nombre_largo.get(nom, tr("Director {0}", nom[1:])), f"{longitud(y, diseno, 0)} {u}", f"{longitud(lg + corr, diseno)} {u}",
                      f"{longitud(lg + corr + sob, diseno, 0)} {u}"])
    y_fin = tabla(hoja, 14, 46, [0, 62, 98, 134], [tr("Elemento"), tr("Posición"), tr("Largo final"), tr("Cortar a")], filas, 180)
    y = y_fin + 8
    hoja.anadir(Texto(14, y, tr("Eje de {0} de largo, con unos 60 mm de margen en cada extremo.", longitud(largo_eje, diseno, 0) + " " + u), 6.2))
    y += 12
    if boom == "ninguno":
        texto = tr("Eje no metálico: no hay corrección. Con un eje metálico pasa a otro largo de corte.")
    else:
        texto = tr("Eje metálico de Ø {0} mm con los elementos {1}: cada elemento lleva {2} mm más que en el modelo (corrección de\n"
                   "DL6WU, la mitad si pasan aislados). Es una regla de la bibliografía para ejes de hasta 0,055 λ, sin comprobar con\n"
                   "medidas aquí; sube con la frecuencia. Si cambias el eje, vuelve a generar el plano.",
                   fmt(boom_mm, 0), tr("aislados") if boom == "aislado" else tr("unidos"), fmt(corr, 1))
    hoja.anadir(Texto(14, y, texto, 6.2, VERDE))
    regla(hoja, 14, 244)
    return hoja


# ---------------------------------------------------------------- Moxon

def hojas_moxon(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    a, td, tr_, hu, c = g["ancho_mm"], g["punta_excitado_mm"], g["punta_reflector_mm"], g["hueco_mm"], g["centro_mm"]
    d, u, sob = diseno.diametro_mm, unidad(diseno), diseno.sobrante_mm
    fondo = td + hu + tr_
    hoja = hoja_a4(diseno, _titulo(N_("Moxon rectangular · {0} MHz ({1})"), diseno),
                   tr("Dos elementos de alambre de Ø {0} mm con las puntas enfrentadas · alimentado con coaxial de 50 Ω, sin adaptador", fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista desde arriba, sin escala · el haz sale hacia arriba · medidas en {0} al eje del alambre", u))
    modelo = diseno.modelo()
    us = [p[0] for h in modelo.hilos for p in (h.inicio, h.fin)]
    vs = [p[1] for h in modelo.hilos for p in (h.inicio, h.fin)]
    x0, y0, ancho, alto = 44.0, 54.0, 140.0, 36.0
    esc = min(ancho / (max(us) - min(us)), alto / (max(vs) - min(vs)))
    ox = x0 + (ancho - (max(us) - min(us)) * esc) / 2
    oy = y0 + (alto - (max(vs) - min(vs)) * esc) / 2
    P = lambda p3: (ox + (p3[0] - min(us)) * esc, oy + (max(vs) - p3[1]) * esc)      # noqa: E731
    for i, h in enumerate(modelo.hilos, start=1):
        if i > 1:                                                         # el primero es el tramo del punto de alimentación
            p, q = P(h.inicio), P(h.fin)
            hoja.anadir(Linea(p[0], p[1], q[0], q[1], COBRE, 0.85))
    xi, yf = P((-a / 2000, 0, 0))
    xd, _ = P((a / 2000, 0, 0))
    _, y_td = P((0, -td / 1000, 0))
    _, y_pr = P((0, -(td + hu) / 1000, 0))
    _, y_r = P((0, -fondo / 1000, 0))
    hoja.anadir(Cota(xi, yf - 3, xd, yf - 3, longitud(a, diseno, 0), tam=5.6),
                Cota(xi - 8, yf, xi - 8, y_td, longitud(td, diseno, 0), tam=5.0),
                Cota(xi - 8, y_td, xi - 8, y_pr, longitud(hu, diseno, 0), tam=5.0),
                Cota(xi - 8, y_pr, xi - 8, y_r, longitud(tr_, diseno, 0), tam=5.0),
                Texto((xi + xd) / 2, yf + 5, tr("excitado: coaxial en el centro (vivo a un lado, malla al otro)"), 5.6, ancla="centro"),
                Texto((xi + xd) / 2, y_r + 5, tr("reflector, de una sola pieza"), 5.6, ancla="centro"))
    seccion(hoja, 14, 101, tr("LISTA DE CORTE"), tr("Corta con el sobrante, dobla y ajusta después"), VERDE)
    brazo = a / 2 - c / 2 + td
    refl = a + 2 * tr_
    filas = [
        [tr("Excitado (mitad con su punta), Ø {0} mm", fmt(d, 1)), "2", f"{longitud(brazo, diseno)} {u}", f"{longitud(brazo + sob, diseno, 0)} {u}"],
        [tr("Reflector con sus dos puntas, Ø {0} mm", fmt(d, 1)), "1", f"{longitud(refl, diseno)} {u}", f"{longitud(refl + sob, diseno, 0)} {u}"],
        [tr("Marco de PVC o varilla no metálica"), "1", f"{longitud(a, diseno, 0)} × {longitud(fondo, diseno, 0)} {u}", "—"],
        [tr("Aislador central de PVC, 60 × 25 × 5 mm"), "1", "—", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 113, [0, 52, 62, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 108)
    hoja.anadir(Texto(14, 152, tr("Dobla cada punta a 90° justo en la esquina: los extremos de\nlas puntas quedan enfrentados a {0} y no se tocan.\n"
                                  "Ajuste: acorta o alarga las dos puntas del excitado por\nigual; el hueco entre puntas es lo más sensible.",
                                  longitud(hu, diseno, 0) + " " + u), 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    r = diseno.resultados
    if r and "ganancia_frente_dBi" in r:
        hoja.anadir(Texto(128, 176, tr("Hacia delante {0} dBi, delante/detrás {1} dB\n(simulado, en espacio libre).", fmt(r["ganancia_frente_dBi"], 1),
                                       fmt(r["relacion_delante_detras_dB"], 0)), 6.0))
    hoja.anadir(Texto(14, 200, tr("La Moxon es compacta ({0} de ancho para {1} MHz) y da una relación delante/detrás alta; la polarización\n"
                                  "es la de los elementos (horizontal con ellos en horizontal). Simulada sin mástil ni cable de bajada: el coaxial\n"
                                  "sale por detrás, en ángulo recto con los elementos, y lleva un choke.", longitud(a, diseno, 0) + " " + u, frecuencia(diseno.f_MHz)), 6.0, ROJO))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- Quad cúbica de dos elementos

def hojas_quad(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    le, lr, s, c = g["lado_excitado_mm"], g["lado_reflector_mm"], g["separacion_mm"], g["centro_mm"]
    d, u, sob = diseno.diametro_mm, unidad(diseno), diseno.sobrante_mm
    hoja = hoja_a4(diseno, _titulo(N_("Quad cúbica de 2 elementos · {0} MHz ({1})"), diseno),
                   tr("Dos lazos cuadrados de alambre de Ø {0} mm, el reflector algo mayor y detrás · alimentado con coaxial de 50 Ω, sin adaptador", fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTAS"), tr("Sin escala · el haz sale hacia la derecha en la vista lateral · medidas en {0} al eje del alambre", u))
    esc = 33.0 / lr
    # vista frontal: los dos lazos concéntricos
    fx, fy = 52.0, 48.0 + 33.0                                         # centro en x, base del reflector en y
    z0 = (le - lr) / 2
    def cuadrado(x0, y0, lado, color, grosor=0.85):
        a = lado * esc
        for p, q in (((x0 - a / 2, y0), (x0 + a / 2, y0)), ((x0 + a / 2, y0), (x0 + a / 2, y0 - a)),
                     ((x0 + a / 2, y0 - a), (x0 - a / 2, y0 - a)), ((x0 - a / 2, y0 - a), (x0 - a / 2, y0))):
            hoja.anadir(Linea(p[0], p[1], q[0], q[1], color, grosor))
    cuadrado(fx, fy, lr, ROJO)
    cuadrado(fx, fy - z0 * esc, le, COBRE)
    hoja.anadir(Cota(fx - lr * esc / 2, fy + 3.5, fx + lr * esc / 2, fy + 3.5, longitud(lr, diseno, 0), tam=5.0),
                Texto(fx, fy + 10, tr("vista frontal: excitado {0} (cobre), reflector (rojo)", longitud(le, diseno, 0)), 5.6, ancla="centro"))
    # vista lateral: dos líneas verticales separadas
    sx = 140.0
    hoja.anadir(Linea(sx, fy - z0 * esc, sx, fy - z0 * esc - le * esc, COBRE, 0.85),
                Linea(sx - s * esc, fy, sx - s * esc, fy - lr * esc, ROJO, 0.85),
                Linea(sx - s * esc - 6, fy - lr * esc / 2, sx + 6, fy - lr * esc / 2, GRIS, 0.5),
                Cota(sx - s * esc, fy + 3.5, sx, fy + 3.5, longitud(s, diseno, 0), tam=5.0),
                Texto(sx - s * esc / 2, fy + 10, tr("vista lateral y travesaño"), 5.6, ancla="centro"))
    seccion(hoja, 14, 101, tr("LISTA DE CORTE"), tr("Corta con el sobrante, forma el lazo y ajusta después"), VERDE)
    lazo_e = 4 * le - c
    lazo_r = 4 * lr
    filas = [
        [tr("Lazo excitado, Ø {0} mm (abierto en la fuente)", fmt(d, 1)), "1", f"{longitud(lazo_e, diseno)} {u}", f"{longitud(lazo_e + sob, diseno, 0)} {u}"],
        [tr("Lazo reflector, Ø {0} mm (cerrado)", fmt(d, 1)), "1", f"{longitud(lazo_r, diseno)} {u}", f"{longitud(lazo_r + sob, diseno, 0)} {u}"],
        [tr("Varillas de fibra o PVC para el marco"), "4", f"≈ {longitud(math.hypot(lr, lr) / 2 + s, diseno, 0)} {u}", "—"],
        [tr("Travesaño central de PVC"), "1", f"{longitud(s + 60, diseno, 0)} {u}", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 113, [0, 52, 62, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 108)
    hoja.anadir(Texto(14, 152, tr("Los dos lazos son de una sola pieza con las esquinas dobladas a 90°; el del reflector se cierra\n"
                                  "soldando los extremos. La fuente va en el centro del lado de abajo del excitado (hueco de {0}).\n"
                                  "Ajuste: acorta o alarga el excitado por igual en los cuatro lados.", longitud(c, diseno, 0) + " " + u), 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    r = diseno.resultados
    if r and "ganancia_frente_dBi" in r:
        hoja.anadir(Texto(128, 176, tr("Hacia delante {0} dBi, delante/detrás {1} dB\n(simulado, en espacio libre).", fmt(r["ganancia_frente_dBi"], 1),
                                       fmt(r["relacion_delante_detras_dB"], 0)), 6.0))
    hoja.anadir(Texto(14, 200, tr("Con la fuente abajo la polarización es horizontal; para polarización vertical pon la fuente en el centro de un\n"
                                  "lado (el mismo diseño girado 90°: en espacio libre la ROE no cambia). Simulada sin mástil ni cable de bajada:\n"
                                  "el coaxial sale por detrás y lleva un choke."), 6.0, ROJO))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- Dipolos apilados en fase

def hojas_apilados(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    n = int(g["n_dipolos"])
    largo, sep, lin = g["dipolo_mm"], g["separacion_mm"], g["linea_mm"]
    z0, vf = g["z0_linea"], g["vf_linea"]
    d, u, sob = diseno.diametro_mm, unidad(diseno), diseno.sobrante_mm
    hoja = hoja_a4(diseno, _titulo(N_("Dipolos apilados en fase · {0} MHz ({1})"), diseno),
                   tr("Dipolos de media onda horizontales, uno sobre otro, alimentados en fase con líneas iguales de {0} Ω · coaxial de 50 Ω", fmt(z0, 0)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista de frente, sin escala · medidas en {0} al eje del alambre", u))
    alto = (n - 1) * sep
    esc = min(84.0 / alto, 60.0 / largo)
    cx, y0 = 50.0, 50.0                                                 # eje vertical de los dipolos y arriba del apilado
    ys = [y0 + k * sep * esc for k in range(n)]
    bus = cx + 30.0
    ym = y0 + alto * esc / 2
    for y in ys:
        hoja.anadir(Linea(cx - largo * esc / 2, y, cx + largo * esc / 2, y, COBRE, 0.85),
                    Linea(cx, y, bus, y, ROJO, 0.5, (1.5, 1.0)))
    hoja.anadir(Linea(bus, ys[0], bus, ys[-1], ROJO, 0.5, (1.5, 1.0)),
                Circulo(bus, ym, 1.4, TINTA, 0.2, BLANCO),
                Texto(bus + 3, ym + 1.5, tr("unión: coaxial de 50 Ω a la estación"), 5.6),
                Texto(bus + 3, ys[0] + 1.5, tr("línea de {0} Ω, {1}, igual en todos", fmt(z0, 0), longitud(lin, diseno, 0)), 5.6, ROJO),
                Cota(cx - largo * esc / 2, ys[0] - 3.5, cx + largo * esc / 2, ys[0] - 3.5, longitud(largo, diseno, 0), tam=5.0),
                Cota(cx - largo * esc / 2 - 6, ys[0], cx - largo * esc / 2 - 6, ys[1], longitud(sep, diseno, 0), tam=5.0))
    seccion(hoja, 14, 142, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    brazo = largo / 2
    filas = [
        [tr("Brazo de dipolo, alambre Ø {0} mm", fmt(d, 1)), str(2 * n), f"{longitud(brazo, diseno)} {u}", f"{longitud(brazo + sob, diseno, 0)} {u}"],
        [tr("Línea de fase, coaxial de {0} Ω (VF {1})", fmt(z0, 0), fmt(vf, 2)), str(n), f"{longitud(lin, diseno, 0)} {u}", tr("todas iguales")],
        [tr("Balun 1:1 en el centro de cada dipolo"), str(n), "—", "—"],
        [tr("Mástil no metálico"), "1", f"{longitud(alto + 400, diseno, 0)} {u}", "—"],
        [tr("Conector en el punto de unión"), "1", "—", "—"],
    ]
    tabla(hoja, 14, 154, [0, 60, 72, 94], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 108)
    _simulacion_roe(hoja, diseno)
    hoja.anadir(Texto(14, 196, tr("Ajuste: las cuatro líneas deben ser idénticas (largo y tipo de coaxial); acorta los brazos por igual.\n"
                                  "Las líneas hacen de transformador (75 Ω) y ponen en fase los dipolos: no las acortes ni las dejes de distinto largo.\n"
                                  "Radia hacia los dos lados (perpendicular a los dipolos) y casi nada por los extremos. Simulada con líneas ideales y\n"
                                  "sin mástil: las pérdidas reales del coaxial restan algo de ganancia."), 6.0, ROJO))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- Yagi de dos bandas

def hojas_yagi_bibanda(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    d, u, hueco = diseno.diametro_mm, unidad(diseno), 20.0           # 20 mm entre los dos brazos de cada dipolo (generadores.yagi_bibanda)
    f_alta = g["f_alta_MHz"]
    sob = diseno.sobrante_mm
    dz = g["sep_dipolos_mm"]
    y1 = g["y_excitado_mm"]
    y_dir_b = g["y_director_bajo_mm"]
    dir_a, ys_a = list(g["directores_altos_mm"]), list(g["ys_directores_altos_mm"])
    hoja = hoja_a4(diseno, tr("Yagi bibanda · {0} y {1} MHz", frecuencia(diseno.f_MHz), frecuencia(f_alta)),
                   tr("Dos dipolos desde el mismo punto, reflector y directores de cada banda en un eje · coaxial de 50 Ω · alambre de Ø {0} mm", fmt(d, 1)))
    # --- vista general: elementos verticales, eje horizontal; la banda alta (rojo) se desplaza para que se vea
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista desde arriba, sin escala; la banda alta se dibuja desplazada"))
    modelo = diseno.modelo()
    desplaza = 6.0
    proy = lambda p: (p[1] + desplaza * p[2], p[0])                    # noqa: E731
    segs = [(proy(h.inicio), proy(h.fin)) for h in modelo.hilos]
    us = [p[0] for s in segs for p in s]
    vs = [p[1] for s in segs for p in s]
    x0, y0, ancho, alto = 14.0, 50.0, 94.0, 86.0
    esc = min(ancho / (max(us) - min(us)), alto / (max(vs) - min(vs)))
    ox = x0 + (ancho - (max(us) - min(us)) * esc) / 2
    oy = y0 + (alto - (max(vs) - min(vs)) * esc) / 2
    P = lambda p: (ox + (proy(p)[0] - min(us)) * esc, oy + (max(vs) - proy(p)[1]) * esc)   # noqa: E731
    for i, h in enumerate(modelo.hilos, start=1):
        if i == 1:
            continue                                                   # el tramo del punto de alimentación es de 20 mm
        a, b = P(h.inicio), P(h.fin)
        alta = h.inicio[2] > 1e-9 or h.fin[2] > 1e-9
        hoja.anadir(Linea(a[0], a[1], b[0], b[1], ROJO if alta else COBRE, 0.85))
    xb = P((0, 0, 0))[0]
    yb = P((0, 0, 0))[1]
    hoja.anadir(Linea(P((0, -0.02, 0))[0], yb, P((0, 0.8, 0))[0] + 8, yb, GRIS, 0.5))
    xs = lambda y, alta=False: P((0, y / 1000, dz / 1000 if alta else 0.0))[0]    # noqa: E731
    hoja.anadir(Texto(xs(0.0), oy - 3, "R", 5.6, ancla="centro"), Texto(xs(y1), oy - 3, "P", 5.6, ancla="centro"),
                Texto(xs(y_dir_b), oy - 3, "D", 5.6, ancla="centro"),
                *[Texto(xs(y, True), oy + (max(vs) - min(vs)) * esc + 5, f"d{k}", 5.6, ROJO, ancla="centro") for k, y in enumerate(ys_a, start=1)])
    hoja.anadir(Texto(xs(0.0, True), oy + (max(vs) - min(vs)) * esc + 5, "r", 5.6, ROJO, ancla="centro"),
                Texto(xs(y1, True), oy + (max(vs) - min(vs)) * esc + 5, "p", 5.6, ROJO, ancla="centro"))
    hoja.anadir(Texto(x0, y0 + alto + 10, tr("Negro: banda {0} MHz (R reflector, P excitado, D director).\nRojo: banda {1} MHz (r, p, d1 y d2).", frecuencia(diseno.f_MHz), frecuencia(f_alta)), 5.6, GRIS))
    # --- lista de corte
    seccion(hoja, 112, 33, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    def fila(nombre: str, cant: str, largo: float) -> list[str]:
        return [nombre, cant, f"{longitud(largo, diseno)} {u}", f"{longitud(largo + sob, diseno, 0)} {u}"]
    filas = [fila(tr("Brazo del dipolo {0}", frecuencia(diseno.f_MHz)), "2", g["dipolo_bajo_mm"] / 2 - hueco / 2),
             fila(tr("Brazo del dipolo {0}", frecuencia(f_alta)), "2", g["dipolo_alto_mm"] / 2 - hueco / 2),
             fila(tr("Reflector {0}", frecuencia(diseno.f_MHz)), "1", g["reflector_bajo_mm"]),
             fila(tr("Reflector {0}", frecuencia(f_alta)), "1", g["reflector_alto_mm"]),
             fila(tr("Director {0}", frecuencia(diseno.f_MHz)), "1", g["director_bajo_mm"]),
             fila(tr("Director d1 {0}", frecuencia(f_alta)), "1", dir_a[0]),
             fila(tr("Director d2 {0}", frecuencia(f_alta)), "1", dir_a[1])]
    tabla(hoja, 112, 45, [0, 38, 48, 68], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 90)
    # --- posiciones en el eje
    seccion(hoja, 112, 108, tr("POSICIONES EN EL EJE"), tr("Desde el reflector, al eje de cada elemento"), VERDE)
    pos = [(tr("Reflectores R y r"), 0.0), (tr("Excitado P y p"), y1), (tr("Director D"), y_dir_b), (tr("Director d1"), ys_a[0]), (tr("Director d2"), ys_a[1])]
    tabla(hoja, 112, 120, [0, 52], [tr("Elemento"), tr("Posición")], [[n, f"{longitud(y, diseno, 0)} {u}"] for n, y in pos], 90)
    hoja.anadir(Texto(112, 150, tr("Eje de {0}, con unos 60 mm de margen en cada extremo.\nEje no metálico (PVC o madera): no hay corrección.", longitud(ys_a[1] + 120, diseno, 0) + " " + u), 6.0))
    # --- resultados
    r = diseno.resultados
    if r and "alta" in r:
        for x, y, res, f, nombre in ((14, 168, r, diseno.f_MHz, tr("BANDA BAJA {0} MHz", frecuencia(diseno.f_MHz))),
                                     (112, 168, r["alta"], f_alta, tr("BANDA ALTA {0} MHz", frecuencia(f_alta)))):
            adelante = res.get("ganancia_frente_dBi")
            seccion(hoja, x, y, nombre, tr("ROE {0} · {1} dBi (espacio libre)", fmt(res["roe"], 2), fmt(adelante if adelante is not None else res["ganancia_dBi"], 1)))
            grafica_roe(hoja, x + 8, y + 12, 70, 31, res["barrido"]["f_MHz"], res["barrido"]["roe"], None)
    else:
        seccion(hoja, 14, 168, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(14, 180, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
    hoja.anadir(Texto(14, 225, tr("Los dos dipolos salen del mismo punto: el de la banda alta {0} mm por encima del otro en vertical,\n"
                                  "con un solo coaxial (vivo a un brazo de cada dipolo, malla al otro). Los 20 mm centrales de cada dipolo quedan\n"
                                  "sin hilo: ahí va el coaxial. Simulada en espacio libre, sin medir: los dos dipolos se acoplan, así que el largo\n"
                                  "de cada uno se ajusta con el NanoVNA en su banda (la banda baja es la más sensible: 2 % de largo es ROE 1,3).", fmt(dz, 0)), 6.0, VERDE))
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


# ---------------------------------------------------------------- torniquete


def hojas_torniquete(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    brazo, sep, z0l, vf, linea = g["brazo_mm"], g["sep_mm"], g["z0_linea"], g["vf_linea"], g["linea_mm"]
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, _titulo(N_("Torniquete en X · {0} MHz ({1})"), diseno),
                   tr("Dos dipolos cruzados a 90° y una línea de λ/4 entre sus centros: polarización circular · coaxial de 50 Ω"))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista desde arriba, sin escala · medidas en {0} al eje del alambre", u))
    modelo, esc, P = _vista(hoja, diseno, lambda p: (p[0], p[1]))
    c = P((0, 0, 0))
    hoja.anadir(Texto(c[0] + esc * brazo / 1000 + 3, c[1] + 1.5, tr("brazo {0}", longitud(brazo, diseno, 0)), 5.4),
                Texto(c[0] + 3, c[1] - esc * brazo / 1000 - 1, tr("dipolo 2, {0} más alto", longitud(sep, diseno, 0)), 5.4),
                Texto(c[0] - esc * brazo / 1000, c[1] + 4, tr("dipolo 1, alimentado directo"), 5.4))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    sob = diseno.sobrante_mm
    filas = [
        [tr("Brazo, alambre Ø {0} mm", fmt(d, 1)), "4", f"{longitud(brazo, diseno)} {u}", f"{longitud(brazo + sob, diseno, 0)} {u}"],
        [tr("Línea de coaxial de {0} Ω, VF {1}", fmt(z0l, 0), fmt(vf, 2)), "1", f"{longitud(linea, diseno)} {u}",
         f"{longitud(linea + sob, diseno, 0)} {u}"],
        [tr("Cruceta aislante de PVC o plástico, 2 piezas"), "1", tr("a medida"), "—"],
        [tr("Mástil no metálico, soporte del cruce"), "1", tr("a medida"), "—"],
        [tr("Coaxial RG-58 de 50 Ω, bajada + choke"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    nota = tr("Ajuste: recorta los cuatro brazos por igual. La línea ya sale ajustada por simulación para dar 90° de fase;\n"
              "con otro coaxial recalcúlala (λ/4 × VF).")
    if r and "razon_axial_cenit_dB" in r:
        nota += "\n" + tr("Razón axial hacia el cénit: {0} dB (simulada; 0 dB es circular perfecta).", fmt(r["razon_axial_cenit_dB"], 1))
    hoja.anadir(Texto(14, 138, nota, 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("CENTRO DEL CRUCE"), tr("Escala 1:1 · los dos huecos de alimentación y la línea que los une"), VERDE)
    cx, cy, L, h = 150.0, 186.0, 26.0, 10.0
    hoja.anadir(Rect(cx - L, cy - d / 2, L - h / 2, d, None, relleno=COBRE, etiqueta="plantilla:brazo_1a"),
                Rect(cx + h / 2, cy - d / 2, L - h / 2, d, None, relleno=COBRE, etiqueta="plantilla:brazo_1b"),
                Rect(cx - d / 2, cy - L, d, L - h / 2, None, relleno=CUBIERTA, etiqueta="plantilla:brazo_2a"),
                Rect(cx - d / 2, cy + h / 2, d, L - h / 2, None, relleno=CUBIERTA, etiqueta="plantilla:brazo_2b"),
                Linea(cx + h / 2 + 4, cy - 2, cx + h / 2 + 4, cy - 2 - 22, GRIS, 0.2, (1.4, 0.8)),
                Texto(cx + h / 2 + 8, cy - 12, tr("línea λ/4"), 5.6),
                Cota(cx - h / 2, cy + 9, cx + h / 2, cy + 9, longitud(h, diseno, 0), tam=5.6),
                Texto(14, 168, tr("Dipolo 1 (cobre): el coaxial de bajada se suelda en su hueco,\nvivo a un brazo y malla al otro."), 5.8),
                Texto(14, 182, tr("Dipolo 2 (gris): a {0} por encima, girado 90°, con la línea de λ/4\nsoldada a los dos lados de su hueco.",
                                  longitud(sep, diseno, 0)), 5.8),
                Texto(14, 196, tr("Se dibuja solo el centro: cada brazo mide {0}.", longitud(brazo, diseno, 0)), 5.8, GRIS))
    regla(hoja, 14, 244)
    return [hoja]


# ---------------------------------------------------------------- batwing


def hojas_batwing(diseno: Diseno, fecha: str) -> list[Hoja]:
    g = diseno.geometria
    ala, w, hueco, n = g["ala_mm"], g["ancho_mm"], g["hueco_mm"], int(g["radios"])
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, _titulo(N_("Batwing · {0} MHz ({1})"), diseno),
                   tr("Dipolo con dos alas de abanico de {0} radios de alambre Ø {1} mm · alimentado con coaxial de 50 Ω", n, fmt(d, 1)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje del alambre", u))
    _vista(hoja, diseno, lambda p: (p[0], p[2]), margen_x=46)
    hoja.anadir(Texto(14, 56, tr("ala {0}", longitud(ala, diseno)), 5.6), Texto(14, 62, tr("ancho de punta {0}", longitud(w, diseno)), 5.6),
                Texto(14, 68, tr("hueco {0}", longitud(hueco, diseno, 0)), 5.6, GRIS))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Medidas desde el vértice; corta con el sobrante"), VERDE)
    sob = diseno.sobrante_mm
    largos: dict[float, int] = {}
    for i in range(n):
        z = abs(w / 2 - w * i / (n - 1))
        largos[round(math.hypot(ala, z), 1)] = largos.get(round(math.hypot(ala, z), 1), 0) + 2
    filas = [[tr("Radio, alambre Ø {0} mm", fmt(d, 1)), str(c), f"{longitud(lg, diseno)} {u}", f"{longitud(lg + sob, diseno, 0)} {u}"]
             for lg, c in sorted(largos.items())]
    filas.append([tr("Borde de la punta, Ø {0} mm", fmt(d, 1)), "2", f"{longitud(w, diseno)} {u}", f"{longitud(w + sob, diseno, 0)} {u}"])
    filas.append([tr("Aislador central de PVC y coaxial de 50 Ω"), "1", "—", "—"])
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    nota = tr("Ajuste: alarga o acorta las alas por igual; los radios se sueldan al borde de la punta.")
    if r and r.get("f_inferior_roe2_MHz"):
        nota += "\n" + tr("ROE < 2 de {0} a {1} MHz ({2} % de ancho de banda, simulado).",
                          fmt(r["f_inferior_roe2_MHz"], 0), fmt(r["f_superior_roe2_MHz"], 0), fmt(r["ancho_roe2_pct"], 0))
    hoja.anadir(Texto(14, 140, nota, 6.0, VERDE))
    _simulacion_roe(hoja, diseno)
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("VÉRTICE Y ABANICO"), tr("Escala 1:1 · los radios salen del hueco central"), VERDE)
    vx, vy, L = 105.0, 200.0, 60.0
    for s in (1, -1):
        for i in range(n):
            z = (w / 2 - w * i / (n - 1))
            norma = math.hypot(ala, z)
            hoja.anadir(Linea(vx + s * hueco / 2, vy, vx + s * (hueco / 2 + L * ala / norma), vy - L * z / norma, COBRE, max(d, 0.6), None,
                              "plantilla:radio"))
    hoja.anadir(Rect(vx - hueco / 2 - 2, vy - 4, hueco + 4, 8, TINTA, 0.18, PVC, etiqueta="plantilla:aislador"),
                Cota(vx - hueco / 2, vy + 12, vx + hueco / 2, vy + 12, longitud(hueco, diseno, 0), tam=5.6),
                Texto(vx, vy + 22, tr("coaxial: vivo a un lado, malla al otro"), 5.6, ancla="centro"))
    regla(hoja, 14, 244)
    return [hoja]
