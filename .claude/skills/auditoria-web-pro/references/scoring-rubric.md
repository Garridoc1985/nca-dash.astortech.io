# Scoring Rubric — Web Audit

Cada dimensión se puntúa de 0 a 100. Usar este rubric para traducir métricas brutas en puntajes.

> **Nota metodológica:** Este rubric evalúa lo observable desde el HTML estático. Para sitios SPA (React, Next.js, Vue), el HTML inicial puede estar incompleto — mencionar esta limitación en el reporte. Siempre evaluar con perspectiva **mobile-first**, ya que Google indexa principalmente la versión móvil.

---

## 1. Performance & Carga (15%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | HTML < 100KB, < 500 elementos DOM, 0 recursos render-blocking, todas las imágenes con lazy loading + srcset, < 3 scripts de terceros, preload/preconnect presentes |
| 75–89  | HTML < 200KB, < 1.000 elementos, ≤ 2 render-blocking, > 50% imágenes con lazy, < 5 scripts de terceros |
| 60–74  | HTML < 500KB, < 1.500 elementos, ≤ 5 render-blocking, algo de lazy loading, < 10 scripts de terceros |
| 40–59  | HTML < 1MB, < 2.000 elementos, > 5 render-blocking, optimización mínima |
| 0–39   | HTML > 1MB, > 2.000 elementos, muchos render-blocking, sin optimización, scripts de terceros excesivos |

**Deducciones clave:**
- Scripts sin async/defer: -10
- Sin preload hints: -5
- > 10 scripts de terceros: -15
- Sin lazy loading en imágenes: -10
- Profundidad DOM > 15: -5
- Más de 5 fuentes externas (Google Fonts, etc.): -5

---

## 2. SEO On-Page (15%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | Title (50-60ch), meta desc (150-160ch), H1 único, jerarquía correcta, canonical, OG+Twitter tags, Schema.org, > 95% cobertura alt, URL limpia, hreflang si multiidioma |
| 75–89  | Title + meta desc presentes (cualquier longitud), H1 presente, algunos OG tags, > 80% alt, canonical |
| 60–74  | Title presente, meta desc débil, algunos problemas de headings, > 50% alt |
| 40–59  | Solo title, sin meta desc O de baja calidad, múltiples H1, < 50% alt |
| 0–39   | Sin title o elementos SEO críticos, sin structured data, sin alt tags |

**Deducciones clave:**
- Sin title: -30
- Sin meta description: -15
- Múltiples H1 o sin H1: -10
- Sin canonical: -5
- Sin OG tags: -5
- Sin structured data / Schema.org: -10
- Cobertura alt < 50%: -10
- Sin hreflang (sitio multiidioma detectado): -5
- Title < 30 chars o > 70 chars: -5

---

## 3. SEM & Tracking (10%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | GTM + GA4 + píxeles de conversión (Meta, TikTok, Google Ads), herramienta A/B testing, remarketing configurado, propuesta de valor clara above fold |
| 75–89  | GTM + GA4, al menos un píxel de anuncios, página carga rápido (buen Quality Score) |
| 60–74  | Analytics básico (GA o similar), al menos un píxel de tracking |
| 40–59  | Solo analytics básico, sin tracking de anuncios |
| 0–39   | Sin analytics ni tracking whatsoever |

**Scoring positivo:**
- Google Tag Manager: +15
- Google Analytics / GA4: +15
- Meta Pixel: +10
- TikTok Pixel: +8
- LinkedIn Insight Tag: +8
- Google Ads / Remarketing: +10
- Microsoft Clarity o Hotjar: +8
- Herramienta A/B testing (Optimizely, VWO, AB Tasty): +10
- Pinterest Tag / Twitter Pixel: +5 c/u
- Sin tracking alguno: score base = 5

---

## 4. Diseño & Responsividad (15%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | Viewport correcto, media queries, CSS moderno (grid/flexbox), imágenes responsivas, picture elements, print stylesheet, framework detectado |
| 75–89  | Viewport + media queries + framework, algunas imágenes responsivas |
| 60–74  | Viewport presente, responsive básico, framework detectado |
| 40–59  | Viewport presente pero patrones responsive limitados |
| 0–39   | Sin viewport meta, sin patrones responsive |

**Scoring:**
- Sin viewport meta: máximo puntaje = 30
- Viewport presente: +20 base
- Media queries detectadas: +15
- Framework CSS detectado: +10
- Imágenes responsivas (srcset): +10
- Picture elements: +5
- Print stylesheet: +5
- Layout moderno (grid/flexbox en CSS): +10
- Fuentes escalables (rem/em vs px fijo): +5

---

