"""Construye la web lite: copia `web/` y empaqueta el núcleo de `wire/` en `py/wire.zip`.

    python herramientas/construir_web.py [carpeta_de_salida]      (por defecto salidas/web)

El núcleo es lo que corre en Pyodide: se deja fuera `motor.py` y `ajuste.py` (PyNEC) y se **falla** si algún archivo
empaquetado importa algo que no carga en el navegador (PyNEC, numpy, scipy, matplotlib) o depende de lo que se ha dejado fuera.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUERA = {"motor.py", "ajuste.py"}              # solo escritorio
# Solo importaciones en la columna 0 (las de dentro de una función, como la de `diseno.disenar`, son perezosas y no se
# ejecutan en el navegador).
PROHIBIDO = re.compile(r"^(?:import|from)\s+(PyNEC|numpy|scipy|matplotlib|nicegui)\b", re.M)
DEPENDE_DE_FUERA = re.compile(r"^(?:from\s+\.+\s*import\s+(?:motor|ajuste)\b|from\s+\.+(?:motor|ajuste)\s+import|"
                              r"import\s+wire\.(?:motor|ajuste)\b)", re.M)


def nucleo() -> list[tuple[str, str]]:
    """(ruta en disco, ruta en el zip) de cada archivo del núcleo."""
    lista = []
    for carpeta, subcarpetas, archivos in os.walk(os.path.join(RAIZ, "wire")):
        subcarpetas[:] = [d for d in subcarpetas if d != "__pycache__"]
        for a in archivos:
            if a in FUERA or a.endswith(".pyc"):
                continue
            ruta = os.path.join(carpeta, a)
            lista.append((ruta, os.path.relpath(ruta, RAIZ).replace("\\", "/")))
    return sorted(lista, key=lambda p: p[1])


def comprobar(lista: list[tuple[str, str]]) -> None:
    for ruta, nombre in lista:
        if not nombre.endswith(".py"):
            continue
        with open(ruta, encoding="utf-8") as f:
            texto = f.read()
        mal = PROHIBIDO.search(texto)
        if mal:
            sys.exit(f"{nombre} importa {mal.group(1)}, que no carga en Pyodide: no puede ir en el núcleo de la web")
        if DEPENDE_DE_FUERA.search(texto):
            sys.exit(f"{nombre} depende de motor.py o ajuste.py, que no van en la web")


def construir(salida: str) -> None:
    web = os.path.join(RAIZ, "web")
    if not os.path.isdir(web):
        sys.exit("no existe web/")
    if os.path.isdir(salida):
        shutil.rmtree(salida)
    shutil.copytree(web, salida)
    img = os.path.join(salida, "img")
    os.makedirs(img, exist_ok=True)
    for n in ("logo-wire.svg", "logo-wire-oscuro.svg", "grillo-wire.svg", "favicon-32.png", "icono-192.png"):
        shutil.copy(os.path.join(RAIZ, "img", n), img)
    idiomas = os.path.join(salida, "idiomas")           # los mismos catálogos que usa Python, para la interfaz
    os.makedirs(idiomas, exist_ok=True)
    for a in os.listdir(os.path.join(RAIZ, "wire", "idiomas")):
        if a.endswith(".json"):
            shutil.copy(os.path.join(RAIZ, "wire", "idiomas", a), idiomas)
    lista = nucleo()
    comprobar(lista)
    os.makedirs(os.path.join(salida, "py"), exist_ok=True)
    with zipfile.ZipFile(os.path.join(salida, "py", "wire.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for ruta, nombre in lista:
            z.write(ruta, nombre)
    print(f"{salida}: {len(lista)} archivos del núcleo en py/wire.zip")


if __name__ == "__main__":
    construir(sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "salidas", "web"))
