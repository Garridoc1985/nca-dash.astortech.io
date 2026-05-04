# Auditoría Web Pro

> Skill autosuficiente de **auditoría web técnica + diseño frontend + outreach**. Analiza una URL en 8 dimensiones, genera un reporte profesional `.docx/.pdf` con identidad de marca, y opcionalmente crea componentes/páginas web de producción.

---

## Para qué sirve

Esta skill resuelve cuatro necesidades en un solo flujo:

1. **Diagnóstico técnico de una URL** — Evalúa cualquier sitio web en 8 dimensiones críticas (performance, SEO on-page, tracking, diseño, UX, contenido, seguridad, conversión) y genera un puntaje global de 0–100 con calificación A+/A/B+/B/C+/C/D/F.

2. **Generación de reportes profesionales** — Produce un entregable visual (HTML + `.docx` + PDF) con sistema de diseño de marca **Grupo Atlas / ASTOR Tech** (paleta obsidiana/oro, tipografía Arial, gauges SVG animados).

3. **Diseño frontend de producción** — Cuando el usuario lo pide, genera componentes, landings o apps web con HTML/CSS/JS, React o Vue, siguiendo principios de diseño memorable (no genérico).

4. **Email de outreach** — Redacta emails cortos para enviar resultados al cliente o para cold outreach con framework AIDA, en menos de 150 palabras.

**Casos típicos de uso:**
- "Audita esta URL: ejemplo.com"
- "Compará esta web con la de mi competencia"
- "Generá un reporte profesional de la auditoría"
- "Mejorá el diseño de esta landing"
- "Redactame un email para enviarle la auditoría al cliente"

---

## Cómo se ejecuta

### Activación

Claude Code activa la skill automáticamente al detectar pedidos como:
- "auditar / analizar / revisar / evaluar [URL]"
- "audita esta web", "analiza este sitio"
- "generar reporte de auditoría"
- "crear componente / página web"
- "mejorar diseño frontend"

### Flujo de ejecución (auditoría)

```
1. WebFetch del HTML de la URL
2. Análisis de las 8 dimensiones según scoring-rubric.md
3. (Opcional) Ejecución de scripts/web_audit.py para métricas técnicas
4. Cálculo del puntaje global ponderado
5. Generación del HTML visual en output/auditoria-[dominio]-[fecha].html
6. Generación del .docx con python-docx
7. Conversión a PDF con docx2pdf
8. Confirmación de las 3 rutas al usuario
```

### Las 8 dimensiones evaluadas

| # | Dimensión | Peso |
|---|-----------|------|
| 1 | Performance & Carga | 15% |
| 2 | SEO On-Page | 15% |
| 3 | SEM & Tracking | 10% |
| 4 | Diseño & Responsividad | 15% |
| 5 | UX/UI & Accesibilidad | 15% |
| 6 | Calidad del Contenido | 10% |
| 7 | Seguridad Técnica | 10% |
| 8 | Optimización de Conversión | 10% |

**Fórmula del score global:**
```
Score = (Perf×0.15) + (SEO×0.15) + (SEM×0.10) + (Diseño×0.15)
      + (UX×0.15) + (Contenido×0.10) + (Seg×0.10) + (Conv×0.10)
```

### Outputs generados

