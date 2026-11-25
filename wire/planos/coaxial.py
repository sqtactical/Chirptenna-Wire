"""Hojas de las antenas de coaxial: dipolo de manga (1 hoja) y colineal CoCo (2 hojas).

Los tramos de cable van sin escala (con su longitud física y, entre paréntesis, la eléctrica: física / VF) y el
pelado y los cruces, a escala 1:1 con la etiqueta `plantilla:*`. Las cotas del pelado son orientativas.
"""

from __future__ import annotations

from ..diseno import Diseno, banda_de
from ..i18n import N_, tr
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .patron import patron_manga, patrones_coco
from .hoja import (BLANCO, COBRE, CUBIERTA, DIELECTRICO, GRIS, PVC, TINTA, VERDE, Circulo, Cota, Hoja, Linea,
                   Polilinea, Rect, Texto, rayado)

ORIGENES_VF = (N_("catálogo"), N_("medido"))  # para el extractor de idiomas
VIVO_MM = 0.9  # diámetro del vivo del RG-58 (orientativo; los demás cables lo dan parecido)


def _vf(diseno: Diseno) -> str:
    c = diseno.cable
    return tr("VF {0} ({1})", fmt(c['vf'], 2), tr(c['vf_origen']))


def _aviso_vf(hoja: Hoja, diseno: Diseno, x: float, y: float) -> None:
    c = diseno.cable
    if c["vf_origen"] != "medido":
        hoja.anadir(Texto(x, y, tr("Ojo: el VF {0} es de catálogo; el del cable de verdad puede cambiar\nunos puntos. Mídelo (latiguillo abierto, NanoVNA) y vuelve a generar el plano.", fmt(c['vf'], 2)),
                          5.6, GRIS))


# ---------------------------------------------------------------- dipolo de manga


