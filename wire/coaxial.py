"""Tramos de cable coaxial para el modelo NEC2 (Python puro).

La malla exterior es un hilo con el radio exterior de la malla (es lo que radia) y el interior, una línea de
transmisión (`TL`) cuya longitud eléctrica es la física dividida entre el VF del cable (`docs/roadmap/nec2.md` §5–§6).
"""

from __future__ import annotations

import math

from .cables import Cable
from .modelo import Hilo, Linea, Punto


def tramo_coaxial(p0: Punto, p1: Punto, cable: Cable, segmentos: int, indice_hilo: int,
                  longitud_cable_m: float | None = None) -> tuple[Hilo, Linea]:
    """(hilo de la malla, línea interior) de un tramo de coaxial entre `p0` y `p1` (metros).

    `indice_hilo` es el número (desde 1) que tendrá el hilo de la malla en el `Modelo`; la línea une el primer y el
    último segmento de ese hilo. `longitud_cable_m` es la longitud física del cable si no coincide con la distancia
    entre los extremos (cable plegado o con vueltas); por defecto, la distancia.
    """
    hilo = Hilo(p0, p1, cable.radio_malla_m, segmentos)
    longitud = hilo.longitud if longitud_cable_m is None else longitud_cable_m
    linea = Linea(indice_hilo, 1, indice_hilo, segmentos, cable.z0, longitud, cable.vf)
    return hilo, linea


def longitud_cuarto_de_onda_m(f_MHz: float, cable: Cable) -> float:
    """Longitud física de λ/4 dentro del cable: λ·VF/4."""
    return 299_792_458.0 / (f_MHz * 1e6) * cable.vf / 4.0


def impedancia_stub_abierto(z0: float, longitud_electrica_m: float, f_MHz: float) -> complex:
    """Impedancia de entrada de una línea sin pérdidas abierta en el extremo: −j·Z0·cot(β·l)."""
    beta_l = 2 * math.pi * longitud_electrica_m * f_MHz * 1e6 / 299_792_458.0
    return complex(0.0, -z0 / math.tan(beta_l))
