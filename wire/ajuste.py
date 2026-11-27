"""Ajuste de las cotas con el motor (solo escritorio: necesita PyNEC).

Devuelve las cotas ajustadas y los resultados simulados como diccionarios que van tal cual a `diseno.json`;
el generador de planos los lee de ahí y no llama nunca al motor.
"""

from __future__ import annotations

import math

from . import motor
from .generadores import (BANDAS_HF, abanico, abanico_por_defecto, banda_hf, banda_por_nombre, bandas_de, dipolo_hf, dipolo_hf_por_defecto, vertical_hf, vertical_hf_por_defecto,
                          efhw, efhw_por_defecto, g5rv, g5rv_por_defecto, trampas, trampas_por_defecto, vinv_hf, vinv_hf_por_defecto)
from .generadores import (BAT_ANCHO, BAT_RADIOS, batwing, batwing_por_defecto, torniquete, torniquete_por_defecto)
from .generadores import biconica, biconica_por_defecto, gp, gp_por_defecto, vinv, vinv_por_defecto, yagi, yagi_por_defecto, discone, discone_por_defecto, dipolo, jpole, jpole_koch, jpole_koch_por_defecto, jpole_por_defecto
from .generadores import (COL_GANANCIA_MIN, COLB_GANANCIA_MIN, colineal, colineal_bibanda, colineal_bibanda_por_defecto,
                          colineal_por_defecto)
from .modelo import Barrido, Modelo

Z0 = 50.0


def _gamma(modelo: Modelo, f_MHz: float) -> float:
    z = motor.simular(modelo, Barrido(f_MHz, f_MHz, 1), diagrama=False).z[0]
    return abs((z - Z0) / (z + Z0))


def minimo_roe(modelo: Modelo, f_min: float, f_max: float, pasos: int = 61) -> float:
    """Frecuencia (MHz) del mínimo de |S11| en [f_min, f_max], con refinado por sección áurea."""
    r = motor.simular(modelo, Barrido(f_min, f_max, pasos), diagrama=False)
    g = [abs(x) for x in r.s11]
    k = min(range(pasos), key=g.__getitem__)
    a = r.frecuencias[max(k - 1, 0)]
    b = r.frecuencias[min(k + 1, pasos - 1)]
    phi = (math.sqrt(5) - 1) / 2
    c, d = b - phi * (b - a), a + phi * (b - a)
    gc, gd = _gamma(modelo, c), _gamma(modelo, d)
    while b - a > 1e-4:
        if gc < gd:
            b, d, gd = d, c, gc
            c = b - phi * (b - a)
            gc = _gamma(modelo, c)
        else:
            a, c, gc = c, d, gd
            d = a + phi * (b - a)
            gd = _gamma(modelo, d)
    return (a + b) / 2


def nelder_mead(funcion, x0, pasos, tolerancia=1e-7, iteraciones=400):
    """Nelder–Mead mínimo (sin SciPy): devuelve (x, f(x))."""
    n = len(x0)
    simplex = [list(x0)]
    for i in range(n):
        x = list(x0)
        x[i] += pasos[i]
        simplex.append(x)
    valores = [funcion(x) for x in simplex]
    for _ in range(iteraciones):
        orden = sorted(range(n + 1), key=valores.__getitem__)
        simplex = [simplex[i] for i in orden]
        valores = [valores[i] for i in orden]
        if valores[-1] - valores[0] < tolerancia:
            break
        centro = [sum(p[i] for p in simplex[:-1]) / n for i in range(n)]
        peor = simplex[-1]
        reflejado = [c + (c - w) for c, w in zip(centro, peor)]
        fr = funcion(reflejado)
        if fr < valores[0]:
            expandido = [c + 2 * (c - w) for c, w in zip(centro, peor)]
            fe = funcion(expandido)
            simplex[-1], valores[-1] = (expandido, fe) if fe < fr else (reflejado, fr)
        elif fr < valores[-2]:
            simplex[-1], valores[-1] = reflejado, fr
        else:
            contraido = [c + 0.5 * (w - c) for c, w in zip(centro, peor)]
            fc = funcion(contraido)
            if fc < valores[-1]:
                simplex[-1], valores[-1] = contraido, fc
            else:
                mejor = simplex[0]
                simplex = [mejor] + [[m + 0.5 * (p - m) for m, p in zip(mejor, q)] for q in simplex[1:]]
                valores = [valores[0]] + [funcion(x) for x in simplex[1:]]
    k = min(range(n + 1), key=valores.__getitem__)
    return simplex[k], valores[k]


def _resultados(modelo: Modelo, f_MHz: float, ancho: float = 0.035) -> dict:
    """Barrido de ROE alrededor de f, Z y ganancia a f (lo que se guarda en `diseno.json`)."""
    barrido = motor.simular(modelo, Barrido(f_MHz * (1 - ancho), f_MHz * (1 + ancho), 41), diagrama=False)
    centro = motor.simular(modelo, Barrido(f_MHz, f_MHz, 1), diagrama=True)
    z = centro.z[0]
    return {
        "motor": "PyNEC",
        "z0_ohm": Z0,
        "f_MHz": f_MHz,
        "r_ohm": z.real,
        "x_ohm": z.imag,
        "roe": centro.roe[0],
        "s11_dB": centro.s11_dB[0],
        "ganancia_dBi": centro.ganancia_max[0],
        "barrido": {"f_MHz": list(barrido.frecuencias), "roe": list(barrido.roe)},
    }


def ajustar_dipolo(f_MHz: float, diametro_mm: float) -> dict:
    """Dipolo resonante (X = 0) a f. Devuelve {"geometria", "resultados"} en mm y unidades del plano."""
    radio = diametro_mm / 2
    largo = 0.48 * 299792.458 / f_MHz
    for _ in range(5):
        f, _ = motor.resonancia(dipolo(f_MHz, radio, longitud_mm=largo), 0.8 * f_MHz, 1.2 * f_MHz)
        largo *= f / f_MHz
    modelo = dipolo(f_MHz, radio, longitud_mm=largo)
    f_res, z = motor.resonancia(modelo, 0.8 * f_MHz, 1.2 * f_MHz)
    f_corto, _ = motor.resonancia(dipolo(f_MHz, radio, longitud_mm=largo - 10), 0.8 * f_MHz, 1.2 * f_MHz)
    resultados = _resultados(modelo, f_MHz)
    resultados.update({
        "f_resonancia_MHz": f_res,
        "r_resonancia_ohm": z.real,
        # Quitar 1 mm de cada brazo acorta 2 mm el total.
        "sensibilidad_MHz_por_mm": (f_corto - f_res) / 10 * 2,
        "sensibilidad_pieza": "cada brazo",
    })
    return {"geometria": {"largo_total_mm": largo}, "resultados": resultados}