def hojas_manga(diseno: Diseno, fecha: str) -> list[Hoja]:
    g, c = diseno.geometria, diseno.cable
    rad, man = g["radiador_mm"], g["manga_mm"]
    u = unidad(diseno)
    od = diseno.diametro_mm
    r = diseno.resultados
    hoja = hoja_a4(diseno, tr("Dipolo de manga de coaxial · {0} MHz ({1})", frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz)),
                   tr("Coaxial {0} · {1} · radiador: el vivo; manga: la malla doblada hacia atrás", c['nombre'], _vf(diseno)))

    # 1. Vista general, sin escala
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0}", u))
    yv, xj, px_m = 62.0, 108.0, 72.0
    px_r = min(px_m * rad / man, 80.0)
    xs = xj - px_m
    hoja.anadir(
        Linea(22, yv, xj, yv, CUBIERTA, 0.56),
        Rect(xs, yv - 3.2, px_m, 6.4, TINTA, 0.18, PVC),
        Linea(xj, yv, xj + px_r, yv, COBRE, 0.85),
        Cota(xs, yv - 10, xj, yv - 10, tr("manga {0}", longitud(man, diseno))),
        Cota(xj, yv - 10, xj + px_r, yv - 10, tr("radiador {0}", longitud(rad, diseno))),
        Texto(xj, yv + 7.5, tr("malla unida al cable en este punto"), 5.8, ancla="centro", fondo=BLANCO),
        Texto(22, yv + 5.5, tr("al equipo\n(con choke)"), 5.8),
        Texto(xs + 2, yv - 4.5, tr("manga (malla doblada)"), 5.6),
    )

    # 2. Lista de corte
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Medidas desde el extremo del cable; sobrante para ajustar"), VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        [tr("Radiador: vivo con su dieléctrico"), "1", f"{longitud(rad, diseno)} {u}", f"{longitud(rad + sobrante, diseno, 0)} {u}"],
        [tr("Manga: malla doblada hacia atrás"), "1", f"{longitud(man, diseno)} {u}", "—"],
        [tr("Coaxial {0}, bajada", c['nombre']), "1", tr("a medida"), "—"],
        [tr("Termorretráctil Ø {0} mm", fmt(od + 6, 0)), "1", f"{longitud(man + 10, diseno, 0)} {u}", "—"],
        [tr("Estaño y vaina de silicona"), "1", "—", "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 136, tr("Ajuste: recorta el vivo (el radiador) poco a poco; la manga no se toca."), 6.2, VERDE))
    _simulacion(hoja, diseno, "manga")

    # 3. Detalle del pelado a escala 1:1
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("DETALLE DEL PELADO"), tr("Escala 1:1 · solo el extremo del cable; la manga y el vivo siguen más largos"), VERDE)
    dd = _diam(c, "diametro_dielectrico_mm", 0.45 * od)
    mm = _diam(c, "diametro_malla_mm", 0.8 * od)
    yd, xf = 186.0, 112.0
    hoja.anadir(
        Rect(18, yd - od / 2, 50, od, None, relleno=CUBIERTA, etiqueta="plantilla:cubierta"),
        Rect(xf - 44, yd - od / 2 - 1.0, 44, od + 2.0, COBRE, 0.3, None, etiqueta="plantilla:manga"),
        Rect(xf, yd - dd / 2, 40, dd, TINTA, 0.1, DIELECTRICO, etiqueta="plantilla:dielectrico"),
        Rect(xf, yd - VIVO_MM / 2, 76, VIVO_MM, None, relleno=COBRE, etiqueta="plantilla:vivo"),
    )
    hoja.anadir(*rayado(xf - 44, yd - od / 2 - 1.0, 44, od + 2.0, 1.2, TINTA, 0.1))
    hoja.anadir(
        Linea(xf, yd - od / 2 - 4, xf, yd + od / 2 + 5, GRIS, 0.12, (1.2, 0.8)),
        Texto(xf, yd + od / 2 + 8, tr("aquí: la malla se dobla hacia atrás y se suelda al cable"), 5.6, ancla="centro"),
        Cota(18, yd + od / 2 + 14, 68, yd + od / 2 + 14, tr("cubierta (sigue)")),
        Texto(xf - 44, yd - od / 2 - 5, tr("manga: malla doblada, {0} {1} en total (sigue ←)", longitud(man, diseno, 0), u), 5.6),
        Texto(xf + 41, yd - dd / 2 - 3.5, tr("dieléctrico"), 5.6),
        Texto(xf + 41, yd + 4.2, tr("vivo hasta {0} {1} (sigue →)", longitud(rad, diseno, 0), u), 5.6),
    )
    hoja.anadir(Texto(14, 216, tr("Pelado orientativo: quita la cubierta en la longitud de la manga, desenreda la malla, dóblala sobre la\ncubierta y suéldala al cable donde empieza el dieléctrico. Cubre todo con termorretráctil."), 5.8))
    _aviso_vf(hoja, diseno, 14, 226)
    patron = patron_manga(diseno)
    hoja.anadir(Texto(14, 235, tr("Patrón del coaxial a 1:1 desde la hoja {0}: pon el cable encima para marcar.", 2) if patron
                      else tr("El patrón del coaxial no cabe a escala: usa las cotas."), 6.0, VERDE))
    regla(hoja, 14, 244)
    return [hoja] + patron


def _diam(c: dict, clave: str, defecto: float) -> float:
    from ..cables import cable
    try:
        return getattr(cable(c["nombre"]), clave)
    except ValueError:
        return defecto


# ---------------------------------------------------------------- colineal CoCo


def hojas_coco(diseno: Diseno, fecha: str) -> list[Hoja]:
    patrones = patrones_coco(diseno)
    resumen = _coco_resumen(diseno)
    resumen.anadir(Texto(14, 214, tr("Patrón del coaxial a 1:1 (tramo y punta) desde la hoja {0}: pon el cable encima para marcar.", 3)
                         if patrones else tr("El patrón del coaxial no cabe a escala: usa las cotas."), 6.0, VERDE))
    return [resumen, _coco_detalle(diseno)] + patrones


