"""Trabajo pesado de la interfaz de escritorio (en un proceso aparte para no bloquear la página)."""

from __future__ import annotations

from .diseno import disenar


def calcular(tipo: str, f_MHz: float, diametro_mm: float, ajustar: bool, cable: str | None, vf_medido: float | None,
             papel: str, unidades: str, idioma: str, conector: str | None = None) -> str:
    """Diseño (ajustado con PyNEC si `ajustar` y está) como texto de `diseno.json`."""
    return disenar(tipo, f_MHz, diametro_mm, ajustar=ajustar, cable=cable, vf_medido=vf_medido, papel=papel,
                   unidades=unidades, idioma=idioma, conector=conector).a_json()
