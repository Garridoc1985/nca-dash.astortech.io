# Report Template — Web Audit (ASTOR Brand)

Usar esta estructura para generar el reporte HTML final.
El diseño sigue las Brand Guidelines v1.0 de ASTOR.

> **REGLA CRÍTICA:** El CSS que aparece en la sección "CSS Canónico Completo" de este archivo
> DEBE ser copiado VERBATIM al generar el HTML — sin minificar, sin abreviar variables,
> sin simplificar clases. El archivo de referencia visual es
> `output/auditoria-upset-20260330.html`. Cualquier reporte que no use este CSS
> exacto NO cumple con el estándar de marca.

---

## Sistema de Diseño — Brand ASTOR

### Colores oficiales (CSS variables — nombres completos, no abreviar)

```css
:root {
  --obsidiana:      #1A1A18;  /* Primario · fondos header/footer */
  --obsidiana-deep: #111110;  /* Topbar y footer profundo */
  --obsidiana-mid:  #2a2a27;  /* Acentos oscuros */
  --oro:            #C4963A;  /* Acento principal · énfasis · logo */
  --oro-suave:      #E8D5A3;  /* Fondos de énfasis suave */
  --oro-bg:         rgba(196,150,58,0.07);
  --blanco:         #FAF8F4;  /* Fondo principal claro */
  --seccion-alt:    #F0EDE6;  /* Secciones alternadas */
  --piedra:         #6B6860;  /* Texto secundario */
  --piedra-clara:   #9a9790;
  --borde:          rgba(26,26,24,0.1);

  /* Colores funcionales para scores — NO usar brillantes ni neones */
  --score-bueno:    #2d7a6a;  /* 75–100 */
  --score-aceptable:#C4963A;  /* 70–74  */
  --score-regular:  #a07830;  /* 60–69  */
  --score-mejoras:  #b05c28;  /* 40–59  */
  --score-critico:  #922828;  /* 0–39   */
}
```

**PROHIBIDO:**
- Minificar o abreviar variables (NO usar `--ob`, `--oro` acortado, `--bl`)
- Colores brillantes, saturados o neones
- Negro puro `#000000` — usar `--obsidiana` o `--obsidiana-deep`
- Blanco puro `#FFFFFF` — usar `--blanco` (`#FAF8F4`)
- Más de 2 familias tipográficas
- CSS inline con estilos que deberían ser clases

