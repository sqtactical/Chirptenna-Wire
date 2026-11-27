"""Generadores de antenas: de las entradas del usuario (frecuencia, material) a un `Modelo`.

Python puro (corre en Pyodide): el ajuste con el motor está en `wire/ajuste.py`, que solo se usa en escritorio.
"""

from __future__ import annotations

from . import geometria
import math

from .modelo import Barrido, Carga, Hilo, Linea, Modelo, Puerto, longitud_onda_m

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


BOOMS = ("ninguno", "aislado", "unido")   # eje no metálico; metálico con los elementos pasando aislados; metálico con ellos unidos
B_MAXIMO_EJE = 0.055                      # el diámetro del eje, en λ, hasta donde vale la fórmula de DL6WU


def correccion_eje_mm(f_MHz: float, boom: str, boom_mm: float) -> float:
    """Lo que hay que **añadir** (mm) al largo de cada elemento que atraviesa un eje metálico de `boom_mm` de diámetro.

    Fórmula de DL6WU (G3SEK): por mitad de elemento, c = 12,5975·B − 114,5·B² veces el diámetro del eje, con B = diámetro / λ;
    el elemento entero lleva el doble. Con los elementos pasando aislados del eje vale la mitad. Es una regla empírica de
    la bibliografía para ejes de hasta 0,055 λ, **sin comprobar aquí con medidas**: la hay también con otros valores (25–45 %
    del diámetro en elementos unidos según otros autores) y sube con la frecuencia. Un eje de plástico o madera no corrige."""
    if boom not in BOOMS:
        raise ValueError(f"eje desconocido: {boom} (hay: {', '.join(BOOMS)})")
    if boom == "ninguno":
        return 0.0
    b = boom_mm / (longitud_onda_m(f_MHz) * 1000)
    c = 12.5975 * b - 114.5 * b * b
    return 2 * c * boom_mm * (0.5 if boom == "aislado" else 1.0)
YAGI_SEP_DIRECTORES = (0.15, 0.22, 0.28)  # en λ: el primero cerca del excitado y el resto más abiertos (el último se repite)


def yagi_por_defecto(f_MHz: float, n_elementos: int = 3, boom_mm: float | None = None) -> dict:
    """Cotas de partida de una Yagi de `n_elementos` (reflector, dipolo plegado y n − 2 directores), en mm.

    Los directores bajan 0,01 λ cada uno. Con 3 elementos salen las mismas cotas de siempre (`director_mm`,
    `sep_director_mm` repiten el primer director para los diseños guardados)."""
    if n_elementos < 3:
        raise ValueError("una Yagi necesita al menos 3 elementos")
    lam = longitud_onda_m(f_MHz) * 1000
    directores = [(YAGI_DIRECTOR - 0.01 * k) * lam for k in range(n_elementos - 2)]
    seps = [YAGI_SEP_DIRECTORES[min(k, len(YAGI_SEP_DIRECTORES) - 1)] * lam for k in range(n_elementos - 2)]
    return {"reflector_mm": YAGI_REFLECTOR * lam, "excitado_mm": YAGI_EXCITADO * lam, "director_mm": directores[0],
            "sep_reflector_mm": YAGI_SEP_REFLECTOR * lam, "sep_director_mm": seps[0], "sep_plegado_mm": YAGI_SEP_PLEGADO * lam,
            "n_elementos": float(n_elementos), "directores_mm": directores, "seps_directores_mm": seps,
            "boom": "ninguno", "boom_mm": boom_mm if boom_mm is not None else max(8.0, round(0.01 * lam))}


def yagi(f_MHz: float, diametro_mm: float, reflector_mm: float | None = None, excitado_mm: float | None = None,
         director_mm: float | None = None, sep_reflector_mm: float | None = None, sep_director_mm: float | None = None,
         sep_plegado_mm: float | None = None, barrido: Barrido | None = None, densidad: float = 1.0, *,
         directores_mm: list[float] | None = None, seps_directores_mm: list[float] | None = None, n_elementos: int | None = None) -> Modelo:
    """Yagi de N elementos con el excitado en dipolo plegado (dos alambres paralelos unidos en los extremos), en espacio libre.

    Los elementos van a lo largo de x y el eje (boom) a lo largo de y: reflector en y = 0, el excitado a `sep_reflector_mm`
    y cada director a su separación del anterior. El dipolo plegado tiene su alambre alimentado abajo y el otro a
    `sep_plegado_mm` por encima (eje z); la fuente va en el segmento central del alimentado.

    **El eje no se modela**: un alambre paralelo a y y perpendicular a los elementos, centrado en ellos, no se acopla (con o
    sin los elementos unidos a él la impedancia sale igual al ohmio). El efecto de un eje metálico se aplica aparte, como
    corrección de longitud de corte (`correccion_eje_mm`), que es como se hace en la práctica (DL6WU / G3SEK).
    """
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    if directores_mm is None and director_mm is not None:
        directores_mm = [director_mm]
    if n_elementos is None:
        n_elementos = len(directores_mm) + 2 if directores_mm else 3
    p = yagi_por_defecto(f_MHz, n_elementos)
    dires = [d / 1000 for d in (directores_mm or p["directores_mm"])]
    seps = [s / 1000 for s in (seps_directores_mm or ([sep_director_mm] + p["seps_directores_mm"][1:] if sep_director_mm else p["seps_directores_mm"]))]
    if len(dires) != len(seps) or len(dires) < 1:
        raise ValueError("hace falta un director por cada separación (y al menos uno)")
    refl = (reflector_mm or p["reflector_mm"]) / 1000
    exc = (excitado_mm or p["excitado_mm"]) / 1000
    y1 = (sep_reflector_mm or p["sep_reflector_mm"]) / 1000
    sp = (sep_plegado_mm or p["sep_plegado_mm"]) / 1000
    if sp <= 2 * diametro_mm / 1000:
        raise ValueError(f"la separación del dipolo plegado es demasiado pequeña para ese diámetro: a {f_MHz:g} MHz usa "
                         f"un alambre de menos de {sp * 500:.1f} mm")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    ys = [0.0, y1]
    for s in seps:
        ys.append(ys[-1] + s)
    n = _segmentos(exc, paso)
    n += 1 - n % 2                                  # impar: la fuente va en el central
    n_v = max(1, round(sp / paso))
    hilos: list[Hilo] = [Hilo((-refl / 2, 0, 0), (refl / 2, 0, 0), r, _segmentos(refl, paso)),      # reflector
                         Hilo((-exc / 2, y1, 0), (exc / 2, y1, 0), r, n),                           # excitado (alimentado)
                         Hilo((-exc / 2, y1, sp), (exc / 2, y1, sp), r, n),                         # excitado (plegado)
                         Hilo((-exc / 2, y1, 0), (-exc / 2, y1, sp), r, n_v),                       # cierre izquierdo
                         Hilo((exc / 2, y1, 0), (exc / 2, y1, sp), r, n_v)]                         # cierre derecho
    for d, y in zip(dires, ys[2:]):
        hilos.append(Hilo((-d / 2, y, 0), (d / 2, y, 0), r, _segmentos(d, paso)))
    return Modelo(f"Yagi de {len(dires) + 2} elementos", f_MHz, tuple(hilos), Puerto(2, n // 2 + 1), barrido=barrido,
                  comentarios=(f"Yagi de {len(dires) + 2} elementos con dipolo plegado a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Reflector {refl * 1000:.1f}, excitado {exc * 1000:.1f}, directores "
                               + ", ".join(f"{d * 1000:.1f}" for d in dires) + " mm; separaciones "
                               + ", ".join(f"{(b - a) * 1000:.1f}" for a, b in zip(ys, ys[1:])) + " mm"))


# ---------------------------------------------------------------- Moxon rectangular

# Cotas de partida en λ (optimizadas con PyNEC a 145 MHz, alambre de 2 mm, hacia delante = +y): ancho, puntas del excitado y del
# reflector y hueco entre puntas. El hueco central del excitado (donde va el coaxial) es 0,0097 λ.
MOXON_X = {"ancho": 0.3617, "punta_excitado": 0.055, "punta_reflector": 0.0724, "hueco": 0.049, "centro": 0.0097}


def moxon_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"ancho_mm": MOXON_X["ancho"] * lam, "punta_excitado_mm": MOXON_X["punta_excitado"] * lam,
            "punta_reflector_mm": MOXON_X["punta_reflector"] * lam, "hueco_mm": MOXON_X["hueco"] * lam,
            "centro_mm": max(6.0, MOXON_X["centro"] * lam)}


