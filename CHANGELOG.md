# Cambios

## Sin publicar

- Tipos nuevos, **sin medir**: J-pole de Koch (plantilla 1:1 en A3 o mosaico de A4) y discone de varillas.
- Papel grande: A3 y mosaico de A4 con solape, marcas de registro, mapa de montaje y regla en cada hoja.
- `instalar.bat` para Windows y capturas en el README.
- Interfaz de escritorio (NiceGUI): `python gui/app.py` con Elegir, Diseño, Simulación, Plano y Medir.
- Medidas: `wire/medidas.py` lee `.s1p`, compara con la simulación y da el estado «Medido» con ≤ 2 %.
- Idiomas es/en/fr/de en planos, CLI, web y escritorio (`wire/i18n.py`, `herramientas/i18n.py`).
- Dipolo de manga y colineal CoCo de coaxial (sin medir; la CoCo, sin validar frente a un caso publicado).
- Web: galería con miniaturas, cable y VF medido, selector de idioma; prueba en un navegador real en la CI.

## 0.1.0-alpha (25-11-2026)

Primera versión pública.

- Modelo de hilos y líneas de transmisión, exportación y lectura de `.nec`, motor PyNEC y ajuste.
- Dipolo de media onda y J-pole de alambre (ajustada con el motor, segmentación convergida).
- Generador común de planos (descripción vectorial en mm → SVG y PDF), A4 con cajetín y detalles a 1:1.
- `diseno.json` con el bloque `plano`; línea de comandos `python -m wire`.
- CI: Windows con PyNEC, Linux con nec2c y generación del plano dentro de Pyodide.
- Identidad visual (grillo con antenas de coaxial y «Wire» en aluminio).
- Sin medir: todos los tipos son «Simulado» o «Sin validar».
