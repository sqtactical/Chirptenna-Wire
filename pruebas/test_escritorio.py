"""Lo que la interfaz de escritorio pide al motor: diseños con los campos propios de cada tipo y la plantilla 3D."""

import io
import json
import zipfile

import pytest

from wire import escritorio


def test_calcular_pasa_lo_propio_de_cada_tipo():
    d = json.loads(escritorio.calcular("yagi", 145.0, 2.0, False, None, None, "A4", "mm", "es", elementos=5, eje="unido", eje_mm=20.0))
    assert d["geometria"]["n_elementos"] == 5 and d["geometria"]["boom"] == "unido"
    d = json.loads(escritorio.calcular("colineal_bibanda", 145.0, 3.0, False, None, None, "A4", "mm", "es", elementos=2, f_alta_MHz=433.0))
    assert d["geometria"]["f_alta_MHz"] == 433.0
    d = json.loads(escritorio.calcular("efhw", 7.1, 2.0, False, None, None, "A4", "mm", "es", relacion=64, altura_m=8.0, suelo="bueno",
                                       potencia_w=50.0, largo_max_m=15.0))
    assert d["geometria"]["relacion"] == 64


def test_lo_que_no_vale_para_el_tipo_se_rechaza():
    with pytest.raises(ValueError):
        escritorio.calcular("dipolo", 145.0, 2.0, False, None, None, "A4", "mm", "es", elementos=5)


def test_plantilla3d_zip():
    d = escritorio.calcular("jpole", 145.0, 2.0, False, None, None, "A4", "mm", "es")
    z = zipfile.ZipFile(io.BytesIO(escritorio.plantilla3d(d)))
    assert any(n.endswith(".stl") for n in z.namelist())
