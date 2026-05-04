# Diagnóstico Cruzado — Mapa de Impacto

Este archivo se lee en el **Paso 4** del flujo de `auditoria-performance-report`.
Contiene la lógica para conectar hallazgos técnicos, SEO estratégicos y métricas de marketing.

---

## SECCIÓN A — Impacto técnico del sitio → métricas de marketing

*(Fuente: `auditoria-web-pro`)*

| Dimensión técnica | Métricas de marketing afectadas | Señal de problema cruzado |
|---|---|---|
| **1. Performance & Carga** (15%) | Bounce rate, tiempo en página, conversion rate, Quality Score (paid search) | CTR bueno + conversión baja + bounce alto → sitio lento bloqueando la conversión |
| **2. SEO On-Page** (15%) | Organic sessions, keyword rankings, organic CTR, páginas indexadas | Tráfico orgánico cae + score SEO bajo → problema técnico de implementación en el sitio |
| **3. SEM & Tracking** (10%) | Datos de atribución (todos los canales), ROAS, CPA, view-through conversions | Datos inconsistentes o atribución incompleta → tracking mal instalado, no problema de campaña |
| **4. Diseño & Responsividad** (15%) | Bounce rate mobile, conversion rate mobile, engagement en social | Tráfico mobile alto + conversión mobile baja → diseño responsivo deficiente |
| **5. UX/UI & Accesibilidad** (15%) | Tiempo en página, scroll depth, completación de formularios, leads generados | Tráfico bueno + leads bajos → fricción en el flujo de conversión |
| **6. Calidad del Contenido** (10%) | Tiempo en página, bounce rate, backlinks ganados, social shares | Contenido pobre + bajo engagement orgánico → el sitio no retiene visitantes |
| **7. Seguridad Técnica** (10%) | Bounce inmediato inexplicado, anomalías en sesiones | Picos de bounce sin causa aparente → advertencias de seguridad del browser |
| **8. Optimización Conversión** (10%) | Conversion rate, CPA, leads, formularios completados, ROAS | ROAS bajo + CTR bueno → landing page o embudo deficiente |

### Regla de diagnóstico por score técnico

```
Score técnico < 70  → causa probable: TÉCNICA (el sitio está limitando el resultado)
Score técnico 70-84 → causa probable: MIXTA (mejorar técnico + ajustar estrategia en paralelo)
Score técnico ≥ 85  → causa probable: ESTRATÉGICA o SEO (el sitio no es el cuello de botella)
```

---

## SECCIÓN B — Hallazgos SEO estratégicos → métricas de marketing

*(Fuente: `seo-audit`)*

| Hallazgo SEO | Métricas de marketing afectadas | Señal de problema cruzado |
|---|---|---|
| **Keywords mal dirigidos** (intent equivocado) | Organic sessions, organic conversion rate | Tráfico orgánico estable pero conversión orgánica baja → ranking para keywords informacionales cuando el negocio necesita transaccionales |
| **Content gaps** (competidores rankean, nosotros no) | Organic sessions, keyword rankings | Caída o estancamiento de tráfico orgánico en categorías específicas → mercado cubierto por competencia |
| **Thin content** (páginas sin profundidad) | Tiempo en página, bounce rate, keyword rankings | Páginas con buen tráfico pero alto bounce y posiciones descendiendo |
| **Content freshness** (páginas sin actualizar 12+ meses) | Keyword rankings graduales cayendo, organic CTR | Pérdida lenta de posiciones sin causa técnica obvia |
| **Missing structured data** (schema ausente) | Organic CTR, featured snippet ownership | Rankings aceptables pero CTR orgánico bajo → competidores con rich snippets capturan los clicks |
| **Broken internal links / redirect chains** | Páginas indexadas, organic sessions por página | Páginas que deberían rankear no reciben link equity → posiciones más bajas de lo esperado |
| **Competitor backlink advantage** | Keyword rankings en términos competitivos | Buen contenido pero no rankea para keywords principales → dominio authority inferior |
| **SERP feature gaps** (sin featured snippets, PAA) | Organic CTR, branded vs. non-branded traffic | Impresiones altas en Search Console pero clicks bajos → competidores dominan las SERP features |
| **Indexation issues** (páginas excluidas del índice) | Organic sessions, páginas indexadas | Caída abrupta en organic sessions → páginas desindexadas por cambios en robots.txt o canonical |

