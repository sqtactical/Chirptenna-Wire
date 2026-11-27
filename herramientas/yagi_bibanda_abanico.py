"""Yagi de dos bandas (145 / 433 MHz) con el excitado en abanico: comprobación del tipo `yagi_bibanda` con PyNEC.

    python herramientas/yagi_bibanda_abanico.py

Idea: dos dipolos simples desde el mismo punto de alimentación (uno por banda; el de 433 MHz 25 mm más arriba), un reflector y
un director de 145 MHz y un reflector y dos directores de 433 MHz en el mismo eje (boom). Un solo coaxial de 50 Ω.

Las cotas de `generadores.YAGIB_X` salen de optimizar (27-11, alambre de 2 mm, sin medir, espacio libre) la ROE de las dos bandas
**y la dirección del haz** (la primera versión, solo con la ROE, daba ROE 1,05 pero el haz de 433 MHz salía de lado, φ 205°):
ROE ≈ 1,0 a 145 y 433 MHz, 6,3 dBi hacia delante en las dos. Con ±2 % en cualquier cota la ROE llega a 1,81 como mucho (la que
más pesa es el largo del dipolo de 145 MHz), la separación entre dipolos de 15 a 35 mm apenas cambia nada, y de 144 a 146 MHz la
ROE queda por debajo de 1,08 y de 430 a 440 MHz por debajo de 1,63. Los reflectores salen de 0,66 y 0,64 λ (el de 145 MHz ≈ 2 λ de
433 MHz): sirven a las dos bandas a la vez.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wire import generadores, motor  # noqa: E402
from wire.modelo import Barrido  # noqa: E402

if __name__ == "__main__":
    m = generadores.yagi_bibanda(145.0, 2.0)
    for f in (145.0, 145.0 * generadores.YAGIB_RAZON):
        r = motor.simular(m, Barrido(f, f, 1))
        delante = motor.ganancias_en(m, f, [(90.0, 90.0)])[0]
        print(f"{f:.0f} MHz: Z = {r.z[0]:.1f} Ω, ROE {r.roe[0]:.2f}, ganancia máx. {r.ganancia_max[0]:.1f} dBi, hacia delante {delante:.1f} dBi")
