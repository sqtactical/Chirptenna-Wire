# Cómo trabajar una tarea de la hoja de ruta

Guía para quien ejecute las tareas de [`ROADMAP.md`](../../ROADMAP.md), persona o agente (está pensada para que un modelo
como Sonnet pueda seguirla sin adivinar). Léela entera antes de empezar. [`CLAUDE.md`](../../CLAUDE.md) manda si hay
conflicto.

## 1. Antes de empezar

1. Lee `ROADMAP.md`, la guía de la fase (`fase1.md` … `fase5.md`) y, si la tarea toca el modelo, [`nec2.md`](nec2.md).
2. Elige **la primera tarea sin marcar cuya línea «Depende de» esté cumplida**. No saltes de fase sin que el usuario lo
   pida.
3. Mira **«Quién»**:
   - **Agente**: se hace sin el usuario.
   - **Usuario delante**: hay que construir, soldar o medir con el NanoVNA. **Para y pide al usuario** lo que diga la
     tarea; no hagas nada con el equipo hasta que confirme. Las reglas del NanoVNA son las de Chirptenna (nunca `save`;
     restaurar el barrido al acabar).
   - **Decisión del usuario**: prepara las opciones con datos y pregunta; no decidas tú.
4. Si una función, clase o archivo citado no existe, **búscalo antes de inventarlo** (`Grep`). Las guías se escribieron
   el 25-11-2026, durante la fase 1. Si de verdad no existe, dilo en el informe.
5. Lee el código que vas a tocar **entero** antes de editarlo, y las pruebas que lo cubren.

## 2. Entorno y comandos (PowerShell, desde la raíz del repositorio)

```powershell
$PY  = "$env:LOCALAPPDATA\chirptenna-wire\venv\Scripts\python.exe"
$GIT = "$env:LOCALAPPDATA\Programs\MinGit\cmd\git.exe"
```

| Para | Comando |
|---|---|
| Pruebas | `& $PY -m pytest` (las del motor se saltan sin PyNEC; la de nec2c, sin nec2c) |
| Plano de un tipo | `& $PY -m wire plano jpole 145 --diametro 2 --salida salida\jpole_145.pdf` |
| Plano desde un diseño | `& $PY -m wire plano --desde diseno.json --salida plano.svg` |
| Exportar el `.nec` | `& $PY -m wire nec dipolo 145 --diametro 2 --salida dipolo_145.nec` |
| Estado de git | `& $GIT status --short` |

- El venv está **fuera de OneDrive** (rutas de más de 260 caracteres). **No toques** el venv de Chirptenna
  (`%LOCALAPPDATA%\antenas\venv`).
- **PowerShell 5.1 se come las comillas** al pasar código a `python -c`: escribe el script en un archivo y ejecútalo.
- Los ficheros de texto se escriben en **UTF-8** (con las herramientas de edición, no con `Set-Content`).
- Para verificar un PDF visualmente, conviértelo a PNG o ábrelo; mira siempre el resultado antes de dar algo por bueno.

## 3. Reglas que no se saltan

- **Núcleo en Python puro**: `wire/modelo.py`, `wire/generadores.py`, `wire/nec.py`, `wire/diseno.py`, `wire/planos/` y
  todo lo que vaya a la web no importa PyNEC, matplotlib, scipy ni nada que no cargue en Pyodide. PyNEC solo dentro de
  `wire/motor.py` (y lo que lo use explícitamente, como `wire/ajuste.py`). `import wire` debe funcionar sin PyNEC.
- **Lo simulado es lo que se entrega**: el motor ejecuta el `.nec` exportado, no un modelo aparte.
- **Unidades**: metros y MHz dentro del modelo (como NEC2); los generadores y los planos reciben mm.
- **Planos**: todo en mm reales del papel; lo marcado «Escala 1:1» tiene que medir lo que dice. La regla de comprobación
  va en toda hoja con algo a 1:1.
- **Estados honestos**: «Simulado» (motor, sin medir), «Medido» (con medida guardada) o «Sin validar». Nunca «validado»
  sin decir cómo.
- **No ampliar tipos** fuera de su fase ni antes de medir los anteriores.
- **Idioma**: todo en castellano (nombres, comentarios, mensajes, JSON). El `.nec` en ASCII (comentarios sin tildes).
- **No subir a GitHub** ni cambiar la visibilidad del repositorio sin que el usuario lo diga. Commits locales sí, con el
  correo noreply ya configurado y la línea `Co-Authored-By` que indique la sesión.
- **No reescribir commits** que no sean tuyos (nada de `rebase`, `reset` o `--amend` sobre trabajo ajeno).

## 4. Definición de «hecho»

Una tarea está hecha cuando se cumplen **todas**:

1. Su apartado **«Hecho cuando»**, comprobado ejecutando (no suponiendo).
2. `pytest` pasa entero.
3. Si cambia el modelo o un generador: el `.nec` exportado se lee con `nec.leer` y el motor da el resultado esperado.
4. Si cambia un plano: has mirado el PDF o el SVG generado y la regla mide lo que dice.
5. Documentación al día: `README.md` si cambia el uso, `CLAUDE.md` si se aprende algo que no hay que repetir,
   `ROADMAP.md` con la casilla marcada y la fecha.
6. Commit local con un mensaje que diga qué y por qué.

## 5. Informe al acabar

Escribe en el chat, en castellano y sin relleno:

- qué tarea, qué has hecho y en qué archivos;
- los **números** (resonancia, R, ROE, ganancia, segmentos, lo que toque) y con qué los has comparado;
- qué has comprobado y cómo (pruebas, PDF mirado, medida);
- lo que no has podido hacer o queda dudoso, sin maquillarlo;
- el siguiente paso.

## 6. Cuándo parar y preguntar

- La tarea pide algo físico (construir, medir) o una decisión del usuario.
- Un resultado no tiene sentido físico (R negativa, resonancia fuera de ±20 % de lo esperado, ganancia > 10 dBi en un
  dipolo): **no lo ajustes a ojo**; revisa la segmentación (`nec2.md`) y, si sigue, pregunta.
- Dos caminos razonables con consecuencias distintas (formato de archivo, dependencia nueva, cambio del `diseno.json`).
- Algo de esta guía contradice el código o el usuario: el usuario manda; avisa de la contradicción.
