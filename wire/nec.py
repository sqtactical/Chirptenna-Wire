"""Exportador e intérprete de mazos NEC2 (`.nec`).

El motor no llama a PyNEC desde el `Modelo` directamente: exporta el mazo, lo vuelve a leer y ejecuta esas
tarjetas. Así lo que se simula es exactamente el `.nec` que el usuario abre en 4nec2, xnec2c o nec2c.

Formato: una tarjeta por línea, nombre de dos letras y campos separados por espacios (el formato libre que
aceptan nec2c, xnec2c y 4nec2). Solo ASCII: los comentarios se pasan sin tildes.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .modelo import Carga, Conductividad, Modelo

# Tarjetas que se escriben y se leen. Cada una con el número de enteros y de reales que lleva.
CAMPOS = {
    "GW": (2, 7),
    "GE": (1, 0),
    "GN": (4, 6),
    "EX": (4, 6),
    "TL": (4, 6),
    "LD": (4, 3),
    "FR": (4, 2),
    "RP": (4, 6),
    "EN": (0, 0),
}

# Diagrama por defecto: cada 5° en θ (0–180) y φ (0–355). XNDA = 1000: polarización vertical/horizontal,
# sin normalizar, ganancia de potencia, sin promediar.
RP_POR_DEFECTO = ([0, 37, 72, 1000], [0.0, 0.0, 5.0, 5.0, 0.0, 0.0])


@dataclass(frozen=True)
class Tarjeta:
    nombre: str
    enteros: tuple[int, ...] = ()
    reales: tuple[float, ...] = ()

    def texto(self) -> str:
        campos = [self.nombre, *(str(i) for i in self.enteros), *(_real(x) for x in self.reales)]
        return " ".join(campos)


def _real(x: float) -> str:
    if x == 0:
        return "0"
    return f"{x:.9g}"


def _ascii(texto: str) -> str:
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def tarjetas(modelo: Modelo, diagrama: bool = True) -> list[Tarjeta]:
    """Las tarjetas de geometría y de control del modelo, de GW a EN (sin CM/CE)."""
    t: list[Tarjeta] = []
    for etiqueta, h in enumerate(modelo.hilos, start=1):
        t.append(Tarjeta("GW", (etiqueta, h.segmentos), (*h.inicio, *h.fin, h.radio)))
    if modelo.plano_masa:
        t.append(Tarjeta("GE", (1 if modelo.toca_el_suelo else -1,)))
        t.append(Tarjeta("GN", (1, 0, 0, 0), (0.0,) * 6))
    else:
        t.append(Tarjeta("GE", (0,)))
        t.append(Tarjeta("GN", (-1, 0, 0, 0), (0.0,) * 6))
    for carga in modelo.cargas:
        if isinstance(carga, Carga):
            t.append(Tarjeta("LD", (1 if carga.paralela else 0, carga.hilo, carga.segmento_inicial, carga.segmento_final),
                             (carga.r, carga.l, carga.c)))
        elif isinstance(carga, Conductividad):
            t.append(Tarjeta("LD", (5, 0, 0, 0), (carga.sigma, 0.0, 0.0)))
    p = modelo.puerto
    t.append(Tarjeta("EX", (0, p.hilo, p.segmento, 0), (p.tension.real, p.tension.imag, 0.0, 0.0, 0.0, 0.0)))
    for linea in modelo.lineas:
        z0 = -linea.z0 if linea.cruzada else linea.z0
        t.append(Tarjeta("TL", (linea.hilo1, linea.segmento1, linea.hilo2, linea.segmento2),
                         (z0, linea.longitud_electrica, 0.0, 0.0, 0.0, 0.0)))
    b = modelo.barrido
    f0, df, n = (b.f_inicial, b.incremento, b.pasos) if b else (modelo.f_MHz, 0.0, 1)
    t.append(Tarjeta("FR", (0, n, 0, 0), (f0, df)))
    if diagrama:
        enteros, reales = RP_POR_DEFECTO
        t.append(Tarjeta("RP", tuple(enteros), tuple(reales)))
    t.append(Tarjeta("EN"))
    return t


def exportar(modelo: Modelo, diagrama: bool = True) -> str:
    """El mazo `.nec` completo del modelo, con CM/CE de cabecera."""
    comentarios = [modelo.nombre, *modelo.comentarios, "Generado por Chirptenna Wire"]
    lineas = [f"CM {_ascii(c)}" for c in comentarios]
    lineas.append("CE")
    lineas += [t.texto() for t in tarjetas(modelo, diagrama)]
    return "\n".join(lineas) + "\n"


def guardar(modelo: Modelo, ruta, diagrama: bool = True) -> None:
    with open(ruta, "w", encoding="ascii", newline="\n") as f:
        f.write(exportar(modelo, diagrama))


def leer(texto: str) -> list[Tarjeta]:
    """Lee un mazo `.nec` (de los que escribe `exportar`) y devuelve sus tarjetas, sin CM/CE.

    No es un intérprete NEC2 completo: rechaza las tarjetas que este proyecto no usa.
    """
    resultado: list[Tarjeta] = []
    for numero, linea in enumerate(texto.splitlines(), start=1):
        linea = linea.strip()
        if not linea:
            continue
        nombre, *campos = linea.replace(",", " ").split()
        nombre = nombre.upper()
        if nombre in ("CM", "CE"):
            continue
        if nombre not in CAMPOS:
            raise ValueError(f"línea {numero}: tarjeta {nombre} no admitida")
        n_ent, n_real = CAMPOS[nombre]
        if len(campos) > n_ent + n_real:
            raise ValueError(f"línea {numero}: demasiados campos en {nombre}")
        campos += ["0"] * (n_ent + n_real - len(campos))
        try:
            enteros = tuple(int(c) for c in campos[:n_ent])
            reales = tuple(float(c) for c in campos[n_ent:])
        except ValueError as e:
            raise ValueError(f"línea {numero}: campo no numérico en {nombre}") from e
        resultado.append(Tarjeta(nombre, enteros, reales))
        if nombre == "EN":
            break
    if not resultado or resultado[-1].nombre != "EN":
        raise ValueError("el mazo no termina en EN")
    return resultado
