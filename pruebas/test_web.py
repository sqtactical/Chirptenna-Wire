"""Web lite: el núcleo empaquetado no arrastra el motor y la API devuelve lo mismo que el escritorio."""

import importlib.util
import json
import os
import zipfile

from wire import planos, web_api
from wire.diseno import disenar

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _construir():
    espec = importlib.util.spec_from_file_location("construir_web", os.path.join(RAIZ, "herramientas", "construir_web.py"))
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


def test_el_zip_lleva_el_nucleo_sin_el_motor(tmp_path):
    _construir().construir(str(tmp_path / "web"))
    with zipfile.ZipFile(tmp_path / "web" / "py" / "wire.zip") as z:
        nombres = z.namelist()
    assert "wire/web_api.py" in nombres and "wire/planos/pdf.py" in nombres
    assert "wire/motor.py" not in nombres and "wire/ajuste.py" not in nombres
    assert os.path.exists(tmp_path / "web" / "index.html")


def test_catalogo_y_plano():
    c = json.loads(web_api.catalogo())
    assert {t["clave"] for t in c["tipos"]} == {"dipolo", "jpole", "manga", "coco", "jpole_koch", "discone", "gp", "vinv", "yagi", "biconica"}
    assert c["coaxial"]["tipos"] == ["manga", "coco"] and any(k["nombre"] == "RG-58" for k in c["coaxial"]["cables"])
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "jpole", "f_MHz": 435, "diametro_mm": 2})))
    assert r["estado"] == "Sin validar" and len(r["hojas"]) == 2 and r["hojas"][0].startswith("<svg")
    assert web_api.plano_pdf(json.dumps({"diseno": r["diseno"]})).startswith(b"%PDF-")


def test_un_diseno_de_escritorio_da_el_mismo_plano_en_la_api():
    d = disenar("dipolo", 145, 2.0, ajustar=False)
    esperado = [planos.a_svg(h) for h in planos.generar(d).hojas]
    r = json.loads(web_api.plano_svg(json.dumps({"diseno": d.a_dict()})))
    assert r["hojas"] == esperado


def test_la_api_genera_el_plano_de_una_coco_con_vf_medido():
    r = json.loads(web_api.plano_svg(json.dumps({"tipo": "coco", "f_MHz": 433, "cable": "RG-316", "vf_medido": 0.7})))
    assert len(r["hojas"]) >= 3 and r["diseno"]["cable"] == {"nombre": "RG-316", "z0": 50.0, "vf": 0.7, "vf_origen": "medido"}
    assert web_api.nec_texto(json.dumps({"diseno": r["diseno"]})).startswith("CM")
