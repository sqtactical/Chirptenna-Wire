"""W2.1 y W2.2: el tramo de coaxial se comporta como la teoría y la tabla de cables es coherente."""

import math

import pytest

from wire import Barrido, Hilo, Modelo, Puerto, motor, nec
from wire.cables import CABLES, cable
from wire.coaxial import impedancia_stub_abierto, longitud_cuarto_de_onda_m, tramo_coaxial

C0 = 299_792_458.0


def _modelo_stub(c, longitud_m, f_MHz):
    """Fuente en un hilo diminuto unido por una TL abierta (al otro hilo diminuto) de `longitud_m` de cable."""
    a = Hilo((0, 0, 0), (0, 0, 0.02), 0.001, 1)
    b = Hilo((1.0, 0, 0), (1.0, 0, 0.02), 0.001, 1)
    from wire.modelo import Linea
    linea = Linea(1, 1, 2, 1, c.z0, longitud_m, c.vf)
    return Modelo("stub", f_MHz, (a, b), Puerto(1, 1), lineas=(linea,), barrido=Barrido(f_MHz, f_MHz, 1))


def test_el_tramo_devuelve_malla_y_linea_con_el_vf():
    c = cable("RG-58")
    hilo, linea = tramo_coaxial((0, 0, 0), (0, 0, 1.0), c, 11, indice_hilo=3)
    assert hilo.radio == pytest.approx(c.radio_malla_m) and hilo.segmentos == 11
    assert (linea.hilo1, linea.segmento1, linea.hilo2, linea.segmento2) == (3, 1, 3, 11)
    assert linea.longitud == pytest.approx(1.0) and linea.longitud_electrica == pytest.approx(1.0 / c.vf)


def test_la_tl_exportada_lleva_la_longitud_electrica():
    c = cable("RG-58")
    _, linea = tramo_coaxial((0, 0, 0), (0, 0, 1.0), c, 3, indice_hilo=1)
    modelo = Modelo("t", 100.0, (Hilo((0, 0, 0), (0, 0, 1), 0.001, 3),), Puerto(1, 2), lineas=(linea,))
    tl = [t for t in nec.leer(nec.exportar(modelo)) if t.nombre == "TL"]
    assert len(tl) == 1 and tl[0].reales[0] == pytest.approx(50.0) and tl[0].reales[1] == pytest.approx(1.0 / 0.66, rel=1e-4)


@pytest.mark.skipif(not motor.disponible(), reason="no hay PyNEC")
def test_stub_abierto_de_cuarto_de_onda_se_ve_como_un_cortocircuito():
    c = cable("RG-58")
    longitud = 1.0                                   # m de cable
    f = C0 / (4 * longitud / c.vf) / 1e6             # λ/4 eléctrico en MHz (≈ 49,5 MHz)
    z = motor.simular(_modelo_stub(c, longitud, f)).z[0]
    assert abs(z) < 5.0, z
    # A la mitad de esa frecuencia la línea mide λ/8: reactancia capacitiva de −Z0·cot(π/4) ≈ −50 Ω (la teoría).
    z8 = motor.simular(_modelo_stub(c, longitud, f / 2)).z[0]
    teoria = impedancia_stub_abierto(c.z0, longitud / c.vf, f / 2)
    assert z8.imag == pytest.approx(teoria.imag, rel=0.25) and z8.imag < 0


def test_cuarto_de_onda_en_el_cable_usa_el_vf():
    c = cable("LMR-400")
    assert longitud_cuarto_de_onda_m(145.0, c) == pytest.approx(C0 / 145e6 * 0.85 / 4)


def test_tabla_de_cables():
    for nombre in ("RG-58", "RG-174", "RG-316", "RG-213", "LMR-400", "Aircell 7", "H155"):
        c = CABLES[nombre]
        assert c.z0 == 50.0 and 0.6 <= c.vf <= 0.9
        assert c.diametro_dielectrico_mm < c.diametro_malla_mm < c.diametro_exterior_mm
        assert c.perdida_1000MHz_dB_100m > c.perdida_100MHz_dB_100m > 0
        assert c.perdida_dB(100.0, 100.0) == pytest.approx(c.perdida_100MHz_dB_100m)
        assert c.perdida_dB(1000.0, 100.0) == pytest.approx(c.perdida_1000MHz_dB_100m)
        assert not c.verificado and c.vf_origen == "catálogo"


def test_el_diseno_guarda_el_cable_y_el_origen_del_vf():
    from wire.diseno import Diseno, disenar
    d = disenar("dipolo", 145.0, 2.0, ajustar=False).con_cable(cable("RG-58").con_vf_medido(0.67))
    otro = Diseno.desde_json(d.a_json())
    assert otro.cable == {"nombre": "RG-58", "z0": 50.0, "vf": 0.67, "vf_origen": "medido"}
    assert disenar("dipolo", 145.0, 2.0, ajustar=False).cable is None


def test_vf_medido_sustituye_al_de_catalogo():
    medido = cable("RG-58").con_vf_medido(0.68)
    assert medido.vf == 0.68 and medido.vf_origen == "medido" and cable("RG-58").vf == 0.66
    with pytest.raises(ValueError):
        cable("RG-58").con_vf_medido(1.2)
    with pytest.raises(ValueError):
        cable("RG-999")