| Archivo | Ubicación | Propósito |
|---------|-----------|-----------|
| `auditoria-[dominio]-[fecha].html` | `output/` | Reporte visual web |
| `auditoria-[dominio]-[fecha].docx` | `C:\Users\Usuario\Desktop\Auditoria web Skills\` | Entregable Word |
| `auditoria-[dominio]-[fecha].pdf` | `C:\Users\Usuario\Desktop\Auditoria web Skills\` | Entregable PDF |

---

## Cuándo ejecutarla

| Situación | ¿Usar esta skill? |
|-----------|-------------------|
| Tengo una URL y necesito diagnóstico técnico | **Sí** |
| Quiero entregar un reporte profesional al cliente | **Sí** |
| Necesito comparar 2+ sitios web (modo comparativo) | **Sí** |
| Quiero crear o rediseñar una interfaz web | **Sí** |
| Necesito redactar email de outreach con auditoría | **Sí** |
| Tengo URL **+ métricas reales de campañas** y quiero diagnóstico cruzado | **No → usar `auditoria-performance-report`** |
| Solo necesito investigar keywords o competidores SEO | **No → usar `seo-audit`** |
| Solo tengo métricas de marketing | **No → usar `performance-report`** |

### Ciclo recomendado

- **Trimestral:** Auditoría técnica completa para fotografía del estado del sitio.
- **Post-rediseño / migración:** Auditoría de validación.
- **Pre-campaña:** Auditoría de la landing para asegurar conversión óptima.
- **Pitch comercial:** Auditoría gratuita como hook de outreach.

---

## Stack técnico

### Lenguajes y entornos
- **Python 3** — Generación de reportes y scripts de extracción
- **HTML5 + CSS3** — Reportes visuales y diseño frontend
- **JavaScript / React / Vue** — Cuando se invoca el módulo de diseño

### Librerías Python
| Librería | Uso |
|----------|-----|
| `python-docx` | Generación del archivo `.docx` con estructura, estilos y tablas |
| `docx2pdf` | Conversión `.docx → .pdf` (requiere Word instalado en Windows) |
| `requests` / `WebFetch` | Descarga del HTML de la URL auditada |
| `beautifulsoup4` (opcional) | Parseo del DOM en `scripts/web_audit.py` |

### Sistema de diseño (Brand Grupo Atlas / ASTOR Tech)
- **Paleta:** Obsidiana `#1A1A18` · Oro Atlas `#C4963A` · Blanco Cálido `#FAF8F4`
- **Tipografía Word:** Arial — Título 18pt, H1 14pt, H2 12pt, Cuerpo 11pt
- **Tipografía Web:** CSS variables canónicas (no minificar, no abreviar)
- **Elementos visuales obligatorios en el HTML:** noise texture grain (SVG fractal), top bar de marca, hero dark obsidiana, gauge SVG animado con `gaugeReveal`, score cards con `::before`, animaciones fadeUp, gold rule divisor, radar con leyenda lateral, roadmap dark, footer dark.

---

## Arquitectura

### Estructura de archivos

```
.claude/skills/auditoria-web-pro/
├── SKILL.md                              # Definición principal de la skill
├── README.md                             # Este archivo (documentación pública)
└── references/
    ├── scoring-rubric.md                 # Criterios de scoring de las 8 dimensiones
    ├── report-template.md                # Sistema de diseño HTML/CSS/SVG canónico
    └── generar_informe_auditoria.py      # Template Python para generar .docx + PDF
```

### Pipeline de ejecución

```
┌─────────────────┐
│  Input: URL     │
└────────┬────────┘
         ▼
┌─────────────────────────────────────────┐
│  Módulo 1: Auditoría Técnica            │
│  - WebFetch → HTML                      │
│  - Análisis 8 dimensiones               │
│  - Lectura: scoring-rubric.md           │
│  - Score ponderado + hallazgos          │
└────────┬────────────────────────────────┘
         ▼
┌─────────────────────────────────────────┐
│  Módulo 2: Generación de Reporte        │
│  - Lectura: report-template.md          │
│  - HTML visual → output/                │
│  - .docx (python-docx)                  │
│  - PDF (docx2pdf)                       │
│  - Carpeta destino fija (Desktop)       │
└────────┬────────────────────────────────┘
         ▼
┌─────────────────────────────────────────┐
│  Módulo 3 (opcional): Diseño Frontend   │
│  - Tono + propósito + diferenciador     │
│  - HTML/CSS/JS o React/Vue              │
│  - Diseño memorable, no genérico        │
└────────┬────────────────────────────────┘
         ▼
┌─────────────────────────────────────────┐
│  Módulo 4 (opcional): Email Outreach    │
│  - Resultados al cliente                │
│  - Cold outreach (AIDA, < 125 palabras) │
└─────────────────────────────────────────┘
```

### Reglas críticas de implementación

1. **Lectura obligatoria antes de actuar:**
   - `scoring-rubric.md` antes de puntuar.
   - `report-template.md` antes de generar HTML.

2. **CSS verbatim:** El CSS del reporte HTML debe copiarse **literal** desde `report-template.md`. Prohibido minificar, abreviar variables o simplificar clases.

3. **Limitaciones conocidas:**
   - Analiza **HTML estático** — para SPAs (React/Next/Vue) la auditoría es parcial; mencionar la limitación al usuario.
   - Recomendar siempre complementar con Google PageSpeed Insights, GTmetrix, Ahrefs o Semrush.

4. **Idioma:** Por defecto español. Si el usuario escribe en inglés, todo el output va en inglés.

---

## Referencias internas

- [SKILL.md](./SKILL.md) — Definición técnica completa para Claude Code
- [scoring-rubric.md](./references/scoring-rubric.md) — Criterios de puntaje
- [report-template.md](./references/report-template.md) — Sistema de diseño visual
- [generar_informe_auditoria.py](./references/generar_informe_auditoria.py) — Template del generador
