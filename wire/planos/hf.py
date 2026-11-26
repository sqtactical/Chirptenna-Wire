"""Hojas de la EFHW de HF: la antena (vista, lista de corte y ROE por banda), el transformador y su ajuste.

El transformador no está en la simulación (se usa uno ideal): la hoja 2 dice cómo montarlo y la 3 cómo ajustarlo con un
NanoVNA y una carga de prueba. Las vueltas, los núcleos y los condensadores son los **habituales en los montajes de
aficionados**, sin verificar aquí: hay que ajustarlos con el VNA.
"""

from __future__ import annotations

import math

from ..diseno import Diseno
from ..i18n import N_, tr
from .comun import fmt, frecuencia, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import BLANCO, COBRE, CUBIERTA, GRIS, PVC, ROJO, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Rect, Texto

# Núcleos de ferrita de mezcla 43 (diámetro exterior, interior y alto en mm; de las hojas de datos de Fair-Rite de memoria: orientativos).
NUCLEOS = {"FT140-43": (35.5, 23.0, 12.7), "FT240-43": (61.0, 35.5, 12.7)}


SUELO_NOMBRE = {"pobre": N_("pobre"), "normal": N_("normal"), "bueno": N_("bueno"), "mar": N_("de mar")}


def transformador(relacion: int, potencia_w: float) -> dict:
    """Datos de montaje del transformador de `relacion`:1 para `potencia_w` (vueltas de aficionado, sin verificar)."""
    nucleo = "FT140-43" if potencia_w <= 100 else "FT240-43"
    if relacion == 49:
        d = {"tipo": "transformador", "primario": 2, "secundario": 14, "condensador": "100 pF (50–150 pF)"}
    elif relacion == 64:
        nucleo = "FT240-43"
        d = {"tipo": "transformador", "primario": 2, "secundario": 16, "condensador": "68 pF (47–100 pF)"}
    elif relacion == 9:
        d = {"tipo": "autotransformador", "total": 9, "toma": 3, "condensador": None}
    else:
        raise ValueError(f"relación sin datos de montaje: {relacion}:1")
    d.update(nucleo=nucleo, dims=NUCLEOS[nucleo], relacion=relacion, carga=50.0 * relacion,
             tension_rms=math.sqrt(potencia_w * 50.0 * relacion))
    d["carga_texto"] = {49: "2,4 kΩ (dos de 1,2 kΩ en serie)", 64: "3,3 kΩ (3,3 kΩ, o 3,0 kΩ + 200 Ω)", 9: "470 Ω"}[relacion]
    return d


