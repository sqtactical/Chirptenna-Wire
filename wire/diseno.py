"""El diseño que se guarda en `diseno.json`: tipo, frecuencia, material, cotas, resultados y configuración del plano.

Python puro (corre en Pyodide). Las cotas van en mm al eje del alambre; los resultados, si los hay, los ha puesto
el motor en escritorio (`wire/ajuste.py`) y el plano solo los lee.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields

from . import generadores
from .modelo import Modelo

TIPOS = {
    "dipolo": "Dipolo de media onda",
    "jpole": "J-pole",
    "manga": "Dipolo de manga de coaxial",
    "coco": "Colineal CoCo de coaxial",
}

TIPOS_COAXIAL = ("manga", "coco")
CABLE_POR_DEFECTO = "RG-58"

ESTADOS = ("Simulado", "Medido", "Sin validar")

# Sobrante de corte por defecto (mm), según el tipo (`plano.sobrante_mm` lo cambia).
SOBRANTE = {"dipolo": 15.0, "jpole": 20.0, "manga": 15.0, "coco": 15.0}

BANDAS = [  # (nombre, f_min, f_max) en MHz: las bandas iniciales de la propuesta
    ("banda aérea", 118.0, 137.0),
    ("2 m", 144.0, 146.0),
    ("banda marina VHF", 156.0, 162.1),
    ("70 cm", 430.0, 440.0),
    ("PMR446", 446.0, 446.2),
    ("LoRa 868", 863.0, 870.0),
    ("LoRa 915", 902.0, 928.0),
    ("ADS-B", 1089.0, 1091.0),
]


def banda_de(f_MHz: float) -> tuple[str, float, float] | None:
    for b in BANDAS:
        if b[1] <= f_MHz <= b[2]:
            return b
    return None


@dataclass
class ConfigPlano:
    """Bloque `plano` de `diseno.json` (docs/PLANOS.md §6)."""

    papel: str = "A4"
    grandes: str = "mosaico"
    orientacion: str = "auto"
    solape_mm: float = 10.0
    unidades: str = "mm"
    idioma: str = "es"
    sobrante_mm: float | None = None  # None: el del tipo

    VALORES = {
        "papel": ("A4", "A3"),
        "grandes": ("A3", "mosaico", "sin_escala"),
        "orientacion": ("auto", "vertical", "apaisada"),
        "unidades": ("mm", "pulgadas"),
        "idioma": ("es", "en", "fr", "de"),
    }

    def __post_init__(self) -> None:
        for clave, validos in self.VALORES.items():
            if getattr(self, clave) not in validos:
                raise ValueError(f"plano.{clave} debe ser uno de {', '.join(validos)}")
        if not 0 <= self.solape_mm <= 20:
            raise ValueError("plano.solape_mm debe estar entre 0 y 20")
        if self.sobrante_mm is not None and self.sobrante_mm < 0:
            raise ValueError("plano.sobrante_mm no puede ser negativo")

    @classmethod
    def desde_dict(cls, datos: dict | None) -> "ConfigPlano":
        datos = dict(datos or {})
        conocidas = {f.name for f in fields(cls)}
        sobran = set(datos) - conocidas
        if sobran:
            raise ValueError(f"claves desconocidas en plano: {', '.join(sorted(sobran))}")
        return cls(**datos)


@dataclass
class Diseno:
    tipo: str
    f_MHz: float
    diametro_mm: float
    geometria: dict
    nombre: str = ""
    material: str = "varilla de latón o aluminio"
    resultados: dict | None = None
    estado: str = "Sin validar"
    plano: ConfigPlano = field(default_factory=ConfigPlano)
    version: int = 1
    # Antenas de coaxial: {"nombre", "z0", "vf", "vf_origen": "catálogo"|"medido"}; None en las de alambre.
    cable: dict | None = None

    def con_cable(self, c) -> "Diseno":
        """Guarda el cable usado y de dónde sale su VF (`wire.cables.Cable`)."""
        self.cable = {"nombre": c.nombre, "z0": c.z0, "vf": c.vf, "vf_origen": c.vf_origen}
        return self

    def __post_init__(self) -> None:
        if self.tipo not in TIPOS:
            raise ValueError(f"tipo desconocido: {self.tipo}")
        if self.estado not in ESTADOS:
            raise ValueError(f"estado desconocido: {self.estado}")
        if not self.nombre:
            self.nombre = f"{self.tipo}_{self.f_MHz:g}"

    @property
    def nombre_tipo(self) -> str:
        return TIPOS[self.tipo]

    @property
    def sobrante_mm(self) -> float:
        return SOBRANTE[self.tipo] if self.plano.sobrante_mm is None else self.plano.sobrante_mm

    def cable_obj(self):
        """El `Cable` del diseño (con el VF guardado, de catálogo o medido); solo en los tipos de coaxial."""
        from dataclasses import replace

        from .cables import cable
        if not self.cable:
            raise ValueError(f"el tipo {self.tipo} necesita un cable")
        return replace(cable(self.cable["nombre"]), vf=self.cable["vf"], vf_origen=self.cable["vf_origen"])

    def modelo(self) -> Modelo:
        """El modelo de hilos con estas cotas (sin motor)."""
        g = self.geometria
        if self.tipo == "manga":
            from . import coaxial
            return coaxial.dipolo_manga(self.f_MHz, self.cable_obj(), radiador_m=g["radiador_mm"] / 1000,
                                        manga_m=g["manga_mm"] / 1000, resto_m=g["bajada_mm"] / 1000)
        if self.tipo == "coco":
            from . import coaxial
            return coaxial.colineal_coco(self.f_MHz, self.cable_obj(), tramos=int(g["tramos"]),
                                         punta_lambda=g["punta_lambda"], factor_tramo=g["factor_tramo"])
        if self.tipo == "dipolo":
            return generadores.dipolo(self.f_MHz, self.diametro_mm / 2, longitud_mm=g["largo_total_mm"])
        return generadores.jpole(self.f_MHz, self.diametro_mm, largo_mm=g["largo_mm"], corto_mm=g["corto_mm"],
                                 toma_mm=g["toma_mm"], separacion_mm=g["separacion_mm"])

    def a_dict(self) -> dict:
        d = asdict(self)
        d["plano"] = asdict(self.plano)
        return d

    def a_json(self) -> str:
        return json.dumps(self.a_dict(), ensure_ascii=False, indent=2)

    @classmethod
    def desde_dict(cls, datos: dict) -> "Diseno":
        datos = dict(datos)
        datos["plano"] = ConfigPlano.desde_dict(datos.get("plano"))
        conocidas = {f.name for f in fields(cls)}
        sobran = set(datos) - conocidas
        if sobran:
            raise ValueError(f"claves desconocidas en el diseño: {', '.join(sorted(sobran))}")
        return cls(**datos)

    @classmethod
    def desde_json(cls, texto: str) -> "Diseno":
        return cls.desde_dict(json.loads(texto))


def disenar(tipo: str, f_MHz: float, diametro_mm: float, ajustar: bool = True, cable: str | None = None,
            vf_medido: float | None = None, **plano) -> Diseno:
    """Diseño con las cotas ajustadas por el motor si está (escritorio) o las de partida si no (estado «Sin validar»).

    En los tipos de coaxial (`manga`, `coco`) `cable` es el nombre de la tabla (por defecto RG-58) y `vf_medido`, si se
    da, sustituye al VF de catálogo; el diámetro del alambre no se usa (el hilo es la malla del cable).
    """
    config = ConfigPlano.desde_dict(plano)
    if tipo in TIPOS_COAXIAL:
        return _disenar_coaxial(tipo, f_MHz, ajustar, cable or CABLE_POR_DEFECTO, vf_medido, config)
    if ajustar:
        from . import ajuste, motor
        if motor.disponible():
            funcion = ajuste.ajustar_dipolo if tipo == "dipolo" else ajuste.ajustar_jpole
            r = funcion(f_MHz, diametro_mm)
            return Diseno(tipo, f_MHz, diametro_mm, r["geometria"], resultados=r["resultados"], estado="Simulado",
                          plano=config)
    if tipo == "dipolo":
        geometria = {"largo_total_mm": generadores.FACTOR_DIPOLO * 299792.458 / f_MHz}
    elif tipo == "jpole":
        geometria = generadores.jpole_por_defecto(f_MHz, diametro_mm)
    else:
        raise ValueError(f"tipo desconocido: {tipo}")
    return Diseno(tipo, f_MHz, diametro_mm, geometria, plano=config)


def _disenar_coaxial(tipo: str, f_MHz: float, ajustar: bool, nombre_cable: str, vf_medido: float | None,
                     config: ConfigPlano) -> Diseno:
    from .cables import cable as buscar
    from .coaxial import RADIADOR_MANGA
    c = buscar(nombre_cable)
    if vf_medido is not None:
        c = c.con_vf_medido(vf_medido)
    lam_mm = 299792.458 / f_MHz
    if tipo == "manga":
        geometria = {"radiador_mm": RADIADOR_MANGA * lam_mm, "manga_mm": lam_mm / 4, "bajada_mm": lam_mm / 2}
    else:
        geometria = {"tramos": 4, "factor_tramo": 1.0, "punta_lambda": 0.25, "tramo_mm": lam_mm / 2 * c.vf,
                     "punta_mm": lam_mm / 4}
    diseno = Diseno(tipo, f_MHz, c.diametro_exterior_mm, geometria, material=f"coaxial {c.nombre}", plano=config)
    diseno.con_cable(c)
    if ajustar:
        from . import ajuste, motor
        if motor.disponible():
            if tipo == "manga":
                r = ajuste.ajustar_manga(f_MHz, c)
            else:
                r = ajuste.ajustar_coco(f_MHz, c, tramos=int(geometria["tramos"]))
                r["geometria"].update(tramo_mm=lam_mm / 2 * c.vf * r["geometria"]["factor_tramo"],
                                      punta_mm=r["geometria"]["punta_lambda"] * lam_mm)
                r["resultados"]["red"] = r.pop("red")
            diseno.geometria = {**geometria, **r["geometria"]}
            diseno.resultados = r["resultados"]
            diseno.estado = "Simulado"
    return diseno
