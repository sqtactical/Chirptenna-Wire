"""Cómo imprimir una plantilla 1:1 según su tamaño y el bloque `plano` (docs/PLANOS.md §3).

Fase 1: solo se generan hojas A4 sueltas (vertical o apaisada). La decisión de A3 y mosaico ya se toma aquí para que
la fase 4 solo tenga que dibujarlas.
"""

from __future__ import annotations

from ..diseno import ConfigPlano
from .hoja import PAPELES

MARGEN = 10.0  # mm, marco de la hoja
ALTO_CAJETIN = 44.0  # mm, lo que el cajetín quita al área útil por abajo
CABECERA = 30.0  # mm, título y rótulo de la sección
MAX_HOJAS_MOSAICO = 12  # más de ~4 × 3 hojas: mejor sin escala


def area_util(papel: str, apaisada: bool) -> tuple[float, float]:
    a, b = PAPELES[papel]
    ancho, alto = (b, a) if apaisada else (a, b)
    return ancho - 2 * MARGEN, alto - 2 * MARGEN - ALTO_CAJETIN - CABECERA


def decidir_papel(ancho_mm: float, alto_mm: float, config: ConfigPlano) -> dict:
    """Devuelve {"modo": "hoja" | "A3" | "mosaico" | "sin_escala", "papel", "apaisada", "hojas": (columnas, filas)}."""
    orientaciones = {"auto": (False, True), "vertical": (False,), "apaisada": (True,)}[config.orientacion]

    def cabe(papel: str, apaisada: bool) -> bool:
        w, h = area_util(papel, apaisada)
        return ancho_mm <= w and alto_mm <= h

    for apaisada in orientaciones:
        if cabe(config.papel, apaisada):
            return {"modo": "hoja", "papel": config.papel, "apaisada": apaisada, "hojas": (1, 1)}
    if config.grandes == "A3" and config.papel == "A4":
        for apaisada in orientaciones:
            if cabe("A3", apaisada):
                return {"modo": "A3", "papel": "A3", "apaisada": apaisada, "hojas": (1, 1)}
    if config.grandes == "mosaico":
        w, h = area_util(config.papel, False)
        paso_x, paso_y = w - config.solape_mm, h - config.solape_mm
        columnas = max(1, -int(-(ancho_mm - config.solape_mm) // paso_x))
        filas = max(1, -int(-(alto_mm - config.solape_mm) // paso_y))
        if columnas * filas <= MAX_HOJAS_MOSAICO:
            return {"modo": "mosaico", "papel": config.papel, "apaisada": False, "hojas": (columnas, filas)}
    return {"modo": "sin_escala", "papel": config.papel, "apaisada": False, "hojas": (1, 1)}