### Matriz causa raíz: organic sessions cayendo

```
Organic sessions cayendo →

  ¿Score SEO On-Page (Dimensión 2) < 70?
    SÍ → Causa técnica de implementación. Prioridad: corregir title/meta/canonical.
    NO ↓

  ¿seo-audit muestra indexation issues o redirect chains?
    SÍ → Causa técnica de crawlability. Prioridad: Technical SEO check.
    NO ↓

  ¿seo-audit muestra content gaps o thin content?
    SÍ → Causa SEO estratégica. Prioridad: crear/profundizar contenido.
    NO ↓

  ¿seo-audit muestra competitor backlink advantage?
    SÍ → Causa SEO off-page. Prioridad: link-building estratégico.
    NO → Causa externa (cambio de algoritmo, estacionalidad). Monitorear Search Console.
```

---

## SECCIÓN C — Preguntas diagnósticas clave

Usar estas preguntas como guía durante el Paso 4:

**1. CTR alto + conversión baja**
→ Revisar score Dimensiones 5 (UX/UI) y 8 (Conversión) de `auditoria-web-pro`.
→ Si score < 70: el anuncio funciona, el sitio falla. Acción: corregir sitio antes de escalar presupuesto.

**2. Tráfico orgánico cayendo**
→ Aplicar la Matriz causa raíz de la Sección B (arriba).
→ Determinar si es técnico, de implementación SEO o estratégico antes de actuar.

**3. ROAS bajo en paid**
→ Revisar Dimensión 1 (Performance & Carga) de la landing page.
→ Sitio lento = Quality Score bajo = CPC más caro = ROAS estructuralmente peor.

**4. Datos de atribución inconsistentes**
→ Revisar Dimensión 3 (SEM & Tracking). Si score < 70: el problema es el tracking, no la campaña.
→ No tomar decisiones de inversión hasta validar que el tracking esté correcto.

**5. Leads cayendo sin caída en tráfico**
→ Revisar Dimensiones 5 (UX/UI) y 8 (Conversión). El embudo de captura tiene fricción nueva.
→ Preguntar si hubo cambios en el sitio en el período.

**6. Organic CTR bajo a pesar de buenas posiciones**
→ Revisar hallazgo de `seo-audit`: ¿hay competidores con featured snippets o PAA para esos keywords?
→ Prioridad: implementar structured data (schema FAQ, HowTo, Article) para recuperar SERP features.

**7. Rankings buenos, pero tráfico orgánico no convierte**
→ Revisar hallazgo de `seo-audit`: ¿el intent de los keywords rankeados es informacional en vez de transaccional?
→ Problema de estrategia SEO, no técnico. Crear contenido transaccional con keywords de conversión.

**8. Contenido con buen tráfico pero posiciones descendiendo gradualmente**
→ Revisar hallazgo `seo-audit` de content freshness. ¿Está sin actualizar 12+ meses?
→ Actualizar y profundizar el contenido existente antes de crear nuevo.

---

## SECCIÓN D — Diagnóstico comparativo (modo multi-URL)

Si el usuario provee varias URLs (ej: landing A vs landing B de dos campañas):

1. Score técnico de cada URL por separado (`auditoria-web-pro` modo comparativo).
2. Análisis SEO de cada URL (`seo-audit` por URL si es relevante).
3. Métricas de marketing de cada campaña asociada.
4. Concluir si los diferenciales de performance se explican por diferencias técnicas o SEO.

| Dimensión | URL A | URL B | Δ | Métrica afectada | Δ métrica |
|---|---|---|---|---|---|
| Performance & Carga | [score] | [score] | [+/-] | Conversion rate | [+/-] |
| UX/UI | [score] | [score] | [+/-] | Leads | [+/-] |
| Content quality (SEO) | [status] | [status] | — | Tiempo en página | [+/-] |

Si las URLs con mejor score técnico y SEO muestran sistemáticamente mejores métricas → el sitio/contenido es factor determinante.
Si los scores son similares pero los resultados difieren → el diferencial es estratégico (creativos, audiencia, oferta).
