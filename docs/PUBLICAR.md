# Pasos para hacer público el repositorio

Lista para cuando el usuario diga «publica». Nada de esto se hace antes.

## Ya comprobado (25-11-2026)

- [x] Un solo autor en el historial, con el correo noreply de GitHub.
- [x] Sin claves, tokens ni contraseñas en el árbol (búsqueda de `token`, `password`, `secret`, `gmail`).
- [x] Sin rutas de este ordenador en el código ni en las maquetas (`docs/maquetas/*.py` usan rutas relativas;
      la de J-pole de Koch pide una copia de Chirptenna: variable `CHIRPTENNA`).
- [x] Licencias: `LICENSE` (AGPL-3.0), `LICENSE-DISENOS.md` (CC BY-NC 4.0 para diseños y planos), fuente DejaVu con su
      `LICENSE_DEJAVU`.
- [x] README en castellano e inglés, con el estado honesto («Simulado», nada «Medido»).
- [x] `CHANGELOG.md` y `pyproject.toml` con licencia y enlaces.

## Antes de publicar (decide el usuario)

1. **CI verde** en el último commit de `main` (Windows, Linux con nec2c, Pyodide). Mirar con `gh run list`.
2. **Revisar `CLAUDE.md` y `ROADMAP.md`**: son notas de trabajo y quedarán a la vista. Hoy no contienen datos
   personales, pero sí rutas de instalación habituales (`%LOCALAPPDATA%`). Decidir si se quedan.
3. **Medir al menos la J-pole (W1.8)** si se quiere publicar con un tipo «Medido»; si no, publicar como
   «alpha, sin medir» (es lo que dicen el README y el CHANGELOG).
4. Repasar `docs/PROPUESTA.md` (menciona al repositorio hermano y decisiones internas).
5. Cambiar la visibilidad: Settings → General → Danger Zone → *Change visibility* → Public (o
   `gh repo edit sqtactical/Chirptenna-Wire --visibility public --accept-visibility-change-consequences`).
6. Etiquetar: poner `version = "0.1.0a0"` en `pyproject.toml`, pasar «Sin publicar» del CHANGELOG a la versión,
   `git tag v0.1.0-alpha` y `gh release create v0.1.0-alpha --prerelease` (con el SHA completo si falla el `--target`).
7. Activar en GitHub: Issues, y *Private vulnerability reporting* (Settings → Security).
8. Tras publicar, enlazar desde el README de Chirptenna (fila de Wire en su `ROADMAP.md` y README).

## Cosas que no se pueden deshacer

Revisado el 25-11 con `git log -p --no-textconv`: sin claves ni correos. Las rutas del ordenador del autor que había
en commits antiguos de las maquetas se quitaron reescribiendo el historial (`git filter-branch`) antes de publicar.

Una vez público, el historial puede copiarse y quedar en cachés aunque se vuelva a poner en privado. Revisar el
historial entero (`git log -p`) antes del paso 5, no solo el árbol actual.
