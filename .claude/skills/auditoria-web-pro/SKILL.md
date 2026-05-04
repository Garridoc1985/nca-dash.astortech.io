---
name: auditoria-web-pro
description: "Auditoría web integral + diseño frontend. Analiza 8 dimensiones (performance, SEO, SEM, diseño, UX/UI, contenido, seguridad, conversión), genera reportes .docx/.pdf en el Escritorio, redacta emails de outreach, y crea/mejora interfaces web con diseño de producción. Usa cuando el usuario pida: auditar/analizar un sitio web, revisar una URL, evaluar SEO/rendimiento/seguridad, generar reporte de auditoría, construir componentes o páginas web, mejorar diseño frontend, rediseñar una landing page, 'analiza esta URL', 'audita mi web', 'crea un componente/página'. Español e inglés."
---

# Auditoría Web Pro — Auditoría + Diseño Frontend

Skill unificada con tres capacidades:
1. **Auditar** — Análisis de 8 dimensiones de cualquier URL
2. **Reportar** — Reporte .docx/.pdf profesional (Brand ASTOR · astortech.io)
3. **Diseñar** — Crear o mejorar interfaces web con diseño de producción

---

## Módulo 1: Auditoría Web (8 Dimensiones)

### Flujo de ejecución

1. Usar `WebFetch` para obtener el HTML de la URL
2. Analizar las 8 dimensiones con el scoring rubric en `.claude/skills/auditoria-web-pro/references/scoring-rubric.md`
3. (Opcional) Ejecutar script técnico si está disponible en el proyecto:
   ```bash
   python scripts/web_audit.py "<URL>" "/tmp/audit_output"
   cat /tmp/audit_output/audit_metrics.json
   ```
4. Generar reporte siguiendo `.claude/skills/auditoria-web-pro/references/report-template.md`

### Las 8 dimensiones

| # | Dimensión | Peso | Qué evalúa |
|---|-----------|------|-------------|
| 1 | Performance & Carga | 15% | HTML size, DOM, render-blocking, lazy loading, scripts terceros |
| 2 | SEO On-Page | 15% | Title, meta desc, headings, canonical, OG, Schema.org, alt |
| 3 | SEM & Tracking | 10% | GTM, GA4, píxeles (Meta, TikTok, LinkedIn), remarketing |
| 4 | Diseño & Responsividad | 15% | Viewport, media queries, framework CSS, imágenes responsivas |
| 5 | UX/UI & Accesibilidad | 15% | Navegación, ARIA, formularios, skip links, cookie consent |
| 6 | Calidad del Contenido | 10% | Palabras, ratio texto/HTML, estructura, multimedia |
| 7 | Seguridad Técnica | 10% | HTTPS, mixed content, SRI, CSP, form actions |
| 8 | Optimización Conversión | 10% | CTAs, trust badges, testimonios, WhatsApp, chat, formularios |

**Puntaje global:**
```
Score = (Perf×0.15) + (SEO×0.15) + (SEM×0.10) + (Diseño×0.15) +
        (UX×0.15) + (Contenido×0.10) + (Seguridad×0.10) + (Conv×0.10)
```

**Escala:** A+(95-100) · A(90-94) · B+(85-89) · B(75-84) · C+(70-74) · C(60-69) · D(40-59) · F(0-39)

Por dimensión: asignar puntaje + 3-5 hallazgos (✅ fortalezas, ⚠️ advertencias, ❌ problemas) + 2-4 recomendaciones con prioridad Alta/Media/Baja.

**Modo comparativo:** Si el usuario entrega varias URLs, incluir tabla comparativa lado a lado + análisis de brechas.

---

## Módulo 2: Generación de Reporte

### Flujo completo (ejecutar siempre al auditar una URL)