def _titulo_coco(diseno: Diseno) -> str:
    n = int(diseno.geometria["tramos"])
    return tr("Colineal CoCo de {0} tramos · {1} MHz ({2})", n, frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz))


def _coco_resumen(diseno: Diseno) -> Hoja:
    g, c = diseno.geometria, diseno.cable
    n = int(g["tramos"])
    tramo, punta = g["tramo_mm"], g["punta_mm"]
    electrico = tramo / c["vf"]
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo_coco(diseno),
                   tr("Coaxial {0} · {1} · tramos de λ/2 eléctrico con el vivo y la malla cruzados", c['nombre'], _vf(diseno)))

    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Sin escala · medidas en {0}", u))
    y, x0 = 66.0, 24.0
    px = min(18.0, 150.0 / n)
    x = x0
    hoja.anadir(Linea(x0 - 8, y, x0, y, CUBIERTA, 0.56), Texto(x0 - 8, y + 6, tr("al equipo (con choke)"), 5.6))
    for k in range(n):
        hoja.anadir(Rect(x, y - 2.2, px - 1.6, 4.4, TINTA, 0.18, CUBIERTA if k % 2 == 0 else "#4b5057"))
        hoja.anadir(Circulo(x + px - 0.8, y, 0.9, COBRE, 0.3, BLANCO))
        if k == 0:
            hoja.anadir(Cota(x, y - 8, x + px - 1.6, y - 8, f"{longitud(tramo, diseno, 0)}", tam=5.6))
        x += px
    hoja.anadir(Linea(x - 0.8, y, x + 12, y, COBRE, 0.85),
                Cota(x - 0.8, y - 8, x + 12, y - 8, tr("punta {0}", longitud(punta, diseno, 0)), tam=5.6),
                Texto(x0 - 8, y + 14, tr("{0} tramos iguales: {1} {2} de cable\n({3} {2} eléctricos = λ/2)", n, longitud(tramo, diseno), u, longitud(electrico, diseno)), 5.8))

    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Cada tramo se corta con sobrante para los pelados"), VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        [tr("Tramo de coaxial {0}", c['nombre']), str(n), f"{longitud(tramo, diseno)} {u}", f"{longitud(tramo + sobrante, diseno, 0)} {u}"],
        [tr("Punta: vivo con dieléctrico"), "1", f"{longitud(punta, diseno)} {u}", f"{longitud(punta + sobrante, diseno, 0)} {u}"],
        [tr("Coaxial {0}, bajada", c['nombre']), "1", tr("a medida"), "—"],
        [tr("Termorretráctil (uniones)"), str(n + 1), tr("40 mm"), "—"],
        [tr("Tubo PVC de protección"), "1", tr("todo el largo"), "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 104)
    hoja.anadir(Texto(14, 136, tr("Choke bajo el primer tramo: 6–8 vueltas de coaxial sobre Ø 10 cm (orientativo)."), 6.0, VERDE))
    _simulacion(hoja, diseno, "coco")
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, tr("ORDEN DE MONTAJE"), tr("Los detalles de cada unión, a escala 1:1, en la hoja 2"), VERDE)
    pasos = (tr("1. Corta los tramos y la punta con el sobrante; mide el VF del cable si puedes."),
             tr("2. Pela cada extremo como en la hoja 2: malla a un lado, vivo al otro."),
             tr("3. Une los tramos cruzando: la malla de uno con el vivo del siguiente, y al revés."),
             tr("4. Aísla cada unión con termorretráctil y mete todo en el tubo."),
             tr("5. Mide la ROE con el NanoVNA y recorta la punta si hace falta."))
    for i, t in enumerate(pasos):
        hoja.anadir(Texto(14, 164 + i * 6, t, 6.0))
    _aviso_vf(hoja, diseno, 14, 198)
    regla(hoja, 14, 244)
    return hoja


