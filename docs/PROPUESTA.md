# Chirptenna Wire · propuesta de alcance (25-11-2026, revisada)

Spin-off de [Chirptenna](https://github.com/sqtactical/chirptenna) para **antenas de alambre, varilla y coaxial**: da el
**plano de construcción** (cotas, lista de corte, materiales y montaje) para una frecuencia, con la **simulación** que lo
respalda. Tiene su propio repositorio, como Chirptenna VNA, porque cambian el usuario, el motor y la salida. Las rutas
que se citan (`antenas/hilos.py`, `antenas/geometria.py`, `vna/medir_latiguillo.py`, `pruebas/test_verdad.py`) son del
repositorio de Chirptenna.

**Cambios respecto a la primera versión (25-11)**: entran las antenas de **coaxial** (dipolo de coaxial y colineal
CoCo) y la **J-pole de Koch**; la simulación es parte central del producto, así que el motor va **primero en escritorio**
(PyNEC) y la web después; el primer paso es **exportar a `.nec`**; se añade la **identidad visual** (apartado 9).

## 1. Para quién y para qué

- **Usuario**: radioaficionado o maker que construye su antena con material de ferretería (alambre, varilla de latón o
  de aluminio, tubo de cobre, cable coaxial) y no va a diseñar una PCB.
- **Problema**: las calculadoras que hay dan dos o tres longitudes con fórmulas fijas, sin tener en cuenta el diámetro
  del material, el factor de velocidad del cable que tiene el usuario ni cuánto se mueve la frecuencia al recortar.
- **Qué aporta Chirptenna Wire**:
  - un plano acotado que se puede imprimir;
  - longitudes calculadas con el diámetro real y, en las de coaxial, con el **factor de velocidad medido** del cable;
  - un margen de recorte con «cortar X mm sube Y MHz»;
  - la curva de ROE, la impedancia y el diagrama simulados;
  - el `.nec` del diseño, para abrirlo en 4nec2 o xnec2c;
  - el paso a Chirptenna VNA para medirla y ajustarla.

## 2. Tipos

| Orden | Tipo | Material | Por qué en ese orden | Detalle del plano |
|---|---|---|---|---|
| 1 | Dipolo de 1/2 onda | alambre o varilla | Valida el motor contra la teoría | Brazos, hueco central, choke de coaxial (vueltas y diámetro) |
| 2 | J-pole | alambre o varilla | La más pedida; se mide fácil | Brazo largo, brazo corto, separación y punto de toma, con margen para moverla |
| 3 | Dipolo de coaxial | coaxial | Primera prueba de malla + línea de transmisión | Dónde se pela, largo de cada mitad, choke |
| 4 | Colineal CoCo | coaxial | Depende del factor de velocidad: se valida con un cable medido | Tramos, cruces vivo–malla, tramo final y choke |
| 5 | J-pole de Koch | alambre | Reutiliza la curva de Koch de Chirptenna (`antenas/geometria.py`) | Plantilla 1:1 para doblar el alambre |
| 6 | Discone | varillas | Banda ancha; la más difícil de validar | Disco y cono con 8–16 varillas, ángulo del cono y frecuencia mínima |

Después, si los anteriores se han medido: ground plane de 1/4 de onda con radiales y Yagi de varillas (plantilla de
taladrado del boom).

**Bandas iniciales**: 2 m (144–146 MHz), 70 cm (430–440 MHz), PMR446, banda marina VHF, banda aérea (118–137 MHz),
LoRa 868/915 MHz y ADS-B 1090 MHz. **Fuera**: HF, quad, log-periódica, hélice, Moxon de hilo y antenas activas.

**Entradas**: frecuencia o banda; material (diámetro del alambre o la varilla, o un predefinido); en las de coaxial, el
cable (RG-58, RG-213, LMR-400, Aircell 7… con su VF de catálogo, o el VF medido); conector; montaje (mástil metálico o
no, altura aproximada); unidades en mm o en pulgadas.

**Salidas**:
1. **Plano acotado** en SVG y PDF (A4/Carta), con detalle de la alimentación y tabla de cotas; a escala 1:1 cuando cabe.
2. **Lista de corte** con la longitud final, la de cortar (con sobrante) y la sensibilidad (MHz por mm).
3. **Lista de materiales** y guía de montaje paso a paso.
4. **Resultados simulados**: ROE/S11, impedancia, ganancia y diagrama, con el aviso de lo que no se modela.
5. **`.nec`** del modelo, **`diseno.json`** para reabrirlo y un enlace a Chirptenna VNA con la frecuencia y la banda
   puestas (`?f=&banda=&nombre=`, el contrato que ya usa Chirptenna).

## 3. Cómo se modela

Todo son **hilos con radio** y **líneas de transmisión**, que es lo que resuelve NEC2 (método de momentos de hilo fino):

- **Alambre y varilla**: segmentos de hilo con su radio. Las curvas de Koch son hilos doblados; la discone es una rejilla
  de varillas.
- **Coaxial**: la cara exterior de la malla radia y es un hilo con el radio de la malla; el interior es una línea de
  transmisión (tarjeta `TL`) de la impedancia del cable, con longitud eléctrica = longitud física / VF. Los cruces de la
  CoCo son líneas que unen el vivo de un tramo con la malla del siguiente. Así se modela la CoCo en 4nec2.
- **Factor de velocidad**: es lo que más pesa en la CoCo (0,66 en PE macizo, ~0,82–0,85 en espumado). Se puede medir
  con `vna/medir_latiguillo.py` de Chirptenna (o un asistente equivalente en Chirptenna VNA): el plano sale con el VF real.
- **Cable de bajada**: en la CoCo y el dipolo de coaxial, la malla del cable que baja al equipo también radia (modo
  común). Se añade como un hilo más hasta el choke, y el plano incluye el choke.

**Límites que hay que decir en la interfaz**: hilo fino (radio ≪ λ: un tubo de 15 mm a 1090 MHz ya está al límite);
las líneas `TL` de NEC2 no tienen pérdidas (en una CoCo larga hay que estimarlas aparte); en la J-pole de Koch los
segmentos deben ser cortos frente a λ pero varias veces más largos que el radio del alambre, lo que limita la iteración;
el mástil y el suelo solo cuentan si se modelan; los contactos y soldaduras no son ideales.

## 4. Motor y arquitectura

Por capas, para que haya algo útil desde el principio:

1. **Núcleo en Python**: modelo de hilos (puntos, radio, uniones, líneas de transmisión, puerto, cargas) y generadores
   de cada tipo. Sin dependencias pesadas; también por línea de comandos.
2. **Exportador `.nec`** (tarjetas GW, GE, GN, EX, TL, LD, FR, RP): el usuario puede simular en 4nec2 o xnec2c desde el
   primer día, y sirve para contrastar nuestro motor.
3. **Motor en escritorio con PyNEC** (interfaz de Python de necpp, que deriva de NEC2): ROE, impedancia, ganancia y
   diagrama en milisegundos. **Comprobar en la fase 0 que PyNEC instala en Windows con el Python que se use** (si no,
   nec2c compilado como ejecutable y leyendo su salida).
4. **Interfaz de escritorio** con NiceGUI, como Chirptenna (mismo esquema de pestañas: elegir, diseño, simulación,
   plano, medir).
5. **Web lite después** (decidido el 25-11: habrá escritorio y web lite): como mínimo, diseño y planos en el navegador
   con el mismo núcleo en Pyodide; la simulación en la web (nec2c en WebAssembly) se decide cuando el escritorio
   funcione. **Los planos (A4 con cajetín y logo, 1:1 para lo doblado, A3 o mosaico de A4 para lo grande) salen del mismo
   generador en las dos versiones: diseño en [`PLANOS.md`](PLANOS.md).** Por eso el núcleo (modelo, generadores, planos)
   debe ser Python puro que corra en Pyodide; PyNEC solo en el motor de escritorio.

**Idiomas**: el esquema de Chirptenna (castellano como texto fuente y clave; `en`, `fr`, `de`; `faltan` en la CI).
**Licencias**: AGPL-3.0 para el código y CC BY-NC 4.0 para los diseños publicados. **Relación con los otros
proyectos**: se copian las piezas (catálogos de idioma, estilo, curva de Koch), no se depende de Chirptenna como librería;
enlaces cruzados entre las tres herramientas.

## 5. Validación (antes de ampliar)

- **Motor**: dipolo λ/2 de hilo fino con resonancia a ~0,47–0,48 λ y R ≈ 70–73 Ω; el mismo `.nec` en nec2c de escritorio
  da la misma impedancia a ≤ 0,5 %.
- **Medir pronto**: una J-pole y una CoCo construidas con el plano y medidas con el NanoVNA (la CoCo con el VF del cable
  medido). Criterio: resonancia a ≤ 2 % de la simulada. Si no se cumple, se corrige el modelo antes de añadir tipos.
- Cada tipo con un estado honesto en la interfaz: «Simulado», «Medido» o «Sin validar».

## 6. Fases

| Fase | Contenido | Hecho cuando |
|---|---|---|
| 0 · Base | Estructura del repo, modelo de hilos, exportador `.nec`, PyNEC instalado y probado, CI con pytest | El dipolo exportado se abre en xnec2c/4nec2 y PyNEC da R ≈ 70–73 Ω |
| 1 · Primeros tipos | Dipolo de alambre y J-pole; barrido de ROE; lista de corte con sensibilidad; plano SVG | J-pole construida y medida a ≤ 2 % |
| 2 · Coaxial | Dipolo de coaxial y CoCo con `TL`, VF medido, cable de bajada y choke | CoCo construida y medida a ≤ 2 % |
| 3 · Interfaz | Escritorio con NiceGUI, PDF, idiomas, logo e identidad | Un usuario hace una J-pole de principio a fin sin ayuda |
| 4 · Más tipos | J-pole de Koch y discone | Cada una medida en su banda |
| 5 · Web | nec2c en WebAssembly o web solo de planos | Publicada en GitHub Pages |

## 7. Riesgos

- **PyNEC en Windows**: si no hay paquete para el Python que se use, hay que compilar necpp o usar nec2c como ejecutable.
- **CoCo**: muy sensible al VF y al modo común; los resultados dependen de modelar el cable de bajada.
- **J-pole**: la adaptación depende del punto de toma; el plano da margen y el método para buscarla con el NanoVNA.
- **Discone**: la frecuencia mínima depende del número de varillas; hay que validarla con medida.
- **Material**: diámetros reales distintos de los nominales; VF de catálogo distinto del real.
- **Mantenimiento**: es el tercer proyecto. Arrancar pequeño y medir pronto.

## 8. Decisiones del usuario

1. **Repositorio público** desde el principio o privado hasta la primera versión (hoy: privado).
2. **Unidades**: mm por defecto con conmutador a pulgadas.
3. **Primeras antenas que construir y medir**: J-pole de 70 cm o 2 m (fase 1) y CoCo de 868 MHz o 70 cm (fase 2).
4. ~~**Identidad**~~: decidida el 25-11 (antenas de coaxial y «Wire» en aluminio; `img/`).

## 9. Identidad visual

La familia ya tiene un lenguaje común: el **grillo verde visto desde arriba**, el nombre con «Chirp» en tinta oscura
(`#1f2a24`) y «tenna» en el **cobre** de la PCB (`#c8892b`); Chirptenna VNA añade la palabra «VNA» en verde
(`#2f6b3a`) y tiene una colección de ilustraciones del grillo (`img/variantes/` de su repositorio). En Chirptenna las
antenas del grillo son **curvas de Koch** (generadas con la misma geometría que el programa) porque es una herramienta de
antenas fractales en PCB.

Para Wire se mantiene el grillo, el verde y la tipografía (que se reconozca como de la familia), y cambian dos cosas:

- **Las antenas del grillo**: dejan de ser Koch. **Decidido por el usuario (25-11): coaxial** (opción b), tras ver los
  dos borradores; hecho en `img/generar_logo_wire.py` (ver `img/LEEME.md`). Opciones que se consideraron:
  - (b) **coaxial**: antenas rectas con el rayado de la malla y un tramo pelado en la punta, que habla de la CoCo y del
    dipolo de coaxial;
  - (c) **alambre doblado**: varilla con un doblez y una bolita en la punta, la más simple y la que mejor se ve en un
    favicon.
  En los favicons el coaxial va simplificado (cubierta, malla y vivo, sin trenzado) y con un borde gris en la cubierta
  para que se vea sobre fondos oscuros.
- **El color de la palabra «Wire»**: **aluminio** (decidido el 25-11), distinto del cobre de la PCB y del verde de VNA:
  `#7f8c98` sobre claro (contraste 3,4:1, válido para letra grande en negrita) y `#b9c3cc` sobre oscuro (9,8:1). Un
  aluminio más claro sobre blanco (`#c0c6cc`, 1,7:1) no se lee.

**Entregables**: un generador del logo como en los otros dos repositorios (`img/generar_logo_wire.py` que parte del
grillo de Chirptenna y cambia las antenas), el logo con texto en claro y oscuro, el icono para el favicon y una
miniatura por tipo de antena para la galería (como `antenas/miniaturas/` en Chirptenna). Se hace en la fase 3, salvo un
borrador del logo para el README al empezar.
