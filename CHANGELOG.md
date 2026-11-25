# Cambios

## Sin publicar

Primera versión pública prevista: **0.1.0-alpha** (cuando el usuario lo decida; ver `docs/PUBLICAR.md`).

- Modelo de hilos y líneas de transmisión, exportación y lectura de `.nec`, motor PyNEC y ajuste.
- Dipolo de media onda y J-pole de alambre (ajustada con el motor, segmentación convergida).
- Generador común de planos (descripción vectorial en mm → SVG y PDF), A4 con cajetín y detalles a 1:1.
- `diseno.json` con el bloque `plano`; línea de comandos `python -m wire`.
- CI: Windows con PyNEC, Linux con nec2c y generación del plano dentro de Pyodide.
- Identidad visual (grillo con antenas de coaxial y «Wire» en aluminio).
- Sin medir: todos los tipos son «Simulado» o «Sin validar».
