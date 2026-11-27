"""EFHW de HF: suelo real, transformador ideal por la impedancia de referencia, bandas armónicas y hojas del transformador."""

import json

import pytest

from wire import generadores, motor, nec, planos, web_api
from wire.diseno import disenar
from wire.modelo import Barrido

necesita_motor = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def test_el_mazo_nec_lleva_el_suelo_real_y_solo_el_hemisferio_de_arriba():
    texto = nec.exportar(generadores.efhw(7.1, 2.0))
    assert "GN 2 0 0 0 13 0.005" in texto and "GE -1" in texto
    assert "RP 0 19 72 1000" in texto
    assert "GN -1" not in texto


def test_un_modelo_sin_suelo_real_sigue_exportando_igual():
    texto = nec.exportar(generadores.dipolo(145.0, 1.0))
    assert "GN -1" in texto and "GN 2" not in texto and "RP 0 37 72" in texto


def test_las_bandas_de_una_efhw_son_la_propia_y_sus_armonicos():
    nombres = [b[0] for b in generadores.bandas_de(7.1, 49)]
    assert nombres == ["40 m", "20 m", "15 m", "10 m"]
    assert [b[0] for b in generadores.bandas_de(3.65, 64)] == ["80 m", "40 m", "20 m", "17 m"]
    assert "10 m" in [b[0] for b in generadores.bandas_de(7.1, 9)] and "30 m" in [b[0] for b in generadores.bandas_de(7.1, 9)]


def test_los_parametros_se_validan():
    with pytest.raises(ValueError, match="relación"):
        disenar("efhw", 7.1, 2.0, ajustar=False, relacion=5)
    with pytest.raises(ValueError, match="suelo"):
        disenar("efhw", 7.1, 2.0, ajustar=False, suelo="roca")
    with pytest.raises(ValueError, match="solo valen para los tipos de HF"):
        disenar("dipolo", 7.1, 2.0, ajustar=False, relacion=49)
    with pytest.raises(ValueError, match="solo valen para la EFHW"):
        disenar("dipolo_hf", 7.1, 2.0, ajustar=False, relacion=49)
    with pytest.raises(ValueError, match="altura"):
        disenar("efhw", 7.1, 2.0, ajustar=False, altura_m=0.5)


def test_el_plano_tiene_tres_hojas_y_el_transformador_depende_de_la_relacion():
    p49 = planos.generar(disenar("efhw", 7.1, 2.0, ajustar=False, relacion=49))
    p9 = planos.generar(disenar("efhw", 7.1, 2.0, ajustar=False, relacion=9))
    assert len(p49.hojas) == len(p9.hojas) == 3
    texto = lambda p: " ".join(getattr(e, "texto", "") for h in p.hojas for e in h.elementos)  # noqa: E731
    assert "2 vueltas de primario" in texto(p49) and "14 de secundario" in texto(p49) and "2,4 kΩ" in texto(p49)
    assert "9 vueltas en total" in texto(p9) and "470 Ω" in texto(p9) and "autotransformador" in texto(p9)
    assert "MÁS ADELANTE" not in texto(p49) and "Transformador de la EFHW" in texto(p49)     # la hoja apunta a la herramienta de Chirptenna VNA


def test_la_potencia_elige_el_nucleo():
    from wire.planos.hf import transformador
    assert transformador(49, 100)["nucleo"] == "FT140-43" and transformador(49, 400)["nucleo"] == "FT240-43"
    assert transformador(64, 50)["nucleo"] == "FT240-43"
    assert abs(transformador(49, 100)["tension_rms"] - 495) < 1


def test_la_api_web_acepta_los_parametros_de_hf():
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "efhw", "f_MHz": 14.2, "diametro_mm": 2, "relacion": 64, "altura_m": 8,
                                                 "suelo": "bueno", "potencia_w": 200})))
    g = r["diseno"]["geometria"]
    assert g["relacion"] == 64 and g["suelo"] == "bueno" and g["altura_mm"] == 8000 and len(r["hojas"]) == 3


@necesita_motor
def test_el_suelo_cambia_la_impedancia_de_la_efhw():
    f = 7.1
    z = {}
    for suelo in ("pobre", "mar"):
        m = generadores.efhw(f, 2.0, suelo=suelo, altura_mm=3000.0)        # baja: el suelo pesa
        z[suelo] = motor.simular(m, Barrido(f, f, 1), diagrama=False, z0=2450.0).z[0]
    assert abs(z["pobre"] - z["mar"]) > 50


@necesita_motor
def test_la_ganancia_con_suelo_real_es_un_numero_razonable():
    f = 14.2
    r = motor.simular(generadores.efhw(f, 2.0), Barrido(f, f, 1), diagrama=True, z0=2450.0)
    assert 0.0 < r.ganancia_max[0] < 12.0           # antes del RP de media esfera salían números absurdos


@necesita_motor
def test_el_ajuste_de_la_efhw_49_adapta_la_banda_de_diseno():
    d = disenar("efhw", 7.1, 2.0, relacion=49, altura_m=10, suelo="normal")
    bandas = {b["banda"]: b for b in d.resultados["bandas"]}
    assert set(bandas) == {"40 m", "20 m", "15 m", "10 m"}
    assert bandas["40 m"]["roe"] < 2.0 and max(b["roe"] for b in bandas.values()) < 3.5
    assert 18.0 < d.geometria["largo_mm"] / 1000 < 23.0
