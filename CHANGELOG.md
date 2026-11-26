# Cambios

## Sin publicar

- Diagrama de radiaciÃ³n en la pestaÃ±a SimulaciÃ³n del escritorio: cortes polares de azimut y elevaciÃ³n por el mÃ¡ximo (`motor.diagrama`, `graficas.svg_diagrama`), y vista 3D que se gira con el ratón (nube de puntos coloreada por ganancia con la antena dentro), como en Chirptenna.
- Interfaz de escritorio al dÃ­a: galerÃ­a por categorÃ­as con la ganancia teÃ³rica, campos propios de cada tipo (Yagi, colineal, bibanda, HF, EFHW) y botÃ³n de la plantilla de doblado 3D.
- Ganancia teÃ³rica de cada diseÃ±o (`wire/ganancias.json`): en el cajetÃ­n de los planos, en la galerÃ­a y en la cabecera de la web, y tabla en el README.
- La colineal con bobinas de fase llega a 6 secciones (5 y 6: 6,2 y 6,7 dBi, para 433 MHz dentro de un tubo de PVC de 1,6 a 2,2 m).
- Colineal bibanda 145 / 433 MHz: bobinas con un condensador en serie (resonante en 145 MHz: no hacen nada) que en 433 MHz apilan 2 o 4 medias ondas (3,9 y 4,7 dBi en espacio libre; en 145 es un Â¼ o 5/8 de onda). 50 Î© en las dos bandas. Sin medir.
- Colineal con bobinas de fase para VHF/UHF (2 a 4 secciones, la Â«de 2 / 5 dBiÂ»): â‰ˆ 3, 4,8 y 5,5 dBi en espacio libre con 50 Î©, con hoja de la bobina y su ajuste con el NanoVNA. Sin medir.
- Trampas: esquema, trampa montada en su tubo y ajuste con el VNA (S21 con dos lazos) en la hoja de las trampas.
- Web: la galerÃ­a es una pantalla de selecciÃ³n y los parÃ¡metros van en otra; el plano se rehace solo al cambiar un campo y los errores se ven; Yagi: eje y nÃºmero de elementos validados.
- MÃ¡s tipos de HF sobre suelo real: dipolo, V invertida, dipolo en abanico multibanda, dipolo con trampas y G5RV, con hoja del balun o choke 1:1 (y de las trampas), sin medir.
- Primer tipo de HF: EFHW con transformador 49:1, 64:1 o 9:1 sobre suelo real, con hojas de montaje y ajuste del transformador (valores de aficionados, sin verificar). El motor admite suelo real.
- La galerÃ­a de la web se agrupa en categorÃ­as (HF, VHF y UHF, coaxial, banda ancha).
- Yagi de 3 a 15 elementos y eje metÃ¡lico o no (correcciÃ³n de corte de DL6WU, sin comprobar con medidas); hoja de elementos y eje cuando hay mÃ¡s de 3 o eje metÃ¡lico.
- Plantilla de doblado para imprimir en 3D (STL en zip) de la J-pole y la J-pole de Koch, con radio de doblado y baldosas con encajes si pasa de la cama. Sin probar en una impresora.
- VF medido con Chirptenna VNA: `--cable-medido archivo.json` en la CLI y Â«cargar el archivoÂ» en la web rellenan el VF del diseÃ±o (formato `chirptenna-cable`, `wire.cables.leer_cable_medido`).
- Tipos nuevos, sin medir: torniquete en X (dipolos cruzados con lÃ­nea de 75 Î©, razÃ³n axial calculada con `motor.razon_axial_dB`) y batwing de alambre.
- Tipos nuevos, sin medir: ground plane (SO-239 o N), dipolo en V invertida, Yagi de 3 elementos y bicÃ³nica.
- PatrÃ³n del coaxial a 1:1 (tramo, punta y extremo de la manga) en los planos de la CoCo y las antenas de coaxial.
- El mosaico de A4 elige la orientaciÃ³n (vertical o apaisada) que da menos hojas.
- Tipos nuevos, **sin medir**: J-pole de Koch (plantilla 1:1 en A3 o mosaico de A4) y discone de varillas.
- Papel grande: A3 y mosaico de A4 con solape, marcas de registro, mapa de montaje y regla en cada hoja.
- `instalar.bat` para Windows y capturas en el README.
- Interfaz de escritorio (NiceGUI): `python gui/app.py` con Elegir, DiseÃ±o, SimulaciÃ³n, Plano y Medir.
- Medidas: `wire/medidas.py` lee `.s1p`, compara con la simulaciÃ³n y da el estado Â«MedidoÂ» con â‰¤ 2 %.
- Idiomas es/en/fr/de en planos, CLI, web y escritorio (`wire/i18n.py`, `herramientas/i18n.py`).
- Dipolo de manga y colineal CoCo de coaxial (sin medir; la CoCo, sin validar frente a un caso publicado).
- Web: galerÃ­a con miniaturas, cable y VF medido, selector de idioma; prueba en un navegador real en la CI.

## 0.1.0-alpha (25-11-2026)

Primera versiÃ³n pÃºblica.

- Modelo de hilos y lÃ­neas de transmisiÃ³n, exportaciÃ³n y lectura de `.nec`, motor PyNEC y ajuste.
- Dipolo de media onda y J-pole de alambre (ajustada con el motor, segmentaciÃ³n convergida).
- Generador comÃºn de planos (descripciÃ³n vectorial en mm â†’ SVG y PDF), A4 con cajetÃ­n y detalles a 1:1.
- `diseno.json` con el bloque `plano`; lÃ­nea de comandos `python -m wire`.
- CI: Windows con PyNEC, Linux con nec2c y generaciÃ³n del plano dentro de Pyodide.
- Identidad visual (grillo con antenas de coaxial y Â«WireÂ» en aluminio).
- Sin medir: todos los tipos son Â«SimuladoÂ» o Â«Sin validarÂ».
