"""Generador de planos común al escritorio y a la web lite (Python puro: corre en Pyodide).

    plano = generar(diseno)      # descripción vectorial (hojas en mm reales)
    a_svg(plano.hojas[0])        # vista previa
    a_pdf(plano)                 # para imprimir al 100 % (fpdf2)
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import date

from ..diseno import Diseno
from ..i18n import tr, usar
from . import coaxial, colineal, comun, discone, dipolo, hf, hf_dipolos, hf_vertical, hilos, jpole, koch
from .hoja import Hoja, Plano
from .paginacion import decidir_papel
from .pdf import a_pdf
from .svg import a_svg

GENERADORES = {"dipolo": dipolo.hojas, "jpole": jpole.hojas, "manga": coaxial.hojas_manga, "coco": coaxial.hojas_coco,
               "jpole_koch": koch.hojas, "discone": discone.hojas, "gp": hilos.hojas_gp, "colineal": colineal.hojas, "colineal_bibanda": colineal.hojas,
               "vinv": hilos.hojas_vinv, "yagi": hilos.hojas_yagi, "yagi_bibanda": hilos.hojas_yagi_bibanda, "moxon": hilos.hojas_moxon, "quad": hilos.hojas_quad, "apilados": hilos.hojas_apilados, "biconica": hilos.hojas_biconica,
               "torniquete": hilos.hojas_torniquete, "batwing": hilos.hojas_batwing,
               "efhw": hf.hojas, "dipolo_hf": hf_dipolos.hojas_hilo, "vinv_hf": hf_dipolos.hojas_hilo, "abanico": hf_dipolos.hojas_hilo,
               "trampas": hf_dipolos.hojas_hilo, "g5rv": hf_dipolos.hojas_hilo, "vertical_hf": hf_vertical.hojas}


def generar(diseno: Diseno, fecha: str | None = None) -> Plano:
    fecha = fecha or date.today().strftime("%d-%m-%Y")
    with usar(diseno.plano.idioma):
        hojas = GENERADORES[diseno.tipo](diseno, fecha)
        for n, hoja in enumerate(hojas, start=1):
            escala = tr("1:1 (ver cada vista)") if _tiene_escala_1_1(hoja) else tr("Sin escala")
            if n == 1 and diseno.tipo == "dipolo":
                escala = tr("varias: ver cada vista")
            comun.cajetin(hoja, diseno, escala, n, len(hojas), fecha)
    return Plano(hojas, diseno.nombre)


def _tiene_escala_1_1(hoja: Hoja) -> bool:
    return any(getattr(e, "etiqueta", "").startswith(("regla:", "plantilla:")) for e in hoja.elementos)


def descripcion(plano: Plano) -> list[dict]:
    """La descripción vectorial como datos (para comparar escritorio y Pyodide sin mirar píxeles)."""
    return [{"papel": h.papel, "apaisada": h.apaisada, "escala": h.escala,
             "primitivas": [{"tipo": type(p).__name__, **asdict(p)} for p in h.primitivas()]} for h in plano.hojas]


__all__ = ["Plano", "a_pdf", "a_svg", "decidir_papel", "descripcion", "generar"]
