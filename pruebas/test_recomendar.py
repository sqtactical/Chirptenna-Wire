"""Recomendador de antenas por frecuencia, ganancia y tamaño."""

import pytest

from wire import recomendar as R
from wire.__main__ import main


def test_vhf_ordena_por_ganancia_y_filtra_por_tamano():
    todos = R.recomendar(145.0)
    gan = [f["ganancia_dBi"] for f in todos]
    assert gan == sorted(gan, reverse=True) and todos[0]["tipo"] == "yagi" and todos[0]["elementos"] == 15
    chicos = R.recomendar(145.0, tamano_max_m=1.0)
    assert chicos and all(f["tamano_m"] <= 1.0 for f in chicos) and len(chicos) < len(todos)
    buenos = R.recomendar(145.0, ganancia_min=8.0)
    assert buenos and all(f["ganancia_dBi"] >= 8.0 for f in buenos) and {f["tipo"] for f in buenos} == {"yagi"}


def test_hf_y_rangos():
    hf = R.recomendar(7.1)
    assert {f["tipo"] for f in hf} >= {"dipolo_hf", "vertical_hf", "efhw"}
    assert R.recomendar(7.1, tamano_max_m=1.0) == []                      # a 7 MHz nada de alambre cabe en 1 m
    with pytest.raises(ValueError):
        R.recomendar(0.5)
    with pytest.raises(ValueError):
        R.recomendar(2000.0)


def test_web_api():
    import io
    import json
    import zipfile
    from wire import web_api
    r = json.loads(web_api.recomendar_json(json.dumps({"f_MHz": 433, "ganancia_dBi": 6, "idioma": "en"})))
    assert r["error"] is None and r["filas"] and all(f["ganancia_dBi"] >= 6 for f in r["filas"])
    assert "Yagi" in r["filas"][0]["nombre"]
    assert json.loads(web_api.recomendar_json(json.dumps({"f_MHz": 5000})))["error"]
    assert "aisladores" in json.loads(web_api.catalogo())
    z = web_api.aisladores_zip(json.dumps({"tipo": "dipolo", "f_MHz": 145}))
    assert any(n.endswith(".stl") for n in zipfile.ZipFile(io.BytesIO(z)).namelist())


def test_cli(capsys):
    assert main(["recomendar", "433", "--ganancia", "6"]) == 0
    assert "Yagi" in capsys.readouterr().out
    assert main(["recomendar", "145", "--ganancia", "30"]) == 1
