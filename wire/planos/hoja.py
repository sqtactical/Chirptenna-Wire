"""Descripción vectorial de las hojas: primitivas en mm reales del papel, origen arriba a la izquierda y y hacia abajo
(como SVG y fpdf2). Las salidas SVG y PDF solo saben dibujar estas primitivas; las cotas y los rayados se descomponen
aquí, en código común, para que las dos salidas sean idénticas.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from functools import lru_cache
from importlib import resources

PT = 25.4 / 72  # mm por punto tipográfico

PAPELES = {"A4": (210.0, 297.0), "A3": (297.0, 420.0)}

TINTA, GRIS, GRIS_CLARO = "#1f2a24", "#6d7680", "#c9cdd2"
COBRE, VERDE, ROJO = "#c8892b", "#2f6b3a", "#b04a3a"
CUBIERTA, PVC, DIELECTRICO, BLANCO = "#26292c", "#efeadf", "#f1efe6", "#ffffff"


@dataclass(frozen=True)
class Linea:
    x1: float
    y1: float
    x2: float
    y2: float
    color: str = TINTA
    grosor: float = 0.18  # mm
    discontinua: tuple[float, float] | None = None  # (trazo, hueco) en mm
    etiqueta: str = ""

    @property
    def caja(self):
        return min(self.x1, self.x2), min(self.y1, self.y2), max(self.x1, self.x2), max(self.y1, self.y2)

    @property
    def longitud(self) -> float:
        return math.hypot(self.x2 - self.x1, self.y2 - self.y1)


@dataclass(frozen=True)
class Polilinea:
    puntos: tuple[tuple[float, float], ...]
    color: str | None = TINTA
    grosor: float = 0.18
    cerrada: bool = False
    relleno: str | None = None
    etiqueta: str = ""

    @property
    def caja(self):
        xs, ys = zip(*self.puntos)
        return min(xs), min(ys), max(xs), max(ys)


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    ancho: float
    alto: float
    color: str | None = TINTA  # None: sin borde
    grosor: float = 0.18
    relleno: str | None = None
    etiqueta: str = ""

    @property
    def caja(self):
        return self.x, self.y, self.x + self.ancho, self.y + self.alto


@dataclass(frozen=True)
class Circulo:
    cx: float
    cy: float
    r: float
    color: str | None = TINTA
    grosor: float = 0.18
    relleno: str | None = None
    discontinua: tuple[float, float] | None = None
    etiqueta: str = ""

    @property
    def caja(self):
        return self.cx - self.r, self.cy - self.r, self.cx + self.r, self.cy + self.r


@dataclass(frozen=True)
class Arco:
    """Arco de circunferencia de `desde` a `hasta` grados (0° a la derecha, sentido horario con y hacia abajo)."""

    cx: float
    cy: float
    r: float
    desde: float
    hasta: float
    color: str = TINTA
    grosor: float = 0.18
    etiqueta: str = ""

    def puntos(self, n: int = 32) -> tuple[tuple[float, float], ...]:
        a, b = math.radians(self.desde), math.radians(self.hasta)
        return tuple((self.cx + self.r * math.cos(a + (b - a) * i / n), self.cy + self.r * math.sin(a + (b - a) * i / n))
                     for i in range(n + 1))

    @property
    def caja(self):
        return Polilinea(self.puntos()).caja


@dataclass(frozen=True)
class Texto:
    """Texto en la línea base `y`. `ancla`: izquierda, centro o derecha. Tamaño en puntos. Admite varias líneas."""

    x: float
    y: float
    texto: str
    tam: float = 7.0
    color: str = TINTA
    estilo: str = "normal"  # normal, negrita, cursiva
    ancla: str = "izquierda"
    fondo: str | None = None  # color de una caja detrás del texto
    rotacion: float = 0.0  # grados, antihorario (solo 0 y 90 en las cajas)
    etiqueta: str = ""

    INTERLINEA = 1.25

    @property
    def lineas(self) -> list[str]:
        return self.texto.split("\n")

    def ancho(self) -> float:
        return max(ancho_texto(l, self.tam, self.estilo) for l in self.lineas)

    @property
    def caja(self):
        alto_em = self.tam * PT
        ancho = self.ancho()
        x0 = {"izquierda": 0.0, "centro": -ancho / 2, "derecha": -ancho}[self.ancla]
        arriba = -0.76 * alto_em
        abajo = 0.24 * alto_em + (len(self.lineas) - 1) * self.INTERLINEA * alto_em
        if self.rotacion == 90:  # gira alrededor de (x, y): lo que era x pasa a ser -y
            return self.x + arriba, self.y - (x0 + ancho), self.x + abajo, self.y - x0
        return self.x + x0, self.y + arriba, self.x + x0 + ancho, self.y + abajo


@dataclass(frozen=True)
class Imagen:
    """Recurso de `wire/planos/recursos` (por ahora solo el logo SVG), encajado en la caja dada."""

    x: float
    y: float
    ancho: float
    alto: float
    recurso: str = "grillo-wire.svg"
    etiqueta: str = ""

    @property
    def caja(self):
        return self.x, self.y, self.x + self.ancho, self.y + self.alto


@dataclass(frozen=True)
class Cota:
    """Cota lineal entre dos puntos, con flechas y el texto centrado sobre fondo blanco.

    `ref1`/`ref2`: puntos de la pieza desde los que salen las líneas de referencia hasta los extremos de la cota.
    """

    x1: float
    y1: float
    x2: float
    y2: float
    texto: str
    tam: float = 6.5
    ref1: tuple[float, float] | None = None
    ref2: tuple[float, float] | None = None
    texto_en: float = 0.5  # posición del texto a lo largo de la cota (0–1)
    etiqueta: str = ""

    def primitivas(self) -> list:
        dx, dy = self.x2 - self.x1, self.y2 - self.y1
        largo = math.hypot(dx, dy)
        ux, uy = dx / largo, dy / largo
        px, py = -uy, ux
        flecha = min(1.8, largo / 3)
        out: list = []
        for r, (ex, ey) in ((self.ref1, (self.x1, self.y1)), (self.ref2, (self.x2, self.y2))):
            if r is not None:
                out.append(Linea(r[0], r[1], ex, ey, GRIS, 0.12))
        out.append(Linea(self.x1, self.y1, self.x2, self.y2, TINTA, 0.15, etiqueta=self.etiqueta))
        for (ax, ay), s in (((self.x1, self.y1), 1), ((self.x2, self.y2), -1)):
            punta = (ax, ay)
            base = (ax + s * ux * flecha, ay + s * uy * flecha)
            out.append(Polilinea((punta, (base[0] + px * flecha * 0.3, base[1] + py * flecha * 0.3),
                                  (base[0] - px * flecha * 0.3, base[1] - py * flecha * 0.3)),
                                 color=None, cerrada=True, relleno=TINTA))
        tx = self.x1 + dx * self.texto_en
        ty = self.y1 + dy * self.texto_en
        vertical = abs(dx) < 1e-9
        alto = self.tam * PT
        if vertical:  # texto girado, de abajo arriba
            out.append(Texto(tx + 0.36 * alto, ty, self.texto, self.tam, ancla="centro", fondo=BLANCO, rotacion=90,
                             etiqueta=self.etiqueta))
        else:
            out.append(Texto(tx, ty + 0.36 * alto, self.texto, self.tam, ancla="centro", fondo=BLANCO,
                             etiqueta=self.etiqueta))
        return out

    @property
    def caja(self):
        return union_cajas([p.caja for p in self.primitivas()])


@dataclass
class Hoja:
    papel: str = "A4"
    apaisada: bool = False
    elementos: list = field(default_factory=list)
    escala: str = "Sin escala"  # lo que dice el cajetín
    titulo: str = ""
    marco: tuple[float, float, float, float] = (10.0, 10.0, 200.0, 287.0)  # área útil (x0, y0, x1, y1)
    cajetin: tuple[float, float, float, float] | None = None  # caja del cajetín (x0, y0, x1, y1)

    @property
    def tamano(self) -> tuple[float, float]:
        a, b = PAPELES[self.papel]
        return (b, a) if self.apaisada else (a, b)

    def anadir(self, *elementos) -> None:
        self.elementos.extend(elementos)

    def primitivas(self) -> list:
        """Elementos con las cotas descompuestas: lo único que dibujan las salidas."""
        out = []
        for e in self.elementos:
            out.extend(e.primitivas() if isinstance(e, Cota) else [e])
        return out


@dataclass
class Plano:
    hojas: list[Hoja]
    nombre: str = ""


def union_cajas(cajas):
    x0, y0, x1, y1 = zip(*cajas)
    return min(x0), min(y0), max(x1), max(y1)


def se_solapan(a, b, holgura: float = 0.0) -> bool:
    return a[0] < b[2] - holgura and b[0] < a[2] - holgura and a[1] < b[3] - holgura and b[1] < a[3] - holgura


def dentro(a, b) -> bool:
    return a[0] >= b[0] and a[1] >= b[1] and a[2] <= b[2] and a[3] <= b[3]


# ---------------------------------------------------------------- recursos y medida del texto

FUENTES = {"normal": "DejaVuSans.ttf", "negrita": "DejaVuSans-Bold.ttf", "cursiva": "DejaVuSans-Oblique.ttf"}


def recurso(nombre: str) -> bytes:
    return resources.files("wire.planos").joinpath("recursos", nombre).read_bytes()


def ruta_recurso(nombre: str) -> str:
    return str(resources.files("wire.planos").joinpath("recursos", nombre))


@lru_cache(maxsize=None)
def _anchos(estilo: str) -> tuple[dict[int, int], int, int]:
    """Avance de cada carácter (unidades de la fuente), avance por defecto y unidades por em (con fontTools)."""
    from io import BytesIO

    from fontTools.ttLib import TTFont

    fuente = TTFont(BytesIO(recurso(FUENTES[estilo])), lazy=True)
    hmtx = fuente["hmtx"].metrics
    anchos = {c: hmtx[g][0] for c, g in fuente.getBestCmap().items()}
    return anchos, hmtx[".notdef"][0], fuente["head"].unitsPerEm


def ancho_texto(texto: str, tam_pt: float, estilo: str = "normal") -> float:
    """Ancho en mm de una línea de texto en DejaVu Sans (la misma fuente que lleva el PDF)."""
    anchos, defecto, em = _anchos(estilo)
    return sum(anchos.get(ord(c), defecto) for c in texto) / em * tam_pt * PT


def rayado(x: float, y: float, ancho: float, alto: float, paso: float, color: str, grosor: float = 0.12) -> list:
    """Rayado cruzado (malla del coaxial) recortado al rectángulo."""
    lineas = []
    n = int((ancho + alto) / paso) + 1
    for i in range(n + 1):
        k = x - alto + i * paso
        for a, b in (((k, y), (k + alto, y + alto)), ((k, y + alto), (k + alto, y))):  # diagonales a 45° y −45°
            seg = _recortar(*a, *b, x, y, x + ancho, y + alto)
            if seg:
                lineas.append(Linea(*seg, color=color, grosor=grosor))
    return lineas


def _recortar(x1, y1, x2, y2, xmin, ymin, xmax, ymax):
    """Liang–Barsky."""
    dx, dy = x2 - x1, y2 - y1
    t0, t1 = 0.0, 1.0
    for p, q in ((-dx, x1 - xmin), (dx, xmax - x1), (-dy, y1 - ymin), (dy, ymax - y1)):
        if p == 0:
            if q < 0:
                return None
            continue
        t = q / p
        if p < 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1:
            return None
    if t1 - t0 < 1e-9:
        return None
    return x1 + t0 * dx, y1 + t0 * dy, x1 + t1 * dx, y1 + t1 * dy
