---
name: auditoria-performance-report
description: "Skill integradora que combina auditoría técnica web (8 dimensiones), auditoría SEO estratégica (keywords, gaps de contenido, competidores) y análisis de performance de marketing (canales, campañas, tendencias) en un diagnóstico cruzado único. Determina si un problema de métricas tiene causa técnica (sitio), estratégica (SEO/contenido/campaña) o mixta. Usar cuando: (1) se tienen URL + métricas de marketing; (2) el organic bajó y no está claro si es técnico o estratégico; (3) se quiere saber si el sitio, el SEO o la campaña está limitando los resultados; (4) se necesita un plan de acción integrado con correcciones técnicas, mejoras SEO y ajustes de campaña en un único roadmap. No usar si solo hay URL → auditoria-web-pro o seo-audit. No usar si solo hay métricas → performance-report."
---

# Auditoría Performance Report — Skill Integradora

Orquesta tres diagnósticos complementarios en un ciclo completo:

| Skill | Qué aporta |
|---|---|
| **`auditoria-web-pro`** | Estado técnico del sitio: 8 dimensiones (performance, SEO on-page, tracking, diseño, UX, contenido, seguridad, conversión) |
| **`seo-audit`** | Estrategia SEO: keywords, gaps de contenido, competidores, Core Web Vitals, structured data |
| **`performance-report`** | Resultados de marketing en el tiempo: canales, campañas, tendencias, atribución |

Esta skill NO repite el contenido de ninguna de las tres. Agrega la lógica que las une.

---

## Cuándo usar esta skill vs. las individuales

| Situación | Skill correcta |
|---|---|
| Solo tengo una URL para auditar técnicamente | `auditoria-web-pro` |
| Solo quiero investigar keywords o competidores SEO | `seo-audit` |
| Solo tengo métricas de campañas/canales | `performance-report` |
| Tengo URL + métricas de marketing | **Esta skill** |
| El organic bajó y no sé si es técnico o de estrategia SEO | **Esta skill** |
| El performance bajó y no sé si es el sitio o la campaña | **Esta skill** |
| Quiero un plan que integre técnica + SEO + campaña | **Esta skill** |

---

## Insumos requeridos

Solicitar al usuario antes de comenzar:

**A) URL(s)** — sitio principal o landing page de campaña a analizar.

**B) Datos de marketing** — período, métricas por canal (datos pegados, CSV, números clave), período de comparación, objetivo de cada canal.

**C) Contexto SEO** (si es relevante) — keywords objetivo actuales, competidores conocidos, ¿hubo cambios en el sitio (migración, rediseño)?

**D) Contexto de negocio** — ¿hubo cambios en campañas en el período? ¿hay una hipótesis inicial sobre qué está fallando?

---

## Flujo de ejecución

### Paso 1 — Auditoría técnica del sitio
Ejecutar **`auditoria-web-pro`** (Módulo 1) sobre la URL. Registrar puntaje por dimensión — se usa en el diagnóstico cruzado.

### Paso 2 — Auditoría SEO estratégica *(condicional)*
Ejecutar **`seo-audit`** cuando se cumpla al menos una de estas condiciones:
- Las métricas de marketing incluyen organic sessions, keyword rankings, CTR orgánico o backlinks
- El usuario quiere analizar competidores o gaps de contenido
- El tráfico orgánico está "At Risk" u "Off Track"
- Hubo una migración o rediseño reciente del sitio

Tipos de `seo-audit` a ejecutar según contexto:
- Organic bajando sin causa técnica clara → **Full site audit + Competitor SEO comparison**
- Tráfico estable pero conversión orgánica baja → **Content gap analysis + On-page**
- Entrada a nuevo mercado/nicho → **Keyword research + Content gap analysis**
- Post-migración → **Technical SEO check + Crawlability**

### Paso 3 — Performance de marketing
Ejecutar **`performance-report`** con los datos provistos. Registrar métricas por canal y su estado (On Track / At Risk / Off Track).

### Paso 4 — Diagnóstico cruzado
**LEER `references/diagnostico-cruzado.md` COMPLETO antes de este paso.**

Usar las tablas del archivo para identificar, por cada métrica Off Track o At Risk:
- Causa probable: Técnica (sitio) / SEO estratégica / Estratégica (campaña) / Mixta
- Evidencia: qué score técnico, qué hallazgo SEO y qué métrica de marketing lo sustentan
- Impacto estimado si se corrige: Alto / Medio / Bajo