### Tipografía

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
```

- **Display/Titulares:** Cormorant Garamond (serif elegante)
- **UI/Cuerpo:** Inter (sans-serif limpio)

---

## Funciones Helper de Score

```js
// Clase CSS según score (para color-* en cards, radar-items y dimensions)
function scoreClass(s) {
  if (s >= 75) return 'color-bueno';
  if (s >= 70) return 'color-aceptable';
  if (s >= 60) return 'color-regular';
  if (s >= 40) return 'color-mejoras';
  return 'color-critico';
}
function scoreGrade(s) {
  if (s >= 95) return 'A+'; if (s >= 90) return 'A';
  if (s >= 85) return 'B+'; if (s >= 75) return 'B';
  if (s >= 70) return 'C+'; if (s >= 60) return 'C';
  if (s >= 40) return 'D'; return 'F';
}
function scoreLabel(s) {
  if (s >= 95) return 'Excepcional'; if (s >= 90) return 'Excelente';
  if (s >= 85) return 'Muy Bueno';  if (s >= 75) return 'Bueno';
  if (s >= 70) return 'Aceptable';  if (s >= 60) return 'Regular';
  if (s >= 40) return 'Necesita Mejoras'; return 'Crítico';
}
```

---

## Cálculo del Radar Chart Polygon

Centro: (200, 200), radio máximo: 150. 8 ejes desde -90° en pasos de 45°.

```js
// Orden de dimensiones: Performance, SEO, SEM, Diseño, UX/UI, Contenido, Seguridad, Conversión
const cx = 200, cy = 200, r = 150;
const scores = [perf, seo, sem, diseno, ux, contenido, seguridad, conversion];
const points = scores.map((s, i) => {
  const angle = (i * 45 - 90) * Math.PI / 180;
  const d = (s / 100) * r;
  return `${Math.round(cx + d * Math.cos(angle))},${Math.round(cy + d * Math.sin(angle))}`;
}).join(' ');
// Usar points como atributo del polygon SVG
```

---

## CSS Canónico Completo

**COPIAR ESTE BLOQUE EXACTAMENTE — no simplificar ni modificar la estructura de clases.**

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }

body {
  background: var(--blanco);
  color: var(--obsidiana);
  font-family: 'Inter', sans-serif;
  font-size: 15px;
  font-weight: 300;
  line-height: 1.65;
  -webkit-font-smoothing: antialiased;
}

/* ─── NOISE TEXTURE ─── */
body::before {
  content: '';
  position: fixed;
  inset: 0;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='1'/%3E%3C/svg%3E");
  opacity: 0.022;
  pointer-events: none;
  z-index: 1000;
}

/* ─── LAYOUT ─── */
.wrap { max-width: 1080px; margin: 0 auto; padding: 0 44px; }

/* ─── TOP BAR ─── */
.topbar { background: var(--obsidiana-deep); padding: 16px 0; }
.topbar .wrap { display: flex; align-items: center; justify-content: space-between; }
.topbar-brand {
  display: flex; align-items: center; gap: 14px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 19px; font-weight: 400;
  letter-spacing: 0.07em;
  color: var(--oro);
}
.topbar-meta { font-size: 11px; color: rgba(255,255,255,0.4); letter-spacing: 0.06em; text-align: right; }
.topbar-meta strong { display: block; color: rgba(255,255,255,0.65); font-weight: 500; font-size: 12px; }

/* ─── HERO (dark) ─── */
.hero { background: var(--obsidiana); padding: 64px 0 56px; }
.hero .wrap { display: grid; grid-template-columns: 1fr 300px; gap: 56px; align-items: center; }
.hero-eyebrow {
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--oro); margin-bottom: 18px;
  opacity: 0; animation: fadeUp 0.5s 0s forwards;
}
.hero-title {
  font-family: 'Cormorant Garamond', serif;
  font-size: clamp(36px, 4.5vw, 52px);
  font-weight: 300; line-height: 1.1;
  color: var(--blanco); margin-bottom: 10px;
  opacity: 0; animation: fadeUp 0.5s 0.1s forwards;
}
.hero-title em { font-style: italic; color: var(--oro-suave); }
.hero-url {
  font-size: 12px; color: rgba(250,248,244,0.45);
  margin-bottom: 24px; letter-spacing: 0.02em;
  opacity: 0; animation: fadeUp 0.5s 0.2s forwards;
}
.hero-url a { color: var(--oro); text-decoration: none; }
.hero-summary {
  font-size: 13.5px; color: rgba(250,248,244,0.6);
  line-height: 1.75; max-width: 500px;
  border-left: 2px solid rgba(196,150,58,0.4);
  padding-left: 16px;
  opacity: 0; animation: fadeUp 0.5s 0.3s forwards;
}

/* ─── GAUGE ─── */
.gauge-wrap { text-align: center; }
.gauge-score {
  font-family: 'Cormorant Garamond', serif;
  font-size: 84px; font-weight: 300; line-height: 1;
  color: var(--blanco); margin-top: -12px;
}
.gauge-grade {
  display: inline-block; font-size: 10px; font-weight: 700;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--blanco); padding: 5px 14px; margin-top: 6px;
}
.gauge-label { font-size: 11px; color: rgba(255,255,255,0.35); margin-top: 8px; }

/* ─── GOLD RULE ─── */
.gold-rule {
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--oro), transparent);
  opacity: 0.3;
}

/* ─── SECTION HEADER ─── */
.section-header { padding: 52px 0 36px; }
.section-eyebrow {
  font-size: 10px; font-weight: 600;
  letter-spacing: 0.22em; text-transform: uppercase;
  color: var(--oro); margin-bottom: 8px;
}
.section-title { font-family: 'Cormorant Garamond', serif; font-size: 32px; font-weight: 300; color: var(--obsidiana); }

/* ─── SCORE GRID ─── */
.score-grid-section { background: var(--seccion-alt); padding-bottom: 56px; }
.score-grid-section .section-header { padding-top: 52px; }
.score-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.score-card {
  background: var(--blanco);
  padding: 24px 20px 20px;
  border: 1px solid var(--borde);
  position: relative;
  opacity: 0;
  animation: fadeUp 0.4s forwards;
}
.score-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}
.score-card.color-bueno::before     { background: var(--score-bueno); }
.score-card.color-aceptable::before { background: var(--score-aceptable); }
.score-card.color-regular::before   { background: var(--score-regular); }
.score-card.color-mejoras::before   { background: var(--score-mejoras); }
.score-card.color-critico::before   { background: var(--score-critico); }
.score-card-dim { font-size: 9.5px; font-weight: 600; letter-spacing: 0.16em; text-transform: uppercase; color: var(--piedra); margin-bottom: 10px; }
.score-card-num { font-family: 'Cormorant Garamond', serif; font-size: 60px; font-weight: 300; line-height: 1; margin-bottom: 4px; }
.score-card.color-bueno     .score-card-num { color: var(--score-bueno); }
.score-card.color-aceptable .score-card-num { color: var(--score-aceptable); }
.score-card.color-regular   .score-card-num { color: var(--score-regular); }
.score-card.color-mejoras   .score-card-num { color: var(--score-mejoras); }
.score-card.color-critico   .score-card-num { color: var(--score-critico); }
.score-card-label { font-size: 11px; font-weight: 500; color: var(--piedra); }
.score-card-peso  { font-size: 10px; color: var(--piedra-clara); margin-top: 2px; }
.score-card:nth-child(1) { animation-delay: 0.05s; }
.score-card:nth-child(2) { animation-delay: 0.10s; }
.score-card:nth-child(3) { animation-delay: 0.15s; }
.score-card:nth-child(4) { animation-delay: 0.20s; }
.score-card:nth-child(5) { animation-delay: 0.25s; }
.score-card:nth-child(6) { animation-delay: 0.30s; }
.score-card:nth-child(7) { animation-delay: 0.35s; }
.score-card:nth-child(8) { animation-delay: 0.40s; }

/* ─── RADAR SECTION ─── */
.radar-section { padding: 56px 0 60px; background: var(--blanco); }
.radar-layout { display: grid; grid-template-columns: 400px 1fr; gap: 64px; align-items: center; }
.radar-legend { display: flex; flex-direction: column; gap: 0; }
.radar-item {
  display: grid; grid-template-columns: 1fr auto;
  align-items: center; padding: 11px 0;
  border-bottom: 1px solid var(--borde);
  opacity: 0; animation: fadeUp 0.4s forwards;
}
.radar-item:nth-child(1) { animation-delay: 0.1s; }
.radar-item:nth-child(2) { animation-delay: 0.15s; }
.radar-item:nth-child(3) { animation-delay: 0.2s; }
.radar-item:nth-child(4) { animation-delay: 0.25s; }
.radar-item:nth-child(5) { animation-delay: 0.3s; }
.radar-item:nth-child(6) { animation-delay: 0.35s; }
.radar-item:nth-child(7) { animation-delay: 0.4s; }
.radar-item:nth-child(8) { animation-delay: 0.45s; }
.radar-item-name { font-size: 12px; font-weight: 500; color: var(--obsidiana); }
.radar-item-bar { height: 2px; background: rgba(26,26,24,0.1); width: 120px; margin: 4px 0; }
.radar-item-bar-fill { height: 100%; background: var(--oro); }
.radar-item-score { font-family: 'Cormorant Garamond', serif; font-size: 26px; font-weight: 300; margin-left: 20px; }
.radar-item.color-bueno     .radar-item-score { color: var(--score-bueno); }
.radar-item.color-aceptable .radar-item-score { color: var(--score-aceptable); }
.radar-item.color-regular   .radar-item-score { color: var(--score-regular); }
.radar-item.color-mejoras   .radar-item-score { color: var(--score-mejoras); }
.radar-item.color-critico   .radar-item-score { color: var(--score-critico); }

/* ─── DIMENSIONS SECTION ─── */
.dimensions-section { background: var(--seccion-alt); padding: 56px 0 60px; }
.dimension {
  padding: 40px 0;
  border-top: 1px solid rgba(26,26,24,0.1);
  display: grid;
  grid-template-columns: 180px 1fr;
  gap: 44px;
}
.dimension:last-child { border-bottom: 1px solid rgba(26,26,24,0.1); }
.dimension-num {
  font-family: 'Cormorant Garamond', serif;
  font-size: 76px; font-weight: 300; line-height: 1; display: block;
}
.dimension.color-bueno     .dimension-num { color: var(--score-bueno); }
.dimension.color-aceptable .dimension-num { color: var(--score-aceptable); }
.dimension.color-regular   .dimension-num { color: var(--score-regular); }
.dimension.color-mejoras   .dimension-num { color: var(--score-mejoras); }
.dimension.color-critico   .dimension-num { color: var(--score-critico); }
.dimension-title { font-size: 9.5px; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--piedra); margin-top: 6px; line-height: 1.5; }
.dimension-grade {
  display: inline-block; font-size: 9px; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase;
  color: #fff; padding: 3px 10px; margin-top: 10px;
}
.dimension.color-bueno     .dimension-grade { background: var(--score-bueno); }
.dimension.color-aceptable .dimension-grade { background: var(--score-aceptable); color: var(--obsidiana); }
.dimension.color-regular   .dimension-grade { background: var(--score-regular); }
.dimension.color-mejoras   .dimension-grade { background: var(--score-mejoras); }
.dimension.color-critico   .dimension-grade { background: var(--score-critico); }
.dimension-body h3 { font-family: 'Cormorant Garamond', serif; font-size: 21px; font-weight: 400; color: var(--obsidiana); margin-bottom: 14px; }
.dimension-body p { font-size: 13px; color: var(--piedra); margin-bottom: 18px; line-height: 1.75; }
.findings { display: flex; flex-direction: column; gap: 7px; margin-bottom: 20px; }
.finding { display: flex; gap: 10px; align-items: flex-start; font-size: 12.5px; line-height: 1.6; color: var(--obsidiana); }
.finding-icon { flex-shrink: 0; font-size: 13px; }
.recs { display: flex; flex-direction: column; gap: 8px; }
.rec {
  background: rgba(196,150,58,0.06);
  border-left: 2px solid rgba(196,150,58,0.4);
  padding: 10px 14px;
  font-size: 12.5px; color: var(--piedra); line-height: 1.6;
}
.rec strong { color: var(--obsidiana); font-weight: 500; }
.rec-priority {
  display: inline-block; font-size: 9px; font-weight: 700;
  letter-spacing: 0.14em; text-transform: uppercase;
  padding: 2px 7px; margin-bottom: 5px;
}
.rec-priority.alta  { background: rgba(176,92,40,0.15); color: #c06030; }
.rec-priority.media { background: rgba(160,120,48,0.15); color: #9a7020; }
.rec-priority.baja  { background: rgba(45,122,106,0.15); color: #2d7a6a; }

/* ─── ALERTA CRÍTICA ─── */
.alerta-critica {
  background: rgba(146,40,40,0.06);
  border: 1px solid rgba(146,40,40,0.2);
  border-left: 3px solid var(--score-critico);
  padding: 14px 18px; margin-bottom: 20px;
  font-size: 12.5px; color: var(--obsidiana); line-height: 1.6;
}
.alerta-critica strong { color: var(--score-critico); font-weight: 600; }

/* ─── ROADMAP (dark section) ─── */
.roadmap-section { padding: 56px 0; background: var(--obsidiana); }
.roadmap-section .section-title { color: var(--blanco); }
.roadmap-section .section-eyebrow { color: var(--oro); }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
thead tr { border-bottom: 1px solid rgba(196,150,58,0.3); }
thead th {
  font-size: 9.5px; font-weight: 600;
  letter-spacing: 0.18em; text-transform: uppercase;
  color: var(--oro); padding: 0 16px 12px 0; text-align: left;
}
tbody tr { border-bottom: 1px solid rgba(255,255,255,0.07); transition: background 0.15s; }
tbody tr:hover { background: rgba(255,255,255,0.03); }
tbody td { padding: 13px 16px 13px 0; color: rgba(250,248,244,0.55); vertical-align: top; line-height: 1.55; }
tbody td:first-child { color: rgba(250,248,244,0.85); font-weight: 400; }
.tag {
  display: inline-block; font-size: 9px; font-weight: 700;
  letter-spacing: 0.12em; text-transform: uppercase; padding: 3px 8px;
}
.tag.alta  { background: rgba(176,92,40,0.2);  color: #e07040; border: 1px solid rgba(176,92,40,0.3); }
.tag.media { background: rgba(160,120,48,0.2); color: #c09040; border: 1px solid rgba(160,120,48,0.3); }
.tag.baja  { background: rgba(45,122,106,0.2); color: #3d9a8a; border: 1px solid rgba(45,122,106,0.3); }
.tag.alto  { background: rgba(45,122,106,0.2); color: #3d9a8a; border: 1px solid rgba(45,122,106,0.3); }
.tag.medio { background: rgba(160,120,48,0.2); color: #c09040; border: 1px solid rgba(160,120,48,0.3); }
.tag.bajo  { background: rgba(146,40,40,0.2);  color: #c05050; border: 1px solid rgba(146,40,40,0.3); }

/* ─── METHODOLOGY ─── */
.methodology { padding: 48px 0; border-top: 1px solid var(--borde); background: var(--blanco); }
.methodology p { font-size: 12px; color: var(--piedra); line-height: 1.8; max-width: 720px; }

/* ─── FOOTER ─── */
footer { background: var(--obsidiana-deep); padding: 24px 0; }
.footer-inner { display: flex; align-items: center; justify-content: space-between; }
.footer-brand {
  display: flex; align-items: center; gap: 12px;
  font-family: 'Cormorant Garamond', serif;
  font-size: 16px; font-weight: 400;
  color: var(--oro); letter-spacing: 0.06em;
}
.footer-copy { font-size: 11px; color: rgba(255,255,255,0.25); }

/* ─── ANIMATIONS ─── */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes gaugeReveal {
  from { stroke-dashoffset: 502; }
  to   { stroke-dashoffset: 0; }
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ─── RESPONSIVE ─── */
@media (max-width: 900px) {
  .hero .wrap     { grid-template-columns: 1fr; }
  .gauge-wrap     { order: -1; }
  .radar-layout   { grid-template-columns: 1fr; }
  .score-grid     { grid-template-columns: repeat(2,1fr); }
  .dimension      { grid-template-columns: 1fr; gap: 14px; }
}
@media (max-width: 540px) {
  .wrap           { padding: 0 20px; }
  .score-grid     { grid-template-columns: 1fr; }
}
@media print {
  body::before    { display: none; }
  .score-card, .radar-item, .hero-title, .hero-summary, .hero-url, .hero-eyebrow {
    opacity: 1 !important; animation: none !important;
  }
}
```

