"""VF medido con Chirptenna VNA: el JSON que descarga se lee y se aplica al diseño."""

import json
import os

import pytest

from wire.__main__ import main
from wire.cables import leer_cable_medido
from wire.diseno import Diseno

MEDIDO = {"formato": "chirptenna-cable", "version": 1, "nombre": "RG-58 azul", "vf": 0.667, "largo_m": 2.0,
          "extremo": "abierto", "perdida_db_100m": 24.5, "f_perdida_MHz": 30.0, "fecha": "2026-11-25"}


def test_lee_el_json_de_chirptenna_vna_con_o_sin_bom():
    assert leer_cable_medido(json.dumps(MEDIDO))["vf"] == 0.667
    assert leer_cable_medido("﻿" + json.dumps(MEDIDO))["nombre"] == "RG-58 azul"


@pytest.mark.parametrize("texto", ["no es json", json.dumps({"vf": 0.66}), json.dumps({**MEDIDO, "vf": 1.7}),
                                   json.dumps({**MEDIDO, "vf": 0.1}), json.dumps({**MEDIDO, "vf": "0,66"}),
                                   json.dumps({**MEDIDO, "vf": True}), "[1, 2]"])
def test_rechaza_lo_que_no_es_una_medida_creible(texto):
    with pytest.raises(ValueError):
        leer_cable_medido(texto)


def test_la_cli_aplica_el_vf_medido_a_la_coco(tmp_path):
    cable = tmp_path / "cable.json"
    cable.write_text(json.dumps(MEDIDO), encoding="utf-8")
    json_salida = tmp_path / "coco.json"
    main(["plano", "coco", "433", "--sin-motor", "--cable-medido", str(cable), "--salida", str(tmp_path / "coco.svg"),
          "--guardar", str(json_salida)])
    d = Diseno.desde_json(json_salida.read_text(encoding="utf-8"))
    assert d.cable["vf"] == 0.667 and d.cable["vf_origen"] == "medido"
    assert [n for n in os.listdir(tmp_path) if n.startswith("coco") and n.endswith(".svg")]
