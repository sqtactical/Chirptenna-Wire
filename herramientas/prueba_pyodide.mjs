// Genera un plano con el paquete `wire` dentro de Pyodide (como la web lite) y guarda la descripción vectorial y
// el PDF, para compararlos con los del escritorio (pruebas/test_pyodide.py).
//
//   node herramientas/prueba_pyodide.mjs <carpeta con node_modules/pyodide> <raíz del repo> <diseno.json> <salida>
//
// Escribe <salida>.json (descripción) y <salida>.pdf. Necesita red la primera vez (micropip baja fpdf2).
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { pathToFileURL } from "node:url";

const [modulos, raiz, diseno, salida] = process.argv.slice(2);
const { loadPyodide } = await import(pathToFileURL(join(modulos, "node_modules", "pyodide", "pyodide.mjs")));

const t0 = Date.now();
const py = await loadPyodide();
await py.loadPackage("micropip");
await py.pyimport("micropip").install("fpdf2");

// Copia el paquete wire/ (sin __pycache__) al sistema de archivos de Pyodide.
function copiar(carpeta) {
  for (const nombre of readdirSync(carpeta)) {
    const ruta = join(carpeta, nombre);
    if (nombre === "__pycache__") continue;
    const destino = "/home/pyodide/" + relative(raiz, ruta).replaceAll("\\", "/");
    if (statSync(ruta).isDirectory()) {
      py.FS.mkdirTree(destino);
      copiar(ruta);
    } else {
      py.FS.writeFile(destino, readFileSync(ruta));
    }
  }
}
py.FS.mkdirTree("/home/pyodide/wire");
copiar(join(raiz, "wire"));
py.FS.writeFile("/tmp/diseno.json", readFileSync(diseno));

const version = py.runPython(`
import json, sys
sys.path.insert(0, "/home/pyodide")
from wire import planos
from wire.diseno import Diseno
d = Diseno.desde_json(open("/tmp/diseno.json", encoding="utf-8").read())
p = planos.generar(d, fecha="25-11-2026")
open("/tmp/descripcion.json", "w").write(json.dumps(planos.descripcion(p)))
open("/tmp/plano.pdf", "wb").write(planos.a_pdf(p))
import fpdf
f"{sys.version.split()[0]} fpdf2 {fpdf.__version__} PyNEC {'PyNEC' in sys.modules}"
`);
writeFileSync(salida + ".json", py.FS.readFile("/tmp/descripcion.json"));
writeFileSync(salida + ".pdf", py.FS.readFile("/tmp/plano.pdf"));
console.log(`Pyodide ${py.version} · Python ${version} · ${(Date.now() - t0) / 1000} s`);