---

## Estructura HTML Completa

Secciones en orden — usar siempre este esqueleto:

### 1. `<head>` con fonts y CSS

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Auditoría Web — [Nombre sitio] — ASTOR</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,600;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
    :root { /* variables de color — copiar exactamente del CSS canónico */ }
    /* PEGAR AQUÍ EL CSS CANÓNICO COMPLETO */
  </style>
</head>
```

### 2. TOP BAR (barra oscura de marca)

```html
<header class="topbar">
  <div class="wrap">
    <div class="topbar-brand">
      <svg width="30" height="30" viewBox="0 0 48 48" fill="none">
        <polygon points="24,4 44,44 4,44" fill="none" stroke="#C4963A" stroke-width="1.8"/>
        <polygon points="24,14.5 35.5,38 12.5,38" fill="none" stroke="#C4963A" stroke-width="1.2"/>
      </svg>
      ASTOR · Auditoría Web
    </div>
    <div class="topbar-meta">
      <strong>[dominio.cl]</strong>
      [DD de mes de AAAA] · v1.0
    </div>
  </div>
</header>
```

### 3. HERO (dark, grid 2 columnas: texto | gauge)

```html
<section class="hero">
  <div class="wrap">
    <div class="hero-left">
      <p class="hero-eyebrow">Diagnóstico Integral — 8 Dimensiones</p>
      <h1 class="hero-title">
        [Nombre del Sitio]<br>
        <em>Informe de Auditoría</em>
      </h1>
      <p class="hero-url">
        <a href="[URL]" target="_blank">[URL]</a>
        &nbsp;·&nbsp; [Plataforma] &nbsp;·&nbsp; [Industria], Chile
      </p>
      <p class="hero-summary">
        [Párrafo resumen de 3-4 oraciones: qué hace el sitio, hallazgos clave, oportunidades principales]
      </p>
    </div>

    <div class="gauge-wrap">
      <!-- GAUGE SVG: arco semicircular con bandas de color -->
      <svg viewBox="0 0 300 170" width="300" height="170" style="overflow:visible">
        <!-- Bandas de referencia (opacidad baja) -->
        <path d="M 30,155 A 120,120 0 0 0 78,57"   fill="none" stroke="#922828" stroke-width="10" stroke-linecap="round" opacity="0.3"/>
        <path d="M 78,57  A 120,120 0 0 0 150,35"  fill="none" stroke="#b05c28" stroke-width="10" stroke-linecap="round" opacity="0.3"/>
        <path d="M 150,35 A 120,120 0 0 0 222,57"  fill="none" stroke="#a07830" stroke-width="10" stroke-linecap="round" opacity="0.3"/>
        <path d="M 222,57 A 120,120 0 0 0 270,155" fill="none" stroke="#2d7a6a" stroke-width="10" stroke-linecap="round" opacity="0.3"/>

        <!-- Score arc animado: el punto final depende del score -->
        <!-- Score 0→ (30,155) | Score 50→ (150,35) | Score 100→ (270,155) -->
        <!-- Para score S, ángulo = -180 + (S/100)*180 grados desde centro (150,155) radio 120 -->
        <path d="M 30,155 A 120,120 0 0 0 [punto-final-x],[punto-final-y]"
              fill="none" stroke="#C4963A" stroke-width="6" stroke-linecap="round"
              stroke-dasharray="502" stroke-dashoffset="502"
              style="animation: gaugeReveal 1.4s 0.3s cubic-bezier(.4,0,.2,1) forwards;"/>

        <!-- Needle (línea desde centro al punto del score) -->
        <line x1="150" y1="155" x2="[punto-final-x]" y2="[punto-final-y]"
              stroke="#FAF8F4" stroke-width="1.5" stroke-linecap="round"
              opacity="0" style="animation: fadeIn 0.4s 1.6s forwards;"/>
        <circle cx="150" cy="155" r="5" fill="#C4963A"
                opacity="0" style="animation: fadeIn 0.4s 1.6s forwards;"/>

        <!-- Ticks y etiquetas de escala -->
        <g stroke="rgba(255,255,255,0.2)" stroke-width="1">
          <line x1="30" y1="155" x2="36" y2="155"/>
          <line x1="150" y1="35" x2="150" y2="42"/>
          <line x1="270" y1="155" x2="264" y2="155"/>
        </g>
        <text x="24"  y="172" fill="rgba(255,255,255,0.35)" font-size="9" font-family="Inter,sans-serif" text-anchor="middle">0</text>
        <text x="150" y="28"  fill="rgba(255,255,255,0.35)" font-size="9" font-family="Inter,sans-serif" text-anchor="middle">50</text>
        <text x="276" y="172" fill="rgba(255,255,255,0.35)" font-size="9" font-family="Inter,sans-serif" text-anchor="middle">100</text>
      </svg>

      <div class="gauge-score">[SCORE]</div>
      <div class="gauge-grade" style="background: [scoreColor];">[GRADE] · [LABEL]</div>
      <p class="gauge-label">Puntaje global ponderado / 100</p>
    </div>
  </div>
