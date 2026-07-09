# CLAUDE.md

Este archivo provee instrucciones a Claude Code (claude.ai/code) cuando trabaja con código en este repositorio.

---

## Idioma

**Siempre responder en español.** Todas las respuestas, explicaciones, resúmenes y comentarios deben estar en español, independientemente del idioma en que el usuario escriba.

---

## Qué Es Esto

Este es un **Claude Workspace Template** — un entorno estructurado diseñado para trabajar con Claude Code como un potente asistente agente entre sesiones. El usuario abrirá nuevas sesiones de Claude Code repetidamente, usando `/iniciar` al comienzo de cada una para cargar contexto esencial sin sobrecargar el contexto.

**Este archivo (CLAUDE.md) es la base.** Se carga automáticamente al inicio de cada sesión. Mantenelo actualizado — es la única fuente de verdad sobre cómo Claude debe entender y operar dentro de este workspace.

---

## La Relación Claude-Usuario

Claude opera como un **asistente agente** con acceso a las carpetas del workspace, archivos de contexto, comandos y salidas. La relación es:

- **Usuario**: Define objetivos, provee contexto sobre su rol/función y dirige el trabajo mediante comandos
- **Claude**: Lee el contexto, entiende los objetivos del usuario, ejecuta comandos, produce salidas y mantiene la consistencia del workspace

Claude siempre debe orientarse a través de `/iniciar` al inicio de la sesión, y luego actuar con plena conciencia de quién es el usuario, qué está tratando de lograr y cómo este workspace lo apoya.

---

## Estructura del Workspace

```
.
├── CLAUDE.md              # Este archivo — contexto principal, siempre cargado
├── .claude/
│   └── commands/          # Comandos que Claude puede ejecutar
│       ├── iniciar.md      # /iniciar — inicialización de sesión
│       ├── crear-plan.md   # /crear-plan — crear planes de implementación
│       └── implementar.md  # /implementar — ejecutar planes
├── contexto/              # Contexto de fondo sobre el usuario y el proyecto
│                          # (El usuario debe completar con rol, objetivos, estrategias)
├── planes/                # Planes de implementación creados por /crear-plan
├── salidas/               # Productos de trabajo, herramientas y entregables
├── referencia/            # Plantillas, ejemplos, patrones reutilizables
└── scripts/               # Scripts de automatización auxiliares (si aplica)
```

**Directorios principales:**

| Directorio    | Propósito                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------- |
| `contexto/`   | Quién es el usuario, su rol, prioridades actuales, estrategias. Leído por `/iniciar`.           |
| `planes/`     | Planes de implementación detallados. Creados por `/crear-plan`, ejecutados por `/implementar`.  |
| `salidas/`    | Entregables, análisis, reportes, herramientas y productos de trabajo.                           |
| `referencia/` | Docs de ayuda, plantillas y patrones para asistir en distintos flujos de trabajo.               |
| `scripts/`    | Scripts de automatización auxiliares (bash, python, etc.) que soporten otros flujos.            |

---

## Comandos

### /iniciar

**Propósito:** Inicializar una nueva sesión con plena conciencia del contexto.

Ejecutalo al inicio de cada sesión. Claude:

1. Detectará el **repo activo** con precedencia: (a) campo `active_project:` en `contexto/datos-actuales.md` (declarativo, manda), (b) actividad reciente de `.jsonl` (automático), (c) SBDSW como fallback explícito
2. Leerá CLAUDE.md, los archivos de contexto y la **memoria reciente** (`MEMORY.md` + `.md` recientes)
3. Resumirá su comprensión del usuario, el workspace y los objetivos
4. **Priorizará el repo activo como contexto principal** — no asume NCA/ASTOR/búsqueda laboral por defecto si hay un repo activo declarado o más reciente
5. Confirmará que está listo para asistir

### /crear-plan [pedido]

**Propósito:** Crear un plan de implementación detallado antes de hacer cambios.

Usalo cuando se agrega nueva funcionalidad, comandos, scripts, o se hacen cambios estructurales. Produce un documento de plan exhaustivo en `planes/` que captura contexto, justificación y tareas paso a paso.

Ejemplo: `/crear-plan agregar comando de análisis de competidores`

### /implementar [ruta-al-plan]

**Propósito:** Ejecutar un plan creado por /crear-plan.

Lee el plan, ejecuta cada paso en orden, valida el trabajo y actualiza el estado del plan.

Ejemplo: `/implementar planes/2026-01-28-comando-analisis-competidores.md`

---

## Instrucción Crítica: Mantener Este Archivo

**Siempre que Claude haga cambios en el workspace, DEBE considerar si CLAUDE.md necesita actualizarse.**

Después de cualquier cambio — agregar comandos, scripts, flujos de trabajo, o modificar la estructura — preguntarse:

1. ¿Este cambio agrega nueva funcionalidad que los usuarios necesitan conocer?
2. ¿Modifica la estructura del workspace documentada arriba?
3. ¿Debe listarse un nuevo comando?
4. ¿Necesita `contexto/` nuevos archivos para capturar esto?

Si la respuesta es sí a cualquiera, actualizar las secciones relevantes. Este archivo debe siempre reflejar el estado actual del workspace para que las sesiones futuras tengan contexto preciso.

**Ejemplos de cambios que requieren actualizar CLAUDE.md:**

