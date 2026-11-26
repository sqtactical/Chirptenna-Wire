"""Colineal con bobinas de fase: geometría, validaciones, planos y (con PyNEC) ajuste y ganancia."""

import pytest

from wire import generadores, planos
from wire.diseno import Diseno, disenar
from wire.motor import disponible

PYNEC = pytest.mark.skipif(not disponible(), reason="PyNEC no está instalado")


@pytest.mark.parametrize("n", [2, 3, 4, 5, 6])
def test_modelo_tiene_n_secciones_y_n_menos_uno_bobinas(n):
    d = disenar("colineal", 145.0, 3.0, ajustar=False, elementos=n)
    m = d.modelo()
    assert len(d.geometria["secciones_mm"]) == n
    assert len(m.cargas) == n - 1 and all(c.l > 0 for c in m.cargas)
    assert d.estado == "Sin validar"


def test_la_bobina_escala_con_la_frecuencia():
    a = generadores.colineal_por_defecto(145.0, 3)["bobina_uH"]
    b = generadores.colineal_por_defecto(435.0, 3)["bobina_uH"]
    assert a == pytest.approx(3 * b)


def test_validaciones():
    with pytest.raises(ValueError):
        disenar("colineal", 145.0, 3.0, ajustar=False, elementos=7)
    with pytest.raises(ValueError):
        disenar("colineal", 145.0, 3.0, ajustar=False, eje="unido")
    with pytest.raises(ValueError):
        disenar("dipolo", 145.0, 3.0, ajustar=False, elementos=3)


def test_planos_dos_hojas_y_json_redondo():
    d = disenar("colineal", 433.0, 2.0, ajustar=False, elementos=2)
    assert len(planos.generar(d).hojas) == 2
    assert Diseno.desde_json(d.a_json()).modelo().hilos == d.modelo().hilos


@PYNEC
def test_ajuste_da_50_ohm_y_la_ganancia_prometida():
    from wire.motor import simular
    for n, g_min in ((2, 3.0), (3, 4.5)):
        d = disenar("colineal", 145.0, 3.0, elementos=n)
        r = d.resultados
        assert d.estado == "Simulado" and r["roe"] < 1.15 and r["ganancia_dBi"] >= g_min - 0.2
        assert simular(d.modelo()).ganancia_max[0] == pytest.approx(r["ganancia_dBi"], abs=0.05)


# ---------------------------------------------------------------- bibanda 145 / 433

@pytest.mark.parametrize("n", [2, 4])
def test_bibanda_lleva_enlaces_l_c_en_serie(n):
    d = disenar("colineal_bibanda", 145.0, 3.0, ajustar=False, elementos=n)
    m = d.modelo()
    assert len(m.cargas) == n - 1 and all(c.l > 0 and c.c > 0 for c in m.cargas)
    assert d.geometria["f_alta_MHz"] == 433.0
    assert len(planos.generar(d).hojas) == 2
    assert Diseno.desde_json(d.a_json()).modelo().hilos == m.hilos


def test_bibanda_validaciones():
    with pytest.raises(ValueError):
        disenar("colineal_bibanda", 145.0, 3.0, ajustar=False, elementos=3)          # ≈ λ/2 en la banda baja
    with pytest.raises(ValueError):
        disenar("colineal_bibanda", 145.0, 3.0, ajustar=False, f_alta_MHz=900.0)     # razón fuera de 2,5 a 3,5
    with pytest.raises(ValueError):
        disenar("colineal", 145.0, 3.0, ajustar=False, f_alta_MHz=433.0)


@PYNEC
def test_bibanda_adapta_en_las_dos_bandas():
    d = disenar("colineal_bibanda", 145.0, 3.0, elementos=2)
    r = d.resultados
    assert d.estado == "Simulado" and r["roe"] < 1.2 and r["alta"]["roe"] < 1.2
    assert r["alta"]["ganancia_dBi"] > r["ganancia_dBi"] + 1.0        # en la alta apila medias ondas
