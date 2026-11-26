# Cambios

## Sin publicar

- Aisladores 3D (`wire/aisladores.py`, `python -m wire aisladores …`, botón en la pestaña Plano del escritorio): aislador central (con un agujero por hilo y lado, el del abanico lleva más, cuerda arriba y ranuras para bridas del coaxial) y de extremo, en un zip con los STL y un LÉEME. Para los dipolos de HF, el de V invertida, el abanico, las trampas, la G5RV, el dipolo y la V de VHF y la EFHW (solo extremo). Agujeros cuadrados del lado del alambre más una holgura; **sin probar en una impresora**. Aún no está en la web.

- Colineal (con bobinas y bibanda) **sobre suelo real**: casilla «Sobre suelo real» en la web y el escritorio (o `altura_m` y `suelo` en `disenar`); el ajuste sigue siendo en espacio libre y los resultados y la hoja son los del diseño ya sobre ese suelo. A 145 MHz con 3 secciones y la base a 5 m sobre suelo normal la ROE sigue en 1,0 pero la ganancia máxima baja de 4,8 a 2,6 dBi (a 10 m sobre suelo bueno, 3,7). Sin mástil ni cable de bajada.
- Vertical de HF (`vertical_hf`): radiador de λ/4 con 8 radiales horizontales elevados sobre suelo real, ajustada con PyNEC (7,1 MHz, 2 m de altura de radiales, suelo normal: R ≈ 45 Ω, ROE 1,1, ≈ 0 dBi por las pérdidas del suelo). Hoja con vista, lista de corte, tabla simulada y montaje con choke; en la galería de HF de la web y del escritorio. **Sin medir**; los radiales reales y el suelo del terreno cambian la impedancia. Sin bobina de carga todavía.
- Guía de cómo llevar y traer una antena entre Wire y Chirptenna VNA (README en castellano e inglés, y desplegable en la pestaña Medir del escritorio) y botón «Abrir cable medido» en Diseño para cargar el JSON del VF que descarga Chirptenna VNA. Los cuatro README de Chirptenna VNA llevan la sección equivalente.
- S11 simulado en Touchstone (`python -m wire s1p …` y botón en Simulación; `wire/touchstone.py`) para superponerlo a la medida en Chirptenna VNA, que ya carga `.s1p` como referencia y da la desviación de la resonancia (comprobado con su `leerTouchstone` y `compararConReferencia`).
- Diagrama de radiación en la pestaña Simulación del escritorio: cortes polares de azimut y elevación por el máximo (`motor.diagrama`, `graficas.svg_diagrama`), y vista 3D que se gira con el ratón (nube de puntos coloreada por ganancia con la antena dentro), como en Chirptenna.
- Interfaz de escritorio al día: galería por categorías con la ganancia teórica, campos propios de cada tipo (Yagi, colineal, bibanda, HF, EFHW) y botón de la plantilla de doblado 3D.
- Ganancia teórica de cada diseño (`wire/ganancias.json`): en el cajetín de los planos, en la galería y en la cabecera de la web, y tabla en el README.
- La colineal con bobinas de fase llega a 6 secciones (5 y 6: 6,2 y 6,7 dBi, para 433 MHz dentro de un tubo de PVC de 1,6 a 2,2 m).
- Colineal bibanda 145 / 433 MHz: bobinas con un condensador en serie (resonante en 145 MHz: no hacen nada) que en 433 MHz apilan 2 o 4 medias ondas (3,9 y 4,7 dBi en espacio libre; en 145 es un ¼ o 5/8 de onda). 50 Î© en las dos bandas. Sin medir.
- Colineal con bobinas de fase para VHF/UHF (2 a 4 secciones, la «de 2 / 5 dBi»): â‰ˆ 3, 4,8 y 5,5 dBi en espacio libre con 50 Î©, con hoja de la bobina y su ajuste con el NanoVNA. Sin medir.
- Trampas: esquema, trampa montada en su tubo y ajuste con el VNA (S21 con dos lazos) en la hoja de las trampas.
- Web: la galería es una pantalla de selección y los parámetros van en otra; el plano se rehace solo al cambiar un campo y los errores se ven; Yagi: eje y número de elementos validados.
- Más tipos de HF sobre suelo real: dipolo, V invertida, dipolo en abanico multibanda, dipolo con trampas y G5RV, con hoja del balun o choke 1:1 (y de las trampas), sin medir.
- Primer tipo de HF: EFHW con transformador 49:1, 64:1 o 9:1 sobre suelo real, con hojas de montaje y ajuste del transformador (valores de aficionados, sin verificar). El motor admite suelo real.
- La galería de la web se agrupa en categorías (HF, VHF y UHF, coaxial, banda ancha).
- Yagi de 3 a 15 elementos y eje metálico o no (corrección de corte de DL6WU, sin comprobar con medidas); hoja de elementos y eje cuando hay más de 3 o eje metálico.
- Plantilla de doblado para imprimir en 3D (STL en zip) de la J-pole y la J-pole de Koch, con radio de doblado y baldosas con encajes si pasa de la cama. Sin probar en una impresora.
- VF medido con Chirptenna VNA: `--cable-medido archivo.json` en la CLI y «cargar el archivo» en la web rellenan el VF del diseño (formato `chirptenna-cable`, `wire.cables.leer_cable_medido`).
- Tipos nuevos, sin medir: torniquete en X (dipolos cruzados con línea de 75 Î©, razón axial calculada con `motor.razon_axial_dB`) y batwing de alambre.
- Tipos nuevos, sin medir: ground plane (SO-239 o N), dipolo en V invertida, Yagi de 3 elementos y bicónica.
- Patrón del coaxial a 1:1 (tramo, punta y extremo de la manga) en los planos de la CoCo y las antenas de coaxial.
- El mosaico de A4 elige la orientación (vertical o apaisada) que da menos hojas.
- Tipos nuevos, **sin medir**: J-pole de Koch (plantilla 1:1 en A3 o mosaico de A4) y discone de varillas.
- Papel grande: A3 y mosaico de A4 con solape, marcas de registro, mapa de montaje y regla en cada hoja.
- `instalar.bat` para Windows y capturas en el README.
- Interfaz de escritorio (NiceGUI): `python gui/app.py` con Elegir, Diseño, Simulación, Plano y Medir.
- Medidas: `wire/medidas.py` lee `.s1p`, compara con la simulación y da el estado «Medido» con â‰¤ 2 %.
- Idiomas es/en/fr/de en planos, CLI, web y escritorio (`wire/i18n.py`, `herramientas/i18n.py`).
- Dipolo de manga y colineal CoCo de coaxial (sin medir; la CoCo, sin validar frente a un caso publicado).
- Web: galería con miniaturas, cable y VF medido, selector de idioma; prueba en un navegador real en la CI.

## 0.1.0-alpha (25-11-2026)

Primera versión pública.

- Modelo de hilos y líneas de transmisión, exportación y lectura de `.nec`, motor PyNEC y ajuste.
- Dipolo de media onda y J-pole de alambre (ajustada con el motor, segmentación convergida).
- Generador común de planos (descripción vectorial en mm â†’ SVG y PDF), A4 con cajetín y detalles a 1:1.
- `diseno.json` con el bloque `plano`; línea de comandos `python -m wire`.
- CI: Windows con PyNEC, Linux con nec2c y generación del plano dentro de Pyodide.
- Identidad visual (grillo con antenas de coaxial y «Wire» en aluminio).
- Sin medir: todos los tipos son «Simulado» o «Sin validar».
