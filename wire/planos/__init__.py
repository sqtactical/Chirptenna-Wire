"""Generador de planos común al escritorio y a la web lite (Python puro: corre en Pyodide).

    plano = generar(diseno)      # descripción vectorial (hojas en mm reales)
    a_svg(plano.hojas[0])        # vista previa
    a_pdf(plano)                 # para imprimir al 100 % (fpdf2)
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from ..diseno import Diseno
from . import comun, dipolo, jpole
from .hoja import Hoja, Plano
from .paginacion import decidir_papel
from .pdf import a_pdf
from .svg import a_svg

GENERADORES = {"dipolo": dipolo.hojas, "jpole": jpole.hojas}


def generar(diseno: Diseno, fecha: str | None = None) -> Plano:
    fecha = fecha or date.today().strftime("%d-%m-%Y")
    hojas = GENERADORES[diseno.tipo](diseno, fecha)
    for n, hoja in enumerate(hojas, start=1):
        escala = "1:1 (ver cada vista)" if _tiene_escala_1_1(hoja) else "Sin escala"
        if n == 1 and diseno.tipo == "dipolo":
            escala = "varias: ver cada vista"
        comun.cajetin(hoja, diseno, escala, n, len(hojas), fecha)
    return Plano(hojas, diseno.nombre)


def _tiene_escala_1_1(hoja: Hoja) -> bool:
    return any(getattr(e, "etiqueta", "").startswith("regla:") for e in hoja.elementos)


def descripcion(plano: Plano) -> list[dict]:
    """La descripción vectorial como datos (para comparar escritorio y Pyodide sin mirar píxeles)."""
    return [{"papel": h.papel, "apaisada": h.apaisada, "escala": h.escala,
             "primitivas": [{"tipo": type(p).__name__, **asdict(p)} for p in h.primitivas()]} for h in plano.hojas]


__all__ = ["Plano", "a_pdf", "a_svg", "decidir_papel", "descripcion", "generar"]
