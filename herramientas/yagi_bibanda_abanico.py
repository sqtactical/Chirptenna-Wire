"""Experimento: Yagi de dos bandas (145 / 433 MHz) con el excitado en abanico, simulada con PyNEC en espacio libre.

    python herramientas/yagi_bibanda_abanico.py

Idea: dos dipolos simples desde el mismo punto de alimentación (uno por banda, el de 433 MHz 8 mm más arriba), un reflector
y un director de 145 MHz y un reflector y dos directores de 433 MHz en el mismo eje (boom). Un solo coaxial de 50 Ω.

Resultado del 27-11 (alambre de 2 mm, sin medir, sin plegado): ROE 1,06 a 145 MHz y 1,05 a 433 MHz, ganancia 6,7 y 6,4 dBi; con
±2 % en cualquiera de las cotas la ROE llega a 1,73 como mucho y de 144 a 146 MHz queda por debajo de 1,15 y de 430 a 440 MHz por
debajo de 1,52. **Dos cotas quedaron en el límite del optimizador** (separación del reflector 0,40 λ de 145 MHz y 8 mm entre los
dos dipolos): hace falta mirarlo antes de hacer de esto un tipo del catálogo (a 25 mm entre dipolos la ROE se quedaba en 1,7).
"""

from __future__ import annotations

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wire import motor  # noqa: E402
from wire.modelo import Barrido, Hilo, Modelo, Puerto  # noqa: E402

C = 299792.458          # km/s: λ(mm) = C / f(MHz)
LB, LA = C / 145.0, C / 433.0


def parametros(x):
    """x = [largo de brazo bajo, id. alto (en λ), separación del reflector (λ145), separación entre dipolos (mm),
    director de 145 (λ145), directores de 433 (λ433)]."""
    kb, ka, y1f, dz, kdb, kda = x
    y1 = y1f * LB
    return dict(y1=y1 / 1000, Lb=kb * LB, La=ka * LA, dz=dz, Rb=0.5 * LB, Ra=0.5 * LA,
                Db=[(kdb * LB, y1 + 0.25 * LB)], Da=[(kda * LA, y1 + 0.2 * LA), (kda * 0.98 * LA, y1 + 0.4 * LA)])


def modelo(p, diametro_mm=2.0):
    r = diametro_mm / 2000
    g = 0.02
    hilos = [Hilo((-g / 2, p["y1"], 0), (g / 2, p["y1"], 0), r, 1)]
    for lado in (1, -1):
        for largo, dz in ((p["Lb"], 0.0), (p["La"], p["dz"])):
            fin = (lado * largo / 2000, p["y1"], dz / 1000)
            ini = (lado * g / 2, p["y1"], 0)
            hilos.append(Hilo(ini, fin, r, max(5, round(math.dist(ini, fin) / 0.02))))

    def pasivo(largo, y, z=0.0):
        return Hilo((-largo / 2000, y / 1000, z / 1000), (largo / 2000, y / 1000, z / 1000), r, max(5, round(largo / 1000 / 0.02)))

    hilos += [pasivo(p["Rb"], 0.0), pasivo(p["Ra"], 0.0, p["dz"])]
    hilos += [pasivo(largo, y) for largo, y in p["Db"]] + [pasivo(largo, y, p["dz"]) for largo, y in p["Da"]]
    return Modelo("Yagi bibanda en abanico", 145.0, tuple(hilos), Puerto(1, 1))


X_MEJOR = [0.4781, 0.4806, 0.3984, 8.1168, 0.3972, 0.3791]

if __name__ == "__main__":
    m = modelo(parametros(X_MEJOR))
    for f in (145.0, 433.0):
        r = motor.simular(m, Barrido(f, f, 1))
        print(f"{f:g} MHz: Z = {r.z[0]:.1f} Ω, ROE {r.roe[0]:.2f}, ganancia {r.ganancia_max[0]:.1f} dBi")