</section>

<div class="gold-rule"></div>
```

**Cálculo del punto final del gauge (centro 150,155 radio 120):**
```
angle_rad = (-180 + score * 1.8) * π / 180
x = 150 + 120 * cos(angle_rad)  → round to integer
y = 155 + 120 * sin(angle_rad)  → round to integer
```
Ejemplos: score 59 → (184, 40) · score 71 → (218, 51) · score 54 → (176, 43)

### 4. SCORE GRID (fondo seccion-alt)

```html
<section class="score-grid-section">
  <div class="wrap">
    <div class="section-header">
      <p class="section-eyebrow">Resumen por Dimensión</p>
      <h2 class="section-title">Las 8 Dimensiones</h2>
    </div>
    <div class="score-grid">
      <!-- Por cada dimensión — color-class según scoreClass(score) -->
      <div class="score-card [color-class]">
        <p class="score-card-dim">[Dimensión]</p>
        <div class="score-card-num">[score]</div>
        <p class="score-card-label">[Grade] — [Label]</p>
        <p class="score-card-peso">Peso: [X]%</p>
      </div>
      <!-- ... 8 tarjetas total -->
    </div>
  </div>
</section>

<div class="gold-rule"></div>
```

### 5. RADAR SECTION (fondo blanco, grid radar SVG | leyenda)

```html
<section class="radar-section">
  <div class="wrap">
    <div class="section-header" style="padding-top:0">
      <p class="section-eyebrow">Visualización Comparativa</p>
      <h2 class="section-title">Perfil de Madurez Digital</h2>
    </div>
    <div class="radar-layout">

      <!-- Radar SVG: centro (200,200), radio máx 150, 8 ejes -90° cada 45° -->
      <svg viewBox="40 40 320 320" width="400" height="400" style="overflow:visible">
        <!-- Polígonos de guía (25%, 50%, 75%, 100%) -->
        <polygon points="200,50 306,94 350,200 306,306 200,350 94,306 50,200 94,94"
                 fill="rgba(196,150,58,0.04)" stroke="rgba(26,26,24,0.1)" stroke-width="1"/>
        <polygon points="200,87 279,120 313,200 279,280 200,313 121,280 87,200 121,120"
                 fill="none" stroke="rgba(26,26,24,0.08)" stroke-width="1"/>
        <polygon points="200,125 253,147 275,200 253,253 200,275 147,253 125,200 147,147"
                 fill="none" stroke="rgba(26,26,24,0.07)" stroke-width="1"/>
        <polygon points="200,163 227,174 238,200 227,226 200,238 174,226 163,200 174,174"
                 fill="none" stroke="rgba(26,26,24,0.05)" stroke-width="1"/>

        <!-- Ejes -->
        <g stroke="rgba(26,26,24,0.12)" stroke-width="1">
          <line x1="200" y1="200" x2="200" y2="50"/>
          <line x1="200" y1="200" x2="306" y2="94"/>
          <line x1="200" y1="200" x2="350" y2="200"/>
          <line x1="200" y1="200" x2="306" y2="306"/>
          <line x1="200" y1="200" x2="200" y2="350"/>
          <line x1="200" y1="200" x2="94"  y2="306"/>
          <line x1="200" y1="200" x2="50"  y2="200"/>
          <line x1="200" y1="200" x2="94"  y2="94"/>
        </g>

        <!-- Polígono de scores — calcular con la fórmula de radar -->
        <polygon points="[puntos calculados]"
                 fill="rgba(196,150,58,0.12)" stroke="#C4963A" stroke-width="1.5"
                 style="animation: fadeIn 0.8s 0.4s both;"/>

        <!-- Puntos de datos -->
        <g fill="#C4963A">
          <!-- <circle cx="[x]" cy="[y]" r="4"/> para cada dimensión -->
        </g>

        <!-- Labels de ejes -->
        <g font-family="Inter,sans-serif" font-size="11" fill="#6B6860">
          <text x="200" y="42"  text-anchor="middle">Performance</text>
          <text x="316" y="90"  text-anchor="start">SEO</text>
          <text x="358" y="204" text-anchor="start">SEM</text>
          <text x="316" y="322" text-anchor="start">Diseño</text>
          <text x="200" y="368" text-anchor="middle">UX/UI</text>
          <text x="84"  y="322" text-anchor="end">Contenido</text>
          <text x="40"  y="204" text-anchor="end">Seguridad</text>
          <text x="84"  y="90"  text-anchor="end">Conversión</text>
        </g>
      </svg>

      <!-- Leyenda lateral con barras -->
      <div class="radar-legend">
        <!-- Por dimensión: -->
        <div class="radar-item [color-class]">
          <div>
            <div class="radar-item-name">[Nombre Dimensión]</div>
            <div class="radar-item-bar"><div class="radar-item-bar-fill" style="width:[score]%"></div></div>
          </div>
          <div class="radar-item-score">[score]</div>
        </div>
        <!-- ... 8 items -->
      </div>

    </div>
  </div>
