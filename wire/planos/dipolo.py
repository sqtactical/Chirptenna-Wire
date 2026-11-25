"""Hoja del dipolo de media onda (formato de `docs/maquetas/plano_ejemplo_dipolo`)."""

from __future__ import annotations

from ..diseno import Diseno, banda_de
from .comun import fmt, frecuencia, grafica_roe, hoja_a4, longitud, regla, seccion, tabla, texto_banda, unidad
from .hoja import (COBRE, CUBIERTA, DIELECTRICO, GRIS, GRIS_CLARO, PVC, TINTA, VERDE, BLANCO, Circulo, Cota, Hoja,
                   Linea, Rect, Texto, rayado)

HUECO = 10.0  # mm entre los brazos, en el aislador
AISLADOR = (60.0, 25.0, 5.0)  # mm
TALADROS = 28.0  # mm entre taladros M3


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    total = diseno.geometria["largo_total_mm"]
    brazo = (total - HUECO) / 2
    d = diseno.diametro_mm
    u = unidad(diseno)
    r = diseno.resultados
    hoja = hoja_a4(diseno, f"Dipolo de media onda · {frecuencia(diseno.f_MHz)} MHz ({texto_banda(diseno.f_MHz)})",
                   f"Alambre o varilla de Ø {fmt(d, 1)} mm · alimentado con coaxial de 50 Ω")

    # 1. Vista general, sin escala
    seccion(hoja, 14, 33, "VISTA GENERAL", f"Sin escala · medidas en {u}")
    yv, xc = 59.0, 105.0
    hoja.anadir(
        Linea(22, yv, xc - 5, yv, COBRE, 0.85), Linea(xc + 5, yv, 188, yv, COBRE, 0.85),
        Rect(xc - 8, yv - 5, 16, 10, TINTA, 0.18, PVC),
        Linea(xc, yv + 5, xc, 84, CUBIERTA, 0.56),
        Cota(22, yv - 9, xc - 5, yv - 9, f"brazo {longitud(brazo, diseno)}"),
        Cota(xc + 5, yv - 9, 188, yv - 9, f"brazo {longitud(brazo, diseno)}"),
        Cota(22, yv - 17, 188, yv - 17, f"longitud total {longitud(total, diseno)}"),
        Texto(xc, yv + 9.5, f"aislador · hueco {longitud(HUECO, diseno, 0)}", 6, ancla="centro", fondo=BLANCO),
        Texto(xc + 6, 77, "choke: 6–8 vueltas de coaxial\nsobre Ø 10 cm (orientativo)", 5.8),
    )
    for k in range(4):
        hoja.anadir(Circulo(xc, 74.5 + k * 1.8, 3.4, CUBIERTA, 0.2))

    # 2. Lista de corte y resultados
    seccion(hoja, 14, 91, "LISTA DE CORTE", "Corta con el sobrante y ajusta después", VERDE)
    sobrante = diseno.sobrante_mm
    filas = [
        [f"Brazo, alambre Ø {fmt(d, 1)} mm", "2", f"{longitud(brazo, diseno)} {u}",
         f"{longitud(brazo + sobrante, diseno, 0)} {u}"],
        [f"Aislador, PVC {AISLADOR[0]:.0f} × {AISLADOR[1]:.0f} × {AISLADOR[2]:.0f}", "1", "—", "—"],
        ["Tornillos M3 × 10 con tuerca", "2", "—", "—"],
        ["Coaxial RG-58, bajada + choke", "1", "a medida", "—"],
    ]
    tabla(hoja, 14, 103, [0, 52, 64, 84], ["Pieza", "Cant.", "Final", "Cortar a"], filas, 104)
    if r:
        s = r["sensibilidad_MHz_por_mm"]
        hoja.anadir(Texto(14, 133, "Ajuste: recorta los dos brazos por igual. Quitar 1 mm de cada brazo\n"
                                   f"sube la resonancia ≈ {fmt(s, 2)} MHz (1 MHz ≈ {fmt(1 / s, 1)} mm por brazo).",
                          6.2, VERDE))
    else:
        hoja.anadir(Texto(14, 133, "Ajuste: recorta los dos brazos por igual hasta que la ROE mínima\n"
                                   "caiga en la frecuencia (mídela con el NanoVNA).", 6.2, VERDE))
    _simulacion(hoja, diseno)

    # 3. Detalle del centro, a escala 1:1
    hoja.anadir(Linea(10, 163, 200, 163, GRIS_CLARO, 0.14))
    seccion(hoja, 14, 168, "DETALLE DEL CENTRO", "Escala 1:1 · pon las piezas encima del papel para marcar y pelar",
            VERDE)
    yd, xa = 193.0, 105.0
    an, al = AISLADOR[0], AISLADOR[1]
    hoja.anadir(Rect(xa - an / 2, yd - al / 2, an, al, TINTA, 0.18, PVC, etiqueta="plantilla:aislador"))
    for x1, x2, etiqueta in ((xa - 80, xa - HUECO / 2, "plantilla:brazo_izq"), (xa + HUECO / 2, xa + 80,
                                                                                  "plantilla:brazo_der")):
        hoja.anadir(Rect(x1, yd - d / 2, x2 - x1, d, None, relleno=COBRE, etiqueta=etiqueta))
    for s in (-1, 1):
        hoja.anadir(Circulo(xa + s * TALADROS / 2, yd, 1.6, TINTA, 0.14, BLANCO, etiqueta="plantilla:taladro"),
                    Circulo(xa + s * TALADROS / 2, yd, 3.0, GRIS, 0.1, discontinua=(0.4, 0.4)))
    abajo = yd + al / 2
    hoja.anadir(
        Cota(xa - HUECO / 2, yd - al / 2 - 4, xa + HUECO / 2, yd - al / 2 - 4, longitud(HUECO, diseno, 0)),
        # La altura del aislador se acota en el hueco central, donde no hay brazo que cortar.
        Cota(xa, yd - al / 2, xa, abajo, longitud(al, diseno, 0), texto_en=0.25),
        Cota(xa - TALADROS / 2, abajo + 5, xa + TALADROS / 2, abajo + 5,
             f"{longitud(TALADROS, diseno, 0)} (taladros Ø 3,2)",
             ref1=(xa - TALADROS / 2, yd + 1.6), ref2=(xa + TALADROS / 2, yd + 1.6)),
        Cota(xa - an / 2, abajo + 11, xa + an / 2, abajo + 11, longitud(an, diseno, 0),
             ref1=(xa - an / 2, abajo), ref2=(xa + an / 2, abajo)),
        Texto(xa - 79, yd - 3.5, "← brazo (sigue)", 5.8),
        Texto(xa + 79, yd - 3.5, "brazo (sigue) →", 5.8, ancla="derecha"),
    )
    _coaxial(hoja, diseno, 30.0, 228.5)

    regla(hoja, 14, 244)
    return [hoja]


