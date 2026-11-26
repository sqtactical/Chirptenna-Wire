"""Aisladores para imprimir en 3D (STL): el central de un dipolo y el de extremo (hueso), con agujeros para el alambre y la cuerda.

Python puro (corre en Pyodide). Como en `impresion3d`, todo son cajas que se solapan y el laminador las funde; los agujeros son
cuadrados (del lado del alambre más la holgura), que es lo que se puede hacer sin operaciones booleanas. **Sin probar en una
impresora**: el material (PETG o ASA al exterior; el PLA se deforma con el sol), el espesor y las holguras son orientativos.
"""

from __future__ import annotations

import io
import zipfile

from .diseno import Diseno
from .i18n import tr
from .impresion3d import _placa, a_stl

TIPOS_CENTRO = ("dipolo", "vinv", "dipolo_hf", "vinv_hf", "abanico", "trampas", "g5rv")
TIPOS_AISLADORES = TIPOS_CENTRO + ("efhw",)
ESPESOR = 6.0              # mm
MARGEN = 8.0               # mm de material alrededor de cada agujero
PASO_HILOS = 11.0          # mm entre los agujeros de dos hilos del mismo lado (abanico)
CUERDA = 6.0               # mm de lado del agujero de la cuerda de sujeción


def _hueco(cx: float, cy: float, lado: float) -> tuple[float, float, float, float]:
    return (cx - lado / 2, cy - lado / 2, cx + lado / 2, cy + lado / 2)


def centro(diametro_mm: float, hilos_por_lado: int = 1, holgura: float = 0.6) -> bytes:
    """Aislador central: placa con, a cada lado, un agujero por hilo (pasa y se enrolla sobre sí mismo), la cuerda arriba y dos
    ranuras abajo para atar el coaxial con bridas."""
    a = diametro_mm + holgura
    ancho = 2 * (30.0 + MARGEN) + 2 * a
    alto = 2 * MARGEN + 2 * CUERDA + hilos_por_lado * PASO_HILOS
    y_hilos = [alto / 2 + (k - (hilos_por_lado - 1) / 2) * PASO_HILOS for k in range(hilos_por_lado)]
    huecos = [_hueco(lado * 30.0 + ancho / 2, y, a) for lado in (-1, 1) for y in y_hilos]
    huecos.append(_hueco(ancho / 2, alto - MARGEN, CUERDA))                       # cuerda
    huecos += [_hueco(ancho / 2 + d, MARGEN, 4.0) for d in (-8.0, 8.0)]            # bridas del coaxial
    return a_stl(_placa(0.0, 0.0, ancho, alto, huecos, ESPESOR), "Chirptenna Wire aislador central")


def extremo(diametro_mm: float, holgura: float = 0.6) -> bytes:
    """Aislador de extremo (hueso): a un lado dos agujeros para el alambre (se enhebra y se vuelve) y al otro uno para la cuerda."""
    a = diametro_mm + holgura
    ancho, alto = 70.0, 2 * MARGEN + 2 * a + 4.0
    huecos = [_hueco(MARGEN + a / 2, alto / 2 - (a / 2 + 2.0), a), _hueco(MARGEN + a / 2, alto / 2 + (a / 2 + 2.0), a),
              _hueco(ancho - MARGEN - CUERDA / 2, alto / 2, CUERDA)]
    return a_stl(_placa(0.0, 0.0, ancho, alto, huecos, ESPESOR), "Chirptenna Wire aislador de extremo")


def generar(diseno: Diseno, holgura: float = 0.6) -> dict[str, bytes]:
    """Piezas del diseño: nombre de archivo → STL. Falla con ValueError si el tipo no lleva aisladores."""
    if diseno.tipo not in TIPOS_AISLADORES:
        raise ValueError(f"el tipo {diseno.tipo} no lleva aisladores de hilo: valen {', '.join(TIPOS_AISLADORES)}")
    d = diseno.diametro_mm
    piezas = {"aislador_extremo.stl": extremo(d, holgura)}
    if diseno.tipo in TIPOS_CENTRO:
        n = len(diseno.geometria.get("bandas", [])) if diseno.tipo == "abanico" else 1
        piezas = {"aislador_centro.stl": centro(d, max(1, min(n, 4)), holgura), **piezas}
    return piezas


def cantidades(diseno: Diseno) -> dict[str, int]:
    """Cuántos de cada uno: el dipolo lleva uno central y dos de extremo; la EFHW, dos de extremo (uno en el transformador)."""
    return {"aislador_extremo.stl": 2, **({"aislador_centro.stl": 1} if diseno.tipo in TIPOS_CENTRO else {})}


def a_zip(diseno: Diseno, holgura: float = 0.6) -> bytes:
    piezas, cant = generar(diseno, holgura), cantidades(diseno)
    leeme = [tr("Aisladores para {0} (Ø de alambre {1} mm)", diseno.nombre_tipo, f"{diseno.diametro_mm:g}"), "",
             *[tr("{0}: imprime {1}", n, cant[n]) for n in piezas], "",
             tr("Material: PETG o ASA al exterior (el PLA se deforma con el sol). Relleno de al menos el 50 % y 4 paredes."),
             tr("Los agujeros del alambre son cuadrados del lado del alambre + {0} mm: si queda justo o suelto, cambia la holgura.", f"{holgura:g}"),
             tr("Sin probar en una impresora: comprueba una pieza antes de imprimir las demás.")]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for nombre, datos in piezas.items():
            z.writestr(nombre, datos)
        z.writestr("LEEME.txt", "\n".join(leeme) + "\n")
    return out.getvalue()
