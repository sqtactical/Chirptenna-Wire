# Maquetas de planos (25-11-2026)

Referencia del formato **aprobado por el usuario** el 25-11 para los planos de `docs/PLANOS.md`. Son maquetas hechas a
mano con matplotlib, no el generador definitivo (fase 1: descripción vectorial común → SVG y PDF, Python puro).

- `plano_ejemplo_dipolo.*`: dipolo de 145 MHz en una hoja A4 (vista general sin escala, lista de corte, resultados de
  NEC2, detalle del centro a 1:1, regla de comprobación y cajetín). Los números salen del motor de la fase 0
  (`datos_dipolo.py` → `datos_dipolo.json`); el aislador, los tornillos y el pelado del coaxial son de ejemplo.
- `plano_ejemplo_jpole_koch.pdf` y `plano_jpole_koch_p1..3.png`: J-pole de Koch de alambre a 433 MHz en tres A4 (hoja
  resumen con mapa de montaje y plantilla a 1:1 en un mosaico de dos hojas con solape de 10 mm y marcas de registro).
  **Cotas orientativas, sin simular.**
- `plano_ejemplo.py` y `plano_jpole_koch.py`: los scripts de las maquetas (dependen de rutas de este ordenador y, el de
  la J-pole, de `antenas/geometria.py` de Chirptenna).

Pendiente para el generador: la cota que corta el brazo en el detalle del dipolo, la U del fondo en el mapa del mosaico
y ofrecer A3 cuando la plantilla quepa en una hoja.
