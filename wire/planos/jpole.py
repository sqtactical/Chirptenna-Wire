"""Hojas de la J-pole: resumen (sin escala) y detalle 1:1 del adaptador y la toma."""

from __future__ import annotations

from ..diseno import Diseno, banda_de
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad, alambre
from .hoja import BLANCO, COBRE, CUBIERTA, GRIS, TINTA, VERDE, Circulo, Cota, Hoja, Linea, Texto
from .paginacion import decidir_papel

# Detalle 1:1: dónde va el fondo de la U y la altura del brazo largo en la hoja.
X_U, Y_LARGO = 26.0, 62.0
MARGEN_IZQ, MARGEN_DER = 16.0, 30.0  # sitio para la cota de la separación y el rótulo de la punta


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    return [_resumen(diseno), _detalle(diseno)]


def _titulo(diseno: Diseno) -> str:
    return f"J-pole · {frecuencia(diseno.f_MHz)} MHz ({texto_banda(diseno.f_MHz)})"


def _resumen(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    largo, corto, toma, s = g["largo_mm"], g["corto_mm"], g["toma_mm"], g["separacion_mm"]
    d = diseno.diametro_mm
    u = unidad(diseno)
    hoja = hoja_a4(diseno, _titulo(diseno),
                   f"Una pieza de alambre o varilla de Ø {fmt(d, 1)} mm doblada en U · alimentada con coaxial de 50 Ω")

    # 1. Vista general, sin escala (tumbada: la U a la izquierda, la punta del radiante a la derecha)
    seccion(hoja, 14, 33, "VISTA GENERAL", f"Sin escala · medidas en {u} al eje del alambre")
    x0, x1, yl, yc = 32.0, 188.0, 62.0, 72.0
    xc = x0 + (x1 - x0) * corto / largo
    xt = x0 + 18.0  # la toma, exagerada para que se vea
    hoja.anadir(
        Linea(x0, yl, x1, yl, COBRE, 0.85), Linea(x0, yc, xc, yc, COBRE, 0.85), Linea(x0, yl, x0, yc, COBRE, 0.85),
        Circulo(xt, yl, 0.9, TINTA, 0.15, BLANCO), Circulo(xt, yc, 0.9, TINTA, 0.15, BLANCO),
        Linea(xt, yc + 0.9, xt, 80, CUBIERTA, 0.56),
        Texto(xt + 2, 80.5, "coaxial al equipo (con choke)", 5.6),
        Cota(x0, yl - 14, x1, yl - 14, f"brazo largo {longitud(largo, diseno)}", ref1=(x0, yl), ref2=(x1, yl)),
        Cota(xc, yl - 7, x1, yl - 7, f"radiante (λ/2) {longitud(largo - corto, diseno)}", ref1=(xc, yl)),
        Cota(x0, 88, xc, 88, f"brazo corto (λ/4) {longitud(corto, diseno)}", ref1=(x0, yc), ref2=(xc, yc)),
        Cota(x0, yc + 4, xt, yc + 4, f"toma {longitud(toma, diseno)}", texto_en=0.5),
        Cota(x0 - 6, yl, x0 - 6, yc, longitud(s, diseno, 1 if s % 1 else 0), ref1=(x0, yl), ref2=(x0, yc)),
        Texto(xc + 3, yc + 1.2, "adaptador", 5.6, GRIS),
    )

    # 2. Lista de corte y resultados
    seccion(hoja, 14, 101, "LISTA DE CORTE", "Corta con el sobrante (queda en la punta del brazo largo)", VERDE)
    total = largo + s + corto
    filas = [
        [f"Alambre Ø {fmt(d, 1)} mm, una pieza", "1", f"{longitud(total, diseno)} {u}",
         f"{longitud(total + diseno.sobrante_mm, diseno, 0)} {u}"],
        [f"Espaciador aislante, {longitud(s, diseno, 0)} {u} entre ejes", "2", "—", "—"],
        ["Coaxial RG-58, bajada + choke", "1", "a medida", "—"],
        ["Abrazaderas aisladas para el mástil", "2", "—", "—"],
    ]
    y = tabla(hoja, 14, 113, [0, 52, 64, 84], ["Pieza", "Cant.", "Final", "Cortar a"], filas, 104)
    hoja.anadir(Texto(14, y + 1, f"Dobleces a 90°, medidos desde la punta del brazo corto: {longitud(corto, diseno)} "
                                 f"y {longitud(corto + s, diseno)} {u}.", 6.0))
    r = diseno.resultados
    if r:
        sl, sc = r["sensibilidad_MHz_por_mm"], r.get("sensibilidad_corto_MHz_por_mm")
        texto = (f"Ajuste: recorta la punta del brazo largo; quitar 1 mm sube el mínimo\n"
                 f"de ROE ≈ {fmt(sl, 3)} MHz")
        if sc:
            texto += f" (en el brazo corto, ≈ {fmt(sc, 2)} MHz por mm)"
        texto += ".\nSi la ROE mínima no baja de 1,5, sube o baja la toma unos mm."
    else:
        texto = ("Ajuste: recorta la punta del brazo largo hasta que la ROE mínima\ncaiga en la frecuencia; "
                 "luego mueve la toma para bajarla.")
    hoja.anadir(Texto(14, y + 8, texto, 6.0, VERDE))
    _simulacion(hoja, diseno)

    # 3. Montaje
    seccion(hoja, 14, 176, "MONTAJE", "Paso a paso · la hoja 2 lleva el fondo de la U y la toma a escala 1:1")
    pasos = [
        "1. Corta el alambre a «Cortar a» y enderézalo.",
        f"2. Marca los dos dobleces desde la punta del brazo corto y dóblalos a 90° sobre la plantilla de la hoja 2.",
        "3. Pon los espaciadores para mantener la separación entre los brazos.",
        "4. Coaxial en la toma: vivo al brazo largo, malla al corto (soldado o con abrazadera).",
        "5. Choke: 6–8 vueltas del coaxial sobre Ø 10 cm justo debajo de la U (orientativo).",
        "6. Sujeta la J-pole al mástil por la U; el mástil no está en el modelo y puede mover la resonancia.",
        "7. Mide con el NanoVNA (Chirptenna VNA) y recorta la punta del brazo largo en pasos de 2–3 mm.",
    ]
    hoja.anadir(Texto(14, 188, "\n".join(pasos), 6.3))
    return hoja


def _simulacion(hoja: Hoja, diseno: Diseno) -> None:
    r = diseno.resultados
    if not r:
        seccion(hoja, 128, 101, "SIN SIMULAR", "Cotas de partida, sin ajustar")
        hoja.anadir(Texto(128, 113, "Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c.", 6.3))
        return
    seccion(hoja, 128, 101, "SIMULADO (NEC2) · SIN MEDIR", "Espacio libre, sin mástil ni cable de bajada")
    signo = "+" if r["x_ohm"] >= 0 else "−"
    hoja.anadir(Texto(128, 113, f"Mínimo de ROE a {fmt(r['f_minimo_roe_MHz'], 2)} MHz\n"
                                f"Z = {fmt(r['r_ohm'], 1)} {signo} j{fmt(abs(r['x_ohm']), 1)} Ω · "
                                f"S11 = {fmt(max(r['s11_dB'], -40), 0)} dB · {fmt(r['ganancia_dBi'], 2)} dBi", 6.3))
    banda = banda_de(diseno.f_MHz)
    grafica_roe(hoja, 138, 125, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], banda[1:] if banda else None)


