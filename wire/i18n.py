"""Idiomas de Chirptenna Wire: el castellano es el texto fuente y la clave (estilo gettext).

    tr("texto {0}", x)   traduce con el catálogo del idioma activo y formatea (si falta la traducción sale el castellano)
    usar("en")           idioma activo dentro de un bloque `with` (el plano lo usa con `diseno.plano.idioma`)

Un idioma es `wire/idiomas/<código>.json` con `_nombre` y `textos`. Python puro (corre en Pyodide).
Reglas: todo texto nuevo que ve el usuario va con `tr(...)`; nada de `tr` a nivel de módulo (se evalúa al importar, con
el idioma equivocado); en f-strings, `tr("plantilla {0:.1f}", valor)`, nunca un f-string dentro de `tr`.
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from importlib import resources

IDIOMAS = ("es", "en", "fr", "de")
_actual = "es"
_cache: dict[str, dict[str, str]] = {}


def catalogo(codigo: str) -> dict[str, str]:
    """Las traducciones de `codigo` (vacío para el castellano o si no hay archivo)."""
    if codigo not in _cache:
        try:
            texto = resources.files("wire").joinpath("idiomas", f"{codigo}.json").read_text(encoding="utf-8")
            _cache[codigo] = json.loads(texto)["textos"]
        except (FileNotFoundError, OSError, KeyError, ValueError):
            _cache[codigo] = {}
    return _cache[codigo]


def idioma() -> str:
    return _actual


@contextmanager
def usar(codigo: str):
    """Activa `codigo` mientras dure el bloque."""
    global _actual
    if codigo not in IDIOMAS:
        raise ValueError(f"idioma desconocido: {codigo}")
    anterior, _actual = _actual, codigo
    try:
        yield
    finally:
        _actual = anterior


def tr(texto: str, *args) -> str:
    traducido = catalogo(_actual).get(texto, texto) if _actual != "es" else texto
    return traducido.format(*args) if args else traducido


def N_(texto: str) -> str:
    """Solo marca el texto para el extractor; se traduce al mostrarlo (`tr(valor)`)."""
    return texto


def fijar(codigo: str) -> None:
    """Fija el idioma de todo el proceso (interfaz de un solo usuario); para planos usa `usar`."""
    global _actual
    if codigo not in IDIOMAS:
        raise ValueError(f"idioma desconocido: {codigo}")
    _actual = codigo


def separador_decimal() -> str:
    return "." if _actual == "en" else ","
