"""Interfaz de escritorio de Chirptenna Wire (NiceGUI). Escucha solo en 127.0.0.1.

    python gui/app.py [--puerto 8090] [--idioma es|en|fr|de]

Pestañas: Elegir (galería de tipos) · Diseño (parámetros y ajuste con PyNEC) · Simulación (resultados) · Plano (vista y
descargas) · Medir (Chirptenna VNA y comparación con un .s1p). El trabajo pesado va en un proceso aparte (`wire.escritorio`).
Los textos van con `tr()`: el castellano es el texto fuente (`herramientas/i18n.py`).
"""

from __future__ import annotations

import argparse
import os
import sys
from urllib.parse import quote

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from nicegui import app, run, ui  # noqa: E402

from wire import escritorio, i18n, medidas, motor, nec, planos  # noqa: E402
from wire.cables import CABLES  # noqa: E402
from wire import ganancias  # noqa: E402
from wire.diseno import (BANDAS, CATEGORIAS, CONECTORES, ESTADO_TIPO, RESUMEN, TIPOS, TIPOS_COAXIAL, ConfigPlano, Diseno,  # noqa: E402
                         banda_de)
from wire.generadores import BOOMS, RELACIONES, SUELOS, TIPOS_HF  # noqa: E402
from wire.impresion3d import TIPOS_3D  # noqa: E402
from wire.planos.comun import fmt  # noqa: E402
from wire.graficas import puntos_diagrama, svg_diagrama, svg_roe  # noqa: E402
from wire.i18n import tr  # noqa: E402
from wire.miniaturas import MINIATURAS  # noqa: E402

VNA_URL = os.environ.get("CHIRPTENNA_VNA_URL", "http://localhost:8765/")
IDIOMAS = {"es": "Castellano", "en": "English", "fr": "Français", "de": "Deutsch"}
IDIOMA_INICIAL = os.environ.get("CHIRPTENNA_IDIOMA", "es")

CSS = """
body.body--light{background:#f6f7f5;color:#1f2a24}
body.body--dark{background:#14181a;color:#e9eee9}
.q-tab{color:inherit}
.q-tab-panels,.q-panel,.q-tab-panel{background:transparent}
.carta-tipo{cursor:pointer;width:230px;transition:box-shadow .15s}
.carta-tipo:hover{box-shadow:0 0 0 2px #c8892b}
.carta-tipo.activa{box-shadow:0 0 0 3px #c8892b}
.carta-tipo svg{max-width:100%;height:auto}
.hoja-svg{background:#fff;border:1px solid #ccc;border-radius:6px;max-width:640px;width:100%}
.hoja-svg svg{width:100%;height:auto;display:block}
.aviso-caja{background:#fff4dc;color:#7a4e00;border-radius:8px;padding:8px 12px}
body.body--dark .aviso-caja{background:#33290f;color:#f1c97a}
"""


def mensaje(error: Exception) -> str:
    """Última línea de un error de Python, sin el nombre de la excepción (lo que sirve al usuario)."""
    lineas = [x for x in str(error).strip().splitlines() if x.strip()]
    return (lineas[-1] if lineas else "").split("Error: ", 1)[-1]


def escena_diagrama(theta, phi, g, modelo) -> None:
    """Diagrama de radiación en 3D (nube de puntos coloreada por ganancia) con los hilos de la antena dentro, centrados."""
    puntos, colores, gmax = puntos_diagrama(theta, phi, g)
    ui.label(tr("Diagrama 3D (arrastra para girar; máx {0:.1f} dBi, color rojo = máximo)", gmax)).classes("text-xs opacity-70")
    hilos = [(h.inicio, h.fin) for h in modelo.hilos]
    todos = [p for par in hilos for p in par]
    centro = [sum(p[i] for p in todos) / len(todos) for i in range(3)]
    semi = max((max(abs(p[i] - centro[i]) for p in todos) for i in range(3)), default=1.0) or 1.0
    k = 0.45 / semi                                          # la antena ocupa ~la mitad del radio del diagrama
    with ui.scene(width=640, height=460, background_color="#f4f6f8").classes("max-w-full") as escena:
        escena.point_cloud(puntos, colores, point_size=0.06)
        for a, b in hilos:
            escena.line([(a[i] - centro[i]) * k for i in range(3)], [(b[i] - centro[i]) * k for i in range(3)]).material("#111111")
        escena.axes_helper(length=1.15)
        escena.move_camera(x=1.0, y=-1.3, z=0.8, look_at_x=0, look_at_y=0, look_at_z=0)


