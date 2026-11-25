# Chirptenna Wire · propuesta de alcance (25-11-2026)

Spin-off de [Chirptenna](https://github.com/sqtactical/chirptenna) para **antenas de varilla, tubo e hilo** (J-pole,
ground plane, dipolo, discone, Yagi): da el **plano de construcción** (cotas, lista de corte, materiales y montaje) para
una frecuencia, con la simulación que lo respalda. Tiene su propio repositorio, como Chirptenna VNA, porque cambian el
usuario, el motor y la salida. Este documento es la propuesta: no hay nada hecho todavía. Las rutas que se citan
(`antenas/hilos.py`, `pruebas/test_verdad.py`) son del repositorio de Chirptenna.

## 1. Para quién y para qué

- **Usuario**: radioaficionado o maker que construye su antena con material de ferretería (varilla de latón o de
  aluminio, tubo de cobre, hilo, varillas de soldar, cinta métrica) y no va a diseñar una PCB.
- **Problema**: las calculadoras que hay dan dos o tres longitudes con fórmulas fijas, sin tener en cuenta el diámetro
  del material ni el conector, y sin decir cuánto se mueve la frecuencia al recortar.
- **Qué aporta Chirptenna Wire**:
  - un plano acotado que se puede imprimir;
  - la longitud calculada con el diámetro real (método de momentos, no una fórmula);
  - un margen de recorte con «cortar X mm sube Y MHz»;
  - la curva de ROE y el diagrama simulados;
  - el paso a Chirptenna VNA para medirla y ajustarla.

## 2. Alcance de la primera versión

**Tipos** (los cinco clásicos; ningún tipo más hasta medir al menos dos):

| Tipo | Por qué | Detalle del plano |
|---|---|---|
| Ground plane de 1/4 de onda | La más construida; referencia para validar el motor | Radiador, 3–4 radiales con su ángulo (0–45°) y conector SO-239/N |
| Dipolo de 1/2 onda | Teoría conocida; segunda referencia | Brazos, hueco central y choke de coaxial (número de vueltas y diámetro) |
| J-pole | Pedida; sin radiales; muy popular en 2 m y 70 cm | Brazo largo, brazo corto, separación y punto de toma, con margen para mover la toma |
| Discone | Pedida; banda ancha para escáner y SDR | Disco y cono modelados con varillas (8–16), ángulo del cono y frecuencia mínima |
| Yagi de varillas | Más ganancia; plantilla de taladrado del boom | Elementos, separaciones, boom (madera o PVC; metálico con corrección) y alimentación |

**Bandas iniciales**: 2 m (144–146 MHz), 70 cm (430–440 MHz), PMR446, banda marina VHF, banda aérea (118–137 MHz),
LoRa 868/915 MHz y ADS-B 1090 MHz. **Fuera de la primera versión**: HF (las longitudes y los planos de masa cambian
el problema), quad, log-periódica, hélice, Moxon de hilo y antenas activas.

**Entradas**:
- frecuencia o banda;
- material: diámetro de la varilla o del tubo, o un predefinido como «varilla de soldar de 2,4 mm» o «tubo de cobre de 15 mm»;
- conector;
- montaje (mástil metálico o no, altura aproximada);
- unidades en mm o en pulgadas.

**Salidas**:
1. **Plano acotado** en SVG y PDF (A4/Carta): vista general, detalle de la alimentación y tabla de cotas. A escala 1:1
   cuando cabe (plantilla de taladrado del boom de la Yagi, detalle de la toma de la J-pole).
2. **Lista de corte**: cada pieza con su longitud final y la longitud para cortar (con sobrante para ajustar), y la
   sensibilidad (MHz por mm).
3. **Lista de materiales** y guía de montaje paso a paso.
4. **Resultados simulados**: ROE/S11 en la banda, impedancia, ganancia y diagrama, con el aviso de lo que no se modela.
5. **`diseno.json`** para reabrir el diseño y un enlace a Chirptenna VNA con la frecuencia y la banda ya puestas
   (`?f=&banda=&nombre=`, el mismo contrato que usa Chirptenna).

## 3. Motor de cálculo

Para hilos y varillas en el aire lo adecuado es el **método de momentos de hilo fino (NEC2)**, no la FDTD de openEMS:
una J-pole o una ground plane se resuelve en milisegundos y cabe en el navegador. Opciones, por orden de preferencia:

1. **nec2c (C, dominio público) compilado a WebAssembly** con Emscripten. Es el estándar de facto: lo que calcula es
   comparable con 4nec2, EZNEC y xnec2c, que usan los radioaficionados. Riesgo: hay que montar y mantener la compilación;
   comprobar antes si ya existe una compilación a WASM mantenida y con licencia compatible.
