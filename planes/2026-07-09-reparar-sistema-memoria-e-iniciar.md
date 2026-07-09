# Plan: Reparar sistema de memoria (consolidador) y hacer que /iniciar priorice el repo activo

**Creado:** 2026-07-09
**Estado:** Listo para implementar
**Pedido:** Fix mínimo del consolidador (timeout del hook, persistencia del log, logging propio con rotación) + fix funcional de `/iniciar` (leer memoria reciente y priorizar el repo activo SBDSW por sobre el workspace general, detección declarativa primero).

---

## Descripción General

### Qué Logra Este Plan

Reactiva el consolidador de memoria, que dejó de persistir su registro desde la migración a WSL (último `last_run` = 2026-07-04), y corrige `/iniciar` para que abra cada sesión con el contexto correcto: la memoria reciente y el **repo activo** (`proyectos/smart-business-decision-support-workspace`, "SBDSW"), en lugar de asumir por defecto NCA / ASTOR / búsqueda laboral.

### Por Qué Importa

El sistema de memoria es la columna vertebral de la continuidad entre sesiones descrita en `CLAUDE.md`. Hoy está silenciosamente roto: las sesiones de julio no se registran y no hay forma de diagnosticarlo porque el consolidador no deja rastro. Además, `/iniciar` orienta cada sesión hacia contexto obsoleto (búsqueda laboral, NCA) cuando el trabajo real más reciente ocurre en SBDSW. Ambos defectos degradan la utilidad de Claude en cada arranque.

---

## Estado Actual

### Estructura Existente Relevante

```
~/.claude/settings.json                         ← hook SessionStart, timeout: 60
scripts/memory_consolidator/
  main.py                                        ← orquestador; save_log condicional (línea ~212)
  jsonl_processor.py                             ← encuentra .jsonl previo
  memory_writer.py                               ← call_claude_cli timeout=120
  skill_evolver.py
  doc_processor.py
memory/                                          ← carpeta WORKSPACE (ruta A)
  processed_log.json                             ← last_run 2026-07-04 (congelado)
  extraction_prompt.md
  inbox/
/home/sgarrido/.claude/projects/-mnt-c-.../memory/   ← carpeta REAL (ruta B)
  MEMORY.md, session_*.md, feedback_*.md, user_profile.md
.claude/commands/iniciar.md                      ← solo lee CLAUDE.md y ./contexto
proyectos/smart-business-decision-support-workspace/.governance/
  PROJECT_STATE.md                               ← estado del repo activo
```

**Diagnóstico previo (referencia):** el consolidador escribe en DOS carpetas `memory/` distintas — `processed_log.json`/`extraction_prompt.md`/`inbox/` en la ruta A (workspace, vía `Path(__file__).parent.parent.parent`), y los `.md` de contexto (`MEMORY.md`, `session_*`, `feedback_*`) en la ruta B (`get_memory_dir()`, dentro de `~/.claude/projects/`). Este plan **NO unifica** esas carpetas (fuera de alcance).

### Brechas o Problemas que se Abordan

1. **Timeout incompatible:** el hook `SessionStart` tiene `timeout: 60` pero `call_claude_cli()` usa `timeout=120`. La invocación anidada de `claude -p` suele exceder 60s → Claude Code mata el hook antes de `save_log()` → nada se registra.
2. **`save_log()` condicional:** en `main.py` solo se guarda si `changed or session_extracted`. Si la extracción devuelve `{}` o falla, el `.jsonl` procesado **no queda marcado**, por lo que se reintenta indefinidamente y `last_run` nunca avanza.
3. **Sin observabilidad:** el stdout del consolidador se pierde; no hay forma de saber si corrió, falló o expiró.
4. **`/iniciar` desalineado:** solo lee `CLAUDE.md` y `./contexto`; no lee `memory/` ni detecta el repo activo. Orienta la sesión hacia contexto por defecto (NCA/ASTOR/búsqueda laboral) aunque el trabajo reciente esté en SBDSW.

---

## Cambios Propuestos

### Resumen de Cambios

- **Fix mínimo (consolidador):**
  - Subir `timeout` del hook `SessionStart` de `60` → `180` en `~/.claude/settings.json`.
  - Modificar `main.py` para que `processed_log.json` se persista **siempre** al final (aunque la extracción devuelva `{}` o falle parcialmente), marcando el `.jsonl` como procesado y actualizando `last_run`.
  - Agregar logging persistente a `memory/consolidator.log` (ruta A / workspace).
