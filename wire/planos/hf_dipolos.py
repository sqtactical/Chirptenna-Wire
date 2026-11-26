"""Hojas de los dipolos de HF sobre suelo real: dipolo, V invertida, abanico, trampas y G5RV.

Cada una lleva una hoja con la antena (vista, lista de corte y ROE por banda) y otra con el balun o choke 1:1; el dipolo de
trampas lleva además la hoja de las trampas. Los valores del balun y de las trampas son los **habituales de los montajes de
aficionados**, sin verificar aquí: se comprueban con el VNA.
"""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..i18n import tr
from .comun import fmt, frecuencia, hoja_a4, regla, seccion, tabla, texto_banda
from .hf import SUELO_NOMBRE, _m
from .hoja import COBRE, GRIS, PVC, ROJO, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto

TITULOS = {"dipolo_hf": "Dipolo de HF", "vinv_hf": "V invertida de HF", "abanico": "Dipolo en abanico", "trampas": "Dipolo con trampas",
           "g5rv": "G5RV"}


def hojas_hilo(diseno: Diseno, fecha: str) -> list[Hoja]:
    hojas = [_hoja_antena(diseno), _hoja_balun(diseno)]
    if diseno.tipo == "trampas":
        hojas.append(_hoja_trampas(diseno))
    return hojas


