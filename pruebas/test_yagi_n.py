"""Yagi de N elementos y corrección por el eje metálico."""

import json

import pytest

from wire import generadores, motor, planos, web_api
from wire.diseno import disenar

necesita_motor = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def test_la_yagi_tiene_un_hilo_mas_por_cada_director():
    for n in (3, 5, 8):
        m = generadores.yagi(145.0, 3.0, n_elementos=n)
        assert len(m.hilos) == 5 + (n - 2) and m.nombre == f"Yagi de {n} elementos"


def test_los_directores_de_partida_bajan_y_las_separaciones_se_abren():
    p = generadores.yagi_por_defecto(145.0, 6)
    d, s = p["directores_mm"], p["seps_directores_mm"]
    assert len(d) == len(s) == 4 and d == sorted(d, reverse=True) and s == sorted(s)
    assert p["director_mm"] == d[0] and p["sep_director_mm"] == s[0]      # compatibilidad con los diseños de 3 elementos


def test_un_diseno_antiguo_de_3_elementos_sigue_generando_igual():
    nuevo = disenar("yagi", 145.0, 3.0, ajustar=False)
    g = {k: v for k, v in nuevo.geometria.items() if k in ("reflector_mm", "excitado_mm", "director_mm", "sep_reflector_mm",
                                                           "sep_director_mm", "sep_plegado_mm")}
    antiguo = type(nuevo)("yagi", 145.0, 3.0, g)
    assert antiguo.modelo().hilos == nuevo.modelo().hilos


def test_la_correccion_del_eje_sigue_dl6wu():
    # 20 mm a 145 MHz: B = 0,00967; mitad de elemento 12,5975·B − 114,5·B² = 0,111 del diámetro → 2,22 mm; entero ×2
    assert generadores.correccion_eje_mm(145.0, "ninguno", 20.0) == 0.0
    unido = generadores.correccion_eje_mm(145.0, "unido", 20.0)
    assert abs(unido - 4.45) < 0.05
    assert abs(generadores.correccion_eje_mm(145.0, "aislado", 20.0) - unido / 2) < 1e-9
    with pytest.raises(ValueError):
        generadores.correccion_eje_mm(145.0, "metalico", 20.0)


def test_el_plano_suma_la_correccion_y_hay_hoja_de_elementos():
    sin = planos.generar(disenar("yagi", 145.0, 3.0, ajustar=False, elementos=5, eje="ninguno", eje_mm=20.0))
    con = planos.generar(disenar("yagi", 145.0, 3.0, ajustar=False, elementos=5, eje="unido", eje_mm=20.0))
    assert len(sin.hojas) == len(con.hojas) == 2
    texto = lambda p: " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)  # noqa: E731
    assert "DL6WU" not in texto(sin) and "DL6WU" in texto(con)
    assert "1038 mm" in texto(sin) and "1043 mm" in texto(con)      # reflector 1023,4 + sobrante 15 y 4,45 mm más con el eje
    assert len(planos.generar(disenar("yagi", 145.0, 3.0, ajustar=False)).hojas) == 1       # 3 elementos y eje de plástico: como antes


def test_los_parametros_se_validan():
    with pytest.raises(ValueError):
        disenar("yagi", 145.0, 3.0, ajustar=False, elementos=2)
    with pytest.raises(ValueError):
        disenar("yagi", 145.0, 3.0, ajustar=False, eje="oro")
    with pytest.raises(ValueError, match="solo valen para la Yagi"):
        disenar("dipolo", 145.0, 3.0, ajustar=False, elementos=5)


def test_la_api_web_acepta_elementos_y_eje():
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "yagi", "f_MHz": 433, "diametro_mm": 2, "elementos": 6, "eje": "aislado", "eje_mm": 12})))
    assert r["diseno"]["geometria"]["n_elementos"] == 6 and r["diseno"]["geometria"]["boom"] == "aislado" and len(r["hojas"]) == 2


@necesita_motor
def test_mas_elementos_dan_mas_ganancia_hacia_delante():
    f = 145.0
    g = {}
    for n in (3, 5, 7):
        m = generadores.yagi(f, 3.0, n_elementos=n)
        g[n] = motor.ganancias_en(m, f, [(90.0, 90.0)])[0]
    assert g[5] > g[3] + 1.0 and g[7] > g[5] + 0.5


@necesita_motor
def test_el_ajuste_de_5_elementos_adapta_y_apunta_hacia_delante():
    d = disenar("yagi", 145.0, 3.0, elementos=5, eje="unido", eje_mm=20.0)
    r = d.resultados
    assert r["roe"] < 1.5 and r["ganancia_frente_dBi"] > 9.5 and r["relacion_delante_detras_dB"] > 8
    dires = d.geometria["directores_mm"]
    assert len(dires) == 3 and dires == sorted(dires, reverse=True)
