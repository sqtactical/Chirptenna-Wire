# Chirptenna Wire · notas para Claude

Planos de antenas de alambre, varilla y coaxial con simulación NEC2. Alcance y fases: `docs/PROPUESTA.md`.

## Entorno

- Windows; Python 3.14 del sistema (`py -3.14`). venv propio **fuera de OneDrive** (rutas de más de 260 caracteres):
  `%LOCALAPPDATA%\chirptenna-wire\venv` con `PyNEC numpy pytest`. Dentro de la app de Claude esa ruta se redirige a
  `%LOCALAPPDATA%\Packages\Claude_*\LocalCache\Local\chirptenna-wire\venv`; fuera de ella hay que crearlo de nuevo.
- **No tocar** el venv de Chirptenna (`%LOCALAPPDATA%\antenas\venv`).
- Motor: **PyNEC 2.4.1** (rueda `cp311-abi3`, instala sin compilar en Windows y Linux). nec2c no está en este Windows
  (ni compilador ni WSL): el contraste con nec2c lo hace la CI en Ubuntu (`apt install nec2c`).
- git portable: `%LOCALAPPDATA%\Programs\MinGit\cmd\git.exe` (no está en el PATH). Commits con el correo noreply ya
  configurado. **No empujar ni hacer público el repositorio sin que lo diga el usuario.**
- Pruebas: `python -m pytest` desde la raíz (las de motor se saltan sin PyNEC; la de nec2c, sin nec2c).
- En PowerShell 5.1 no pasar código con comillas a `python -c`: se pierden. Usar un script en un archivo.

## Reglas

- Todo en español: nombres, comentarios, mensajes, claves de JSON. El `.nec` va en ASCII (comentarios sin tildes).
- Unidades internas en metros y MHz (como NEC2); los generadores reciben mm.
- `motor.simular` ejecuta el `.nec` exportado (exportar → leer → PyNEC): lo simulado es lo que se entrega.
- **No ampliar tipos antes de medir.** Cada tipo con estado honesto: «Simulado», «Medido» o «Sin validar».
- Se copian piezas de Chirptenna (`..\proyecto_generador_antenas`), no se depende de él como librería.
- Licencia AGPL-3.0 (código); CC BY-NC 4.0 para los diseños publicados.