def _simulacion(hoja: Hoja, diseno: Diseno) -> None:
    r = diseno.resultados
    if not r:
        seccion(hoja, 128, 91, "SIN SIMULAR", "Cotas de partida (0,48 λ), sin ajustar")
        hoja.anadir(Texto(128, 103, "Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c.", 6.3))
        return
    seccion(hoja, 128, 91, "SIMULADO (NEC2) · SIN MEDIR", "Modelo del motor de Chirptenna Wire")
    hoja.anadir(Texto(128, 103, f"Resonancia {fmt(r['f_resonancia_MHz'], 1)} MHz · R = {fmt(r['r_resonancia_ohm'], 1)} Ω"
                                f"\nGanancia {fmt(r['ganancia_dBi'], 2)} dBi", 6.3))
    banda = banda_de(diseno.f_MHz)
    grafica_roe(hoja, 138, 113, 58, 31, r["barrido"]["f_MHz"], r["barrido"]["roe"], banda[1:] if banda else None)
    hoja.anadir(Texto(128, 156, f"ROE mínima ≈ {fmt(min(r['barrido']['roe']), 2)}: un dipolo da ~72 Ω, no 50.\n"
                                "Vale tal cual; para bajarla, un adaptador.", 5.6, GRIS))


def _coaxial(hoja: Hoja, diseno: Diseno, x: float, yc: float) -> None:
    """RG-58 pelado a escala 1:1 (cotas orientativas del pelado)."""
    malla, dielectrico, vivo = 12.0, 6.0, 12.0
    xm, xd, xv = x + 50, x + 50 + malla, x + 50 + malla + dielectrico
    hoja.anadir(Rect(x, yc - 2.5, 50, 5, None, relleno=CUBIERTA),
                Rect(xm, yc - 2.3, malla, 4.6, None, relleno=COBRE))
    hoja.anadir(*rayado(xm, yc - 2.3, malla, 4.6, 1.2, TINTA))
    hoja.anadir(Rect(xd, yc - 1.5, dielectrico, 3, TINTA, 0.1, DIELECTRICO),
                Rect(xv, yc - 0.5, vivo, 1, None, relleno=COBRE),
                Cota(xm, yc - 6.5, xd, yc - 6.5, longitud(malla, diseno, 0)),
                Cota(xd, yc - 6.5, xv, yc - 6.5, longitud(dielectrico, diseno, 0)),
                Cota(xv, yc - 6.5, xv + vivo, yc - 6.5, longitud(vivo, diseno, 0)),
                Texto(x, yc + 7, "RG-58 a escala: malla al tornillo del brazo izquierdo · dieléctrico · vivo al derecho.\n"
                                 "Sella el centro con termorretráctil o silicona neutra.", 5.8))