def _coco_detalle(diseno: Diseno) -> Hoja:
    c = diseno.cable
    od = diseno.diametro_mm
    dd = _diam(c, "diametro_dielectrico_mm", 0.45 * od)
    u = unidad(diseno)
    hoja = hoja_a4(diseno, tr("CoCo · detalle de la unión · {0} MHz", frecuencia(diseno.f_MHz)),
                   tr("Escala 1:1 · coaxial {0} · cotas del pelado orientativas ({1})", c['nombre'], u))
    seccion(hoja, 14, 33, tr("UNIÓN ENTRE DOS TRAMOS"), tr("Escala 1:1 · la malla de cada tramo va con el vivo del otro"), VERDE)
    yd = 62.0
    xa, xb = 64.0, 146.0  # fin del tramo k y comienzo del k+1
    malla, dielectrico, vivo = 12.0, 6.0, 14.0
    # tramo k (a la izquierda) pelado hacia la derecha
    hoja.anadir(Rect(18, yd - od / 2, xa - 18, od, None, relleno=CUBIERTA, etiqueta="plantilla:tramo_k"),
                Rect(xa, yd - od * 0.4, malla, od * 0.8, None, relleno=COBRE, etiqueta="plantilla:malla_k"),
                Rect(xa + malla, yd - dd / 2, dielectrico, dd, TINTA, 0.1, DIELECTRICO),
                Rect(xa + malla + dielectrico, yd - VIVO_MM / 2, vivo, VIVO_MM, None, relleno=COBRE))
    hoja.anadir(*rayado(xa, yd - od * 0.4, malla, od * 0.8, 1.2, TINTA, 0.1))
    # tramo k+1 (a la derecha) pelado hacia la izquierda
    hoja.anadir(Rect(xb, yd - od / 2, 196 - xb, od, None, relleno=CUBIERTA, etiqueta="plantilla:tramo_k1"),
                Rect(xb - malla, yd - od * 0.4, malla, od * 0.8, None, relleno=COBRE, etiqueta="plantilla:malla_k1"),
                Rect(xb - malla - dielectrico, yd - dd / 2, dielectrico, dd, TINTA, 0.1, DIELECTRICO),
                Rect(xb - malla - dielectrico - vivo, yd - VIVO_MM / 2, vivo, VIVO_MM, None, relleno=COBRE))
    hoja.anadir(*rayado(xb - malla, yd - od * 0.4, malla, od * 0.8, 1.2, TINTA, 0.1))
    # cruces: vivo de k a la malla de k+1, malla de k al vivo de k+1
    x_vk = xa + malla + dielectrico + vivo               # punta del vivo de k
    x_vk1 = xb - malla - dielectrico - vivo              # punta del vivo de k+1
    arriba = yd - od * 0.4                               # borde de arriba de la malla
    hoja.anadir(Polilinea(((x_vk, yd), (x_vk + 4, yd - 9), (xb - malla / 2, yd - 9), (xb - malla / 2, arriba)),
                          ROJO_CRUCE, 0.5),
                Polilinea(((xa + malla / 2, arriba), (xa + malla / 2, yd - 14), (x_vk1 - 0.0, yd - 14), (x_vk1, yd)),
                          ROJO_CRUCE, 0.5))
    hoja.anadir(
        Cota(xa, yd + od / 2 + 3, xa + malla, yd + od / 2 + 3, longitud(malla, diseno, 0), tam=5.6),
        Cota(xa + malla, yd + od / 2 + 3, xa + malla + dielectrico, yd + od / 2 + 3, longitud(dielectrico, diseno, 0), tam=5.6),
        Cota(xa + malla + dielectrico, yd + od / 2 + 3, xa + malla + dielectrico + vivo, yd + od / 2 + 3, longitud(vivo, diseno, 0), tam=5.6),
        Texto(18, yd + 11, tr("tramo k (sigue ←)"), 5.8), Texto(196, yd + 11, tr("tramo k + 1 (sigue →)"), 5.8, ancla="derecha"),
        Texto(105, yd - 17, tr("cruce: vivo de k ↔ malla de k+1  ·  malla de k ↔ vivo de k+1"), 5.8, ancla="centro", fondo=BLANCO),
    )
    hoja.anadir(Texto(14, 85, tr("Suelda cada cruce con hilo corto; deja la unión lo más corta posible y cúbrela con termorretráctil."), 5.8))

    seccion(hoja, 14, 98, tr("PELADOS"), tr("Medidas en {0}", u), VERDE)
    filas = [
        [tr("Cubierta que se quita en cada extremo"), longitud(malla + dielectrico + vivo, diseno, 0)],
        [tr("Malla que se deja a la vista"), longitud(malla, diseno, 0)],
        [tr("Dieléctrico que se deja a la vista"), longitud(dielectrico, diseno, 0)],
        [tr("Vivo que sobresale"), longitud(vivo, diseno, 0)],
    ]
    tabla(hoja, 14, 110, [0, 95], [tr("Pelado"), u], filas, 104)

    hoja.anadir(Linea(10, 140, 200, 140, GRIS, 0.1))
    seccion(hoja, 14, 145, tr("PUNTA Y PROTECCIÓN"), tr("Extremo de arriba y cómo se protege"), VERDE)
    for k, t in enumerate((tr("Punta: deja solo el vivo con su dieléctrico (sin malla) en la longitud de la hoja 1 y tapa el extremo."),
                           tr("Protección: cada unión con termorretráctil con adhesivo; todo el conjunto dentro de un tubo de PVC"),
                           tr("(Ø interior ≈ 2 × el del cable) sellado arriba. Cuidado: el agua entra por el coaxial."))):
        hoja.anadir(Texto(14, 156 + k * 6, t, 5.8))
    _aviso_vf(hoja, diseno, 14, 180)
    regla(hoja, 14, 244)
    return hoja


