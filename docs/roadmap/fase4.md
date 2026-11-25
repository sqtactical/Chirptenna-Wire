# Fase 4 · J-pole de Koch, discone y papel grande

Objetivo: los dos tipos que más necesitan plantilla a 1:1 y el papel grande (A3 y mosaico de A4). **Solo después de
haber medido la J-pole (W1.8) y una antena de coaxial (W2.7).** Formato de referencia: `docs/maquetas/` (la J-pole de
Koch en mosaico está aprobada por el usuario).

## W4.1 · Geometría de Koch
- **Quién**: Agente. **Depende de**: nada.
- **Archivos**: `wire/geometria.py` (nuevo).
- **Pasos**: copiar el algoritmo de Chirptenna (`antenas/geometria.py`: sistema L `F → F+F--F+F`, giro de 60°, y el
  ajuste de los extremos a dos puntos) **sin importar** ese repositorio, con su crédito en un comentario. Devuelve una
  lista de puntos en mm.
- **Hecho cuando**: iteraciones 0–3 dan 1, 4, 16 y 64 tramos y la longitud total es (4/3)^n veces la cuerda (prueba).

## W4.2 · J-pole de Koch
- **Quién**: Agente. **Depende de**: W4.1, W1.2.
- **Pasos**: el radiador λ/2 de la J-pole se sustituye por una curva de Koch (iteración 1 o 2) entre los mismos extremos;
  el adaptador λ/4 queda recto. Cada tramo de la curva es un `GW` con sus segmentos (ver `nec2.md` §1: Δ/a ≥ 8 limita la
  iteración con alambre grueso; **avisa** si el tramo es demasiado corto para el diámetro). Ajuste: altura de la curva y
  toma. Las muescas hacia fuera, lejos de la rama corta.
- **Pruebas**: convergencia N/2N; acortamiento frente a la J-pole recta (dato a anotar, no a suponer); ROE ≤ −15 dB.
- **Hecho cuando**: el tipo da diseños coherentes en 2 m y 70 cm y su plano (W4.3) sale bien.

## W4.3 · A3 y mosaico de A4
- **Quién**: Agente. **Depende de**: W1.3.
- **Archivos**: `wire/planos/paginacion.py` (`area_util`, `decidir_papel`), y las hojas de cada tipo.
- **Pasos** (`docs/PLANOS.md` §3): si la plantilla 1:1 no cabe en A4 → A3 si cabe, o mosaico de A4 con solape de 10 mm,
  marcas de registro, línea de corte, etiquetas A1, A2… y mapa de montaje en la hoja resumen (dibujando **toda** la
  antena en el mapa, U del fondo incluida); lo que no cabe ni en 4 × 3 hojas, sin escala.
- **Pruebas**: la unión de las ventanas del mosaico, quitando el solape, cubre la plantilla entera sin huecos ni
  duplicados; ninguna marca pisa el dibujo.
- **Hecho cuando**: la J-pole de Koch de 433 MHz sale en mosaico como la maqueta y en A3 cuando se elige.

## W4.4 · Discone
- **Quién**: Agente. **Depende de**: W4.3.
- **Pasos**: disco de N radiales (8 por defecto, probar 16) y cono de N varillas con su ángulo (por defecto 60° de
  apertura total), alimentados en un hilo corto entre el centro del disco y el vértice del cono (`nec2.md` §3);
  frecuencia mínima ≈ la del cono de λ/4; segmentos parecidos en la unión central. Plano: varillas sin escala con su
  longitud; plantilla 1:1 de la pieza central (taladros y ángulos) y del ángulo del cono.
- **Pruebas**: ROE < 2 en al menos 1:3 de rango de frecuencia; con 16 varillas la frecuencia mínima baja un poco
  respecto a 8 (anotar cuánto).
- **Hecho cuando**: diseños coherentes para 100–500 MHz y plano con la pieza central a 1:1.

## W4.5 · Medir
- **Quién**: **Usuario delante**. **Depende de**: W4.2, W4.4.
- Como W1.8, para la J-pole de Koch y la discone. La discone se mide en todo el rango del NanoVNA que cubra.
