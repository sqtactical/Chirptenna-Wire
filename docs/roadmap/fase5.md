# Fase 5 · Web lite

Objetivo: diseñar y descargar los planos en el navegador, sin instalar nada, con **el mismo núcleo** que el escritorio.
Modelo a copiar: la web lite de Chirptenna (`..\proyecto_generador_antenas\web\`, `antenas/web_api.py`,
`herramientas/construir_web.py`, `herramientas/prueba_web.py`, `.github/workflows/web.yml`), sin importar nada de allí.

## W5.1 · Núcleo en Pyodide
- **Quién**: Agente. **Depende de**: W1.1, W1.3.
- **Archivos**: `wire/web_api.py` (nuevo: funciones con JSON de entrada y salida: `catalogo`, `disenar`, `plano` →
  SVG por hoja y PDF en bytes), `herramientas/construir_web.py` (nuevo: empaqueta en un zip **solo** el núcleo y falla
  si se cuela algo que no carga en Pyodide, como PyNEC).
- **Pasos**: sin motor en el navegador, `disenar` usa las longitudes por defecto del generador (sin ajuste) o un
  resultado ya ajustado que venga en el `diseno.json`; el plano lo dice en el cajetín («sin simular en esta versión»).
- **Hecho cuando**: dentro de Pyodide se genera el plano de la J-pole y es idéntico (descripción vectorial) al de
  escritorio con los mismos parámetros.

## W5.2 · Interfaz web
- **Quién**: Agente. **Depende de**: W5.1.
- **Archivos**: `web/index.html`, `web/app.js`, `web/motor.js` (Web Worker con Pyodide), `web/idiomas/` (los mismos
  catálogos).
- **Pasos**: galería de tipos, parámetros, vista SVG por hoja, descargas (PDF, SVG, `.nec`, `diseno.json`), idiomas,
  tema claro/oscuro, aviso de imprimir al 100 %. Sin frameworks, como Chirptenna.
- **Hecho cuando**: funciona en Edge/Chrome y en móvil; abrir un `diseno.json` hecho en escritorio da el mismo plano.

## W5.3 · Simulación en el navegador (investigación)
- **Quién**: Agente para investigar; **decisión del usuario** para hacerlo. **Depende de**: W5.2.
- **Pasos**: buscar una compilación de nec2c a WebAssembly mantenida y con licencia compatible, o compilarla con
  Emscripten; medir el tiempo de un dipolo y de una J-pole; comparar resultados con PyNEC.
- **Hecho cuando**: hay un informe con opciones, coste y riesgos, y el usuario decide.

## W5.4 · Publicación y prueba en la CI
- **Quién**: Agente; publicar solo cuando el usuario lo diga. **Depende de**: W5.2.
- **Pasos**: flujo de GitHub Pages (publicación a mano o con cada versión), prueba con Playwright que genera el plano de
  cada tipo dentro del navegador y compara con escritorio.
- **Hecho cuando**: la prueba pasa en la CI y la web está publicada (si el usuario lo ha pedido).
- **Trampa conocida en Chirptenna**: el despliegue en Pages desde una etiqueta falla si el entorno solo acepta `main`;
  allí se publica con `gh workflow run web.yml --ref main`.
