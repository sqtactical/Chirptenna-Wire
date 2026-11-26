"""El diseño que se guarda en `diseno.json`: tipo, frecuencia, material, cotas, resultados y configuración del plano.

Python puro (corre en Pyodide). Las cotas van en mm al eje del alambre; los resultados, si los hay, los ha puesto
el motor en escritorio (`wire/ajuste.py`) y el plano solo los lee.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields

from . import generadores
from .i18n import N_, tr
from .modelo import Modelo

TIPOS = {
    "dipolo": N_("Dipolo de media onda"),
    "jpole": N_("J-pole"),
    "manga": N_("Dipolo de manga de coaxial"),
    "coco": N_("Colineal CoCo de coaxial"),
    "jpole_koch": N_("J-pole de Koch"),
    "discone": N_("Discone"),
    "gp": N_("Ground plane"),
    "colineal": N_("Colineal con bobinas de fase"),
    "colineal_bibanda": N_("Colineal bibanda (2 m y 70 cm)"),
    "vinv": N_("Dipolo en V invertida"),
    "yagi": N_("Yagi de N elementos"),
    "biconica": N_("Bicónica"),
    "torniquete": N_("Torniquete en X (dipolos cruzados)"),
    "batwing": N_("Batwing (dipolo de alas)"),
    "efhw": N_("EFHW de HF con transformador"),
    "dipolo_hf": N_("Dipolo de HF"),
    "vinv_hf": N_("V invertida de HF"),
    "abanico": N_("Dipolo en abanico multibanda"),
    "trampas": N_("Dipolo de dos bandas con trampas"),
    "g5rv": N_("G5RV con escalerilla"),
}

# Categorías de la galería: (clave, nombre, tipos). Cada tipo va en una sola.
CATEGORIAS = (
    ("hf", N_("HF · hilos sobre suelo real"), ("dipolo_hf", "vinv_hf", "abanico", "trampas", "g5rv", "efhw")),
    ("vhf", N_("VHF y UHF · alambre y varilla"), ("dipolo", "jpole", "jpole_koch", "gp", "colineal", "colineal_bibanda", "vinv", "yagi", "torniquete", "batwing")),
    ("coaxial", N_("Antenas de coaxial"), ("manga", "coco")),
    ("banda_ancha", N_("Banda ancha"), ("discone", "biconica")),
)

CONECTORES = ("SO-239", "N")

TIPOS_COAXIAL = ("manga", "coco")

# Lo que se dice de cada tipo en la galería: resumen y estado honesto (para el tipo, no para un diseño concreto).
RESUMEN = {
    "dipolo": N_("Dos brazos y coaxial: el más simple y la referencia para medir."),
    "jpole": N_("Una sola pieza de alambre doblada en U, alimentada con coaxial."),
    "manga": N_("Coaxial con la malla doblada hacia atrás como manga; sin soldar hilos."),
    "coco": N_("Varios tramos de coaxial con vivo y malla cruzados; más ganancia."),
    "jpole_koch": N_("La J-pole con el radiador en curva de Koch: más baja, con plantilla 1:1 en mosaico."),
    "discone": N_("Disco y cono de varillas: banda muy ancha (más de 4:1) para escáner."),
    "gp": N_("Radiador de λ/4 y cuatro radiales a 45° sobre un conector SO-239 o N."),
    "colineal": N_("Varias medias ondas apiladas con una bobina de fase entre cada dos (la de «2 / 5 dBi»): más ganancia hacia el horizonte."),
    "colineal_bibanda": N_("Una sola antena para 145 y 433 MHz: en 145 es un ¼ o 5/8 de onda y en 433 las bobinas con condensador apilan 2 o 4 medias ondas."),
    "vinv": N_("Dipolo con el vértice en un mástil y los brazos caídos: se tensa con cuerda."),
    "yagi": N_("Reflector, dipolo plegado y de 1 a 13 directores sobre un eje de plástico o metal: ganancia y dirección."),
    "biconica": N_("Dos conos de varillas vértice con vértice: banda ancha (más de 4:1)."),
    "torniquete": N_("Dos dipolos en cruz con una línea de λ/4: polarización circular (satélites, 137 MHz)."),
    "batwing": N_("Dipolo con dos alas de abanico: algo más de banda que el dipolo, sin panel ni reflector."),
    "efhw": N_("Hilo de media onda alimentado por el extremo con transformador 49:1, 64:1 o 9:1: varias bandas de HF."),
    "dipolo_hf": N_("Dipolo de media onda a media altura sobre el suelo, con balun 1:1: una banda, el más simple."),
    "vinv_hf": N_("Dipolo con el vértice en un mástil alto y los brazos caídos: una banda, un solo soporte."),
    "abanico": N_("Un par de hilos por banda desde un mismo centro: varias bandas con un solo coaxial y sin acoplador."),
    "trampas": N_("Dipolo de dos bandas con una trampa LC a cada lado: más corto que dos dipolos."),
    "g5rv": N_("Dipolo largo con escalerilla de 450 Ω y coaxial: multibanda con acoplador."),
}
ESTADO_TIPO = {
    "dipolo": N_("Simulado (validado contra la teoría), sin medir"),
    "jpole": N_("Simulado, sin medir"),
    "manga": N_("Simulado (modelo de banda estrecha), sin medir"),
    "coco": N_("Simulado, sin validar frente a un caso publicado ni medido"),
    "jpole_koch": N_("Simulado, sin medir (la J-pole recta tampoco está medida)"),
    "discone": N_("Simulado, sin medir ni validar frente a un caso publicado"),
    "gp": N_("Simulado (en espacio libre), sin medir"),
    "colineal": N_("Simulado (en espacio libre, bobinas ideales), sin medir; la bobina real hay que ajustarla"),
    "colineal_bibanda": N_("Simulado (en espacio libre, componentes ideales), sin medir; los enlaces L-C reales hay que ajustarlos"),
    "vinv": N_("Simulado (en espacio libre), sin medir"),
    "yagi": N_("Simulado, sin medir ni validar frente a un caso publicado"),
    "biconica": N_("Simulado, sin medir ni validar frente a un caso publicado"),
    "torniquete": N_("Simulado (en espacio libre, con razón axial calculada), sin medir"),
    "batwing": N_("Simulado, sin medir ni validar frente a un caso publicado"),
    "efhw": N_("Simulado sobre suelo real con transformador ideal, sin medir; el transformador real hay que ajustarlo"),
    "dipolo_hf": N_("Simulado sobre suelo real, sin medir"),
    "vinv_hf": N_("Simulado sobre suelo real, sin medir"),
    "abanico": N_("Simulado sobre suelo real, sin medir; los hilos se acoplan: hay que ajustar en la antena"),
    "trampas": N_("Simulado sobre suelo real con trampas ideales (Q = 100), sin medir; la trampa real hay que ajustarla"),
    "g5rv": N_("Simulado sobre suelo real, sin medir; la línea es ideal y sin pérdidas"),
}
CABLE_POR_DEFECTO = "RG-58"

ESTADOS = ("Simulado", "Medido", "Sin validar")

# Sobrante de corte por defecto (mm), según el tipo (`plano.sobrante_mm` lo cambia).
SOBRANTE = {"dipolo": 15.0, "jpole": 20.0, "manga": 15.0, "coco": 15.0, "jpole_koch": 20.0, "discone": 15.0,
             "gp": 15.0, "colineal": 15.0, "colineal_bibanda": 15.0, "vinv": 15.0, "yagi": 15.0, "biconica": 15.0,
             "torniquete": 15.0, "batwing": 15.0, "efhw": 150.0,
             "dipolo_hf": 150.0, "vinv_hf": 150.0, "abanico": 150.0, "trampas": 150.0, "g5rv": 150.0}

BANDAS = [  # (nombre, f_min, f_max) en MHz: las bandas iniciales de la propuesta
    (N_("banda aérea"), 118.0, 137.0),
    (N_("2 m"), 144.0, 146.0),
    (N_("banda marina VHF"), 156.0, 162.1),
    (N_("70 cm"), 430.0, 440.0),
    (N_("PMR446"), 446.0, 446.2),
    (N_("LoRa 868"), 863.0, 870.0),
    (N_("LoRa 915"), 902.0, 928.0),
    (N_("ADS-B"), 1089.0, 1091.0),
    *[(N_(n), a, b) for n, a, b in generadores.BANDAS_HF],     # HF: 160 m a 10 m
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
    material: str = N_("varilla de latón o aluminio")
    resultados: dict | None = None
    estado: str = "Sin validar"
    plano: ConfigPlano = field(default_factory=ConfigPlano)
    version: int = 1
    # Antenas de coaxial: {"nombre", "z0", "vf", "vf_origen": "catálogo"|"medido"}; None en las de alambre.
    cable: dict | None = None
    # Medida del NanoVNA guardada con el diseño (`wire.medidas.guardar_medida`); None si no hay.
    medida: dict | None = None

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
        return tr(TIPOS[self.tipo])

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
        if self.tipo == "jpole_koch":
            return generadores.jpole_koch(self.f_MHz, self.diametro_mm, altura_koch_mm=g["altura_koch_mm"],
                                          corto_mm=g["corto_mm"], toma_mm=g["toma_mm"], separacion_mm=g["separacion_mm"],
                                          iteracion=int(g["iteracion"]))
        if self.tipo == "gp":
            return generadores.gp(self.f_MHz, self.diametro_mm, radiador_mm=g["radiador_mm"], radial_mm=g["radial_mm"],
                                  angulo=g["angulo"], radiales=int(g["radiales"]))
        if self.tipo == "colineal":
            return generadores.colineal(self.f_MHz, self.diametro_mm, secciones_mm=list(g["secciones_mm"]), bobina_uH=g["bobina_uH"],
                                        radial_mm=g["radial_mm"], angulo=g["angulo"], radiales=int(g["radiales"]))
        if self.tipo == "colineal_bibanda":
            return generadores.colineal_bibanda(self.f_MHz, g["f_alta_MHz"], self.diametro_mm, secciones_mm=list(g["secciones_mm"]),
                                                bobina_uH=g["bobina_uH"], condensador_pF=g["condensador_pF"], radial_mm=g["radial_mm"],
                                                angulo=g["angulo"], radiales=int(g["radiales"]))
        if self.tipo == "vinv":
            return generadores.vinv(self.f_MHz, self.diametro_mm, brazo_mm=g["brazo_mm"], apertura=g["apertura"])
        if self.tipo == "yagi":
            return generadores.yagi(self.f_MHz, self.diametro_mm, reflector_mm=g["reflector_mm"], excitado_mm=g["excitado_mm"],
                                    sep_reflector_mm=g["sep_reflector_mm"], sep_plegado_mm=g["sep_plegado_mm"],
                                    directores_mm=g.get("directores_mm") or [g["director_mm"]],
                                    seps_directores_mm=g.get("seps_directores_mm") or [g["sep_director_mm"]])
        if self.tipo == "biconica":
            return generadores.biconica(self.f_MHz, self.diametro_mm, cono_mm=g["cono_mm"], hueco_mm=g["hueco_mm"],
                                        semiangulo=g["semiangulo"], varillas=int(g["varillas"]))
        if self.tipo == "dipolo_hf":
            return generadores.dipolo_hf(self.f_MHz, self.diametro_mm, largo_mm=g["largo_mm"], altura_mm=g["altura_mm"], suelo=g["suelo"])
        if self.tipo == "vinv_hf":
            return generadores.vinv_hf(self.f_MHz, self.diametro_mm, brazo_mm=g["brazo_mm"], apertura=g["apertura"],
                                       altura_mm=g["altura_mm"], suelo=g["suelo"])
        if self.tipo == "abanico":
            return generadores.abanico(self.f_MHz, self.diametro_mm, list(g["largos_mm"]), altura_mm=g["altura_mm"], suelo=g["suelo"],
                                       sep_mm=g["sep_mm"])
        if self.tipo == "trampas":
            return generadores.trampas(g["f_baja_MHz"], self.diametro_mm, g["f_alta_MHz"], g["interior_mm"], g["exterior_mm"],
                                       g["trampa_L_uH"], g["trampa_C_pF"], trampa_largo_mm=g["trampa_largo_mm"], altura_mm=g["altura_mm"],
                                       suelo=g["suelo"])
        if self.tipo == "g5rv":
            return generadores.g5rv(self.f_MHz, self.diametro_mm, largo_mm=g["largo_mm"], escalerilla_mm=g["escalerilla_mm"],
                                    escalerilla_z0=g["escalerilla_z0"], escalerilla_vf=g["escalerilla_vf"], altura_mm=g["altura_mm"],
                                    suelo=g["suelo"])
        if self.tipo == "efhw":
            return generadores.efhw(self.f_MHz, self.diametro_mm, largo_mm=g["largo_mm"], contrapeso_mm=g["contrapeso_mm"],
                                    altura_mm=g["altura_mm"], suelo=g["suelo"], relacion=int(g["relacion"]))
        if self.tipo == "torniquete":
            return generadores.torniquete(self.f_MHz, self.diametro_mm, brazo_mm=g["brazo_mm"], sep_mm=g["sep_mm"],
                                          z0_linea=g["z0_linea"], vf_linea=g["vf_linea"], linea_mm=g["linea_mm"])
        if self.tipo == "batwing":
            return generadores.batwing(self.f_MHz, self.diametro_mm, ala_mm=g["ala_mm"], ancho_mm=g["ancho_mm"],
                                       hueco_mm=g["hueco_mm"], radios=int(g["radios"]))
        if self.tipo == "discone":
            return generadores.discone(self.f_MHz, self.diametro_mm, cono_mm=g["cono_mm"], disco_mm=g["disco_mm"],
                                       hueco_mm=g["hueco_mm"], semiangulo=g["semiangulo"], varillas=int(g["varillas"]))
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
            vf_medido: float | None = None, conector: str | None = None, elementos: int | None = None,
            eje: str | None = None, eje_mm: float | None = None, relacion: int | None = None, altura_m: float | None = None,
            suelo: str | None = None, potencia_w: float | None = None, largo_max_m: float | None = None,
            bandas: list[str] | None = None, f_alta_MHz: float | None = None, **plano) -> Diseno:
    """Diseño con las cotas ajustadas por el motor si está (escritorio) o las de partida si no (estado «Sin validar»).

    En los tipos de coaxial (`manga`, `coco`) `cable` es el nombre de la tabla (por defecto RG-58) y `vf_medido`, si se
    da, sustituye al VF de catálogo; el diámetro del alambre no se usa (el hilo es la malla del cable).
    """
    config = ConfigPlano.desde_dict(plano)
    if tipo == "yagi":
        elementos = 3 if elementos is None else int(elementos)
        if not 3 <= elementos <= 15:
            raise ValueError("la Yagi lleva entre 3 y 15 elementos")
        if eje is not None and eje not in generadores.BOOMS:
            raise ValueError(f"eje desconocido: {eje} (hay: {', '.join(generadores.BOOMS)})")
        if eje in ("aislado", "unido"):
            lam_mm = generadores.longitud_onda_m(f_MHz) * 1000
            d_eje = eje_mm if eje_mm is not None else generadores.yagi_por_defecto(f_MHz, elementos)["boom_mm"]
            if not d_eje > 0:
                raise ValueError("el diámetro del eje metálico debe ser positivo")
            if d_eje / lam_mm > generadores.B_MAXIMO_EJE:
                raise ValueError(f"el eje metálico de {d_eje:g} mm es demasiado grueso a {f_MHz:g} MHz: la corrección solo vale "
                                 f"hasta {generadores.B_MAXIMO_EJE * lam_mm:.0f} mm (0,055 λ)")
    elif tipo == "colineal_bibanda":
        elementos = 4 if elementos is None else int(elementos)
        f_alta_MHz = 433.0 if f_alta_MHz is None else float(f_alta_MHz)
        if elementos not in generadores.COLB_SECCIONES:
            raise ValueError("la colineal bibanda lleva 2 o 4 secciones (con 3 mide ≈ λ/2 en la banda baja y no adapta)")
        if not generadores.COLB_RAZON[0] <= f_alta_MHz / f_MHz <= generadores.COLB_RAZON[1]:
            raise ValueError("la banda alta debe ser de 2,5 a 3,5 veces la baja (145 y 433 MHz, por ejemplo)")
        if eje is not None or eje_mm is not None:
            raise ValueError("el eje solo vale para la Yagi")
    elif tipo == "colineal":
        elementos = 3 if elementos is None else int(elementos)
        if elementos not in generadores.COL_SECCIONES:
            raise ValueError("la colineal lleva de 2 a 4 secciones")
        if eje is not None or eje_mm is not None:
            raise ValueError("el eje solo vale para la Yagi")
    elif elementos is not None or eje is not None or eje_mm is not None:
        raise ValueError("el número de elementos y el eje solo valen para la Yagi")
    if f_alta_MHz is not None and tipo != "colineal_bibanda":
        raise ValueError("la frecuencia alta solo vale para la colineal bibanda")
    if tipo in generadores.TIPOS_HF:
        altura_m = (12.0 if tipo == "vinv_hf" else 10.0) if altura_m is None else float(altura_m)
        suelo = suelo or "normal"
        if suelo not in generadores.SUELOS:
            raise ValueError(f"suelo desconocido: {suelo} (hay: {', '.join(generadores.SUELOS)})")
        if not 1.5 <= altura_m <= 60:
            raise ValueError("la altura debe estar entre 1,5 y 60 m")
        if tipo != "efhw" and any(v is not None for v in (relacion, potencia_w, largo_max_m)):
            raise ValueError("la relación, la potencia y el largo máximo solo valen para la EFHW")
        if tipo not in ("abanico", "trampas") and bandas is not None:
            raise ValueError("las bandas solo valen para el dipolo en abanico y el de trampas")
    elif any(v is not None for v in (relacion, altura_m, suelo, potencia_w, largo_max_m, bandas)):
        raise ValueError("la relación, la altura, el suelo, la potencia y las bandas solo valen para los tipos de HF")
    if tipo == "efhw":
        relacion = 49 if relacion is None else int(relacion)
        potencia_w = 100.0 if potencia_w is None else float(potencia_w)
        if relacion not in generadores.RELACIONES:
            raise ValueError(f"relación desconocida: {relacion}:1 (hay: {', '.join(str(r) for r in generadores.RELACIONES)})")
        if potencia_w <= 0:
            raise ValueError("la potencia debe ser positiva")
    if tipo in ("abanico", "trampas"):
        bandas = list(bandas) if bandas else [b[0] for b in generadores.bandas_de(f_MHz, 49)][: (2 if tipo == "trampas" else 4)]
        for b in bandas:
            generadores.banda_por_nombre(b)
        if tipo == "trampas" and len(bandas) != 2:
            raise ValueError("el dipolo con trampas es de dos bandas")
        if len(bandas) < 2 and tipo == "abanico":
            raise ValueError("el dipolo en abanico necesita al menos dos bandas")
        f_MHz = min((generadores.banda_por_nombre(b)[1] + generadores.banda_por_nombre(b)[2]) / 2 for b in bandas)
    if tipo in TIPOS_COAXIAL:
        return _disenar_coaxial(tipo, f_MHz, ajustar, cable or CABLE_POR_DEFECTO, vf_medido, config)
    if ajustar:
        from . import ajuste, motor
        if motor.disponible():
            funcion = {"dipolo": ajuste.ajustar_dipolo, "jpole": ajuste.ajustar_jpole,
                       "jpole_koch": ajuste.ajustar_jpole_koch, "discone": ajuste.ajustar_discone, "gp": ajuste.ajustar_gp, "colineal": ajuste.ajustar_colineal, "colineal_bibanda": ajuste.ajustar_colineal_bibanda,
                       "vinv": ajuste.ajustar_vinv, "yagi": ajuste.ajustar_yagi, "biconica": ajuste.ajustar_biconica,
                       "torniquete": ajuste.ajustar_torniquete, "batwing": ajuste.ajustar_batwing,
                       "efhw": ajuste.ajustar_efhw, "dipolo_hf": ajuste.ajustar_dipolo_hf, "vinv_hf": ajuste.ajustar_vinv_hf,
                       "abanico": ajuste.ajustar_abanico, "trampas": ajuste.ajustar_trampas, "g5rv": ajuste.ajustar_g5rv}[tipo]
            if tipo == "yagi":
                r = funcion(f_MHz, diametro_mm, n_elementos=elementos, boom=eje or "ninguno", boom_mm=eje_mm)
            elif tipo == "colineal":
                r = funcion(f_MHz, diametro_mm, secciones=elementos)
            elif tipo == "colineal_bibanda":
                r = funcion(f_MHz, f_alta_MHz, diametro_mm, secciones=elementos)
            elif tipo == "efhw":
                r = funcion(f_MHz, diametro_mm, relacion=relacion, altura_m=altura_m, suelo=suelo, largo_max_m=largo_max_m)
                r["geometria"]["potencia_w"] = potencia_w
            elif tipo in ("abanico", "trampas"):
                r = funcion(f_MHz, diametro_mm, bandas=bandas, altura_m=altura_m, suelo=suelo)
            elif tipo in generadores.TIPOS_HF:
                r = funcion(f_MHz, diametro_mm, altura_m=altura_m, suelo=suelo)
            else:
                r = funcion(f_MHz, diametro_mm)
            if tipo == "gp":
                r["geometria"]["conector"] = _conector(conector)
            return Diseno(tipo, f_MHz, diametro_mm, r["geometria"], resultados=r["resultados"], estado="Simulado",
                          plano=config)
    if tipo == "dipolo":
        geometria = {"largo_total_mm": generadores.FACTOR_DIPOLO * 299792.458 / f_MHz}
    elif tipo == "jpole":
        geometria = generadores.jpole_por_defecto(f_MHz, diametro_mm)
    elif tipo == "jpole_koch":
        geometria = generadores.jpole_koch_por_defecto(f_MHz, diametro_mm)
    elif tipo == "discone":
        geometria = generadores.discone_por_defecto(f_MHz)
    elif tipo == "gp":
        geometria = {**generadores.gp_por_defecto(f_MHz), "conector": _conector(conector)}
    elif tipo == "colineal":
        geometria = generadores.colineal_por_defecto(f_MHz, elementos)
    elif tipo == "colineal_bibanda":
        geometria = generadores.colineal_bibanda_por_defecto(f_MHz, f_alta_MHz, elementos)
    elif tipo == "vinv":
        geometria = generadores.vinv_por_defecto(f_MHz)
    elif tipo == "yagi":
        geometria = generadores.yagi_por_defecto(f_MHz, elementos, eje_mm)
        geometria["boom"] = eje or "ninguno"
    elif tipo == "biconica":
        geometria = generadores.biconica_por_defecto(f_MHz)
    elif tipo == "torniquete":
        geometria = generadores.torniquete_por_defecto(f_MHz)
    elif tipo == "efhw":
        geometria = {**generadores.efhw_por_defecto(f_MHz, relacion, altura_m, suelo), "potencia_w": potencia_w}
    elif tipo == "dipolo_hf":
        geometria = generadores.dipolo_hf_por_defecto(f_MHz, altura_m, suelo)
    elif tipo == "vinv_hf":
        geometria = generadores.vinv_hf_por_defecto(f_MHz, altura_m, suelo)
    elif tipo == "abanico":
        geometria = generadores.abanico_por_defecto(bandas, altura_m, suelo)
    elif tipo == "trampas":
        baja, alta = sorted((generadores.banda_por_nombre(b) for b in bandas), key=lambda b: b[1])
        f_baja, f_alta = (baja[1] + baja[2]) / 2, (alta[1] + alta[2]) / 2
        geometria = {**generadores.trampas_por_defecto(f_baja, f_alta, altura_m, suelo), "bandas": [baja[0], alta[0]], "f_baja_MHz": f_baja}
    elif tipo == "g5rv":
        geometria = generadores.g5rv_por_defecto(f_MHz, altura_m, suelo)
    elif tipo == "batwing":
        geometria = {**generadores.batwing_por_defecto(f_MHz), "radios": float(generadores.BAT_RADIOS)}
    else:
        raise ValueError(f"tipo desconocido: {tipo}")
    return Diseno(tipo, f_MHz, diametro_mm, geometria, plano=config)


def _conector(nombre: str | None) -> str:
    if nombre is not None and nombre not in CONECTORES:
        raise ValueError(f"conector desconocido: {nombre} (hay: {', '.join(CONECTORES)})")
    return nombre or CONECTORES[0]


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
