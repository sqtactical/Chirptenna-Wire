"""Puerta de entrada de la web lite (Pyodide): funciones con texto JSON de entrada y de salida.

Sin motor (PyNEC no corre en el navegador): el diseño sale con las cotas de partida y el estado «Sin validar», salvo
que se abra un `diseno.json` ya ajustado en escritorio (trae sus resultados y su estado). Python puro.
"""

from __future__ import annotations

import json

from . import nec, planos
from .diseno import BANDAS, ESTADOS, TIPOS, ConfigPlano, Diseno, disenar

VERSION_API = 1


def catalogo() -> str:
    return json.dumps({
        "version_api": VERSION_API,
        "tipos": [{"clave": c, "nombre": n} for c, n in TIPOS.items()],
        "estados": list(ESTADOS),
        "bandas": [{"nombre": n, "f_min": a, "f_max": b} for n, a, b in BANDAS],
        "plano": {k: list(v) for k, v in ConfigPlano.VALORES.items()},
    }, ensure_ascii=False)


def _diseno(entrada: str) -> Diseno:
    datos = json.loads(entrada)
    if "diseno" in datos:  # un diseno.json abierto desde el escritorio
        return Diseno.desde_dict(datos["diseno"])
    plano = {k: datos[k] for k in ("papel", "unidades") if k in datos}
    return disenar(datos["tipo"], float(datos["f_MHz"]), float(datos.get("diametro_mm", 2.0)), ajustar=False, **plano)


def disenar_json(entrada: str) -> str:
    """{tipo, f_MHz, diametro_mm, papel, unidades} o {diseno: {...}} → diseno.json."""
    return _diseno(entrada).a_json()


def plano_svg(entrada: str) -> str:
    """Igual entrada → {nombre, estado, hojas: [svg…]}."""
    diseno = _diseno(entrada)
    plano = planos.generar(diseno)
    return json.dumps({"nombre": diseno.nombre, "estado": diseno.estado, "tipo": diseno.nombre_tipo,
                       "f_MHz": diseno.f_MHz, "hojas": [planos.a_svg(h) for h in plano.hojas],
                       "diseno": diseno.a_dict()}, ensure_ascii=False)


def plano_pdf(entrada: str) -> bytes:
    return planos.a_pdf(planos.generar(_diseno(entrada)))


def nec_texto(entrada: str) -> str:
    return nec.exportar(_diseno(entrada).modelo())
