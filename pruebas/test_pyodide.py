"""El mismo plano en Pyodide (web lite) que en el escritorio: misma descripción vectorial y PDF válido.

Se salta si no hay Node ni Pyodide instalado con npm. Para activarla:
    cd %LOCALAPPDATA%\\chirptenna-wire\\pyodide-prueba; npm install pyodide
o pon la carpeta en la variable CHIRPTENNA_PYODIDE.
"""

import json
import os
import shutil
import subprocess

import pytest

from wire import planos
from wire.diseno import Diseno

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODULOS = os.environ.get("CHIRPTENNA_PYODIDE",
                         os.path.join(os.environ.get("LOCALAPPDATA", ""), "chirptenna-wire", "pyodide-prueba"))
HAY_PYODIDE = shutil.which("node") and os.path.exists(os.path.join(MODULOS, "node_modules", "pyodide", "pyodide.mjs"))


@pytest.mark.skipif(not HAY_PYODIDE, reason="no hay Node con Pyodide (npm install pyodide)")
def test_plano_identico_en_pyodide(tmp_path):
    diseno = os.path.join(RAIZ, "docs", "ejemplos", "jpole_435.json")
    salida = str(tmp_path / "pyodide")
    r = subprocess.run(["node", os.path.join(RAIZ, "herramientas", "prueba_pyodide.mjs"), MODULOS, RAIZ, diseno,
                        salida], capture_output=True, text=True, encoding="utf-8", timeout=600)
    assert r.returncode == 0, r.stderr
    assert "PyNEC False" in r.stdout
    with open(diseno, encoding="utf-8") as f:
        local = planos.descripcion(planos.generar(Diseno.desde_json(f.read()), fecha="25-11-2026"))
    with open(salida + ".json", encoding="utf-8") as f:
        remoto = json.load(f)
    assert remoto == json.loads(json.dumps(local))
    with open(salida + ".pdf", "rb") as f:
        assert f.read(5) == b"%PDF-"