- **Fix funcional (`/iniciar`):**
  - Reescribir `.claude/commands/iniciar.md` para leer la memoria reciente (ruta B `MEMORY.md` + `.md` recientes) y **detectar y priorizar el repo activo** SBDSW.
  - Distinguir explícitamente "workspace general" vs "repo activo".
  - Regla de precedencia: si hay un repo activo más reciente, **no** asumir NCA/ASTOR/búsqueda laboral como contexto principal.
- **Mantenimiento de consistencia:** actualizar la sección "Sistema de Memoria Automática" y "/iniciar" en `CLAUDE.md`.

### Nuevos Archivos a Crear

| Ruta del Archivo | Propósito |
| --- | --- |
| `memory/consolidator.log` | Log persistente del consolidador (se crea en runtime; no versionado — ver Paso 3 sobre `.gitignore`). |
| `planes/2026-07-09-reparar-sistema-memoria-e-iniciar.md` | Este plan. |

### Archivos a Modificar

| Ruta del Archivo | Cambios |
| --- | --- |
| `~/.claude/settings.json` | `timeout: 60` → `180` en el hook `SessionStart` del consolidador. |
| `scripts/memory_consolidator/main.py` | (a) Persistir `processed_log.json` siempre (marcar `.jsonl` procesado aun con `{}`/fallo); (b) instrumentar logging a `memory/consolidator.log`. |
| `.claude/commands/iniciar.md` | Añadir pasos: leer `active_project` declarativo → fallback automático, leer memoria reciente, regla de precedencia workspace vs repo activo. |
| `contexto/datos-actuales.md` | Añadir campo declarativo `active_project: proyectos/smart-business-decision-support-workspace`. |
| `CLAUDE.md` | Actualizar descripción de `/iniciar` y del "Sistema de Memoria Automática" (timeout, log con rotación, precedencia de contexto, `active_project`). |
| `.gitignore` | Añadir `memory/consolidator.log` y `memory/consolidator.log.1`. |

### Archivos a Eliminar (si aplica)

Ninguno. **No se borran rutas históricas** de `processed_log.json` (fuera de alcance).

---

## Decisiones de Diseño

### Decisiones Clave Tomadas

1. **Timeout del hook a 180s (no 130s):** el CLI interno usa 120s; se deja margen (180 > 120) para overhead de arranque de `claude -p`, I/O y el procesamiento del `inbox/`. Cumple el pedido explícito del usuario (180).
2. **Marcar el `.jsonl` como procesado incluso si la extracción da `{}`:** una sesión sin contenido relevante es un resultado **válido y final**; reintentarla en cada arranque desperdicia el presupuesto de 180s y bloquea el avance de `last_run`. Se registra en el log que "no hubo extracción" para trazabilidad.
3. **`save_log()` incondicional al final:** se mueve la escritura del log fuera del `if changed`, de modo que `last_run` siempre avance y el `.jsonl` de la sesión previa quede marcado. Se conserva el cap de 20 rutas existente (no se toca la política de retención).
4. **Log en ruta A (`memory/consolidator.log`):** misma carpeta que `processed_log.json`, coherente con dónde el script ya escribe estado (`get_log_path()`). Evita depender de `get_memory_dir()` (ruta B), que puede resolver a `None`.
5. **Logging dual (archivo + stdout):** se mantiene el `print()` actual (para debug manual) y se agrega escritura a archivo, envuelto para que un fallo de logging **nunca** rompa el consolidador (el bloque `finally: sys.exit(0)` sigue garantizando no bloquear el arranque).
6. **`/iniciar` detecta repo activo por mtime de `.jsonl`:** se determina el repo activo comparando la fecha del `.jsonl` más reciente por subproyecto en `~/.claude/projects/`, y/o por la presencia de `.governance/PROJECT_STATE.md`. SBDSW se nombra explícitamente como repo activo actual (pedido del usuario), pero la lógica queda descrita de forma que generalice.
7. **Precedencia de contexto explícita en `/iniciar`:** se añade una regla textual: "Si existe un repo activo con actividad más reciente que el workspace general, ese repo es el contexto principal; NCA/ASTOR/búsqueda laboral pasan a contexto de fondo salvo pedido explícito."

