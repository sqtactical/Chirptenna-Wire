"""Hojas de las antenas de coaxial: dipolo de manga (1 hoja) y colineal CoCo (2 hojas).

Los tramos de cable van sin escala (con su longitud física y, entre paréntesis, la eléctrica: física / VF) y el
pelado y los cruces, a escala 1:1 con la etiqueta `plantilla:*`. Las cotas del pelado son orientativas.
"""

from __future__ import annotations

from ..diseno import Diseno, banda_de
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import (BLANCO, COBRE, CUBIERTA, DIELECTRICO, GRIS, PVC, TINTA, VERDE, Circulo, Cota, Hoja, Linea,
                   Polilinea, Rect, Texto, rayado)

VIVO_MM = 0.9  # diámetro del vivo del RG-58 (orientativo; los demás cables lo dan parecido)


def _vf(diseno: Diseno) -> str:
    c = diseno.cable
    return f"VF {fmt(c['vf'], 2)} ({c['vf_origen']})"


def _aviso_vf(hoja: Hoja, diseno: Diseno, x: float, y: float) -> None:
    c = diseno.cable
    if c["vf_origen"] != "medido":
        hoja.anadir(Texto(x, y, f"Ojo: el VF {fmt(c['vf'], 2)} es de catálogo; el del cable de verdad puede cambiar\n"
                                "unos puntos. Mídelo (latiguillo abierto, NanoVNA) y vuelve a generar el plano.",
                          5.6, GRIS))


# ---------------------------------------------------------------- dipolo de manga


def hojas_manga(diseno: Diseno, fecha: str) -> list[Hoja]:
    g, c = diseno.geometria, diseno.cable
    rad, man = g["radiador_mm"], g["manga_mm"]
    u = unidad(diseno)
    od = diseno.diametro_mm
    r = diseno.resultados
    hoja = hoja_a4(diseno, f"Dipolo de manga de coaxial · {frecuencia(diseno.f_MHz)} MHz ({texto_banda(diseno.f_MHz)})",
                   f"Coaxial {c['nombre']} · {_vf(diseno)} · radiador: el vivo; manga: la malla doblada hacia atrás")

    # 1. Vista general, sin escala
    seccion(hoja, 14, 33, "VISTA GENERAL", f"Sin escala · medidas en {u}")
    yv, xj, px_m = 62.0, 108.0, 72.0
    px_r = min(px_m * rad / man, 80.0)
    xs = xj - px_m
    hoja.anadir(
        Linea(22, yv, xj, yv, CUBIERTA, 0.56),
        Rect(xs, yv - 3.2, px_m, 6.4, TINTA, 0.18, PVC),
        Linea(xj, yv, xj + px_r, yv, COBRE, 0.85),
        Cota(xs, yv - 10, xj, yv - 10, f"manga {longitud(man, diseno)}"),
        Cota(xj, yv - 10, xj + px_r, yv - 10, f"radiador {longitud(rad, diseno)}"),
        Texto(xj, yv + 7.5, "malla unida al cable en este punto", 5.8, ancla="centro", fondo=BLANCO),
        Texto(22, yv + 5.5, "al equipo\n(con choke)", 5.8),
        Texto(xs + 2, yv - 4.5, "manga (malla doblada)", 5.6),
    )

    # 2. Lista de corte
    seccion(hoja, 14, 91, "LISTA DE CORTE", "Medidas desde el extremo del cable; sobrante para ajustar", VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        ["Radiador: vivo con su dieléctrico", "1", f"{longitud(rad, diseno)} {u}", f"{longitud(rad + sobrante, diseno, 0)} {u}"],
        ["Manga: malla doblada hacia atrás", "1", f"{longitud(man, diseno)} {u}", "—"],
        [f"Coaxial {c['nombre']}, bajada", "1", "a medida", "—"],
        [f"Termorretráctil Ø {fmt(od + 6, 0)} mm", "1", f"{longitud(man + 10, diseno, 0)} {u}", "—"],
        ["Estaño y vaina de silicona", "1", "—", "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], ["Pieza", "Cant.", "Final", "Cortar a"], filas, 104)
    hoja.anadir(Texto(14, 136, "Ajuste: recorta el vivo (el radiador) poco a poco; la manga no se toca.", 6.2, VERDE))
    _simulacion(hoja, diseno, "manga")

    # 3. Detalle del pelado a escala 1:1
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, "DETALLE DEL PELADO", "Escala 1:1 · solo el extremo del cable; la manga y el vivo siguen más largos", VERDE)
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
        Texto(xf, yd + od / 2 + 8, "aquí: la malla se dobla hacia atrás y se suelda al cable", 5.6, ancla="centro"),
        Cota(18, yd + od / 2 + 14, 68, yd + od / 2 + 14, "cubierta (sigue)"),
        Texto(xf - 44, yd - od / 2 - 5, f"manga: malla doblada, {longitud(man, diseno, 0)} {u} en total (sigue ←)", 5.6),
        Texto(xf + 41, yd - dd / 2 - 3.5, "dieléctrico", 5.6),
        Texto(xf + 41, yd + 4.2, f"vivo hasta {longitud(rad, diseno, 0)} {u} (sigue →)", 5.6),
    )
    hoja.anadir(Texto(14, 216, "Pelado orientativo: quita la cubierta en la longitud de la manga, desenreda la malla, dóblala sobre la\n"
                               "cubierta y suéldala al cable donde empieza el dieléctrico. Cubre todo con termorretráctil.", 5.8))
    _aviso_vf(hoja, diseno, 14, 226)
    regla(hoja, 14, 244)
    return [hoja]