def _titulo(diseno: Diseno) -> str:
    nombre = {"dipolo_hf": tr("Dipolo de HF"), "vinv_hf": tr("V invertida de HF"), "abanico": tr("Dipolo en abanico"),
              "trampas": tr("Dipolo con trampas"), "g5rv": tr("G5RV")}[diseno.tipo]
    return tr("{0} · {1} MHz ({2})", nombre, frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


# ---------------------------------------------------------------- hoja 1: la antena

def _vista(hoja: Hoja, diseno: Diseno) -> None:
    g = diseno.geometria
    alto = g["altura_mm"]
    x0, x1, yb, ya = 30.0, 190.0, 82.0, 50.0                       # extremos del dibujo, suelo y altura del centro
    xc = (x0 + x1) / 2
    hoja.anadir(Linea(20, yb, 196, yb, GRIS, 0.6), Texto(196, yb + 4, tr("suelo"), 5.4, GRIS, ancla="derecha"),
                Linea(xc, yb, xc, ya + 3, GRIS, 0.8))
    if diseno.tipo == "dipolo_hf":
        hoja.anadir(Linea(x0, ya, x1, ya, COBRE, 1.0), Rect(xc - 4, ya - 1, 8, 6, TINTA, 0.3, PVC),
                    Cota(x0, ya - 10, x1, ya - 10, tr("largo {0}", _m(g["largo_mm"], diseno)), tam=5.6, ref1=(x0, ya - 3), ref2=(x1, ya - 3)),
                    Texto(xc + 6, ya + 9, tr("balun 1:1 y coaxial"), 5.4, GRIS))
    elif diseno.tipo == "vinv_hf":
        m = math.radians(g["apertura"] / 2)
        dx, dz = 70.0 * math.sin(m), 70.0 * math.cos(m)
        hoja.anadir(Linea(xc, ya - 6, xc - dx, ya - 6 + dz * 0.45, COBRE, 1.0), Linea(xc, ya - 6, xc + dx, ya - 6 + dz * 0.45, COBRE, 1.0),
                    Rect(xc - 4, ya - 10, 8, 6, TINTA, 0.3, PVC),
                    Texto(xc + dx + 2, ya - 6 + dz * 0.45, tr("brazo {0}", _m(g["brazo_mm"], diseno)), 5.4),
                    Texto(xc + 6, ya + 2, tr("apertura {0}°", fmt(g["apertura"], 0)), 5.4, GRIS))
    elif diseno.tipo == "abanico":
        n = len(g["largos_mm"])
        mayor = max(g["largos_mm"])
        for k, (b, largo) in enumerate(zip(g["bandas"], g["largos_mm"])):
            ancho = 58.0 * largo / mayor
            y = ya + (k - (n - 1) / 2) * 5.0
            hoja.anadir(Linea(xc - ancho, y, xc + ancho, y, COBRE, 0.9), Texto(xc + ancho + 2, y + 1.5, f"{b} {_m(largo, diseno)}", 5.2))
        hoja.anadir(Rect(xc - 4, ya - 4, 8, 8, TINTA, 0.3, PVC))
    elif diseno.tipo == "trampas":
        ai, ae = g["interior_mm"], g["exterior_mm"]
        escala = (x1 - x0) / 2 / (ai + ae + g["trampa_largo_mm"])
        xi = xc + ai * escala
        xe = xc + (ai + ae + g["trampa_largo_mm"]) * escala
        for lado in (1, -1):
            xa, xb = xc + lado * ai * escala, xc + lado * (ai + g["trampa_largo_mm"]) * escala
            hoja.anadir(Linea(xc, ya, xc + lado * (ai + ae + g["trampa_largo_mm"]) * escala, ya, COBRE, 1.0),
                        Rect(min(xa, xb) - 2, ya - 4, abs(xb - xa) + 4, 8, TINTA, 0.3, PVC))
        hoja.anadir(Rect(xc - 4, ya - 1, 8, 6, TINTA, 0.3, PVC),
                    Cota(xc, ya - 10, xi, ya - 10, tr("interior {0}", _m(ai, diseno)), tam=5.2, ref1=(xc, ya - 3), ref2=(xi, ya - 5)),
                    Cota(xi, ya - 18, xe, ya - 18, tr("exterior {0}", _m(ae, diseno)), tam=5.2, ref1=(xi, ya - 5), ref2=(xe, ya - 3)),
                    Texto(xi - 2, ya + 10, tr("trampa"), 5.4, GRIS, ancla="derecha"))
    else:                                                                              # g5rv
        hoja.anadir(Linea(x0, ya, x1, ya, COBRE, 1.0), Rect(xc - 4, ya - 1, 8, 6, TINTA, 0.3, PVC),
                    Linea(xc - 1, ya + 5, xc - 1, yb - 8, COBRE, 0.5), Linea(xc + 1, ya + 5, xc + 1, yb - 8, COBRE, 0.5),
                    Cota(x0, ya - 10, x1, ya - 10, tr("dipolo {0}", _m(g["largo_mm"], diseno)), tam=5.6, ref1=(x0, ya - 3), ref2=(x1, ya - 3)),
                    Texto(xc + 6, ya + 14, tr("escalerilla {0}", _m(g["escalerilla_mm"], diseno)), 5.4),
                    Texto(xc + 6, yb - 6, tr("choke 1:1 y coaxial de 50 Ω"), 5.4, GRIS))
    if diseno.tipo != "vinv_hf":
        hoja.anadir(Cota(x1 - 6, ya, x1 - 6, yb, _m(alto, diseno), tam=5.0))
    else:
        hoja.anadir(Cota(x1 - 6, ya - 6, x1 - 6, yb, _m(alto, diseno), tam=5.0))


def _filas_corte(diseno: Diseno) -> list[list[str]]:
    g, d, sob = diseno.geometria, diseno.diametro_mm, diseno.sobrante_mm
    hilo = tr("Hilo, Ø {0} mm", fmt(d, 1))
    if diseno.tipo == "dipolo_hf":
        return [[hilo, "2", _m(g["largo_mm"] / 2, diseno), _m(g["largo_mm"] / 2 + sob, diseno)]]
    if diseno.tipo == "vinv_hf":
        return [[hilo, "2", _m(g["brazo_mm"], diseno), _m(g["brazo_mm"] + sob, diseno)]]
    if diseno.tipo == "abanico":
        return [[tr("Hilo {0}, Ø {1} mm", b, fmt(d, 1)), "2", _m(largo / 2, diseno), _m(largo / 2 + sob, diseno)]
                for b, largo in zip(g["bandas"], g["largos_mm"])]
    if diseno.tipo == "trampas":
        return [[tr("Tramo interior, Ø {0} mm", fmt(d, 1)), "2", _m(g["interior_mm"], diseno), _m(g["interior_mm"] + sob, diseno)],
                [tr("Tramo exterior, Ø {0} mm", fmt(d, 1)), "2", _m(g["exterior_mm"], diseno), _m(g["exterior_mm"] + sob, diseno)],
                [tr("Trampa LC (hoja 3)"), "2", tr("{0} µH · {1} pF", fmt(g["trampa_L_uH"], 2), fmt(g["trampa_C_pF"], 0)), "—"]]
    return [[tr("Hilo del dipolo, Ø {0} mm", fmt(d, 1)), "2", _m(g["largo_mm"] / 2, diseno), _m(g["largo_mm"] / 2 + sob, diseno)],
            [tr("Escalerilla de {0} Ω, VF {1}", fmt(g["escalerilla_z0"], 0), fmt(g["escalerilla_vf"], 2)), "1", _m(g["escalerilla_mm"], diseno),
             _m(g["escalerilla_mm"] + sob, diseno)]]


def _hoja_antena(diseno: Diseno) -> Hoja:
    g, r = diseno.geometria, diseno.resultados
    hoja = hoja_a4(diseno, _titulo(diseno),
                   tr("A {0} sobre suelo {1} · alimentada con coaxial de 50 Ω y balun 1:1", _m(g["altura_mm"], diseno), tr(SUELO_NOMBRE[g["suelo"]])))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista lateral, sin escala"))
    _vista(hoja, diseno)
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    filas = _filas_corte(diseno) + [[tr("Aislador central y de extremos, cuerda"), "1", "—", "—"],
                                    [tr("Balun o choke 1:1 y coaxial de 50 Ω"), "1", tr("hoja 2"), "—"]]
    tabla(hoja, 14, 103, [0, 70, 82, 106], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 132)
    y0 = 103 + 9 + 6.5 * len(filas)
    if r and r.get("bandas"):
        seccion(hoja, 14, y0 + 6, tr("SIMULADO (NEC2) · SIN MEDIR"), tr("Suelo {0}, a 50 Ω: la ROE es la del coaxial", tr(SUELO_NOMBRE[g["suelo"]])), VERDE)
        filas = [[b["banda"], fmt(b["f_MHz"], 2), fmt(b["roe"], 2), fmt(b["roe_max"], 2),
                  f"{fmt(b['r_ohm'], 0)} {'+' if b['x_ohm'] >= 0 else '−'} j{fmt(abs(b['x_ohm']), 0)}", fmt(b["ganancia_dBi"], 1)] for b in r["bandas"]]
        y = tabla(hoja, 14, y0 + 18, [0, 24, 52, 80, 108, 148], [tr("Banda"), tr("f (MHz)"), tr("ROE centro"), tr("ROE máx."), tr("Z (Ω)"), tr("dBi")],
                  filas, 180)
        avisos = [tr("La ganancia es la máxima del diagrama (no hacia el horizonte); el suelo cambia la impedancia y el diagrama.")]
        malas = [b["banda"] for b in r["bandas"] if b["roe"] > 2.0]
        if malas:
            avisos.insert(0, tr("ROE > 2 en {0}: ahí hace falta un acoplador.", ", ".join(malas)))
        if diseno.tipo == "abanico":
            avisos.append(tr("Los hilos se acoplan entre sí: ajusta una banda cada vez con el VNA, empezando por la más alta."))
        if diseno.tipo == "g5rv":
            avisos.append(tr("La G5RV no se adapta por sí sola: se usa con acoplador, y el coaxial pierde con ROE alta."))
        hoja.anadir(Texto(14, y + 6, "\n".join(avisos), 6.0, VERDE))
    else:
        seccion(hoja, 14, y0 + 6, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(14, y0 + 18, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
    regla(hoja, 14, 244)
    return hoja


# ---------------------------------------------------------------- hoja 2: balun o choke 1:1

def _hoja_balun(diseno: Diseno) -> Hoja:
    hoja = hoja_a4(diseno, tr("Balun o choke 1:1 · montaje y comprobación"),
                   tr("Corta las corrientes que bajan por fuera del coaxial: el cable no debe radiar ni captar ruido"))
    seccion(hoja, 14, 33, tr("TRES FORMAS DE HACERLO"), tr("Valores habituales de aficionado, sin verificar: se comprueban con el VNA"), VERDE)
    filas = [
        [tr("Choke de coaxial enrollado"), tr("8–10 vueltas de RG-58 o RG-316 en un diámetro de 15–20 cm, atadas"), tr("Sin núcleo; sirve de 3,5 a 30 MHz")],
        [tr("Choke con ferrita"), tr("FT240-31 o FT240-43 con 8–10 vueltas de RG-316 (hasta ~100 W)"), tr("Más compacto; con más potencia, dos núcleos")],
        [tr("Balun de corriente de dos devanados"), tr("Primario y secundario iguales, 8–10 vueltas bifilares en FT240-43"), tr("Para dipolos y V invertidas")],
    ]
    tabla(hoja, 14, 46, [0, 50, 132], [tr("Montaje"), tr("Cómo"), tr("Nota")], filas, 182)
    seccion(hoja, 14, 76, tr("DÓNDE VA"), tr("Siempre pegado al punto de alimentación"), VERDE)
    pasos = [tr("• Dipolo, V invertida, abanico y trampas: justo debajo del aislador central, con el coaxial bajando en vertical un trozo."),
             tr("• G5RV: al pie de la escalerilla, donde se une al coaxial; es ahí donde se mide la ROE de la tabla."),
             tr("• Un segundo choke a la entrada de la casa, si hay ruido, no hace daño.")]
    hoja.anadir(Texto(14, 88, "\n".join(pasos), 6.3))
    seccion(hoja, 14, 112, tr("COMPROBACIÓN CON EL NANOVNA"), tr("Orientativa: un NanoVNA mide mal las impedancias muy altas"), VERDE)
    pasos = [tr("1. Con el choke ya montado, junta el vivo y la malla en un extremo del coaxial (cortocircuito)."),
             tr("2. Calibra el VNA y conecta el otro extremo del coaxial: lo que mides es la impedancia por fuera de la malla."),
             tr("3. Mira el módulo de Z de 3 a 30 MHz: lo bueno es más de 1 kΩ en las bandas que uses."),
             tr("4. Si queda corto en las bajas, añade vueltas; si falla en las altas, junta menos las vueltas (menos capacidad)."),
             tr("5. Con la antena puesta, la ROE no debe cambiar al tocar el coaxial o moverlo: si cambia, falta choke.")]
    hoja.anadir(Texto(14, 124, "\n".join(pasos), 6.3))
    hoja.anadir(Texto(14, 160, tr("Un asistente de Chirptenna VNA hará esta medida paso a paso; todavía no existe."), 6.2, GRIS))
    regla(hoja, 14, 244)
    return hoja


# ---------------------------------------------------------------- hoja 3: las trampas

def _vueltas_bobina(l_uh: float, diametro_forma_mm: float, hilo_mm: float) -> tuple[int, float]:
    """Vueltas y largo (mm) de una bobina de una capa, con las espiras juntas, de `l_uh` µH (fórmula de Wheeler, en pulgadas)."""
    d_in = diametro_forma_mm / 25.4
    paso = (hilo_mm + 0.3) / 25.4
    mejor = (1, 0.0)
    for n in range(1, 80):
        largo = n * paso
        l = n * n * d_in * d_in / (18 * d_in + 40 * largo)
        mejor = (n, largo * 25.4)
        if l >= l_uh:
            break
    return mejor


def _hoja_trampas(diseno: Diseno) -> Hoja:
    g, d = diseno.geometria, diseno.diametro_mm
    forma = 40.0                                                      # tubo de PVC de Ø 40 mm
    n, largo = _vueltas_bobina(g["trampa_L_uH"], forma, min(d, 2.0))
    hoja = hoja_a4(diseno, tr("Trampas · bobina y condensador"),
                   tr("Circuito L-C en paralelo resonante a {0} MHz: en la banda alta deja el tramo exterior sin conectar", fmt(g["f_alta_MHz"], 2)))
    seccion(hoja, 14, 33, tr("DATOS"), tr("Valores de partida de la simulación: se ajustan con el VNA"), VERDE)
    filas = [[tr("Bobina"), tr("{0} µH", fmt(g["trampa_L_uH"], 2)), tr("≈ {0} vueltas de hilo Ø {1} mm juntas en un tubo de PVC de Ø {2} mm ({3} mm de largo)", str(n), fmt(min(d, 2.0), 1), fmt(forma, 0), fmt(largo, 0))],
             [tr("Condensador"), tr("{0} pF", fmt(g["trampa_C_pF"], 0)), tr("mica o C0G, ≥ 3 kV: dos o tres en paralelo reparten la tensión y la corriente")],
             [tr("Resonancia"), tr("{0} MHz", fmt(g["f_alta_MHz"], 2)), tr("en paralelo con Q ≈ 100 en el modelo; una trampa real pierde algo más")]]
    tabla(hoja, 14, 46, [0, 36, 66], [tr("Pieza"), tr("Valor"), tr("Montaje")], filas, 184)
    seccion(hoja, 14, 82, tr("ESQUEMA Y MONTAJE"), tr("Circuito eléctrico y trampa montada en su tubo"), VERDE)
    _dibujo_trampa(hoja, g, forma, n, largo)
    seccion(hoja, 14, 154, tr("AJUSTE CON EL VNA"), tr("Antes de subirla al hilo"), VERDE)
    pasos = [tr("1. Enrolla la bobina con las espiras juntas y suelda el condensador en paralelo, con las patillas más cortas posible."),
             tr("2. Pon la trampa entre dos lazos de una vuelta, muy separados de ella, uno en cada puerto del VNA, y mide S21."),
             tr("3. En la resonancia hay un pozo estrecho de S21; con un solo lazo, un pico en el módulo de S11 o un cambio de Z."),
             tr("4. Ajusta hasta {0} MHz abriendo o cerrando las espiras (más espiras juntas = frecuencia más baja).", fmt(g["f_alta_MHz"], 2)),
             tr("5. Acopla lo menos posible: con los lazos pegados la lectura baja de frecuencia y miente."),
             tr("6. Cierra el tubo (el hilo entra y sale por los extremos) y mide otra vez: la tapa y el pegamento mueven la frecuencia."),
             tr("7. Con la antena puesta, retoca el tramo exterior (no la trampa) hasta la mejor ROE en la banda baja.")]
    hoja.anadir(Texto(14, 166, "\n".join(pasos), 6.3))
    # medida: VNA — lazo — trampa — lazo — VNA
    y = 212
    hoja.anadir(Rect(14, y - 7, 26, 14, TINTA, 0.25, None))
    hoja.anadir(Texto(27, y + 1, "VNA CH0", 6.0, TINTA, "negrita", "centro"))
    hoja.anadir(Rect(170, y - 7, 26, 14, TINTA, 0.25, None))
    hoja.anadir(Texto(183, y + 1, "VNA CH1", 6.0, TINTA, "negrita", "centro"))
    hoja.anadir(Linea(40, y, 62, y, TINTA, 0.25))
    hoja.anadir(Circulo(68, y, 6, COBRE, 0.35))
    hoja.anadir(Rect(92, y - 7, 36, 14, COBRE, 0.5, None))
    hoja.anadir(Texto(110, y + 1, tr("trampa"), 6.0, TINTA, "normal", "centro"))
    hoja.anadir(Circulo(152, y, 6, COBRE, 0.35))
    hoja.anadir(Linea(158, y, 170, y, TINTA, 0.25))
    hoja.anadir(Linea(74, y, 92, y, GRIS, 0.15, (1, 1)))
    hoja.anadir(Linea(128, y, 146, y, GRIS, 0.15, (1, 1)))
    hoja.anadir(Texto(68, y + 10, tr("lazo"), 6.0, GRIS, "cursiva", "centro"))
    hoja.anadir(Texto(152, y + 10, tr("lazo"), 6.0, GRIS, "cursiva", "centro"))
    hoja.anadir(Texto(14, 230, tr("La trampa alarga algo el dipolo en la banda baja y su pérdida estrecha las dos bandas: la simulación\n"
                                  "usa trampas ideales de Q = 100, y la trampa real conviene medirla antes de fiarse de las cotas."), 6.0, ROJO))
    regla(hoja, 14, 244)
    return hoja


def _dibujo_trampa(hoja: Hoja, g: dict, forma: float, n: int, largo: float) -> None:
    """Esquema L-C (izquierda) y la trampa montada en su tubo (derecha, a 1:1 si cabe)."""
    # --- esquema eléctrico
    y = 114
    hoja.anadir(Texto(14, 94, tr("Esquema"), 6.3, GRIS, "cursiva"))
    hoja.anadir(Linea(14, y, 24, y))
    hoja.anadir(Linea(24, y - 12, 24, y + 12))
    hoja.anadir(Linea(24, y - 12, 80, y - 12))
    hoja.anadir(Linea(24, y + 12, 80, y + 12))
    # bobina: zigzag redondeado de 5 picos entre x = 34 y x = 70
    xs = [34 + k * 36 / 10 for k in range(11)]
    hoja.anadir(Linea(24, y - 12, 34, y - 12))
    zig = [(xs[0], y - 12)] + [(xs[k], y - 12 + (-5 if k % 2 else 5)) for k in range(1, 10)] + [(xs[10], y - 12)]
    for a, b in zip(zig, zig[1:]):
        hoja.anadir(Linea(a[0], a[1], b[0], b[1], COBRE, 0.35))
    hoja.anadir(Linea(70, y - 12, 80, y - 12))
    hoja.anadir(Texto(52, y - 20, tr("L = {0} µH", fmt(g["trampa_L_uH"], 2)), 6.3, TINTA, "normal", "centro"))
    # condensador (dos placas) en la rama de abajo
    hoja.anadir(Linea(24, y + 12, 49, y + 12))
    hoja.anadir(Linea(49, y + 6, 49, y + 18, COBRE, 0.5))
    hoja.anadir(Linea(55, y + 6, 55, y + 18, COBRE, 0.5))
    hoja.anadir(Linea(55, y + 12, 80, y + 12))
    hoja.anadir(Texto(52, y + 26, tr("C = {0} pF", fmt(g["trampa_C_pF"], 0)), 6.3, TINTA, "normal", "centro"))
    hoja.anadir(Linea(80, y - 12, 80, y + 12))
    hoja.anadir(Linea(80, y, 90, y))
    hoja.anadir(Texto(14, y + 8, tr("hilo"), 6.0, GRIS, "cursiva"))
    hoja.anadir(Texto(84, y + 8, tr("hilo"), 6.0, GRIS, "cursiva"))
    # --- trampa montada: tubo de PVC con la bobina
    hoja.anadir(Texto(100, 94, tr("Montada"), 6.3, GRIS, "cursiva"))
    tapa = 12.0
    largo_tubo = largo + 2 * 10
    esc = min(1.0, 78.0 / (largo_tubo + 2 * tapa))
    x0, yc = 114.0, 114.0
    r = forma / 2 * esc
    lt = largo_tubo * esc
    hoja.anadir(Rect(x0 + tapa * esc, yc - r, lt, 2 * r, PVC, 0.4, None))
    hoja.anadir(Rect(x0, yc - r - 2, tapa * esc, 2 * r + 4, PVC, 0.3, "#d8ddd9"))
    hoja.anadir(Rect(x0 + (tapa + largo_tubo) * esc, yc - r - 2, tapa * esc, 2 * r + 4, PVC, 0.3, "#d8ddd9"))
    xb = x0 + (tapa + 10) * esc
    paso = largo / max(n, 1) * esc
    for k in range(n):
        x = xb + k * paso
        hoja.anadir(Linea(x, yc - r - 0.6, x + paso * 0.5, yc + r + 0.6, COBRE, 0.35))
    xe = xb + largo * esc
    hoja.anadir(Linea(x0 - 8, yc, xb, yc, COBRE, 0.35))
    hoja.anadir(Linea(xb, yc, xb, yc - r, COBRE, 0.35))             # el hilo entra por la tapa y se une a la primera espira
    hoja.anadir(Linea(xe, yc, xe + (10 + tapa) * esc + 8, yc, COBRE, 0.35))
    hoja.anadir(Linea(xe, yc, xe, yc + r, COBRE, 0.35))
    hoja.anadir(Rect((xb + xe) / 2 - 3, yc - 2, 6, 4, ROJO, 0.3, "#f3d7a8"))   # el condensador, dentro
    hoja.anadir(Linea(xb, yc, (xb + xe) / 2 - 3, yc, GRIS, 0.2, (1, 0.8)))
    hoja.anadir(Linea((xb + xe) / 2 + 3, yc, xe, yc, GRIS, 0.2, (1, 0.8)))
    hoja.anadir(Texto((xb + xe) / 2, yc + 6, "C", 6.0, ROJO, "negrita", "centro"))
    hoja.anadir(Cota(xb, yc + r + 7, xe, yc + r + 7, tr("{0} mm", fmt(largo, 0)), 6.0, ref1=(xb, yc + r), ref2=(xe, yc + r)))
    hoja.anadir(Cota(x0 + tapa * esc + lt + 6, yc - r, x0 + tapa * esc + lt + 6, yc + r, tr("Ø {0}", fmt(forma, 0)), 6.0))
    hoja.anadir(Texto(104, 148, tr("Tubo de PVC de Ø {0} mm, tapas pegadas con un agujero por donde sale el hilo ({1}).", fmt(forma, 0),
                                   tr("1:1") if esc >= 0.999 else tr("reducido")), 5.8, GRIS, "cursiva"))
