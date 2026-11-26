"""Diagrama de radiación de la simulación: rejilla de PyNEC y cortes polares en SVG."""

import numpy as np
import pytest

from wire import motor
from wire.diseno import disenar
from wire.graficas import svg_diagrama

pytestmark = pytest.mark.skipif(not motor.disponible(), reason="PyNEC no está instalado")


def test_diagrama_de_un_dipolo_en_espacio_libre():
    d = disenar("dipolo", 145.0, 2.0, ajustar=False)
    th, ph, g = motor.diagrama(d.modelo())
    assert g.shape == (len(th), len(ph)) and th[0] == 0.0 and th[-1] == 180.0
    assert g.max() == pytest.approx(2.15, abs=0.3)          # λ/2 en espacio libre
    it, _ = np.unravel_index(int(np.argmax(g)), g.shape)
    assert 85.0 <= th[it] <= 95.0                           # el máximo es perpendicular al hilo


def test_diagrama_con_suelo_solo_hemisferio_superior():
    d = disenar("efhw", 7.1, 2.0, ajustar=False, altura_m=10.0, suelo="normal")
    th, _, g = motor.diagrama(d.modelo())
    assert th[-1] <= 90.0 and g.max() > 4.0


def test_svg_con_dos_cortes():
    d = disenar("yagi", 145.0, 2.0, ajustar=False, elementos=5)
    svg = svg_diagrama(*motor.diagrama(d.modelo()))
    assert svg.startswith("<svg") and svg.count("<polygon") == 2 and "nan" not in svg
