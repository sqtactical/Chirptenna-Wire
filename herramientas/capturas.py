"""Capturas del README (docs/capturas/): la interfaz de escritorio y la web lite, con Playwright y Edge o Chromium.

    python herramientas/capturas.py [--canal msedge]

Arranca la interfaz en un puerto libre y sirve la web construida; hace falta red (Pyodide se baja de jsdelivr).
"""

from __future__ import annotations

import argparse
import functools
import http.server
import importlib.util
import os
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SALIDA = os.path.join(RAIZ, "docs", "capturas")


def puerto_libre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def main() -> None:
    from playwright.sync_api import sync_playwright

    ap = argparse.ArgumentParser()
    ap.add_argument("--canal", default=None, help="msedge, chrome… (por defecto, el Chromium de Playwright)")
    args = ap.parse_args()
    os.makedirs(SALIDA, exist_ok=True)

    espec = importlib.util.spec_from_file_location("construir_web", os.path.join(RAIZ, "herramientas", "construir_web.py"))
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    carpeta = os.path.join(tempfile.mkdtemp(), "web")
    modulo.construir(carpeta)
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta)
    manejador.log_message = lambda *a, **k: None
    web = http.server.ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=web.serve_forever, daemon=True).start()

    puerto = puerto_libre()
    entorno = {k: v for k, v in os.environ.items() if not k.startswith(("PYTEST", "NICEGUI"))}
    gui = subprocess.Popen([sys.executable, os.path.join(RAIZ, "gui", "app.py"), "--puerto", str(puerto)], cwd=RAIZ, env=entorno,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(40):
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{puerto}/", timeout=2)
                break
            except OSError:
                time.sleep(0.5)
        with sync_playwright() as p:
            navegador = p.chromium.launch(channel=args.canal) if args.canal else p.chromium.launch()
            ctx = navegador.new_context(viewport={"width": 1180, "height": 760}, color_scheme="light")
            pag = ctx.new_page()
            pag.goto(f"http://127.0.0.1:{puerto}/?idioma=es")
            pag.wait_for_timeout(1500)
            pag.screenshot(path=os.path.join(SALIDA, "escritorio_elegir.png"))
            pag.get_by_text("J-pole de Koch").first.click()
            pag.wait_for_timeout(1200)
            pag.get_by_text("Cotas de partida (sin motor)").click()
            pag.get_by_role("tab", name="PLANO").wait_for(timeout=30000)
            pag.wait_for_selector(".hoja-svg svg", timeout=60000)
            pag.wait_for_timeout(800)
            pag.screenshot(path=os.path.join(SALIDA, "escritorio_plano.png"))
            pag2 = ctx.new_page()
            pag2.goto(f"http://127.0.0.1:{web.server_address[1]}/?idioma=es")
            pag2.wait_for_function("document.querySelectorAll('#vista svg').length > 0", timeout=120000)
            pag2.wait_for_timeout(800)
            pag2.screenshot(path=os.path.join(SALIDA, "web.png"))
            navegador.close()
    finally:
        gui.terminate()
        web.shutdown()
    print("capturas en", SALIDA)


if __name__ == "__main__":
    main()