- Agregar un nuevo comando → agregar a la sección de Comandos
- Crear un nuevo tipo de salida → documentar en Estructura del Workspace o crear una sección
- Agregar un script → documentar su propósito y uso
- Cambiar patrones de flujo de trabajo → actualizar la documentación relevante

---

## Para Usuarios que Descargan Esta Plantilla

Para personalizar este workspace según tus necesidades:

1. Completá los documentos de contexto en `contexto/` con tu información, negocio y objetivos
2. Usá `/crear-plan` para planificar cualquier adición o cambio estructural
3. Usá `/implementar` para ejecutar los planes

Esto asegura que todo se mantenga sincronizado — especialmente CLAUDE.md, que siempre debe reflejar el estado actual del workspace.

---

## Aplicaciones Web Python (Flask)

Dos servidores Flask listos para levantar localmente:

### servidor_nca.py — Dashboard Financiero NCA

**Puerto:** 5000 | **Login:** ver `users.json`

**Uso:**
```bash
python -X utf8 servidor_nca.py
# Abre: http://localhost:5000
```

**Flujo:** Login → sube Excel NCA → genera dashboard HTML con 8 módulos financieros → visualiza en el navegador

**Motor:** `.claude/skills/dashboard-financiero-nca/generador_nca.py` (1999 líneas)

**Módulos del dashboard:**
- M1 EERR: Estado de Resultados por sucursal
- M2 Flujo Caja: Proyección mensual 2026 + acumulado
- M3 Ventas: Consolidado histórico 2024-2026
- M4 Detalle Ventas: Tratamientos y transacciones
- M5 RRHH: Gastos de personal 2025 vs 2026
- M6 Gastos Adm/Op: Administrativos y operativos
- M7 Gs No Op + Mkt: No operacionales y marketing
- M8 Conclusiones: Alertas y plan de acción

**Log:** `servidor_nca.log`

**Nota ETL:** Hojas EERR y MARKETING tienen lecturas por índice fijo — no modificar estructura del Excel. Ver `.claude/skills/dashboard-financiero-nca/references/lecturas_fragiles.md`

---

### servidor_ventas.py — Dashboard de Ventas

**Puerto:** 5001 | **Login:** ver `users.json`

**Uso:**
```bash
python -X utf8 servidor_ventas.py
# Abre: http://localhost:5001
```

**Flujo:** Login → sube Excel de ventas (cualquier formato) → normaliza → genera dashboard HTML → visualiza

**Motor:** `.claude/skills/data-analytics-pro/scripts/normalizar_reporte_ventas.py` → `generador_html_ventas.py`

**Log:** `servidor_ventas.log`

---

### Archivos de soporte

| Archivo | Propósito |
|---|---|
| `users.json` | Usuarios y contraseñas para ambos servidores |
| `config.ini` | Ruta por defecto al Excel NCA |
| `uploads/` | Excels subidos temporalmente |
| `output/` | Dashboards HTML generados |

---

## Flujo de Trabajo de Sesión

1. **Inicio**: Ejecutar `/iniciar` para cargar el contexto
2. **Trabajo**: Usar comandos o dirigir a Claude con tareas
3. **Planificar cambios**: Usar `/crear-plan` antes de adiciones significativas
4. **Ejecutar**: Usar `/implementar` para ejecutar los planes
5. **Mantener**: Claude actualiza CLAUDE.md y `contexto/` a medida que el workspace evoluciona

---

## Sistema de Memoria Automática

Al iniciar cada sesión, Claude Code ejecuta automáticamente el consolidador de memoria (`scripts/memory_consolidator/main.py`) vía un hook `SessionStart` en `~/.claude/settings.json` (con `timeout: 180` segundos):

1. **Procesa la sesión anterior** — extrae decisiones, feedback y estado de proyectos del `.jsonl` anterior. La sesión queda **marcada como procesada aunque la extracción devuelva `{}` o falle** (evita reintentos infinitos y hace avanzar `last_run`).
2. **Procesa el inbox/** — analiza archivos nuevos depositados en `memory/inbox/`
3. **Actualiza `memory/`** — crea o actualiza archivos `.md` de memoria con lo extraído

### Log de ejecución

`memory/consolidator.log` — rastro persistente de cada corrida del consolidador (hitos, resultado, errores). **Rotación por tamaño:** al superar 1 MB se renombra a `consolidator.log.1` (se mantiene 1 solo backup). Es log de runtime — está en `.gitignore`, no se versiona.

### Cómo depositar archivos para que Claude los aprenda

Depositar en `memory/inbox/` cualquier archivo que quieras que Claude recuerde:

- Código fuente (`.py`, `.js`, `.ts`, `.sql`)
- Documentos (`.pdf`, `.docx`, `.pptx`)
- Datos (`.xlsx`, `.csv`)

Al abrir la próxima sesión, el archivo se procesa automáticamente y su contexto queda disponible.

**Nota:** No depositar archivos con datos sensibles de clientes.

### Registro de procesamiento

`memory/processed_log.json` — lista de sesiones y archivos ya procesados. Para reprocesar algo, eliminar su entrada del log.

### Dependencias (instalar una vez)

```bash
pip install anthropic openpyxl pandas pdfplumber python-docx python-pptx python-dotenv
```

---

## Notas

- Mantener el contexto mínimo pero suficiente — evitar sobrecarga
- Los planes viven en `planes/` con nombres de archivo con fecha para historial
- Las salidas se organizan por tipo/propósito en `salidas/`
- Los materiales de referencia van en `referencia/` para reutilización