</section>

<div class="gold-rule"></div>
```

### 6. DIMENSION DETAILS (fondo seccion-alt)

```html
<section class="dimensions-section">
  <div class="wrap">
    <div class="section-header">
      <p class="section-eyebrow">Análisis Detallado</p>
      <h2 class="section-title">Las 8 Dimensiones en Profundidad</h2>
    </div>

    <!-- Por cada dimensión: -->
    <div class="dimension [color-class]">
      <div class="dimension-aside">
        <span class="dimension-num">[score]</span>
        <div class="dimension-title">[Nombre]<br>& [Subtítulo]</div>
        <span class="dimension-grade">[Grade] · [Label]</span>
      </div>
      <div class="dimension-body">
        <h3>[Título descriptivo del estado de la dimensión]</h3>
        <p>[Párrafo de contexto y análisis — 3-5 oraciones]</p>
        <div class="findings">
          <div class="finding"><span class="finding-icon">✅</span><span>[Fortaleza]</span></div>
          <div class="finding"><span class="finding-icon">⚠️</span><span>[Advertencia]</span></div>
          <div class="finding"><span class="finding-icon">❌</span><span>[Problema crítico]</span></div>
        </div>
        <div class="recs">
          <div class="rec">
            <div class="rec-priority alta">Alta</div>
            <strong>[Título de la recomendación].</strong> [Descripción detallada con steps concretos].
          </div>
          <div class="rec">
            <div class="rec-priority media">Media</div>
            <strong>[Título].</strong> [Descripción].
          </div>
        </div>
      </div>
    </div>
    <!-- ... 8 dimensiones total -->

  </div>