ROJO_CRUCE = "#b04a3a"


def _simulacion(hoja: Hoja, diseno: Diseno, tipo: str) -> None:
    r = diseno.resultados
    if not r:
        seccion(hoja, 128, 91, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(128, 103, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
        return
    seccion(hoja, 128, 91, tr("SIMULADO (NEC2) · SIN MEDIR"), tr("Modelo del motor de Chirptenna Wire"))
    if tipo == "manga":
        hoja.anadir(Texto(128, 103, tr("Resonancia {0} MHz · R = {1} Ω\nGanancia {2} dBi", fmt(r['f_resonancia_MHz'], 1), fmt(r['r_resonancia_ohm'], 1), fmt(r['ganancia_dBi'], 2)), 6.3))
        banda = banda_de(diseno.f_MHz)
        grafica_roe(hoja, 138, 113, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], banda[1:] if banda else None)
        hoja.anadir(Texto(128, 156, tr("ROE mínima ≈ {0}. La manga es un modelo de banda\nestrecha: sin medir, el choke real puede ser peor.", fmt(min(r['barrido']['roe']), 2)), 5.6, GRIS))
        return
    red = r.get("red") or {}
    hoja.anadir(Texto(128, 103, tr("Z en el conector {0} {1} j{2} Ω\nGanancia {3} dBi\nROE sin red {4} · con red {5}\nROE ≤ 2: solo {6} MHz", fmt(r['r_ohm'], 0), '+' if r['x_ohm'] >= 0 else '−', fmt(abs(r['x_ohm']), 0), fmt(r['ganancia_dBi'], 2), fmt(r['roe_sin_red'], 1), fmt(r['roe_con_red'], 2), fmt(r['ancho_roe2_MHz'], 1)), 6.3))
    if red:
        serie = tr("{0} nH", fmt(red['l_serie_nH'], 0)) if "l_serie_nH" in red else tr("{0} pF", fmt(red['c_serie_pF'], 1))
        par = tr("{0} pF", fmt(red['c_paralelo_pF'], 1)) if "c_paralelo_pF" in red else tr("{0} nH", fmt(red['l_paralelo_nH'], 0))
        hoja.anadir(Texto(128, 128, tr("Red en L en el conector:\nen serie {0}, en paralelo {1}.\n(Banda muy estrecha: ajusta midiendo.)", serie, par), 6.0, VERDE))
