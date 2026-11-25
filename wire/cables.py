"""Tabla de cables coaxiales: impedancia, factor de velocidad (VF), medidas y pérdida.

Los números son los **típicos de las hojas de datos de los fabricantes** (Belden 8219/8259, Times Microwave LMR-400,
Aircell 7 de Eurocable/Kabelwerk, Huber+Suhner H155, MIL-C-17 para RG-174/316/213). Están escritos de memoria del tipo de
cable, **sin comprobar uno por uno contra la hoja concreta**: `verificado = False` hasta que alguien lo haga, y el plano
lo dirá. El VF de catálogo es una aproximación (cambia con el lote y el dieléctrico): mejor medir el del cable del
usuario (`con_vf_medido`). La pérdida solo sirve para avisar en tiradas largas: NEC2 modela la línea sin pérdidas.

Python puro (corre en Pyodide).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Cable:
    nombre: str
    z0: float                       # Ω
    vf: float                       # factor de velocidad, (0, 1]
    diametro_exterior_mm: float     # cubierta
    diametro_malla_mm: float        # exterior de la malla (el hilo que radia en NEC2)
    diametro_dielectrico_mm: float
    perdida_100MHz_dB_100m: float
    perdida_1000MHz_dB_100m: float
    vf_origen: str = "catálogo"     # «catálogo» o «medido»
    verificado: bool = False        # ¿se han comprobado las cifras contra la hoja de datos?

    def __post_init__(self) -> None:
        if not 0 < self.vf <= 1:
            raise ValueError("el factor de velocidad debe estar en (0, 1]")
        if self.vf_origen not in ("catálogo", "medido"):
            raise ValueError("vf_origen debe ser «catálogo» o «medido»")

    @property
    def radio_malla_m(self) -> float:
        return self.diametro_malla_mm / 2000.0

    def perdida_dB(self, f_MHz: float, longitud_m: float) -> float:
        """Pérdida (dB) de `longitud_m` a `f_MHz`: ley de raíz de f entre los dos puntos de la hoja de datos."""
        a1, a2 = self.perdida_100MHz_dB_100m, self.perdida_1000MHz_dB_100m
        exponente = math.log(a2 / a1) / math.log(10.0)
        return a1 * (f_MHz / 100.0) ** exponente * longitud_m / 100.0

    def con_vf_medido(self, vf: float) -> "Cable":
        """El mismo cable con el VF medido por el usuario (sustituye al de catálogo)."""
        return replace(self, vf=vf, vf_origen="medido")


CABLES: dict[str, Cable] = {c.nombre: c for c in (
    Cable("RG-58", 50.0, 0.66, 4.95, 2.95 + 0.9, 2.95, 16.9, 54.0),
    Cable("RG-174", 50.0, 0.66, 2.8, 1.5 + 0.6, 1.5, 32.0, 105.0),
    Cable("RG-316", 50.0, 0.69, 2.5, 1.52 + 0.4, 1.52, 27.0, 85.0),
    Cable("RG-213", 50.0, 0.66, 10.3, 7.24 + 1.0, 7.24, 8.2, 27.0),
    Cable("LMR-400", 50.0, 0.85, 10.29, 7.24 + 0.4, 7.24, 3.9, 12.8),
    Cable("Aircell 7", 50.0, 0.83, 7.3, 4.9 + 0.7, 4.9, 8.0, 28.0),
    Cable("H155", 50.0, 0.79, 5.4, 2.8 + 0.9, 2.8, 12.0, 38.0),
)}


def cable(nombre: str) -> Cable:
    if nombre not in CABLES:
        raise ValueError(f"cable desconocido: {nombre} (hay: {', '.join(CABLES)})")
    return CABLES[nombre]
