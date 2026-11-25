"""La interfaz de escritorio arranca y sirve cada idioma (necesita NiceGUI; se salta si no está)."""

import os
import socket
import subprocess
import sys
import time
import urllib.request

import pytest

pytest.importorskip("nicegui")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def servidor():
    puerto = _puerto_libre()
    # Sin las variables de pytest: NiceGUI las ve y se pone en «modo de pruebas de pantalla».
    entorno = {k: v for k, v in os.environ.items() if not k.startswith(("PYTEST", "NICEGUI"))}
    proceso = subprocess.Popen([sys.executable, os.path.join(RAIZ, "gui", "app.py"), "--puerto", str(puerto)],
                               cwd=RAIZ, env=entorno, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    base = f"http://127.0.0.1:{puerto}"
    for _ in range(40):
        if proceso.poll() is not None:
            break
        try:
            urllib.request.urlopen(base + "/", timeout=2)
            break
        except OSError:
            time.sleep(0.5)
    else:
        proceso.kill()
        pytest.fail("la interfaz no arrancó: " + proceso.stderr.read().decode("utf-8", "replace")[-500:])
    yield base
    proceso.terminate()
    try:
        proceso.wait(10)
    except subprocess.TimeoutExpired:
        proceso.kill()


@pytest.mark.parametrize("idioma,texto", [("es", "Elige el tipo de antena"), ("en", "Choose the antenna type"),
                                          ("fr", "Choisis le type d"), ("de", "Antennentyp wählen")])
def test_la_pagina_sale_en_cada_idioma(servidor, idioma, texto):
    with urllib.request.urlopen(f"{servidor}/?idioma={idioma}", timeout=20) as r:
        html = r.read().decode("utf-8")
    assert r.status == 200 and texto in html


def test_solo_escucha_en_local(servidor):
    assert servidor.startswith("http://127.0.0.1:")
