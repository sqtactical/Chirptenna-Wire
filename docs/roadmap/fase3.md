# Fase 3 · Interfaz de escritorio

Objetivo: que un usuario haga una antena de principio a fin sin tocar la terminal. Se copia el estilo de la interfaz de
Chirptenna (`..\proyecto_generador_antenas\gui\app.py`: NiceGUI, pestañas, tema claro/oscuro, variables CSS), sin
importar nada de ese repositorio.

## W3.1 · Esqueleto de la interfaz
- **Quién**: Agente. **Depende de**: fase 1 cerrada.
- **Archivos**: `gui/app.py` (nuevo), `requirements` o `pyproject.toml` (añadir NiceGUI como dependencia **opcional**
  de escritorio, no del núcleo).
- **Pasos**: pestañas **Elegir** (galería de tipos con miniatura y estado), **Diseño** (frecuencia o banda, material,
  cable, parámetros básicos y avanzados con ayuda «?»), **Simulación** (ROE, Z, ganancia, diagrama), **Plano** (vista y
  descargas), **Medir** (enlace a Chirptenna VNA). Escucha solo en 127.0.0.1. La simulación en un hilo o subproceso
  para no bloquear la página.
- **Hecho cuando**: se arranca con `python gui/app.py`, se elige la J-pole, se ajusta y se ve el resultado.
- **Trampas**: lecciones 19, 33, 47 y 49 del `CLAUDE.md` de Chirptenna (subproceso, tipos de Python en lo que va a la
  interfaz, colores con variables CSS, Plotly en la sesión de Claude con `herramientas/lanzar_app_claude.py`).

## W3.2 · Vista previa y descargas del plano
- **Quién**: Agente. **Depende de**: W3.1.
- **Pasos**: el SVG de cada hoja se muestra en la pestaña Plano (con selector de hoja); botones para PDF, SVG, `.nec` y
  `diseno.json`; configuración del plano (papel, qué hacer con lo grande, unidades) guardada en el diseño.
- **Hecho cuando**: lo que se ve es lo que se descarga (mismo `Plano`), y al reabrir el diseño la configuración sigue.

## W3.3 · Idiomas
- **Quién**: Agente. **Depende de**: W3.1.
- **Pasos**: copiar el esquema de Chirptenna (`antenas/i18n.py`, `herramientas/i18n.py`): castellano como texto fuente y
  clave, `tr('texto {0}', x)`, catálogos `idiomas/<código>.json`, `faltan` en la CI. Los planos también se traducen
  (textos del cajetín, cotas, lista de corte) con el mismo `tr`.
- **Hecho cuando**: en, fr y de completos y la CI falla si falta una traducción.

## W3.4 · Enlace con Chirptenna VNA y estado «Medido»
- **Quién**: Agente. **Depende de**: W3.1.
- **Pasos**: botón «Medir con Chirptenna VNA» que abre su web con `?f=<MHz>&banda=<ini-fin>&nombre=<diseño>` (el mismo
  contrato que usa Chirptenna); importar un `.s1p` medido y superponerlo a la ROE simulada; guardar la medida con el
  diseño; un tipo pasa a «Medido» solo con una medida guardada a ≤ 2 %.
- **Hecho cuando**: con un `.s1p` de ejemplo se ve la comparación y el estado cambia.

## W3.5 · Instalación y README
- **Quién**: Agente; la decisión de cómo distribuir es del **usuario**. **Depende de**: W3.1–W3.4.
- **Pasos**: instrucciones de instalación (venv fuera de OneDrive, `pip install`), o un `instalar.bat` como el de
  Chirptenna si el usuario lo pide; capturas del README; CHANGELOG y primera versión etiquetada **solo cuando el usuario
  lo diga**.
