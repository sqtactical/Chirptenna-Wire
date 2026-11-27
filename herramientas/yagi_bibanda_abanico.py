"""Experimento: Yagi de dos bandas (145 / 433 MHz) con el excitado en abanico, simulada con PyNEC en espacio libre.

    python herramientas/yagi_bibanda_abanico.py

Idea: dos dipolos simples desde el mismo punto de alimentación (uno por banda; el de 433 MHz `DZ_MM` más arriba), un reflector y
un director de 145 MHz y un reflector y dos directores de 433 MHz en el mismo eje (boom). Un solo coaxial de 50 Ω.

Resultado del 27-11 (alambre de 2 mm, sin medir, sin plegado), optimizado con la ROE de las dos bandas **y la dirección del haz**
(la primera versión, solo con la ROE, daba ROE 1,05 pero el haz de 433 MHz salía de lado, φ 205°): ROE 1,00 a 145 y 433 MHz,
6,3 dBi hacia delante en las dos. Con ±2 % en cualquier cota la ROE llega a 1,81 como mucho (la que más pesa es el largo del
dipolo de 145 MHz), la separación entre dipolos de 15 a 35 mm apenas cambia nada, y de 144 a 146 MHz la ROE queda por debajo de
1,08 y de 430 a 440 MHz por debajo de 1,63. Ninguna cota está en el límite del optimizador salvo la distancia del director de
145 MHz al excitado (0,098 λ; el límite era 0,08). Los reflectores salen de 0,66 y 0,64 λ (uno de ellos ≈ 2 λ de 433 MHz): sirven
a las dos bandas a la vez.
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
DZ_MM = 25.0


def parametros(x, dz=DZ_MM):
    """x = [dipolo de 145 (λ145), dipolo de 433 (λ433), reflector a (λ145), director de 145 (λ145), directores de 433 (λ433),
    reflector de 145 (λ145), reflector de 433 (λ433), director de 145 al excitado (λ145), 1.er director de 433 al excitado (λ433)]."""
    kb, ka, y1f, kdb, kda, krb, kra, sdb, sda = x
    y1 = y1f * LB
    return dict(y1=y1 / 1000, Lb=kb * LB, La=ka * LA, dz=dz, Rb=krb * LB, Ra=kra * LA,
                Db=[(kdb * LB, y1 + sdb * LB)], Da=[(kda * LA, y1 + sda * LA), (kda * 0.98 * LA, y1 + 2 * sda * LA)])


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


X_MEJOR = [0.4858, 0.2844, 0.2385, 0.4155, 0.4651, 0.6578, 0.6389, 0.0983, 0.1634]

if __name__ == "__main__":
    m = modelo(parametros(X_MEJOR))
    for f in (145.0, 433.0):
        r = motor.simular(m, Barrido(f, f, 1))
        delante = motor.ganancias_en(m, f, [(90.0, 90.0)])[0]
        print(f"{f:g} MHz: Z = {r.z[0]:.1f} Ω, ROE {r.roe[0]:.2f}, ganancia máx. {r.ganancia_max[0]:.1f} dBi, hacia delante {delante:.1f} dBi")
