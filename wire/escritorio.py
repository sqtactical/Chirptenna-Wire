"""Trabajo pesado de la interfaz de escritorio (en un proceso aparte para no bloquear la página)."""

from __future__ import annotations

from .diseno import disenar


def calcular(tipo: str, f_MHz: float, diametro_mm: float, ajustar: bool, cable: str | None, vf_medido: float | None,
             papel: str, unidades: str, idioma: str, conector: str | None = None, **especificos) -> str:
    """Diseño (ajustado con PyNEC si `ajustar` y está) como texto de `diseno.json`.

    `especificos`: lo propio de cada tipo (`elementos`, `eje`, `eje_mm`, `relacion`, `altura_m`, `suelo`, `potencia_w`,
    `largo_max_m`, `bandas`, `f_alta_MHz`); `disenar` rechaza lo que no vale para el tipo."""
    return disenar(tipo, f_MHz, diametro_mm, ajustar=ajustar, cable=cable, vf_medido=vf_medido, papel=papel,
                   unidades=unidades, idioma=idioma, conector=conector, **especificos).a_json()


def s1p(diseno_json: str) -> str:
    """S11 simulado del diseño en Touchstone (.s1p), para superponerlo a la medida en Chirptenna VNA."""
    from . import touchstone
    from .diseno import Diseno
    return touchstone.s1p(Diseno.desde_json(diseno_json))


def plantilla3d(diseno_json: str, cama_mm: float = 200.0, holgura_mm: float = 0.3, radio_mm: float | None = None) -> bytes:
    """Zip con la plantilla de doblado 3D de un diseño (`wire.impresion3d`)."""
    from . import impresion3d
    from .diseno import Diseno
    from .i18n import usar
    diseno = Diseno.desde_json(diseno_json)
    with usar(diseno.plano.idioma):
        return impresion3d.a_zip(impresion3d.generar(diseno, cama=(cama_mm, cama_mm), holgura=holgura_mm, radio_mm=radio_mm))