</section>

<div class="gold-rule"></div>
```

### 7. ROADMAP (fondo obsidiana)

```html
<section class="roadmap-section">
  <div class="wrap">
    <div class="section-header">
      <p class="section-eyebrow">Plan de Acción</p>
      <h2 class="section-title">Roadmap Priorizado</h2>
    </div>
    <table>
      <thead>
        <tr>
          <th>Acción</th>
          <th>Dimensión</th>
          <th>Prioridad</th>
          <th>Impacto</th>
          <th>Esfuerzo</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>[Descripción de la acción]</td>
          <td>[Dimensión]</td>
          <td><span class="tag alta">Alta</span></td>
          <td><span class="tag alto">Alto</span></td>
          <td>[X días/horas]</td>
        </tr>
        <!-- filas ordenadas Alta→Media→Baja -->
      </tbody>
    </table>
  </div>
</section>
```

### 8. METHODOLOGY + FOOTER

```html
<section class="methodology">
  <div class="wrap">
    <p class="section-eyebrow" style="margin-bottom:12px;">Notas Metodológicas</p>
    <p>Esta auditoría evalúa el estado observable del sitio [URL] el [fecha]. El análisis cubre 8 dimensiones ponderadas: Performance (15%), SEO On-Page (15%), Diseño & Responsividad (15%), UX/UI & Accesibilidad (15%), SEM & Tracking (10%), Calidad del Contenido (10%), Seguridad Técnica (10%) y Optimización de Conversión (10%). El puntaje global es la suma ponderada de los 8 scores individuales.</p>
    <p style="margin-top:10px;">Limitación: el análisis evalúa el HTML estático entregado por el servidor. Para SPAs (React/Next/Vue), el HTML inicial puede estar incompleto. Complementar con Google PageSpeed Insights, GTmetrix, Ahrefs o Semrush para validación completa.</p>
  </div>
</section>

<footer>
  <div class="wrap">
    <div class="footer-inner">
      <div class="footer-brand">
        <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
          <polygon points="24,4 44,44 4,44" fill="none" stroke="#C4963A" stroke-width="1.8"/>
          <polygon points="24,14.5 35.5,38 12.5,38" fill="none" stroke="#C4963A" stroke-width="1.2"/>
        </svg>
        ASTOR
      </div>
      <p class="footer-copy">Auditoría Web Integral · [fecha] · astortech.io</p>
    </div>
  </div>
</footer>
```

---

## Logo SVG (inline — no depende de archivos externos)

```svg
<!-- 30×30px para topbar/footer -->
<svg width="30" height="30" viewBox="0 0 48 48" fill="none">
  <polygon points="24,4 44,44 4,44" fill="none" stroke="#C4963A" stroke-width="1.8"/>
  <polygon points="24,14.5 35.5,38 12.5,38" fill="none" stroke="#C4963A" stroke-width="1.2"/>
</svg>
```
