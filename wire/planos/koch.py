"""Hojas de la J-pole de Koch: resumen (sin escala) y plantilla del alambre a 1:1 (una hoja, A3 o mosaico de A4)."""

from __future__ import annotations

import math

from .. import geometria
from ..diseno import Diseno
from ..i18n import tr
from .comun import envolver, fmt, frecuencia, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import BLANCO, COBRE, CUBIERTA, GRIS, ROJO, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Polilinea, Rect, Texto
from .jpole import _simulacion
from .paginacion import RELLENO_PLANTILLA, hojas_plantilla, mapa_montaje


def _titulo(diseno: Diseno) -> str:
    return tr("J-pole de Koch · {0} MHz ({1})", frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


def curva(diseno: Diseno) -> list[tuple[float, float]]:
    """La curva de Koch del radiador (mm): x hacia fuera es negativo; z hacia arriba, desde la altura del brazo corto."""
    g = diseno.geometria
    return geometria.koch_hacia_fuera(int(g["iteracion"]), (0.0, g["corto_mm"]), (0.0, g["corto_mm"] + g["altura_koch_mm"]))


def medidas(diseno: Diseno) -> dict:
    g = diseno.geometria
    pts = curva(diseno)
    largo_curva = geometria.longitud(pts)
    return {"curva": pts, "largo_curva": largo_curva, "corto": g["corto_mm"], "toma": g["toma_mm"],
            "s": g["separacion_mm"], "altura": g["altura_koch_mm"], "iteracion": int(g["iteracion"]),
            "total": 2 * g["corto_mm"] + g["separacion_mm"] + largo_curva, "dobleces": len(pts) - 2}


def plantilla(diseno: Diseno) -> tuple[list, float, float]:
    """Primitivas de la plantilla a 1:1 (mm, y hacia abajo, con aire alrededor) y su tamaño."""
    m = medidas(diseno)
    d = diseno.diametro_mm
    xs = [x for x, _ in m["curva"]] + [0.0, m["s"]]
    x_min, x_max = min(xs), max(xs)
    z_max = m["corto"] + m["altura"]
    pad = RELLENO_PLANTILLA + 10.0
    X = lambda x: pad + (x - x_min)  # noqa: E731
    Y = lambda z: pad + (z_max - z)  # noqa: E731
    ancho = X(x_max) + pad + 50.0           # sitio a la derecha para las notas de la toma
    alto = Y(0.0) + pad
    largo = [(X(0.0), Y(0.0)), (X(0.0), Y(m["corto"]))] + [(X(x), Y(z)) for x, z in m["curva"][1:]]
    prims: list = [
        Polilinea(tuple(largo), COBRE, d, etiqueta="plantilla:brazo_largo"),
        Polilinea(((X(m["s"]), Y(0.0)), (X(m["s"]), Y(m["corto"]))), COBRE, d, etiqueta="plantilla:brazo_corto"),
        Polilinea(((X(0.0), Y(0.0)), (X(m["s"]), Y(0.0))), COBRE, d, etiqueta="plantilla:fondo_u"),
    ]
    for p in largo[1:-1] + [(X(0.0), Y(0.0)), (X(m["s"]), Y(0.0)), (X(m["s"]), Y(m["corto"])), largo[-1]]:
        prims.append(Circulo(p[0], p[1], d / 2, None, 0.1, COBRE))          # codos redondeados
    xt, yt = X(m["s"]) + 6, Y(m["toma"])
    prims += [
        Linea(X(0.0) - 6, Y(m["toma"]), X(m["s"]) + 6, Y(m["toma"]), VERDE, 0.3, (1.2, 0.6), "plantilla:toma"),
        Texto(xt + 2, yt + 1.2, tr("toma {0} · vivo al largo, malla al corto", longitud(m["toma"], diseno)), 5.4, VERDE),
        Texto(X(m["s"]) + 4, Y(m["corto"] / 2), tr("adaptador λ/4"), 5.6, GRIS),
    ]
    for n, (x, z) in enumerate(m["curva"][1:-1], start=1):                   # los dobleces, numerados
        prims.append(Circulo(X(x), Y(z), 1.7, TINTA, 0.12))
        prims.append(Texto(X(x) + 3.2, Y(z) - 1.6, str(n), 5.0, TINTA))
    return prims, ancho, alto


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    prims, ancho, alto = plantilla(diseno)
    plantillas, decision = hojas_plantilla(diseno, _titulo(diseno), tr("Plantilla del alambre a 1:1: pon el alambre encima"),
                                           prims, ancho, alto)
    return [_resumen(diseno, decision, prims, ancho, alto, len(plantillas))] + plantillas


def _resumen(diseno: Diseno, decision: dict, prims: list, ancho: float, alto: float, n_plantillas: int) -> Hoja:
    m = medidas(diseno)
    d = diseno.diametro_mm
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo(diseno), tr("Una pieza de alambre o varilla de Ø {0} mm doblada en U con el radiador en curva de Koch · "
                                              "alimentada con coaxial de 50 Ω", fmt(d, 1)))

    # 1. Vista general (tumbada: la U a la izquierda, la punta a la derecha), sin escala
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0} al eje del alambre", u))
    pts = m["curva"]
    ancho_x = max(abs(x) for x, _ in pts) + m["s"]
    alto_total = m["corto"] + m["altura"]
    esc = min(150.0 / alto_total, 20.0 / max(ancho_x, 1e-6))
    x0, yc = 30.0, 66.0

    def P(x, z):
        return x0 + z * esc, yc + x * esc            # x hacia fuera (negativo) queda arriba

    hoja.anadir(Polilinea(tuple([P(0, 0), P(0, m["corto"])] + [P(x, z) for x, z in pts[1:]]), COBRE, 0.85),
                Polilinea((P(m["s"], 0), P(m["s"], m["corto"])), COBRE, 0.85),
                Polilinea((P(0, 0), P(m["s"], 0)), COBRE, 0.85))
    xe = x0 + alto_total * esc
    hoja.anadir(
        Cota(x0, yc + m["s"] * esc + 12, x0 + m["corto"] * esc, yc + m["s"] * esc + 12,
             tr("brazo corto (λ/4) {0}", longitud(m["corto"], diseno)), tam=5.6),
        Cota(x0 + m["corto"] * esc, 40, xe, 40, tr("curva de Koch · cuerda {0}", longitud(m["altura"], diseno)), tam=5.6),
        Texto(x0 + m["toma"] * esc, yc + m["s"] * esc + 5, tr("toma {0}", longitud(m["toma"], diseno)), 5.6, ancla="centro"),
        Texto(xe + 2, yc - 3, tr("curva de {0} dobleces · largo {1}", m["dobleces"], longitud(m["largo_curva"], diseno)), 5.6, ancla="izquierda")
        if xe + 2 + 38 < 196 else Texto(xe, yc + 14, tr("curva de {0} dobleces · largo {1}", m["dobleces"], longitud(m["largo_curva"], diseno)), 5.6, ancla="derecha"),
    )

    # 2. Lista de corte
    seccion(hoja, 14, 101, tr("LISTA DE CORTE"), tr("Corta con el sobrante (queda en la punta del radiador)"), VERDE)
    filas = [
        [tr("Alambre Ø {0} mm, una pieza", fmt(d, 1)), "1", f"{longitud(m['total'], diseno)} {u}",
         f"{longitud(m['total'] + diseno.sobrante_mm, diseno, 0)} {u}"],
        [tr("Espaciador aislante, {0} {1} entre ejes", longitud(m["s"], diseno, 0), u), "2", "—", "—"],
        [tr("Coaxial RG-58, bajada + choke"), "1", tr("a medida"), "—"],
        [tr("Abrazaderas aisladas para el mástil"), "2", "—", "—"],
    ]
    y = tabla(hoja, 14, 113, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, y + 1, tr("{0} dobleces de la curva (numerados en la plantilla) y 2 de 90° en la U.", m["dobleces"]), 6.0))
    r = diseno.resultados
    if r:
        sl = r["sensibilidad_MHz_por_mm"]
        hoja.anadir(Texto(14, y + 8, tr("Ajuste: acorta la cuerda de la curva; quitar 1 mm sube el mínimo\nde ROE ≈ {0} MHz.", fmt(sl, 3)), 6.0, VERDE))
    else:
        hoja.anadir(Texto(14, y + 8, tr("Ajuste: acorta la curva hasta que la ROE mínima\ncaiga en la frecuencia; luego mueve la toma."), 6.0, VERDE))
    _simulacion(hoja, diseno)

    # 3. Montaje y mapa
    hoja.anadir(Linea(10, 160, 200, 160, GRIS, 0.1))
    if decision["modo"] == "mosaico":
        columnas, filas_m = decision["hojas"]
        seccion(hoja, 14, 168, tr("MAPA DE MONTAJE"), tr("La plantilla ocupa {0} hojas: júntalas por las marcas y el solape", columnas * filas_m), VERDE)
        mapa_montaje(hoja, 16, 179, 70, 58, decision, ancho, alto, prims, diseno)
        x_texto = 100
    elif decision["modo"] == "sin_escala":
        seccion(hoja, 14, 168, tr("PLANTILLA"), tr("No cabe a escala en 12 hojas de A4: usa las cotas"), VERDE)
        x_texto = 14
    else:
        seccion(hoja, 14, 168, tr("PLANTILLA"), tr("Plantilla a 1:1 en la hoja 2 ({0})", decision["papel"]), VERDE)
        x_texto = 14
    pasos = (tr("1. Comprueba la escala con la regla de abajo."),
             tr("2. Pon el alambre sobre la plantilla y dobla en cada marca."),
             tr("3. Las muescas de la curva van hacia fuera, lejos del brazo corto."),
             tr("4. Marca la toma y suelda el coaxial: vivo al largo, malla al corto."),
             tr("5. Mide con el NanoVNA y acorta la curva en pasos de 2–3 mm."))
    hoja.anadir(Texto(x_texto, 186 if x_texto > 14 else 180, "\n".join(envolver(p, 196 - x_texto, 6.0) for p in pasos), 6.0))
    regla(hoja, 14, 244)
    return hoja
