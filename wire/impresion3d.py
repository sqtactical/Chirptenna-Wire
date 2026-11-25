"""Plantillas de doblado para imprimir en 3D (STL): una placa con dos costillas que guían el alambre.

El alambre se dobla contra las costillas en lugar de sobre el papel. Si la plantilla es mayor que la cama de la
impresora se parte en baldosas que se encajan con pestañas en T (cada pestaña entra en su ranura desde arriba).

Python puro (corre en Pyodide). No usa operaciones booleanas: todo son prismas convexos que se solapan, que los
laminadores (Cura, PrusaSlicer, Bambu Studio…) funden al cortar. Sin probar todavía en una impresora: la holgura de
los encajes es un parámetro.
"""

from __future__ import annotations

import io
import math
import struct
import zipfile
from dataclasses import dataclass, field

from .diseno import Diseno
from .i18n import tr

Punto = tuple[float, float]

TIPOS_3D = ("jpole", "jpole_koch")
MARGEN = 22.0               # mm de placa alrededor del trazado
ESPESOR = 3.0               # mm de la placa
ANCHO_RIEL = 2.0            # mm de cada costilla
TALLO, CABEZA = 6.0, 8.0    # mm: largo del tallo y de la cabeza de la pestaña en T
ANCHO_TALLO, ANCHO_CABEZA = 6.0, 12.0
UNION = TALLO + CABEZA      # lo que sobresale la pestaña
MARGEN_UNION = 22.0         # mm de las pestañas a las esquinas de la baldosa
DISTANCIA_UNION = 14.0      # mm mínimos del centro de una pestaña al alambre
LIMITE_INGLETE = 3.2        # factor máximo del inglete (ángulos de ~35° o más)


@dataclass
class Trazado:
    """El recorrido del alambre en el plano de la plantilla (mm, y hacia arriba)."""

    camino: list[Punto]
    marcas: list[tuple[Punto, Punto]] = field(default_factory=list)   # (punto, dirección del camino) donde marcar la toma
    tope_inicio: bool = False                                          # tope donde apoya la punta del alambre
    avisos: list[str] = field(default_factory=list)


@dataclass
class Plantilla3D:
    piezas: dict[str, bytes]
    mapa_svg: str
    leeme: str
    avisos: list[str]
    columnas: int
    filas: int
    ancho: float
    alto: float


# ---------------------------------------------------------------- geometría 2D

def _unit(a: Punto, b: Punto) -> Punto:
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def _area(poli: list[Punto]) -> float:
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poli, poli[1:] + poli[:1])) / 2


