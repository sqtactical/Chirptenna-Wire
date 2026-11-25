# Chirptenna Wire · hoja de ruta

Plan de trabajo por fases (escrito el 25-11-2026). Cada tarea (W1.1, W2.3…) está desarrollada en
`docs/roadmap/` con quién la hace, archivos, pasos, pruebas, criterio de «hecho» y trampas conocidas. **Quien ejecute
una tarea (persona o agente) lee antes [`docs/roadmap/00_como_trabajar.md`](docs/roadmap/00_como_trabajar.md).**
El porqué de cada decisión está en [`docs/PROPUESTA.md`](docs/PROPUESTA.md) y el de los planos en
[`docs/PLANOS.md`](docs/PLANOS.md). Al terminar una tarea, márcala (`[x]`) con la fecha.

| Guía | Contenido |
|---|---|
| [`00_como_trabajar.md`](docs/roadmap/00_como_trabajar.md) | **Leer primero**: entorno, comandos, reglas, «hecho», informe, cuándo parar y preguntar |
| [`nec2.md`](docs/roadmap/nec2.md) | Chuleta de modelado en NEC2: segmentos, uniones, fuente, suelo, líneas de transmisión, coaxial |
| [`fase1.md`](docs/roadmap/fase1.md) | W1: J-pole, generador de planos (SVG y PDF), `diseno.json`, línea de comandos, primera medida |
| [`fase2.md`](docs/roadmap/fase2.md) | W2: coaxial (malla + línea de transmisión, factor de velocidad), dipolo de manga, CoCo |
| [`fase3.md`](docs/roadmap/fase3.md) | W3: interfaz de escritorio (NiceGUI), idiomas, enlace con Chirptenna VNA |
| [`fase4.md`](docs/roadmap/fase4.md) | W4: J-pole de Koch, discone, A3 y mosaico de A4 |
| [`fase5.md`](docs/roadmap/fase5.md) | W5: web lite (Pyodide, GitHub Pages) |

## Fase 1 · J-pole y planos (en curso desde el 25-11)

- [x] W1.1 fpdf2 en Pyodide: comprobar o elegir alternativa — 25-11-2026 (Pyodide 0.29.3; requiere cargar `ssl`)
- [x] W1.2 J-pole de alambre en el motor, con ajuste de largo y toma — 25-11-2026 (3 × segmentos: converge)
- [x] W1.3 Generador de planos común (descripción vectorial → SVG y PDF), cajetín, regla, A4 — 25-11-2026
- [x] W1.4 Hojas del dipolo y de la J-pole según las maquetas aprobadas (`docs/maquetas/`) — 25-11-2026
- [x] W1.5 `diseno.json` con el bloque `plano` — 25-11-2026
- [x] W1.6 Línea de comandos `python -m wire` — 25-11-2026 (`--help` en castellano)
- [x] W1.7 Pruebas de escala, solapes y equivalencia con/sin PyNEC — 25-11-2026 (pasan en local y en la CI: Windows, Linux con nec2c y Pyodide)
- [ ] W1.8 **Usuario delante**: construir y medir una J-pole con el plano (≤ 2 % en f)

Salida: J-pole medida a ≤ 2 % de la simulada, o la causa identificada.

## Fase 2 · Coaxial