def estado_texto(estado: str) -> str:
    return {"Sin validar": tr("Sin validar"), "Simulado": tr("Simulado"), "Medido": tr("Medido")}.get(estado, estado)


@ui.page("/")
def pagina(idioma: str | None = None) -> None:
    i18n.fijar(idioma if idioma in IDIOMAS else app.storage.general.get("idioma", IDIOMA_INICIAL))
    app.storage.general["idioma"] = i18n.idioma()
    ui.add_css(CSS)
    ui.colors(primary="#c8892b")
    oscuro = ui.dark_mode()
    s = {"tipo": "dipolo", "f": 145.0, "diametro": 2.0, "cable": "RG-58", "vf": None, "conector": "SO-239", "papel": "A4", "unidades": "mm",
         "diseno": None, "plano": None, "hoja": 0, "medida": None,
         # lo propio de cada tipo
         "elementos": 3, "secciones": 3, "eje": "ninguno", "eje_mm": None, "relacion": 49, "altura": 10.0, "suelo": "normal",
         "bandas": "40 m, 20 m, 15 m", "potencia": 100.0, "largo_max": None, "f_alta": 433.0, "cama": 200.0, "radio": None}

    # ------------------------------------------------------------------ cabecera
    with ui.header().classes("items-center gap-4 bg-transparent text-inherit border-b").style("border-color:#8884"):
        ui.image("/img/logo-wire.svg").classes("h-10 w-auto dark:hidden")
        ui.image("/img/logo-wire-oscuro.svg").classes("h-10 w-auto hidden dark:block")
        ui.space()
        ui.select(IDIOMAS, value=i18n.idioma(), on_change=lambda e: ui.navigate.to(f"/?idioma={e.value}")) \
            .props("dense outlined").classes("w-36").tooltip(tr("Idioma"))
        ui.button(icon="contrast", on_click=oscuro.toggle).props("flat round").tooltip(tr("Tema claro/oscuro"))

    with ui.tabs().classes("w-full") as pestanas:
        t_elegir = ui.tab(tr("Elegir antena"))
        t_diseno = ui.tab(tr("Diseño"))
        t_sim = ui.tab(tr("Simulación"))
        t_plano = ui.tab(tr("Plano"))
        t_medir = ui.tab(tr("Medir"))
    paneles = ui.tab_panels(pestanas, value=t_elegir).classes("w-full")

    def refrescar() -> None:
        resumen_diseno.refresh()
        simulacion.refresh()
        vista_plano.refresh()
        medir.refresh()

    # ------------------------------------------------------------------ Elegir
    with paneles:
        with ui.tab_panel(t_elegir):
            ui.label(tr("Elige el tipo de antena")).classes("text-lg font-bold")
            ui.label(tr("Planos de alambre, varilla y coaxial con simulación NEC2. Estado honesto: nada está «Medido» hasta que se mide.")) \
                .classes("opacity-70")
            cartas: dict[str, ui.card] = {}

            def valores_por_tipo(clave: str) -> None:
                """Al pasar de VHF/UHF a HF (o al revés) la frecuencia y los valores de antes no sirven."""
                hf = clave in TIPOS_HF
                if hf and not 1.8 <= s["f"] <= 30:
                    s["f"] = 7.1
                elif not hf and s["f"] < 30:
                    s["f"] = 145.0
                s["altura"] = 12.0 if clave == "vinv_hf" else 10.0
                if clave == "trampas":
                    s["bandas"] = "40 m, 20 m"
                elif clave == "abanico":
                    s["bandas"] = "40 m, 20 m, 15 m"
                if clave == "colineal_bibanda" and s["secciones"] not in (2, 4):
                    s["secciones"] = 4

            def elegir(clave: str) -> None:
                s["tipo"], s["diseno"], s["plano"] = clave, None, None
                for k, c in cartas.items():
                    c.classes(add="activa" if k == clave else "", remove="" if k == clave else "activa")
                valores_por_tipo(clave)
                campos_visibles()
                refrescar()
                pestanas.set_value(t_diseno)

            en_categoria = {t for _c, _n, ts in CATEGORIAS for t in ts}
            grupos = [(tr(n), list(ts)) for _c, n, ts in CATEGORIAS] + [("", [t for t in TIPOS if t not in en_categoria])]
            for titulo, claves in grupos:
                if not claves:
                    continue
                if titulo:
                    ui.label(titulo.upper()).classes("text-sm font-bold opacity-70 mt-4")
                with ui.row().classes("gap-4 mt-2"):
                    for clave in claves:
                        with ui.card().classes("carta-tipo items-center") as carta:
                            ui.html(MINIATURAS[clave], sanitize=False)
                            ui.label(tr(TIPOS[clave])).classes("font-bold text-center")
                            g = ganancias.rango_tipo(clave, fmt)
                            if g:
                                ui.label(g).classes("text-sm font-bold text-primary")
                            ui.label(tr(ESTADO_TIPO[clave])).classes("text-xs opacity-70 text-center")
                            ui.label(tr(RESUMEN[clave])).classes("text-xs text-center")
                        carta.on("click", lambda _e, k=clave: elegir(k))
                        cartas[clave] = carta
            cartas[s["tipo"]].classes(add="activa")

        # -------------------------------------------------------------- Diseño
        with ui.tab_panel(t_diseno):
            with ui.row().classes("gap-8 items-start"):
                with ui.column().classes("w-80"):
                    banda_opts = {None: tr("— otra —")} | {i: f"{tr(n)} ({a:g}–{b:g} MHz)" for i, (n, a, b) in enumerate(BANDAS)}

                    def poner_banda(e) -> None:
                        if e.value is not None:
                            n, a, b = BANDAS[e.value]
                            f_campo.set_value(round((a + b) / 2, 3))

                    ui.select(banda_opts, value=None, label=tr("Banda"), on_change=poner_banda).classes("w-full")
                    f_campo = ui.number(tr("Frecuencia (MHz)"), value=s["f"], min=30, max=3000, step=0.001, format="%.3f") \
                        .classes("w-full").bind_value(s, "f")
                    diam = ui.number(tr("Diámetro del alambre (mm)"), value=s["diametro"], min=0.5, max=20, step=0.1) \
                        .classes("w-full").bind_value(s, "diametro")
                    with ui.column().classes("w-full") as campos_coaxial:
                        ui.select([c.nombre for c in CABLES.values()], value=s["cable"], label=tr("Cable coaxial")) \
                            .classes("w-full").bind_value(s, "cable")
                        ui.number(tr("VF medido (opcional)"), min=0.5, max=1, step=0.01, placeholder=tr("el de catálogo")) \
                            .classes("w-full").bind_value(s, "vf")
                    with ui.column().classes("w-full") as campos_gp:
                        ui.select(list(CONECTORES), value=s["conector"], label=tr("Conector")).classes("w-full").bind_value(s, "conector")
                    with ui.column().classes("w-full") as campos_yagi:
                        ui.number(tr("Elementos"), min=3, max=15, step=1, precision=0).classes("w-full").bind_value(s, "elementos")
                        ui.select({"ninguno": tr("No metálico"), "aislado": tr("Metálico, elementos aislados"),
                                   "unido": tr("Metálico, elementos unidos")}, label=tr("Eje (boom)")).classes("w-full").bind_value(s, "eje")
                        ui.number(tr("Ø del eje metálico (mm)"), min=4, max=60, step=1, placeholder=tr("1 % de λ")) \
                            .classes("w-full").bind_value(s, "eje_mm").bind_visibility_from(s, "eje", backward=lambda v: v != "ninguno")
                    with ui.column().classes("w-full") as campos_colineal:
                        ui.number(tr("Secciones"), min=2, max=6, step=1, precision=0).classes("w-full").bind_value(s, "secciones")
                        with ui.column().classes("w-full") as campos_bibanda:
                            ui.number(tr("Frecuencia de la banda alta (MHz)"), min=100, max=3000, step=0.001).classes("w-full") \
                                .bind_value(s, "f_alta")
                            ui.label(tr("Banda baja = la frecuencia de arriba. Secciones: 2 o 4.")).classes("text-xs opacity-70")
                    with ui.column().classes("w-full") as campos_hf:
                        ui.number(tr("Altura del hilo (m)"), min=1.5, max=60, step=0.5).classes("w-full").bind_value(s, "altura")
                        ui.select({"pobre": tr("pobre"), "normal": tr("normal"), "bueno": tr("bueno"), "mar": tr("de mar")},
                                  label=tr("Suelo")).classes("w-full").bind_value(s, "suelo")
                        with ui.column().classes("w-full") as campos_bandas:
                            ui.input(tr("Bandas (separadas por comas)")).classes("w-full").bind_value(s, "bandas")
                    with ui.column().classes("w-full") as campos_efhw:
                        ui.select({r: f"{r}:1" for r in RELACIONES}, label=tr("Transformador")).classes("w-full").bind_value(s, "relacion")
                        ui.number(tr("Potencia (W)"), min=5, max=1500, step=5).classes("w-full").bind_value(s, "potencia")
                        ui.number(tr("Largo máximo del hilo (m, opcional)"), min=3, max=100, step=0.5, placeholder=tr("sin límite")) \
                            .classes("w-full").bind_value(s, "largo_max")

                    def campos_visibles() -> None:
                        t = s["tipo"]
                        campos_coaxial.set_visibility(t in TIPOS_COAXIAL)
                        campos_gp.set_visibility(t == "gp")
                        campos_yagi.set_visibility(t == "yagi")
                        campos_colineal.set_visibility(t in ("colineal", "colineal_bibanda"))
                        campos_bibanda.set_visibility(t == "colineal_bibanda")
                        campos_hf.set_visibility(t in TIPOS_HF)
                        campos_bandas.set_visibility(t in ("abanico", "trampas"))
                        campos_efhw.set_visibility(t == "efhw")

                    campos_visibles()
                    ui.select(list(ConfigPlano.VALORES["papel"]), value=s["papel"], label=tr("Papel")).classes("w-full") \
                        .bind_value(s, "papel")
                    ui.select({"mm": "mm", "pulgadas": tr("pulgadas")}, value=s["unidades"], label=tr("Unidades")) \
                        .classes("w-full").bind_value(s, "unidades")
                    estado_calculo = ui.label("").classes("text-sm opacity-70")
                    boton_ajuste = ui.button(tr("Simular y ajustar (PyNEC)"), on_click=lambda: calcular(True)) \
                        .classes("w-full")
                    ui.button(tr("Cotas de partida (sin motor)"), on_click=lambda: calcular(False)).props("outline") \
                        .classes("w-full")
                    if not motor.disponible():
                        boton_ajuste.disable()
                        ui.label(tr("PyNEC no está instalado: solo hay cotas de partida («Sin validar»).")).classes("text-xs")

                    async def calcular(ajustar: bool) -> None:
                        estado_calculo.set_text(tr("Calculando… (el ajuste puede tardar un minuto)"))
                        try:
                            es_coax = s["tipo"] in TIPOS_COAXIAL
                            texto = await run.cpu_bound(
                                escritorio.calcular, s["tipo"], float(s["f"]), float(s["diametro"]), ajustar,
                                s["cable"] if es_coax else None, s["vf"] if es_coax and s["vf"] else None, s["papel"],
                                s["unidades"], i18n.idioma(), s["conector"] if s["tipo"] == "gp" else None, **especificos())
                            s["diseno"] = Diseno.desde_json(texto)
                            nuevo_plano()
                            estado_calculo.set_text("")
                            refrescar()
                            pestanas.set_value(t_sim if ajustar else t_plano)
                        except Exception as error:  # noqa: BLE001 - se muestra al usuario
                            estado_calculo.set_text(tr("Error: {0}", mensaje(error)))

                    def especificos() -> dict:
                        """Lo propio del tipo elegido, como argumentos de `disenar` (nada de lo que no le vale)."""
                        t = s["tipo"]
                        e: dict = {}
                        if t == "yagi":
                            e.update(elementos=int(s["elementos"] or 3), eje=s["eje"])
                            if s["eje"] != "ninguno" and s["eje_mm"]:
                                e["eje_mm"] = float(s["eje_mm"])
                        elif t in ("colineal", "colineal_bibanda"):
                            e["elementos"] = int(s["secciones"] or 3)
                            if t == "colineal_bibanda":
                                e["f_alta_MHz"] = float(s["f_alta"])
                        if t in TIPOS_HF:
                            e.update(altura_m=float(s["altura"]), suelo=s["suelo"])
                        if t in ("abanico", "trampas"):
                            e["bandas"] = [b.strip() for b in str(s["bandas"]).split(",") if b.strip()]
                        if t == "efhw":
                            e.update(relacion=int(s["relacion"]), potencia_w=float(s["potencia"]))
                            if s["largo_max"]:
                                e["largo_max_m"] = float(s["largo_max"])
                        return e

                @ui.refreshable
                def resumen_diseno() -> None:
                    d = s["diseno"]
                    with ui.column().classes("gap-1"):
                        if d is None:
                            ui.label(tr("Aún no hay diseño: calcula uno a la izquierda.")).classes("opacity-70")
                            return
                        ui.label(f"{tr(TIPOS[d.tipo])} · {d.f_MHz:g} MHz").classes("text-lg font-bold")
                        ui.badge(estado_texto(d.estado))
                        g = ganancias.texto(d, fmt)
                        if g:
                            ui.label(f"{tr('Ganancia')}: {g}").classes("text-sm font-bold")
                        with ui.grid(columns=2).classes("gap-x-6 gap-y-1"):
                            for k, v in d.geometria.items():
                                ui.label(k.replace("_", " "))
                                ui.label(f"{v:.2f}" if isinstance(v, float) else str(v))
                        ui.button(tr("Guardar diseño (diseno.json)"), icon="download",
                                  on_click=lambda: ui.download.content(d.a_json().encode("utf-8"), f"{d.nombre}.json")) \
                            .props("flat")
                        ui.upload(label=tr("Abrir diseno.json"), auto_upload=True, on_upload=abrir_diseno).props("flat dense") \
                            .classes("w-72")

                resumen_diseno()

    # ------------------------------------------------------------------ comunes
    def nuevo_plano() -> None:
        d = s["diseno"]
        d.plano.idioma = i18n.idioma()
        s["plano"], s["hoja"] = planos.generar(d), 0

    async def abrir_diseno(e) -> None:
        try:
            d = Diseno.desde_json((await e.file.read()).decode("utf-8-sig"))
        except Exception as error:  # noqa: BLE001
            ui.notify(tr("No se pudo abrir el diseño: {0}", mensaje(error)), type="negative")
            return
        s["diseno"], s["tipo"], s["f"], s["diametro"] = d, d.tipo, d.f_MHz, d.diametro_mm
        g = d.geometria
        if d.tipo == "yagi":
            s["elementos"], s["eje"] = int(g.get("n_elementos", 3)), g.get("boom", "ninguno")
            s["eje_mm"] = g.get("boom_mm") if s["eje"] != "ninguno" else None
        elif d.tipo in ("colineal", "colineal_bibanda"):
            s["secciones"] = int(g.get("n_secciones", 3))
            s["f_alta"] = g.get("f_alta_MHz", 433.0)
        if d.tipo in TIPOS_HF:
            s["altura"], s["suelo"] = g["altura_mm"] / 1000, g["suelo"]
            if g.get("bandas"):
                s["bandas"] = ", ".join(g["bandas"])
        if d.tipo == "efhw":
            s["relacion"], s["potencia"] = int(g["relacion"]), g.get("potencia_w") or 100.0
        campos_visibles()
        if d.cable:
            s["cable"], s["vf"] = d.cable["nombre"], d.cable["vf"] if d.cable["vf_origen"] == "medido" else None
        nuevo_plano()
        refrescar()
        pestanas.set_value(t_plano)

    async def descargar_3d() -> None:
        d = s["diseno"]
        try:
            datos = await run.cpu_bound(escritorio.plantilla3d, d.a_json(), float(s["cama"] or 200.0), 0.3,
                                        float(s["radio"]) if s["radio"] else None)
        except Exception as error:  # noqa: BLE001
            ui.notify(mensaje(error), type="negative")
            return
        ui.download.content(datos, f"{d.nombre}_plantilla3d.zip", "application/zip")

    # ------------------------------------------------------------------ Simulación
    with paneles:
        with ui.tab_panel(t_sim):
            @ui.refreshable
            def simulacion() -> None:
                d = s["diseno"]
                if d is None or not d.resultados:
                    ui.label(tr("Sin simulación: calcula el diseño con el ajuste de PyNEC en la pestaña Diseño.")).classes("opacity-70")
                    return
                r = d.resultados
                ui.label(tr("Simulado (NEC2), sin medir")).classes("text-lg font-bold")
                with ui.row().classes("gap-8"):
                    if "r_ohm" in r:
                        signo = "+" if r["x_ohm"] >= 0 else "−"
                        ui.label(f"Z = {r['r_ohm']:.1f} {signo} j{abs(r['x_ohm']):.1f} Ω")
                    if "roe" in r:
                        ui.label(f"{tr('ROE')} = {r['roe']:.2f}")
                    if "ganancia_dBi" in r:
                        ui.label(f"{r['ganancia_dBi']:.2f} dBi")
                if r.get("barrido"):
                    b = banda_de(d.f_MHz)
                    ui.html(svg_roe([(tr("Simulado"), r["barrido"]["f_MHz"], r["barrido"]["roe"])], b[1:] if b else None),
                            sanitize=False).classes("w-full max-w-2xl")
                if "roe_con_red" in r:
                    ui.label(tr("ROE sin red {0} · con red en L {1} · ROE ≤ 2 en solo {2} MHz",
                                f"{r['roe_sin_red']:.1f}", f"{r['roe_con_red']:.2f}", f"{r['ancho_roe2_MHz']:.1f}"))
                    red = (r.get("red") or {})
                    if red:
                        ui.label(", ".join(f"{k}: {v:.3g}" for k, v in red.items() if isinstance(v, float)))
                try:
                    th, ph, gd = motor.diagrama(d.modelo())
                    ui.label(tr("Diagrama de radiación (NEC2) a {0} MHz", f"{d.f_MHz:g}")).classes("font-bold")
                    ui.html(svg_diagrama(th, ph, gd), sanitize=False).classes("w-full max-w-3xl")
                    escena_diagrama(th, ph, gd, d.modelo())
                except Exception as error:  # noqa: BLE001
                    ui.label(tr("Sin diagrama: {0}", mensaje(error))).classes("text-xs opacity-70")
                ui.label(tr("Espacio libre, sin mástil ni cable de bajada")).classes("text-xs opacity-70")

            simulacion()

    # ------------------------------------------------------------------ Plano
    with paneles:
        with ui.tab_panel(t_plano):
            @ui.refreshable
            def vista_plano() -> None:
                p, d = s["plano"], s["diseno"]
                if p is None:
                    ui.label(tr("Aún no hay plano: calcula un diseño en la pestaña Diseño.")).classes("opacity-70")
                    return
                with ui.row().classes("items-center gap-3"):
                    ui.label(f"{tr(TIPOS[d.tipo])} · {d.f_MHz:g} MHz").classes("text-lg font-bold")
                    ui.badge(estado_texto(d.estado))
                    g = ganancias.texto(d, fmt)
                    if g:
                        ui.badge(f"{tr('Ganancia')}: {g}").props("outline")
                ui.label(tr("Esta vista es la que se descarga. Imprime al 100 % («tamaño real») y comprueba la regla de 80 mm "
                            "antes de usar los detalles 1:1.")).classes("aviso-caja")
                hojas = {i: tr("Hoja {0}", i + 1) for i in range(len(p.hojas))}
                if len(hojas) > 1:
                    ui.toggle(hojas, value=s["hoja"], on_change=lambda e: (s.__setitem__("hoja", e.value), contenido.refresh()))
                with ui.row().classes("gap-2"):
                    ui.button("PDF", on_click=lambda: ui.download.content(planos.a_pdf(p), f"{d.nombre}.pdf",
                                                                           "application/pdf"))
                    ui.button(tr("SVG (hoja)"), on_click=lambda: ui.download.content(
                        planos.a_svg(p.hojas[s["hoja"]]).encode("utf-8"), f"{d.nombre}_hoja{s['hoja'] + 1}.svg"))
                    ui.button(".nec", on_click=lambda: ui.download.content(nec.exportar(d.modelo()).encode("utf-8"),
                                                                           f"{d.nombre}.nec"))
                    ui.button("diseno.json", on_click=lambda: ui.download.content(d.a_json().encode("utf-8"), f"{d.nombre}.json"))
                if d.tipo in TIPOS_3D:
                    with ui.row().classes("items-end gap-3"):
                        ui.number(tr("Cama de la impresora (mm)"), min=80, step=10).classes("w-48").bind_value(s, "cama")
                        ui.number(tr("Radio de doblado (mm)"), min=1, step=0.5, placeholder=tr("2 × Ø")).classes("w-40").bind_value(s, "radio")
                        ui.button(tr("Plantilla de doblado 3D (STL)"), on_click=descargar_3d).props("outline")

                @ui.refreshable
                def contenido() -> None:
                    ui.html(planos.a_svg(p.hojas[s["hoja"]]), sanitize=False).classes("hoja-svg")

                contenido()

            vista_plano()

    # ------------------------------------------------------------------ Medir
    with paneles:
        with ui.tab_panel(t_medir):
            @ui.refreshable
            def medir() -> None:
                d = s["diseno"]
                if d is None:
                    ui.label(tr("Aún no hay diseño: calcula uno en la pestaña Diseño.")).classes("opacity-70")
                    return
                b = banda_de(d.f_MHz)
                ini, fin = (b[1], b[2]) if b else (d.f_MHz * 0.97, d.f_MHz * 1.03)
                url = f"{VNA_URL}?f={d.f_MHz:g}&banda={ini:g}-{fin:g}&nombre={quote(d.nombre)}"
                ui.label(tr("Medir con el NanoVNA")).classes("text-lg font-bold")
                ui.label(tr("Solo una aplicación puede tener el puerto del NanoVNA: cierra Chirptenna VNA antes de usar otra.")) \
                    .classes("text-xs opacity-70")
                ui.link(tr("Abrir Chirptenna VNA"), url, new_tab=True).classes("text-primary")
                ui.separator()
                ui.label(tr("Importa el .s1p medido para compararlo con la simulación. Un diseño solo pasa a «Medido» si la "
                            "frecuencia medida cae a ≤ 2 % de la simulada."))
                ui.upload(label=tr("Abrir .s1p medido"), auto_upload=True, on_upload=subir_medida).props("flat dense").classes("w-72")
                m = s["medida"]
                if m is not None:
                    curvas = [(tr("Medido"), list(m.f_MHz), list(m.roe))]
                    if d.resultados and d.resultados.get("barrido"):
                        curvas.insert(0, (tr("Simulado"), d.resultados["barrido"]["f_MHz"], d.resultados["barrido"]["roe"]))
                    ui.html(svg_roe(curvas, b[1:] if b else None), sanitize=False).classes("w-full max-w-2xl")
                    c = medidas.comparar(d, m)
                    ui.label(tr("{0}: medida {1} MHz, simulada {2} MHz ({3} % de diferencia)", tr(c["referencia"]),
                                f"{c['f_medida_MHz']:.2f}", f"{c['f_simulada_MHz']:.2f}", f"{c['error_pct']:+.1f}"))
                    if not d.resultados:
                        ui.label(tr("Sin simulación no se puede dar el diseño por medido.")).classes("aviso-caja")
                    ui.button(tr("Guardar la medida con el diseño"), on_click=guardar_medida)
                if d.medida:
                    ui.label(tr("Medida guardada ({0}): {1}", d.medida.get("archivo") or "—", estado_texto(d.estado))) \
                        .classes("font-bold")

            async def subir_medida(e) -> None:
                try:
                    s["medida"] = medidas.leer_s1p((await e.file.read()).decode("utf-8-sig"))
                    s["medida_nombre"] = e.file.name
                except Exception as error:  # noqa: BLE001
                    ui.notify(tr("No se pudo leer el .s1p: {0}", error), type="negative")
                    return
                medir.refresh()

            def guardar_medida() -> None:
                medidas.guardar_medida(s["diseno"], s["medida"], s.get("medida_nombre", ""))
                nuevo_plano()
                refrescar()
                ui.notify(tr("Medida guardada con el diseño"), type="positive")

            medir()


def main() -> None:
    p = argparse.ArgumentParser(description="Chirptenna Wire (interfaz de escritorio)")
    p.add_argument("--puerto", type=int, default=8090)
    p.add_argument("--idioma", choices=sorted(IDIOMAS), default=None)
    a = p.parse_args()
    if a.idioma:
        os.environ["CHIRPTENNA_IDIOMA"] = a.idioma
    app.add_static_files("/img", os.path.join(RAIZ, "img"))
    ui.run(host=os.environ.get("CHIRPTENNA_HOST", "127.0.0.1"), port=a.puerto, title="Chirptenna Wire", reload=False,
           show=False, favicon=os.path.join(RAIZ, "img", "favicon-32.png"), storage_secret="chirptenna-wire")


if __name__ in {"__main__", "__mp_main__"}:
    main()
