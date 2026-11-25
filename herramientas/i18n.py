"""Catálogos de idiomas: extrae los textos de `tr()`/`N_()` del código y de la web y comprueba que no falte ninguna.

    python herramientas/i18n.py extraer             lista los textos del código y de la web
    python herramientas/i18n.py actualizar          añade a cada catálogo las claves nuevas (vacías) y quita las que sobran
    python herramientas/i18n.py faltan [código]     lista las traducciones que faltan (código 1 si falta alguna)

El castellano es la clave. Un idioma nuevo: crear `wire/idiomas/<código>.json` con `_nombre` y `textos` y añadir el
código a `wire.i18n.IDIOMAS`. En la web, los textos van con `T('texto {0}', x)` y `data-t` (web/app.js, web/index.html).
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDIOMAS = ("en", "fr", "de")
CARPETA = os.path.join(RAIZ, "wire", "idiomas")


def _claves_python() -> set[str]:
    claves: set[str] = set()
    for raiz in ("wire", "gui"):
        for carpeta, subcarpetas, archivos in os.walk(os.path.join(RAIZ, raiz)):
            subcarpetas[:] = [d for d in subcarpetas if d != "__pycache__"]
            for a in archivos:
                if not a.endswith(".py"):
                    continue
                with open(os.path.join(carpeta, a), encoding="utf-8") as f:
                    arbol = ast.parse(f.read())
                for n in ast.walk(arbol):
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("tr", "N_") and n.args \
                            and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                        claves.add(n.args[0].value)
    return claves


def _claves_web() -> set[str]:
    claves: set[str] = set()
    ruta = os.path.join(RAIZ, "web", "app.js")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for m in re.finditer(r"\bT\(\s*(?:'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\")", f.read()):
                claves.add((m.group(1) if m.group(1) is not None else m.group(2)).replace("\\'", "'").replace("\\n", "\n"))
    ruta = os.path.join(RAIZ, "web", "index.html")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            html = f.read()
        for m in re.finditer(r"data-t(?![-\w])(?:=\"([^\"]*)\")?[^>]*>([^<]*)<", html):
            clave = m.group(1) or m.group(2).strip()
            if clave:
                claves.add(clave)
        for m in re.finditer(r"data-t-(?:placeholder|title)=\"([^\"]+)\"", html):
            claves.add(m.group(1))
    ruta = os.path.join(RAIZ, "web", "motor.js")
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            for m in re.finditer(r"progreso\('((?:[^'\\]|\\.)*)'", f.read()):
                claves.add(m.group(1))
    return claves


def claves() -> list[str]:
    return sorted(_claves_python() | _claves_web())


def cargar(codigo: str) -> dict:
    ruta = os.path.join(CARPETA, f"{codigo}.json")
    if not os.path.exists(ruta):
        return {"_nombre": codigo, "textos": {}}
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def guardar(codigo: str, datos: dict) -> None:
    with open(os.path.join(CARPETA, f"{codigo}.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write("\n")


def faltan(codigo: str) -> list[str]:
    textos = cargar(codigo)["textos"]
    return [c for c in claves() if not textos.get(c)]


def sobran(codigo: str) -> list[str]:
    todas = set(claves())
    return [c for c in cargar(codigo)["textos"] if c not in todas]


def actualizar() -> None:
    todas = claves()
    for codigo in IDIOMAS:
        datos = cargar(codigo)
        textos = datos["textos"]
        datos["textos"] = {c: textos.get(c, "") for c in todas}
        guardar(codigo, datos)
        print(f"{codigo}: {len(todas)} claves, {len(faltan(codigo))} sin traducir")


def main(argv: list[str]) -> int:
    orden = argv[0] if argv else "faltan"
    if orden == "extraer":
        print("\n".join(claves()))
    elif orden == "actualizar":
        actualizar()
    elif orden == "faltan":
        malo = False
        for codigo in (argv[1:] or IDIOMAS):
            f = faltan(codigo)
            malo |= bool(f)
            print(f"{codigo}: faltan {len(f)}" + ("".join("\n  " + c.replace("\n", "\\n") for c in f[:200]) if f else ""))
        return 1 if malo else 0
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
