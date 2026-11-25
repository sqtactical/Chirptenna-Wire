<picture>
  <source media="(prefers-color-scheme: dark)" srcset="img/logo-wire-oscuro.png">
  <img src="img/logo-wire.png" alt="Chirptenna Wire" width="600">
</picture>

# Chirptenna Wire

Build plans for **wire, rod and coaxial-cable antennas** (dipole, J-pole, Koch J-pole, discone, coax dipole,
CoCo collinear) for a given frequency: dimensions, cut list with trimming margin, materials and assembly, backed
by an NEC2 simulation, plus the `.nec` model to open in 4nec2 or xnec2c.

**Status: alpha, under development (phase 1).** Nothing has been measured with a VNA yet: every type is labelled
"Simulated" or "Unvalidated" and the drawings say so. Scope and phases: [`docs/PROPUESTA.md`](docs/PROPUESTA.md)
(Spanish); drawing design: [`docs/PLANOS.md`](docs/PLANOS.md) (Spanish).

| Type | Status | Drawing |
|---|---|---|
| Half-wave dipole | **Simulated** (checked against theory, not measured) | 1 A4 sheet: overview, cut list, simulated SWR, 1:1 centre detail |
| Wire J-pole | **Simulated** (not measured) | 2 A4 sheets: summary and 1:1 detail of the U bottom, matching section and feed tap |

Examples in [`docs/ejemplos/`](docs/ejemplos/) (PDF, `diseno.json`, `.nec`).

```powershell
python -m wire plano jpole 145 --diametro 2 --salida jpole_145.pdf --guardar jpole_145.json
python -m wire plano --desde jpole_145.json --salida jpole_145.svg
python -m wire nec jpole 145 --diametro 2 --salida jpole_145.nec
```

The core (`wire/modelo.py`, `generadores.py`, `nec.py`, `diseno.py`, `planos/`) is pure Python and also runs in
Pyodide (planned web lite). The simulation engine (`wire/motor.py`, `ajuste.py`) needs
[PyNEC](https://pypi.org/project/PyNEC/) and is desktop-only.

## Install

Python 3.11 or later.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install PyNEC numpy fpdf2 pytest
.venv\Scripts\python.exe -m pytest
```

**Print drawings at 100 % ("actual size")** and check the 80 mm ruler before using the 1:1 details.

## Licence

Code: [AGPL-3.0](LICENSE). Published designs and drawings: CC BY-NC 4.0, see
[`LICENSE-DISENOS.md`](LICENSE-DISENOS.md). Part of the [Chirptenna](https://github.com/sqtactical/chirptenna)
family (PCB antennas).