2. **Motor propio en numpy bajo Pyodide**, ampliando `antenas/hilos.py` de Chirptenna. Hoy solo admite hilos paralelos
   al eje z, sin uniones ni plano de masa. Haría falta: segmentos en 3D, uniones de varios hilos, plano de masa por
   imágenes, cargas concentradas y pérdidas del conductor. Es más trabajo y menos contrastable que NEC2. Sirve de
   respaldo o de segundo motor para comparar.

En cualquier caso, la CI compara contra **nec2c de escritorio** y contra la teoría (dipolo λ/2: resonancia a ~0,47–0,48 λ
y R ≈ 70–73 Ω; ground plane con radiales a 45°: R ≈ 50 Ω), igual que `pruebas/test_verdad.py` en Chirptenna.

**Límites que hay que decir en la interfaz**:
- hilo fino: el radio debe ser mucho menor que λ, así que un tubo de 15 mm a 1090 MHz ya está al límite;
- la discone es una rejilla de varillas, no superficies continuas;
- no se modelan las corrientes por la malla del coaxial (el choke se recomienda, no se simula);
- el mástil y el suelo solo se tienen en cuenta si se modelan;
- el contacto entre tramos telescópicos o tornillos no es ideal.

## 4. Arquitectura

- **Solo web** (GitHub Pages), sin instalador: núcleo en Python, que corre con Pyodide (el mismo patrón que la web lite
  de Chirptenna), o en JS si el motor final es nec2c en WASM. Se puede usar sin conexión una vez cargada.
- El núcleo también se usa por línea de comandos, para la CI y para generar tablas.
- **Idiomas**: el mismo esquema de Chirptenna (el castellano como texto fuente y clave; `en`, `fr` y `de`; la
  herramienta `faltan` en la CI).
- **Licencias**: el código con AGPL-3.0 y los diseños publicados con CC BY-NC 4.0, como Chirptenna.
- **Relación con los otros proyectos**: se copian las piezas (catálogos de idioma, estilo de la web), no se depende de
  Chirptenna como librería. Enlaces cruzados: desde Chirptenna, «¿la quieres de varilla?», y desde las dos herramientas
  a Chirptenna VNA para medir.

## 5. Validación (antes de ampliar)

- **v0.1**: ground plane y dipolo; el motor coincide con nec2c a ≤ 0,5 % en la resonancia y con la teoría.
- **Medir antes de la v0.2**: una ground plane de 868 MHz y una J-pole de 2 m o 70 cm, construidas con el plano y medidas
  con el NanoVNA. Criterio: resonancia a ≤ 2 % de la simulada. Si no se cumple, se corrige el modelo antes de añadir
  tipos (la lección de Chirptenna: no ampliar antes de medir).
- Cada tipo con un estado honesto en la interfaz: «Simulado», «Medido» o «Sin validar».

## 6. Hitos

| Versión | Contenido | Hecho cuando |
|---|---|---|
| v0.1 | Motor (decisión nec2c-WASM o propio), ground plane y dipolo, plano SVG, ROE simulada, web publicada | Coincide con nec2c y la teoría; plano imprimible a escala |
| v0.2 | J-pole y Yagi, PDF, lista de corte con sensibilidad, plantilla de taladrado, idiomas | Dos antenas construidas y medidas a ≤ 2 % |
| v0.3 | Discone, montaje (mástil, altura), enlace con Chirptenna VNA | Discone medida en su banda |

## 7. Riesgos

- **Motor**: si no hay una compilación de nec2c a WASM mantenida, la v0.1 se alarga (hay que hacerla o escribir el motor).
- **Discone**: la rejilla de varillas da bien la impedancia pero la frecuencia mínima depende del número de varillas; hay
  que validar contra medida.
- **J-pole**: la adaptación depende mucho del punto de toma, así que el plano debe dar margen y el método para buscarla
  con el NanoVNA.
- **Material**: diámetros reales distintos de los nominales; aluminio frente a cobre (pérdidas); tornillería.
- **Mantenimiento**: sería el tercer proyecto. Arrancar pequeño y medir pronto.

## 8. Decisiones del usuario

1. **Motor**: nec2c en WebAssembly (recomendado si existe o se compila sin problemas) o motor propio.
2. **Solo web**, o también un modo de escritorio (no hace falta: NEC2 es ligero).
3. **Repositorio público desde el principio**, o privado hasta la v0.1.
4. **Unidades**: mm por defecto con conmutador a pulgadas.
5. **Primera antena que se construirá y medirá**: propuesta, una ground plane de 868 MHz (la más fácil de construir y
   de medir con el NanoVNA).
