"""Tramos de cable coaxial para el modelo NEC2 (Python puro).

La malla exterior es un hilo con el radio exterior de la malla (es lo que radia) y el interior, una línea de
transmisión (`TL`) cuya longitud eléctrica es la física dividida entre el VF del cable (`docs/roadmap/nec2.md` §5–§6).
"""

from __future__ import annotations

import math

from .cables import Cable
from .generadores import segmentos_para
from .modelo import Carga, Hilo, Linea, Modelo, Puerto, Punto, longitud_onda_m


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


def dipolo_con_bajada(f_MHz: float, cable: Cable, largo_mm: float | None = None, bajada_m: float | None = None,
                      choke_ohm: float | None = 1500.0, resto_m: float | None = None,
                      segmentos: int | None = None, axial: bool = False) -> Modelo:
    """Dipolo de media onda de coaxial (eje z) con el cable de bajada como un hilo más (docs/roadmap/nec2.md §6).

    El dipolo se parte en tres hilos (brazo de abajo, segmento central con la fuente y brazo de arriba) para que el
    cable pueda salir de la unión; el exterior de la malla baja `bajada_m` (por defecto λ/2) hasta el choke, en
    horizontal (eje −x) o, con `axial`, colgando en línea con el dipolo (eje −z, donde más perturba), una carga resistiva `choke_ohm` en el último segmento (1–2 kΩ; `None`, sin choke), y sigue `resto_m`
    más (por defecto λ/2: el cable hasta el equipo). Con choke se corta la corriente de modo común y la impedancia se
    acerca a la del dipolo aislado.
    """
    lam = longitud_onda_m(f_MHz)
    largo = largo_mm / 1000 if largo_mm else 0.48 * lam
    n = segmentos or segmentos_para(largo, lam)
    if n % 2 == 0:
        raise ValueError("el dipolo necesita un número impar de segmentos")
    radio = cable.radio_malla_m
    delta = largo / n
    medio = (n - 1) // 2
    z_bajo, z_alto = -delta / 2, delta / 2
    hilos = [Hilo((0.0, 0.0, -largo / 2), (0.0, 0.0, z_bajo), radio, medio),
             Hilo((0.0, 0.0, z_bajo), (0.0, 0.0, z_alto), radio, 1),
             Hilo((0.0, 0.0, z_alto), (0.0, 0.0, largo / 2), radio, medio)]
    bajada = lam / 2 if bajada_m is None else bajada_m
    resto = lam / 2 if resto_m is None else resto_m
    cargas = []
    if bajada > 0:
        n_b = max(2, round(bajada / delta))
        # perpendicular: sale de la unión central hacia −x; axial: continúa el brazo de abajo hacia −z (el cable
        # colgando bajo la antena, el caso malo).
        origen = (0.0, 0.0, -largo / 2) if axial else (0.0, 0.0, z_bajo)
        paso = (0.0, 0.0, -1.0) if axial else (-1.0, 0.0, 0.0)
        choke_en = tuple(o + p * bajada for o, p in zip(origen, paso))
        fin = tuple(o + p * (bajada + resto) for o, p in zip(origen, paso))
        hilos.append(Hilo(origen, choke_en, radio, n_b))
        if choke_ohm:
            cargas.append(Carga(len(hilos), n_b, n_b, r=float(choke_ohm)))
        if resto > 0:
            hilos.append(Hilo(choke_en, fin, radio, max(2, round(resto / delta))))
    nombre = "Dipolo de coaxial con bajada" + (" y choke" if bajada > 0 and choke_ohm else "")
    return Modelo(nombre, f_MHz, tuple(hilos), Puerto(2, 1), cargas=tuple(cargas),
                  comentarios=(f"{nombre} a {f_MHz:g} MHz, cable {cable.nombre}",
                               f"Dipolo {largo * 1000:.1f} mm, bajada {bajada * 1000:.0f} mm, choke {choke_ohm or 0:g} ohm"))


def longitud_cuarto_de_onda_m(f_MHz: float, cable: Cable) -> float:
    """Longitud física de λ/4 dentro del cable: λ·VF/4."""
    return 299_792_458.0 / (f_MHz * 1e6) * cable.vf / 4.0


def impedancia_stub_abierto(z0: float, longitud_electrica_m: float, f_MHz: float) -> complex:
    """Impedancia de entrada de una línea sin pérdidas abierta en el extremo: −j·Z0·cot(β·l)."""
    beta_l = 2 * math.pi * longitud_electrica_m * f_MHz * 1e6 / 299_792_458.0
    return complex(0.0, -z0 / math.tan(beta_l))