def moxon(f_MHz: float, diametro_mm: float, ancho_mm: float | None = None, punta_excitado_mm: float | None = None,
          punta_reflector_mm: float | None = None, hueco_mm: float | None = None, centro_mm: float | None = None,
          barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Moxon rectangular de alambre: un rectángulo abierto por delante con el excitado en el lado de delante (y = 0) y el
    reflector detrás, con las puntas de los dos dobladas una hacia la otra (`hueco_mm` entre ellas). Alimentación en el centro del
    excitado (hueco de `centro_mm`). El haz sale hacia +y. Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = moxon_por_defecto(f_MHz)
    a = (ancho_mm or p["ancho_mm"]) / 1000
    td = (punta_excitado_mm or p["punta_excitado_mm"]) / 1000
    tr_ = (punta_reflector_mm or p["punta_reflector_mm"]) / 1000
    g = (hueco_mm or p["hueco_mm"]) / 1000
    c = (centro_mm or p["centro_mm"]) / 1000
    if min(a, td, tr_, g) <= 0 or c >= a:
        raise ValueError("las cotas de la Moxon deben ser positivas y el hueco central menor que el ancho")
    r = diametro_mm / 2000
    if g <= 3 * r:
        raise ValueError("el hueco entre las puntas es demasiado pequeño para ese diámetro")
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    y_r = -(td + g + tr_)
    hilos = [Hilo((-c / 2, 0, 0), (c / 2, 0, 0), r, 1)]                                   # el punto de alimentación
    for s in (1, -1):
        hilos.append(Hilo((s * c / 2, 0, 0), (s * a / 2, 0, 0), r, _segmentos(a / 2 - c / 2, paso)))      # excitado
        hilos.append(Hilo((s * a / 2, 0, 0), (s * a / 2, -td, 0), r, _segmentos(td, paso)))              # punta del excitado
        hilos.append(Hilo((s * a / 2, y_r, 0), (s * a / 2, y_r + tr_, 0), r, _segmentos(tr_, paso)))     # punta del reflector
    hilos.append(Hilo((-a / 2, y_r, 0), (a / 2, y_r, 0), r, _segmentos(a, paso)))                         # reflector
    return Modelo("Moxon", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Moxon rectangular a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Ancho {a * 1000:.1f}, puntas {td * 1000:.1f} y {tr_ * 1000:.1f}, hueco {g * 1000:.1f} mm"))


# ---------------------------------------------------------------- Quad cúbica de dos elementos

# Cotas de partida en λ (optimizadas con PyNEC a 145 MHz, alambre de 2 mm, hacia delante = +y): lado del lazo excitado, lado del
# reflector, separación entre lazos y hueco central de la fuente (en el lado de abajo del excitado).
QUAD_X = {"lado_excitado": 0.2546, "lado_reflector": 0.2641, "separacion": 0.148, "centro": 0.0097}


def quad_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"lado_excitado_mm": QUAD_X["lado_excitado"] * lam, "lado_reflector_mm": QUAD_X["lado_reflector"] * lam,
            "separacion_mm": QUAD_X["separacion"] * lam, "centro_mm": max(6.0, QUAD_X["centro"] * lam)}


def quad(f_MHz: float, diametro_mm: float, lado_excitado_mm: float | None = None, lado_reflector_mm: float | None = None,
         separacion_mm: float | None = None, centro_mm: float | None = None, barrido: Barrido | None = None,
         densidad: float = 1.0) -> Modelo:
    """Quad cúbica de dos elementos: dos lazos cuadrados de alambre en planos verticales (x–z) paralelos, el excitado en y = 0
    con la fuente en el centro del lado de abajo (polarización horizontal) y el reflector (algo mayor) a `separacion_mm` por detrás.
    El haz sale hacia +y. Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = quad_por_defecto(f_MHz)
    le = (lado_excitado_mm or p["lado_excitado_mm"]) / 1000
    lr = (lado_reflector_mm or p["lado_reflector_mm"]) / 1000
    s = (separacion_mm or p["separacion_mm"]) / 1000
    c = (centro_mm or p["centro_mm"]) / 1000
    if min(le, lr, s) <= 0 or c >= le:
        raise ValueError("las cotas de la quad deben ser positivas y el hueco central menor que el lado")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad

    def tramo(a, b) -> Hilo:
        return Hilo(a, b, r, _segmentos(math.dist(a, b), paso))

    a, b = le / 2, lr / 2
    z0 = (le - lr) / 2                                            # el reflector queda centrado sobre el excitado
    hilos = [Hilo((-c / 2, 0, 0), (c / 2, 0, 0), r, 1),          # el punto de alimentación
             tramo((c / 2, 0, 0), (a, 0, 0)), tramo((a, 0, 0), (a, 0, le)), tramo((a, 0, le), (-a, 0, le)),
             tramo((-a, 0, le), (-a, 0, 0)), tramo((-a, 0, 0), (-c / 2, 0, 0)),
             tramo((-b, -s, z0), (b, -s, z0)), tramo((b, -s, z0), (b, -s, z0 + lr)),
             tramo((b, -s, z0 + lr), (-b, -s, z0 + lr)), tramo((-b, -s, z0 + lr), (-b, -s, z0))]
    return Modelo("Quad", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Quad cubica de 2 elementos a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Lados {le * 1000:.1f} y {lr * 1000:.1f} mm, separacion {s * 1000:.1f} mm"))


# ---------------------------------------------------------------- Delta loop

# Cotas de partida en λ (optimizadas con PyNEC a 145 MHz, alambre de 2 mm): base y altura del triángulo (perímetro ≈ 1,1 λ) y
# hueco central de la fuente, en el centro de la base.
DELTA_X = {"base": 0.28, "alto": 0.385, "centro": 0.0097}


def delta_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"base_mm": DELTA_X["base"] * lam, "alto_mm": DELTA_X["alto"] * lam, "centro_mm": max(6.0, DELTA_X["centro"] * lam)}


def delta(f_MHz: float, diametro_mm: float, base_mm: float | None = None, alto_mm: float | None = None,
          centro_mm: float | None = None, barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Delta loop: lazo triangular de alambre en un plano vertical (x–z), con la base horizontal abajo, el vértice arriba y la
    fuente en el centro de la base (polarización horizontal). Radia hacia los dos lados del plano del lazo (±y). Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = delta_por_defecto(f_MHz)
    b = (base_mm or p["base_mm"]) / 1000
    h = (alto_mm or p["alto_mm"]) / 1000
    c = (centro_mm or p["centro_mm"]) / 1000
    if min(b, h) <= 0 or c >= b:
        raise ValueError("la base y la altura deben ser positivas y el hueco central menor que la base")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    izq, der, vert = (-b / 2, 0, 0), (b / 2, 0, 0), (0, 0, h)

    def tramo(a, c2) -> Hilo:
        return Hilo(a, c2, r, _segmentos(math.dist(a, c2), paso))

    hilos = (Hilo((-c / 2, 0, 0), (c / 2, 0, 0), r, 1), tramo((c / 2, 0, 0), der), tramo(der, vert), tramo(vert, izq), tramo(izq, (-c / 2, 0, 0)))
    return Modelo("Delta loop", f_MHz, hilos, Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Delta loop a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Base {b * 1000:.1f} mm, altura {h * 1000:.1f} mm, perimetro {(b + 2 * math.hypot(b / 2, h)) * 1000:.1f} mm"))


# ---------------------------------------------------------------- Cuatro dipolos apilados en fase

APIL_N = 4
APIL_Z0, APIL_VF = 75.0, 0.66            # las líneas de fase: coaxial de 75 Ω con aislante de PE
# Cotas de partida en λ (optimizadas con PyNEC a 145 MHz, alambre de 2 mm): largo de cada dipolo, separación vertical entre
# dipolos y largo físico de cada línea de fase (iguales: del punto de unión al centro de cada dipolo).
APIL_X = {"dipolo": 0.464, "separacion": 0.57, "linea": 0.901}


def apilados_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"dipolo_mm": APIL_X["dipolo"] * lam, "separacion_mm": APIL_X["separacion"] * lam, "linea_mm": APIL_X["linea"] * lam,
            "n_dipolos": float(APIL_N), "z0_linea": APIL_Z0, "vf_linea": APIL_VF}


def apilados(f_MHz: float, diametro_mm: float, dipolo_mm: float | None = None, separacion_mm: float | None = None,
             linea_mm: float | None = None, n_dipolos: float = APIL_N, z0_linea: float = APIL_Z0, vf_linea: float = APIL_VF,
             barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """`n_dipolos` dipolos horizontales (eje x) apilados en vertical (z) y alimentados en fase desde un punto común, cada uno por
    una línea de `linea_mm` (todas iguales, Z0 `z0_linea`). Radia en el plano perpendicular a los dipolos (±y), con ≈ 4 dB más que un
    dipolo por cada duplicación. Espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = apilados_por_defecto(f_MHz)
    largo = (dipolo_mm or p["dipolo_mm"]) / 1000
    sep = (separacion_mm or p["separacion_mm"]) / 1000
    lin = (linea_mm or p["linea_mm"]) / 1000
    n = int(n_dipolos)
    if n < 2:
        raise ValueError("hacen falta al menos dos dipolos")
    if lin < (n - 1) / 2 * sep:
        raise ValueError("las líneas de fase no llegan del punto de unión al dipolo más lejano: alárgalas o acerca los dipolos")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    seg = _segmentos(largo, paso)
    seg += 1 - seg % 2                                              # impar: la línea llega al segmento central
    hilos = [Hilo((-largo / 2, 0, (k - (n - 1) / 2) * sep), (largo / 2, 0, (k - (n - 1) / 2) * sep), r, seg) for k in range(n)]
    hilos.append(Hilo((0, 0, -0.01), (0, 0, 0.01), r, 1))          # el punto de alimentación, en el centro del apilado
    lineas = tuple(Linea(n + 1, 1, k + 1, seg // 2 + 1, z0_linea, lin, vf_linea) for k in range(n))
    return Modelo("Dipolos apilados", f_MHz, tuple(hilos), Puerto(n + 1, 1), lineas=lineas, barrido=barrido,
                  comentarios=(f"{n} dipolos apilados en fase a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Dipolos de {largo * 1000:.1f} mm separados {sep * 1000:.1f} mm, lineas de {lin * 1000:.1f} mm ({z0_linea:g} ohm, VF {vf_linea:g})"))


# ---------------------------------------------------------------- Yagi de dos bandas (145 / 433 MHz) con el excitado en abanico

YAGIB_RAZON = 433.0 / 145.0              # banda alta / banda baja (las cotas de partida están optimizadas para 145 y 433 MHz)
YAGIB_F_RANGO = (100.0, 250.0)           # banda baja (MHz) en la que tiene sentido escalar las cotas
YAGIB_DZ_MM = 25.0                       # separación entre los dos dipolos (de 15 a 35 mm apenas cambia nada)
# Cotas optimizadas con PyNEC (espacio libre, alambre de 2 mm; herramientas/yagi_bibanda_abanico.py): largo de los dipolos y
# reflectores y posiciones de los directores en λ de su banda (la posición del excitado, en λ de la baja).
YAGIB_X = {"dipolo_bajo": 0.4858, "dipolo_alto": 0.2844, "y_excitado": 0.2385, "director_bajo": 0.4155, "directores_altos": 0.4651,
           "reflector_bajo": 0.6578, "reflector_alto": 0.6389, "sep_director_bajo": 0.0983, "sep_director_alto": 0.1634}
YAGIB_GANANCIA_MIN = 5.0


def yagi_bibanda_por_defecto(f_baja: float) -> dict:
    """Cotas de partida (mm) de la Yagi de dos bandas: la banda alta es `f_baja` × 433 / 145 (la razón para la que están
    optimizadas). Reflectores y directores de las dos bandas en un mismo eje (y = 0 en el reflector de la banda baja)."""
    if not YAGIB_F_RANGO[0] <= f_baja <= YAGIB_F_RANGO[1]:
        raise ValueError(f"la Yagi bibanda está calculada para una banda baja de {YAGIB_F_RANGO[0]:g} a {YAGIB_F_RANGO[1]:g} MHz (145 y 433 MHz)")
    f_alta = f_baja * YAGIB_RAZON
    lb, la = 299792.458 / f_baja, 299792.458 / f_alta
    x = YAGIB_X
    y1 = x["y_excitado"] * lb
    return {"f_alta_MHz": f_alta, "dipolo_bajo_mm": x["dipolo_bajo"] * lb, "dipolo_alto_mm": x["dipolo_alto"] * la,
            "sep_dipolos_mm": YAGIB_DZ_MM, "y_excitado_mm": y1,
            "reflector_bajo_mm": x["reflector_bajo"] * lb, "reflector_alto_mm": x["reflector_alto"] * la,
            "director_bajo_mm": x["director_bajo"] * lb, "y_director_bajo_mm": y1 + x["sep_director_bajo"] * lb,
            "directores_altos_mm": [x["directores_altos"] * la, 0.98 * x["directores_altos"] * la],
            "ys_directores_altos_mm": [y1 + x["sep_director_alto"] * la, y1 + 2 * x["sep_director_alto"] * la]}


def yagi_bibanda(f_baja: float, diametro_mm: float, *, dipolo_bajo_mm: float | None = None, dipolo_alto_mm: float | None = None,
                 sep_dipolos_mm: float | None = None, y_excitado_mm: float | None = None, reflector_bajo_mm: float | None = None,
                 reflector_alto_mm: float | None = None, director_bajo_mm: float | None = None, y_director_bajo_mm: float | None = None,
                 directores_altos_mm: list[float] | None = None, ys_directores_altos_mm: list[float] | None = None,
                 barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Yagi de dos bandas con un solo coaxial: dos dipolos simples desde el mismo punto de alimentación (el de la banda alta
    `sep_dipolos_mm` más arriba, en z), un reflector y un director de la banda baja y un reflector y dos directores de la alta,
    todos en el mismo eje (y). Espacio libre. Los elementos van a lo largo de x y el excitado está en y = `y_excitado_mm`."""
    if diametro_mm <= 0:
        raise ValueError("el diámetro debe ser positivo")
    p = yagi_bibanda_por_defecto(f_baja)
    v = lambda dado, clave: (p[clave] if dado is None else dado)       # noqa: E731
    lb_mm, la_mm = v(dipolo_bajo_mm, "dipolo_bajo_mm"), v(dipolo_alto_mm, "dipolo_alto_mm")
    dz = v(sep_dipolos_mm, "sep_dipolos_mm") / 1000
    y1 = v(y_excitado_mm, "y_excitado_mm") / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_baja * YAGIB_RAZON) / SEGMENTOS_POR_LAMBDA / densidad     # el de la banda alta, que es la más fina
    if dz <= 3 * r:
        raise ValueError("los dos dipolos quedan demasiado juntos para ese diámetro")

    def pasivo(largo_mm: float, y: float, z: float = 0.0) -> Hilo:
        return Hilo((-largo_mm / 2000, y, z), (largo_mm / 2000, y, z), r, max(5, round(largo_mm / 1000 / paso)))

    hueco = 0.02
    hilos = [Hilo((-hueco / 2, y1, 0), (hueco / 2, y1, 0), r, 1)]                                  # el punto de alimentación
    for lado in (1, -1):
        for largo, z in ((lb_mm, 0.0), (la_mm, dz)):
            ini, fin = (lado * hueco / 2, y1, 0), (lado * largo / 2000, y1, z)
            hilos.append(Hilo(ini, fin, r, max(5, round(math.dist(ini, fin) / paso))))
    hilos.append(pasivo(v(reflector_bajo_mm, "reflector_bajo_mm"), 0.0))
    hilos.append(pasivo(v(reflector_alto_mm, "reflector_alto_mm"), 0.0, dz))
    hilos.append(pasivo(v(director_bajo_mm, "director_bajo_mm"), v(y_director_bajo_mm, "y_director_bajo_mm") / 1000))
    for largo, y in zip(v(directores_altos_mm, "directores_altos_mm"), v(ys_directores_altos_mm, "ys_directores_altos_mm")):
        hilos.append(pasivo(largo, y / 1000, dz))
    return Modelo("Yagi de dos bandas", f_baja, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Yagi de dos bandas ({f_baja:g} y {f_baja * YAGIB_RAZON:.0f} MHz) con el excitado en abanico, alambre de {diametro_mm:g} mm",
                               f"Dipolos {lb_mm:.1f} y {la_mm:.1f} mm separados {dz * 1000:.0f} mm; excitado a {y1 * 1000:.1f} mm del reflector"))


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


# ---------------------------------------------------------------- HF: EFHW con transformador

BANDAS_HF = (("160 m", 1.8, 2.0), ("80 m", 3.5, 3.8), ("60 m", 5.3515, 5.3665), ("40 m", 7.0, 7.2), ("30 m", 10.1, 10.15),
             ("20 m", 14.0, 14.35), ("17 m", 18.068, 18.168), ("15 m", 21.0, 21.45), ("12 m", 24.89, 24.99), ("10 m", 28.0, 29.7))
# Suelo real (εr, conductividad en S/m): los valores típicos de NEC y del ARRL, **sin medir en tu terreno**.
SUELOS = {"pobre": (5.0, 0.001), "normal": (13.0, 0.005), "bueno": (20.0, 0.03), "mar": (80.0, 5.0)}
RELACIONES = (9, 49, 64)                    # relación de impedancias del transformador (9:1 = 3:1 en vueltas, 49:1 = 7:1, 64:1 = 8:1)
EFHW_LARGO, EFHW_CONTRAPESO = 0.475, 0.06   # en λ de la banda más baja


def bandas_de(f_MHz: float, relacion: int) -> list[tuple[str, float, float]]:
    """Bandas donde se mide una EFHW pensada para `f_MHz`: la propia y sus armónicos (49:1 y 64:1, que solo funcionan en múltiplos
    de media onda) o todas las de HF por encima (9:1, de hilo no resonante)."""
    sal = []
    for nombre, a, b in BANDAS_HF:
        c = (a + b) / 2
        if a <= f_MHz <= b or (relacion != 9 and any(abs(c / (n * f_MHz) - 1) < 0.045 for n in (2, 3, 4, 5)) or (relacion == 9 and c >= f_MHz * 0.9)):
            sal.append((nombre, a, b))
    return sal


def efhw_por_defecto(f_MHz: float, relacion: int = 49, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    lam = 299.792458 / f_MHz
    return {"largo_mm": EFHW_LARGO * lam * 1000, "contrapeso_mm": EFHW_CONTRAPESO * lam * 1000, "altura_mm": altura_m * 1000,
            "relacion": float(relacion), "suelo": suelo}


def efhw(f_MHz: float, diametro_mm: float, largo_mm: float | None = None, contrapeso_mm: float | None = None,
         altura_mm: float = 10000.0, suelo: str = "normal", relacion: int = 49, barrido: Barrido | None = None,
         densidad: float = 1.0) -> Modelo:
    """Hilo horizontal alimentado por un extremo (EFHW) a `altura_mm` sobre suelo real, con un contrapeso corto.

    La fuente está en el primer segmento del hilo; la impedancia que sale es la del extremo (miles de ohmios). El
    transformador (`relacion`: 49 = 49:1…) **no está en el modelo**: se simula la antena y la ROE se calcula contra
    50 Ω × `relacion` (`motor.simular(..., z0=...)`), es decir, con un transformador ideal, sin pérdidas ni parásitos."""
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    if suelo not in SUELOS:
        raise ValueError(f"suelo desconocido: {suelo} (hay: {', '.join(SUELOS)})")
    if relacion not in RELACIONES:
        raise ValueError(f"relación desconocida: {relacion}:1 (hay: {', '.join(str(r) for r in RELACIONES)})")
    p = efhw_por_defecto(f_MHz, relacion, altura_mm / 1000, suelo)
    largo = (largo_mm or p["largo_mm"]) / 1000
    cp = (contrapeso_mm if contrapeso_mm is not None else p["contrapeso_mm"]) / 1000
    h = altura_mm / 1000
    if h <= 1.0:
        raise ValueError("la altura debe ser de más de 1 m")
    r = diametro_mm / 2000
    paso = 299.792458 / min(4 * f_MHz, 30.0) / SEGMENTOS_POR_LAMBDA / densidad
    hilos = [Hilo((0, 0, h), (largo, 0, h), r, max(3, round(largo / paso)))]
    if cp > 0.05:
        hilos.append(Hilo((0, 0, h), (-cp, 0, h), r, max(1, round(cp / paso))))
    return Modelo(f"EFHW {relacion}:1", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"EFHW {relacion}:1 a {f_MHz:g} MHz, hilo de {diametro_mm:g} mm a {h:g} m sobre suelo {suelo}",
                               f"Hilo de {largo:.2f} m, contrapeso de {cp:.2f} m; la ROE va contra {50 * relacion} ohm (transformador ideal)"))


# ---------------------------------------------------------------- colineal con bobinas de fase (VHF/UHF)

COL_SECCIONES = (2, 3, 4, 5, 6)
COL_HUECO_MM = 10.0                     # el modelo concentra cada bobina en un tramo de 10 mm
# Cotas de partida en λ a 145 MHz (salen de ajustar a 50 Ω con el motor); la bobina escala con 1/f (misma reactancia)
COL_BASE = {2: ([0.253, 0.467], 0.78, 0.259), 3: ([0.265, 0.517, 0.537], 1.1, 0.211), 4: ([0.265, 0.517, 0.537, 0.537], 1.1, 0.211),
            5: ([0.265, 0.517, 0.537, 0.537, 0.537], 1.1, 0.211), 6: ([0.265, 0.517, 0.537, 0.537, 0.537, 0.537], 1.1, 0.211)}
COL_GANANCIA_MIN = {2: 3.0, 3: 4.5, 4: 5.5, 5: 6.2, 6: 6.8}   # dBi (espacio libre) que pide el ajuste, además de 50 Ω


def colineal_por_defecto(f_MHz: float, secciones: int = 3) -> dict:
    if secciones not in COL_SECCIONES:
        raise ValueError("la colineal lleva de 2 a 6 secciones")
    lam = longitud_onda_m(f_MHz) * 1000
    largos, bobina, radial = COL_BASE[secciones]
    return {"secciones_mm": [v * lam for v in largos], "bobina_uH": bobina * 145.0 / f_MHz, "radial_mm": radial * lam,
            "n_secciones": float(secciones), "angulo": GP_ANGULO, "radiales": float(GP_RADIALES)}


def colineal(f_MHz: float, diametro_mm: float, secciones_mm: list[float] | None = None, bobina_uH: float | None = None,
             radial_mm: float | None = None, angulo: float = GP_ANGULO, radiales: int = GP_RADIALES,
             barrido: Barrido | None = None, densidad: float = 1.0, condensador_pF: float | None = None,
             f_alta_MHz: float | None = None, altura_mm: float | None = None, suelo: str | None = None) -> Modelo:
    """Colineal vertical de `n` secciones con una bobina de fase (inductancia en serie) entre cada dos, sobre `radiales`
    radiales como un ground plane. La bobina hace que la corriente de la sección de arriba vaya en fase con la de abajo
    (sin ella, media onda sobre media onda se anularían en el horizonte). La fuente va en la base. Espacio libre.

    Con `condensador_pF` cada bobina lleva un condensador **en serie**: resonante a `f_MHz` (la banda baja) el enlace no hace
    nada, y en `f_alta_MHz` queda una reactancia inductiva que sí invierte la fase (colineal bibanda).

    Con `altura_mm` y `suelo` la base de la antena (la unión con los radiales) va a esa altura sobre suelo real; sin ellos,
    espacio libre."""
    if f_MHz <= 0 or diametro_mm <= 0 or radiales < 2:
        raise ValueError("frecuencia y diámetro positivos y al menos 2 radiales")
    if (altura_mm is None) != (suelo is None):
        raise ValueError("la altura y el suelo van juntos: o los dos o ninguno (espacio libre)")
    if suelo is not None and suelo not in SUELOS:
        raise ValueError(f"suelo desconocido: {suelo} (hay: {', '.join(SUELOS)})")
    p = colineal_por_defecto(f_MHz, len(secciones_mm) if secciones_mm else 3)
    largos = [v / 1000 for v in (secciones_mm or p["secciones_mm"])]
    if not 2 <= len(largos) <= 6 or min(largos) <= 0:
        raise ValueError("la colineal lleva de 2 a 6 secciones de largo positivo")
    lb = (bobina_uH if bobina_uH is not None else p["bobina_uH"]) * 1e-6
    rl = (radial_mm or p["radial_mm"]) / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(max(f_MHz, f_alta_MHz or 0.0)) / SEGMENTOS_POR_LAMBDA / densidad
    hilos: list[Hilo] = []
    cargas: list[Carga] = []
    z0 = (altura_mm or 0.0) / 1000                      # la base sobre el suelo (0 en espacio libre: el origen)
    if suelo is not None and z0 - rl * math.sin(math.radians(angulo)) < 0.3:
        raise ValueError("los radiales quedan a menos de 0,3 m del suelo: sube la base de la antena")
    z = z0
    for i, largo in enumerate(largos):
        hilos.append(Hilo((0, 0, z), (0, 0, z + largo), r, _segmentos(largo, paso)))
        z += largo
        if i < len(largos) - 1:
            hilos.append(Hilo((0, 0, z), (0, 0, z + COL_HUECO_MM / 1000), r, 1))
            cargas.append(Carga(len(hilos), 1, 1, l=lb, c=(condensador_pF or 0.0) * 1e-12))
            z += COL_HUECO_MM / 1000
    c, s = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
    for i in range(radiales):
        a = 2 * math.pi * i / radiales
        hilos.append(Hilo((0, 0, z0), (rl * c * math.cos(a), rl * c * math.sin(a), z0 - rl * s), r, _segmentos(rl, paso)))
    donde = f", base a {z0:g} m sobre suelo {suelo}" if suelo is not None else ""
    return Modelo("Colineal con bobinas de fase", f_MHz, tuple(hilos), Puerto(1, 1), cargas=tuple(cargas), barrido=barrido,
                  suelo=SUELOS[suelo] if suelo is not None else None,
                  comentarios=(f"Colineal de {len(largos)} secciones a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm{donde}",
                               "Secciones " + ", ".join(f"{v * 1000:.1f}" for v in largos) + f" mm; bobinas de {lb * 1e6:.2f} uH",
                               f"{radiales} radiales de {rl * 1000:.1f} mm a {angulo:g} grados"))


# Colineal bibanda 145 / 433 MHz: enlaces L-C en serie, resonantes en la banda baja (transparentes) e inductivos en la alta.
# Cotas de partida en λ de la banda alta, bobina a f_alta = 433 MHz y C a f_baja = 145 MHz (salen de ajustar a 50 Ω en las dos bandas).
COLB_SECCIONES = (2, 4)               # con 3 el conjunto mide ≈ λ/2 en la banda baja (alimentado por el extremo: no adapta)
COLB_RAZON = (2.5, 3.5)               # f_alta / f_baja simulada
COLB_BASE = {2: ([0.272, 0.579], 0.40, 3.77, 0.209), 4: ([0.261, 0.529, 0.63, 0.59], 0.46, 3.86, 0.198)}
COLB_GANANCIA_MIN = {2: 3.0, 4: 4.5}  # dBi en la banda alta (espacio libre)


def colineal_bibanda_por_defecto(f_baja: float, f_alta: float, secciones: int = 4) -> dict:
    if secciones not in COLB_SECCIONES:
        raise ValueError("la colineal bibanda lleva 2 o 4 secciones")
    if not COLB_RAZON[0] <= f_alta / f_baja <= COLB_RAZON[1]:
        raise ValueError("la banda alta debe ser de 2,5 a 3,5 veces la baja (145 y 433 MHz, por ejemplo)")
    lam = longitud_onda_m(f_alta) * 1000
    largos, bobina, cond, radial = COLB_BASE[secciones]
    return {"secciones_mm": [v * lam for v in largos], "bobina_uH": bobina * 433.0 / f_alta,
            "condensador_pF": cond * (f_alta / 433.0) * (145.0 / f_baja) ** 2,
            "radial_mm": radial * lam, "n_secciones": float(secciones), "angulo": GP_ANGULO, "radiales": float(GP_RADIALES),
            "f_alta_MHz": f_alta}


def colineal_bibanda(f_baja: float, f_alta: float, diametro_mm: float, secciones_mm: list[float] | None = None,
                     bobina_uH: float | None = None, condensador_pF: float | None = None, radial_mm: float | None = None,
                     angulo: float = GP_ANGULO, radiales: int = GP_RADIALES, barrido: Barrido | None = None,
                     densidad: float = 1.0, altura_mm: float | None = None, suelo: str | None = None) -> Modelo:
    """Colineal de `n` secciones con enlaces L-C en serie: resonantes a `f_baja` (no hacen nada: la antena es un ¼ o 5/8 de
    onda) e inductivos a `f_alta` (invierten la fase y apilan las medias ondas). Espacio libre, componentes ideales."""
    p = colineal_bibanda_por_defecto(f_baja, f_alta, len(secciones_mm) if secciones_mm else 4)
    return colineal(f_baja, diametro_mm, secciones_mm or p["secciones_mm"], bobina_uH if bobina_uH is not None else p["bobina_uH"],
                    radial_mm or p["radial_mm"], angulo, radiales, barrido, densidad,
                    condensador_pF=condensador_pF if condensador_pF is not None else p["condensador_pF"], f_alta_MHz=f_alta,
                    altura_mm=altura_mm, suelo=suelo)


# ---------------------------------------------------------------- HF: dipolos sobre suelo real

TIPOS_HF = ("efhw", "dipolo_hf", "vinv_hf", "abanico", "trampas", "g5rv", "vertical_hf")
DIPOLO_HF_LARGO, VINV_HF_BRAZO, VINV_HF_APERTURA = 0.475, 0.235, 110.0   # en λ (largo total, cada brazo) y grados
ABANICO_SEP_MM = 300.0                                                    # separación vertical entre los hilos de dos bandas
TRAMPA_LARGO_MM, TRAMPA_Z_OHM, TRAMPA_Q = 100.0, 330.0, 100.0           # largo físico de la bobina, X de L y C, Q de la trampa
G5RV_FACTOR, G5RV_ESCALERILLA_Z, G5RV_ESCALERILLA_VF = 31.1, 450.0, 0.88  # m del dipolo en 80 m; línea abierta de 450 Ω


def banda_hf(f_MHz: float) -> tuple[str, float, float]:
    """La banda de HF que contiene a `f_MHz`, o una banda de ±1 % alrededor si no cae en ninguna."""
    for b in BANDAS_HF:
        if b[1] <= f_MHz <= b[2]:
            return b
    return (f"{f_MHz:g} MHz", f_MHz * 0.99, f_MHz * 1.01)


def banda_por_nombre(nombre: str) -> tuple[str, float, float]:
    for b in BANDAS_HF:
        if b[0] == nombre:
            return b
    raise ValueError(f"banda desconocida: {nombre} (hay: {', '.join(b[0] for b in BANDAS_HF)})")


def _paso_hf(f_MHz: float, factor: float = 2.2) -> float:
    return 299.792458 / min(factor * f_MHz, 30.0) / SEGMENTOS_POR_LAMBDA


def _comprobar_hf(f_MHz: float, diametro_mm: float, altura_mm: float, suelo: str) -> None:
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    if suelo not in SUELOS:
        raise ValueError(f"suelo desconocido: {suelo} (hay: {', '.join(SUELOS)})")
    if altura_mm <= 1000:
        raise ValueError("la altura debe ser de más de 1 m")


def dipolo_hf_por_defecto(f_MHz: float, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    return {"largo_mm": DIPOLO_HF_LARGO * 299792.458 / f_MHz, "altura_mm": altura_m * 1000, "suelo": suelo}


def dipolo_hf(f_MHz: float, diametro_mm: float, largo_mm: float | None = None, altura_mm: float = 10000.0, suelo: str = "normal",
              barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Dipolo horizontal de media onda a `altura_mm` sobre suelo real; la fuente en el segmento central."""
    _comprobar_hf(f_MHz, diametro_mm, altura_mm, suelo)
    largo = (largo_mm or dipolo_hf_por_defecto(f_MHz)["largo_mm"]) / 1000
    h = altura_mm / 1000
    n = max(3, round(largo / (_paso_hf(f_MHz) / densidad)))
    n += 1 - n % 2
    return Modelo("Dipolo de HF", f_MHz, (Hilo((-largo / 2, 0, h), (largo / 2, 0, h), diametro_mm / 2000, n),), Puerto(1, n // 2 + 1),
                  barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"Dipolo de HF a {f_MHz:g} MHz, hilo de {diametro_mm:g} mm a {h:g} m sobre suelo {suelo}", f"Largo total {largo:.2f} m"))


def vinv_hf_por_defecto(f_MHz: float, altura_m: float = 12.0, suelo: str = "normal") -> dict:
    return {"brazo_mm": VINV_HF_BRAZO * 299792.458 / f_MHz, "apertura": VINV_HF_APERTURA, "altura_mm": altura_m * 1000, "suelo": suelo}


def vinv_hf(f_MHz: float, diametro_mm: float, brazo_mm: float | None = None, apertura: float = VINV_HF_APERTURA,
            altura_mm: float = 12000.0, suelo: str = "normal", barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """V invertida con el vértice a `altura_mm` sobre suelo real y los brazos caídos `apertura` grados entre sí."""
    _comprobar_hf(f_MHz, diametro_mm, altura_mm, suelo)
    if not 30 <= apertura <= 180:
        raise ValueError("la apertura debe estar entre 30° y 180°")
    brazo = (brazo_mm or vinv_hf_por_defecto(f_MHz)["brazo_mm"]) / 1000
    h, m = altura_mm / 1000, math.radians(apertura / 2)
    if h - brazo * math.cos(m) < 1.0:
        raise ValueError("los extremos de la V quedan a menos de 1 m del suelo: sube el vértice o cierra la apertura")
    n = max(2, round(brazo / (_paso_hf(f_MHz) / densidad)))
    r = diametro_mm / 2000
    hilos = (Hilo((0, 0, h), (brazo * math.sin(m), 0, h - brazo * math.cos(m)), r, n),
             Hilo((0, 0, h), (-brazo * math.sin(m), 0, h - brazo * math.cos(m)), r, n))
    return Modelo("V invertida de HF", f_MHz, hilos, Puerto(1, 1), barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"V invertida de HF a {f_MHz:g} MHz, hilo de {diametro_mm:g} mm, vértice a {h:g} m sobre suelo {suelo}",
                               f"Brazos de {brazo:.2f} m, apertura {apertura:g} grados"))


VERT_RADIADOR, VERT_RADIAL, VERT_RADIALES = 0.245, 0.25, 8             # en λ (radiador, cada radial) y número de radiales
VERT_ALTURA_M = 2.0                                                       # altura de los radiales sobre el suelo (m)


def vertical_hf_por_defecto(f_MHz: float, altura_m: float = VERT_ALTURA_M, suelo: str = "normal") -> dict:
    lam = 299792.458 / f_MHz
    return {"radiador_mm": VERT_RADIADOR * lam, "radial_mm": VERT_RADIAL * lam, "radiales": float(VERT_RADIALES),
            "altura_mm": altura_m * 1000, "suelo": suelo}


def vertical_hf(f_MHz: float, diametro_mm: float, radiador_mm: float | None = None, radial_mm: float | None = None,
                radiales: int = VERT_RADIALES, altura_mm: float = VERT_ALTURA_M * 1000, suelo: str = "normal",
                barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Vertical de λ/4 con `radiales` radiales horizontales elevados `altura_mm` sobre suelo real; la fuente en el primer
    segmento del radiador, en la unión con los radiales. Los radiales elevados dan unos 30 a 36 Ω (no 50 Ω): la ROE contra 50 Ω
    queda en ≈ 1,5; con radiales enterrados o inclinados (como el ground plane de VHF) subiría."""
    _comprobar_hf(f_MHz, diametro_mm, altura_mm, suelo)
    if radiales < 2:
        raise ValueError("hacen falta al menos 2 radiales")
    p = vertical_hf_por_defecto(f_MHz)
    rad = (radiador_mm or p["radiador_mm"]) / 1000
    rl = (radial_mm or p["radial_mm"]) / 1000
    h, r = altura_mm / 1000, diametro_mm / 2000
    paso = _paso_hf(f_MHz) / densidad
    hilos = [Hilo((0, 0, h), (0, 0, h + rad), r, max(3, round(rad / paso)))]
    for i in range(radiales):
        a = 2 * math.pi * i / radiales
        hilos.append(Hilo((0, 0, h), (rl * math.cos(a), rl * math.sin(a), h), r, max(2, round(rl / paso))))
    return Modelo("Vertical de HF", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"Vertical de HF a {f_MHz:g} MHz, hilo de {diametro_mm:g} mm, radiales a {h:g} m sobre suelo {suelo}",
                               f"Radiador {rad:.2f} m, {radiales} radiales de {rl:.2f} m"))


def abanico_por_defecto(bandas: list[str], altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """Un hilo por banda, cada uno de 0,47 λ de la frecuencia central de su banda (la ROE ajusta el resto)."""
    largos = [0.47 * 299792.458 / ((banda_por_nombre(b)[1] + banda_por_nombre(b)[2]) / 2) for b in bandas]
    return {"bandas": list(bandas), "largos_mm": largos, "altura_mm": altura_m * 1000, "suelo": suelo, "sep_mm": ABANICO_SEP_MM}


def abanico(f_MHz: float, diametro_mm: float, largos_mm: list[float], altura_mm: float = 10000.0, suelo: str = "normal",
            sep_mm: float = ABANICO_SEP_MM, barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Dipolo en abanico: un par de hilos por banda desde un mismo centro, repartidos en vertical `sep_mm` unos de otros."""
    _comprobar_hf(f_MHz, diametro_mm, altura_mm, suelo)
    if not largos_mm:
        raise ValueError("hace falta al menos una banda")
    h, r, g = altura_mm / 1000, diametro_mm / 2000, 0.1
    paso = _paso_hf(f_MHz) / densidad
    hilos = [Hilo((-g / 2, 0, h), (g / 2, 0, h), r, 1)]
    n = len(largos_mm)
    for k, largo in enumerate(largos_mm):
        dz = (k - (n - 1) / 2) * sep_mm / 1000
        for lado in (1, -1):
            fin = (lado * largo / 2000, 0, h + dz)
            hilos.append(Hilo((lado * g / 2, 0, h), fin, r, max(2, round(math.dist((lado * g / 2, 0, h), fin) / paso))))
    return Modelo("Dipolo en abanico", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"Dipolo en abanico de {n} bandas, hilo de {diametro_mm:g} mm a {h:g} m sobre suelo {suelo}",
                               "Largos totales: " + ", ".join(f"{x / 1000:.2f}" for x in largos_mm) + " m"))


def trampas_por_defecto(f_baja: float, f_alta: float, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """Cotas de partida del dipolo con trampas: la parte interior resuena en la banda alta y la trampa en esa misma banda."""
    w = 2 * math.pi * f_alta * 1e6
    l_uh = TRAMPA_Z_OHM / w * 1e6
    c_pf = 1 / (w * TRAMPA_Z_OHM) * 1e12
    interior = 0.475 / 2 * 299792.458 / f_alta
    exterior = max(0.2 * interior, (0.475 / 2 * 299792.458 / f_baja - interior) * 0.85)
    return {"f_alta_MHz": f_alta, "interior_mm": interior, "exterior_mm": exterior, "trampa_L_uH": l_uh, "trampa_C_pF": c_pf,
            "trampa_largo_mm": TRAMPA_LARGO_MM, "altura_mm": altura_m * 1000, "suelo": suelo}


def trampas(f_baja: float, diametro_mm: float, f_alta: float, interior_mm: float, exterior_mm: float, l_uh: float, c_pf: float,
            trampa_largo_mm: float = TRAMPA_LARGO_MM, altura_mm: float = 10000.0, suelo: str = "normal",
            barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Dipolo de dos bandas con una trampa (circuito paralelo L-C resonante en la banda alta) a cada lado.

    Del centro salen `interior_mm` de hilo, la trampa (`trampa_largo_mm` de largo con `l_uh` y `c_pf` en paralelo y una
    pérdida de Q = 100) y `exterior_mm` más. En la banda alta la trampa corta el exterior; en la baja lo deja conectado
    y el conjunto resuena como dipolo largo (la trampa lo alarga un poco)."""
    _comprobar_hf(f_baja, diametro_mm, altura_mm, suelo)
    h, r, g = altura_mm / 1000, diametro_mm / 2000, 0.1
    ai, ae, tl = interior_mm / 1000, exterior_mm / 1000, trampa_largo_mm / 1000
    paso = _paso_hf(f_alta, 1.0) / densidad
    w = 2 * math.pi * f_alta * 1e6
    rp = TRAMPA_Q * w * l_uh * 1e-6                      # resistencia en paralelo para una Q propia de 100
    hilos = [Hilo((-g / 2, 0, h), (g / 2, 0, h), r, 1)]
    cargas = []
    for lado in (1, -1):
        x0 = lado * g / 2
        tramos = [(x0, lado * ai, max(2, round(abs(ai - g / 2) / paso))), (lado * ai, lado * (ai + tl), 1),
                  (lado * (ai + tl), lado * (ai + tl + ae), max(2, round(ae / paso)))]
        for a, b, n in tramos:
            hilos.append(Hilo((a, 0, h), (b, 0, h), r, n))
        cargas.append(Carga(len(hilos) - 1, 1, 1, r=rp, l=l_uh * 1e-6, c=c_pf * 1e-12, paralela=True))
    return Modelo("Dipolo con trampas", f_baja, tuple(hilos), Puerto(1, 1), cargas=tuple(cargas), barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"Dipolo de dos bandas ({f_baja:g} y {f_alta:g} MHz) con trampas, hilo de {diametro_mm:g} mm a {h:g} m sobre suelo {suelo}",
                               f"Interior {ai:.2f} m, exterior {ae:.2f} m por lado; trampa {l_uh:.2f} uH y {c_pf:.1f} pF"))


def g5rv_por_defecto(f_MHz: float, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """G5RV a la escala de `f_MHz`: 31,1 m de dipolo y 10,4 m de línea abierta a 3,65 MHz; a 7,1 MHz la «media» G5RV."""
    k = 3.65 / f_MHz
    return {"largo_mm": G5RV_FACTOR * k * 1000, "escalerilla_mm": 10360.0 * k, "escalerilla_z0": G5RV_ESCALERILLA_Z,
            "escalerilla_vf": G5RV_ESCALERILLA_VF, "altura_mm": altura_m * 1000, "suelo": suelo}


def g5rv(f_MHz: float, diametro_mm: float, largo_mm: float | None = None, escalerilla_mm: float | None = None,
         escalerilla_z0: float = G5RV_ESCALERILLA_Z, escalerilla_vf: float = G5RV_ESCALERILLA_VF, altura_mm: float = 10000.0,
         suelo: str = "normal", barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """G5RV: dipolo largo alimentado por una línea abierta de 450 Ω (`escalerilla_mm`, con su VF) y, al pie de ella, el coaxial.

    La impedancia que sale es la del pie de la escalerilla (donde se conecta el coaxial con su choke 1:1). La línea es
    una TL ideal, sin pérdidas, y no cuenta el coaxial: la ROE que se calcula es la que ve el coaxial."""
    _comprobar_hf(f_MHz, diametro_mm, altura_mm, suelo)
    p = g5rv_por_defecto(f_MHz)
    largo, esc = (largo_mm or p["largo_mm"]) / 1000, (escalerilla_mm or p["escalerilla_mm"]) / 1000
    h, r = altura_mm / 1000, diametro_mm / 2000
    n = max(3, round(largo / (_paso_hf(f_MHz, 8.0) / densidad)))
    n += 1 - n % 2
    hilos = (Hilo((-largo / 2, 0, h), (largo / 2, 0, h), r, n), Hilo((0, 0, h - 1.2), (0, 0, h - 1.0), r, 1))
    return Modelo("G5RV", f_MHz, hilos, Puerto(2, 1), lineas=(Linea(1, n // 2 + 1, 2, 1, escalerilla_z0, esc, escalerilla_vf),),
                  barrido=barrido, suelo=SUELOS[suelo],
                  comentarios=(f"G5RV a la escala de {f_MHz:g} MHz, hilo de {diametro_mm:g} mm a {h:g} m sobre suelo {suelo}",
                               f"Dipolo de {largo:.2f} m, escalerilla de {esc:.2f} m ({escalerilla_z0:g} ohm, VF {escalerilla_vf:g})"))


# ---------------------------------------------------------------- torniquete y batwing

TORN_BRAZO, TORN_SEP, TORN_Z0, TORN_VF = 0.236, 0.02, 75.0, 0.66    # brazo en λ, separación entre los dos dipolos en λ, coaxial de 75 Ω
BAT_ALA, BAT_ANCHO, BAT_HUECO, BAT_RADIOS = 0.173, 1.0, 0.004, 5                  # ala en λ, ancho de la punta respecto al largo del ala, hueco en λ


def torniquete_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"brazo_mm": TORN_BRAZO * lam, "sep_mm": TORN_SEP * lam, "z0_linea": TORN_Z0, "vf_linea": TORN_VF,
            "linea_mm": lam / 4 * TORN_VF}


def torniquete(f_MHz: float, diametro_mm: float, brazo_mm: float | None = None, sep_mm: float | None = None,
               z0_linea: float = TORN_Z0, vf_linea: float = TORN_VF, linea_mm: float | None = None,
               barrido: Barrido | None = None, densidad: float = 1.0) -> Modelo:
    """Torniquete: dos dipolos de media onda cruzados en cruz (uno a lo largo de x y otro de y, el segundo `sep_mm` más alto).

    El primero se alimenta directo y el segundo por una línea de λ/4 eléctricos (coaxial de `z0_linea` Ω y `vf_linea`):
    esos 90° de fase dan polarización circular hacia arriba y hacia abajo. Espacio libre. NEC2 solo da la ganancia máxima:
    la razón axial no se ha comprobado.
    """
    if f_MHz <= 0 or diametro_mm <= 0:
        raise ValueError("la frecuencia y el diámetro deben ser positivos")
    p = torniquete_por_defecto(f_MHz)
    brazo = (brazo_mm or p["brazo_mm"]) / 1000
    sep = (sep_mm or p["sep_mm"]) / 1000
    linea = (linea_mm if linea_mm is not None else p["linea_mm"]) / 1000
    if sep <= 2 * diametro_mm / 1000:
        raise ValueError("la separación entre los dipolos es demasiado pequeña para ese diámetro")
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    n = _segmentos(2 * brazo, paso)
    n += 1 - n % 2
    hilos = (Hilo((-brazo, 0, 0), (brazo, 0, 0), r, n), Hilo((0, -brazo, sep), (0, brazo, sep), r, n))
    return Modelo("Torniquete", f_MHz, hilos, Puerto(1, n // 2 + 1),
                  lineas=(Linea(1, n // 2 + 1, 2, n // 2 + 1, z0_linea, linea, vf_linea),), barrido=barrido,
                  comentarios=(f"Torniquete de dos dipolos cruzados a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm",
                               f"Brazos de {brazo * 1000:.1f} mm, separacion {sep * 1000:.1f} mm, linea de {linea * 1000:.1f} mm "
                               f"({z0_linea:g} ohm, VF {vf_linea:g})"))


def batwing_por_defecto(f_MHz: float) -> dict[str, float]:
    lam = longitud_onda_m(f_MHz) * 1000
    return {"ala_mm": BAT_ALA * lam, "ancho_mm": BAT_ALA * lam * BAT_ANCHO, "hueco_mm": max(4.0, round(BAT_HUECO * lam))}


def batwing(f_MHz: float, diametro_mm: float, ala_mm: float | None = None, ancho_mm: float | None = None,
            hueco_mm: float | None = None, radios: int = BAT_RADIOS, barrido: Barrido | None = None,
            densidad: float = 1.0) -> Modelo:
    """Batwing de alambre: dipolo con dos alas triangulares, en el plano x–z, hechas de `radios` alambres que salen del
    vértice y un borde de alambre en la punta (como un abanico).

    La fuente va en el hueco entre los dos vértices. Banda más ancha que un dipolo de varilla. Espacio libre.
    """
    if f_MHz <= 0 or diametro_mm <= 0 or radios < 3:
        raise ValueError("frecuencia y diámetro positivos y al menos 3 radios por ala")
    p = batwing_por_defecto(f_MHz)
    ala = (ala_mm or p["ala_mm"]) / 1000
    w = (ancho_mm or p["ancho_mm"]) / 1000
    g = (hueco_mm or p["hueco_mm"]) / 1000
    r = diametro_mm / 2000
    paso = longitud_onda_m(f_MHz) / SEGMENTOS_POR_LAMBDA / densidad
    hilos = [Hilo((-g / 2, 0, 0), (g / 2, 0, 0), r, 1)]
    zs = [w / 2 - w * i / (radios - 1) for i in range(radios)]          # los puntos del borde de la punta, de arriba abajo
    for s in (1, -1):
        v, punta = (s * g / 2, 0, 0), s * (g / 2 + ala)
        puntos = [(punta, 0, z) for z in zs]
        for p in puntos:                                                  # radios desde el vértice
            hilos.append(Hilo(v, p, r, _segmentos(math.dist(v, p), paso)))
        for a, b in zip(puntos, puntos[1:]):                              # borde de la punta
            hilos.append(Hilo(a, b, r, _segmentos(math.dist(a, b), paso)))
    return Modelo("Batwing", f_MHz, tuple(hilos), Puerto(1, 1), barrido=barrido,
                  comentarios=(f"Batwing de alambre a {f_MHz:g} MHz, alambre de {diametro_mm:g} mm, {radios} radios por ala",
                               f"Alas de {ala * 1000:.1f} mm de largo y {w * 1000:.1f} mm de ancho, hueco {g * 1000:.1f} mm"))
