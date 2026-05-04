# Auditoría Performance Report

> Skill **integradora (orquestadora)** que combina auditoría técnica web (`auditoria-web-pro`), auditoría SEO estratégica (`seo-audit`) y análisis de performance de marketing (`performance-report`) en un único diagnóstico cruzado de causa raíz.

---

## Para qué sirve

Esta skill **no audita por sí sola** — orquesta a otras tres y agrega la lógica que las une. Su valor está en responder una pregunta que ninguna skill individual puede:

> **¿La caída de mis métricas es un problema técnico (sitio), estratégico (SEO/contenido/campaña) o mixto?**

### Diagnósticos típicos que resuelve

| Síntoma | Diagnóstico cruzado |
|---------|---------------------|
| CTR bueno + conversión baja + bounce alto | Sitio lento bloqueando la conversión (causa técnica) |
| Tráfico orgánico cae sin causa técnica | Content gap, pérdida de freshness o competidores con backlinks (causa SEO estratégica) |
| ROAS bajo en paid + landing OK | Problema de campaña (creativo, audiencia, oferta) — no del sitio |
| ROAS bajo + landing lenta | Quality Score caído por performance — causa técnica |
| Datos de atribución inconsistentes | Tracking mal instalado (Dim 3 técnica) — no es la campaña |
| Leads cayendo sin caída en tráfico | Fricción nueva en el embudo (UX/Conversión) |

### Output principal

Un **plan de acción integrado** con prioridades P1–P4 que combina acciones técnicas, SEO y de campaña, sin duplicaciones, ordenadas por impacto real sobre el negocio.

---

## Cómo se ejecuta

### Activación

Claude Code activa la skill al detectar pedidos como:
- "Tengo URL + métricas, querés diagnosticar"
- "El organic bajó pero no sé si es técnico o estratégico"
- "El performance cayó, no sé si es el sitio o la campaña"
- "Necesito un plan integrado técnico + SEO + campaña"

### Insumos requeridos

| Tipo | Qué pedir al usuario |
|------|----------------------|
| **A) URL(s)** | Sitio principal o landing de campaña |
| **B) Datos de marketing** | Métricas por canal, período, comparación, objetivos |
| **C) Contexto SEO** | Keywords objetivo, competidores, cambios recientes (migración/rediseño) |
| **D) Contexto de negocio** | Cambios de campaña, hipótesis inicial |

### Flujo de ejecución (6 pasos)

```
Paso 1 → auditoria-web-pro (Módulo 1)         [obligatorio]
         Score técnico de las 8 dimensiones

Paso 2 → seo-audit                            [condicional]
         Solo si: hay métricas orgánicas, análisis competitivo,
         organic cayendo, o post-migración

Paso 3 → performance-report                   [obligatorio]
         Métricas por canal con estado On/At Risk/Off Track

Paso 4 → Diagnóstico cruzado
         Lectura: references/diagnostico-cruzado.md
         Por cada métrica Off Track / At Risk:
           - Causa probable (Técnica / SEO / Campaña / Mixta)
           - Evidencia (score técnico + hallazgo SEO + métrica)
           - Impacto estimado si se corrige

Paso 5 → Diagnóstico unificado en 4 capas
         Capa 1: Score técnico
         Capa 2: Estado SEO estratégico
         Capa 3: Performance de marketing
         Capa 4: Causalidad cruzada

Paso 6 → Plan de acción integrado
         Roadmap único P1/P2/P3/P4
         | Acción | Origen | Hallazgo | Métrica | Prioridad | Esfuerzo |
```

### Regla de diagnóstico por score técnico

```
Score < 70   → Causa probable: TÉCNICA      (sitio limitando resultado)
Score 70-84  → Causa probable: MIXTA        (técnico + estrategia en paralelo)
Score ≥ 85   → Causa probable: ESTRATÉGICA  (sitio NO es el cuello de botella)
```

### Output del reporte

| Modo | Entregable |
|------|------------|
| **Default** | Diagnóstico integrado completo en el chat (tablas pasos 5 y 6) |
| **A pedido** | `.docx/.pdf` extendido con secciones 9 (SEO), 10 (Performance), 11 (Diagnóstico + Plan), reusando el pipeline de `auditoria-web-pro` |

---

## Cuándo ejecutarla

| Situación | Skill correcta |
|-----------|----------------|
| Solo tengo URL para auditar técnicamente | `auditoria-web-pro` |
| Solo quiero investigar keywords / competidores SEO | `seo-audit` |
| Solo tengo métricas de campañas/canales | `performance-report` |
| **Tengo URL + métricas de marketing** | **Esta skill** |
| **Organic cayó y no sé si es técnico o estrategia** | **Esta skill** |
| **Performance cayó y no sé si es sitio o campaña** | **Esta skill** |
| **Quiero un plan que integre técnica + SEO + campaña** | **Esta skill** |

### Ciclo de uso recomendado

```
TRIMESTRAL      → auditoria-web-pro + seo-audit (fotografía + benchmark)
MENSUAL         → performance-report             (resultados de canales)
ANTE ANOMALÍAS  → auditoria-performance-report   (esta skill — causa raíz)
POST-CAMBIOS    → performance-report             (validar mejoras)
```

### Mínimo viable para que funcione

