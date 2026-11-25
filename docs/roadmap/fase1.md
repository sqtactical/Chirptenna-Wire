# Fase 1 · J-pole y planos

Objetivo: la primera antena útil de principio a fin (J-pole de alambre: diseño → simulación → plano A4 → construir →
medir) y el generador de planos que usarán todos los tipos. Empezó el 25-11-2026; parte del código ya existe
(`wire/ajuste.py`, `wire/diseno.py`, `wire/planos/`, `python -m wire`). **Si una tarea ya está hecha, compruébala con
su «Hecho cuando» y márcala; no la rehagas.**

## W1.1 · fpdf2 en Pyodide
- **Quién**: Agente. **Depende de**: nada.
- **Archivos**: `wire/planos/pdf.py`, `docs/PLANOS.md`.
- **Pasos**: 1) Carga Pyodide (versión fijada, la misma que use la web: Chirptenna usa 0.29.3) en Node o en Edge sin
  ventana; 2) `micropip.install('fpdf2')`; 3) genera con `wire.planos.pdf.a_pdf` un plano del dipolo dentro de Pyodide;
  4) compara su tamaño de página y la posición de la regla con el PDF de escritorio.
- **Hecho cuando**: el PDF de Pyodide abre, mide A4 y la regla está en las mismas coordenadas que en escritorio; o, si
  fpdf2 no carga, `docs/PLANOS.md` dice qué alternativa se usa y por qué.
- **Trampas**: las fuentes TTF (`wire/planos/recursos/`) hay que cargarlas desde bytes, no por ruta del disco.

## W1.2 · J-pole de alambre
- **Quién**: Agente. **Depende de**: nada.
- **Archivos**: `wire/generadores.py` (`jpole`, `jpole_por_defecto`), `wire/ajuste.py` (`ajustar_jpole`), pruebas.
- **Pasos**: 1) geometría: rama larga (radiador λ/2 + adaptador λ/4), rama corta (λ/4), U del fondo, separación S y toma
  a altura h; 2) fuente en un puente horizontal entre las ramas a la altura h (ver `nec2.md` §3); 3) ajuste en dos
  variables (largo del radiador y altura de la toma) minimizando la ROE a 50 Ω en la frecuencia objetivo (Nelder-Mead
  ya está en `ajuste.py`); 4) segmentos alineados en las dos ramas.
- **Pruebas**: 145 MHz y 435 MHz con alambre de 2 mm: S11 ≤ −15 dB en el centro, ganancia 1,5–3 dBi; convergencia con
  N y 2N segmentos (resonancia ±0,2 %).
- **Hecho cuando**: las pruebas pasan y `docs/ejemplos/jpole_145.*` se regeneran con el ajuste.
- **Trampas**: si la ROE mínima no baja de 2, la toma está fuera del rango buscado o los segmentos de las ramas no están
  alineados.

## W1.3 · Generador de planos común
- **Quién**: Agente. **Depende de**: W1.1 (para saber qué PDF usar).
- **Archivos**: `wire/planos/hoja.py` (primitivas: `Linea`, `Polilinea`, `Rect`, `Circulo`, `Arco`, `Texto`, `Imagen`,
  `Cota`, `Hoja`, `Plano`), `svg.py` (`a_svg`), `pdf.py` (`a_pdf`), `comun.py` (cajetín, regla, tabla, gráfica de ROE).
- **Pasos**: todo en mm del papel con el origen abajo a la izquierda; las salidas SVG y PDF solo traducen primitivas; los
  textos con anchura calculada (`ancho_texto`) para poder comprobar solapes.
- **Hecho cuando**: el mismo `Plano` da un SVG y un PDF que se ven iguales; `descripcion(plano)` (lista de dicts) es
  idéntica con y sin PyNEC instalado.
- **Trampas**: nada de matplotlib aquí; la imagen del logo va como SVG o PNG embebido desde `recursos/`.

## W1.4 · Hojas del dipolo y de la J-pole
- **Quién**: Agente. **Depende de**: W1.2, W1.3.
- **Archivos**: `wire/planos/dipolo.py`, `wire/planos/jpole.py`; referencia: `docs/maquetas/` (formato aprobado).
- **Pasos**: seguir las maquetas: vista general sin escala con cotas, lista de corte (final y «cortar a» con sobrante),
  sensibilidad (MHz por mm), resultados simulados con la gráfica de ROE, detalle 1:1 (centro del dipolo; adaptador, U y
  toma de la J-pole), regla y cajetín. Corregir lo que anota `docs/maquetas/LEEME.md` (cota que corta el brazo).
- **Hecho cuando**: los PDF de `docs/ejemplos/` se parecen a las maquetas; impresos al 100 %, la regla y el detalle miden
  lo que dicen (compruébalo en las coordenadas del PDF).

## W1.5 · `diseno.json`
- **Quién**: Agente. **Depende de**: W1.2.
- **Archivos**: `wire/diseno.py` (`Diseno`, `ConfigPlano`, `disenar`).
- **Pasos**: tipo, frecuencia, material, parámetros ajustados, resultados simulados y el bloque `plano` (claves de
  `docs/PLANOS.md` §6); `Diseno.desde_json` lee lo que escribe `a_json` (o como se llame: búscalo).
- **Hecho cuando**: ida y vuelta JSON sin pérdidas (prueba) y un plano generado desde el JSON es igual al original.

## W1.6 · Línea de comandos
- **Quién**: Agente. **Depende de**: W1.4, W1.5.
- **Archivos**: `wire/__main__.py`.
- **Hecho cuando**: `python -m wire plano jpole 145 --diametro 2 --salida x.pdf`, `--desde diseno.json` y `nec …`
  funcionan y tienen `--help` en castellano.

## W1.7 · Pruebas de planos
- **Quién**: Agente. **Depende de**: W1.4.
- **Pruebas a escribir**: la regla mide lo que dice; las vistas 1:1 coinciden con la geometría del modelo (± 0,05 mm);
  ningún texto se sale del área útil ni pisa el cajetín (`hoja.se_solapan`, `hoja.dentro`); la descripción vectorial es
  la misma con y sin PyNEC.
- **Hecho cuando**: las pruebas están en `pruebas/` y pasan en la CI.

## W1.8 · Medir una J-pole construida con el plano
- **Quién**: **Usuario delante**. **Depende de**: W1.4.
- **Pasos**: 1) el usuario elige la banda (2 m o 70 cm) y el alambre; 2) genera el plano, lo imprime al 100 % y comprueba
  la regla; 3) construye; 4) mide con el NanoVNA (Chirptenna VNA o `vna/medir_antena_pc.py` de Chirptenna) lejos de
  metales; 5) guarda la medida (`.s1p`) en `docs/medidas/` con fecha; 6) compara resonancia y ROE con la simulada.
- **Hecho cuando**: la resonancia medida está a ≤ 2 % de la simulada, o la diferencia tiene causa (cable sin choke,
  medida, material) apuntada en `docs/medidas/`. Entonces el estado del tipo puede pasar a «Medido».
