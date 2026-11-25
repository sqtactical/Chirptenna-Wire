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
