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
- [ ] W2.4 Dipolo de manga de coaxial (sleeve)
- [ ] W2.5 Colineal CoCo
- [ ] W2.6 Hojas de planos: pelado y cruces a 1:1, tramos sin escala
- [ ] W2.7 **Usuario delante**: medir el VF de su cable y una CoCo construida con el plano

## Fase 3 · Interfaz de escritorio

- [ ] W3.1 Esqueleto NiceGUI con pestañas Elegir, Diseño, Simulación, Plano, Medir
- [ ] W3.2 Vista previa del plano en SVG y descargas (PDF, SVG, `.nec`, `diseno.json`)
- [ ] W3.3 Idiomas (es, en, fr, de) con el esquema de Chirptenna
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