### Paso 5 — Diagnóstico unificado
Presentar en cuatro capas:

**Capa 1 — Score técnico (auditoria-web-pro)**
```
Score global: [X]/100 ([calificación])
Dimensiones críticas (< 70): [lista]
Dimensiones fuertes (≥ 85): [lista]
```

**Capa 2 — Estado SEO estratégico (seo-audit)**
```
Keyword gaps críticos: [lista]
Problemas técnicos SEO: [lista de Fail/Warning]
Ventaja/desventaja vs competidores: [resumen]
```

**Capa 3 — Performance de marketing (performance-report)**
```
On Track:  [lista de métricas]
At Risk:   [lista de métricas]
Off Track: [lista de métricas]
```

**Capa 4 — Causalidad cruzada**
Para cada métrica Off Track o At Risk:
- Causa probable: Técnica / SEO estratégica / Estratégica / Mixta
- Evidencia: [hallazgo técnico o SEO] + [métrica en valor concreto]
- Impacto estimado si se corrige: Alto / Medio / Bajo

### Paso 6 — Plan de acción integrado
Un único roadmap que combina acciones técnicas, SEO y de campaña, sin duplicaciones, ordenado por impacto real sobre resultados de negocio:

| Prioridad | Criterio |
|---|---|
| **P1 — Urgente** | Problema técnico causando pérdida activa de conversiones o datos; tracking roto; penalización activa |
| **P2 — Esta semana** | Métrica Off Track con causa técnica o SEO identificada y solución de baja complejidad |
| **P3 — Este mes** | Gaps de contenido SEO de alta oportunidad; ajustes estratégicos de campaña |
| **P4 — Este trimestre** | Mejoras técnicas de alta complejidad; clusters de contenido; link-building; rediseño |

Formato de salida:

| Acción | Origen | Dimensión/hallazgo afectado | Métrica que mejora | Prioridad | Esfuerzo |
|---|---|---|---|---|---|
| [acción concreta] | Técnica / SEO / Campaña | [dimensión o hallazgo] | [métrica] | P1/P2/P3/P4 | Alto/Medio/Bajo |

---

## Output del reporte

**Siempre:** Diagnóstico integrado completo en el chat (tablas de los pasos 5 y 6).

**Si el usuario lo solicita — Documento:** Extender el reporte `.docx/.pdf` de `auditoria-web-pro` con tres secciones adicionales:
- **Sección 9:** Auditoría SEO Estratégica (keyword opportunities, content gaps, competitor comparison)
- **Sección 10:** Dashboard de Performance de Marketing (métricas por canal + período)
- **Sección 11:** Diagnóstico Cruzado + Plan de Acción Integrado

Usar el mismo pipeline de `auditoria-web-pro`:
- CSS y estructura desde `references/report-template.md` de esa skill
- Template `.docx` desde `references/generar_informe_auditoria.py` de esa skill
- Carpeta destino: `C:\Users\Usuario\Desktop\Auditoria web Skills\`
- Nomenclatura: `auditoria-performance-[dominio]-[fecha].docx`

---

## Ciclo de uso recomendado

```
TRIMESTRAL  →  auditoria-web-pro          (fotografía técnica del sitio)
              + seo-audit                 (benchmark SEO vs competidores)
MENSUAL     →  performance-report         (resultados de canales de marketing)
ANTE ANOMALÍAS → auditoria-performance-report  (diagnóstico cruzado + causa raíz)
POST-CAMBIOS →  performance-report        (validar si los cambios mejoraron métricas)
```

---

## Notas

- Si el usuario solo tiene URL: redirigir a `auditoria-web-pro` o `seo-audit` según necesidad.
- Si el usuario solo tiene métricas: redirigir a `performance-report`.
- El Paso 2 (seo-audit) es condicional — no es obligatorio si no hay métricas orgánicas involucradas.
- El diagnóstico cruzado requiere mínimo métricas de 1 canal + score de 3 dimensiones técnicas para ser concluyente.
- Para SPAs (React/Next/Vue): la auditoría técnica analiza HTML estático — mencionar la limitación.
- Complementar siempre con Google Search Console, PageSpeed Insights y herramientas de analítica para validar el diagnóstico.
