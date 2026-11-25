"""Exportador `.nec`: tarjetas, formato y lectura de vuelta. No necesita PyNEC."""

import pytest

from wire import Barrido, Carga, Conductividad, Hilo, Linea, Modelo, Puerto, dipolo, longitud_onda_m
from wire import nec

MNEMONICOS = {"CM", "CE", "GW", "GE", "GN", "EX", "TL", "LD", "FR", "RP", "EN"}


def _dipolo():
    return dipolo(145.0, radio_mm=2.0)


def test_dipolo_geometria():
    m = _dipolo()
    h = m.hilos[0]
    assert h.segmentos % 2 == 1
    assert m.puerto.segmento == h.segmentos // 2 + 1
    assert h.longitud == pytest.approx(0.48 * longitud_onda_m(145.0))
    assert h.inicio[2] == pytest.approx(-h.fin[2])


def test_mazo_orden_y_formato():
    texto = nec.exportar(_dipolo())
    lineas = texto.splitlines()
    assert texto.endswith("EN\n")
    assert texto.isascii()
    nombres = [l.split()[0] for l in lineas]
    assert set(nombres) <= MNEMONICOS
    assert nombres[0] == "CM"
    # Comentarios primero, luego CE, geometría, GE y control, con EN al final.
    ce = nombres.index("CE")
    assert all(n == "CM" for n in nombres[:ce])
    assert nombres[ce + 1:] == ["GW", "GE", "GN", "EX", "FR", "RP", "EN"]
    for l in lineas:
        assert "\t" not in l
        if not l.startswith("CM"):
            assert "," not in l  # el separador decimal es el punto
        assert l == l.strip()


def test_tarjetas_del_dipolo():
    m = _dipolo()
    t = {x.nombre: x for x in nec.tarjetas(m)}
    h = m.hilos[0]
    assert t["GW"].enteros == (1, h.segmentos)
    assert t["GW"].reales == (*h.inicio, *h.fin, h.radio)
    assert t["GE"].enteros == (0,)
    assert t["GN"].enteros[0] == -1
    assert t["EX"].enteros == (0, 1, m.puerto.segmento, 0)
    assert t["EX"].reales[:2] == (1.0, 0.0)
    assert t["FR"].enteros == (0, 1, 0, 0) and t["FR"].reales == (145.0, 0.0)


def test_campos_numericos_validos():
    """Cada tarjeta lleva los enteros como enteros y los reales en notación que lee C (strtod)."""
    for linea in nec.exportar(_dipolo()).splitlines():
        nombre, *campos = linea.split()
        if nombre in ("CM", "CE"):
            continue
        n_ent, n_real = nec.CAMPOS[nombre]
        assert len(campos) == n_ent + n_real
        for c in campos[:n_ent]:
            int(c)
        for c in campos[n_ent:]:
            float(c)


def test_barrido_en_fr():
    m = dipolo(145.0, 2.0, barrido=Barrido(140.0, 150.0, 21))
    fr = [t for t in nec.tarjetas(m) if t.nombre == "FR"][0]
    assert fr.enteros == (0, 21, 0, 0)
    assert fr.reales == pytest.approx((140.0, 0.5))


def test_sin_diagrama_no_hay_rp():
    nombres = [t.nombre for t in nec.tarjetas(_dipolo(), diagrama=False)]
    assert "RP" not in nombres and nombres[-1] == "EN"


def test_suelo_perfecto_con_monopolo():
    lam = longitud_onda_m(145.0)
    h = Hilo((0, 0, 0), (0, 0, 0.24 * lam), 0.002, 13)
    m = Modelo("Monopolo", 145.0, (h,), Puerto(1, 1), plano_masa=True)
    t = {x.nombre: x for x in nec.tarjetas(m)}
    assert t["GE"].enteros == (1,)  # el hilo toca el suelo
    assert t["GN"].enteros[0] == 1
    flotante = Modelo("Alto", 145.0, (Hilo((0, 0, 1), (0, 0, 2), 0.002, 11),), Puerto(1, 6), plano_masa=True)
    assert [x for x in nec.tarjetas(flotante) if x.nombre == "GE"][0].enteros == (-1,)


def test_linea_carga_y_conductividad():
    a = Hilo((0, 0, 0), (0, 0, 1), 0.001, 11)
    b = Hilo((0, 0.1, 0), (0, 0.1, 1), 0.001, 11)
    m = Modelo(
        "Prueba", 145.0, (a, b), Puerto(1, 6),
        lineas=(Linea(1, 6, 2, 6, z0=50.0, longitud=0.66, vf=0.66, cruzada=True),),
        cargas=(Carga(2, 1, 1, r=10.0, l=1e-9, c=1e-12), Conductividad(5.8e7)),
    )
    t = nec.tarjetas(m)
    tl = [x for x in t if x.nombre == "TL"][0]
    assert tl.enteros == (1, 6, 2, 6)
    assert tl.reales[0] == -50.0  # cruzada: Z0 negativo
    assert tl.reales[1] == pytest.approx(1.0)  # longitud eléctrica = 0,66 / 0,66
    ld = [x for x in t if x.nombre == "LD"]
    assert ld[0].enteros == (0, 2, 1, 1) and ld[0].reales == (10.0, 1e-9, 1e-12)
    assert ld[1].enteros == (5, 0, 0, 0) and ld[1].reales[0] == 5.8e7
    # LD va antes que EX y TL después, como en los mazos de 4nec2.
    nombres = [x.nombre for x in t]
    assert nombres.index("LD") < nombres.index("EX") < nombres.index("TL") < nombres.index("FR")


def test_leer_devuelve_las_mismas_tarjetas():
    m = dipolo(433.0, 1.0, barrido=Barrido(420.0, 450.0, 7))
    leidas, originales = nec.leer(nec.exportar(m)), nec.tarjetas(m)
    assert len(leidas) == len(originales)
    for a, b in zip(leidas, originales):
        assert (a.nombre, a.enteros) == (b.nombre, b.enteros)
        assert a.reales == pytest.approx(b.reales, rel=1e-8, abs=1e-12)  # 9 cifras significativas


def test_leer_rechaza_mazos_raros():
    with pytest.raises(ValueError):
        nec.leer("CM x\nCE\nGW 1 11 0 0 0 0 0 1 0.001\n")  # sin EN
    with pytest.raises(ValueError):
        nec.leer("CE\nSP 0 0\nEN\n")  # tarjeta no admitida


def test_comentarios_sin_tildes():
    m = dipolo(145.0, 2.0)
    texto = nec.exportar(m)
    assert "CM Dipolo de media onda" in texto
    assert texto.isascii()


def test_validaciones_del_modelo():
    h = Hilo((0, 0, 0), (0, 0, 1), 0.001, 11)
    with pytest.raises(ValueError):
        Modelo("x", 145.0, (h,), Puerto(1, 12))
    with pytest.raises(ValueError):
        Modelo("x", 145.0, (h,), Puerto(2, 1))
    with pytest.raises(ValueError):
        Linea(1, 1, 1, 2, z0=50.0, longitud=1.0, vf=1.2)
    with pytest.raises(ValueError):
        dipolo(145.0, 2.0, segmentos=24)