def _diam(c: dict, clave: str, defecto: float) -> float:
    from ..cables import cable
    try:
        return getattr(cable(c["nombre"]), clave)
    except ValueError:
        return defecto


# ---------------------------------------------------------------- colineal CoCo


def hojas_coco(diseno: Diseno, fecha: str) -> list[Hoja]:
    return [_coco_resumen(diseno), _coco_detalle(diseno)]


def _titulo_coco(diseno: Diseno) -> str:
    n = int(diseno.geometria["tramos"])
    return f"Colineal CoCo de {n} tramos · {frecuencia(diseno.f_MHz)} MHz ({texto_banda(diseno.f_MHz)})"


def _coco_resumen(diseno: Diseno) -> Hoja:
    g, c = diseno.geometria, diseno.cable
    n = int(g["tramos"])
    tramo, punta = g["tramo_mm"], g["punta_mm"]
    electrico = tramo / c["vf"]
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo_coco(diseno),
                   f"Coaxial {c['nombre']} · {_vf(diseno)} · tramos de λ/2 eléctrico con el vivo y la malla cruzados")

    seccion(hoja, 14, 33, "VISTA GENERAL", f"Sin escala · medidas en {u}")
    y, x0 = 66.0, 24.0
    px = min(18.0, 150.0 / n)
    x = x0
    hoja.anadir(Linea(x0 - 8, y, x0, y, CUBIERTA, 0.56), Texto(x0 - 8, y + 6, "al equipo (con choke)", 5.6))
    for k in range(n):
        hoja.anadir(Rect(x, y - 2.2, px - 1.6, 4.4, TINTA, 0.18, CUBIERTA if k % 2 == 0 else "#4b5057"))
        hoja.anadir(Circulo(x + px - 0.8, y, 0.9, COBRE, 0.3, BLANCO))
        if k == 0:
            hoja.anadir(Cota(x, y - 8, x + px - 1.6, y - 8, f"{longitud(tramo, diseno, 0)}", tam=5.6))
        x += px
    hoja.anadir(Linea(x - 0.8, y, x + 12, y, COBRE, 0.85),
                Cota(x - 0.8, y - 8, x + 12, y - 8, f"punta {longitud(punta, diseno, 0)}", tam=5.6),
                Texto(x0 - 8, y + 14, f"{n} tramos iguales: {longitud(tramo, diseno)} {u} de cable\n"
                                 f"({longitud(electrico, diseno)} {u} eléctricos = λ/2)", 5.8))

    seccion(hoja, 14, 91, "LISTA DE CORTE", "Cada tramo se corta con sobrante para los pelados", VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        [f"Tramo de coaxial {c['nombre']}", str(n), f"{longitud(tramo, diseno)} {u}", f"{longitud(tramo + sobrante, diseno, 0)} {u}"],
        ["Punta: vivo con dieléctrico", "1", f"{longitud(punta, diseno)} {u}", f"{longitud(punta + sobrante, diseno, 0)} {u}"],
        [f"Coaxial {c['nombre']}, bajada", "1", "a medida", "—"],
        ["Termorretráctil (uniones)", str(n + 1), "40 mm", "—"],
        ["Tubo PVC de protección", "1", "todo el largo", "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], ["Pieza", "Cant.", "Final", "Cortar a"], filas, 104)
    hoja.anadir(Texto(14, 136, "Choke bajo el primer tramo: 6–8 vueltas de coaxial sobre Ø 10 cm (orientativo).", 6.0, VERDE))
    _simulacion(hoja, diseno, "coco")
    hoja.anadir(Linea(10, 148, 200, 148, GRIS, 0.1))
    seccion(hoja, 14, 153, "ORDEN DE MONTAJE", "Los detalles de cada unión, a escala 1:1, en la hoja 2", VERDE)
    pasos = ("1. Corta los tramos y la punta con el sobrante; mide el VF del cable si puedes.",
             "2. Pela cada extremo como en la hoja 2: malla a un lado, vivo al otro.",
             "3. Une los tramos cruzando: la malla de uno con el vivo del siguiente, y al revés.",
             "4. Aísla cada unión con termorretráctil y mete todo en el tubo.",
             "5. Mide la ROE con el NanoVNA y recorta la punta si hace falta.")
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
    hoja = hoja_a4(diseno, f"CoCo · detalle de la unión · {frecuencia(diseno.f_MHz)} MHz",
                   f"Escala 1:1 · coaxial {c['nombre']} · cotas del pelado orientativas ({u})")
    seccion(hoja, 14, 33, "UNIÓN ENTRE DOS TRAMOS", "Escala 1:1 · la malla de cada tramo va con el vivo del otro", VERDE)
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
        Texto(18, yd + 11, "tramo k (sigue ←)", 5.8), Texto(196, yd + 11, "tramo k + 1 (sigue →)", 5.8, ancla="derecha"),
        Texto(105, yd - 17, "cruce: vivo de k ↔ malla de k+1  ·  malla de k ↔ vivo de k+1", 5.8, ancla="centro", fondo=BLANCO),
    )
    hoja.anadir(Texto(14, 85, "Suelda cada cruce con hilo corto; deja la unión lo más corta posible y cúbrela con termorretráctil.", 5.8))

    seccion(hoja, 14, 98, "PELADOS", f"Medidas en {u}", VERDE)
    filas = [
        ["Cubierta que se quita en cada extremo", longitud(malla + dielectrico + vivo, diseno, 0)],
        ["Malla que se deja a la vista", longitud(malla, diseno, 0)],
        ["Dieléctrico que se deja a la vista", longitud(dielectrico, diseno, 0)],
        ["Vivo que sobresale", longitud(vivo, diseno, 0)],
    ]
    tabla(hoja, 14, 110, [0, 95], ["Pelado", u], filas, 104)

    hoja.anadir(Linea(10, 140, 200, 140, GRIS, 0.1))
    seccion(hoja, 14, 145, "PUNTA Y PROTECCIÓN", "Extremo de arriba y cómo se protege", VERDE)
    for k, t in enumerate(("Punta: deja solo el vivo con su dieléctrico (sin malla) en la longitud de la hoja 1 y tapa el extremo.",
                           "Protección: cada unión con termorretráctil con adhesivo; todo el conjunto dentro de un tubo de PVC",
                           "(Ø interior ≈ 2 × el del cable) sellado arriba. Cuidado: el agua entra por el coaxial.")):
        hoja.anadir(Texto(14, 156 + k * 6, t, 5.8))
    _aviso_vf(hoja, diseno, 14, 180)
    regla(hoja, 14, 244)
    return hoja


ROJO_CRUCE = "#b04a3a"


def _simulacion(hoja: Hoja, diseno: Diseno, tipo: str) -> None:
    r = diseno.resultados
    if not r:
        seccion(hoja, 128, 91, "SIN SIMULAR", "Cotas de partida, sin ajustar")
        hoja.anadir(Texto(128, 103, "Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c.", 6.3))
        return
    seccion(hoja, 128, 91, "SIMULADO (NEC2) · SIN MEDIR", "Modelo del motor de Chirptenna Wire")
    if tipo == "manga":
        hoja.anadir(Texto(128, 103, f"Resonancia {fmt(r['f_resonancia_MHz'], 1)} MHz · R = {fmt(r['r_resonancia_ohm'], 1)} Ω"
                                    f"\nGanancia {fmt(r['ganancia_dBi'], 2)} dBi", 6.3))
        banda = banda_de(diseno.f_MHz)
        grafica_roe(hoja, 138, 113, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], banda[1:] if banda else None)
        hoja.anadir(Texto(128, 156, f"ROE mínima ≈ {fmt(min(r['barrido']['roe']), 2)}. La manga es un modelo de banda\n"
                                    "estrecha: sin medir, el choke real puede ser peor.", 5.6, GRIS))
        return
    red = r.get("red") or {}
    hoja.anadir(Texto(128, 103, f"Z en el conector {fmt(r['r_ohm'], 0)} {'+' if r['x_ohm'] >= 0 else '−'} j{fmt(abs(r['x_ohm']), 0)} Ω"
                                f"\nGanancia {fmt(r['ganancia_dBi'], 2)} dBi\nROE sin red {fmt(r['roe_sin_red'], 1)}"
                                f" · con red {fmt(r['roe_con_red'], 2)}\nROE ≤ 2: solo {fmt(r['ancho_roe2_MHz'], 1)} MHz", 6.3))
    if red:
        serie = f"{fmt(red['l_serie_nH'], 0)} nH" if "l_serie_nH" in red else f"{fmt(red['c_serie_pF'], 1)} pF"
        par = f"{fmt(red['c_paralelo_pF'], 1)} pF" if "c_paralelo_pF" in red else f"{fmt(red['l_paralelo_nH'], 0)} nH"
        hoja.anadir(Texto(128, 128, f"Red en L en el conector:\nen serie {serie}, en paralelo {par}.\n"
                                    "(Banda muy estrecha: ajusta midiendo.)", 6.0, VERDE))
