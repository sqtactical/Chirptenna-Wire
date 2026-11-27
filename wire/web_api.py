"""Puerta de entrada de la web lite (Pyodide): funciones con texto JSON de entrada y de salida.

Sin motor (PyNEC no corre en el navegador): el diseño sale con las cotas de partida y el estado «Sin validar», salvo
que se abra un `diseno.json` ya ajustado en escritorio (trae sus resultados y su estado). Python puro.
"""

from __future__ import annotations

import json

from . import nec, planos
from .i18n import IDIOMAS, tr, usar
from .cables import CABLES
from . import ganancias
from .planos.comun import fmt
from .diseno import BANDAS, CATEGORIAS, CONECTORES, ESTADO_TIPO, ESTADOS, RESUMEN, TIPOS, TIPOS_COAXIAL, ConfigPlano, Diseno, disenar
from .generadores import TIPOS_HF
from .aisladores import TIPOS_AISLADORES
from .impresion3d import TIPOS_3D
from .miniaturas import MINIATURAS

VERSION_API = 1


def catalogo(idioma: str = "es") -> str:
    with usar(idioma if idioma in IDIOMAS else "es"):
        return _catalogo()


def _catalogo() -> str:
    return json.dumps({
        "version_api": VERSION_API,
        "tipos": [{"clave": c, "nombre": tr(n), "resumen": tr(RESUMEN[c]), "estado": tr(ESTADO_TIPO[c]), "miniatura": MINIATURAS[c],
                   "ganancia": ganancias.rango_tipo(c, fmt)}
                  for c, n in TIPOS.items()],
        "categorias": [{"clave": c, "nombre": tr(n), "tipos": list(t)} for c, n, t in CATEGORIAS],
        "estados": list(ESTADOS),
        "bandas": [{"nombre": tr(n), "f_min": a, "f_max": b} for n, a, b in BANDAS],
        "plano": {k: list(v) for k, v in ConfigPlano.VALORES.items()},
        "plantilla3d": list(TIPOS_3D),
        "aisladores": list(TIPOS_AISLADORES),
        "tipos_hf": list(TIPOS_HF),
        "conectores": list(CONECTORES), "coaxial": {"tipos": list(TIPOS_COAXIAL), "cables": [{"nombre": c.nombre, "vf": c.vf} for c in CABLES.values()]},
    }, ensure_ascii=False)


def _diseno(entrada: str) -> Diseno:
    datos = json.loads(entrada)
    idioma = datos.get("idioma")
    if "diseno" in datos:  # un diseno.json abierto desde el escritorio
        diseno = Diseno.desde_dict(datos["diseno"])
        if idioma in IDIOMAS:
            diseno.plano.idioma = idioma
        return diseno
    plano = {k: datos[k] for k in ("papel", "unidades", "idioma") if k in datos}
    return disenar(datos["tipo"], float(datos["f_MHz"]), float(datos.get("diametro_mm", 2.0)), ajustar=False,
                   cable=datos.get("cable"), vf_medido=datos.get("vf_medido"), conector=datos.get("conector"),
                   elementos=datos.get("elementos"), eje=datos.get("eje"), eje_mm=datos.get("eje_mm"), relacion=datos.get("relacion"),
                   altura_m=datos.get("altura_m"), suelo=datos.get("suelo"), potencia_w=datos.get("potencia_w"),
                   largo_max_m=datos.get("largo_max_m"), bandas=datos.get("bandas"), f_alta_MHz=datos.get("f_alta_MHz"), **plano)


def disenar_json(entrada: str) -> str:
    """{tipo, f_MHz, diametro_mm, papel, unidades} o {diseno: {...}} → diseno.json."""
    return _diseno(entrada).a_json()


def _nombre_tipo(diseno: Diseno) -> str:
    with usar(diseno.plano.idioma):
        return diseno.nombre_tipo


def plano_svg(entrada: str) -> str:
    """Igual entrada → {nombre, estado, hojas: [svg…]}."""
    diseno = _diseno(entrada)
    plano = planos.generar(diseno)
    with usar(diseno.plano.idioma):
        ganancia = ganancias.texto(diseno, fmt)
    return json.dumps({"nombre": diseno.nombre, "estado": diseno.estado, "tipo": _nombre_tipo(diseno), "ganancia": ganancia,
                       "f_MHz": diseno.f_MHz, "hojas": [planos.a_svg(h) for h in plano.hojas],
                       "diseno": diseno.a_dict()}, ensure_ascii=False)


def plano_pdf(entrada: str) -> bytes:
    return planos.a_pdf(planos.generar(_diseno(entrada)))


def nec_texto(entrada: str) -> str:
    return nec.exportar(_diseno(entrada).modelo())


def recomendar_json(entrada: str) -> str:
    """{f_MHz, ganancia_dBi, tamano_m, diametro_mm, idioma} (los tres últimos opcionales) → {filas: [{tipo, elementos, nombre,
    ganancia_dBi, tamano_m}], error}. Sin simular: ganancias teóricas y cotas de partida."""
    from . import recomendar
    datos = json.loads(entrada)
    idioma = datos.get("idioma")
    with usar(idioma if idioma in IDIOMAS else "es"):
        try:
            filas = recomendar.recomendar(float(datos["f_MHz"]), datos.get("ganancia_dBi"), datos.get("tamano_m"),
                                          float(datos.get("diametro_mm") or 3.0))
        except ValueError as e:
            return json.dumps({"filas": [], "error": tr(str(e))}, ensure_ascii=False)
        for f in filas:
            f["nombre"] = tr(TIPOS[f["tipo"]]) + (f" ({f['elementos']})" if f["elementos"] else "")
        return json.dumps({"filas": filas, "error": None}, ensure_ascii=False)


def aisladores_zip(entrada: str) -> bytes:
    """Igual entrada que `plano_svg` → zip con los STL de los aisladores y el LÉEME."""
    from . import aisladores
    diseno = _diseno(entrada)
    with usar(diseno.plano.idioma):
        return aisladores.a_zip(diseno)


def plantilla3d_zip(entrada: str) -> bytes:
    """Igual entrada, más `cama_mm` (lado de la cama cuadrada, 200) y `holgura_mm` (0,3) → zip con los STL, el mapa y el LÉEME."""
    from . import impresion3d
    datos = json.loads(entrada)
    diseno = _diseno(entrada)
    cama = float(datos.get("cama_mm") or 200.0)
    with usar(diseno.plano.idioma):
        p = impresion3d.generar(diseno, cama=(cama, cama), holgura=float(datos.get("holgura_mm") or 0.3),
                                radio_mm=float(datos["radio_mm"]) if datos.get("radio_mm") else None)
        return impresion3d.a_zip(p)
