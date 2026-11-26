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
    pagina.wait_for_function("document.querySelectorAll('#galeria .carta').length > 0", timeout=120_000)
    for tipo in TIPOS:
        assert pagina.is_visible("#elegir") and not pagina.is_visible("#diseno")      # primero se elige la antena
        pagina.click(f'.carta[data-tipo="{tipo}"]')
        pagina.wait_for_function(
            "(t) => !document.getElementById('diseno').classList.contains('oculto') && actual && "
            "actual.plano.diseno.tipo === t && !document.getElementById('generar').disabled", arg=tipo,
            timeout=60_000)
        pagina.wait_for_timeout(500)
        hojas = pagina.evaluate("actual.plano.hojas")
        extra = {"abanico": {"bandas": ["40 m", "20 m", "15 m"]}, "trampas": {"bandas": ["40 m", "20 m"]}}.get(tipo, {})
        esperado = planos.generar(disenar(tipo, 7.1 if tipo in TIPOS_HF else 145.0, 2.0, ajustar=False, idioma=idioma,
                                          cable="RG-58" if tipo in TIPOS_COAXIAL else None, **extra))
        assert hojas == [planos.a_svg(h) for h in esperado.hojas], f"{tipo} ({idioma}) no coincide con el escritorio"
        pagina.click("#atras")                                                          # y se vuelve a la galería
    assert not errores, errores
    pagina.close()


def test_yagi_al_cambiar_elementos_eje_y_frecuencia(web, pagina_nueva):
    pagina = pagina_nueva()
    pagina.goto(f"{web}/?idioma=es")
    pagina.wait_for_function("document.querySelectorAll('#galeria .carta').length > 0", timeout=120_000)
    pagina.click('.carta[data-tipo="yagi"]')
    pagina.wait_for_function("actual && actual.plano.diseno.tipo === 'yagi'", timeout=60_000)
    assert not pagina.is_visible("#eje-mm")                                  # eje no metálico: sin diámetro
    pagina.fill("#elementos", "7")                                           # el plano se rehace solo
    pagina.wait_for_function("actual && actual.plano.diseno.geometria.n_elementos === 7", timeout=60_000)
    pagina.select_option("#eje", "unido")
    assert pagina.is_visible("#eje-mm")
    pagina.wait_for_function("actual && actual.plano.diseno.geometria.boom === 'unido'", timeout=60_000)
    pagina.fill("#elementos", "40")                                          # se limita a 15
    pagina.dispatch_event("#elementos", "change")
    assert pagina.input_value("#elementos") == "15"
    pagina.fill("#eje-mm", "45")
    pagina.fill("#f", "433")                                                 # 45 mm a 433 MHz: demasiado grueso → error visible
    pagina.wait_for_function("!document.getElementById('error').classList.contains('oculto')", timeout=60_000)
    assert "demasiado grueso" in pagina.inner_text("#error")
    pagina.fill("#eje-mm", "10")
    pagina.wait_for_function("actual && actual.plano.diseno.f_MHz === 433 && actual.plano.diseno.geometria.boom_mm === 10", timeout=60_000)
    assert not pagina.is_visible("#error")
    pagina.close()


def test_el_selector_de_idioma_traduce_la_interfaz(web, pagina_nueva):
    pagina = pagina_nueva()
    pagina.goto(f"{web}/?idioma=es")
    pagina.wait_for_function("document.querySelectorAll('#galeria .carta').length > 0", timeout=120_000)
    pagina.click('.carta[data-tipo="dipolo"]')
    pagina.wait_for_function("document.querySelectorAll('#vista svg').length > 0", timeout=60_000)
    pagina.select_option("#idioma", "de")
    pagina.wait_for_function("document.querySelector('#atras').textContent.includes('Antenne')", timeout=30_000)
    pagina.wait_for_function("document.getElementById('vista').innerText.includes('ZUSCHNITTLISTE')", timeout=30_000)
    assert "ZUSCHNITTLISTE" in pagina.inner_text("#vista")
    pagina.close()