def ajustar_jpole(f_MHz: float, diametro_mm: float, separacion_mm: float | None = None) -> dict:
    """J-pole con |S11| mínimo a f a 50 Ω: ajusta brazo largo, brazo corto y toma (Nelder–Mead)."""
    partida = jpole_por_defecto(f_MHz, diametro_mm)
    s = separacion_mm or partida["separacion_mm"]

    def construir(x):
        return jpole(f_MHz, diametro_mm, largo_mm=x[0], corto_mm=x[1], toma_mm=x[2], separacion_mm=s)

    def coste(x):
        if not 0 < x[2] < x[1] < x[0]:
            return 10.0
        return _gamma(construir(x), f_MHz)

    lam = 299792.458 / f_MHz
    x0 = [partida["largo_mm"], partida["corto_mm"], partida["toma_mm"]]
    x, _ = nelder_mead(coste, x0, [0.02 * lam, 0.01 * lam, 0.01 * lam], tolerancia=1e-6)
    x, _ = nelder_mead(coste, x, [0.002 * lam, 0.002 * lam, 0.002 * lam], tolerancia=1e-8)
    modelo = construir(x)
    resultados = _resultados(modelo, f_MHz)
    f_min = minimo_roe(modelo, 0.95 * f_MHz, 1.05 * f_MHz)
    recortado = jpole(f_MHz, diametro_mm, largo_mm=x[0] - 10, corto_mm=x[1], toma_mm=x[2], separacion_mm=s)
    f_rec = minimo_roe(recortado, 0.95 * f_MHz, 1.08 * f_MHz)
    corto = jpole(f_MHz, diametro_mm, largo_mm=x[0], corto_mm=x[1] - 10, toma_mm=x[2], separacion_mm=s)
    f_corto = minimo_roe(corto, 0.95 * f_MHz, 1.08 * f_MHz)
    resultados.update({
        "f_minimo_roe_MHz": f_min,
        "sensibilidad_MHz_por_mm": (f_rec - f_min) / 10,
        "sensibilidad_pieza": "punta del brazo largo",
        "sensibilidad_corto_MHz_por_mm": (f_corto - f_min) / 10,
    })
    geometria = {"largo_mm": x[0], "corto_mm": x[1], "toma_mm": x[2], "separacion_mm": s}
    return {"geometria": geometria, "resultados": resultados}


def ajustar_jpole_koch(f_MHz: float, diametro_mm: float, iteracion: int = 2, separacion_mm: float | None = None) -> dict:
    """J-pole de Koch con |S11| mínimo a f a 50 Ω: ajusta la altura de la curva, el brazo corto y la toma (Nelder–Mead)."""
    partida = jpole_koch_por_defecto(f_MHz, diametro_mm, iteracion)
    s = separacion_mm or partida["separacion_mm"]

    def construir(x):
        return jpole_koch(f_MHz, diametro_mm, altura_koch_mm=x[0], corto_mm=x[1], toma_mm=x[2], separacion_mm=s,
                          iteracion=iteracion)

    def coste(x):
        if not 0 < x[2] < x[1] or x[0] <= 0:
            return 10.0
        return _gamma(construir(x), f_MHz)

    lam = 299792.458 / f_MHz
    x0 = [partida["altura_koch_mm"], partida["corto_mm"], partida["toma_mm"]]
    x, _ = nelder_mead(coste, x0, [0.02 * lam, 0.01 * lam, 0.01 * lam], tolerancia=1e-6)
    x, _ = nelder_mead(coste, x, [0.002 * lam, 0.002 * lam, 0.002 * lam], tolerancia=1e-8)
    modelo = construir(x)
    resultados = _resultados(modelo, f_MHz)
    f_min = minimo_roe(modelo, 0.95 * f_MHz, 1.05 * f_MHz)
    recortado = jpole_koch(f_MHz, diametro_mm, altura_koch_mm=x[0] - 3, corto_mm=x[1], toma_mm=x[2], separacion_mm=s,
                           iteracion=iteracion)
    f_rec = minimo_roe(recortado, 0.95 * f_MHz, 1.08 * f_MHz)
    resultados.update({"f_minimo_roe_MHz": f_min, "sensibilidad_MHz_por_mm": (f_rec - f_min) / 3,
                       "sensibilidad_pieza": "la altura de la curva"})
    geometria = {"altura_koch_mm": x[0], "corto_mm": x[1], "toma_mm": x[2], "separacion_mm": s, "iteracion": float(iteracion)}
    return {"geometria": geometria, "resultados": resultados}


def ajustar_discone(f_min_MHz: float, diametro_mm: float, varillas: int = 8) -> dict:
    """Discone con el límite inferior de ROE < 2 en `f_min_MHz`: escala el cono y el disco (la banda sube y baja con su tamaño)."""
    partida = discone_por_defecto(f_min_MHz)
    k = 1.0
    f_inf = f_sup = f_min_MHz

    def construir(k_):
        p = discone_por_defecto(f_min_MHz, k_)
        return discone(f_min_MHz, diametro_mm, cono_mm=p["cono_mm"], disco_mm=p["disco_mm"], hueco_mm=p["hueco_mm"],
                       varillas=varillas, barrido=Barrido(0.8 * f_min_MHz, 5.0 * f_min_MHz, 81))

    mejor = (float("inf"), 1.0)
    for _ in range(6):
        r = motor.simular(construir(k), diagrama=False)
        buenas = [f for f, ro in zip(r.frecuencias, r.roe) if ro < 2.0]
        if not buenas:
            break
        f_inf, f_sup = buenas[0], buenas[-1]
        mejor = min(mejor, (abs(math.log(f_inf / f_min_MHz)), k))
        if mejor[0] < 0.01:
            break
        k = min(1.6, max(0.6, k * (f_inf / f_min_MHz) ** 0.7))      # amortiguado: el disco y el hueco también cuentan
    k = mejor[1]
    p = discone_por_defecto(f_min_MHz, k)
    modelo = construir(k)
    r = motor.simular(modelo, diagrama=False)
    buenas = [f for f, ro in zip(r.frecuencias, r.roe) if ro < 2.0]
    f_inf, f_sup = (buenas[0], buenas[-1]) if buenas else (0.0, 0.0)
    centro = motor.simular(discone(f_min_MHz, diametro_mm, cono_mm=p["cono_mm"], disco_mm=p["disco_mm"],
                                   hueco_mm=p["hueco_mm"], varillas=varillas, barrido=Barrido(2 * f_min_MHz, 2 * f_min_MHz, 1)))
    resultados = {"motor": "PyNEC", "z0_ohm": Z0, "f_MHz": f_min_MHz, "f_inferior_roe2_MHz": f_inf, "f_superior_roe2_MHz": f_sup,
                  "relacion_banda": (f_sup / f_inf) if f_inf else 0.0, "ganancia_dBi": centro.ganancia_max[0],
                  "f_ganancia_MHz": 2 * f_min_MHz, "barrido": {"f_MHz": list(r.frecuencias), "roe": list(r.roe)}}
    geometria = {"cono_mm": p["cono_mm"], "disco_mm": p["disco_mm"], "hueco_mm": p["hueco_mm"],
                 "semiangulo": p["semiangulo"], "varillas": float(varillas)}
    return {"geometria": geometria, "resultados": resultados}


def _nm_gamma(f_MHz: float, construir, x0: list[float], escalas: list[float], valido=None, penalizacion=None):
    """Nelder–Mead de |S11| a f (dos pasadas: gruesa y fina). `penalizacion(modelo)` suma al coste (p. ej. una ganancia mínima)."""
    def coste(x):
        if valido is not None and not valido(x):
            return 10.0
        m = construir(x)
        return _gamma(m, f_MHz) + (penalizacion(m) if penalizacion else 0.0)

    x, _ = nelder_mead(coste, x0, escalas, tolerancia=1e-6)
    x, _ = nelder_mead(coste, x, [e / 10 for e in escalas], tolerancia=1e-8)
    return x


def _con_resultados(modelo: Modelo, f_MHz: float, geometria: dict, sensibilidad_param=None) -> dict:
    resultados = _resultados(modelo, f_MHz)
    resultados["f_minimo_roe_MHz"] = minimo_roe(modelo, 0.9 * f_MHz, 1.1 * f_MHz)
    if sensibilidad_param:
        resultados.update(sensibilidad_param(modelo, resultados["f_minimo_roe_MHz"]))
    return {"geometria": geometria, "resultados": resultados}


