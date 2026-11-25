# Chuleta de modelado en NEC2 (para las tareas de Chirptenna Wire)

NEC2 resuelve corrientes en **hilos finos partidos en segmentos**. Casi todos los resultados absurdos vienen de una mala
segmentación, de uniones mal hechas o de poner la fuente donde no toca. Lo de aquí son reglas prácticas de la
documentación de NEC-2 y de la práctica habitual en 4nec2/EZNEC; donde algo hay que **comprobarlo**, se dice.

## 1. Segmentos

| Regla | Valor | Por qué |
|---|---|---|
| Largo máximo del segmento Δ | ≤ λ/10 en general; ≤ λ/20 cerca de la fuente y en curvas | Resolución de la corriente |
| Largo mínimo | Δ ≥ ~λ/1000 | Precisión numérica |
| Relación largo/radio | Δ/a ≥ 8 (núcleo de hilo fino); con el núcleo extendido (`EK`) se tolera hasta ~2 | Con Δ/a pequeño el núcleo de hilo fino falla |
| Radio frente a λ | 2πa/λ ≪ 1 (en la práctica a ≲ λ/100) | Hipótesis de hilo fino |
| Vecinos | sin saltos bruscos de longitud: razón ≤ 2 cerca de la fuente y en uniones, ≤ 5 en general | Errores en las uniones |

- `generadores.segmentos_para` reparte a unos λ/50 por segmento y fuerza un número impar (segmento central para la
  fuente). Para una curva (Koch), cada **tramo recto** es un hilo `GW` con sus propios segmentos.
- **Convergencia**: todo tipo nuevo se valida simulando con N y con 2N segmentos; la resonancia no debe moverse más de
  ~0,2 %. Si se mueve más, la segmentación no vale.

## 2. Uniones e hilos cercanos

- Dos hilos se unen si sus extremos tienen **exactamente** las mismas coordenadas. Genera las coordenadas una sola vez y
  reutilízalas; no las recalcules con otro redondeo.
- En una unión de varios hilos (pieza central de la discone), los segmentos que llegan deben tener **longitudes
  parecidas** y no muy cortas frente al radio.
- **Hilos paralelos cercanos** (adaptador de la J-pole): separación entre ejes mucho mayor que el radio (≥ ~4 radios),
  segmentos de **la misma longitud y alineados** enfrente unos de otros.
- Un hilo no puede atravesar otro ni solaparse con él.

## 3. Fuente (`EX`)

- `EX 0 tag seg 0 1.0 0.0`: fuente de tensión en el **centro de un segmento**. El segmento de la fuente y sus vecinos,
  de la misma longitud.
- **J-pole**: la fuente va en un hilo corto horizontal que une las dos ramas a la altura de la toma (un «puente» de un
  segmento o tres, con la fuente en el central). Al mover la toma se mueve ese hilo.
- **Dipolo**: en el segmento central (número impar de segmentos).
- **Discone**: en un hilo vertical corto entre el centro del disco y el vértice del cono.
- La impedancia que da NEC2 es la del **punto de la fuente**; el coaxial hasta el conector no está dentro salvo que se
  modele (fase 2).

## 4. Suelo y pérdidas

- `GN -1` (o sin `GN`): espacio libre. `GN 1`: suelo perfecto (imagen); los hilos pueden tocar z = 0 (quedan unidos a
  tierra) pero ninguno puede bajar de z = 0.
- Para comparar con las medidas del usuario (antena colgada lejos del suelo), espacio libre es lo razonable al principio.
- Conductividad del material: `LD 5 tag 0 0 sigma` (S/m). Cobre 5,8e7; latón ~1,5e7; aluminio ~3,5e7. Con alambre de
  2 mm a VHF la pérdida es pequeña, pero se pone para no sobrestimar la eficiencia.

## 5. Líneas de transmisión (`TL`)

`TL I1 I2 I3 I4 F1 F2 F3 F4 F5 F6`:

| Campo | Significado |
|---|---|
| I1, I2 | hilo (tag) y segmento del extremo 1 |
| I3, I4 | hilo y segmento del extremo 2 |
| F1 | impedancia característica Z0 en Ω. **Negativa = línea cruzada** (los terminales se intercambian en un extremo) |
| F2 | longitud en metros. **0 = la distancia en línea recta** entre los dos segmentos |
| F3–F6 | admitancias en paralelo en los extremos (normalmente 0) |

- La línea de NEC2 **no tiene pérdidas** y se propaga a la velocidad de la luz. Para un coaxial con factor de velocidad
  VF, pon **F2 = longitud física / VF**: así la fase es la correcta. La pérdida del cable no está: en líneas largas
  (CoCo de muchos tramos) hay que estimarla aparte y decirlo en el plano.
- La línea se conecta **a través** de un segmento (en paralelo con su hueco), como una fuente. El segmento tiene que
  existir y ser corto.
- `modelo.Linea` (con Z0, longitud eléctrica y VF) es la que exporta `nec.py` como `TL`: usa esa clase, no escribas la
  tarjeta a mano.

## 6. Coaxial (fase 2)

- **Malla exterior** = un hilo con el radio exterior de la malla: es lo que radia.
- **Interior** = una `TL` con la Z0 del cable y longitud eléctrica = longitud / VF, entre los segmentos de los extremos
  del tramo.
- **Cable de bajada**: la malla del cable que baja hasta el equipo radia (corriente de modo común); se modela como un
  hilo más hasta el choke, y el choke como una carga (`LD`) de impedancia alta o cortando el hilo. Sin él, la
  impedancia de un dipolo de coaxial o de una CoCo sale optimista.
- **CoCo** (colineal coaxial): tramos de λ/2·VF en los que vivo y malla se cruzan en cada unión. El modelo habitual son
  los exteriores de las mallas como hilos (con un hueco pequeño entre tramos) y los interiores como líneas `TL`, con los
  cruces representados por la conexión de las líneas (o con Z0 negativa). **Este esquema hay que validarlo** antes de
  fiarse: reproducir un caso publicado (por ejemplo, los artículos de L. B. Cebik, W4RNL, sobre colineales coaxiales) o
  comparar con 4nec2, y comprobar que el diagrama de una CoCo de 2 y 4 tramos tiene la ganancia y la forma esperadas.
- **Factor de velocidad**: el de catálogo es una aproximación (PE macizo ~0,66; espumado 0,78–0,85). El plano debe decir
  de dónde sale el VF usado y ofrecer meter el medido.

## 7. Comprobaciones rápidas de cordura

| Antena | Lo esperable en espacio libre |
|---|---|
| Dipolo λ/2 de hilo fino | longitud ~0,47–0,48 λ; R ≈ 70–73 Ω; ~2,1 dBi |
| J-pole bien ajustada | S11 ≤ −15 dB en la toma óptima; ganancia ~2 dBi; haz omnidireccional en el plano horizontal |
| Ground plane λ/4 con radiales a 45° | R ≈ 50 Ω (con radiales horizontales, ~35 Ω) |
| Discone | ROE < 2 desde ~la frecuencia en que el cono mide λ/4 hasta varias veces esa frecuencia |
| CoCo de N tramos | ganancia que sube con N (unos 2–3 dB al pasar de 2 a 4 tramos), diagrama omnidireccional aplanado |

Si algo se sale mucho de esto, revisa §1–§3 antes de tocar el diseño.
