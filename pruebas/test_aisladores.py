"""Aisladores 3D de dipolos y EFHW."""

import io
import struct
import zipfile

import pytest

from wire import aisladores, escritorio
from wire.diseno import disenar


def _triangulos(stl: bytes) -> int:
    return struct.unpack("<I", stl[80:84])[0]


def test_dipolo_lleva_centro_y_extremo():
    d = disenar("dipolo_hf", 7.1, 3.0, ajustar=False)
    p = aisladores.generar(d)
    assert set(p) == {"aislador_centro.stl", "aislador_extremo.stl"}
    for stl in p.values():
        assert len(stl) == 84 + 50 * _triangulos(stl) and _triangulos(stl) > 50


def test_efhw_solo_lleva_extremo_y_el_abanico_mas_agujeros():
    assert set(aisladores.generar(disenar("efhw", 7.1, 3.0, ajustar=False))) == {"aislador_extremo.stl"}
    uno = aisladores.generar(disenar("dipolo_hf", 7.1, 3.0, ajustar=False))["aislador_centro.stl"]
    cuatro = aisladores.generar(disenar("abanico", 7.1, 3.0, ajustar=False, bandas=["40 m", "20 m", "15 m", "10 m"]))["aislador_centro.stl"]
    assert _triangulos(cuatro) > _triangulos(uno)


def test_el_agujero_sigue_al_diametro():
    fino = aisladores.centro(1.0)
    grueso = aisladores.centro(6.0)
    assert fino != grueso


def test_tipos_sin_aisladores_se_rechazan():
    with pytest.raises(ValueError):
        aisladores.generar(disenar("jpole", 145.0, 3.0, ajustar=False))


def test_zip_del_escritorio():
    d = disenar("vinv_hf", 7.1, 3.0, ajustar=False)
    z = zipfile.ZipFile(io.BytesIO(escritorio.aisladores(d.a_json())))
    assert {"aislador_centro.stl", "aislador_extremo.stl", "LEEME.txt"} <= set(z.namelist())
    assert "imprime 2" in z.read("LEEME.txt").decode("utf-8")
