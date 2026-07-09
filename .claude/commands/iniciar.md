# Iniciar

> Ejecutá las siguientes secciones para entender el workspace y luego resumí tu comprensión.

## Paso 0: Bienvenida (solo primera vez)

Antes de hacer cualquier otra cosa, verificá si existe el archivo `BIENVENIDA.md` en la raíz del workspace:

- **Si existe:** mostrá su contenido completo tal como está, luego eliminalo con `rm BIENVENIDA.md`, luego continuá con los pasos siguientes
- **Si no existe:** omitir este paso completamente y continuar directo al Paso 1

## Paso 1: Detectar el repo activo

Determiná cuál es el **repo activo** (contexto principal de la sesión) siguiendo este orden de precedencia:

1. **Declarativo (manda):** leé el campo `active_project:` en `contexto/datos-actuales.md`. Si existe y no está vacío, **ese es el repo activo**. Fin de la detección.
2. **Automático (fallback):** si el campo no existe o está vacío, inferí el repo activo por actividad reciente — listá los `.jsonl` más recientes por subproyecto en `~/.claude/projects/` (por fecha de modificación) y/o detectá subcarpetas de `proyectos/` con `.governance/PROJECT_STATE.md` (señal de repo formal en curso).
3. **Fallback explícito:** si nada de lo anterior resuelve, usá `proyectos/smart-business-decision-support-workspace` (SBDSW) mientras sea el proyecto activo.

## Ejecutar

```
ls -la
find . -type f -name "*.md" | head -20
grep -i "active_project" contexto/datos-actuales.md
```

## Leer

- `CLAUDE.md`
- `./contexto` (todos los archivos)
- **Memoria reciente:** `MEMORY.md` y los `.md` más recientes de la carpeta de memoria real
  (`~/.claude/projects/-mnt-c-Users-Usuario-Desktop-espacio-de-trabajo-claude/memory/`)
- **Del repo activo** (SBDSW por defecto): `.governance/PROJECT_STATE.md` y `README.md`

## Regla de precedencia de contexto

- El **workspace general** (NCA, ASTOR, búsqueda laboral descritos en `contexto/`) es el **contexto de fondo**.
- El **repo activo** (declarado en `active_project`, o inferido por actividad reciente) es el **contexto principal** de la sesión.
- **No** asumas NCA / ASTOR / búsqueda laboral como foco principal cuando hay un repo activo declarado o más reciente. Ante duda, **preguntá** cuál es el foco antes de asumir.

## Resumen

Después de leer, proporcioná:

1. Un breve resumen de quién soy, para qué es este workspace y cuál es tu rol
2. Tu comprensión de la estructura del workspace y el propósito de cada sección/archivo
3. Qué comandos están disponibles
4. Un resumen de mis/nuestras estrategias y prioridades actuales
5. Confirmación de que estás listo para ayudarme a perseguir estos objetivos a través de este workspace
6. **El repo activo detectado**, indicando si vino del campo declarativo `active_project` o de detección automática, y confirmá que ese es el foco de la sesión (o pedí aclaración si hay ambigüedad)
