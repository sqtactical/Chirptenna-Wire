# Fase 2 · Coaxial

Objetivo: antenas hechas con cable coaxial (dipolo de manga y colineal CoCo), con la malla modelada como hilo y el
interior como línea de transmisión, el factor de velocidad del cable real y el cable de bajada. Lee antes
[`nec2.md`](nec2.md) §5–§6.

## W2.1 · Coaxial en el modelo
- **Quién**: Agente. **Depende de**: fase 1 cerrada.
- **Archivos**: `wire/modelo.py` (`Linea` ya tiene Z0, longitud eléctrica y VF), `wire/nec.py`, pruebas.
- **Pasos**: 1) una función auxiliar `tramo_coaxial(p0, p1, cable, segmentos)` que devuelva el hilo de la malla (radio
  exterior de la malla) y la `Linea` interior entre los segmentos de sus extremos, con longitud eléctrica = longitud/VF;
  2) comprobar que `nec.exportar` escribe la `TL` con F2 = longitud/VF y que `nec.leer` la recupera.
- **Prueba de validación**: un tramo de coaxial de λ/4·VF abierto en un extremo, visto desde el otro, debe dar una
  impedancia casi nula (cortocircuito) en la frecuencia de diseño: comprueba que la `TL` se comporta como la teoría.
- **Hecho cuando**: la prueba pasa y el `.nec` se abre en xnec2c/4nec2 (o pasa por nec2c en la CI).

## W2.2 · Tabla de cables y VF medido
- **Quién**: Agente (la medida del VF es W2.7). **Depende de**: W2.1.
- **Archivos**: `wire/cables.py` (nuevo).
- **Pasos**: tabla con nombre, Z0, VF de catálogo, diámetro exterior de la malla y del dieléctrico, y pérdida por 100 m a
  100 y 1000 MHz (de hojas de datos; **cita la fuente** en un comentario). Cables: RG-58, RG-174, RG-316, RG-213,
  LMR-400, Aircell 7, H155. Permitir un VF medido que sustituye al de catálogo y que el plano dice «medido».
- **Hecho cuando**: la tabla está con fuentes y el `Diseno` guarda el cable y de dónde sale el VF.

## W2.3 · Cable de bajada y choke
- **Quién**: Agente. **Depende de**: W2.1.
- **Pasos**: el exterior de la malla del cable que baja al equipo como un hilo de longitud configurable (por defecto
  λ/2) que termina en el choke; el choke como una carga `LD` de impedancia alta (por ejemplo 1–2 kΩ resistivos) o un
  corte del hilo. Comparar la impedancia con y sin cable de bajada en un dipolo de coaxial.
- **Hecho cuando**: hay una opción en el modelo para incluirlo y una prueba que muestra el efecto (con choke la
  impedancia se acerca a la del dipolo aislado).

## W2.4 · Dipolo de manga (sleeve) de coaxial
- **Quién**: Agente. **Depende de**: W2.1, W2.3.
- **Qué es**: el vivo con su dieléctrico sobresale λ/4 hacia arriba (radiador) y la malla se dobla hacia atrás λ/4 sobre
  el cable formando la manga (el otro brazo). La manga es un hilo exterior; entre manga y cable hay una línea (la
  manga y el cable forman una línea coaxial abierta de λ/4 que hace de choke).
- **Pasos**: generador, ajuste del largo del radiador y de la manga, plano con el pelado a 1:1. Si el modelado de la manga
  no da resultados razonables (R ~70 Ω, haz de dipolo), para y pregunta antes de seguir.
- **Hecho cuando**: resonancia y ROE razonables, convergencia N/2N, plano generado.

## W2.5 · Colineal CoCo
- **Quién**: Agente. **Depende de**: W2.1–W2.3.
- **Pasos**: 1) parámetros: número de tramos (2–8), cable, VF, punta λ/4 y choke; 2) tramos de λ/2·VF con el cruce
  vivo–malla en cada unión, modelados como en `nec2.md` §6; 3) **validar el modelo** con un caso publicado o con 4nec2
  antes de ajustar nada; 4) ajuste del largo de los tramos y de la punta para la ROE.
- **Pruebas**: la ganancia sube con N (2 → 4 tramos: +2–3 dB); diagrama omnidireccional; la ROE no se dispara al
  cambiar N.
- **Hecho cuando**: el caso de validación coincide y el generador da CoCo de 2, 4 y 6 tramos coherentes.
- **Trampas**: el VF manda en la frecuencia (un 0,66 frente a un 0,82 cambia todo): el plano lo pone bien visible.

## W2.6 · Planos del coaxial
- **Quién**: Agente. **Depende de**: W2.4, W2.5.
- **Pasos**: tramos sin escala con su longitud física (y la eléctrica entre paréntesis); detalle 1:1 del pelado de cada
  extremo y del cruce (dónde se corta la malla, cuánto se pela, cómo se suelda), la punta, el choke (vueltas y diámetro)
  y la protección (tubo de PVC, termorretráctil). Cajetín con el cable y el VF («de catálogo» o «medido»).
- **Hecho cuando**: hay PDF de ejemplo en `docs/ejemplos/` y pasan las pruebas de planos de W1.7.

## W2.7 · Medir el VF y una CoCo
- **Quién**: **Usuario delante**. **Depende de**: W2.5, W2.6.
- **Pasos**: 1) medir el VF del cable del usuario (latiguillo abierto con el NanoVNA; Chirptenna tiene
  `vna/medir_latiguillo.py`); 2) generar la CoCo con ese VF; 3) construir y medir; 4) guardar en `docs/medidas/`.
- **Hecho cuando**: resonancia a ≤ 2 % de la simulada o causa identificada.