def _titulo(diseno: Diseno) -> str:
    g = diseno.geometria
    return tr("EFHW {0}:1 · {1} MHz ({2})", int(g["relacion"]), frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


def _m(mm: float, diseno: Diseno) -> str:
    """Largo en metros (o en pies con las unidades en pulgadas): en HF los milímetros no se leen."""
    if diseno.plano.unidades == "pulgadas":
        return f"{fmt(mm / 304.8, 1)} ft"
    return f"{fmt(mm / 1000, 2)} m"


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    return [_hoja_antena(diseno), _hoja_transformador(diseno), _hoja_ajuste(diseno)]


# ---------------------------------------------------------------- hoja 1: la antena

def _hoja_antena(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    largo, cp, alto, rel = g["largo_mm"], g["contrapeso_mm"], g["altura_mm"], int(g["relacion"])
    suelo = g["suelo"]
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, _titulo(diseno),
                   tr("Hilo de {0} alimentado por un extremo con un transformador {1}:1, a {2} sobre suelo {3}", _m(largo, diseno),
                      str(rel), _m(alto, diseno), tr(SUELO_NOMBRE[suelo])))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista lateral, sin escala"))
    x0, x1, yb, ya = 46.0, 182.0, 82.0, 52.0                      # mástil izquierdo, extremo, suelo y altura del hilo
    hoja.anadir(Linea(20, yb, 196, yb, GRIS, 0.6), Texto(196, yb + 4, tr("suelo"), 5.4, GRIS, ancla="derecha"),
                Linea(x0, yb, x0, ya - 6, GRIS, 0.8), Linea(x1, yb, x1, ya - 6, GRIS, 0.8),
                Linea(x0, ya, x1, ya, COBRE, 1.0),                                        # el hilo
                Linea(x0, ya, x0 - 14, ya, COBRE, 0.8),                                   # contrapeso
                Rect(x0 - 5, ya + 1, 10, 7, TINTA, 0.3, PVC),                              # caja del transformador
                Linea(x0, ya + 8, x0, yb - 6, GRIS, 0.5, (1.2, 0.8)),                      # coaxial
                Cota(x1 - 14, ya, x1 - 14, yb, _m(alto, diseno), tam=5.2),
                Cota(x0, ya - 10, x1, ya - 10, tr("hilo {0}", _m(largo, diseno)), tam=5.6, ref1=(x0, ya - 4), ref2=(x1, ya - 4)),
                Texto(x0 - 7, ya + 6, tr("contrapeso {0}", _m(cp, diseno)), 5.2, ancla="derecha"),
                Texto(x0 + 4, ya + 12, tr("transformador {0}:1", str(rel)), 5.4),
                Texto(x0 + 4, yb - 8, tr("coaxial de 50 Ω con choke"), 5.4, GRIS),
                Texto(x1 - 2, ya - 3, tr("aislador y cuerda"), 5.2, GRIS, ancla="derecha"))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante; el hilo sobrante se recorta en el aislador del extremo"), VERDE)
    sob = diseno.sobrante_mm
    filas = [
        [tr("Hilo, Ø {0} mm", fmt(d, 1)), "1", _m(largo, diseno), _m(largo + sob, diseno)],
        [tr("Contrapeso, Ø {0} mm", fmt(d, 1)), "1", _m(cp, diseno), _m(cp + sob, diseno)],
        [tr("Aisladores de extremo y cuerda"), "2", "—", "—"],
        [tr("Transformador {0}:1 con caja", str(rel)), "1", tr("hojas 2 y 3"), "—"],
        [tr("Coaxial 50 Ω con choke 1:1 (ferritas)"), "1", tr("a medida"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 62, 74, 98], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 124)
    if r and r.get("bandas"):
        seccion(hoja, 14, 148, tr("SIMULADO (NEC2) · SIN MEDIR"),
                tr("Suelo {0}, transformador ideal: la ROE es contra {1} Ω", tr(SUELO_NOMBRE[suelo]), fmt(r["z0_ohm"], 0)), VERDE)
        filas = [[b["banda"], fmt(b["f_MHz"], 2), fmt(b["roe"], 2), fmt(b["roe_max"], 2), f"{fmt(b['r_ohm'], 0)} {'+' if b['x_ohm'] >= 0 else '−'} j{fmt(abs(b['x_ohm']), 0)}",
                  fmt(b["ganancia_dBi"], 1)] for b in r["bandas"]]
        y = tabla(hoja, 14, 160, [0, 24, 52, 80, 108, 148], [tr("Banda"), tr("f (MHz)"), tr("ROE centro"), tr("ROE máx."), tr("Z en el hilo (Ω)"), tr("dBi")],
                  filas, 180)
        aviso = []
        malas = [b["banda"] for b in r["bandas"] if b["roe"] > 2.0]
        if malas:
            aviso.append(tr("ROE > 2 en {0}: con ese transformador ideal esas bandas necesitarían un acoplador.", ", ".join(malas)))
        if rel == 9:
            aviso.append(tr("El 9:1 con un hilo no resonante no se adapta bien en todas las bandas: se usa con acoplador."))
        aviso.append(tr("La ganancia es la máxima del diagrama (no hacia el horizonte); el suelo cambia la impedancia y el diagrama."))
        aviso.append(tr("En el extremo del hilo hay unos {0} V eficaces con {1} W: aíslalo y que nadie lo toque.",
                        fmt(transformador(rel, g.get("potencia_w", 100.0))["tension_rms"], 0), fmt(g.get("potencia_w", 100.0), 0)))
        hoja.anadir(Texto(14, y + 6, "\n".join(aviso), 6.0, VERDE))
    else:
        seccion(hoja, 14, 148, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(14, 160, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
    regla(hoja, 14, 244)
    return hoja


# ---------------------------------------------------------------- hoja 2: el transformador

def _hoja_transformador(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    t = transformador(int(g["relacion"]), g.get("potencia_w", 100.0))
    od, idi, alto = t["dims"]
    hoja = hoja_a4(diseno, tr("Transformador {0}:1 · montaje", str(t["relacion"])),
                   tr("Núcleo {0} · {1}", t["nucleo"], tr("autotransformador (unun)") if t["tipo"] == "autotransformador" else tr("transformador de dos devanados")))
    seccion(hoja, 14, 33, tr("MATERIAL"), tr("Valores habituales de montajes de aficionado, sin verificar: se ajustan con el VNA (hoja 3)"), VERDE)
    if t["tipo"] == "transformador":
        vueltas = tr("{0} vueltas de primario (lado coaxial) y {1} de secundario (lado del hilo)", str(t["primario"]), str(t["secundario"]))
    else:
        vueltas = tr("{0} vueltas en total, con la toma a {1} vueltas del extremo de masa", str(t["total"]), str(t["toma"]))
    filas = [
        [tr("Núcleo de ferrita mezcla 43"), t["nucleo"], tr("{0} × {1} × {2} mm", fmt(od, 1), fmt(idi, 1), fmt(alto, 1))],
        [tr("Vueltas"), vueltas, ""],
        [tr("Hilo de cobre"), tr("Ø 1,0–1,3 mm, esmaltado o con funda de PTFE (≥ 600 V)"), ""],
        [tr("Condensador de compensación"), t["condensador"] or tr("ninguno"), tr("mica o C0G, ≥ 1 kV, en paralelo con el secundario") if t["condensador"] else ""],
        [tr("Caja y conectores"), tr("estanca, SO-239 de entrada, borne o tornillo M5 y masa"), ""],
    ]
    tabla(hoja, 14, 46, [0, 48, 128], [tr("Pieza"), tr("Valor"), tr("Nota")], filas, 180)
    seccion(hoja, 14, 92, tr("VUELTAS EN EL NÚCLEO"), tr("Escala 1:1 · el núcleo visto desde arriba; cada trazo es una vuelta que pasa por el agujero"), VERDE)
    cx, cy = 62.0, 106.0 + od / 2
    hoja.anadir(Circulo(cx, cy, od / 2, TINTA, 0.3, None, etiqueta="plantilla:nucleo_exterior"),
                Circulo(cx, cy, idi / 2, TINTA, 0.3, None, etiqueta="plantilla:nucleo_interior"),
                Cota(cx - od / 2, cy + od / 2 + 7, cx + od / 2, cy + od / 2 + 7, tr("Ø {0} mm", fmt(od, 1)), tam=5.4,
                     ref1=(cx - od / 2, cy + od / 2), ref2=(cx + od / 2, cy + od / 2)))
    n1, n2 = (t["primario"], t["secundario"]) if t["tipo"] == "transformador" else (t["toma"], t["total"] - t["toma"])
    total = n1 + n2
    for k in range(total):
        a = math.radians(90 + 360.0 * (k + 0.5) / (total + 1))
        color = ROJO if k < n1 else COBRE
        hoja.anadir(Linea(cx + idi / 2 * math.cos(a), cy - idi / 2 * math.sin(a), cx + od / 2 * math.cos(a), cy - od / 2 * math.sin(a), color, 0.9,
                          None, "plantilla:vuelta"))
    hoja.anadir(Texto(cx + od / 2 + 8, cy - 14, tr("rojo: {0} vueltas ({1})", str(n1), tr("primario") if t["tipo"] == "transformador" else tr("de masa a la toma")), 5.8, ROJO),
                Texto(cx + od / 2 + 8, cy - 7, tr("cobre: {0} vueltas ({1})", str(n2), tr("secundario") if t["tipo"] == "transformador" else tr("de la toma al hilo")), 5.8),
                Texto(cx + od / 2 + 8, cy + 2, tr("Reparte las vueltas por todo el anillo, sin\nsolaparlas, y deja las dos puntas del primario juntas."), 5.6, GRIS))
    y = cy + od / 2 + 16
    seccion(hoja, 14, y, tr("MONTAJE"), tr("En este orden"), VERDE)
    pasos = [tr("1. Enrolla el secundario (o la parte alta del autotransformador) con las vueltas repartidas y apretadas."),
             tr("2. Enrolla el primario sobre el mismo anillo, del lado del coaxial: vivo a la entrada y malla a masa."),
             tr("3. Suelda el condensador entre el extremo caliente (hacia el hilo) y masa, con patillas cortas."),
             tr("4. Mide con el VNA y una carga de prueba antes de cerrar la caja (hoja 3)."),
             tr("5. Caja estanca, el hilo sale por un prensaestopas con bucle de goteo y el coaxial lleva un choke 1:1.")]
    hoja.anadir(Texto(14, y + 12, "\n".join(pasos), 6.3))
    hoja.anadir(Texto(14, y + 44, tr("Con {0} W hay unos {1} V eficaces en el hilo: usa hilo y soldaduras aislados y no lo toques en emisión.",
                                     fmt(g.get("potencia_w", 100.0), 0), fmt(t["tension_rms"], 0)), 6.0, ROJO))
    hoja.anadir(Texto(14, y + 54, tr("Núcleo para {0} W en SSB; con más potencia o modos continuos (FT8, RTTY) usa un núcleo mayor o dos apilados.",
                                     fmt(g.get("potencia_w", 100.0), 0)), 6.0, GRIS))
    regla(hoja, 14, 244)
    return hoja


# ---------------------------------------------------------------- hoja 3: ajuste

def _hoja_ajuste(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    t = transformador(int(g["relacion"]), g.get("potencia_w", 100.0))
    hoja = hoja_a4(diseno, tr("Transformador {0}:1 · ajuste con el NanoVNA", str(t["relacion"])),
                   tr("Con una carga de prueba de {0} Ω en lugar de la antena", fmt(t["carga"], 0)))
    seccion(hoja, 14, 33, tr("PROCEDIMIENTO"), tr("Sin la antena conectada"), VERDE)
    pasos = [
        tr("1. Carga de prueba: {0}, con resistencias sin inductancia (película de carbón o metal) y patillas lo más cortas posible,", t["carga_texto"]),
        tr("    entre el extremo caliente (donde irá el hilo) y masa."),
        tr("2. Calibra el NanoVNA (abierto, corto y carga) en el conector de entrada del transformador, de 1,8 a 30 MHz."),
        tr("3. Mide S11 y mira la ROE en cada banda que vayas a usar: lo bueno es por debajo de 1,5; hasta 2 sirve."),
        tr("4. Si la ROE no es buena, retoca según la tabla de abajo, de uno en uno, y repite la medida."),
        tr("5. Con la antena puesta, mide otra vez en tus bandas: la ROE real será distinta de la de la carga de prueba,"),
        tr("    porque la antena no es una resistencia pura; compárala con la tabla de la hoja 1 (transformador ideal)."),
        tr("6. Prueba térmica: transmite 1–2 min con la potencia y el modo que vayas a usar y toca el núcleo: tibio vale;"),
        tr("    caliente quiere un núcleo mayor, más vueltas o menos potencia."),
    ]
    hoja.anadir(Texto(14, 45, "\n".join(pasos), 6.3))
    seccion(hoja, 14, 112, tr("QUÉ RETOCAR"), tr("Reglas prácticas, sin verificar con tus medidas: cambia una cosa cada vez"), VERDE)
    filas = [
        [tr("ROE alta en las bandas altas"), tr("Capacidad parásita"), tr("Baja o quita el condensador, patillas cortas, separa los devanados")],
        [tr("ROE alta en las bandas bajas"), tr("Poca inductancia"), tr("Más vueltas con la misma relación (3:21 y no 2:14) o núcleo mayor")],
        [tr("Una sola banda mal"), tr("Resonancia del devanado"), tr("Cambia el condensador 22–33 pF o separa algo las vueltas")],
        [tr("Bien con la carga y mal con la antena"), tr("Es la antena"), tr("Retoca el largo del hilo y el contrapeso (hoja 1)")],
    ]
    tabla(hoja, 14, 124, [0, 62, 98], [tr("Síntoma"), tr("Causa probable"), tr("Qué hacer")], filas, 180)
    seccion(hoja, 14, 180, tr("MÁS ADELANTE"), tr("Un asistente de Chirptenna VNA hará esta medida paso a paso"), VERDE)
    hoja.anadir(Texto(14, 192, tr("Todavía no existe: hoy la medida es manual, con el NanoVNA y la carga de prueba. Los valores de esta hoja\n"
                                  "(vueltas, condensador y reglas) salen de montajes de aficionados y no están comprobados aquí."), 6.2, GRIS))
    regla(hoja, 14, 244)
    return hoja