def _detalle(diseno: Diseno) -> Hoja:
    g = diseno.geometria
    corto, toma, s = g["corto_mm"], g["toma_mm"], g["separacion_mm"]
    d = diseno.diametro_mm
    # Si el adaptador entero cabe a 1:1 en una A4 (vertical o apaisada), va entero; si no, el fondo de la U y la toma.
    decision = decidir_papel(corto + MARGEN_IZQ + MARGEN_DER, s + 50, diseno.plano)
    corto_entero = decision["modo"] == "hoja"
    apaisada = decision["apaisada"] if corto_entero else False
    hoja = hoja_a4(diseno, _titulo(diseno), "Detalle del adaptador y la toma", apaisada=apaisada)
    seccion(hoja, 14, 33, "FONDO DE LA U, ADAPTADOR Y TOMA",
            "Escala 1:1 · pon el alambre encima para marcar los dobleces y la toma", VERDE)
    x_fin = hoja.tamano[0] - 16
    yl, yc = Y_LARGO, Y_LARGO + s
    fin_corto = X_U + corto if corto_entero else x_fin
    fin_largo = min(fin_corto + 22, x_fin) if corto_entero else x_fin
    alambre(hoja, X_U, yl, fin_largo, yl, d, "plantilla:eje_largo")
    alambre(hoja, X_U, yc, fin_corto, yc, d, "plantilla:eje_corto")
    alambre(hoja, X_U, yl, X_U, yc, d, "plantilla:eje_u")
    xt = X_U + toma
    hoja.anadir(
        Linea(xt, yl - 5, xt, yc + 5, VERDE, 0.25, (1.2, 0.6), etiqueta="plantilla:toma"),
        Circulo(xt, yl, d / 2 + 0.8, VERDE, 0.2), Circulo(xt, yc, d / 2 + 0.8, VERDE, 0.2),
        Texto(xt + 1.5, yc + 8.5, "toma: vivo al brazo largo · malla al corto", 5.8, VERDE),
        Cota(X_U - 9, yl, X_U - 9, yc, longitud(s, diseno), ref1=(X_U - d / 2, yl), ref2=(X_U - d / 2, yc)),
        Cota(X_U, yl - 10, xt, yl - 10, f"toma {longitud(toma, diseno)}", ref1=(X_U, yl - d / 2),
             ref2=(xt, yl - 5)),
        Texto(fin_largo, yl - 3, "brazo largo (sigue) →", 5.8, ancla="derecha"),
        Texto(X_U + 2, yl + s / 2 + 1, "doblez 90°", 5.4, GRIS) if s >= 9 else Texto(X_U - 2, yc + 6, "dobleces 90°",
                                                                                    5.4, GRIS),
    )
    if corto_entero:
        hoja.anadir(Cota(X_U, yc + 16, fin_corto, yc + 16, f"brazo corto {longitud(corto, diseno)}",
                         ref1=(X_U, yc + d / 2), ref2=(fin_corto, yc + d / 2)),
                    Texto(fin_corto + 2, yc + 1.2, "punta del brazo corto", 5.6))
    else:
        hoja.anadir(Texto(x_fin, yc + 5, "brazo corto (sigue) →", 5.8, ancla="derecha"),
                    Texto(X_U, yc + 18, f"El brazo corto mide {longitud(corto, diseno)} {unidad(diseno)} desde el "
                                        "fondo de la U: no cabe entero a 1:1 en A4 (A3 y mosaico, más adelante).",
                          6.0))

    y = yc + 30
    seccion(hoja, 14, y, "CÓMO USAR LA PLANTILLA", "Medidas al eje del alambre")
    u = unidad(diseno)
    if corto_entero:
        paso2 = ["2. Pon la punta del alambre en la punta del brazo corto, sigue su eje y dobla a 90° sobre el eje",
                 "    de la U; vuelve a doblar a 90° sobre el eje del brazo largo."]
    else:
        paso2 = [f"2. Marca el primer doblez a {longitud(corto, diseno)} {u} de la punta del alambre, ponlo sobre el eje "
                 "de la U",
                 "    y dobla a 90°; vuelve a doblar a 90° sobre el eje del brazo largo."]
    pasos = [
        "1. Comprueba la escala con la regla de abajo antes de nada.",
        *paso2,
        "3. Marca la toma en los dos brazos (línea verde) con un rotulador fino.",
        "4. Suelda el coaxial en las marcas; deja el choke justo debajo de la U.",
        f"5. Separación entre ejes {longitud(s, diseno)} {u}: los espaciadores la mantienen.",
    ]
    hoja.anadir(Texto(14, y + 12, "\n".join(pasos), 6.3))
    regla(hoja, 14, hoja.tamano[1] - 53)
    return hoja
