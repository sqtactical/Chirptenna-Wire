"""Modelo de hilos: lo que NEC2 sabe resolver (hilos con radio, líneas de transmisión, puerto y cargas).

Unidades internas: metros, ohmios, henrios, faradios y MHz para la frecuencia (como las tarjetas NEC2).
Los hilos se numeran (etiqueta NEC, «tag») por su orden en `Modelo.hilos`, empezando en 1.
Los segmentos también se numeran desde 1, como en NEC2.
"""

from __future__ import annotations

from dataclasses import dataclass, field

C0 = 299_792_458.0  # velocidad de la luz en el vacío, m/s

Punto = tuple[float, float, float]


def longitud_onda_m(f_MHz: float) -> float:
    """Longitud de onda en el vacío, en metros."""
    return C0 / (f_MHz * 1e6)


@dataclass(frozen=True)
class Hilo:
    """Tramo recto de hilo entre dos puntos (m), con su radio (m) y el número de segmentos."""

    inicio: Punto
    fin: Punto
    radio: float
    segmentos: int

    def __post_init__(self) -> None:
        if self.radio <= 0:
            raise ValueError("el radio del hilo debe ser positivo")
        if self.segmentos < 1:
            raise ValueError("el hilo necesita al menos un segmento")
        if self.longitud == 0:
            raise ValueError("el hilo no puede tener longitud cero")

    @property
    def longitud(self) -> float:
        return sum((b - a) ** 2 for a, b in zip(self.inicio, self.fin)) ** 0.5

    @property
    def longitud_segmento(self) -> float:
        return self.longitud / self.segmentos


@dataclass(frozen=True)
class Puerto:
    """Fuente de tensión (EX tipo 0) en el segmento `segmento` del hilo `hilo` (ambos desde 1)."""

    hilo: int
    segmento: int
    tension: complex = 1.0 + 0j


@dataclass(frozen=True)
class Linea:
    """Línea de transmisión sin pérdidas (tarjeta TL) entre dos segmentos.

    `longitud` es la física, en metros; NEC2 no conoce el factor de velocidad, así que en la tarjeta va la
    longitud eléctrica = longitud / vf. `cruzada` invierte la polaridad de un extremo (Z0 negativo en NEC2),
    que es lo que hacen los cruces vivo–malla de una CoCo.
    """

    hilo1: int
    segmento1: int
    hilo2: int
    segmento2: int
    z0: float
    longitud: float
    vf: float = 1.0
    cruzada: bool = False

    def __post_init__(self) -> None:
        if self.z0 <= 0:
            raise ValueError("Z0 debe ser positivo (usa cruzada=True para invertir la línea)")
        if not 0 < self.vf <= 1:
            raise ValueError("el factor de velocidad debe estar en (0, 1]")
        if self.longitud < 0:
            raise ValueError("la longitud de la línea no puede ser negativa")

    @property
    def longitud_electrica(self) -> float:
        return self.longitud / self.vf


@dataclass(frozen=True)
class Carga:
    """Carga RLC en serie (LD tipo 0) en los segmentos `segmento_inicial`..`segmento_final` de un hilo."""

    hilo: int
    segmento_inicial: int
    segmento_final: int
    r: float = 0.0
    l: float = 0.0
    c: float = 0.0
    paralela: bool = False  # True: R, L y C en paralelo (LD tipo 1), como un choke resonante


@dataclass(frozen=True)
class Conductividad:
    """Conductividad del metal (LD tipo 5), en S/m, aplicada a todos los hilos. Cobre ≈ 5,8e7."""

    sigma: float


@dataclass(frozen=True)
class Barrido:
    """Barrido lineal de frecuencias: `pasos` puntos de `f_inicial` a `f_final` (MHz)."""

    f_inicial: float
    f_final: float
    pasos: int = 1

    def __post_init__(self) -> None:
        if self.pasos < 1:
            raise ValueError("el barrido necesita al menos un paso")
        if self.pasos == 1 and self.f_final != self.f_inicial:
            raise ValueError("con un solo paso, f_final debe ser igual a f_inicial")

    @property
    def incremento(self) -> float:
        return 0.0 if self.pasos == 1 else (self.f_final - self.f_inicial) / (self.pasos - 1)

    @property
    def frecuencias(self) -> list[float]:
        return [self.f_inicial + i * self.incremento for i in range(self.pasos)]


@dataclass(frozen=True)
class Modelo:
    """Una antena lista para NEC2: hilos, puerto, líneas, cargas, frecuencia de diseño y suelo."""

    nombre: str
    f_MHz: float
    hilos: tuple[Hilo, ...]
    puerto: Puerto
    lineas: tuple[Linea, ...] = ()
    cargas: tuple[Carga | Conductividad, ...] = ()
    plano_masa: bool = False  # False: espacio libre; True: suelo perfecto en z = 0
    barrido: Barrido | None = None  # si no hay, solo la frecuencia de diseño
    comentarios: tuple[str, ...] = field(default=())
    suelo: tuple[float, float] | None = None  # suelo real en z = 0: (εr, conductividad en S/m); en HF cambia mucho la antena

    def __post_init__(self) -> None:
        if not self.hilos:
            raise ValueError("el modelo necesita al menos un hilo")
        self._comprobar_segmento(self.puerto.hilo, self.puerto.segmento, "puerto")
        for linea in self.lineas:
            self._comprobar_segmento(linea.hilo1, linea.segmento1, "línea")
            self._comprobar_segmento(linea.hilo2, linea.segmento2, "línea")
        for carga in self.cargas:
            if isinstance(carga, Carga):
                self._comprobar_segmento(carga.hilo, carga.segmento_inicial, "carga")
                self._comprobar_segmento(carga.hilo, carga.segmento_final, "carga")

    def _comprobar_segmento(self, hilo: int, segmento: int, que: str) -> None:
        if not 1 <= hilo <= len(self.hilos):
            raise ValueError(f"{que}: no existe el hilo {hilo}")
        if not 1 <= segmento <= self.hilos[hilo - 1].segmentos:
            raise ValueError(f"{que}: el hilo {hilo} no tiene el segmento {segmento}")

    @property
    def frecuencias(self) -> list[float]:
        return self.barrido.frecuencias if self.barrido else [self.f_MHz]

    @property
    def toca_el_suelo(self) -> bool:
        return any(h.inicio[2] == 0 or h.fin[2] == 0 for h in self.hilos)