def ajustar_gp(f_MHz: float, diametro_mm: float, angulo: float = 45.0, radiales: int = 4) -> dict:
    """Ground plane con |S11| mínimo a f a 50 Ω: ajusta el radiador y los radiales."""
    p = gp_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    construir = lambda x: gp(f_MHz, diametro_mm, radiador_mm=x[0], radial_mm=x[1], angulo=angulo, radiales=radiales)  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["radiador_mm"], p["radial_mm"]], [0.01 * lam, 0.01 * lam])

    def sens(m, f0):
        corto = gp(f_MHz, diametro_mm, radiador_mm=x[0] - 5, radial_mm=x[1], angulo=angulo, radiales=radiales)
        return {"sensibilidad_MHz_por_mm": (minimo_roe(corto, 0.9 * f_MHz, 1.15 * f_MHz) - f0) / 5, "sensibilidad_pieza": "el radiador"}

    return _con_resultados(construir(x), f_MHz, {"radiador_mm": x[0], "radial_mm": x[1], "angulo": angulo, "radiales": float(radiales)}, sens)


def ajustar_colineal(f_MHz: float, diametro_mm: float, secciones: int = 3, altura_m: float | None = None, suelo: str | None = None) -> dict:
    """Colineal con bobinas de fase: ajusta el largo de cada sección, la bobina (µH) y los radiales para 50 Ω a f,
    sin bajar de la ganancia mínima de su número de secciones.

    Con `altura_m` y `suelo` el ajuste se hace en espacio libre (más rápido) y los resultados son los del diseño ya sobre ese
    suelo: el suelo cambia la impedancia, así que la ROE puede salir peor que la del ajuste."""
    p = colineal_por_defecto(f_MHz, secciones)
    lam = 299792.458 / f_MHz
    gmin = COL_GANANCIA_MIN[secciones]
    construir = lambda x: colineal(f_MHz, diametro_mm, secciones_mm=list(x[:secciones]), bobina_uH=x[secciones], radial_mm=x[secciones + 1])  # noqa: E731

    def penalizacion(m):
        try:
            return 0.05 * max(0.0, gmin - motor.simular(m, Barrido(f_MHz, f_MHz, 1)).ganancia_max[0])
        except RuntimeError:
            return 1.0

    x = _nm_gamma(f_MHz, construir, p["secciones_mm"] + [p["bobina_uH"], p["radial_mm"]],
                  [0.03 * lam] * secciones + [0.2 * p["bobina_uH"], 0.02 * lam],
                  valido=lambda x: all(v > 5 for v in x[:secciones]) and 0.05 < x[secciones] < 5 and x[secciones + 1] > 0.1 * lam,
                  penalizacion=penalizacion)

    def sens(m, f0):
        corto = colineal(f_MHz, diametro_mm, secciones_mm=list(x[:secciones - 1]) + [x[secciones - 1] - 25], bobina_uH=x[secciones], radial_mm=x[secciones + 1],
                         **_suelo_kw(altura_m, suelo))
        return {"sensibilidad_MHz_por_mm": (minimo_roe(corto, 0.9 * f_MHz, 1.15 * f_MHz, 151) - f0) / 25, "sensibilidad_pieza": "la sección de arriba"}

    geometria = {"secciones_mm": list(x[:secciones]), "bobina_uH": x[secciones], "radial_mm": x[secciones + 1],
                 "n_secciones": float(secciones), "angulo": 45.0, "radiales": 4.0, **_geometria_suelo(altura_m, suelo)}
    final = colineal(f_MHz, diametro_mm, secciones_mm=list(x[:secciones]), bobina_uH=x[secciones], radial_mm=x[secciones + 1], **_suelo_kw(altura_m, suelo))
    return _con_resultados(final, f_MHz, geometria, sens)


def _suelo_kw(altura_m: float | None, suelo: str | None) -> dict:
    return {} if suelo is None else {"altura_mm": altura_m * 1000, "suelo": suelo}


def _geometria_suelo(altura_m: float | None, suelo: str | None) -> dict:
    return {} if suelo is None else {"altura_mm": altura_m * 1000, "suelo": suelo}


def ajustar_colineal_bibanda(f_baja: float, f_alta: float, diametro_mm: float, secciones: int = 4,
                             altura_m: float | None = None, suelo: str | None = None) -> dict:
    """Colineal bibanda: ajusta secciones, bobina, condensador en serie y radiales para 50 Ω en las dos bandas, con la
    ganancia mínima en la alta. Los resultados son los de la banda baja; los de la alta van en `resultados["alta"]`."""
    p = colineal_bibanda_por_defecto(f_baja, f_alta, secciones)
    lam = 299792.458 / f_alta
    gmin = COLB_GANANCIA_MIN[secciones]
    n = secciones
    construir = lambda x: colineal_bibanda(f_baja, f_alta, diametro_mm, secciones_mm=list(x[:n]), bobina_uH=x[n],  # noqa: E731
                                           condensador_pF=x[n + 2], radial_mm=x[n + 1])

    def coste(x):
        if any(v < 5 for v in x[:n]) or not 0.02 < x[n] < 3 or x[n + 1] < 0.1 * lam or not 0.3 < x[n + 2] < 30:
            return 10.0
        m = construir(x)
        try:
            gan = motor.simular(m, Barrido(f_alta, f_alta, 1)).ganancia_max[0]
        except RuntimeError:
            return 10.0
        return _gamma_en(m, f_baja) + _gamma_en(m, f_alta) + 0.05 * max(0.0, gmin - gan)

    x0 = p["secciones_mm"] + [p["bobina_uH"], p["radial_mm"], p["condensador_pF"]]
    pasos = [0.03 * lam] * n + [0.08, 0.02 * lam, 0.5]
    x, _ = nelder_mead(coste, x0, pasos, tolerancia=1e-5, iteraciones=250)
    x, _ = nelder_mead(coste, x, [e / 5 for e in pasos], tolerancia=1e-7, iteraciones=250)
    modelo = colineal_bibanda(f_baja, f_alta, diametro_mm, secciones_mm=list(x[:n]), bobina_uH=x[n], condensador_pF=x[n + 2],
                              radial_mm=x[n + 1], **_suelo_kw(altura_m, suelo))       # con suelo: el ajuste es en espacio libre
    r = _resultados(modelo, f_baja)
    r["f_minimo_roe_MHz"] = minimo_roe(modelo, 0.9 * f_baja, 1.1 * f_baja)
    alta = _resultados(modelo, f_alta)
    alta["f_minimo_roe_MHz"] = minimo_roe(modelo, 0.95 * f_alta, 1.05 * f_alta)
    r["alta"] = alta
    return {"geometria": {"secciones_mm": list(x[:n]), "bobina_uH": x[n], "condensador_pF": x[n + 2], "radial_mm": x[n + 1],
                          "n_secciones": float(n), "angulo": 45.0, "radiales": 4.0, "f_alta_MHz": f_alta,
                          **_geometria_suelo(altura_m, suelo)}, "resultados": r}


