# Planos de construcción · diseño (25-11-2026)

Decisiones del usuario (25-11): habrá **versión de escritorio y versión web lite**, y **las dos generan los planos con
el mismo código y la misma configuración**. Los planos son hojas **DIN A4 con cajetín de datos y el logo de Chirptenna
Wire**. Lo largo y recto (brazos del dipolo, tramos de la CoCo) se acota sin escala; lo doblado o complicado (J-pole de
Koch, adaptador de la J-pole, detalles de la alimentación) se imprime **a escala 1:1** y el propio papel sirve de
plantilla. Si una pieza a 1:1 no cabe en A4, se ofrece **A3** o **varias A4 que se unen**.

## 1. Arquitectura: un solo generador, dos salidas

- **Núcleo común en Python puro** (`wire/planos/`): sin PyNEC, sin matplotlib y sin nada que no corra en Pyodide (numpy
  sí). Lo usan igual el escritorio y la web lite, como `antenas/web_api.py` en Chirptenna.
- El generador no dibuja directamente: produce una **descripción vectorial de las hojas** (lista de páginas, cada una con
  líneas, polilíneas, arcos, textos, cotas e imágenes, en mm reales del papel). Dos salidas leen esa descripción:
  - **SVG**: para la vista previa en la interfaz (escritorio y web) y como descarga.
  - **PDF**: para imprimir. Opción preferida: **fpdf2** (Python puro, dibujo vectorial en mm; hay que comprobar que
    carga en Pyodide con micropip). Si no, el PDF lo hace el navegador a partir del SVG, pero entonces la escala 1:1
    depende de que el usuario no deje «ajustar a la página» en el diálogo de impresión (ver 5).
- **La configuración del plano** (papel, orientación, mosaico, unidades, idioma, solape) va en `diseno.json` dentro de
  un bloque `plano`, así que el mismo diseño da las mismas hojas en escritorio y en web.

## 2. Qué se dibuja y cómo

| Pieza | Cómo | Ejemplos |
|---|---|---|
| Elementos rectos largos | **Sin escala**, esquemáticos, con la longitud acotada (longitud final y longitud de corte con sobrante) | Brazos del dipolo, tramos de la CoCo, radiales, varillas de la discone, brazo largo de la J-pole |
| Formas dobladas o complicadas | **Escala 1:1**: plantilla para poner el alambre encima y doblarlo sobre el papel | J-pole de Koch, codos y separación de la J-pole, curvas |
| Detalles pequeños | **Escala 1:1** siempre que quepan | Dónde pelar el coaxial y cuánto, cruce vivo–malla de la CoCo, punto de toma, espaciador entre brazos |
| Plantillas de montaje | **Escala 1:1** | Ángulo del cono de la discone, pieza central (taladros), separación de radiales |

Cada vista lleva en su rótulo «Escala 1:1» o «Sin escala: medidas en mm», para que nunca se mida con regla un dibujo
esquemático.

## 3. Hojas y paginación

Orden por defecto: (1) hoja resumen con la vista general (sin escala), la **lista de corte** y la de materiales; (2) los
detalles a 1:1; (3) las plantillas grandes; (4) la guía de montaje paso a paso y los resultados simulados (ROE, Z,
diagrama, como imagen).

Para una plantilla a 1:1:
1. Si cabe en **A4** (área útil dentro del margen y sin el cajetín), en vertical o apaisada: una hoja.
2. Si no cabe, se ofrecen dos opciones (la elección se guarda en `plano`):
   - **A3**, si cabe ahí;
   - **mosaico de A4**: se trocea en hojas con un **solape** de 10 mm (configurable), **marcas de registro** en las
     esquinas y en los bordes, una cuadrícula de referencia y la etiqueta de cada hoja (A1, A2, B1… por fila y columna).
     La primera hoja del mosaico lleva un **mapa de montaje** (qué hoja va dónde). Una sola plantilla puede ocupar el
     mosaico; si mide más de ~4 × 3 hojas, se avisa de que es mejor acotarla sin escala.
3. Las piezas que no caben ni así (una CoCo de 2 m de largo) se acotan siempre sin escala.

## 4. Cajetín y logo

Cajetín en la esquina inferior derecha de cada hoja (estilo ISO 7200, simplificado), con:

- el **logo de Chirptenna Wire** (`img/grillo-wire.svg`, el icono del grillo con las antenas de coaxial, y el nombre);
- nombre del diseño y tipo de antena;
- frecuencia y banda; material (diámetro del alambre, cable y su factor de velocidad, «medido» o «de catálogo»);
- escala de la hoja («1:1», «Sin escala» o «Varias»);
- hoja n de m (y la etiqueta del mosaico si es una hoja de un mosaico);
- fecha, versión de Chirptenna Wire y estado del tipo («Simulado», «Medido», «Sin validar»);
- licencia de los diseños (CC BY-NC 4.0) y la URL del proyecto.

En la web y en el escritorio el cajetín es idéntico: sale del mismo generador.

## 5. Escala 1:1 al imprimir

Imprimir a escala real es lo que más falla con planos de este tipo. Por eso:

- toda hoja con algo a 1:1 lleva una **regla de comprobación** (un segmento de 100 mm y un cuadrado de 50 × 50 mm) con
  el texto «Mide esto: si no son 100 mm, imprime de nuevo al 100 % / “tamaño real”, sin ajustar a la página»;
- el PDF declara el tamaño de página exacto (A4 210 × 297 mm, A3 297 × 420 mm) y el contenido en mm reales;
- la interfaz recuerda, al descargar, que hay que imprimir al 100 %.

## 6. Configuración (`diseno.json` → `plano`)

| Clave | Valores | Por defecto |
|---|---|---|
| `papel` | `A4`, `A3` | `A4` |
| `grandes` | `A3`, `mosaico`, `sin_escala` (qué hacer con lo que no cabe en el papel elegido) | `mosaico` |
| `orientacion` | `auto`, `vertical`, `apaisada` | `auto` |
| `solape_mm` | 0–20 | 10 |
| `unidades` | `mm`, `pulgadas` (la escala 1:1 no cambia; solo las cotas) | `mm` |
| `idioma` | `es`, `en`, `fr`, `de` | el de la interfaz |
| `sobrante_mm` | margen de corte añadido en la lista de corte | según el tipo |

## 7. Pruebas

- Las mismas hojas en escritorio y en Pyodide: comparar la descripción vectorial (no los píxeles) para un caso de cada
  tipo.
- Escala: la regla de 100 mm del PDF mide 100 mm en las coordenadas del PDF; una plantilla a 1:1 tiene las mismas
  medidas que la geometría del modelo.
- Mosaico: la unión de las hojas, quitando el solape, reproduce la plantilla completa sin huecos ni duplicados.
- Que ningún texto ni cota se salga del área útil ni pise el cajetín.

## 8. En qué fase

- **Fase 1** (dipolo y J-pole): descripción vectorial, salida SVG y PDF, cajetín, hoja resumen con lista de corte,
  detalle 1:1 de la J-pole y regla de comprobación. Solo A4 de una hoja.
- **Fase 2** (coaxial): detalles 1:1 del pelado y del cruce de la CoCo; tramos sin escala.
- **Fase 4** (J-pole de Koch y discone): plantillas grandes, A3 y mosaico de A4.
- **Fase 5** (web lite): el mismo generador en Pyodide; comprobar fpdf2 allí lo antes posible (si no carga, decidir la
  alternativa antes de la fase 1 para no hacer el trabajo dos veces).
