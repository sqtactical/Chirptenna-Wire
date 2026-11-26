"""Ganancia teórica de cada diseño (dBi), para mostrarla sin necesidad del motor.

`ganancias.json` sale de simular en NEC2 el diseño de partida (o el ajustado, en las colineales y la Yagi) de cada tipo: **en
espacio libre** (los de VHF/UHF) o **sobre suelo normal a 10 m** (los de HF), a la frecuencia por defecto (145 o 7,1 MHz). Es la ganancia
máxima del diagrama, no la de tu instalación. Si el diseño ya trae su simulación (`resultados`), se usa esa.
Python puro (corre en la web).
"""

from __future__ import annotations

import json
from importlib import resources

from .i18n import tr

_tabla: dict | None = None


def tabla() -> dict:
    global _tabla
    if _tabla is None:
        _tabla = json.loads(resources.files("wire").joinpath("ganancias.json").read_text(encoding="utf-8"))
    return _tabla


def _clave(diseno) -> str | None:
    g = diseno.geometria
    if diseno.tipo == "yagi":
        return str(int(g.get("n_elementos", 3)))
    if diseno.tipo in ("colineal", "colineal_bibanda"):
        return str(int(g.get("n_secciones", len(g.get("secciones_mm", [])) or 3)))
    if diseno.tipo == "efhw":
        return str(int(g.get("relacion", 49)))
    return None


def valores(diseno) -> tuple[list[float], bool] | None:
    """([dBi], simulada): un valor (o dos, banda baja y alta, en la bibanda) y si salen de la simulación del propio diseño."""
    r = diseno.resultados
    if r and "ganancia_dBi" in r:
        v = [round(r["ganancia_dBi"], 1)]
        if diseno.tipo == "colineal_bibanda" and "alta" in r:
            v.append(round(r["alta"]["ganancia_dBi"], 1))
        return v, True
    t = tabla().get(diseno.tipo)
    if isinstance(t, dict):
        t = t.get(_clave(diseno))
    if t is None:
        return None
    return (list(t) if isinstance(t, list) else [t]), False


def texto(diseno, fmt) -> str | None:
    """«8,7 dBi · simulada» o «≈ 2,1 dBi · referencia simulada»; la bibanda da las dos bandas."""
    v = valores(diseno)
    if v is None:
        return None
    nums, simulada = v
    if len(nums) == 2:
        cuerpo = tr("{0} dBi en {1} MHz y {2} dBi en {3} MHz", fmt(nums[0], 1), fmt(diseno.f_MHz, 0), fmt(nums[1], 1), fmt(diseno.geometria["f_alta_MHz"], 0))
    else:
        cuerpo = tr("{0} dBi", fmt(nums[0], 1))
    return cuerpo + (tr(" · simulada") if simulada else tr(" · referencia simulada"))


def rango_tipo(tipo: str, fmt) -> str | None:
    """Para la galería: «2,1 dBi» o «8,7–13,2 dBi» según el número de elementos."""
    t = tabla().get(tipo)
    if t is None:
        return None
    if isinstance(t, dict):
        vs = [x for v in t.values() for x in (v if isinstance(v, list) else [v])]
        if min(vs) == max(vs):
            return tr("{0} dBi", fmt(vs[0], 1))
        return tr("{0}–{1} dBi", fmt(min(vs), 1), fmt(max(vs), 1))
    return tr("{0} dBi", fmt(t, 1))
