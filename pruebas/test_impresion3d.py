"""Plantillas de doblado en 3D: STL válidos, baldosas dentro de la cama y encajes que coinciden."""

import json
import math
import struct
import zipfile
import io

import pytest

from wire import impresion3d as I, web_api
from wire.diseno import disenar


def _caja(stl: bytes):
    n = struct.unpack("<I", stl[80:84])[0]
    assert len(stl) == 84 + 50 * n
    pts = [struct.unpack("<12fH", stl[84 + 50 * k: 134 + 50 * k])[3:12] for k in range(n)]
    xs = [v[i] for v in pts for i in (0, 3, 6)]
    ys = [v[i] for v in pts for i in (1, 4, 7)]
    zs = [v[i] for v in pts for i in (2, 5, 8)]
    return n, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs))


def test_la_j_pole_de_koch_se_parte_en_baldosas_que_caben_en_la_cama():
    p = I.generar(disenar("jpole_koch", 434.0, 2.0, ajustar=False), cama=(200.0, 200.0))
    assert p.filas > 1 and len(p.piezas) == p.columnas * p.filas
    for nombre, stl in p.piezas.items():
        n, (x0, x1), (y0, y1), (z0, z1) = _caja(stl)
        assert x1 - x0 <= 200.0 and y1 - y0 <= 200.0, nombre
        assert z0 == 0.0 and z1 > I.ESPESOR


def test_una_plantilla_pequena_va_en_una_sola_pieza():
    p = I.generar(disenar("jpole", 434.0, 2.0, ajustar=False), cama=(300.0, 300.0))
    assert list(p.piezas) == ["plantilla.stl"] and p.avisos == []


def test_las_pestanas_de_una_baldosa_coinciden_con_las_ranuras_de_la_vecina():
    d = disenar("jpole_koch", 434.0, 2.0, ajustar=False)
    c = I.trazado(d).camino
    xs, ys = [q[0] for q in c], [q[1] for q in c]
    y0, y1 = min(ys) - I.MARGEN, max(ys) + I.MARGEN
    # la costura entre las filas 1 y 2: mismos centros en la pestaña de abajo y la ranura de arriba
    p = I.generar(d)
    th = (y1 - y0) / p.filas
    sitios, _ = I._sitios(c, 1, y0 + th, min(xs) - I.MARGEN, max(xs) + I.MARGEN, 3, I.ANCHO_CABEZA / 2 + 2.0)
    for s in sitios:
        ranura = I._rects_ranura(1, y0 + th, s, 0.3)
        pestana = I._rects_pestana(1, y0 + th, s, 0.3)
        for r, q in zip(ranura, pestana):                  # la pestaña cabe dentro de la ranura, con holgura
            assert r[0] < q[0] and q[2] < r[2] and r[3] > q[3] - 1e-9


def test_la_plantilla_deja_libre_el_hueco_del_alambre():
    d = disenar("jpole", 434.0, 2.0, ajustar=False)
    camino = I.trazado(d).camino
    quads = I.rieles(camino, 2.0, 0.3)
    for q in quads:
        for a, b in zip(q, q[1:] + q[:1]):
            pass
    # ningún vértice de las costillas cae más cerca del eje del alambre que d/2 + holgura
    for q in quads:
        for v in q:
            assert I._distancia_camino(v, camino) >= 2.0 / 2 + 0.3 - 1e-6


def test_las_esquinas_llevan_el_radio_de_doblado_y_acortan_el_camino():
    camino = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0)]            # un doblez de 90°
    curvo, r_min, reducidas = I.redondear(camino, 10.0)
    assert reducidas == 0 and abs(r_min - 10.0) < 1e-9
    assert curvo[0] == camino[0] and curvo[-1] == camino[-1]
    # el arco empieza a t = R·tan(45°) = 10 mm antes de la esquina y la cuerda queda a R del centro (90, 10)
    assert any(abs(p[0] - 90.0) < 1e-6 and abs(p[1]) < 1e-6 for p in curvo)
    assert all(abs(math.dist(p, (90.0, 10.0)) - 10.0) < 1e-6 for p in curvo[1:-1])
    assert I._largo(curvo) < I._largo(camino)
    assert abs((I._largo(camino) - I._largo(curvo)) - (2 * 10 - math.pi * 10 / 2)) < 0.1     # 2t − πR/2


def test_el_radio_se_reduce_en_tramos_cortos_y_se_avisa():
    camino = [(0.0, 0.0), (12.0, 0.0), (12.0, 12.0), (0.0, 12.0)]
    curvo, r_min, reducidas = I.redondear(camino, 10.0)
    assert reducidas == 2 and r_min < 10.0
    p = I.generar(disenar("jpole_koch", 434.0, 2.0, ajustar=False), radio_mm=30.0)
    assert any("radio de doblado se reduce" in a.lower() for a in p.avisos)
    assert "radio de doblado de 30" in p.leeme


def test_un_radio_menor_que_1_5_diametros_avisa():
    p = I.generar(disenar("jpole", 434.0, 2.0, ajustar=False), radio_mm=2.0)
    assert any("muy cerrado" in a for a in p.avisos)


def test_el_tipo_sin_plantilla_da_error_claro():
    with pytest.raises(ValueError, match="plantilla 3D"):
        I.trazado(disenar("dipolo", 145.0, 2.0, ajustar=False))


def test_el_zip_lleva_los_stl_el_mapa_y_el_leeme():
    p = I.generar(disenar("jpole_koch", 434.0, 2.0, ajustar=False))
    z = zipfile.ZipFile(io.BytesIO(I.a_zip(p)))
    nombres = z.namelist()
    assert "LEEME.txt" in nombres and "mapa.svg" in nombres and sum(n.endswith(".stl") for n in nombres) == len(p.piezas)
    assert "Sin probar en una impresora" in z.read("LEEME.txt").decode("utf-8")


def test_la_api_web_da_el_mismo_zip_y_anuncia_los_tipos():
    assert json.loads(web_api.catalogo())["plantilla3d"] == list(I.TIPOS_3D)
    entrada = json.dumps({"tipo": "jpole_koch", "f_MHz": 434, "diametro_mm": 2, "cama_mm": 150})
    z = zipfile.ZipFile(io.BytesIO(web_api.plantilla3d_zip(entrada)))
    assert any(n.endswith(".stl") for n in z.namelist())