- [x] W2.1 Coaxial en el modelo: malla como hilo + interior como línea `TL` con VF — 25-11-2026 (`wire/coaxial.py`; un stub abierto de λ/4·VF da |Z| < 5 Ω y a λ/8 la reactancia teórica, ±25 %)
- [x] W2.2 Tabla de cables (RG-58, RG-174, RG-316, RG-213, LMR-400, Aircell 7…) y VF medido por el usuario — 25-11-2026 (`wire/cables.py`; **cifras típicas sin comprobar una a una contra la hoja de datos** (`verificado=False`); el VF medido sustituye al de catálogo y `Diseno.cable` guarda su origen)
- [x] W2.3 Cable de bajada y choke en el modelo — 25-11-2026 (`coaxial.dipolo_con_bajada`, `axial` o perpendicular; el choke es una carga de 2–10 kΩ: con ella la impedancia deja de depender del largo del cable, 1216 → 25–53 Ω en axial y 22 → 0,6 Ω en perpendicular; **una resistencia no devuelve la Z del dipolo aislado**, el cable extiende el brazo; `Carga.paralela` añade LD tipo 1)
- [ ] W2.4 Dipolo de manga de coaxial (sleeve) — **modelo hecho el 25-11-2026, faltan el plano (W2.6) y el ajuste fino**. La jaula de 4 hilos alrededor de la malla no converge (145 MHz: 30 − j29 Ω con λ/50 y 11 − j196 Ω con λ/100) y se descartó. Vale el **modelo B** (`coaxial.dipolo_manga`): radiador y manga del mismo radio (con radios distintos la R sube de 89 a 120 Ω al subir los segmentos: error de NEC2 en la unión) y el choke de la manga como reactancia de línea j·Z0·tan(2π·manga/λ) en un hilo corto; **solo de banda estrecha**. Resultados a 145 MHz con RG-58: resonancia 145,7 / 146,8 / 147,1 MHz con λ/50, λ/100 y λ/150, R ≈ 64 Ω, 1,7–1,8 dBi; con el choke el cable de 0,3 a 1,2 m mueve la impedancia menos de 20 Ω. La manga más gruesa que el vivo no está modelada; falta `ajustar_manga` y medir
- [ ] W2.5 Colineal CoCo — **validación del esquema hecha el 25-11-2026**: la ganancia del modelo con `TL` cruzadas coincide a 0,001 dB con la del mismo mazo sin líneas y con 1 V en fase en cada hueco (2, 4 y 6 tramos: 4,354 / 6,233 / 6,143 dBi), que es lo que da la teoría (una línea de λ/2 invierte la tensión y el cruce la vuelve a invertir); sin cruzar da 3,4 dBi con 2 tramos, así que la prueba distingue (`pruebas/test_coco.py`). Esto valida la topología y el signo, **no** las cifras absolutas: no hay caso publicado completo (la página de Cebik sobre la «curly collinear» es de bobina, no de coaxial; el artículo del IEEE no se pudo leer) ni 4nec2 ni medida. **Ajuste hecho el 25-11-2026 (`ajuste.ajustar_coco`), con un resultado incómodo**: tocar solo el largo de los tramos y de la punta baja la ROE (4,6 / 2,7 / 2,3 con 2 / 4 / 6 tramos) pero la ganancia deja de subir con los tramos (4,8 / 4,8 / 4,6 dBi), así que por defecto la geometría no se toca (tramos de λ/2·VF, punta de λ/4) y la adaptación va en una **red en L** en el conector (`red_adaptacion`, sin pérdidas, no cambia el diagrama): ROE 1,0 a 145 MHz con RG-58, ganancia 4,35 / 6,23 / 6,14 dBi. **Pero la ROE ≤ 2 solo dura 1,4–2,2 MHz (1–1,5 %)**: la impedancia del modelo en el conector es muy reactiva (260 + j286, 101 + j133, 162 + j156 Ω) y cambia rápido con la frecuencia. Una CoCo real suele tener más banda: puede ser una característica del modelo (sin pérdidas del cable, sin acoplo entre vivo y malla exterior) y habría que medirla. Tampoco es del todo «coherente»: de 4 a 6 tramos la ganancia no sube. **Sigue abierta** hasta contrastar con un caso externo o medir (W2.7). Estado en bruto: `coaxial.colineal_coco`. Mallas como hilos con un hilo de unión de un segmento entre tramos y el vivo de cada tramo como `TL` cruzada entre un hueco y el siguiente. Datos a 145 MHz con RG-58 (VF 0,66): ganancia máxima en el barrido 4,8 dBi (2 tramos), 6,5 (4), 6,7 (6), 8,3 (8); **no es limpio** (de 4 a 6 casi no sube y el máximo cae entre 147 y 160 MHz, no en 145), no converge del todo al duplicar los segmentos (±0,6 dB) y la ROE mínima es de 3,5 a 10 (sin adaptar). Como referencia, la bibliografía cita unos 9 dBi con 8 tramos (artículo del IEEE a 450 MHz) y 10,7 dB con 16 tramos (memoria de la RSRE con NEC), pero **no tengo un caso publicado con todos los datos para reproducirlo ni 4nec2 para contrastar**: falta eso antes de dar el modelo por bueno
- [x] W2.6 Hojas de planos: pelado y cruces a 1:1, tramos sin escala — 25-11-2026 (`wire/planos/coaxial.py`: manga en 1 hoja, CoCo en 2; el cajetín lleva cable y VF «de catálogo» o «medido»; `--cable` y `--vf-medido` en la CLI y selector de cable en la web; ejemplos `docs/ejemplos/manga_145.*` y `coco_145.*`; **las cotas del pelado y de la protección son orientativas y no se han construido ni medido**; la hoja de la CoCo no dibuja la red en L, solo da sus valores)
- [ ] W2.7 **Usuario delante**: medir el VF de su cable y una CoCo construida con el plano