def ajustar_moxon(f_MHz: float, diametro_mm: float) -> dict:
    """Moxon: ajusta el ancho, las dos puntas y el hueco para |S11| mínimo a f, sin perder el haz hacia delante (+y)."""
    from .generadores import moxon, moxon_por_defecto
    p = moxon_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    claves = ("ancho_mm", "punta_excitado_mm", "punta_reflector_mm", "hueco_mm")
    construir = lambda x: moxon(f_MHz, diametro_mm, x[0], x[1], x[2], x[3], p["centro_mm"])  # noqa: E731

    def penal(m):
        frente, atras = motor.ganancias_en(m, f_MHz, [(90.0, 90.0), (90.0, 270.0)])
        maxima = motor.simular(m, Barrido(f_MHz, f_MHz, 1)).ganancia_max[0]
        return 0.01 * max(0.0, maxima - frente) + 0.004 * max(0.0, 15.0 - (frente - atras))      # el haz hacia delante y 15 dB de delante/detrás

    x = _nm_gamma(f_MHz, construir, [p[k] for k in claves], [0.01 * lam, 0.005 * lam, 0.005 * lam, 0.005 * lam],
                  valido=lambda x: min(x) > 0.005 * lam and x[3] > 3 * diametro_mm, penalizacion=penal)
    geometria = dict(zip(claves, x))
    geometria["centro_mm"] = p["centro_mm"]
    r = _con_resultados(construir(x), f_MHz, geometria)
    frente, atras = motor.ganancias_en(construir(x), f_MHz, [(90.0, 90.0), (90.0, 270.0)])
    r["resultados"].update({"ganancia_frente_dBi": frente, "relacion_delante_detras_dB": frente - atras})
    return r


def ajustar_quad(f_MHz: float, diametro_mm: float) -> dict:
    """Quad de dos elementos: ajusta los dos lados y la separación para |S11| mínimo a f, con el haz hacia delante (+y) y al
    menos 10 dB de relación delante/detrás."""
    from .generadores import quad, quad_por_defecto
    p = quad_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    claves = ("lado_excitado_mm", "lado_reflector_mm", "separacion_mm")
    construir = lambda x: quad(f_MHz, diametro_mm, x[0], x[1], x[2], p["centro_mm"])  # noqa: E731

    def penal(m):
        frente, atras = motor.ganancias_en(m, f_MHz, [(90.0, 90.0), (90.0, 270.0)])
        maxima = motor.simular(m, Barrido(f_MHz, f_MHz, 1)).ganancia_max[0]
        return 0.01 * max(0.0, maxima - frente) + 0.004 * max(0.0, 10.0 - (frente - atras))

    x = _nm_gamma(f_MHz, construir, [p[k] for k in claves], [0.01 * lam] * 3,
                  valido=lambda x: min(x) > 0.05 * lam and x[2] < 0.35 * lam, penalizacion=penal)
    geometria = dict(zip(claves, x))
    geometria["centro_mm"] = p["centro_mm"]
    r = _con_resultados(construir(x), f_MHz, geometria)
    frente, atras = motor.ganancias_en(construir(x), f_MHz, [(90.0, 90.0), (90.0, 270.0)])
    r["resultados"].update({"ganancia_frente_dBi": frente, "relacion_delante_detras_dB": frente - atras})
    return r


def ajustar_delta(f_MHz: float, diametro_mm: float) -> dict:
    """Delta loop: ajusta la base y la altura del triángulo para |S11| mínimo a f (la fuente queda en el centro de la base)."""
    from .generadores import delta, delta_por_defecto
    p = delta_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    construir = lambda x: delta(f_MHz, diametro_mm, x[0], x[1], p["centro_mm"])  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["base_mm"], p["alto_mm"]], [0.02 * lam, 0.02 * lam],
                  valido=lambda x: x[0] > 0.15 * lam and x[1] > 0.15 * lam)

    def sens(m, f0):
        corto = delta(f_MHz, diametro_mm, x[0] - 5, x[1] - 5, p["centro_mm"])
        return {"sensibilidad_MHz_por_mm": (minimo_roe(corto, 0.9 * f_MHz, 1.15 * f_MHz) - f0) / 5, "sensibilidad_pieza": "la base y la altura"}

    return _con_resultados(construir(x), f_MHz, {"base_mm": x[0], "alto_mm": x[1], "centro_mm": p["centro_mm"]}, sens)


def ajustar_apilados(f_MHz: float, diametro_mm: float) -> dict:
    """Cuatro dipolos apilados en fase: ajusta el largo de los dipolos, la separación y el largo de las líneas de fase para
    |S11| mínimo a f, con al menos 9 dBi de ganancia."""
    from .generadores import apilados, apilados_por_defecto
    p = apilados_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    claves = ("dipolo_mm", "separacion_mm", "linea_mm")
    construir = lambda x: apilados(f_MHz, diametro_mm, x[0], x[1], x[2])  # noqa: E731
    n = p["n_dipolos"]

    def penal(m):
        return 0.01 * max(0.0, 9.0 - motor.simular(m, Barrido(f_MHz, f_MHz, 1)).ganancia_max[0])

    x = _nm_gamma(f_MHz, construir, [p[k] for k in claves], [0.01 * lam, 0.03 * lam, 0.03 * lam],
                  valido=lambda x: x[0] > 0.3 * lam and x[1] > 0.3 * lam and x[2] >= (n - 1) / 2 * x[1] + 20.0, penalizacion=penal)
    geometria = dict(zip(claves, x))
    geometria.update({"n_dipolos": n, "z0_linea": p["z0_linea"], "vf_linea": p["vf_linea"]})
    return _con_resultados(construir(x), f_MHz, geometria)


def ajustar_yagi_bibanda(f_baja: float, diametro_mm: float) -> dict:
    """Yagi de dos bandas: ajusta el largo de los dos dipolos para 50 Ω en las dos bandas (el resto de cotas son las de partida,
    ya optimizadas con la dirección del haz), con una penalización si el haz de la banda alta no sale hacia delante.
    Los resultados son los de la banda baja; los de la alta van en `resultados["alta"]`."""
    from .generadores import YAGIB_GANANCIA_MIN, yagi_bibanda, yagi_bibanda_por_defecto
    p = yagi_bibanda_por_defecto(f_baja)
    f_alta = p["f_alta_MHz"]
    claves = ("dipolo_bajo_mm", "dipolo_alto_mm")
    construir = lambda x: yagi_bibanda(f_baja, diametro_mm, dipolo_bajo_mm=x[0], dipolo_alto_mm=x[1])  # noqa: E731

    def coste(x):
        if x[0] < 0.3 * p["dipolo_bajo_mm"] or x[1] < 0.5 * p["dipolo_alto_mm"]:
            return 10.0
        m = construir(x)
        try:
            gan = motor.ganancias_en(m, f_alta, [(90.0, 90.0)])[0]
        except RuntimeError:
            return 10.0
        return _gamma_en(m, f_baja) + _gamma_en(m, f_alta) + 0.05 * max(0.0, YAGIB_GANANCIA_MIN - gan)

    x0 = [p[k] for k in claves]
    pasos = [0.01 * x0[0], 0.02 * x0[1]]
    x, _ = nelder_mead(coste, x0, pasos, tolerancia=1e-5, iteraciones=120)
    x, _ = nelder_mead(coste, x, [e / 4 for e in pasos], tolerancia=1e-7, iteraciones=120)
    modelo = construir(x)
    r = _resultados(modelo, f_baja)
    r["f_minimo_roe_MHz"] = minimo_roe(modelo, 0.9 * f_baja, 1.1 * f_baja)
    r["ganancia_frente_dBi"] = motor.ganancias_en(modelo, f_baja, [(90.0, 90.0)])[0]
    alta = _resultados(modelo, f_alta)
    alta["f_minimo_roe_MHz"] = minimo_roe(modelo, 0.95 * f_alta, 1.05 * f_alta)
    alta["ganancia_frente_dBi"] = motor.ganancias_en(modelo, f_alta, [(90.0, 90.0)])[0]
    r["alta"] = alta
    return {"geometria": {**p, "dipolo_bajo_mm": x[0], "dipolo_alto_mm": x[1]}, "resultados": r}