## 5. UX/UI & Accesibilidad (15%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | Navegación clara, skip links, ARIA labels, breadcrumbs, buscador, estilos focus, formularios con validación, excelente accesibilidad, aviso de cookies |
| 75–89  | Nav elements, uso de ARIA, formularios con labels, buena estructura |
| 60–74  | Nav básica, algo de ARIA, formularios presentes |
| 40–59  | Estructura mínima, sin ARIA, formularios básicos |
| 0–39   | Sin elemento nav, sin features de accesibilidad, sin formularios |

**Scoring:**
- Nav element presente: +15
- ARIA labels (> 5): +10
- ARIA roles (> 3): +5
- Skip links: +10
- Función de búsqueda: +5
- Estilos focus (focus-visible): +10
- Formularios con campos requeridos: +5
- Breadcrumbs: +5
- Tabindex gestionado: +5
- Cookie consent / aviso de privacidad detectado: +5
- Chatbot / asistente IA detectado: +5

---

## 6. Calidad del Contenido (10%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | > 800 palabras, ratio texto/HTML > 25%, contenido estructurado (listas, tablas), multimedia, oraciones promedio < 20 palabras, prueba social visible |
| 75–89  | > 500 palabras, ratio > 15%, algo de estructura, algo de multimedia |
| 60–74  | > 300 palabras, ratio > 10%, estructura básica |
| 40–59  | > 100 palabras, ratio > 5%, estructura mínima |
| 0–39   | < 100 palabras, ratio < 5%, sin estructura |

**Scoring:**
- 300-500 palabras: +15 | 500-800: +20 | 800+: +25
- Ratio texto/HTML > 20%: +15
- Párrafos > 5: +5
- Listas presentes: +5
- Tablas presentes: +5
- Video embebido (YouTube, Vimeo, video nativo): +10
- Longitud promedio de oraciones < 20 palabras: +5
- Tags HTML diversos (> 15 únicos): +5
- Señales de prueba social en texto: +5

---

## 7. Seguridad Técnica (10%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | HTTPS, sin mixed content, SRI en scripts externos, CSP, form actions seguros, sin info de servidor expuesta |
| 75–89  | HTTPS, sin mixed content, algo de SRI, formularios seguros |
| 60–74  | HTTPS, mixed content mínimo, seguridad básica |
| 40–59  | HTTPS pero con mixed content o formularios inseguros |
| 0–39   | HTTP, mixed content, sin medidas de seguridad |

**Scoring:**
- HTTPS: +30 (sin HTTPS = máximo 20)
- Sin mixed content: +15
- SRI en scripts externos (> 50%): +15
- CSP detectada: +10
- Todos los form actions en HTTPS: +10
- Sin info de servidor/tech expuesta: +5
- Atributos de cookies seguros detectados: +5 (bonus)

---

## 8. Optimización de Conversión (10%)

| Rango | Criterios |
|-------|-----------|
| 90–100 | CTAs claros, trust badges, testimonios, WhatsApp/chat visible, precios visibles, múltiples métodos de contacto, formularios optimizados (< 5 campos) |
| 75–89  | CTAs presentes, algunas señales de confianza, info de contacto, formularios |
| 60–74  | CTA básico, info de contacto, formulario simple |
| 40–59  | CTA mínimo, contacto difícil de encontrar |
| 0–39   | Sin CTA claro, sin señales de confianza, sin contacto fácil |

**Scoring:**
- Botones CTA detectados: +15
- Trust badges / sellos de confianza: +10
- Testimonios / reviews: +10
- Widget de chat en vivo (Tawk, Intercom, Crisp, Tidio): +8
- WhatsApp como canal de contacto (wa.me link): +8 (especialmente relevante en LATAM)
- Precios visibles: +5
- Teléfono visible: +5
- Formulario de captura de email: +10
- Bajo fricción en formulario (< 5 campos): +5
- Múltiples métodos de contacto: +5

---

## Cálculo del Puntaje Global

```
Puntaje Global = (Performance × 0.15) + (SEO × 0.15) + (SEM × 0.10) +
                 (Diseño × 0.15) + (UX/UI × 0.15) + (Contenido × 0.10) +
                 (Seguridad × 0.10) + (Conversión × 0.10)
```

## Escala de Calificación

| Calificación | Rango | Emoji | Etiqueta |
|--------------|-------|-------|----------|
| A+ | 95–100 | 🟢 | Excepcional |
| A  | 90–94  | 🟢 | Excelente |
| B+ | 85–89  | 🔵 | Muy Bueno |
| B  | 75–84  | 🔵 | Bueno |
| C+ | 70–74  | 🟡 | Aceptable |
| C  | 60–69  | 🟡 | Regular |
| D  | 40–59  | 🟠 | Necesita Mejoras |
| F  | 0–39   | 🔴 | Crítico |