1. Completar análisis raw de las 8 dimensiones
2. **LEER `references/report-template.md` COMPLETO** — ANTES de escribir una sola línea de HTML
3. Generar HTML visual → `output/auditoria-[dominio]-[fecha].html`
4. Generar `.docx` con python-docx → `C:\Users\Usuario\Desktop\Auditoria web Skills\`
5. Convertir a PDF con docx2pdf → misma carpeta
6. Confirmar las 3 rutas al usuario

```python
# Template de generación — adaptar con datos reales
from docx2pdf import convert
# Crear DATOS_[DOMINIO] con resultados del análisis
# Ejecutar: python scripts/generar_informe_[dominio]-[fecha].py
```

Usar `.claude/skills/auditoria-web-pro/references/generar_informe_auditoria.py` como template base. Copiar y poblar con datos reales.

### ⚠️ REGLA CRÍTICA — Generación del HTML

**El CSS del reporte DEBE ser copiado VERBATIM desde `references/report-template.md`.**
**NO inventar CSS. NO minificar. NO abreviar variables. NO simplificar clases.**

El HTML de referencia visual es `output/auditoria-upset-20260330.html`.
Todo reporte generado DEBE tener exactamente estos elementos:

| Elemento | Clase CSS | ¿Obligatorio? |
|----------|-----------|---------------|
| Noise texture grain | `body::before` con SVG fractal | ✅ Sí |
| Top bar de marca | `.topbar` + `.topbar-brand` + `.topbar-meta` | ✅ Sí |
| Hero dark (fondo obsidiana) | `.hero` con grid 2 columnas | ✅ Sí |
| Gauge SVG animado | `.gauge-wrap` con `gaugeReveal` animation | ✅ Sí |
| CSS variables completas | `--obsidiana`, `--obsidiana-deep`, `--oro`, etc. | ✅ Sí |
| Score cards con `::before` | `.score-card.color-[clase]::before` | ✅ Sí |
| Animaciones fadeUp en cards | `animation-delay` por nth-child | ✅ Sí |
| Gold rule divisor | `.gold-rule` | ✅ Sí |
| Radar con leyenda lateral | `.radar-layout` grid | ✅ Sí |
| Dimensions en grid 2 col | `.dimension` grid 180px 1fr | ✅ Sí |
| Roadmap en fondo obsidiana | `.roadmap-section` | ✅ Sí |
| Footer dark | `footer` con `.footer-brand` | ✅ Sí |

**PROHIBIDO en el HTML:**
- CSS minificado (variables como `--ob`, `--bl`, `--pie`)
- Inline styles para lo que ya tiene clase en el template
- Secciones faltantes (topbar, noise, gold-rule, roadmap dark)
- Clases simplificadas que no existen en el CSS canónico

### Sistema de diseño (Brand Grupo Atlas)

- **Paleta:** Obsidiana #1A1A18, Oro Atlas #C4963A, Blanco Cálido #FAF8F4
- **Tipografía Word:** Arial — Título 18pt Bold, H1 14pt Bold, H2 12pt Bold, Cuerpo 11pt, Tablas 10pt
- **Estructura .docx:** Portada → Resumen Ejecutivo → 8 secciones de dimensión → Roadmap → Conclusiones → Notas Metodológicas
- **Márgenes:** 2.5cm · Interlineado: 1.15 cuerpo, 1.0 tablas · Salto de página antes de cada H1

### Nomenclatura de archivos

- `[dominio]` = dominio extraído de la URL (ej: "atlas.cl" → "atlas")
- `[fecha]` = YYYYMMDD
- Ejemplo: `auditoria-atlas-20260328.docx`

---

## Módulo 3: Diseño Frontend

### Cuándo usar este módulo

Activar cuando el usuario pide: crear componentes, páginas o apps web; mejorar o rediseñar una interfaz; proponer mejoras visuales basadas en la auditoría.

### Proceso de diseño

Antes de codear, definir dirección estética:
- **Propósito:** ¿Qué problema resuelve? ¿Quién lo usa?
- **Tono:** Elegir una dirección clara — minimalista brutal, maximalista, retro-futurista, editorial, luxury, orgánico, etc.
- **Diferenciador:** ¿Qué hace esta interfaz MEMORABLE?

Luego implementar código funcional, production-grade (HTML/CSS/JS, React, Vue, etc.).

### Guías de diseño

- **Tipografía:** Fuentes con carácter — evitar Arial, Inter, Roboto, system fonts genéricas. Combinar display distinctive + cuerpo refinado.
- **Color:** CSS variables, paleta cohesiva. Colores dominantes con acentos fuertes > paleta tímida distribuida.
- **Motion:** Animaciones CSS-only preferidas. Un page load bien orquestado > micro-interacciones dispersas. Scroll-triggering y hover que sorprendan.
- **Composición espacial:** Layouts inesperados. Asimetría. Superposición. Flujo diagonal. Elementos que rompen la grilla.
- **Fondos y texturas:** Profundidad y atmósfera — gradient meshes, noise textures, patrones geométricos, sombras dramáticas, grain overlays.

**Prohibido:** Gradientes púrpura sobre blanco, Space Grotesk por defecto, layouts genéricos de IA. Cada diseño debe ser único para su contexto.

**Regla clave:** Maximalismo requiere código elaborado con animaciones extensas. Minimalismo requiere precisión en spacing, tipografía y detalles sutiles. La elegancia viene de ejecutar la visión correctamente.

---

## Módulo 4: Email de Outreach

### Tipos de email

**Envío de resultados al cliente:**
```
Asunto: Auditoría [dominio] — Diagnóstico completo y plan de acción

Hola [Nombre], completamos la auditoría de [dominio]. Obtuvo [score]/100 ([calificación]).
[2-3 insights clave en 1-2 oraciones]. Adjunto el reporte con las 8 dimensiones y roadmap de mejoras.
¿Podemos agendar 30 minutos esta semana para revisar los hallazgos?
```

**Cold outreach (framework AIDA):**
```
Asunto: [Algo específico que noté en dominio.com]

Hola [Nombre], revisé [dominio] y noté [1 hallazgo observable concreto].
[Quién eres + qué haces + por qué es relevante para ellos]
¿Te interesaría un diagnóstico completo gratuito? Evalúo 8 dimensiones y entrego reporte con acciones priorizadas.
```

**Reglas:** < 125 palabras (cold) / < 150 (resultados). Un solo CTA. Personalizar asunto. No abrir con "Me presento". No usar "Estimado señor/señora".

Variables requeridas antes de redactar: destinatario, empresa, objetivo, contexto, diferenciador.

---

## Notas

- La auditoría analiza HTML estático. Para SPAs (React/Next/Vue), mencionar limitación.
- Siempre recomendar complementar con Google PageSpeed Insights, GTmetrix, Ahrefs o Semrush.
- Verificar canal WhatsApp (relevante en LATAM).
- Idioma: español por defecto. Si el usuario escribe en inglés, generar todo en inglés.

## Archivos de referencia

- `.claude/skills/auditoria-web-pro/references/scoring-rubric.md` — Criterios de scoring (leer SIEMPRE antes de puntuar)
- `.claude/skills/auditoria-web-pro/references/report-template.md` — Sistema de diseño HTML/CSS/SVG (leer SIEMPRE antes de generar HTML)
- `.claude/skills/auditoria-web-pro/references/generar_informe_auditoria.py` — Template .docx + PDF (copiar y adaptar por auditoría)
- `scripts/web_audit.py` — Extracción de métricas técnicas desde HTML (opcional — no incluido, debe existir en el proyecto)