def ajustar_vinv(f_MHz: float, diametro_mm: float, apertura: float = 120.0) -> dict:
    """Dipolo en V invertida con |S11| mínimo a f: ajusta el largo de los brazos (la apertura queda fija)."""
    p = vinv_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    construir = lambda x: vinv(f_MHz, diametro_mm, brazo_mm=x[0], apertura=apertura)  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["brazo_mm"]], [0.01 * lam], valido=lambda x: x[0] > 0)

    def sens(m, f0):
        corto = vinv(f_MHz, diametro_mm, brazo_mm=x[0] - 5, apertura=apertura)
        return {"sensibilidad_MHz_por_mm": (minimo_roe(corto, 0.9 * f_MHz, 1.15 * f_MHz) - f0) / 5, "sensibilidad_pieza": "cada brazo"}

    return _con_resultados(construir(x), f_MHz, {"brazo_mm": x[0], "apertura": apertura}, sens)


def ajustar_yagi(f_MHz: float, diametro_mm: float, ganancia_minima_dBi: float | None = None, n_elementos: int = 3,
                 boom: str = "ninguno", boom_mm: float | None = None) -> dict:
    """Yagi de N elementos: ajusta el excitado, el reflector, los directores y el plegado para |S11| mínimo a f, sin bajar de
    la ganancia mínima hacia delante (+y) ni de 12 dB de relación delante/detrás (las separaciones del eje quedan fijas).

    El eje (`boom`, `boom_mm`) no entra en la simulación: se guarda con las cotas y los planos añaden su corrección de corte."""
    p = yagi_por_defecto(f_MHz, n_elementos, boom_mm)
    lam = 299792.458 / f_MHz
    objetivo = ganancia_minima_dBi if ganancia_minima_dBi is not None else 7.0 + 1.5 * (n_elementos - 3)
    nd = n_elementos - 2

    def construir(x):
        return yagi(f_MHz, diametro_mm, reflector_mm=x[1], excitado_mm=x[0], sep_reflector_mm=p["sep_reflector_mm"],
                    sep_plegado_mm=x[2], directores_mm=list(x[3:]), seps_directores_mm=p["seps_directores_mm"])

    def penal(m):
        frente, atras = motor.ganancias_en(m, f_MHz, [(90.0, 90.0), (90.0, 270.0)])
        return 0.05 * max(0.0, objetivo - frente) + 0.01 * max(0.0, 12.0 - (frente - atras))

    def valido(x):
        return (x[0] > 0 and x[1] > x[0] * 0.95 and 2.5 * diametro_mm < x[2] < 0.06 * lam
                and all(0.3 * lam < d < x[0] * 1.02 for d in x[3:])
                and all(b <= a + 1e-9 for a, b in zip(x[3:], x[4:])))        # los directores no crecen hacia delante

    x = _nm_gamma(f_MHz, construir, [p["excitado_mm"], p["reflector_mm"], p["sep_plegado_mm"], *p["directores_mm"]],
                  [0.02 * lam, 0.02 * lam, 0.004 * lam] + [0.02 * lam] * nd, valido=valido, penalizacion=penal)
    geometria = {"reflector_mm": x[1], "excitado_mm": x[0], "director_mm": x[3], "sep_reflector_mm": p["sep_reflector_mm"],
                 "sep_director_mm": p["seps_directores_mm"][0], "sep_plegado_mm": x[2], "n_elementos": float(n_elementos),
                 "directores_mm": list(x[3:]), "seps_directores_mm": p["seps_directores_mm"], "boom": boom, "boom_mm": p["boom_mm"]}
    r = _con_resultados(construir(x), f_MHz, geometria)
    frente, atras = motor.ganancias_en(construir(x), f_MHz, [(90.0, 90.0), (90.0, 270.0)])
    r["resultados"].update({"ganancia_frente_dBi": frente, "relacion_delante_detras_dB": frente - atras})
    return r


def ajustar_biconica(f_min_MHz: float, diametro_mm: float, varillas: int = 8) -> dict:
    """Bicónica con el límite inferior de ROE < 2 en `f_min_MHz`: escala los conos (como `ajustar_discone`)."""
    def construir(k):
        p = biconica_por_defecto(f_min_MHz, k)
        return biconica(f_min_MHz, diametro_mm, cono_mm=p["cono_mm"], hueco_mm=p["hueco_mm"], semiangulo=p["semiangulo"],
                        varillas=varillas, barrido=Barrido(0.6 * f_min_MHz, 4.0 * f_min_MHz, 81))

    k, mejor = 1.0, (float("inf"), 1.0)
    for _ in range(6):
        r = motor.simular(construir(k), diagrama=False)
        buenas = [f for f, ro in zip(r.frecuencias, r.roe) if ro < 2.0]
        if not buenas:
            k = min(1.8, k * 1.2)
            continue
        mejor = min(mejor, (abs(math.log(buenas[0] / f_min_MHz)), k))
        if mejor[0] < 0.01:
            break
        k = min(1.8, max(0.5, k * (buenas[0] / f_min_MHz) ** 0.7))
    k = mejor[1]
    p = biconica_por_defecto(f_min_MHz, k)
    r = motor.simular(construir(k), diagrama=False)
    buenas = [f for f, ro in zip(r.frecuencias, r.roe) if ro < 2.0]
    f_inf, f_sup = (buenas[0], buenas[-1]) if buenas else (0.0, 0.0)
    centro = motor.simular(biconica(f_min_MHz, diametro_mm, cono_mm=p["cono_mm"], hueco_mm=p["hueco_mm"], semiangulo=p["semiangulo"],
                                    varillas=varillas, barrido=Barrido(1.5 * f_min_MHz, 1.5 * f_min_MHz, 1)))
    resultados = {"motor": "PyNEC", "z0_ohm": Z0, "f_MHz": f_min_MHz, "f_inferior_roe2_MHz": f_inf, "f_superior_roe2_MHz": f_sup,
                  "relacion_banda": (f_sup / f_inf) if f_inf else 0.0, "ganancia_dBi": centro.ganancia_max[0],
                  "f_ganancia_MHz": 1.5 * f_min_MHz, "barrido": {"f_MHz": list(r.frecuencias), "roe": list(r.roe)}}
    return {"geometria": {"cono_mm": p["cono_mm"], "hueco_mm": p["hueco_mm"], "semiangulo": p["semiangulo"], "varillas": float(varillas)},
            "resultados": resultados}


def ajustar_torniquete(f_MHz: float, diametro_mm: float) -> dict:
    """Torniquete con |S11| mínimo a f y razón axial baja hacia el cénit: ajusta el largo de los brazos y el de la línea
    (75 Ω). Si solo se mirase |S11| los brazos se alargarían y se perdería la cuadratura (la razón axial pasó de 0,5 a 5,5 dB)."""
    p = torniquete_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    construir = lambda x: torniquete(f_MHz, diametro_mm, brazo_mm=x[0], sep_mm=p["sep_mm"], linea_mm=x[1])  # noqa: E731
    penal = lambda m: 0.04 * motor.razon_axial_dB(m, f_MHz)  # noqa: E731
    valido = lambda x: x[0] > 0 and 0.5 * p["linea_mm"] < x[1] < 1.6 * p["linea_mm"]  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["brazo_mm"], p["linea_mm"]], [0.01 * lam, 0.01 * lam], valido=valido, penalizacion=penal)

    def sens(m, f0):
        corto = torniquete(f_MHz, diametro_mm, brazo_mm=x[0] - 5, sep_mm=p["sep_mm"], linea_mm=x[1])
        return {"sensibilidad_MHz_por_mm": (minimo_roe(corto, 0.9 * f_MHz, 1.15 * f_MHz) - f0) / 5, "sensibilidad_pieza": "cada brazo"}

    modelo = construir(x)
    r = _con_resultados(modelo, f_MHz, {"brazo_mm": x[0], "sep_mm": p["sep_mm"], "z0_linea": p["z0_linea"],
                                        "vf_linea": p["vf_linea"], "linea_mm": x[1]}, sens)
    r["resultados"]["razon_axial_cenit_dB"] = motor.razon_axial_dB(modelo, f_MHz)
    return r