### Alternativas Consideradas

- **Bajar el timeout del CLI interno en vez de subir el del hook:** rechazado — reduciría la calidad de extracción y el usuario pidió explícitamente subir el hook a 180.
- **Reintentar sesiones con `{}` hasta obtener contenido:** rechazado — es exactamente el comportamiento que congela `last_run`; una extracción vacía es terminal.
- **Usar el módulo `logging` de Python con rotación:** viable, pero se opta por un helper simple de append con timestamp para no introducir configuración nueva ni cambiar la arquitectura del consolidador (fuera de alcance). Se puede migrar a `logging` más adelante.
- **Hardcodear SBDSW como único repo activo en `/iniciar`:** rechazado como única solución — se nombra SBDSW pero se describe la detección por recencia para que `/iniciar` no quede obsoleto cuando cambie el foco.
- **Unificar las dos carpetas `memory/`:** explícitamente fuera de alcance por pedido del usuario.

### Preguntas Abiertas (RESUELTAS)

1. **`consolidator.log` — ¿versionar o ignorar?** → **RESUELTO: ignorar en `.gitignore`.** Es log de runtime, no se versiona.
2. **Detección de repo activo en `/iniciar`:** → **RESUELTO: declarativa primero, automática después.** Se agrega un campo `active_project:` en `contexto/datos-actuales.md`. Si el campo existe, manda. Si no existe, se cae a detección automática por actividad reciente (`mtime` de `.jsonl`). **SBDSW queda como fallback explícito** mientras sea el proyecto activo. Justificación del usuario: declarativo es más seguro que `mtime` — evita que una sesión accidental de NCA desplace a SBDSW como proyecto activo.
3. **Rotación del log:** → **RESUELTO: rotación simple por tamaño.** Máximo 1 MB; al superarlo, renombrar a `consolidator.log.1` (1 solo backup) y empezar log nuevo. No crecer libremente.

---

## Tareas Paso a Paso

Ejecutá estas tareas en orden durante la implementación.

### Paso 1: Subir el timeout del hook SessionStart

Editar `~/.claude/settings.json` y cambiar el `timeout` del hook del consolidador.

**Acciones:**

- Leer `~/.claude/settings.json`.
- En el bloque `hooks.SessionStart[...].hooks[...]` cuyo `command` apunta a `scripts/memory_consolidator/main.py`, cambiar `"timeout": 60` → `"timeout": 180`.
- Validar que el JSON siga siendo válido (parseable).

**Archivos afectados:**

- `~/.claude/settings.json`

---

### Paso 2: Persistir processed_log.json siempre (main.py)

Modificar `main.py` para que el `.jsonl` de la sesión previa quede marcado como procesado y `last_run` avance **aunque la extracción devuelva `{}` o falle parcialmente**.

**Acciones:**

- En el bloque "2. Procesar .jsonl de la sesión anterior":
  - Cuando `find_previous_jsonl` devuelve una sesión no procesada, envolver `extract_relevant_fragments` + `update_memory_from_jsonl` en `try/except`. **Independientemente** de si `fragments` es corto, la extracción devuelve `{}`, o lanza excepción:
    - Añadir `session_path` a `log["processed_jsonl"]` (marcarlo procesado — es terminal).
    - Aplicar el cap existente `log["processed_jsonl"] = log["processed_jsonl"][-20:]`.
    - Setear una bandera local (p. ej. `log_dirty = True`) para forzar guardado.
  - Registrar en el log de archivo el resultado: `extraído` / `sin contenido ({})` / `error: <msg>`.
- En el bloque final "5. Guardar log y reportar":
  - Cambiar la condición de guardado para que persista si `changed or session_extracted or log_dirty`.
  - Actualizar `log["last_run"]` siempre que se haya intentado procesar una sesión (aunque sin extracción), no solo cuando hubo cambios en `memory/`.
- No modificar la lógica de `store_extraction` ni de `maybe_evolve_skills` (arquitectura intacta): el contador de skill-evolution sigue avanzando solo con extracciones reales (`session_extracted`).

**Archivos afectados:**

- `scripts/memory_consolidator/main.py`

**Nota de implementación (antes/después conceptual):**