- **1 canal** con período actual + período de comparación
- **3 dimensiones técnicas** evaluadas (provistas por Paso 1)
- **URL** principal del análisis

Sin estos mínimos, redirigir a las skills individuales.

---

## Stack técnico

### No introduce dependencias propias

Esta skill es **pura orquestación**: reutiliza el stack completo de las 3 skills que combina.

### Stack heredado de las skills orquestadas

| Skill | Stack |
|-------|-------|
| `auditoria-web-pro` | Python 3, `python-docx`, `docx2pdf`, `WebFetch`, HTML/CSS/SVG |
| `seo-audit` | WebFetch, conectores externos (GSC, Ahrefs, Semrush — opcionales) |
| `performance-report` | Conectores marketing analytics (GA4, Meta Ads, Google Ads — opcionales), CSV/manual |

### Fuentes de datos de marketing

| Origen | Cómo obtenerlo |
|--------|----------------|
| **Google Search Console** | Performance → Export CSV |
| **Google Analytics 4** | Reports → Acquisition → Export |
| **Google Ads** | Reports → Predefined → Download CSV |
| **Meta Ads** | Ads Manager → Export Reports |
| **Email (Mailchimp/Brevo)** | Reports → Export |
| **MCPs** | Conectores Claude (si están instalados) — pull automático |
| **Manual** | Pegar números clave directamente en el chat |

---

## Arquitectura

### Estructura de archivos

```
.claude/skills/auditoria-performance-report/
├── SKILL.md                              # Definición de la skill orquestadora
├── README.md                             # Este archivo (documentación pública)
└── references/
    └── diagnostico-cruzado.md            # Mapa de impacto técnica × SEO × marketing
                                          # (Secciones A, B, C, D + matrices causa raíz)
```

### Patrón arquitectónico: **Orquestador**

```
┌──────────────────────────────────────────────────────────────┐
│           auditoria-performance-report (Orquestadora)        │
│                                                              │
│   ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│   │ auditoria-web- │  │  seo-audit   │  │ performance-    │ │
│   │ pro (Paso 1)   │  │  (Paso 2)    │  │ report (Paso 3) │ │
│   │                │  │ condicional  │  │                 │ │
│   │ Score técnico  │  │ Estado SEO   │  │ Métricas mkt    │ │
│   │ 8 dimensiones  │  │ estratégico  │  │ por canal       │ │
│   └───────┬────────┘  └──────┬───────┘  └────────┬────────┘ │
│           │                  │                   │          │
│           └──────────────────┼───────────────────┘          │
│                              ▼                              │
│           ┌────────────────────────────────────┐            │
│           │  Paso 4: Diagnóstico cruzado       │            │
│           │  Lectura: diagnostico-cruzado.md   │            │
│           │  Mapeo: técnico × SEO × marketing  │            │
│           └────────────────────┬───────────────┘            │
│                                ▼                            │
│           ┌────────────────────────────────────┐            │
│           │  Paso 5: Diagnóstico unificado     │            │
│           │  4 capas (técnico/SEO/mkt/cruz.)   │            │
│           └────────────────────┬───────────────┘            │
│                                ▼                            │
│           ┌────────────────────────────────────┐            │
│           │  Paso 6: Plan integrado P1/P2/P3/P4│            │
│           │  Acciones técnicas + SEO + campaña │            │
│           └────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

### Lógica del diagnóstico cruzado (`diagnostico-cruzado.md`)

El archivo de referencia contiene **4 secciones operativas**:

| Sección | Contenido |
|---------|-----------|
| **A** | Mapa: Dimensión técnica → métricas de marketing afectadas + señales de problema cruzado |
| **B** | Mapa: Hallazgos SEO → métricas afectadas + matriz causa raíz "organic sessions cayendo" |
| **C** | 8 preguntas diagnósticas clave (CTR alto + conv baja, ROAS bajo, etc.) |
| **D** | Diagnóstico comparativo modo multi-URL (landing A vs B) |

### Reglas críticas

1. **No reemplaza a las skills individuales** — siempre las invoca.
2. **El Paso 2 (`seo-audit`) es condicional** — no obligatorio si no hay métricas orgánicas.
3. **Lectura obligatoria de `diagnostico-cruzado.md`** antes del Paso 4.
4. **No tomar decisiones de inversión** si la Dimensión 3 (Tracking) tiene score < 70 — el problema podría ser el tracking, no la campaña.
5. **Limitación SPAs:** la auditoría técnica analiza HTML estático — mencionar al usuario.
6. **Validación externa recomendada:** Google Search Console, PageSpeed Insights, herramientas de analítica.

---

## Dependencias entre skills

```
auditoria-performance-report
        │
        ├──> auditoria-web-pro       (Paso 1, obligatorio)
        ├──> seo-audit               (Paso 2, condicional)
        └──> performance-report      (Paso 3, obligatorio)
```

Si alguna de las 3 skills no está disponible en el entorno, la orquestadora degrada gracefully al diagnóstico parcial e informa al usuario qué dimensión queda sin cobertura.

---

## Referencias internas

- [SKILL.md](./SKILL.md) — Definición técnica completa para Claude Code
- [diagnostico-cruzado.md](./references/diagnostico-cruzado.md) — Mapa de impacto + matrices causa raíz
- Skills hermanas: [`auditoria-web-pro`](../auditoria-web-pro/README.md), `seo-audit`, `performance-report`
