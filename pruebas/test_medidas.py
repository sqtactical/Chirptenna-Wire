"""W3.4: leer .s1p, comparar con la simulación y el estado «Medido» solo con ≤ 2 %."""

import math

import pytest

from wire import medidas
from wire.diseno import disenar


def _s1p(f0, ancho=0.02, formato="RI", unidad="MHz", z0=50.0, pasos=101, f_ini=None, f_fin=None):
    """Un dipolo sintético: R = 70 Ω y X = 600·(f/f0 − f0/f)·... que cruza por cero en f0."""
    f_ini, f_fin = f_ini or 0.9 * f0, f_fin or 1.1 * f0
    esc = {"Hz": 1e6, "kHz": 1e3, "MHz": 1.0, "GHz": 1e-3}[unidad]
    lineas = [f"# {unidad} S {formato} R {z0:g}"]
    for i in range(pasos):
        f = f_ini + (f_fin - f_ini) * i / (pasos - 1)
        z = complex(70.0, 600.0 * (f / f0 - f0 / f))
        s = (z - z0) / (z + z0)
        if formato == "RI":
            a, b = s.real, s.imag
        elif formato == "MA":
            a, b = abs(s), math.degrees(math.atan2(s.imag, s.real))
        else:
            a, b = 20 * math.log10(abs(s)), math.degrees(math.atan2(s.imag, s.real))
        lineas.append(f"{f * esc:.6f} {a:.6f} {b:.6f}")
    return "\n".join(lineas) + "\n"


@pytest.mark.parametrize("formato", ["RI", "MA", "DB"])
@pytest.mark.parametrize("unidad", ["Hz", "kHz", "MHz", "GHz"])
def test_leer_formatos_y_unidades(formato, unidad):
    m = medidas.leer_s1p(_s1p(145.0, formato=formato, unidad=unidad))
    assert len(m.f_MHz) == 101 and m.f_MHz[0] == pytest.approx(130.5, rel=1e-4)
    assert medidas.resonancia(m, 120, 170) == pytest.approx(145.0, abs=0.1)
    assert min(m.roe) == pytest.approx(70 / 50, rel=0.03)


def test_minimo_de_roe_interpolado():
    m = medidas.leer_s1p(_s1p(145.0, pasos=31))
    assert medidas.minimo_roe(m, 120, 170)[0] == pytest.approx(145.0, abs=0.3)


def test_errores_de_formato():
    with pytest.raises(ValueError):
        medidas.leer_s1p("# MHz S RI R 50\n145 0.1\n")
    with pytest.raises(ValueError):
        medidas.leer_s1p("# MHz S RI R 50\n145 0.1 0.1\n146 0.1 0.1\n")


def _diseno_simulado():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    d.resultados = {"f_resonancia_MHz": 145.0}
    d.estado = "Simulado"
    return d


def test_medida_a_menos_del_2_por_ciento_pasa_a_medido():
    d = _diseno_simulado()
    c = medidas.guardar_medida(d, medidas.leer_s1p(_s1p(147.0)), "dipolo.s1p")   # +1,4 %
    assert c["coincide"] and d.estado == "Medido" and d.medida["archivo"] == "dipolo.s1p"
    assert c["error_pct"] == pytest.approx(1.38, abs=0.1) and len(d.medida["f_MHz"]) <= 101


def test_medida_a_mas_del_2_por_ciento_no_cambia_el_estado():
    d = _diseno_simulado()
    c = medidas.guardar_medida(d, medidas.leer_s1p(_s1p(151.0)))                  # +4,1 %
    assert not c["coincide"] and d.estado == "Simulado" and d.medida is not None


def test_sin_simulacion_no_se_puede_dar_por_medido():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    medidas.guardar_medida(d, medidas.leer_s1p(_s1p(145.0)))
    assert d.estado == "Sin validar"


def test_la_medida_viaja_en_el_json():
    from wire.diseno import Diseno
    d = _diseno_simulado()
    medidas.guardar_medida(d, medidas.leer_s1p(_s1p(145.0)))
    assert Diseno.desde_json(d.a_json()) == d