## Fase 3 · Interfaz de escritorio

- [ ] W3.1 Esqueleto NiceGUI con pestañas Elegir, Diseño, Simulación, Plano, Medir
- [ ] W3.2 Vista previa del plano en SVG y descargas (PDF, SVG, `.nec`, `diseno.json`)
- [x] W3.3 Idiomas (es, en, fr, de) con el esquema de Chirptenna — 25-11-2026 (`wire/i18n.py` con `tr()`, catálogos `wire/idiomas/*.json`, extractor `herramientas/i18n.py faltan` que pasa `pruebas/test_idiomas.py` en la CI; planos, CLI `--idioma` y web; traducciones hechas por Claude, **a revisar por hablantes nativos**; falta la interfaz de escritorio, que aún no existe (W3.1))
- [ ] W3.4 Enlace con Chirptenna VNA (`?f=&banda=&nombre=`) y estado «Medido»
- [ ] W3.5 Instalación para usuarios (script o instrucciones) y README con capturas

## Fase 4 · Más tipos y papel grande

- [ ] W4.1 Geometría de Koch propia (copiada de Chirptenna, sin depender de él)
- [ ] W4.2 J-pole de Koch (radiador de Koch, ajuste, reglas de segmentación)
- [ ] W4.3 Paginación: A3 y mosaico de A4 con solape, registro y mapa
- [ ] W4.4 Discone (rejilla de varillas)
- [ ] W4.5 **Usuario delante**: medir la J-pole de Koch y la discone

## Fase 5 · Web lite

- [x] W5.1 Empaquetar el núcleo para Pyodide (sin PyNEC) y comprobar que genera los planos (`wire/web_api.py`, `herramientas/construir_web.py`, `pruebas/test_web.py`; 25-11-2026)
- [ ] W5.2 Interfaz web (galería, parámetros, vista SVG, descargas): primera versión hecha en `web/` (tipo, banda, parámetros, hojas SVG, PDF, SVG, `.nec`, `diseno.json`, abrir un `diseno.json` de escritorio, tema claro/oscuro; verificada en el navegador el 25-11-2026). Faltan idiomas, miniaturas en la galería y probar en móvil real
- [ ] W5.3 Simulación en el navegador: investigar nec2c en WebAssembly (decisión del usuario)
- [ ] W5.4 Publicación en GitHub Pages y prueba en navegador en la CI

## Siempre

- No añadir tipos sin medir los anteriores; estados honestos («Simulado», «Medido», «Sin validar»).
- No subir a GitHub ni hacer público el repositorio sin que el usuario lo diga.