def _recortar(poli: list[Punto], x0: float, y0: float, x1: float, y1: float) -> list[Punto]:
    """Sutherland–Hodgman de un polígono convexo contra un rectángulo."""
    def corta(p, dentro, interseccion):
        salida = []
        for a, b in zip(p, p[1:] + p[:1]):
            da, db = dentro(a), dentro(b)
            if da:
                salida.append(a)
            if da != db:
                salida.append(interseccion(a, b))
        return salida
    for dentro, inter in (
        (lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
        (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
        (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1)),
    ):
        if not poli:
            return []
        poli = corta(poli, dentro, inter)
    return poli if len(poli) >= 3 and abs(_area(poli)) > 1e-6 else []


def _distancia_segmento(p: Punto, a: Punto, b: Punto) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _distancia_camino(p: Punto, camino: list[Punto]) -> float:
    return min(_distancia_segmento(p, a, b) for a, b in zip(camino, camino[1:]))


def _desplazado(camino: list[Punto], lado: int, desp: float) -> list[Punto]:
    """El camino desplazado `desp` mm a la izquierda (lado = 1) o a la derecha (−1), con inglete en los vértices."""
    n = len(camino)
    dirs = [_unit(a, b) for a, b in zip(camino, camino[1:])]
    normales = [(-lado * d[1], lado * d[0]) for d in dirs]
    sal = [(camino[0][0] + normales[0][0] * desp, camino[0][1] + normales[0][1] * desp)]
    for i in range(1, n - 1):
        n0, n1 = normales[i - 1], normales[i]
        k = 1 + n0[0] * n1[0] + n0[1] * n1[1]
        f = desp / max(k, 1.0 / (LIMITE_INGLETE * LIMITE_INGLETE) * 2)
        sal.append((camino[i][0] + (n0[0] + n1[0]) * f, camino[i][1] + (n0[1] + n1[1]) * f))
    sal.append((camino[-1][0] + normales[-1][0] * desp, camino[-1][1] + normales[-1][1] * desp))
    return sal


def rieles(camino: list[Punto], d: float, holgura: float, ancho: float = ANCHO_RIEL) -> list[list[Punto]]:
    """Cuadriláteros convexos de las dos costillas (una a cada lado del alambre)."""
    dentro = d / 2 + holgura
    quads = []
    for lado in (1, -1):
        a, b = _desplazado(camino, lado, dentro), _desplazado(camino, lado, dentro + ancho)
        for i in range(len(camino) - 1):
            q = [a[i], a[i + 1], b[i + 1], b[i]]
            quads.append(q if _area(q) > 0 else q[::-1])
    return quads


# ---------------------------------------------------------------- mallas

def prisma(poli: list[Punto], z0: float, z1: float) -> list[tuple]:
    """Triángulos (a, b, c) de un prisma recto sobre un polígono convexo."""
    if _area(poli) < 0:
        poli = poli[::-1]
    tris = []
    for i in range(1, len(poli) - 1):
        tris.append(((*poli[0], z1), (*poli[i], z1), (*poli[i + 1], z1)))
        tris.append(((*poli[0], z0), (*poli[i + 1], z0), (*poli[i], z0)))
    for a, b in zip(poli, poli[1:] + poli[:1]):
        tris.append(((*a, z0), (*b, z0), (*b, z1)))
        tris.append(((*a, z0), (*b, z1), (*a, z1)))
    return tris


def caja(x0: float, y0: float, x1: float, y1: float, z0: float, z1: float) -> list[tuple]:
    return prisma([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


def a_stl(tris: list[tuple], nombre: str = "Chirptenna Wire") -> bytes:
    out = io.BytesIO()
    out.write(nombre.encode("ascii", "replace")[:80].ljust(80, b" "))
    out.write(struct.pack("<I", len(tris)))
    for a, b, c in tris:
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        v = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
        m = math.sqrt(sum(x * x for x in n)) or 1.0
        out.write(struct.pack("<12fH", n[0] / m, n[1] / m, n[2] / m, *a, *b, *c, 0))
    return out.getvalue()


_SEGMENTOS = {  # a b c d e f g
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg", "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}


def _digitos(texto: str, x: float, y: float, z0: float, alto_z: float = 1.0, ancho: float = 4.0, alto: float = 7.0, trazo: float = 1.2):
    """Cifras de siete segmentos, hechas de cajas, con la esquina inferior izquierda en (x, y)."""
    tris = []
    for k, c in enumerate(texto):
        x0 = x + k * (ancho + 2.0)
        h = alto / 2
        seg = {"a": (x0, y + alto - trazo, x0 + ancho, y + alto), "g": (x0, y + h - trazo / 2, x0 + ancho, y + h + trazo / 2),
               "d": (x0, y, x0 + ancho, y + trazo), "f": (x0, y + h, x0 + trazo, y + alto), "b": (x0 + ancho - trazo, y + h, x0 + ancho, y + alto),
               "e": (x0, y, x0 + trazo, y + h), "c": (x0 + ancho - trazo, y, x0 + ancho, y + h)}
        for s in _SEGMENTOS.get(c, ""):
            tris += caja(*seg[s], z0, z0 + alto_z)
    return tris


def redondear(camino: list[Punto], radio: float) -> tuple[list[Punto], float, int]:
    """Cambia cada esquina por un arco tangente de radio `radio` (al eje del alambre).

    Si los tramos vecinos son demasiado cortos el radio de esa esquina se reduce. Devuelve (camino, radio mínimo
    conseguido, esquinas que se quedaron por debajo del radio pedido)."""
    n = len(camino)
    sal = [camino[0]]
    r_min, reducidas = radio, 0
    for i in range(1, n - 1):
        a, b, c = camino[i - 1], camino[i], camino[i + 1]
        u1, u2 = _unit(a, b), _unit(b, c)
        cos = max(-1.0, min(1.0, u1[0] * u2[0] + u1[1] * u2[1]))
        giro = math.acos(cos)
        if giro < math.radians(1.0):
            sal.append(b)
            continue
        disp = min(math.dist(a, b) / (1 if i == 1 else 2), math.dist(b, c) / (1 if i == n - 2 else 2))
        r = min(radio, disp / math.tan(giro / 2))
        if r < radio * 0.999:
            reducidas += 1
        r_min = min(r_min, r)
        t = r * math.tan(giro / 2)
        p1, p2 = (b[0] - u1[0] * t, b[1] - u1[1] * t), (b[0] + u2[0] * t, b[1] + u2[1] * t)
        signo = 1.0 if u1[0] * u2[1] - u1[1] * u2[0] > 0 else -1.0
        centro = (p1[0] - signo * u1[1] * r, p1[1] + signo * u1[0] * r)
        a0 = math.atan2(p1[1] - centro[1], p1[0] - centro[0])
        pasos = max(2, math.ceil(math.degrees(giro) / 8.0))
        for k in range(pasos + 1):
            ang = a0 + signo * giro * k / pasos
            sal.append((centro[0] + r * math.cos(ang), centro[1] + r * math.sin(ang)))
    sal.append(camino[-1])
    return sal, r_min, reducidas


def _largo(camino: list[Punto]) -> float:
    return sum(math.dist(a, b) for a, b in zip(camino, camino[1:]))


# ---------------------------------------------------------------- trazado de cada tipo

def trazado(diseno: Diseno, largo_guia_mm: float | None = None) -> Trazado:
    if diseno.tipo not in TIPOS_3D:
        raise ValueError(f"el tipo {diseno.tipo} no tiene plantilla 3D todavía (hay: {', '.join(TIPOS_3D)})")
    g = diseno.geometria
    if diseno.tipo == "jpole":
        s, corto, toma = g["separacion_mm"], g["corto_mm"], g["toma_mm"]
        guia = min(corto, largo_guia_mm or 250.0)
        entero = guia >= corto - 1e-6
        t = Trazado([(guia, s), (0.0, s), (0.0, 0.0), (guia, 0.0)], tope_inicio=entero)
        if toma <= guia:
            t.marcas = [((toma, s), (-1.0, 0.0)), ((toma, 0.0), (1.0, 0.0))]
        if not entero:
            t.avisos.append(tr("El brazo corto mide {0} mm y la guía solo {1}: marca el primer doblez a {0} mm de la punta del alambre.",
                               f"{corto:.0f}", f"{guia:.0f}"))
        return t
    from .planos.koch import curva
    s, corto, toma = g["separacion_mm"], g["corto_mm"], g["toma_mm"]
    pts = [(x, z) for x, z in curva(diseno)]
    camino = [(s, corto), (s, 0.0), (0.0, 0.0)] + pts
    return Trazado(camino, marcas=[((s, toma), (0.0, -1.0)), ((0.0, toma), (0.0, 1.0))], tope_inicio=True)


# ---------------------------------------------------------------- baldosas

def _sitios(camino: list[Punto], eje: int, pos: float, a: float, b: float, n_max: int, margen: float) -> tuple[list[float], bool]:
    """Centros (a lo largo de la costura) de las pestañas: los más alejados del alambre, separados al menos 40 mm."""
    largo = b - a
    if largo < 2 * margen:
        return [(a + b) / 2], False
    cand = []
    y = a + margen
    while y <= b - margen + 1e-9:
        c = (pos + UNION / 2, y) if eje == 0 else (y, pos + UNION / 2)
        cand.append((_distancia_camino(c, camino), y))
        y += 2.0
    buenos = sorted((c for c in cand if c[0] >= DISTANCIA_UNION), key=lambda c: -c[0])
    ok = bool(buenos)
    pool = buenos or sorted(cand, key=lambda c: -c[0])
    elegidos: list[float] = []
    for _, y in pool:
        if all(abs(y - e) >= 40.0 for e in elegidos):
            elegidos.append(y)
        if len(elegidos) >= n_max:
            break
    return sorted(elegidos) or [(a + b) / 2], ok


def _rects_ranura(eje: int, pos: float, c: float, holgura: float) -> list[tuple]:
    """Rectángulos (x0, y0, x1, y1) de la ranura en T que empieza en la costura `pos`; `c` es su centro a lo largo de ella."""
    tallo, cabeza = ANCHO_TALLO / 2 + holgura, ANCHO_CABEZA / 2 + holgura
    if eje == 0:      # costura vertical: la ranura entra hacia +x
        return [(pos, c - tallo, pos + TALLO, c + tallo), (pos + TALLO, c - cabeza, pos + UNION, c + cabeza)]
    return [(c - tallo, pos, c + tallo, pos + TALLO), (c - cabeza, pos + TALLO, c + cabeza, pos + UNION)]


def _rects_pestana(eje: int, pos: float, c: float, holgura: float) -> list[tuple]:
    tallo, cabeza = ANCHO_TALLO / 2 - holgura, ANCHO_CABEZA / 2 - holgura
    f = holgura                                    # la pestaña es algo más corta que la ranura
    if eje == 0:
        return [(pos - 0.5, c - tallo, pos + TALLO, c + tallo), (pos + TALLO - 0.5, c - cabeza, pos + UNION - f, c + cabeza)]
    return [(c - tallo, pos - 0.5, c + tallo, pos + TALLO), (c - cabeza, pos + TALLO - 0.5, c + cabeza, pos + UNION - f)]


def _placa(x0: float, y0: float, x1: float, y1: float, huecos: list[tuple], z1: float) -> list[tuple]:
    """Placa rectangular con huecos rectangulares: filas de cajas por una rejilla con los límites de los huecos."""
    xs = sorted({x0, x1, *[min(max(v, x0), x1) for h in huecos for v in (h[0], h[2])]})
    ys = sorted({y0, y1, *[min(max(v, y0), y1) for h in huecos for v in (h[1], h[3])]})
    tris = []
    for ya, yb in zip(ys, ys[1:]):
        inicio = None
        previo = None
        for xa, xb in zip(xs, xs[1:]):
            lleno = not any(h[0] <= xa + 1e-9 and xb <= h[2] + 1e-9 and h[1] <= ya + 1e-9 and yb <= h[3] + 1e-9 for h in huecos)
            if lleno and inicio is None:
                inicio = xa
            if not lleno and inicio is not None:
                tris += caja(inicio, ya, previo, yb, 0.0, z1)
                inicio = None
            previo = xb
        if inicio is not None:
            tris += caja(inicio, ya, previo, yb, 0.0, z1)
    return tris


def generar(diseno: Diseno, cama: tuple[float, float] = (200.0, 200.0), holgura: float = 0.3,
            largo_guia_mm: float | None = None, radio_mm: float | None = None) -> Plantilla3D:
    """Los STL de la plantilla de doblado (uno por baldosa), el mapa de montaje y las instrucciones.

    `radio_mm` es el radio de curvatura al eje del alambre en cada esquina (por defecto 2 × el diámetro, mínimo 3 mm):
    un alambre no hace una esquina viva sin marcarse, y el radio acorta algo el camino respecto al plano."""
    if min(cama) < UNION + 2 * MARGEN_UNION + 20:
        raise ValueError("la cama es demasiado pequeña para las baldosas")
    t = trazado(diseno, largo_guia_mm)
    d = diseno.diametro_mm
    radio = radio_mm if radio_mm is not None else max(2.0 * d, 3.0)
    if radio <= 0:
        raise ValueError("el radio de doblado debe ser positivo")
    vivo = t.camino
    cam, r_min, reducidas = redondear(vivo, radio)
    t.camino = cam
    xs, ys = [p[0] for p in cam], [p[1] for p in cam]
    x_min, x_max, y_min, y_max = min(xs) - MARGEN, max(xs) + MARGEN, min(ys) - MARGEN, max(ys) + MARGEN
    W, H = x_max - x_min, y_max - y_min
    nc = nf = 1
    while (W / nc + (UNION if nc > 1 else 0)) > cama[0]:
        nc += 1
    while (H / nf + (UNION if nf > 1 else 0)) > cama[1]:
        nf += 1
    tw, th = W / nc, H / nf
    avisos = list(t.avisos)
    margen_u = MARGEN_UNION if (nc > 1 and nf > 1) else ANCHO_CABEZA / 2 + 2.0    # sin costuras en la otra dirección no hay esquinas que evitar
    if reducidas:
        avisos.append(tr("El radio de doblado se reduce a {0} mm en {1} esquinas (pedido: {2} mm) porque los tramos son cortos.",
                         f"{r_min:.1f}", str(reducidas), f"{radio:g}"))
    if r_min < 1.5 * d:
        avisos.append(tr("Radio de doblado de {0} mm con alambre de Ø {1} mm: es muy cerrado y el alambre puede marcarse o aplastarse.",
                         f"{r_min:.1f}", f"{d:g}"))
    largo_min = min(math.dist(a, b) for a, b in zip(vivo, vivo[1:]))
    if largo_min < 2 * (d / 2 + holgura + ANCHO_RIEL) + 1:
        avisos.append(tr("Hay tramos de {0} mm: las costillas de los dos lados casi se tocan. Usa un alambre más fino o una iteración menor.",
                         f"{largo_min:.1f}"))
    alto_riel = max(3.0, 1.2 * d)
    quads = rieles(cam, d, holgura)
    # pestañas: costuras verticales (eje 0) entre columnas y horizontales (eje 1) entre filas
    juntas: dict[tuple, list[float]] = {}
    for i in range(1, nc):
        for j in range(nf):
            xs_ = x_min + i * tw
            c, ok = _sitios(cam, 0, xs_, y_min + j * th, y_min + (j + 1) * th, 3, margen_u)
            juntas[("v", i, j)] = c
            if not ok:
                avisos.append(tr("Una unión de la columna {0} cae cerca del alambre: revisa la baldosa antes de imprimir.", str(i)))
    for j in range(1, nf):
        for i in range(nc):
            ys_ = y_min + j * th
            c, ok = _sitios(cam, 1, ys_, x_min + i * tw, x_min + (i + 1) * tw, 3, margen_u)
            juntas[("h", i, j)] = c
            if not ok:
                avisos.append(tr("Una unión de la fila {0} cae cerca del alambre: revisa la baldosa antes de imprimir.", str(j)))

    piezas: dict[str, bytes] = {}
    mapa = []
    for j in range(nf):
        for i in range(nc):
            x0, y0, x1, y1 = x_min + i * tw, y_min + j * th, x_min + (i + 1) * tw, y_min + (j + 1) * th
            huecos, tris = [], []
            if i > 0:                                   # ranuras a la izquierda (las pestañas de la baldosa vecina)
                for c in juntas[("v", i, j)]:
                    huecos += _rects_ranura(0, x0, c, holgura)
            if j > 0:                                   # y abajo
                for c in juntas[("h", i, j)]:
                    huecos += _rects_ranura(1, y0, c, holgura)
            tris += _placa(x0, y0, x1, y1, huecos, ESPESOR)
            if i < nc - 1:                              # pestañas a la derecha
                for c in juntas[("v", i + 1, j)]:
                    for r in _rects_pestana(0, x1, c, holgura):
                        tris += caja(*r, 0.0, ESPESOR)
            if j < nf - 1:                              # y arriba
                for c in juntas[("h", i, j + 1)]:
                    for r in _rects_pestana(1, y1, c, holgura):
                        tris += caja(*r, 0.0, ESPESOR)
            for q in quads:
                r = _recortar(q, x0, y0, x1, y1)
                if r:
                    tris += prisma(r, ESPESOR, ESPESOR + alto_riel)
            tris += _extras(t, d, holgura, alto_riel, x0, y0, x1, y1)
            if nc * nf > 1:
                tris += _etiqueta(f"{i + 1}{j + 1}", cam, x0, y0, x1, y1)
            nombre = "plantilla.stl" if nc * nf == 1 else f"plantilla_c{i + 1}_f{j + 1}.stl"
            piezas[nombre] = a_stl(tris)
            mapa.append((nombre, x0, y0, x1, y1))
    return Plantilla3D(piezas, _mapa_svg(mapa, x_min, y_min, W, H, cam), _leeme(diseno, nc, nf, W, H, cama, holgura, t, alto_riel, radio, _largo(vivo), _largo(cam)),
                       avisos, nc, nf, W, H)


def _extras(t: Trazado, d: float, holgura: float, alto: float, x0, y0, x1, y1) -> list[tuple]:
    """Marcas de la toma (rayitas a los lados de las costillas) y el tope donde apoya la punta del alambre."""
    tris = []
    fuera = d / 2 + holgura + ANCHO_RIEL
    for (px, py), (dx, dy) in t.marcas:
        n = (-dy, dx)
        for lado in (1, -1):
            a = (px + lado * n[0] * fuera, py + lado * n[1] * fuera)
            b = (px + lado * n[0] * (fuera + 6.0), py + lado * n[1] * (fuera + 6.0))
            w = 0.5
            q = [(a[0] + dx * w, a[1] + dy * w), (b[0] + dx * w, b[1] + dy * w), (b[0] - dx * w, b[1] - dy * w), (a[0] - dx * w, a[1] - dy * w)]
            r = _recortar(q if _area(q) > 0 else q[::-1], x0, y0, x1, y1)
            if r:
                tris += prisma(r, ESPESOR, ESPESOR + 1.0)
    if t.tope_inicio:
        (px, py), (qx, qy) = t.camino[0], t.camino[1]
        dx, dy = _unit((px, py), (qx, qy))
        n = (-dy, dx)
        ancho = d / 2 + holgura + ANCHO_RIEL
        q = [(px - dx * 3 + n[0] * ancho, py - dy * 3 + n[1] * ancho), (px + n[0] * ancho, py + n[1] * ancho),
             (px - n[0] * ancho, py - n[1] * ancho), (px - dx * 3 - n[0] * ancho, py - dy * 3 - n[1] * ancho)]
        r = _recortar(q if _area(q) > 0 else q[::-1], x0, y0, x1, y1)
        if r:
            tris += prisma(r, ESPESOR, ESPESOR + alto)
    return tris


def _etiqueta(texto: str, camino: list[Punto], x0, y0, x1, y1) -> list[tuple]:
    """Número de la baldosa (columna y fila) en relieve, en la esquina libre que quede más lejos del alambre."""
    ancho = 4.0 * len(texto) + 2.0 * (len(texto) - 1)
    mejor = None
    for cx, cy in ((x0 + 3, y0 + 3), (x1 - 3 - ancho, y0 + 3), (x0 + 3, y1 - 3 - 7), (x1 - 3 - ancho, y1 - 3 - 7)):
        dist = _distancia_camino((cx + ancho / 2, cy + 3.5), camino)
        if mejor is None or dist > mejor[0]:
            mejor = (dist, cx, cy)
    return _digitos(texto, mejor[1], mejor[2], ESPESOR) if mejor[0] > 9.0 else []


def _mapa_svg(mapa, x_min, y_min, W, H, cam) -> str:
    esc = 480 / max(W, H)
    pts = " ".join(f"{(x - x_min) * esc:.1f},{(H - (y - y_min)) * esc:.1f}" for x, y in cam)
    celdas = "".join(
        f'<rect x="{(x0 - x_min) * esc:.1f}" y="{(H - (y1 - y_min)) * esc:.1f}" width="{(x1 - x0) * esc:.1f}" height="{(y1 - y0) * esc:.1f}" '
        f'fill="none" stroke="#555" stroke-dasharray="4 3"/><text x="{(x0 - x_min) * esc + 6:.1f}" y="{(H - (y1 - y_min)) * esc + 16:.1f}" '
        f'font-size="12" fill="#555">{n[:-4]}</text>' for n, x0, y0, x1, y1 in mapa)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 {W * esc + 12:.0f} {H * esc + 12:.0f}" width="{W * esc + 12:.0f}" '
            f'height="{H * esc + 12:.0f}">{celdas}<polyline points="{pts}" fill="none" stroke="#c8892b" stroke-width="3"/></svg>')


def _leeme(diseno: Diseno, nc: int, nf: int, W: float, H: float, cama: tuple[float, float], holgura: float, t: Trazado, alto: float,
            radio: float, largo_vivo: float, largo_curvo: float) -> str:
    lineas = [
        tr("Plantilla de doblado 3D · {0} a {1} MHz", diseno.nombre_tipo, f"{diseno.f_MHz:g}"),
        "",
        tr("Placa de {0} × {1} mm con dos costillas de {2} mm de alto: el alambre de Ø {3} mm va entre ellas.",
           f"{W:.0f}", f"{H:.0f}", f"{alto:.1f}", f"{diseno.diametro_mm:g}"),
    ]
    lineas.append(tr("Las esquinas llevan un radio de doblado de {0} mm al eje del alambre. El alambre que sigue la plantilla mide {1} mm "
                     "({2} mm con esquinas vivas, como en el plano): {3} mm menos.", f"{radio:g}", f"{largo_curvo:.0f}", f"{largo_vivo:.0f}",
                     f"{largo_vivo - largo_curvo:.1f}"))
    if nc * nf > 1:
        lineas += [tr("No cabe en una cama de {0} × {1} mm: son {2} baldosas ({3} columnas × {4} filas).", f"{cama[0]:g}", f"{cama[1]:g}",
                      str(nc * nf), str(nc), str(nf)),
                   tr("Cada baldosa lleva su número en relieve (columna y fila; la 11 es la de abajo a la izquierda)."),
                   tr("Las pestañas en T de una baldosa entran por arriba en las ranuras de la vecina; pégalas con cianoacrilato si hace falta."),
                   tr("Holgura de los encajes: {0} mm. Si quedan flojos o no entran, cámbiala y vuelve a generar.", f"{holgura:g}")]
    lineas += ["", tr("Imprime con la placa hacia abajo, sin soportes, capas de 0,2 mm y relleno del 20 %."),
               tr("Los STL llevan las costillas y la placa como piezas que se solapan: el laminador las une.")]
    if t.tope_inicio:
        lineas.append(tr("El tope marca la punta del alambre; el sobrante queda en el otro extremo."))
    if t.marcas:
        lineas.append(tr("Las rayitas junto a las costillas marcan la toma del coaxial."))
    lineas += ["", tr("Sin probar en una impresora."), *t.avisos]
    return "\n".join(lineas) + "\n"


def a_zip(p: Plantilla3D) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in p.piezas.items():
            z.writestr(nombre, datos)
        z.writestr("mapa.svg", p.mapa_svg)
        z.writestr("LEEME.txt", p.leeme)
    return out.getvalue()
