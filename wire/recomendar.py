"""Qué antena elegir: a una frecuencia, con una ganancia mínima y un tamaño máximo, ordena los tipos que cumplen.

Usa la ganancia teórica de `ganancias.json` (de referencia, en espacio libre en VHF/UHF y sobre suelo normal a 10 m en HF) y el
tamaño de las cotas de partida de cada diseño: no simula nada, así que sirve también en la web. Es una guía para empezar, no una
garantía: la ganancia de tu instalación depende del entorno.
"""

from __future__ import annotations

import math

from . import ganancias
from .diseno import TIPOS, disenar

# (tipo, número de elementos o secciones o None): lo que se compara en cada rango de frecuencia
VHF = ([("dipolo", None), ("jpole", None), ("gp", None), ("vinv", None), ("torniquete", None), ("batwing", None)]
       + [("colineal", n) for n in (2, 3, 4, 5, 6)] + [("yagi", n) for n in (3, 5, 7, 10, 15)])
HF = [("dipolo_hf", None), ("vinv_hf", None), ("efhw", None), ("g5rv", None), ("vertical_hf", None)]


def _tamano_m(diseno) -> float:
    """La mayor dimensión de la antena (m): el largo, el ancho o el alto de los hilos del modelo."""
    puntos = [p for h in diseno.modelo().hilos for p in (h.inicio, h.fin)]
    return max(max(p[i] for p in puntos) - min(p[i] for p in puntos) for i in range(3))


def recomendar(f_MHz: float, ganancia_min: float | None = None, tamano_max_m: float | None = None, diametro_mm: float = 3.0) -> list[dict]:
    """Los tipos que cumplen, de más a menos ganancia (y a igualdad, de más pequeño a más grande).

    Cada uno: `tipo`, `elementos`, `nombre`, `ganancia_dBi`, `tamano_m`. Vacío si ninguno cumple."""
    if f_MHz <= 0:
        raise ValueError("la frecuencia debe ser positiva")
    candidatos = HF if f_MHz < 30 else VHF
    if f_MHz < 1.8 or f_MHz > 1300:
        raise ValueError("hay antenas de alambre para de 1,8 a 30 MHz (HF) y de 30 a 1300 MHz (VHF/UHF)")
    salida = []
    for tipo, n in candidatos:
        try:
            d = disenar(tipo, f_MHz, diametro_mm, ajustar=False, **({"elementos": n} if n else {}))
            g = ganancias.valores(d)
            tam = _tamano_m(d)
        except (ValueError, KeyError):
            continue                                              # el tipo no vale a esa frecuencia
        if g is None or not math.isfinite(tam):
            continue
        ganancia = g[0][0]
        if (ganancia_min is not None and ganancia < ganancia_min) or (tamano_max_m is not None and tam > tamano_max_m):
            continue
        nombre = TIPOS[tipo] + (f" ({n})" if n else "")
        salida.append({"tipo": tipo, "elementos": n, "nombre": nombre, "ganancia_dBi": ganancia, "tamano_m": tam})
    return sorted(salida, key=lambda r: (-r["ganancia_dBi"], r["tamano_m"]))
