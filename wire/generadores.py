"""Generadores de antenas: de las entradas del usuario (frecuencia, material) a un `Modelo`.

Python puro (corre en Pyodide): el ajuste con el motor está en `wire/ajuste.py`, que solo se usa en escritorio.
"""

from __future__ import annotations

from . import geometria
import math

from .modelo import Barrido, Hilo, Modelo, Puerto, longitud_onda_m

# Longitud total por defecto del dipolo, en fracciones de λ. Es un punto de partida, no el ajuste:
# la resonancia real depende del radio y se busca con el motor (`ajuste.ajustar_dipolo`).
FACTOR_DIPOLO = 0.48

# Segmentos por longitud de onda: λ/50 por segmento sobra para un dipolo de hilo fino.
SEGMENTOS_POR_LAMBDA = 50

# J-pole: puntos de partida en fracciones de λ (el ajuste los corrige con el motor).
JPOLE_LARGO = 0.73  # brazo largo, del fondo de la U a la punta (adaptador λ/4 + radiante λ/2)
JPOLE_CORTO = 0.245  # brazo corto (adaptador λ/4), del fondo de la U a su punta
JPOLE_TOMA = 0.03  # altura del punto de toma sobre el fondo de la U
JPOLE_SEPARACION = 0.012  # separación entre ejes de los dos brazos

# Segmentación de la J-pole, en múltiplos de min(λ/50, separación). Con 1 el ajuste «converge» a una frecuencia
# 0,3–0,8 % más alta que la real; a partir de 3 el mínimo de ROE ya no se mueve (medido a 145 y 435 MHz, 2 mm).
DENSIDAD_JPOLE = 3.0


def segmentos_para(longitud_m: float, lambda_m: float, minimo: int = 11) -> int:
    """Número impar de segmentos (para que haya un segmento central) a unos λ/50 cada uno."""
    n = max(minimo, round(longitud_m / lambda_m * SEGMENTOS_POR_LAMBDA))
    return n if n % 2 else n + 1


