"""Dipolos de HF sobre suelo real: dipolo, V invertida, abanico, trampas y G5RV."""

import pytest

from wire import generadores as G, motor, planos
from wire.diseno import disenar
from wire.modelo import Barrido

necesita_motor = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def test_los_modelos_llevan_suelo_real_y_la_geometria_esperada():
    d = G.dipolo_hf(7.1, 2.0)
    assert d.suelo == (13.0, 0.005) and len(d.hilos) == 1 and d.hilos[0].inicio[2] == 10.0
    v = G.vinv_hf(7.1, 2.0)
    assert len(v.hilos) == 2 and v.hilos[0].fin[2] < v.hilos[0].inicio[2]
    a = G.abanico(7.1, 2.0, [20000.0, 11000.0, 7000.0])
    assert len(a.hilos) == 1 + 2 * 3
    t = G.trampas(7.1, 2.0, 14.2, 5000.0, 4000.0, 3.7, 34.0)
    assert len(t.hilos) == 7 and len(t.cargas) == 2 and t.cargas[0].paralela
    g = G.g5rv(3.65, 2.0)
    assert len(g.lineas) == 1 and g.lineas[0].z0 == 450.0 and abs(g.lineas[0].longitud - 10.36) < 0.01


def test_los_errores_de_geometria_son_claros():
    with pytest.raises(ValueError, match="1 m del suelo"):
        G.vinv_hf(7.1, 2.0, altura_mm=3000.0)
    with pytest.raises(ValueError, match="suelo desconocido"):
        G.dipolo_hf(7.1, 2.0, suelo="roca")
    with pytest.raises(ValueError, match="banda desconocida"):
        G.banda_por_nombre("33 m")


def test_los_parametros_de_hf_se_validan_en_el_diseno():
    with pytest.raises(ValueError, match="solo valen para el dipolo en abanico"):
        disenar("dipolo_hf", 7.1, 2.0, ajustar=False, bandas=["40 m", "20 m"])
    with pytest.raises(ValueError, match="solo valen para la EFHW"):
        disenar("abanico", 7.1, 2.0, ajustar=False, relacion=49)
    with pytest.raises(ValueError, match="dos bandas"):
        disenar("trampas", 7.1, 2.0, ajustar=False, bandas=["40 m", "20 m", "15 m"])
    with pytest.raises(ValueError, match="al menos dos bandas"):
        disenar("abanico", 7.1, 2.0, ajustar=False, bandas=["40 m"])
    with pytest.raises(ValueError, match="solo valen para los tipos de HF"):
        disenar("dipolo", 145.0, 2.0, ajustar=False, altura_m=10)


def test_el_abanico_y_las_trampas_toman_la_frecuencia_de_la_banda_mas_baja():
    a = disenar("abanico", 14.2, 2.0, ajustar=False, bandas=["20 m", "10 m", "15 m"])
    assert abs(a.f_MHz - 14.175) < 0.01 and a.geometria["bandas"] == ["20 m", "10 m", "15 m"]
    t = disenar("trampas", 99.0, 2.0, ajustar=False, bandas=["20 m", "40 m"])
    assert t.geometria["bandas"] == ["40 m", "20 m"] and abs(t.geometria["f_baja_MHz"] - 7.1) < 0.01


def test_los_planos_llevan_la_hoja_del_balun_y_las_trampas_la_suya():
    for tipo, extra in (("dipolo_hf", {}), ("vinv_hf", {}), ("abanico", {"bandas": ["40 m", "20 m"]}), ("g5rv", {})):
        p = planos.generar(disenar(tipo, 7.1, 2.0, ajustar=False, **extra))
        assert len(p.hojas) == 2, tipo
    p = planos.generar(disenar("trampas", 7.1, 2.0, ajustar=False, bandas=["40 m", "20 m"]))
    assert len(p.hojas) == 3
    texto = " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)
    assert "Balun o choke 1:1" in texto and "Trampas · bobina y condensador" in texto and "vueltas de hilo" in texto


def test_la_bobina_de_la_trampa_sale_con_un_numero_razonable_de_vueltas():
    from wire.planos.hf_dipolos import _vueltas_bobina
    n, largo = _vueltas_bobina(3.7, 40.0, 2.0)
    assert 8 <= n <= 25 and 15 < largo < 80


@necesita_motor
def test_el_ajuste_del_dipolo_de_hf_adapta_la_banda():
    d = disenar("dipolo_hf", 7.1, 2.0)
    assert d.resultados["roe"] < 2.0 and 19.0 < d.geometria["largo_mm"] / 1000 < 22.0


@necesita_motor
def test_la_g5rv_sin_acoplador_no_adapta_en_todas_las_bandas():
    d = disenar("g5rv", 3.65, 2.0)
    roe = {b["banda"]: b["roe"] for b in d.resultados["bandas"]}
    assert max(roe.values()) > 5.0 and "10 m" in roe       # por eso se usa con acoplador


@necesita_motor
def test_el_ajuste_de_las_trampas_adapta_las_dos_bandas():
    d = disenar("trampas", 7.1, 2.0, bandas=["40 m", "20 m"])
    assert [b["banda"] for b in d.resultados["bandas"]] == ["40 m", "20 m"]
    assert max(b["roe"] for b in d.resultados["bandas"]) < 2.5


@necesita_motor
def test_la_trampa_corta_el_tramo_exterior_en_la_banda_alta():
    """Sin la carga de la trampa (cortocircuitada) la banda alta no resuena donde debe: la trampa hace algo."""
    d = disenar("trampas", 7.1, 2.0, ajustar=False, bandas=["40 m", "20 m"])
    m = d.modelo()
    from dataclasses import replace
    sin_trampa = replace(m, cargas=())
    f = 14.2
    z_con = motor.simular(replace(m, barrido=Barrido(f, f, 1)), diagrama=False).z[0]
    z_sin = motor.simular(replace(sin_trampa, barrido=Barrido(f, f, 1)), diagrama=False).z[0]
    assert abs(z_con - z_sin) > 20
