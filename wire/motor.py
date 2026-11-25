"""Motor de simulación con PyNEC (interfaz de Python de necpp, derivado de NEC2).

`simular` exporta el modelo a `.nec`, lo vuelve a leer y ejecuta esas tarjetas en PyNEC, de modo que lo que se
simula es el mismo mazo que se entrega al usuario. `ejecutar_nec2c` pasa el mazo por el ejecutable nec2c, si está
instalado, para contrastar.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, replace

from . import nec
from .modelo import Barrido, Modelo

Z0_POR_DEFECTO = 50.0


@dataclass(frozen=True)
class Resultado:
    frecuencias: tuple[float, ...]  # MHz
    z: tuple[complex, ...]  # impedancia de entrada, Ω
    z0: float  # impedancia de referencia de S11 y ROE
    ganancia_max: tuple[float, ...] | None  # dBi, máximo del diagrama en cada frecuencia

    @property
    def s11(self) -> tuple[complex, ...]:
        return tuple((z - self.z0) / (z + self.z0) for z in self.z)

    @property
    def s11_dB(self) -> tuple[float, ...]:
        import math
        return tuple(20 * math.log10(max(abs(g), 1e-12)) for g in self.s11)

    @property
    def roe(self) -> tuple[float, ...]:
        return tuple(float("inf") if abs(g) >= 1 else (1 + abs(g)) / (1 - abs(g)) for g in self.s11)


def disponible() -> bool:
    """True si PyNEC se puede importar."""
    try:
        import PyNEC  # noqa: F401
    except ImportError:
        return False
    return True


def _contexto(tarjetas: list[nec.Tarjeta]):
    """Carga las tarjetas en un contexto de PyNEC y lo ejecuta: (contexto, frecuencias, hay_diagrama)."""
    from PyNEC import nec_context

    contexto = nec_context()
    geometria = contexto.get_geometry()
    frecuencias: list[float] = []
    con_diagrama = False
    for t in tarjetas:
        i, r = t.enteros, t.reales
        if t.nombre == "GW":
            geometria.wire(i[0], i[1], *r[:6], r[6], 1.0, 1.0)
        elif t.nombre == "GE":
            contexto.geometry_complete(i[0])
        elif t.nombre == "GN":
            contexto.gn_card(i[0], i[1], *r[:6])
        elif t.nombre == "LD":
            contexto.ld_card(*i, *r)
        elif t.nombre == "EX":
            contexto.ex_card(*i, *r)
        elif t.nombre == "TL":
            contexto.tl_card(*i, *r)
        elif t.nombre == "FR":
            if i[0] != 0:
                raise ValueError("solo se admiten barridos lineales (FR tipo 0)")
            frecuencias = [r[0] + k * r[1] for k in range(i[1])]
            contexto.fr_card(i[0], i[1], r[0], r[1])
        elif t.nombre == "RP":
            xnda = f"{i[3]:04d}"
            contexto.rp_card(i[0], i[1], i[2], *(int(d) for d in xnda), *r)
            con_diagrama = True
        elif t.nombre == "EN":
            if not con_diagrama:
                contexto.xq_card(0)
    return contexto, frecuencias, con_diagrama


def razon_axial_dB(modelo: Modelo, f_MHz: float, theta_grados: float = 0.0) -> float:
    """Razón axial (dB, 0 = circular perfecta) del campo en la dirección θ (0° = +z) a `f_MHz`; el primer φ del diagrama."""
    import math
    texto = nec.exportar(replace(modelo, barrido=Barrido(f_MHz, f_MHz, 1)), diagrama=True)
    contexto, _, _ = _contexto(nec.leer(texto))
    patron = contexto.get_radiation_pattern(0)
    k = min(range(patron.get_ntheta()), key=lambda i: abs(patron.get_theta_angles()[i] - theta_grados))
    r = max(float(patron.get_pol_axial_ratio()[k * patron.get_nphi()]), 1e-9)   # NEC: menor/mayor (de 0 a 1); matriz θ × φ en fila
    return -20 * math.log10(min(r, 1.0))


def ganancias_en(modelo: Modelo, f_MHz: float, direcciones: list[tuple[float, float]]) -> list[float]:
    """Ganancia (dBi) del diagrama a `f_MHz` en cada dirección (θ, φ) en grados, a la rejilla más cercana de 5°."""
    import numpy as np
    texto = nec.exportar(replace(modelo, barrido=Barrido(f_MHz, f_MHz, 1)), diagrama=True)
    contexto, _, _ = _contexto(nec.leer(texto))
    patron = contexto.get_radiation_pattern(0)
    g = np.array(patron.get_gain()).reshape(patron.get_ntheta(), patron.get_nphi())
    th, ph = np.array(patron.get_theta_angles()), np.array(patron.get_phi_angles())
    return [float(g[int(np.argmin(abs(th - t))), int(np.argmin(abs(ph - (p % 360.0))))]) for t, p in direcciones]


def ejecutar_tarjetas(tarjetas: list[nec.Tarjeta], z0: float = Z0_POR_DEFECTO) -> Resultado:
    """Ejecuta en PyNEC una lista de tarjetas (las de `nec.leer`)."""
    contexto, frecuencias, con_diagrama = _contexto(tarjetas)
    impedancias = []
    ganancias = [] if con_diagrama else None
    for k in range(len(frecuencias)):
        z = contexto.get_input_parameters(k).get_impedance()
        impedancias.append(complex(z[0]))
        if ganancias is not None:
            ganancias.append(float(contexto.get_radiation_pattern(k).get_gain().max()))
    return Resultado(tuple(frecuencias), tuple(impedancias), z0, tuple(ganancias) if ganancias is not None else None)


def simular_nec(texto: str, z0: float = Z0_POR_DEFECTO) -> Resultado:
    """Simula un mazo `.nec` en PyNEC."""
    return ejecutar_tarjetas(nec.leer(texto), z0)


def simular(
    modelo: Modelo,
    barrido: Barrido | None = None,
    diagrama: bool = True,
    z0: float = Z0_POR_DEFECTO,
) -> Resultado:
    """Z de entrada, S11/ROE y ganancia máxima del modelo, en su barrido o en el que se pase."""
    if barrido is not None:
        modelo = replace(modelo, barrido=barrido)
    return simular_nec(nec.exportar(modelo, diagrama=diagrama), z0)


def resonancia(modelo: Modelo, f_min: float, f_max: float, pasos: int = 41, tolerancia_MHz: float = 1e-5):
    """Primera frecuencia en [f_min, f_max] donde X pasa de negativa a positiva. Devuelve (f_MHz, Z)."""
    r = simular(modelo, Barrido(f_min, f_max, pasos), diagrama=False)
    for k in range(len(r.frecuencias) - 1):
        if r.z[k].imag < 0 <= r.z[k + 1].imag:
            a, b = r.frecuencias[k], r.frecuencias[k + 1]
            xa, xb = r.z[k].imag, r.z[k + 1].imag
            break
    else:
        raise ValueError(f"no hay resonancia serie entre {f_min} y {f_max} MHz")
    # Bisección con paso de secante (regula falsi de Illinois): converge en pocas llamadas.
    lado = 0
    for _ in range(60):
        f = b - xb * (b - a) / (xb - xa)
        z = simular(modelo, Barrido(f, f, 1), diagrama=False).z[0]
        if abs(b - a) < tolerancia_MHz or z.imag == 0:
            return f, z
        if z.imag < 0:
            a, xa = f, z.imag
            if lado == -1:
                xb /= 2
            lado = -1
        else:
            b, xb = f, z.imag
            if lado == 1:
                xa /= 2
            lado = 1
    return f, z


# ---------------------------------------------------------------- nec2c (alternativa y contraste)

def ruta_nec2c() -> str | None:
    return shutil.which("nec2c")


def ejecutar_nec2c(texto: str) -> list[complex]:
    """Pasa el mazo por nec2c y devuelve la Z de entrada de cada frecuencia (lee la salida de texto)."""
    ejecutable = ruta_nec2c()
    if not ejecutable:
        raise FileNotFoundError("nec2c no está instalado")
    with tempfile.TemporaryDirectory() as carpeta:
        entrada = os.path.join(carpeta, "modelo.nec")
        salida = os.path.join(carpeta, "modelo.out")
        with open(entrada, "w", encoding="ascii", newline="\n") as f:
            f.write(texto)
        subprocess.run([ejecutable, "-i", entrada, "-o", salida], check=True, capture_output=True)
        with open(salida, encoding="ascii", errors="replace") as f:
            return leer_salida_nec2c(f.read())


_NUMERO = re.compile(r"^[-+]?\d")


def leer_salida_nec2c(salida: str) -> list[complex]:
    """Impedancias del bloque «ANTENNA INPUT PARAMETERS» de una salida NEC2 (una por frecuencia)."""
    impedancias = []
    lineas = salida.splitlines()
    for k, linea in enumerate(lineas):
        if "ANTENNA INPUT PARAMETERS" not in linea:
            continue
        for siguiente in lineas[k + 1:k + 8]:
            campos = siguiente.split()
            if len(campos) >= 8 and all(_NUMERO.match(c) for c in campos[:8]) and campos[0].isdigit():
                impedancias.append(complex(float(campos[6]), float(campos[7])))
                break
    return impedancias
