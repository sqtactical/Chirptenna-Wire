<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/logo-wire-oscuro.png">
  <img src="img/logo-wire.png" alt="Chirptenna Wire" width="600">
</picture>

# Chirptenna Wire

Planos para construir antenas de **alambre, varilla y cable coaxial** (dipolo, J-pole, J-pole de Koch, discone, dipolo
de coaxial, colineal CoCo) para una frecuencia: cotas, lista de corte con margen de ajuste, materiales y montaje, con la
simulación (NEC2) que los respalda y el modelo en `.nec` para abrirlo en 4nec2 o xnec2c.

**Estado: en desarrollo, fase 0.** El alcance, el modelo (hilos y líneas de transmisión), las fases, la identidad visual y
las decisiones pendientes están en [`docs/PROPUESTA.md`](docs/PROPUESTA.md).

## Qué hay ahora (fase 0)

- `wire/modelo.py`: modelo de hilos (`Hilo`, `Puerto`, `Linea` con Z0 y factor de velocidad, `Carga`, `Conductividad`,
  `Barrido`, `Modelo`).
- `wire/generadores.py`: un solo tipo, `dipolo(f_MHz, radio_mm)`. Estado: **Simulado** (validado contra la teoría,
  sin medir).
- `wire/nec.py`: exportador `.nec` (CM/CE, GW, GE, GN, LD, EX, TL, FR, RP, EN) para 4nec2, xnec2c o nec2c.
- `wire/motor.py`: simulación con [PyNEC](https://pypi.org/project/PyNEC/): Z de entrada, S11/ROE en un barrido,
  ganancia máxima y búsqueda de la resonancia. Ejecuta el mismo `.nec` que se exporta.

Validación del motor (dipolo de hilo fino, radio 0,001 λ, 25 segmentos): resonancia con longitud total 0,474 λ,
R = 71,8 Ω y 2,14 dBi; doblar los segmentos mueve la resonancia menos de un 0,1 %.

```python
from wire import dipolo, nec, motor

d = dipolo(145.0, radio_mm=1.0)
nec.guardar(d, "dipolo_145.nec")        # para abrirlo en 4nec2 o xnec2c
f, z = motor.resonancia(d, 130, 160)    # MHz y ohmios
```

## Instalación

Python 3.11 o posterior. En Windows, crea el entorno fuera de OneDrive (las rutas largas fallan):

```powershell
py -3.14 -m venv $env:LOCALAPPDATA\chirptenna-wire\venv
& $env:LOCALAPPDATA\chirptenna-wire\venv\Scripts\python.exe -m pip install PyNEC numpy pytest
& $env:LOCALAPPDATA\chirptenna-wire\venv\Scripts\python.exe -m pytest
```

El exportador no necesita PyNEC; las pruebas del motor se saltan si no está. La CI pasa también el `.nec` por nec2c en
Linux y exige la misma impedancia que PyNEC a ≤ 0,5 %.

## Licencia

Código bajo [AGPL-3.0](LICENSE). Los diseños que se publiquen, bajo CC BY-NC 4.0.

Forma parte de la familia [Chirptenna](https://github.com/sqtactical/chirptenna) (antenas impresas en PCB) y
Chirptenna VNA (asistente de medida con el NanoVNA).