- *Antes:* `if fragments and len(...) > 50: ... log.append(...); changed = True` → si no, nada se marca.
- *Después:* siempre se marca el `session_path` como procesado; `changed` se reserva para "hubo escritura en `memory/`", y un nuevo `log_dirty`/actualización de `last_run` garantiza la persistencia del avance.

---

### Paso 3: Agregar logging persistente a memory/consolidator.log

Instrumentar `main.py` con un helper de logging que escriba a `memory/consolidator.log` (ruta A) además del `print()` actual.

**Acciones:**

- Añadir en `main.py` constantes: `LOG_MAX_BYTES = 1_048_576` (1 MB), y helper de ruta `get_consolidator_log_path()` → `Path(__file__).parent.parent.parent / "memory" / "consolidator.log"` (misma base que `get_log_path()`).
- Añadir una función `_rotate_log_if_needed(log_path: Path)` que, si el archivo existe y supera `LOG_MAX_BYTES`, lo renombre a `consolidator.log.1` (sobrescribiendo el backup previo si existe) y deje el `.log` vacío para reiniciar. Envuelta en `try/except` silencioso.
- Añadir una función `log_line(msg: str)` que:
  - Llame a `_rotate_log_if_needed(...)` antes de escribir.
  - Haga append de `f"[{datetime.now().isoformat(timespec='seconds')}] {msg}\n"`.
  - Esté envuelta en `try/except` que silencie cualquier error de I/O (el logging nunca debe romper el arranque).
- Reemplazar/duplicar los `print("[Consolidador] ...")` clave por `log_line(...)` en los hitos: inicio, memory_dir resuelto, sesión detectada/procesada/sin contenido/error, inbox, skill-evolution, guardado final, y el `except` global de `main()`.
- Escribir una línea de cierre con el resultado neto (p. ej. `RESULTADO: log persistido, last_run=<iso>`).
- Verificar que el bloque `if __name__ == "__main__": try/except/finally: sys.exit(0)` siga garantizando salida limpia.

**Archivos afectados:**

- `scripts/memory_consolidator/main.py`
- `memory/consolidator.log` y `memory/consolidator.log.1` (se crean en runtime; rotación por tamaño a 1 MB con 1 backup)

---

### Paso 4: Ignorar consolidator.log en git

**Acciones:**

- Leer `.gitignore`.
- Añadir (si no están cubiertas) las líneas `memory/consolidator.log` y `memory/consolidator.log.1`.

**Archivos afectados:**

- `.gitignore`

---

### Paso 5: Añadir el campo declarativo active_project

Fijar el proyecto activo de forma declarativa para que `/iniciar` no dependa de heurísticas de recencia.

**Acciones:**

- Editar `contexto/datos-actuales.md` y añadir, cerca del inicio (bajo el título), un bloque claramente identificable:
  ```
  ## Proyecto Activo

  active_project: proyectos/smart-business-decision-support-workspace
  ```
- Documentar en una línea que si se quiere cambiar el foco, se edita este campo; y que si se borra/queda vacío, `/iniciar` cae a detección automática por actividad reciente.

**Archivos afectados:**

- `contexto/datos-actuales.md`

---

### Paso 6: Reescribir /iniciar para leer memoria reciente y priorizar el repo activo

Actualizar `.claude/commands/iniciar.md` conservando su estructura (Paso 0 Bienvenida + Ejecutar + Leer + Resumen) y añadiendo la lógica de memoria y repo activo, con **detección declarativa primero, automática después**.

**Acciones:**

- **Mantener** el Paso 0 (BIENVENIDA.md) tal cual.
- En la sección **"Ejecutar"**, añadir la detección del repo activo en este orden de precedencia:
  1. **Declarativo:** leer el campo `active_project:` de `contexto/datos-actuales.md`. Si existe y no está vacío, **ese es el repo activo** (fin de la detección).
  2. **Automático (fallback):** si el campo no existe/está vacío, listar los `.jsonl` más recientes por subproyecto en `~/.claude/projects/` (por `mtime`) y/o detectar repos con `.governance/PROJECT_STATE.md` para inferir dónde ocurrió el trabajo reciente.
  3. **Fallback explícito:** si nada de lo anterior resuelve, usar `proyectos/smart-business-decision-support-workspace` (SBDSW) mientras sea el proyecto activo.
