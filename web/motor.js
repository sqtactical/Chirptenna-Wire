// Motor de Chirptenna Wire web: Python (Pyodide) en un Web Worker para que la página no se congele.
// Recibe {id, fn, arg} y responde {id, ok, resultado | error}. fn: catalogo, disenar_json, plano_svg, plano_pdf, nec_texto.
// Chirptenna Wire · AGPL-3.0

// Pyodide 0.29.3, la misma versión que prueba la CI (pruebas/test_pyodide.py).
const PYODIDE = 'https://cdn.jsdelivr.net/pyodide/v0.29.3/full/';
importScripts(PYODIDE + 'pyodide.js');

let api = null;

function progreso(texto, fraccion) {
  postMessage({ progreso: texto, fraccion });
}

async function arrancar() {
  progreso('Cargando Python (Pyodide)…', 0.05);
  const py = await loadPyodide({ indexURL: PYODIDE });
  // En Pyodide 0.29 hace falta `ssl` antes de importar fpdf2.
  progreso('Cargando fpdf2 (PDF)…', 0.4);
  await py.loadPackage(['micropip', 'ssl']);
  await py.runPythonAsync("import micropip\nawait micropip.install('fpdf2')");
  progreso('Cargando el generador de planos…', 0.8);
  const zip = await (await fetch('py/wire.zip', { cache: 'no-cache' })).arrayBuffer();
  py.unpackArchive(zip, 'zip', { extractDir: '/home/pyodide' });
  progreso('Preparando…', 0.95);
  py.runPython("import sys\nsys.path.insert(0, '/home/pyodide')");
  api = py.pyimport('wire.web_api');
  return py;
}

const listo = arrancar().then(
  () => postMessage({ listo: true }),
  (e) => { postMessage({ fallo: String(e) }); throw e; });

onmessage = async (ev) => {
  const { id, fn, arg } = ev.data;
  try {
    await listo;
    const r = fn === 'catalogo' ? api.catalogo(arg) : api[fn](arg);
    if (fn === 'plano_pdf') {
      const bytes = r.toJs();
      r.destroy();
      postMessage({ id, ok: true, resultado: bytes }, [bytes.buffer]);
    } else {
      postMessage({ id, ok: true, resultado: fn === 'catalogo' || fn === 'plano_svg' ? JSON.parse(r) : r });
    }
  } catch (e) {
    postMessage({ id, ok: false, error: String(e.message || e).split('\n').slice(-3).join('\n') });
  }
};