def ajustar_batwing(f_MHz: float, diametro_mm: float, radios: int = BAT_RADIOS) -> dict:
    """Batwing con |S11| mínimo a f: ajusta el largo de las alas (el ancho de la punta es proporcional) y mide la banda de ROE < 2."""
    p = batwing_por_defecto(f_MHz)
    lam = 299792.458 / f_MHz
    construir = lambda x: batwing(f_MHz, diametro_mm, ala_mm=x[0], ancho_mm=x[0] * BAT_ANCHO, hueco_mm=p["hueco_mm"],  # noqa: E731
                                  radios=radios)
    x = _nm_gamma(f_MHz, construir, [p["ala_mm"]], [0.01 * lam], valido=lambda x: x[0] > 0)
    modelo = construir(x)
    r = _con_resultados(modelo, f_MHz, {"ala_mm": x[0], "ancho_mm": x[0] * BAT_ANCHO, "hueco_mm": p["hueco_mm"], "radios": float(radios)})
    barrido = motor.simular(modelo, Barrido(0.7 * f_MHz, 1.4 * f_MHz, 71), diagrama=False)
    k = min(range(len(barrido.roe)), key=lambda i: abs(barrido.frecuencias[i] - r["resultados"]["f_minimo_roe_MHz"]))
    i0 = i1 = k
    while i0 > 0 and barrido.roe[i0 - 1] < 2.0:
        i0 -= 1
    while i1 < len(barrido.roe) - 1 and barrido.roe[i1 + 1] < 2.0:
        i1 += 1
    if barrido.roe[k] < 2.0:
        r["resultados"].update({"f_inferior_roe2_MHz": barrido.frecuencias[i0], "f_superior_roe2_MHz": barrido.frecuencias[i1],
                                "ancho_roe2_pct": 100 * (barrido.frecuencias[i1] - barrido.frecuencias[i0]) / f_MHz})
    else:
        r["resultados"].update({"f_inferior_roe2_MHz": 0.0, "f_superior_roe2_MHz": 0.0, "ancho_roe2_pct": 0.0})
    return r


def _bandas_efhw(modelo: Modelo, bandas, z0: float) -> list[dict]:
    """ROE (contra `z0`), impedancia y ganancia de cada banda: en el centro y el peor de 5 puntos entre sus bordes."""
    sal = []
    for nombre, a, b in bandas:
        fs = [a + (b - a) * k / 4 for k in range(5)]
        r = motor.simular(modelo, Barrido(fs[0], fs[-1], 5), diagrama=False, z0=z0)
        c = motor.simular(modelo, Barrido(fs[2], fs[2], 1), diagrama=True, z0=z0)
        sal.append({"banda": nombre, "f_MHz": fs[2], "r_ohm": c.z[0].real, "x_ohm": c.z[0].imag, "roe": c.roe[0],
                    "roe_max": max(r.roe), "ganancia_dBi": c.ganancia_max[0]})
    return sal


def ajustar_efhw(f_MHz: float, diametro_mm: float, relacion: int = 49, altura_m: float = 10.0, suelo: str = "normal",
                 largo_max_m: float | None = None) -> dict:
    """EFHW: ajusta el largo del hilo y el contrapeso para la mejor ROE (contra 50 Ω × `relacion`) en la banda de diseño y en
    sus armónicos, con la banda de diseño pesando diez veces más. `largo_max_m` recorta el largo posible (poco sitio)."""
    p = efhw_por_defecto(f_MHz, relacion, altura_m, suelo)
    z0 = Z0 * relacion
    bandas = bandas_de(f_MHz, relacion)
    if not bandas:
        raise ValueError(f"{f_MHz:g} MHz no cae en ninguna banda de HF de la lista")
    pesos = [1.5 if a <= f_MHz <= b else 1.0 for _, a, b in bandas]
    centros = [(a + b) / 2 for _, a, b in bandas]
    centros = [f_MHz if a <= f_MHz <= b else c for (_, a, b), c in zip(bandas, centros)]
    tope = (largo_max_m or 1e9) * 1000

    def construir(x):
        return efhw(f_MHz, diametro_mm, largo_mm=x[0], contrapeso_mm=x[1], altura_mm=altura_m * 1000, suelo=suelo, relacion=relacion)

    def coste(x):
        if not (0.2 * p["largo_mm"] < x[0] <= min(1.3 * p["largo_mm"], tope) and 0 <= x[1] <= 2.0 * p["contrapeso_mm"]):
            return 10.0
        m = construir(x)
        peor = mean = 0.0
        for w, f in zip(pesos, centros):
            z = motor.simular(m, Barrido(f, f, 1), diagrama=False, z0=z0).z[0]
            g = w * abs((z - z0) / (z + z0))
            peor, mean = max(peor, g), mean + g / len(pesos)
        return 0.7 * peor + 0.3 * mean

    x0 = [min(p["largo_mm"], tope), p["contrapeso_mm"]]
    x, _ = nelder_mead(coste, x0, [0.02 * p["largo_mm"], 0.3 * p["contrapeso_mm"]], tolerancia=1e-5, iteraciones=150)
    x, _ = nelder_mead(coste, x, [0.004 * p["largo_mm"], 0.1 * p["contrapeso_mm"]], tolerancia=1e-7, iteraciones=150)
    modelo = construir(x)
    tabla = _bandas_efhw(modelo, bandas, z0)
    propia = next(b for b in tabla if b["banda"] == bandas[pesos.index(1.5)][0]) if 1.5 in pesos else tabla[0]
    resultados = {"motor": "PyNEC", "z0_ohm": z0, "f_MHz": f_MHz, "r_ohm": propia["r_ohm"], "x_ohm": propia["x_ohm"], "roe": propia["roe"],
                  "ganancia_dBi": propia["ganancia_dBi"], "bandas": tabla}
    geometria = {"largo_mm": x[0], "contrapeso_mm": x[1], "altura_mm": altura_m * 1000, "relacion": float(relacion), "suelo": suelo}
    return {"geometria": geometria, "resultados": resultados}


def _resultado_hf(modelo: Modelo, bandas, geometria: dict, z0: float = Z0) -> dict:
    tabla = _bandas_efhw(modelo, bandas, z0)
    propia = tabla[0]
    resultados = {"motor": "PyNEC", "z0_ohm": z0, "f_MHz": propia["f_MHz"], "r_ohm": propia["r_ohm"], "x_ohm": propia["x_ohm"],
                  "roe": propia["roe"], "ganancia_dBi": propia["ganancia_dBi"], "bandas": tabla}
    return {"geometria": geometria, "resultados": resultados}


def _gamma_en(modelo: Modelo, f: float, z0: float = Z0) -> float:
    """|S11| a `f` contra `z0`; 2 (peor que un reflejo total) si NEC rechaza la geometría (hilos que se pisan)."""
    try:
        z = motor.simular(modelo, Barrido(f, f, 1), diagrama=False, z0=z0).z[0]
    except RuntimeError:
        return 2.0
    return abs((z - z0) / (z + z0))