- En la sección **"Leer"**, añadir:
  - La memoria reciente: `MEMORY.md` y los `.md` más recientes de la carpeta de memoria real (`~/.claude/projects/-mnt-c-...-espacio-de-trabajo-claude/memory/`).
  - Del repo activo (SBDSW por defecto): `.governance/PROJECT_STATE.md` (y `README.md`).
- Añadir una subsección **"Regla de precedencia de contexto"** con texto explícito:
  - "El workspace general (NCA, ASTOR, búsqueda laboral descritos en `contexto/`) es el **contexto de fondo**."
  - "El **repo activo** (declarado en `active_project`, o inferido) es el **contexto principal** de la sesión."
  - "No asumas NCA/ASTOR/búsqueda laboral como foco principal cuando hay un repo activo declarado o más reciente. Ante duda, preguntá cuál es el foco."
- En la sección **"Resumen"**, añadir un punto: "6. Indicá explícitamente cuál es el **repo activo** detectado (y si vino del campo declarativo o de detección automática) y confirmá que ese es el foco (o pedí aclaración)."

**Archivos afectados:**

- `.claude/commands/iniciar.md`

---

### Paso 7: Actualizar CLAUDE.md para reflejar los cambios

**Acciones:**

- En la sección **"/iniciar"**: describir que ahora también lee la memoria reciente y detecta/prioriza el repo activo (declarativo vía `active_project` primero, automático después), con la regla de precedencia workspace vs repo activo.
- En la sección **"Sistema de Memoria Automática"**: documentar el `timeout` de 180s del hook, el nuevo `memory/consolidator.log` (dónde vive, qué registra, rotación a 1 MB con 1 backup `.log.1`), y aclarar que el consolidador marca las sesiones como procesadas aunque no haya extracción.
- No documentar unificación de carpetas (no ocurre).

**Archivos afectados:**

- `CLAUDE.md`

---

### Paso 8: Validación end-to-end

**Acciones:**

- **JSON válido:** parsear `~/.claude/settings.json` (p. ej. `python -c "import json,os; json.load(open(os.path.expanduser('~/.claude/settings.json')))"`) y confirmar `timeout == 180`.
- **Consolidador corre y persiste:** ejecutar manualmente con env explícito, replicando el hook:
  `CLAUDE_PROJECT_DIR=/mnt/c/Users/Usuario/Desktop/espacio-de-trabajo-claude CLAUDE_SESSION_ID=<sesión-actual> python3 scripts/memory_consolidator/main.py`
  - Confirmar que `memory/consolidator.log` se crea/actualiza con timestamps.
  - Confirmar que `memory/processed_log.json` avanza `last_run` a la fecha de hoy y suma el `.jsonl` previo a `processed_jsonl`.
- **Caso `{}`/fallo:** verificar (por el log) que una sesión sin contenido igual queda marcada como procesada y `last_run` avanza.
- **active_project:** confirmar que `contexto/datos-actuales.md` contiene `active_project: proyectos/smart-business-decision-support-workspace`.
- **Rotación del log:** confirmar (por inspección o test) que al superar 1 MB, `consolidator.log` rota a `consolidator.log.1` y se mantiene 1 solo backup.
- **/iniciar:** ejecutar `/iniciar` en una sesión de prueba y confirmar que (a) lee la memoria reciente, (b) nombra el repo activo (SBDSW, vía campo declarativo) y (c) aplica la regla de precedencia sin volver a asumir NCA/ASTOR por defecto.
- **No regresión:** confirmar que el arranque de sesión no se bloquea ni demora de forma perceptible y que no se borraron rutas históricas del `processed_log.json`.
- **git diff antes de commit:** ejecutar `git status` + `git diff` y revisar cada cambio versionado antes de commitear. (Nota: `~/.claude/settings.json` vive fuera del repo → no aparece en el diff; validarlo aparte.)

**Archivos afectados:**

- Ninguno (solo verificación).

---

## Conexiones y Dependencias

### Archivos que Referencian Esta Área

