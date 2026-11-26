"""Hoja de la vertical de HF con radiales elevados: vista, lista de corte, ROE simulada y montaje.

Los valores del montaje (aislador de base, choke, tensado de los radiales) son los **habituales de los montajes de
aficionados**, sin verificar aquí: se comprueban con el VNA.
"""

from __future__ import annotations

from ..diseno import Diseno
from ..i18n import tr
from .comun import fmt, frecuencia, hoja_a4, regla, seccion, tabla, texto_banda
from .hf import SUELO_NOMBRE, _m
from .hoja import COBRE, GRIS, PVC, TINTA, VERDE, Cota, Hoja, Linea, Rect, Texto


def hojas(diseno: Diseno, fecha: str) -> list[Hoja]:
    return [_hoja(diseno)]


def _hoja(diseno: Diseno) -> Hoja:
    g, r, d, sob = diseno.geometria, diseno.resultados, diseno.diametro_mm, diseno.sobrante_mm
    n = int(g["radiales"])
    hoja = hoja_a4(diseno, tr("Vertical de HF · {0} MHz ({1})", frecuencia(diseno.f_MHz), texto_banda(diseno.f_MHz)),
                   tr("Radiador de λ/4 con {0} radiales a {1} sobre suelo {2} · coaxial de 50 Ω", n, _m(g["altura_mm"], diseno),
                      tr(SUELO_NOMBRE[g["suelo"]])))
    seccion(hoja, 14, 33, tr("VISTA GENERAL"), tr("Vista lateral, sin escala"))
    xc, yb, yr, ya = 105.0, 82.0, 74.0, 42.0                      # eje, suelo, radiales y punta del radiador
    hoja.anadir(Linea(20, yb, 196, yb, GRIS, 0.6), Texto(196, yb + 4, tr("suelo"), 5.4, GRIS, ancla="derecha"),
                Linea(xc, yr, xc, ya, COBRE, 1.2), Rect(xc - 3, yr - 2, 6, 4, TINTA, 0.3, PVC),
                Linea(xc - 3, yr + 1, xc - 58, yr + 1, COBRE, 0.9), Linea(xc + 3, yr + 1, xc + 58, yr + 1, COBRE, 0.9),
                Cota(xc + 10, ya, xc + 10, yr, tr("radiador {0}", _m(g["radiador_mm"], diseno)), tam=5.4, ref1=(xc + 2, ya), ref2=(xc + 3, yr)),
                Cota(xc - 58, yr + 7, xc, yr + 7, tr("radial {0}", _m(g["radial_mm"], diseno)), tam=5.4, ref1=(xc - 58, yr + 1), ref2=(xc, yr + 1)),
                Cota(188, yr + 1, 188, yb, _m(g["altura_mm"], diseno), tam=5.0),
                Texto(xc + 6, yr + 12, tr("base aislada y coaxial"), 5.4, GRIS))
    seccion(hoja, 14, 91, tr("LISTA DE CORTE"), tr("Corta con el sobrante y ajusta después"), VERDE)
    filas = [[tr("Radiador vertical, Ø {0} mm", fmt(d, 1)), "1", _m(g["radiador_mm"], diseno), _m(g["radiador_mm"] + sob, diseno)],
             [tr("Radial, Ø {0} mm", fmt(d, 1)), str(n), _m(g["radial_mm"], diseno), _m(g["radial_mm"] + sob, diseno)],
             [tr("Aislador de base y 3 cuerdas de tensado"), "1", "—", "—"],
             [tr("Coaxial de 50 Ω, con choke de 8–10 vueltas"), "1", "—", "—"]]
    tabla(hoja, 14, 103, [0, 70, 82, 106], [tr("Pieza"), tr("Cant."), tr("Final"), tr("Cortar a")], filas, 132)
    y0 = 103 + 9 + 6.5 * len(filas)
    if r and r.get("bandas"):
        seccion(hoja, 14, y0 + 6, tr("SIMULADO (NEC2) · SIN MEDIR"), tr("Suelo {0}, a 50 Ω: la ROE es la del coaxial", tr(SUELO_NOMBRE[g["suelo"]])), VERDE)
        b = r["bandas"][0]
        filas = [[b["banda"], fmt(b["f_MHz"], 2), fmt(b["roe"], 2), fmt(b["roe_max"], 2),
                  f"{fmt(b['r_ohm'], 0)} {'+' if b['x_ohm'] >= 0 else '−'} j{fmt(abs(b['x_ohm']), 0)}", fmt(b["ganancia_dBi"], 1)]]
        y = tabla(hoja, 14, y0 + 18, [0, 24, 52, 80, 108, 148], [tr("Banda"), tr("f (MHz)"), tr("ROE centro"), tr("ROE máx."), tr("Z (Ω)"), tr("dBi")],
                  filas, 180)
        avisos = [tr("La ganancia es la máxima del diagrama: una vertical sobre suelo normal pierde en el suelo y puede salir por debajo de 0 dBi."),
                  tr("Con radiales elevados la resistencia es de 30 a 45 Ω; con pocos radiales o suelo pobre sube y las pérdidas también.")]
        hoja.anadir(Texto(14, y + 6, "\n".join(avisos), 6.0, VERDE))
        y += 20
    else:
        seccion(hoja, 14, y0 + 6, tr("SIN SIMULAR"), tr("Cotas de partida, sin ajustar"))
        hoja.anadir(Texto(14, y0 + 18, tr("Simula el diseño en el escritorio (PyNEC) o\nabre el .nec en 4nec2/xnec2c."), 6.3))
        y = y0 + 30
    seccion(hoja, 14, y + 4, tr("MONTAJE"), tr("Orientativo, sin verificar: se comprueba con el VNA"), VERDE)
    pasos = [tr("• La malla del coaxial va a la unión de los radiales y el vivo al radiador, con el aislador entre la base y el mástil."),
             tr("• Reparte los radiales en estrella, horizontales y tensos, a la altura de la lista; más radiales (16 o más) bajan las pérdidas."),
             tr("• Pon un choke de 8–10 vueltas de coaxial pegado a la base: si no, el cable baja radiando y la ROE depende de por dónde pase."),
             tr("• Ajusta con el VNA: acorta el radiador si resuena baja, alárgalo si resuena alta; un 1 % de largo es un 1 % de frecuencia.")]
    hoja.anadir(Texto(14, y + 16, "\n".join(pasos), 6.1))
    regla(hoja, 14, 244)
    return hoja
