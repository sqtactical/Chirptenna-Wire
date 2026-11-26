"""La web lite dentro de un navegador real: genera cada tipo en cada idioma y da el mismo plano que el escritorio (W5.4).

Necesita Playwright y un navegador: en la CI `playwright install chromium`; en local, `PRUEBA_WEB_CANAL=msedge`
(o chrome). Pyodide se baja de jsdelivr, así que hace falta red. Se salta si no hay Playwright o no hay navegador.
"""

import functools
import http.server
import importlib.util
import os
import threading

import pytest

from wire import planos
from wire.diseno import TIPOS, TIPOS_COAXIAL, disenar
from wire.generadores import TIPOS_HF

playwright_sync = pytest.importorskip("playwright.sync_api")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="module")
def web(tmp_path_factory):
    espec = importlib.util.spec_from_file_location("construir_web", os.path.join(RAIZ, "herramientas", "construir_web.py"))
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    carpeta = str(tmp_path_factory.mktemp("web") / "salida")
    modulo.construir(carpeta)
    manejador = functools.partial(http.server.SimpleHTTPRequestHandler, directory=carpeta)
    manejador.log_message = lambda *a, **k: None
    servidor = http.server.ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{servidor.server_address[1]}"
    servidor.shutdown()


@pytest.fixture(scope="module")
def pagina_nueva(web):
    with playwright_sync.sync_playwright() as p:
        canal = os.environ.get("PRUEBA_WEB_CANAL")
        try:
            navegador = p.chromium.launch(channel=canal) if canal else p.chromium.launch()
        except Exception as error:  # noqa: BLE001
            pytest.skip(f"no hay navegador para Playwright: {str(error)[:120]}")
        yield lambda: navegador.new_page()
        navegador.close()


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_cada_tipo_sale_igual_que_en_escritorio(web, pagina_nueva, idioma):
    pagina = pagina_nueva()
    errores = []
    pagina.on("pageerror", lambda e: errores.append(str(e)))
    pagina.goto(f"{web}/?idioma={idioma}")
    pagina.wait_for_function("document.querySelectorAll('#vista svg').length > 0", timeout=120_000)
    for tipo in TIPOS:
        pagina.click(f'.carta[data-tipo="{tipo}"]')
        pagina.wait_for_function(
            "(t) => document.querySelector('#galeria .carta[aria-pressed=\"true\"]').dataset.tipo === t && "
            "!document.getElementById('generar').disabled && document.querySelectorAll('#vista svg').length > 0", arg=tipo,
            timeout=60_000)
        pagina.wait_for_timeout(500)
        hojas = pagina.evaluate("actual.plano.hojas")
        extra = {"abanico": {"bandas": ["40 m", "20 m", "15 m"]}, "trampas": {"bandas": ["40 m", "20 m"]}}.get(tipo, {})
        esperado = planos.generar(disenar(tipo, 7.1 if tipo in TIPOS_HF else 145.0, 2.0, ajustar=False, idioma=idioma,
                                          cable="RG-58" if tipo in TIPOS_COAXIAL else None, **extra))
        assert hojas == [planos.a_svg(h) for h in esperado.hojas], f"{tipo} ({idioma}) no coincide con el escritorio"
    assert not errores, errores
    pagina.close()


def test_el_selector_de_idioma_traduce_la_interfaz(web, pagina_nueva):
    pagina = pagina_nueva()
    pagina.goto(f"{web}/?idioma=es")
    pagina.wait_for_function("document.querySelectorAll('#vista svg').length > 0", timeout=120_000)
    pagina.select_option("#idioma", "de")
    pagina.wait_for_function("document.querySelector('h2').textContent === 'Entwurf'", timeout=30_000)
    pagina.wait_for_function("document.getElementById('vista').innerText.includes('ZUSCHNITTLISTE')", timeout=30_000)
    assert "ZUSCHNITTLISTE" in pagina.inner_text("#vista")
    pagina.close()
