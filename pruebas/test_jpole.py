"""J-pole: geometría del generador (sin motor) y ajuste contra lo esperable (con PyNEC)."""

import pytest

from wire import jpole, longitud_onda_m, motor, nec
from wire.generadores import jpole_por_defecto


def _extremos(modelo):
    return [p for h in modelo.hilos for p in (h.inicio, h.fin)]


def test_geometria_de_la_jpole():
    m = jpole(145.0, 2.0, largo_mm=1500, corto_mm=520, toma_mm=35, separacion_mm=25)
    assert len(m.hilos) == 7
    largo = [h for h in m.hilos[:3]]
    assert largo[0].inicio == (0, 0, 0) and largo[-1].fin[2] == pytest.approx(1.5)
    assert sum(h.longitud for h in largo) == pytest.approx(1.5)
    assert sum(h.longitud for h in m.hilos[3:5]) == pytest.approx(0.52)
    assert m.hilos[5].longitud == pytest.approx(0.025)  # fondo de la U
    alimentacion = m.hilos[6]
    assert alimentacion.inicio[2] == alimentacion.fin[2] == pytest.approx(0.035)
    assert m.puerto.hilo == 7 and m.hilos[6].segmentos % 2 == 1
    assert all(h.radio == pytest.approx(0.001) for h in m.hilos)
    # Todos los extremos están unidos a otro hilo, salvo las dos puntas.
    extremos = _extremos(m)
    sueltos = [p for p in extremos if extremos.count(p) == 1]
    assert sorted(sueltos) == sorted([(0, 0, 1.5), (0.025, 0, 0.52)])


def test_jpole_por_defecto_y_errores():
    d = jpole_por_defecto(145.0, 2.0)
    lam = longitud_onda_m(145.0) * 1000
    assert d["largo_mm"] / lam == pytest.approx(0.73)
    assert d["separacion_mm"] >= 12
    with pytest.raises(ValueError):
        jpole(145.0, 2.0, toma_mm=600)  # toma por encima del brazo corto
    with pytest.raises(ValueError):
        jpole(145.0, 2.0, separacion_mm=3)


def test_jpole_exporta_un_mazo_valido():
    m = jpole(145.0, 2.0)
    texto = nec.exportar(m)
    nombres = [l.split()[0] for l in texto.splitlines()]
    assert nombres.count("GW") == 7
    # La fuente va en el segmento central (el puente lleva un número impar de segmentos).
    puente = m.hilos[6]
    assert puente.segmentos % 2 == 1 and m.puerto.segmento == puente.segmentos // 2 + 1
    assert f"EX 0 7 {m.puerto.segmento} 0" in texto
    assert nec.leer(texto)  # el mazo se vuelve a leer


con_motor = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


@pytest.fixture(scope="module")
def ajustes():
    """El ajuste con el motor tarda unos segundos: se hace una vez por frecuencia."""
    from wire import ajuste

    return {f: ajuste.ajustar_jpole(f, 2.0) for f in (145.0, 435.0)}


@con_motor
@pytest.mark.parametrize("f", [145.0, 435.0])
def test_jpole_converge_con_los_segmentos(ajustes, f):
    """Con el doble de segmentos el mínimo de ROE se mueve menos de un 0,2 % (docs/roadmap/fase1.md, W1.2)."""
    from wire import ajuste
    from wire.generadores import DENSIDAD_JPOLE

    g = ajustes[f]["geometria"]
    valores = []
    for densidad in (DENSIDAD_JPOLE, 2 * DENSIDAD_JPOLE):
        m = jpole(f, 2.0, g["largo_mm"], g["corto_mm"], g["toma_mm"], g["separacion_mm"], densidad=densidad)
        valores.append((sum(h.segmentos for h in m.hilos), ajuste.minimo_roe(m, 0.9 * f, 1.1 * f)))
    (n1, f1), (n2, f2) = valores
    assert n2 >= 1.8 * n1
    assert f1 == pytest.approx(f, rel=1e-4)  # el ajuste se hizo con la segmentación por defecto
    assert abs(f2 - f1) / f1 < 0.002


@con_motor
@pytest.mark.parametrize("f", [145.0, 435.0])
def test_jpole_ajustada(ajustes, f):
    r = ajustes[f]
    g, res = r["geometria"], r["resultados"]
    lam = longitud_onda_m(f) * 1000
    assert res["s11_dB"] <= -15  # adaptación a 50 Ω
    assert res["f_minimo_roe_MHz"] == pytest.approx(f, rel=0.005)
    assert 1.5 <= res["ganancia_dBi"] <= 3.0  # ~2 dBi
    assert 0.65 <= g["largo_mm"] / lam <= 0.78
    assert 0.22 <= g["corto_mm"] / lam <= 0.30
    assert 0 < g["toma_mm"] < g["corto_mm"]
    assert res["sensibilidad_MHz_por_mm"] > 0  # recortar la punta sube la frecuencia
    # ROE ≤ 2 en toda la banda de 2 m o de 70 cm
    banda = (144.0, 146.0) if f == 145.0 else (430.0, 440.0)
    roe_banda = [v for fi, v in zip(res["barrido"]["f_MHz"], res["barrido"]["roe"]) if banda[0] <= fi <= banda[1]]
    assert roe_banda and max(roe_banda) <= 2.0