- `CLAUDE.md` → describe `/iniciar` y el "Sistema de Memoria Automática".
- `~/.claude/settings.json` → dispara `main.py` en `SessionStart`.
- `scripts/memory_consolidator/{jsonl_processor,memory_writer,skill_evolver,doc_processor}.py` → importados por `main.py` (no se modifican).
- `memory/processed_log.json`, `memory/extraction_prompt.md`, `memory/inbox/` → estado del consolidador (ruta A).
- `~/.claude/projects/-mnt-c-.../memory/MEMORY.md` y `.md` → memoria real (ruta B), leída por `/iniciar`.

### Actualizaciones Necesarias para Consistencia

- `CLAUDE.md` (Paso 6) — obligatorio por la instrucción de mantener CLAUDE.md sincronizado.
- `.gitignore` (Paso 4) — condicionado a la pregunta abierta #1.

### Impacto en Flujos de Trabajo Existentes

- **`/iniciar`:** cambia su comportamiento — ahora orienta la sesión hacia el repo activo. Es un cambio deseado; el resumen de arranque se verá distinto (menos foco en NCA/ASTOR por defecto).
- **Arranque de sesión:** el hook puede tardar hasta ~180s si hay una sesión previa grande que procesar; sigue siendo no bloqueante (corre en background del `SessionStart`). El log permite diagnosticar demoras.
- **Consolidador:** avanza `last_run` de forma consistente; deja de reintentar sesiones vacías.

---

## Lista de Validación

- [ ] `~/.claude/settings.json` es JSON válido y el hook del consolidador tiene `timeout: 180`.
- [ ] `main.py` marca el `.jsonl` previo como procesado y actualiza `last_run` aunque la extracción sea `{}` o falle.
- [ ] `memory/consolidator.log` se crea y registra hitos con timestamp; un fallo de logging no rompe el consolidador.
- [ ] Ejecución manual del consolidador avanza `last_run` a la fecha de hoy y no borra rutas históricas del `processed_log.json`.
- [ ] `.claude/commands/iniciar.md` lee memoria reciente + detecta el repo activo + incluye la regla de precedencia.
- [ ] `/iniciar` en sesión de prueba nombra SBDSW como repo activo y no asume NCA/ASTOR/búsqueda laboral como foco principal.
- [ ] `CLAUDE.md` actualizado (sección `/iniciar` y "Sistema de Memoria Automática").
- [ ] `.gitignore` cubre `consolidator.log` (o se documentó la decisión de versionarlo).
- [ ] No se unificaron las carpetas `memory/`, no se tocó el harness, no se cambió la arquitectura del consolidador.

---

## Criterios de Éxito

La implementación está completa cuando:

1. Tras una sesión real, `memory/processed_log.json` muestra `last_run` con fecha ≥ 2026-07-09 y el `.jsonl` previo listado, **sin** haberse borrado ninguna ruta histórica.
2. `memory/consolidator.log` contiene el rastro de al menos una ejecución con su resultado (`extraído` / `sin contenido` / `error`), demostrando observabilidad.
3. El hook `SessionStart` completa dentro de los 180s sin ser matado (verificable por el cierre registrado en el log).
4. `/iniciar` produce un resumen que identifica explícitamente el repo activo (SBDSW) como contexto principal y trata NCA/ASTOR/búsqueda laboral como fondo, salvo pedido explícito.
5. Se respetaron todos los "No hacer": sin unificar `memory/`, sin tocar el harness, sin cambiar la arquitectura del consolidador, sin borrar histórico del log.

---

## Notas

- **Doble carpeta `memory/` (deuda conocida, fuera de alcance):** el consolidador escribe estado en la ruta A (workspace) y contexto en la ruta B (`~/.claude/projects/...`). Este plan la respeta a propósito. Una futura unificación merece su propio plan (`/crear-plan`).
- **Inconsistencia cosmética:** varios mensajes/docstrings dicen `extraction_skills.md` pero la constante real es `extraction_prompt.md` (que existe y funciona). No es bug; se puede limpiar en un pase futuro, no en este plan.
- **Detección de repo activo:** SBDSW se nombra por pedido explícito, pero conviene revisar la pregunta abierta #2 (automática vs declarativa) para que `/iniciar` no quede atado a un repo cuando el foco cambie.
- **Presupuesto de tiempo:** si aun con 180s el hook se corta, la causa sería la lentitud de `claude -p` anidado; el log lo evidenciaría y habilitaría un plan siguiente (p. ej. mover la extracción a Haiku vía SDK con `.env`, que hoy no existe).
