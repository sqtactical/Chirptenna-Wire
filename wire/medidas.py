"""Medidas con el NanoVNA: leer un `.s1p`, compararlo con la simulación y decidir si el diseño pasa a «Medido».

Python puro (corre en Pyodide). Regla (docs/roadmap/fase3.md W3.4): un diseño es «Medido» solo con una medida guardada
cuya frecuencia de referencia (resonancia en el dipolo y la manga; mínimo de ROE en la J-pole y la CoCo) cae a ≤ 2 % de la
simulada.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .diseno import Diseno

TOLERANCIA_PCT = 2.0
Z0 = 50.0
_UNIDAD = {"HZ": 1e-6, "KHZ": 1e-3, "MHZ": 1.0, "GHZ": 1e3}


@dataclass(frozen=True)
class Medida:
    f_MHz: tuple[float, ...]
    s11: tuple[complex, ...]
    z0: float = Z0

    @property
    def z(self) -> tuple[complex, ...]:
        return tuple(self.z0 * (1 + s) / (1 - s) if abs(1 - s) > 1e-12 else complex(1e12, 0) for s in self.s11)

    @property
    def roe(self) -> tuple[float, ...]:
        return tuple((1 + abs(s)) / (1 - abs(s)) if abs(s) < 1 else float("inf") for s in self.s11)


def leer_s1p(texto: str) -> Medida:
    """Touchstone de un puerto (RI, MA o DB; Hz, kHz, MHz o GHz; la referencia R de la cabecera)."""
    escala, formato, z0 = 1.0, "MA", Z0
    f, s = [], []
    for linea in texto.splitlines():
        linea = linea.split("!")[0].strip()
        if not linea:
            continue
        if linea.startswith("#"):
            partes = linea[1:].upper().split()
            for i, p in enumerate(partes):
                if p in _UNIDAD:
                    escala = _UNIDAD[p]
                elif p in ("RI", "MA", "DB"):
                    formato = p
                elif p == "R" and i + 1 < len(partes):
                    z0 = float(partes[i + 1])
            continue
        v = linea.split()
        if len(v) < 3:
            raise ValueError("línea de datos incompleta en el .s1p")
        a, b = float(v[1]), float(v[2])
        if formato == "RI":
            c = complex(a, b)
        elif formato == "MA":
            c = complex(a * math.cos(math.radians(b)), a * math.sin(math.radians(b)))
        else:
            m = 10 ** (a / 20)
            c = complex(m * math.cos(math.radians(b)), m * math.sin(math.radians(b)))
        f.append(float(v[0]) * escala)
        s.append(c)
    if len(f) < 3:
        raise ValueError("el .s1p tiene menos de 3 puntos")
    return Medida(tuple(f), tuple(s), z0)


def minimo_roe(m: Medida, f_min: float | None = None, f_max: float | None = None) -> tuple[float, float]:
    """(frecuencia, ROE) del mínimo, con parábola por los tres puntos del mínimo, dentro de [f_min, f_max]."""
    idx = [i for i, f in enumerate(m.f_MHz) if (f_min is None or f >= f_min) and (f_max is None or f <= f_max)]
    if not idx:
        raise ValueError("la medida no cubre la ventana pedida")
    roe = m.roe
    k = min(idx, key=roe.__getitem__)
    if 0 < k < len(roe) - 1 and all(math.isfinite(roe[j]) for j in (k - 1, k, k + 1)):
        a, b, c = roe[k - 1], roe[k], roe[k + 1]
        den = a - 2 * b + c
        if den > 0:
            d = 0.5 * (a - c) / den
            if abs(d) <= 1:
                paso = m.f_MHz[k + 1] - m.f_MHz[k] if d >= 0 else m.f_MHz[k] - m.f_MHz[k - 1]
                return m.f_MHz[k] + d * paso, b - 0.25 * (a - c) * d
    return m.f_MHz[k], roe[k]


def resonancia(m: Medida, f_min: float, f_max: float) -> float | None:
    """Frecuencia donde la reactancia pasa de − a + (la primera) dentro de la ventana; None si no hay."""
    z = m.z
    for i in range(len(z) - 1):
        if f_min <= m.f_MHz[i] <= f_max and z[i].imag <= 0 < z[i + 1].imag:
            t = -z[i].imag / (z[i + 1].imag - z[i].imag)
            return m.f_MHz[i] + t * (m.f_MHz[i + 1] - m.f_MHz[i])
    return None


def referencia_simulada(diseno: Diseno) -> tuple[float, str]:
    """(frecuencia simulada, «resonancia» o «mínimo de ROE») con la que se compara la medida."""
    r = diseno.resultados or {}
    if diseno.tipo in ("dipolo", "manga") and "f_resonancia_MHz" in r:
        return r["f_resonancia_MHz"], "resonancia"
    if "f_minimo_roe_MHz" in r:
        return r["f_minimo_roe_MHz"], "mínimo de ROE"
    return diseno.f_MHz, "mínimo de ROE"


def comparar(diseno: Diseno, m: Medida) -> dict:
    f_sim, tipo = referencia_simulada(diseno)
    ventana = (0.85 * f_sim, 1.15 * f_sim)
    if tipo == "resonancia":
        f_med = resonancia(m, *ventana)
        if f_med is None:
            tipo = "mínimo de ROE"
    if tipo == "mínimo de ROE":
        f_med = minimo_roe(m, *ventana)[0]
    f_roe, roe_min = minimo_roe(m, *ventana)
    error = (f_med - f_sim) / f_sim * 100
    return {"referencia": tipo, "f_simulada_MHz": f_sim, "f_medida_MHz": f_med, "error_pct": error,
            "coincide": abs(error) <= TOLERANCIA_PCT, "f_minimo_roe_MHz": f_roe, "roe_minima": roe_min}


def guardar_medida(diseno: Diseno, m: Medida, nombre: str = "") -> dict:
    """Guarda la medida en el diseño (curva de ROE y comparación) y lo pasa a «Medido» si cuadra con la simulación."""
    paso = max(1, len(m.f_MHz) // 200)
    c = comparar(diseno, m)
    diseno.medida = {**c, "archivo": nombre, "f_MHz": [round(f, 4) for f in m.f_MHz[::paso]],
                     "roe": [round(r, 3) if math.isfinite(r) else 99.0 for r in m.roe[::paso]]}
    diseno.estado = "Medido" if c["coincide"] and diseno.resultados else diseno.estado
    return diseno.medida
