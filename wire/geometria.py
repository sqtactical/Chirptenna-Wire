"""Geometría de las curvas de las antenas de alambre (Python puro, sin numpy: corre en Pyodide).

La curva de Koch sale del sistema L `F → F+F--F+F` con giro de 60°, ajustada para ir de un punto a otro. El algoritmo
(`sistema_l`, `tortuga`, `ajustar_extremos`, `koch`) es el de Chirptenna (`antenas/geometria.py`, mismo autor, AGPL-3.0),
reescrito sin numpy; no se importa ese repositorio.
"""

from __future__ import annotations

import math

Punto2 = tuple[float, float]


def sistema_l(axioma: str, reglas: dict[str, str], iteraciones: int) -> str:
    s = axioma
    for _ in range(iteraciones):
        s = "".join(reglas.get(c, c) for c in s)
    return s


def tortuga(cadena: str, angulo_grados: float, paso: float = 1.0) -> list[Punto2]:
    """Recorre la cadena: F avanza dibujando, + gira a la izquierda y − a la derecha."""
    x = y = a = 0.0
    da = math.radians(angulo_grados)
    puntos = [(x, y)]
    for c in cadena:
        if c in "FG":
            x += paso * math.cos(a)
            y += paso * math.sin(a)
            puntos.append((round(x, 9), round(y, 9)))
        elif c == "+":
            a += da
        elif c == "-":
            a -= da
    return puntos


def ajustar_extremos(puntos: list[Punto2], p0: Punto2, p1: Punto2) -> list[Punto2]:
    """Escala y gira una polilínea para que vaya exactamente de p0 a p1."""
    (ax, ay), (bx, by) = puntos[0], puntos[-1]
    vx, vy = bx - ax, by - ay
    wx, wy = p1[0] - p0[0], p1[1] - p0[1]
    escala = math.hypot(wx, wy) / math.hypot(vx, vy)
    giro = math.atan2(wy, wx) - math.atan2(vy, vx)
    c, s = math.cos(giro) * escala, math.sin(giro) * escala
    return [((x - ax) * c - (y - ay) * s + p0[0], (x - ax) * s + (y - ay) * c + p0[1]) for x, y in puntos]


def koch(iteraciones: int, p0: Punto2 = (0.0, 0.0), p1: Punto2 = (1.0, 0.0), angulo: float = 60.0) -> list[Punto2]:
    """Curva de Koch de `iteraciones` niveles entre p0 y p1: 4**n tramos iguales de longitud |p1 − p0| / 3**n."""
    pts = tortuga(sistema_l("F", {"F": "F+F--F+F"}, iteraciones), angulo)
    ajustados = ajustar_extremos(pts, p0, p1)
    ajustados[0], ajustados[-1] = p0, p1   # extremos exactos (sin redondeo)
    return ajustados


def longitud(puntos: list[Punto2]) -> float:
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(puntos, puntos[1:]))


def koch_hacia_fuera(iteraciones: int, p0: Punto2, p1: Punto2) -> list[Punto2]:
    """Curva de Koch entre p0 y p1 con sus muescas, en su mayoría, hacia la izquierda del sentido p0 → p1."""
    izquierda = koch(iteraciones, p0, p1)
    derecha = _espejo(izquierda, p0, p1)
    # Elige el lado con más puntos a la izquierda del eje p0 → p1.
    def lado(pts: list[Punto2]) -> float:
        return sum((p1[0] - p0[0]) * (y - p0[1]) - (p1[1] - p0[1]) * (x - p0[0]) for x, y in pts)
    return izquierda if lado(izquierda) >= lado(derecha) else derecha


def _espejo(puntos: list[Punto2], p0: Punto2, p1: Punto2) -> list[Punto2]:
    """Refleja la curva respecto a la recta p0 → p1."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy)
    ux, uy = dx / n, dy / n
    out = []
    for x, y in puntos:
        rx, ry = x - p0[0], y - p0[1]
        t = rx * ux + ry * uy
        px, py = p0[0] + t * ux, p0[1] + t * uy
        out.append((2 * px - x, 2 * py - y))
    out[0], out[-1] = p0, p1
    return out