def ajustar_dipolo_hf(f_MHz: float, diametro_mm: float, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """Dipolo de HF sobre suelo real: ajusta el largo para la mejor ROE a 50 Ω en el centro de la banda."""
    p = dipolo_hf_por_defecto(f_MHz, altura_m, suelo)
    construir = lambda x: dipolo_hf(f_MHz, diametro_mm, largo_mm=x[0], altura_mm=altura_m * 1000, suelo=suelo)  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["largo_mm"]], [0.01 * p["largo_mm"]], valido=lambda x: 0.3 * p["largo_mm"] < x[0] < 1.3 * p["largo_mm"])
    return _resultado_hf(construir(x), [banda_hf(f_MHz)], {"largo_mm": x[0], "altura_mm": altura_m * 1000, "suelo": suelo})


def ajustar_vertical_hf(f_MHz: float, diametro_mm: float, altura_m: float = 2.0, suelo: str = "normal") -> dict:
    """Vertical de HF: ajusta el largo del radiador y el de los radiales para la mejor ROE a 50 Ω (con radiales elevados la R
    queda por debajo de 50 Ω, así que la ROE mínima no llega a 1)."""
    p = vertical_hf_por_defecto(f_MHz, altura_m, suelo)

    def construir(x):
        return vertical_hf(f_MHz, diametro_mm, radiador_mm=x[0], radial_mm=x[1], altura_mm=altura_m * 1000, suelo=suelo)

    def coste(x):
        if not (0.6 * p["radiador_mm"] < x[0] < 1.3 * p["radiador_mm"] and 0.5 * p["radial_mm"] < x[1] < 1.5 * p["radial_mm"]):
            return 10.0
        return _gamma_en(construir(x), f_MHz)

    x, _ = nelder_mead(coste, [p["radiador_mm"], p["radial_mm"]], [0.02 * p["radiador_mm"], 0.04 * p["radial_mm"]], tolerancia=1e-5, iteraciones=200)
    x, _ = nelder_mead(coste, x, [0.005 * p["radiador_mm"], 0.01 * p["radial_mm"]], tolerancia=1e-7, iteraciones=200)
    return _resultado_hf(construir(x), [banda_hf(f_MHz)], {"radiador_mm": x[0], "radial_mm": x[1], "radiales": p["radiales"],
                                                           "altura_mm": altura_m * 1000, "suelo": suelo})


def ajustar_vinv_hf(f_MHz: float, diametro_mm: float, altura_m: float = 12.0, suelo: str = "normal", apertura: float = 110.0) -> dict:
    """V invertida de HF: ajusta el largo de los brazos (la apertura queda fija)."""
    p = vinv_hf_por_defecto(f_MHz, altura_m, suelo)
    construir = lambda x: vinv_hf(f_MHz, diametro_mm, brazo_mm=x[0], apertura=apertura, altura_mm=altura_m * 1000, suelo=suelo)  # noqa: E731
    x = _nm_gamma(f_MHz, construir, [p["brazo_mm"]], [0.01 * p["brazo_mm"]], valido=lambda x: 0.3 * p["brazo_mm"] < x[0] < 1.3 * p["brazo_mm"])
    return _resultado_hf(construir(x), [banda_hf(f_MHz)],
                         {"brazo_mm": x[0], "apertura": apertura, "altura_mm": altura_m * 1000, "suelo": suelo})