def dipolo(
    f_MHz: float,
    radio_mm: float,
    longitud_mm: float | None = None,
    segmentos: int | None = None,
    barrido: Barrido | None = None,
) -> Modelo:
    """Dipolo de media onda vertical (eje z), centrado en el origen y alimentado en el segmento central.

    En NEC2 el hueco de alimentación es el propio segmento central; el plano acota el hueco real del aislador.
    """
    if f_MHz <= 0:
        raise ValueError("la frecuencia debe ser positiva")
    if radio_mm <= 0:
        raise ValueError("el radio debe ser positivo")
    lam = longitud_onda_m(f_MHz)
    largo = longitud_mm / 1000 if longitud_mm else FACTOR_DIPOLO * lam
    n = segmentos or segmentos_para(largo, lam)
    if n % 2 == 0:
        raise ValueError("el dipolo necesita un número impar de segmentos")
    radio = radio_mm / 1000
    if radio * 2 >= largo / n:
        raise ValueError("los segmentos son más cortos que el diámetro del hilo: hay que usar menos")
    hilo = Hilo((0.0, 0.0, -largo / 2), (0.0, 0.0, largo / 2), radio, n)
    return Modelo(
        nombre="Dipolo de media onda",
        f_MHz=f_MHz,
        hilos=(hilo,),
        puerto=Puerto(hilo=1, segmento=n // 2 + 1),
        barrido=barrido,
        comentarios=(
            f"Dipolo de media onda a {f_MHz:g} MHz",
            f"Longitud total {largo * 1000:.1f} mm, radio {radio_mm:g} mm, {n} segmentos",
        ),
    )


def jpole_por_defecto(f_MHz: float, diametro_mm: float) -> dict[str, float]:
    """Cotas de partida de la J-pole (mm, al eje del alambre), sin ajustar con el motor."""
    lam = longitud_onda_m(f_MHz) * 1000
    separacion = max(round(JPOLE_SEPARACION * lam * 2) / 2, 6 * diametro_mm)
    return {
        "largo_mm": JPOLE_LARGO * lam,
        "corto_mm": JPOLE_CORTO * lam,
        "toma_mm": JPOLE_TOMA * lam,
        "separacion_mm": separacion,
    }


def jpole(
    f_MHz: float,
    diametro_mm: float,
    largo_mm: float | None = None,
    corto_mm: float | None = None,
    toma_mm: float | None = None,
    separacion_mm: float | None = None,
    barrido: Barrido | None = None,
    densidad: float = DENSIDAD_JPOLE,
) -> Modelo:
    """J-pole de alambre o varilla doblada en U, vertical, en espacio libre (sin mástil).

    `densidad` multiplica el número de segmentos (para comprobar la convergencia: el doble debe dar lo mismo).

    Brazo largo en x = 0 y brazo corto en x = separación, unidos abajo (z = 0) por el tramo recto de la U.
    La alimentación es un hilo horizontal entre los dos brazos a la altura de la toma, con la fuente en él
    (vivo al brazo largo, malla al corto). Todas las cotas, en mm al eje del alambre.
    """
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    partida = jpole_por_defecto(f_MHz, diametro_mm)
    largo = (largo_mm or partida["largo_mm"]) / 1000
    corto = (corto_mm or partida["corto_mm"]) / 1000
    toma = (toma_mm or partida["toma_mm"]) / 1000
    s = (separacion_mm or partida["separacion_mm"]) / 1000
    radio = diametro_mm / 2000
    if not 0 < toma < corto < largo:
        raise ValueError("la J-pole necesita 0 < toma < brazo corto < brazo largo")
    if s <= 2 * diametro_mm / 1000:
        raise ValueError("la separación entre brazos es demasiado pequeña para ese diámetro")
    lam = longitud_onda_m(f_MHz)
    paso = min(lam / SEGMENTOS_POR_LAMBDA, s) / densidad  # segmentos parecidos en las uniones

    def tramo(a, b):
        largo_tramo = sum((y - x) ** 2 for x, y in zip(a, b)) ** 0.5
        return Hilo(a, b, radio, max(1, round(largo_tramo / paso)))

    # El puente de alimentación lleva un número impar de segmentos de la misma longitud que los de las ramas (la
    # fuente va en el central): con un solo segmento largo, el resultado no converge al subdividir el resto.
    n_puente = max(1, round(s / paso))
    n_puente += 1 - n_puente % 2
    hilos = (
        tramo((0, 0, 0), (0, 0, toma)),  # 1 brazo largo: fondo → toma
        tramo((0, 0, toma), (0, 0, corto)),  # 2 brazo largo: toma → altura del corto
        tramo((0, 0, corto), (0, 0, largo)),  # 3 brazo largo: radiante λ/2
        tramo((s, 0, 0), (s, 0, toma)),  # 4 brazo corto: fondo → toma
        tramo((s, 0, toma), (s, 0, corto)),  # 5 brazo corto: toma → punta
        tramo((0, 0, 0), (s, 0, 0)),  # 6 fondo de la U
        Hilo((0, 0, toma), (s, 0, toma), radio, n_puente),  # 7 alimentación
    )
    return Modelo(
        nombre="J-pole",
        f_MHz=f_MHz,
        hilos=hilos,
        puerto=Puerto(hilo=7, segmento=n_puente // 2 + 1),
        barrido=barrido,
        comentarios=(
            f"J-pole a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
            f"Largo {largo * 1000:.1f} mm, corto {corto * 1000:.1f} mm, toma {toma * 1000:.1f} mm, "
            f"separacion {s * 1000:.1f} mm",
        ),
    )


KOCH_ITERACION = 2        # J-pole de Koch: iteración por defecto de la curva del radiador
KOCH_FACTOR = 1.0         # largo del radiador de Koch (a lo largo de la curva) / el del radiador recto; se ajusta con el motor


def jpole_koch_por_defecto(f_MHz: float, diametro_mm: float, iteracion: int = KOCH_ITERACION) -> dict[str, float]:
    """Cotas de partida de la J-pole de Koch (mm): el adaptador de la recta y la altura de la curva que da el mismo largo."""
    recta = jpole_por_defecto(f_MHz, diametro_mm)
    radiante = recta["largo_mm"] - recta["corto_mm"]          # radiador λ/2 recto
    return {
        "corto_mm": recta["corto_mm"],
        "toma_mm": recta["toma_mm"],
        "separacion_mm": recta["separacion_mm"],
        "altura_koch_mm": radiante * KOCH_FACTOR / (4 / 3) ** iteracion,    # cuerda de la curva
        "iteracion": float(iteracion),
    }


def jpole_koch(
    f_MHz: float,
    diametro_mm: float,
    altura_koch_mm: float | None = None,
    corto_mm: float | None = None,
    toma_mm: float | None = None,
    separacion_mm: float | None = None,
    iteracion: int = KOCH_ITERACION,
    barrido: Barrido | None = None,
    densidad: float = DENSIDAD_JPOLE,
) -> Modelo:
    """J-pole con el radiador λ/2 hecho curva de Koch (en el plano de la U, muescas hacia fuera, lejos del brazo corto).

    Igual que `jpole` hasta la altura del brazo corto; encima, la curva de Koch de `iteracion` niveles entre los mismos
    extremos (cuerda `altura_koch_mm`): cada tramo recto de la curva es un hilo con sus segmentos.
    """
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    if not 1 <= iteracion <= 3:
        raise ValueError("la iteración de Koch debe ser 1, 2 o 3")
    partida = jpole_koch_por_defecto(f_MHz, diametro_mm, iteracion)
    altura = (altura_koch_mm or partida["altura_koch_mm"]) / 1000
    corto = (corto_mm or partida["corto_mm"]) / 1000
    toma = (toma_mm or partida["toma_mm"]) / 1000
    s = (separacion_mm or partida["separacion_mm"]) / 1000
    radio = diametro_mm / 2000
    if not 0 < toma < corto:
        raise ValueError("la J-pole necesita 0 < toma < brazo corto")
    if s <= 2 * diametro_mm / 1000:
        raise ValueError("la separación entre brazos es demasiado pequeña para ese diámetro")
    lam = longitud_onda_m(f_MHz)
    paso = min(lam / SEGMENTOS_POR_LAMBDA, s) / densidad

    def tramo(a, b):
        largo_tramo = sum((y - x) ** 2 for x, y in zip(a, b)) ** 0.5
        return Hilo(a, b, radio, max(1, round(largo_tramo / paso)))

    n_puente = max(1, round(s / paso))
    n_puente += 1 - n_puente % 2
    curva = geometria.koch_hacia_fuera(iteracion, (0.0, corto), (0.0, corto + altura))
    puntos = [(x, 0.0, z) for x, z in curva]
    hilos = [
        tramo((0, 0, 0), (0, 0, toma)),
        tramo((0, 0, toma), (0, 0, corto)),
        *[tramo(a, b) for a, b in zip(puntos, puntos[1:])],        # radiador: un hilo por tramo de la curva
        tramo((s, 0, 0), (s, 0, toma)),
        tramo((s, 0, toma), (s, 0, corto)),
        tramo((0, 0, 0), (s, 0, 0)),
        Hilo((0, 0, toma), (s, 0, toma), radio, n_puente),
    ]
    longitud_curva = geometria.longitud(curva) * 1000
    return Modelo(
        nombre="J-pole de Koch",
        f_MHz=f_MHz,
        hilos=tuple(hilos),
        puerto=Puerto(hilo=len(hilos), segmento=n_puente // 2 + 1),
        barrido=barrido,
        comentarios=(
            f"J-pole de Koch (iteracion {iteracion}) a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
            f"Altura de la curva {altura * 1000:.1f} mm (largo {longitud_curva:.1f} mm), corto {corto * 1000:.1f} mm, "
            f"toma {toma * 1000:.1f} mm, separacion {s * 1000:.1f} mm",
        ),
    )


DISCONE_SEMIANGULO = 30.0   # grados: 60° de apertura total del cono
DISCONE_VARILLAS = 8
DISCONE_K_DISCO = 0.5       # radio del disco / largo de la generatriz del cono (probado de 0,3 a 0,5: 0,5 da la banda más ancha)


def discone_por_defecto(f_min_MHz: float, k_cono: float = 1.0) -> dict[str, float]:
    """Cotas de partida del discone (mm): generatriz del cono = k·λ/4 a la frecuencia mínima, radio del disco y hueco."""
    lam = longitud_onda_m(f_min_MHz) * 1000
    cono = k_cono * lam / 4
    return {"cono_mm": cono, "disco_mm": DISCONE_K_DISCO * cono, "hueco_mm": max(4.0, round(0.004 * lam)),
            "semiangulo": DISCONE_SEMIANGULO, "varillas": float(DISCONE_VARILLAS)}


def discone(
    f_min_MHz: float,
    diametro_mm: float,
    cono_mm: float | None = None,
    disco_mm: float | None = None,
    hueco_mm: float | None = None,
    semiangulo: float = DISCONE_SEMIANGULO,
    varillas: int = DISCONE_VARILLAS,
    barrido: Barrido | None = None,
    densidad: float = 1.0,
) -> Modelo:
    """Discone de varillas, vertical y en espacio libre: disco de `varillas` radiales arriba y cono de `varillas` generatrices abajo.

    El cono tiene su vértice en el origen y se abre hacia abajo (semiángulo `semiangulo`); el disco, de radio `disco_mm`,
    queda `hueco_mm` más arriba. La fuente va en el hilo corto entre el vértice y el centro del disco. Medidas al eje del
    alambre, en mm. A `f_min_MHz` la generatriz del cono mide λ/4 con el factor por defecto.
    """
    if f_min_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    if varillas < 3:
        raise ValueError("el discone necesita al menos 3 varillas")
    partida = discone_por_defecto(f_min_MHz)
    cono = (cono_mm or partida["cono_mm"]) / 1000
    disco = (disco_mm or partida["disco_mm"]) / 1000
    g = (hueco_mm or partida["hueco_mm"]) / 1000
    radio = diametro_mm / 2000
    lam = longitud_onda_m(f_min_MHz)
    paso = lam / SEGMENTOS_POR_LAMBDA / densidad
    al = math.radians(semiangulo)

    def hilo(a, b):
        return Hilo(a, b, radio, max(1, round(math.dist(a, b) / paso)))

    hilos = [Hilo((0, 0, 0), (0, 0, g), radio, 1)]           # 1: alimentación
    for i in range(varillas):                                  # disco
        a = 2 * math.pi * i / varillas
        hilos.append(hilo((0, 0, g), (disco * math.cos(a), disco * math.sin(a), g)))
    for i in range(varillas):                                  # cono
        a = 2 * math.pi * i / varillas
        hilos.append(hilo((0, 0, 0), (cono * math.sin(al) * math.cos(a), cono * math.sin(al) * math.sin(a), -cono * math.cos(al))))
    return Modelo(
        nombre="Discone",
        f_MHz=f_min_MHz,
        hilos=tuple(hilos),
        puerto=Puerto(hilo=1, segmento=1),
        barrido=barrido,
        comentarios=(
            f"Discone de {varillas} varillas, frecuencia minima {f_min_MHz:g} MHz, alambre de {diametro_mm:g} mm",
            f"Generatriz {cono * 1000:.1f} mm, radio del disco {disco * 1000:.1f} mm, hueco {g * 1000:.1f} mm, "
            f"semiangulo {semiangulo:g} grados",
        ),
    )


# ---------------------------------------------------------------- ground plane, V invertida, Yagi y bicónica

GP_RADIADOR, GP_RADIAL = 0.232, 0.246     # en λ: el radiador algo corto y los radiales algo largos (45° da ~50 Ω)
GP_ANGULO, GP_RADIALES = 45.0, 4
VINV_BRAZO, VINV_APERTURA = 0.238, 120.0  # en λ, y grados de apertura total entre los brazos
YAGI_REFLECTOR, YAGI_EXCITADO, YAGI_DIRECTOR = 0.495, 0.470, 0.440
YAGI_SEP_REFLECTOR, YAGI_SEP_DIRECTOR, YAGI_SEP_PLEGADO = 0.20, 0.15, 0.012    # en λ


def _segmentos(largo: float, paso: float) -> int:
    return max(1, round(largo / paso))


def gp_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"radiador_mm": GP_RADIADOR * lam, "radial_mm": GP_RADIAL * lam, "angulo": GP_ANGULO, "radiales": float(GP_RADIALES)}


def gp(f_MHz: float, diametro_mm: float, radiador_mm: float | None = None, radial_mm: float | None = None,
       angulo: float = GP_ANGULO, radiales: int = GP_RADIALES, barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Ground plane: radiador vertical de λ/4 y `radiales` radiales inclinados `angulo` grados bajo la horizontal, todo unido
    en el origen (el conector); la fuente en el primer segmento del radiador. Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0 or radiales < 2:
        raise ValueError("frecuencia y diámetro positivos y al menos 2 radiales")
    p = gp_por_defecto(f_MHz)
    rad = (radiador_mm or p["radiador_mm"]) / 1000
    rl = (radial_mm or p["radial_mm"]) / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    hilos = [Hilo((0, 0, 0), (0, 0, rad), r, _segmentos(rad, paso))]
    c, s = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
    for i in range(radiales):
        a = 2 * math.pi * i / radiales
        hilos.append(Hilo((0, 0, 0), (rl * c * math.cos(a), rl * c * math.sin(a), -rl * s), r, _segmentos(rl, paso)))
    return Modelo("Ground plane", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Ground plane a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Radiador {rad * 1000:.1f} mm, {radiales} radiales de {rl * 1000:.1f} mm a {angulo:g} grados"))


def vinv_por_defecto(f_MHz: float) -> dict[str, float]:
    return {"brazo_mm": VINV_BRAZO * longitud_onda_m(f_MHz) * 1000, "apertura": VINV_APERTURA}


def vinv(f_MHz: float, diametro_mm: float, brazo_mm: float | None = None, apertura: float = VINV_APERTURA,
         barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Dipolo en V invertida: dos brazos iguales que bajan desde el vértice (arriba) con `apertura` grados entre sí;
    la fuente en el primer segmento de un brazo, junto al vértice. Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0 or not 30 <= apertura <= 180:
        raise ValueError("frecuencia y diámetro positivos y apertura entre 30° y 180°")
    brazo = (brazo_mm or vinv_por_defecto(f_MHz)["brazo_mm"]) / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    m = math.radians(apertura / 2)
    hilos = (Hilo((0, 0, 0), (brazo * math.sin(m), 0, -brazo * math.cos(m)), r, _segmentos(brazo, paso)),
             Hilo((0, 0, 0), (-brazo * math.sin(m), 0, -brazo * math.cos(m)), r, _segmentos(brazo, paso)))
    return Modelo("Dipolo en V invertida", f_MHz, hilos, Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Dipolo en V invertida a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Brazos de {brazo * 1000:.1f} mm, apertura {apertura:g} grados"))


def yagi_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"reflector_mm": YAGI_REFLECTOR * lam, "excitado_mm": YAGI_EXCITADO * lam, "director_mm": YAGI_DIRECTOR * lam,
            "sep_reflector_mm": YAGI_SEP_REFLECTOR * lam, "sep_director_mm": YAGI_SEP_DIRECTOR * lam,
            "sep_plegado_mm": YAGI_SEP_PLEGADO * lam}


def yagi(f_MHz: float, diametro_mm: float, reflector_mm: float | None = None, excitado_mm: float | None = None,
         director_mm: float | None = None, sep_reflector_mm: float | None = None, sep_director_mm: float | None = None,
         sep_plegado_mm: float | None = None, barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Yagi de 3 elementos con el excitado en dipolo plegado (dos alambres paralelos unidos en los extremos), en espacio libre.

    Los elementos van a lo largo de x y el eje (boom, aislante) a lo largo de y: reflector en y = 0, excitado a
    `sep_reflector_mm` y director a `sep_director_mm` más. El dipolo plegado tiene su alambre alimentado abajo y el otro a
    `sep_plegado_mm` por encima (eje z); la fuente va en el segmento central del alimentado.
    """
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = yagi_por_defecto(f_MHz)
    refl = (reflector_mm or p["reflector_mm"]) / 1000
    exc = (excitado_mm or p["excitado_mm"]) / 1000
    dire = (director_mm or p["director_mm"]) / 1000
    y1 = (sep_reflector_mm or p["sep_reflector_mm"]) / 1000
    y2 = y1 + (sep_director_mm or p["sep_director_mm"]) / 1000
    sp = (sep_plegado_mm or p["sep_plegado_mm"]) / 1000
    if sp <= 2 * diametro_mm / 1000:
        raise ValueError("la separación del dipolo plegado es demasiado pequeña para ese diámetro")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    n = _segmentos(exc, paso)
    n += 1 - n % 2                                  # impar: la fuente va en el central
    n_v = max(1, round(sp / paso))
    hilos = [
        Hilo((-refl / 2, 0, 0), (refl / 2, 0, 0), r, _segmentos(refl, paso)),                 # 1 reflector
        Hilo((-exc / 2, y1, 0), (exc / 2, y1, 0), r, n),                                         # 2 excitado (alimentado)
        Hilo((-exc / 2, y1, sp), (exc / 2, y1, sp), r, n),                                       # 3 excitado (plegado)
        Hilo((-exc / 2, y1, 0), (-exc / 2, y1, sp), r, n_v),                                     # 4 cierre izquierdo
        Hilo((exc / 2, y1, 0), (exc / 2, y1, sp), r, n_v),                                       # 5 cierre derecho
        Hilo((-dire / 2, y2, 0), (dire / 2, y2, 0), r, _segmentos(dire, paso)),                # 6 director
    ]
    return Modelo("Yagi de 3 elementos", f_MHz, tuple(hilos), Puerto(2, n // 2 + 1), barrido=barrido,
                  comentarios=(f"Yagi de 3 elementos con dipolo plegado a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Reflector {refl * 1000:.1f}, excitado {exc * 1000:.1f}, director {dire * 1000:.1f} mm; "
                               f"separaciones {y1 * 1000:.1f} y {(y2 - y1) * 1000:.1f} mm"))


def biconica_por_defecto(f_min_MHz: float, k_cono: float = 1.0) -> dict[str, float]:
    lam = longitud_onda_m(f_min_MHz) * 1000
    return {"cono_mm": k_cono * lam / 4, "hueco_mm": max(4.0, round(0.004 * lam)), "semiangulo": 35.0, "varillas": 8.0}


def biconica(f_min_MHz: float, diametro_mm: float, cono_mm: float | None = None, hueco_mm: float | None = None,
             semiangulo: float = 35.0, varillas: int = 8, barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Antena bicónica de varillas: dos conos iguales, vértice con vértice (uno hacia arriba y otro hacia abajo), con la
    fuente en el hueco entre los vértices. Banda ancha. Espacio libre."""
    if f_min_MHz <= 0 or diametro_mm <= 0 or varillas < 3:
        raise ValueError("frecuencia y diámetro positivos y al menos 3 varillas")
    p = biconica_por_defecto(f_min_MHz)
    cono = (cono_mm or p["cono_mm"]) / 1000
    g = (hueco_mm or p["hueco_mm"]) / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_min_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    al = math.radians(semiangulo)
    hilos = [Hilo((0, 0, 0), (0, 0, g), r, 1)]
    for signo, z0 in ((1, g), (-1, 0.0)):
        for i in range(varillas):
            a = 2 * math.pi * i / varillas
            fin = (cono * math.sin(al) * math.cos(a), cono * math.sin(al) * math.sin(a), z0 + signo * cono * math.cos(al))
            hilos.append(Hilo((0, 0, z0), fin, r, _segmentos(math.dist((0, 0, z0), fin), paso)))
    return Modelo("Bicónica", f_min_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Biconica de {varillas} varillas, frecuencia minima {f_min_MHz:g} MHz",
                               f"Generatriz {cono * 1000:.1f} mm, hueco {g * 1000:.1f} mm, semiangulo {semiangulo:g} grados"))
