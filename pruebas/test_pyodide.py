"""El mismo plano en Pyodide (web lite) que en el escritorio: misma descripción vectorial y mismo PDF en lo que se mide.

Se salta si no hay Node con Pyodide 0.29.3 instalado con npm. Para activarla:
    cd %LOCALAPPDATA%\\chirptenna-wire\\pyodide-0293; npm install pyodide@0.29.3
o pon la carpeta (la que contiene node_modules) en la variable CHIRPTENNA_PYODIDE.
"""

import json
import os
import re
import shutil
import subprocess

import pytest

from wire import planos
from wire.diseno import Diseno
from wire.planos.comun import REGLA_MM

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS = os.environ.get("CHIRPTENNA_PYODIDE",
                         os.path.join(os.environ.get("LOCALAPPDATA", ""), "chirptenna-wire", "pyodide-0293"))
HAY_PYODIDE = shutil.which("node") and os.path.exists(os.path.join(MODULOS, "node_modules", "pyodide", "pyodide.mjs"))
PT_POR_MM = 72 / 25.4


def _rectangulos(pdf: bytes) -> list[tuple[float, ...]]:
    texto = pdf.decode("latin-1")
    return [tuple(float(v) for v in m) for m in re.findall(r"([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+) re", texto)]


def _regla(pdf: bytes) -> tuple[float, ...]:
    barra = [r for r in _rectangulos(pdf) if abs(r[2] - REGLA_MM * PT_POR_MM) < 0.02]
    assert len(barra) == 1
    return barra[0]


@pytest.mark.skipif(not HAY_PYODIDE, reason="no hay Node con Pyodide (npm install pyodide@0.29.3)")
@pytest.mark.parametrize("nombre", ["dipolo_145", "jpole_435"])
def test_plano_identico_en_pyodide(tmp_path, nombre):
    diseno = os.path.join(RAIZ, "docs", "ejemplos", f"{nombre}.json")
    salida = str(tmp_path / "pyodide")
    r = subprocess.run(["node", os.path.join(RAIZ, "herramientas", "prueba_pyodide.mjs"), MODULOS, RAIZ, diseno,
                        salida, "sin_comprimir"], capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr
    assert "Pyodide 0.29.3" in r.stdout and "PyNEC False" in r.stdout
    with open(diseno, encoding="utf-8") as f:
        plano = planos.generar(Diseno.desde_json(f.read()), fecha="25-11-2026")
    with open(salida + ".json", encoding="utf-8") as f:
        assert json.load(f) == json.loads(json.dumps(planos.descripcion(plano)))
    with open(salida + ".pdf", "rb") as f:
        remoto = f.read()
    local = planos.a_pdf(plano, comprimir=False)
    assert remoto.startswith(b"%PDF-")
    # Mismo tamaño de página, misma regla en las mismas coordenadas y los mismos rectángulos (detalles 1:1).
    assert re.findall(rb"/MediaBox \[[^\]]*\]", remoto) == re.findall(rb"/MediaBox \[[^\]]*\]", local)
    assert _regla(remoto) == _regla(local)
    assert _rectangulos(remoto) == _rectangulos(local)
