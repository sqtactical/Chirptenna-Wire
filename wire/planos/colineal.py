"""Hojas de la colineal con bobinas de fase (VHF/UHF): la antena y la bobina de fase con su ajuste.

Hoja 1: vista general sin escala, lista de corte y resultados simulados. Hoja 2: la bobina de fase a 1:1 (vueltas, tubo
y cómo se une a las secciones) y cómo medirla y ajustarla con el NanoVNA.
"""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..i18n import N_, tr
from .comun import fmt, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, unidad
from .hf_dipolos import _vueltas_bobina
from .hoja import COBRE, GRIS, PVC, ROJO, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto
from .jpole import _simulacion as _simulacion_roe

FORMA_MM = 12.0          # tubo o varilla de la bobina
HUECO_MM = 10.0          # lo que ocupa cada bobina en el modelo (generadores.COL_HUECO_MM)


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    return [_hoja_antena(diseno), _hoja_enlace(diseno) if diseno.tipo == "colineal_bibanda" else _hoja_bobina(diseno)]


def _titulo(diseno: Diseno) -> str:
    from .comun import frecuencia, texto_banda
    if diseno.tipo == "colineal_bibanda":
        return tr(N_("Colineal bibanda · {0} y {1} MHz"), frecuencia(diseno.f_MHz), frecuencia(diseno.geometria["f_alta_MHz"]))
    return tr(N_("Colineal con bobinas de fase · {0} MHz ({1})"), frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


def _hoja_antena(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    largos, bobina, radial = g["secciones_mm"], g["bobina_uH"], g["radial_mm"]
    n, d, u = len(largos), diseno.diametro_mm, unidad(diseno)
    bib = diseno.tipo == "colineal_bibanda"
    hoja = hoja_a4(diseno, _titulo(diseno),
                   tr("{0} secciones verticales con un enlace L-C entre cada dos · {1} radiales · coaxial de 50 Ω", n, fmt(g["radiales"], 0)) if bib
                   else tr("{0} secciones verticales con una bobina de fase entre cada dos · {1} radiales · coaxial de 50 Ω", n, fmt(g["radiales"], 0)))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0}", u))
    # --- dibujo vertical
    gap = 12.0                                                    # separación dibujada de cada bobina (mm de hoja)
    alto_total = sum(largos) + (n - 1) * HUECO_MM + radial * math.sin(math.radians(g["angulo"]))
    esc = (148 - gap * (n - 1)) / alto_total
    x0, y = 62.0, 190.0                                           # base (el conector) en la hoja
    hoja.anadir(Texto(x0, y + 7, tr("coaxial de 50 Ω: vivo al radiador, malla a los radiales"), 5.6, GRIS, ancla="centro"))
    for sgn in (-1, 1):                                           # radiales (se ven dos, de canto)
        hoja.anadir(Linea(x0, y, x0 + sgn * radial * math.cos(math.radians(g["angulo"])) * esc,
                          y + radial * math.sin(math.radians(g["angulo"])) * esc, COBRE, 0.85))
    hoja.anadir(Texto(x0 + radial * math.cos(math.radians(g["angulo"])) * esc + 2, y + 3, tr("radial {0}", longitud(radial, diseno)), 5.6))
    for i, largo in enumerate(largos):
        y2 = y - largo * esc
        hoja.anadir(Linea(x0, y, x0, y2, COBRE, 0.85))
        hoja.anadir(Cota(x0 + 12, y, x0 + 12, y2, longitud(largo, diseno), tam=5.6))
        hoja.anadir(Texto(x0 + 18, (y + y2) / 2 + 2, tr("sección {0}", i + 1), 5.6, GRIS))
        y = y2
        if i < n - 1:                                             # bobina de fase
            pts = [(x0, y)] + [(x0 + (3.2 if k % 2 else -3.2), y - gap * (k + 1) / 8) for k in range(7)] + [(x0, y - gap)]
            for a, b in zip(pts, pts[1:]):
                hoja.anadir(Linea(a[0], a[1], b[0], b[1], ROJO, 0.5))
            hoja.anadir(Texto(x0 - 8, y - gap / 2 + 1.5, tr("bobina {0} µH + {1} pF", fmt(bobina, 2), fmt(g["condensador_pF"], 1)) if bib else tr("bobina {0} µH", fmt(bobina, 2)), 5.6, ROJO, ancla="derecha"))
            y -= gap
    # --- lista de corte (columna derecha)
    sob = diseno.sobrante_mm
    seccion(hoja, 124, 33, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    filas = [[tr("Sección {0}, alambre Ø {1} mm", i + 1, fmt(d, 1)), f"{longitud(v, diseno)} {u}", f"{longitud(v + sob, diseno, 0)} {u}"]
             for i, v in enumerate(largos)]
    filas += [[tr("Radial ×{0}", fmt(g["radiales"], 0)), f"{longitud(radial, diseno)} {u}", f"{longitud(radial + sob, diseno, 0)} {u}"],
              ([tr("Enlace L-C ×{0}", n - 1), tr("{0} µH + {1} pF", fmt(bobina, 2), fmt(g["condensador_pF"], 1)), tr("hoja 2")] if bib else
               [tr("Bobina de fase ×{0}", n - 1), tr("{0} µH", fmt(bobina, 2)), tr("hoja 2")]),
              [tr("Conector SO-239 o N"), "1", "—"]]
    tabla(hoja, 124, 45, [0, 38, 54], [tr("Pieza"), tr("Final"), tr("Cortar a")], filas, 72)
    _simulacion_roe(hoja, diseno)
    r = diseno.resultados
    if bib:
        return _cola_bibanda(hoja, diseno)
    texto = [tr("Cada bobina invierte la fase: sin ella, una media onda\nsobre otra se anularía en el horizonte."),
             tr("Ganancia simulada en espacio libre: con 2 secciones ≈ 3 dBi,\ncon 3 ≈ 5 dBi (lo que anuncian como «2 / 5 dBi»). Sobre un\nmástil o un coche cambia algo.")]
    hoja.anadir(Texto(124, 168, "\n".join(texto), 6.0))
    if r and "sensibilidad_MHz_por_mm" in r:
        hoja.anadir(Texto(124, 196, tr("Ajuste: recorta la sección de arriba; cada mm de menos sube\nla frecuencia ≈ {0} MHz.", fmt(abs(r["sensibilidad_MHz_por_mm"]), 2)), 6.0, VERDE))
    hoja.anadir(Texto(124, 208, tr("Simulada con bobinas ideales y sin mástil. La bobina real tiene\ncapacidad y pérdida: se mide y se ajusta (hoja 2)."), 6.0, ROJO))
    return hoja


def _hoja_bobina(diseno: Diseno) -> Hoja:
    g, d = diseno.geometria, diseno.diametro_mm
    bobina, f = g["bobina_uH"], diseno.f_MHz
    hilo = min(d, 2.0)
    n, largo = _vueltas_bobina(bobina, FORMA_MM, hilo)
    x_ohm = 2 * math.pi * f * 1e6 * bobina * 1e-6
    hoja = hoja_a4(diseno, tr("Bobina de fase · montaje y ajuste"),
                   tr("La inductancia en serie que pone en fase las secciones a {0} MHz", fmt(f, 2)))
    seccion(hoja, 14, 33, tr("DATOS"), tr("Valor de partida de la simulación: se mide y se ajusta"), VERDE)
    filas = [[tr("Inductancia"), tr("{0} µH", fmt(bobina, 2)), tr("reactancia ≈ {0} Ω a {1} MHz", fmt(x_ohm, 0), fmt(f, 1))],
             [tr("Bobina"), tr("≈ {0} vueltas", str(n)), tr("hilo Ø {0} mm sobre un tubo de Ø {1} mm, {2} mm de largo", fmt(hilo, 1), fmt(FORMA_MM, 0), fmt(largo, 0))],
             [tr("Cantidad"), str(len(g["secciones_mm"]) - 1), tr("una entre cada dos secciones; todas iguales")]]
    tabla(hoja, 14, 46, [0, 36, 66], [tr("Pieza"), tr("Valor"), tr("Montaje")], filas, 184)
    seccion(hoja, 14, 74, tr("LA BOBINA A 1:1"), tr("Escala 1:1 · las secciones entran por los extremos"), VERDE)
    esc = min(1.0, 120.0 / (largo + 20))
    x0, yc = 40.0, 106.0
    r = FORMA_MM / 2 * esc
    xb = x0 + 10 * esc
    paso = largo / max(n, 1) * esc
    hoja.anadir(Rect(x0, yc - r, (largo + 20) * esc, 2 * r, PVC, 0.4, None))
    for k in range(n):
        x = xb + k * paso
        hoja.anadir(Linea(x, yc - r - 0.6, x + paso * 0.5, yc + r + 0.6, COBRE, 0.35))
    hoja.anadir(Linea(x0 - 22, yc, xb, yc, COBRE, 0.5))
    hoja.anadir(Linea(xb + largo * esc, yc, x0 + (largo + 20) * esc + 22, yc, COBRE, 0.5))
    hoja.anadir(Cota(xb, yc + r + 8, xb + largo * esc, yc + r + 8, tr("{0} mm", fmt(largo, 0)), 6.0,
                     ref1=(xb, yc + r), ref2=(xb + largo * esc, yc + r)))
    hoja.anadir(Texto(x0 - 22, yc - 5, tr("sección de abajo"), 5.6, GRIS),
                Texto(x0 + (largo + 20) * esc + 22, yc - 5, tr("sección de arriba"), 5.6, GRIS, ancla="derecha"))
    hoja.anadir(Texto(14, 126, tr("Las dos secciones y la bobina son el mismo alambre en el modelo; en la práctica se sueldan a la bobina (o se\n"
                                  "enrolla la propia varilla/hilo). Cubre la bobina con un tubo o termorretráctil: el agua y los dedos la mueven."), 5.8, GRIS, "cursiva"))
    seccion(hoja, 14, 140, tr("MEDIRLA Y AJUSTARLA CON EL NANOVNA"), tr("Antes de montarla en la antena"), VERDE)
    pasos = [tr("1. Enrolla las vueltas sobre el tubo, con las espiras casi juntas, y deja las patas de 15–20 mm."),
             tr("2. Calibra el VNA (abierto, corto y carga) y conecta la bobina entre vivo y masa con las patas más cortas posible."),
             tr("3. A una frecuencia baja (10–30 MHz) la reactancia es X = 2π·f·L: mide X y calcula L = X / (2π·f)."),
             tr("4. Si falta inductancia, añade una vuelta (≈ 8 % por vuelta); si sobra, quita una o abre un poco las espiras."),
             tr("5. Comprueba que la autorresonancia queda al menos 3 veces por encima de {0} MHz: si no, usa menos vueltas más separadas.", fmt(f, 0)),
             tr("6. Monta la antena y mide la ROE en la banda: recorta la sección de arriba hasta el mínimo en {0} MHz.", fmt(f, 2)),
             tr("7. Si el mínimo no baja de 1,5, toca la bobina (±1 vuelta) y vuelve a recortar: la bobina manda en la fase.")]
    hoja.anadir(Texto(14, 152, "\n".join(pasos), 6.3))
    hoja.anadir(Texto(14, 200, tr("Una bobina real tiene pérdida y capacidad entre espiras: la ganancia y la adaptación saldrán algo\n"
                                  "peores que en la simulación (que usa bobinas ideales). Sin medir."), 6.0, ROJO))
    regla(hoja, 14, 244)
    return hoja


def _cola_bibanda(hoja: Hoja, diseno: Diseno) -> Hoja:
    """Resultados de la banda alta y avisos de la hoja 1 de la colineal bibanda."""
    r, g = diseno.resultados, diseno.geometria
    if r and "alta" in r:
        a = r["alta"]
        seccion(hoja, 128, 168, tr("BANDA ALTA {0} MHz", fmt(g["f_alta_MHz"], 0)), tr("ROE {0} · {1} dBi (espacio libre)", fmt(a["roe"], 2), fmt(a["ganancia_dBi"], 1)))
        grafica_roe(hoja, 138, 180, 58, 31, a["barrido"]["f_MHz"], a["barrido"]["roe"], None)
    hoja.anadir(Texto(124, 222, tr("En {0} MHz es un ¼ o 5/8 de onda (los enlaces no hacen nada);\n"
                                   "en {1} MHz cada enlace es una bobina y apila medias ondas.\n"
                                   "Componentes ideales: el enlace real se mide (hoja 2).", fmt(diseno.f_MHz, 0), fmt(g["f_alta_MHz"], 0)), 6.0, ROJO))
    return hoja


def _hoja_enlace(diseno: Diseno) -> Hoja:
    g, d = diseno.geometria, diseno.diametro_mm
    bobina, cond, f_baja, f_alta = g["bobina_uH"], g["condensador_pF"], diseno.f_MHz, g["f_alta_MHz"]
    hilo = min(d, 2.0)
    n, largo = _vueltas_bobina(bobina, FORMA_MM, hilo)
    f_serie = 1 / (2 * math.pi * math.sqrt(bobina * 1e-6 * cond * 1e-12)) / 1e6
    x_alta = 2 * math.pi * f_alta * 1e6 * bobina * 1e-6 - 1 / (2 * math.pi * f_alta * 1e6 * cond * 1e-12)
    hoja = hoja_a4(diseno, tr("Enlace L-C · montaje y ajuste"),
                   tr("Bobina y condensador en serie: no hacen nada en {0} MHz y dan la fase en {1} MHz", fmt(f_baja, 0), fmt(f_alta, 0)))
    seccion(hoja, 14, 33, tr("DATOS"), tr("Valores de partida de la simulación: se miden y se ajustan"), VERDE)
    filas = [[tr("Bobina"), tr("{0} µH", fmt(bobina, 2)), tr("≈ {0} vueltas de hilo Ø {1} mm sobre un tubo de Ø {2} mm, {3} mm de largo", str(n), fmt(hilo, 1), fmt(FORMA_MM, 0), fmt(largo, 0))],
             [tr("Condensador"), tr("{0} pF", fmt(cond, 1)), tr("C0G/NP0 (o cerámico de RF), en serie con la bobina, con las patillas cortas")],
             [tr("Resonancia serie"), tr("{0} MHz", fmt(f_serie, 0)), tr("el ajuste la deja algo por debajo de {0} MHz: ahí el enlace casi no se nota", fmt(f_baja, 0))],
             [tr("En {0} MHz", fmt(f_alta, 0)), tr("{0} Ω", fmt(x_alta, 0)), tr("inductivo: se comporta como la bobina de fase de la colineal")],
             [tr("Cantidad"), str(len(g["secciones_mm"]) - 1), tr("uno entre cada dos secciones; todos iguales")]]
    tabla(hoja, 14, 46, [0, 36, 62], [tr("Pieza"), tr("Valor"), tr("Montaje")], filas, 184)
    seccion(hoja, 14, 84, tr("EL ENLACE A 1:1"), tr("Escala 1:1 · bobina y condensador en serie, las secciones entran por los extremos"), VERDE)
    esc = min(1.0, 110.0 / (largo + 30))
    x0, yc = 44.0, 112.0
    r = FORMA_MM / 2 * esc
    xb = x0 + 8 * esc
    paso = largo / max(n, 1) * esc
    hoja.anadir(Rect(x0, yc - r, (largo + 16) * esc, 2 * r, PVC, 0.4, None))
    for k in range(n):
        x = xb + k * paso
        hoja.anadir(Linea(x, yc - r - 0.6, x + paso * 0.5, yc + r + 0.6, COBRE, 0.35))
    xe = xb + largo * esc
    xc = x0 + (largo + 16) * esc + 12
    hoja.anadir(Linea(x0 - 20, yc, xb, yc, COBRE, 0.5))
    hoja.anadir(Linea(xe, yc, xc, yc, COBRE, 0.5))
    hoja.anadir(Linea(xc, yc - 4, xc, yc + 4, COBRE, 0.7))                         # condensador en serie
    hoja.anadir(Linea(xc + 2.5, yc - 4, xc + 2.5, yc + 4, COBRE, 0.7))
    hoja.anadir(Linea(xc + 2.5, yc, xc + 22, yc, COBRE, 0.5))
    hoja.anadir(Texto(xc + 1.2, yc - 7, "C", 6.0, ROJO, "negrita", "centro"))
    hoja.anadir(Cota(xb, yc + r + 8, xe, yc + r + 8, tr("{0} mm", fmt(largo, 0)), 6.0, ref1=(xb, yc + r), ref2=(xe, yc + r)))
    hoja.anadir(Texto(x0 - 20, yc - 5, tr("sección de abajo"), 5.6, GRIS), Texto(xc + 22, yc - 5, tr("sección de arriba"), 5.6, GRIS, ancla="derecha"))
    seccion(hoja, 14, 140, tr("MEDIRLO Y AJUSTARLO CON EL NANOVNA"), tr("Antes de montarlo en la antena"), VERDE)
    pasos = [tr("1. Enrolla la bobina y suelda el condensador en serie, con las patas lo más cortas posible."),
             tr("2. Calibra el VNA y pon el enlace entre CH0 y CH1 como un elemento en serie (S21, 50 Ω a cada lado)."),
             tr("3. En la resonancia serie S21 sube hasta casi 0 dB: ajústala a {0} MHz con los espacios entre espiras o el condensador.", fmt(f_serie, 0)),
             tr("4. Un condensador menor sube la resonancia (f ∝ 1/√C); un pF de más o de menos la mueve un 10–15 %."),
             tr("5. A {0} MHz el enlace debe ser inductivo y de reactancia alta (S21 mucho más bajo): si no, tiene demasiado C.", fmt(f_alta, 0)),
             tr("6. Monta la antena y mide la ROE en las dos bandas; recorta la sección de arriba (mueve las dos) y retoca el enlace (manda en {0} MHz).", fmt(f_alta, 0)),
             tr("7. Si {0} MHz queda bien y {1} MHz no, retoca la longitud de la sección de abajo y el condensador.", fmt(f_alta, 0), fmt(f_baja, 0))]
    hoja.anadir(Texto(14, 152, "\n".join(pasos), 6.3))
    hoja.anadir(Texto(14, 200, tr("Las dos bandas se acoplan: conviene medir las dos tras cada cambio. La simulación usa componentes ideales; el condensador\n"
                                  "real tiene su propia resonancia y la bobina capacidad entre espiras. Sin medir."), 6.0, ROJO))
    regla(hoja, 14, 244)
    return hoja