def ajustar_abanico(f_MHz: float, diametro_mm: float, bandas: list[str], altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """Dipolo en abanico: ajusta el largo de cada hilo para la mejor ROE en el centro de su banda (los hilos se acoplan entre sí)."""
    p = abanico_por_defecto(bandas, altura_m, suelo)
    centros = [(banda_por_nombre(b)[1] + banda_por_nombre(b)[2]) / 2 for b in bandas]

    def construir(x):
        return abanico(f_MHz, diametro_mm, list(x), altura_mm=altura_m * 1000, suelo=suelo, sep_mm=p["sep_mm"])

    def coste(x):
        if any(not 0.3 * l0 < v < 1.3 * l0 for v, l0 in zip(x, p["largos_mm"])):
            return 10.0
        m = construir(x)
        return sum(_gamma_en(m, f) ** 2 for f in centros) / len(centros)

    # primero un hilo cada vez, de la banda más alta a la más baja (los hilos cortos apenas notan a los largos), y luego todos juntos
    x = list(p["largos_mm"])
    orden = sorted(range(len(bandas)), key=lambda k: -centros[k])
    for _ in range(2):
        for k in orden:
            def un_hilo(v, k=k):
                y = list(x)
                y[k] = v[0]
                return coste(y) if False else (10.0 if not 0.3 * p["largos_mm"][k] < v[0] < 1.3 * p["largos_mm"][k]
                                               else _gamma_en(construir(y), centros[k]))
            l0 = p["largos_mm"][k]
            mejor = min((0.7 + 0.02 * i for i in range(26)), key=lambda c: un_hilo([c * l0]))   # barrido grueso: la resonancia puede estar lejos
            v, _ = nelder_mead(un_hilo, [mejor * l0], [0.01 * l0], tolerancia=1e-6, iteraciones=60)
            x[k] = v[0]
    x, _ = nelder_mead(coste, x, [0.01 * l for l in p["largos_mm"]], tolerancia=1e-5, iteraciones=250)
    x, _ = nelder_mead(coste, x, [0.003 * l for l in p["largos_mm"]], tolerancia=1e-7, iteraciones=250)
    geometria = {"bandas": list(bandas), "largos_mm": list(x), "altura_mm": altura_m * 1000, "suelo": suelo, "sep_mm": p["sep_mm"]}
    return _resultado_hf(construir(x), [banda_por_nombre(b) for b in bandas], geometria)


def ajustar_trampas(f_MHz: float, diametro_mm: float, bandas: list[str], altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """Dipolo de dos bandas con trampas: ajusta el tramo interior y el exterior (la trampa queda en la banda alta)."""
    if len(bandas) != 2:
        raise ValueError("el dipolo con trampas es de dos bandas")
    baja, alta = sorted((banda_por_nombre(b) for b in bandas), key=lambda b: b[1])
    f_baja, f_alta = (baja[1] + baja[2]) / 2, (alta[1] + alta[2]) / 2
    p = trampas_por_defecto(f_baja, f_alta, altura_m, suelo)

    def construir(x):
        return trampas(f_baja, diametro_mm, f_alta, x[0], x[1], p["trampa_L_uH"], p["trampa_C_pF"], altura_mm=altura_m * 1000, suelo=suelo)

    def coste(x):
        if not (0.4 * p["interior_mm"] < x[0] < 1.5 * p["interior_mm"] and 0.1 * p["exterior_mm"] < x[1] < 2.5 * p["exterior_mm"]):
            return 10.0
        m = construir(x)
        return _gamma_en(m, f_baja) + _gamma_en(m, f_alta)

    x, _ = nelder_mead(coste, [p["interior_mm"], p["exterior_mm"]], [0.02 * p["interior_mm"], 0.05 * p["exterior_mm"]], tolerancia=1e-5, iteraciones=250)
    x, _ = nelder_mead(coste, x, [0.004 * p["interior_mm"], 0.01 * p["exterior_mm"]], tolerancia=1e-7, iteraciones=250)
    geometria = {**p, "interior_mm": x[0], "exterior_mm": x[1], "bandas": [baja[0], alta[0]], "f_baja_MHz": f_baja}
    return _resultado_hf(construir(x), [baja, alta], geometria)


def ajustar_g5rv(f_MHz: float, diametro_mm: float, altura_m: float = 10.0, suelo: str = "normal") -> dict:
    """G5RV a la escala de `f_MHz`: no se ajusta (es un diseño fijo); se da la ROE al pie de la escalerilla en cada banda de HF
    desde la suya hasta 10 m, que es lo que ve el coaxial: se usa con acoplador."""
    p = g5rv_por_defecto(f_MHz, altura_m, suelo)
    bandas = [b for b in BANDAS_HF if (b[1] + b[2]) / 2 >= 0.9 * f_MHz and b[0] != "60 m"]
    return _resultado_hf(g5rv(f_MHz, diametro_mm, largo_mm=p["largo_mm"], escalerilla_mm=p["escalerilla_mm"], altura_mm=altura_m * 1000, suelo=suelo),
                         bandas, p)


def ajustar_manga(f_MHz: float, cable) -> dict:
    """Dipolo de manga resonante (X = 0) a f ajustando el largo del radiador; la manga queda en λ/4."""
    from .coaxial import RADIADOR_MANGA, dipolo_manga

    lam_m = 299.792458 / f_MHz
    radiador = RADIADOR_MANGA * lam_m
    for _ in range(5):
        f, _ = motor.resonancia(dipolo_manga(f_MHz, cable, radiador_m=radiador), 0.8 * f_MHz, 1.2 * f_MHz)
        radiador *= f / f_MHz
    modelo = dipolo_manga(f_MHz, cable, radiador_m=radiador)
    f_res, z = motor.resonancia(modelo, 0.8 * f_MHz, 1.2 * f_MHz)
    f_corto, _ = motor.resonancia(dipolo_manga(f_MHz, cable, radiador_m=radiador - 0.01), 0.8 * f_MHz, 1.2 * f_MHz)
    resultados = _resultados(modelo, f_MHz)
    resultados.update({"f_resonancia_MHz": f_res, "r_resonancia_ohm": z.real,
                       "sensibilidad_MHz_por_mm": (f_corto - f_res) / 10, "sensibilidad_pieza": "el radiador"})
    return {"geometria": {"radiador_mm": radiador * 1000, "manga_mm": lam_m / 4 * 1000, "bajada_mm": lam_m / 2 * 1000},
            "resultados": resultados}


def red_adaptacion(z: complex, f_MHz: float, z0: float = Z0) -> dict:
    """Red en L sin pérdidas que lleva la impedancia `z` (vista en el punto de alimentación) a `z0`.

    Devuelve `x_serie_ohm` (reactancia en serie, + inductiva) y `b_paralelo_S` (susceptancia en paralelo, + capacitiva),
    y `orden`: «serie_luego_paralelo» (la serie al lado de la antena, el paralelo hacia la fuente; R < Z0) o
    «paralelo_luego_serie» (R > Z0 en la admitancia de la carga). Con los valores en henrios y faradios a `f_MHz`
    (`l_serie_nH` o `c_serie_pF`, `c_paralelo_pF` o `l_paralelo_nH`).
    """
    r, x = z.real, z.imag
    w = 2 * math.pi * f_MHz * 1e6
    if r < z0:
        xs = -x + math.sqrt(r * (z0 - r))
        z1 = complex(r, x + xs)
        bp = -(1 / z1).imag
        orden = "serie_luego_paralelo"
    else:
        y = 1 / z
        bp = -y.imag + math.sqrt(y.real * (1 / z0 - y.real))
        z1 = 1 / complex(y.real, y.imag + bp)
        xs = -z1.imag
        orden = "paralelo_luego_serie"
    d = {"orden": orden, "x_serie_ohm": xs, "b_paralelo_S": bp}
    d["l_serie_nH" if xs >= 0 else "c_serie_pF"] = abs(xs) / w * 1e9 if xs >= 0 else 1 / (w * -xs) * 1e12
    d["c_paralelo_pF" if bp >= 0 else "l_paralelo_nH"] = bp / w * 1e12 if bp >= 0 else 1 / (w * -bp) * 1e9
    return d


def z_con_red(z: complex, red: dict) -> complex:
    """Impedancia vista desde la fuente con la red de `red_adaptacion` (valores fijos) y la carga `z`."""
    xs, bp = red["x_serie_ohm"], red["b_paralelo_S"]
    if red["orden"] == "serie_luego_paralelo":
        z1 = z + 1j * xs
        return 1 / (1 / z1 + 1j * bp)
    y = 1 / z + 1j * bp
    return 1 / y + 1j * xs


def ajustar_coco(f_MHz: float, cable, tramos: int = 4, afinar_geometria: bool = False, max_perdida_dB: float = 1.5) -> dict:
    """CoCo lista para construir: geometría de partida (tramos de λ/2·VF, punta de λ/4) y la red en L que la adapta.

    Con solo el largo de los tramos y de la punta la ROE y la ganancia compiten (25-11-2026, 145 MHz, RG-58: ROE 4,6 /
    2,7 / 2,3 con 2 / 4 / 6 tramos pero la ganancia deja de subir con los tramos: 4,8 / 4,8 / 4,6 dBi frente a 4,4 /
    6,2 / 6,1 sin tocar). Por eso, por defecto la geometría no se toca y la adaptación va en una red en L en el
    conector, que no cambia el diagrama. `afinar_geometria=True` prueba también el largo de los tramos y de la punta
    (sin perder más de `max_perdida_dB`). La red es de banda estrecha: se da el ancho de ROE ≤ 2 que deja.
    """
    from .coaxial import colineal_coco

    def medir(k: float, p: float):
        r = motor.simular(colineal_coco(f_MHz, cable, tramos=tramos, factor_tramo=k, punta_lambda=p))
        return r.roe[0], r.ganancia_max[0], r.z[0]

    roe0, g0, z0 = medir(1.0, 0.25)
    k, p, roe, g, z = 1.0, 0.25, roe0, g0, z0
    if afinar_geometria:
        limite = g0 - max_perdida_dB

        def coste(x):
            if not (0.8 <= x[0] <= 1.2 and 0.0 <= x[1] <= 0.5):
                return 1e3
            r_, g_, _ = medir(*x)
            return r_ + 10.0 * max(0.0, limite - g_)

        arranque = min((coste([a, b]), a, b) for a in (0.88, 0.94, 1.0, 1.06) for b in (0.1, 0.17, 0.25, 0.32))[1:]
        (k, p), _ = nelder_mead(coste, list(arranque), [0.02, 0.02], tolerancia=1e-4, iteraciones=60)
        roe, g, z = medir(k, p)
        if roe >= roe0 and g < limite:
            k, p, roe, g, z = 1.0, 0.25, roe0, g0, z0
    red = red_adaptacion(z, f_MHz)
    modelo = colineal_coco(f_MHz, cable, tramos=tramos, factor_tramo=k, punta_lambda=p,
                           barrido=Barrido(f_MHz * 0.95, f_MHz * 1.05, 41))
    barrido = motor.simular(modelo, diagrama=False)
    roe_red = []
    for zz in barrido.z:
        gam = abs((z_con_red(zz, red) - Z0) / (z_con_red(zz, red) + Z0))
        roe_red.append((1 + gam) / (1 - gam) if gam < 1 else float("inf"))
    c = min(range(len(roe_red)), key=lambda i: abs(barrido.frecuencias[i] - f_MHz))
    a = b = c
    while a > 0 and roe_red[a - 1] <= 2.0:
        a -= 1
    while b < len(roe_red) - 1 and roe_red[b + 1] <= 2.0:
        b += 1
    return {
        "geometria": {"tramos": tramos, "factor_tramo": k, "punta_lambda": p},
        "red": red,
        "resultados": {"motor": "PyNEC", "z0_ohm": Z0, "f_MHz": f_MHz, "r_ohm": z.real, "x_ohm": z.imag,
                       "roe_sin_red": roe, "roe_con_red": roe_red[c], "ganancia_dBi": g,
                       "ancho_roe2_MHz": barrido.frecuencias[b] - barrido.frecuencias[a],
                       "roe_sin_ajustar": roe0, "ganancia_sin_ajustar_dBi": g0},
    }
