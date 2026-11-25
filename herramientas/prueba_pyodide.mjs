// Genera un plano con el paquete `wire` dentro de Pyodide (como la web lite) y guarda la descripción vectorial y
// el PDF, para compararlos con los del escritorio (pruebas/test_pyodide.py).
//
//   node herramientas/prueba_pyodide.mjs <carpeta con node_modules/pyodide> <raíz del repo> <diseno.json> <salida>
//        [sin_comprimir]
//
// Escribe <salida>.json (descripción) y <salida>.pdf. Necesita red la primera vez (micropip baja fpdf2).
// Versión de Pyodide fijada: 0.29.3, la misma que la web de Chirptenna (npm install pyodide@0.29.3).
import { readFileSync, readdirSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { pathToFileURL } from "node:url";

const [modulos, raiz, diseno, salida, opcion] = process.argv.slice(2);
const comprimir = opcion === "sin_comprimir" ? "False" : "True";
const { loadPyodide } = await import(pathToFileURL(join(modulos, "node_modules", "pyodide", "pyodide.mjs")));

const t0 = Date.now();
const py = await loadPyodide();
// En Pyodide 0.29 hace falta `ssl` antes de importar fpdf2 (fpdf.image_parsing importa urllib.request.HTTPSHandler).
await py.loadPackage(["micropip", "ssl"]);
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

let version;
try {
  version = py.runPython(`
import json, sys
sys.path.insert(0, "/home/pyodide")
from wire import planos
from wire.diseno import Diseno
d = Diseno.desde_json(open("/tmp/diseno.json", encoding="utf-8").read())
p = planos.generar(d, fecha="25-11-2026")
open("/tmp/descripcion.json", "w").write(json.dumps(planos.descripcion(p)))
open("/tmp/plano.pdf", "wb").write(planos.a_pdf(p, comprimir=${comprimir}))
import fpdf
f"{sys.version.split()[0]} fpdf2 {fpdf.__version__} PyNEC {'PyNEC' in sys.modules}"
`);
} catch (e) {
  // El volcado de la pila de Node es larguísimo: solo el mensaje de Python.
  console.error("ERROR en Pyodide:", String(e.message).split("\n").slice(-6).join("\n"));
  process.exit(1);
}
writeFileSync(salida + ".json", py.FS.readFile("/tmp/descripcion.json"));
writeFileSync(salida + ".pdf", py.FS.readFile("/tmp/plano.pdf"));
console.log(`Pyodide ${py.version} · Python ${version} · ${(Date.now() - t0) / 1000} s`);
