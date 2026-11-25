"""Ajuste de las cotas con el motor (solo escritorio: necesita PyNEC).

Devuelve las cotas ajustadas y los resultados simulados como diccionarios que van tal cual a `diseno.json`;
el generador de planos los lee de ahí y no llama nunca al motor.
"""

from __future__ import annotations

import math

from . import motor
from .generadores import dipolo, jpole, jpole_por_defecto
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
