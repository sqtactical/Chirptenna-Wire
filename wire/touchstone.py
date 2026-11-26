"""S11 simulado en Touchstone (.s1p) para superponerlo a la medida en Chirptenna VNA (o en cualquier otro programa).

Chirptenna VNA carga un .s1p como referencia (línea gris sobre el gráfico de ROE, con la diferencia punto a punto y
la desviación de la resonancia). Este módulo saca ese archivo del modelo de hilos con PyNEC, a la impedancia de referencia
de 50 Ω del NanoVNA. Es lo simulado en espacio libre (o sobre el suelo del diseño): no incluye cable, mástil ni entorno.
"""

from __future__ import annotations

import unicodedata

from . import motor
from .diseno import Diseno
from .modelo import Barrido

PUNTOS = 201


def rango_MHz(diseno: Diseno) -> tuple[float, float]:
    """Rango del barrido: el de la gráfica de ROE del diseño si la tiene; si no, ±10 % de la frecuencia."""
    b = (diseno.resultados or {}).get("barrido")
    if b and len(b["f_MHz"]) > 1:
        return min(b["f_MHz"]), max(b["f_MHz"])
    return 0.9 * diseno.f_MHz, 1.1 * diseno.f_MHz


def s1p(diseno: Diseno, f_ini_MHz: float | None = None, f_fin_MHz: float | None = None, puntos: int = PUNTOS) -> str:
    """Texto .s1p (RI, 50 Ω, MHz) del S11 simulado del diseño entre `f_ini_MHz` y `f_fin_MHz`."""
    if not motor.disponible():
        raise RuntimeError("PyNEC no está instalado: no se puede simular el S11")
    a, b = rango_MHz(diseno)
    f_ini = a if f_ini_MHz is None else f_ini_MHz
    f_fin = b if f_fin_MHz is None else f_fin_MHz
    if not 0 < f_ini < f_fin or puntos < 2:
        raise ValueError("el rango de frecuencias debe ser creciente y con al menos 2 puntos")
    r = motor.simular(diseno.modelo(), Barrido(f_ini, f_fin, puntos), diagrama=False)
    nombre = unicodedata.normalize("NFKD", diseno.nombre_tipo).encode("ascii", "ignore").decode()   # comentarios en ASCII
    lineas = [f"! Chirptenna Wire: {nombre} a {diseno.f_MHz:g} MHz",
              "! S11 simulado con NEC2 (PyNEC), espacio libre salvo el suelo del diseno; sin cable ni entorno; NO es una medida",
              "# MHz S RI R 50"]
    lineas += [f"{f:.6f} {g.real:.8f} {g.imag:.8f}" for f, g in zip(r.frecuencias, r.s11)]
    return "\n".join(lineas) + "\n"
