# Chirptenna Wire · notas para Claude

Planos de antenas de alambre, varilla y coaxial con simulación NEC2. Alcance: `docs/PROPUESTA.md`.
**Qué hacer y en qué orden: `ROADMAP.md`** (tareas W1.1…W5.4, cada una desarrollada en `docs/roadmap/`). Antes de
cualquier tarea, leer `docs/roadmap/00_como_trabajar.md`, y para tocar el modelo, `docs/roadmap/nec2.md`. Si el usuario
no pide otra cosa, lo siguiente es la primera tarea sin marcar de la primera fase sin cerrar.

## Entorno

- Windows; Python 3.14 del sistema (`py -3.14`). venv propio **fuera de OneDrive** (rutas de más de 260 caracteres):
  `%LOCALAPPDATA%\chirptenna-wire\venv` con `PyNEC numpy pytest`. Dentro de la app de Claude esa ruta se redirige a
  `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Local\chirptenna-wire\venv`; fuera de ella hay que crearlo de nuevo.
- **No tocar** el venv de Chirptenna (`%LOCALAPPDATA%\antenas\venv`).
- Motor: **PyNEC 2.4.1** (rueda `cp311-abi3`, instala sin compilar en Windows y Linux). nec2c no está en este Windows
  (ni compilador ni WSL): el contraste con nec2c lo hace la CI en Ubuntu (`apt install nec2c`).
- git portable: `%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe` (no está en el PATH). Commits con el correo noreply ya
  configurado. **No empujar ni hacer público el repositorio sin que lo diga el usuario.**
- Pruebas: `python -m pytest` desde la raíz (las de motor se saltan sin PyNEC; la de nec2c, sin nec2c; la de Pyodide,
  sin Node + `npm install pyodide` en `%LOCALAPPDATA%\chirptenna-wire\pyodide-prueba` o `CHIRPTENNA_PYODIDE`).
- Planos: fpdf2 2.9 (PDF) carga en Pyodide 0.29 con micropip (comprobado con `herramientas/prueba_pyodide.mjs`).
  Para ver un PDF o SVG: `msedge --headless=new --screenshot` (no hay pdftoppm).
- Los ejemplos de `docs/ejemplos/` se regeneran con `python -m wire plano ... --guardar`; las pruebas de planos los leen.
- En PowerShell 5.1 no pasar código con comillas a `python -c`: se pierden. Usar un script en un archivo.

## Reglas

- Todo en español: nombres, comentarios, mensajes, claves de JSON. El `.nec` va en ASCII (comentarios sin tildes).
- Unidades internas en metros y MHz (como NEC2); los generadores reciben mm.
- `motor.simular` ejecuta el `.nec` exportado (exportar → leer → PyNEC): lo simulado es lo que se entrega.
- Núcleo en **Python puro que corra en Pyodide** (modelo, generadores, nec, diseno, planos). PyNEC solo en
  `wire/motor.py` y `wire/ajuste.py`; `import wire` y `wire.planos` no lo cargan. Los planos leen los resultados de
  `diseno.json`, nunca llaman al motor.
- Planos: primitivas en mm del papel (y hacia abajo); cotas y rayados se descomponen en código común para que SVG y PDF
  sean idénticos. Lo que va a 1:1 lleva etiqueta `plantilla:*` y la hoja, la regla (`regla:barra`).
- **No ampliar tipos antes de medir.** Cada tipo con estado honesto: «Simulado», «Medido» o «Sin validar».
- Se copian piezas de Chirptenna (`..\proyecto_generador_antenas`), no se depende de él como librería.
- Licencia AGPL-3.0 (código); CC BY-NC 4.0 para los diseños publicados.
