# Análisis de Ventas 2025 — NCA Clínicas
**Reporte EDA completo | Generado: 2026-03-25**
**Analista:** Claude Code (Senior Data Scientist)

---

## Índice
1. [Resumen General](#1-resumen-general)
2. [Ventas por Localidad / Sucursal](#2-ventas-por-localidad--sucursal)
3. [Tendencia Mensual](#3-tendencia-mensual)
4. [Top Productos](#4-top-productos)
5. [Formas de Pago](#5-formas-de-pago)
6. [Análisis de Clientes](#6-análisis-de-clientes)
7. [Descuentos y Cortesías](#7-descuentos-y-cortesías)
8. [Insights Clave](#8-insights-clave)

---

## 1. Resumen General

| Métrica | Valor |
|---|---|
| **Total registros (líneas)** | 49.693 |
| **Registros con pago > $0** | 30.627 |
| **Cortesías / gratuidades** | 19.066 (38,4% del total) |
| **Ventas únicas con pago** | 11.611 |
| **Ingresos totales (CLP)** | **$6.387.591.709** |
| **Ticket promedio por venta** | **$550.133** |
| **Clientes únicos (activos con pago)** | 5.319 |
| **Clientes totales en base** | 6.274 |
| **Artículos en catálogo** | 316 |
| **Período cubierto** | 2 enero 2025 → 31 diciembre 2025 |

> **Nota metodológica:** El dataset contiene 49.693 líneas de detalle. Un 38,4% corresponde a cortesías (descuento 100%), principalmente sesiones de control, invitados y cortesía clínica. El análisis de ingresos se realiza sobre las **30.627 líneas con pago real**, que corresponden a **11.611 ventas únicas** (identificadas por número de venta).

---

## 2. Ventas por Localidad / Sucursal

### Ranking por Ingresos

| Ranking | Sucursal | Ingresos (CLP) | Part. % | N° Ventas | Ticket Promedio |
|:---:|---|---:|:---:|---:|---:|
| 1 | **NCA Guardia Vieja** | $1.675.720.614 | 26,2% | 3.305 | $507.026 |
| 2 | NCA Face & Body | $903.245.274 | 14,1% | 1.664 | $542.816 |
| 3 | NCA Therapy | $812.008.770 | 12,7% | 1.268 | $640.385 |
| 4 | NCA Encomenderos | $809.028.804 | 12,7% | 1.727 | $468.459 |
| 5 | NCA Estoril | $757.966.672 | 11,9% | 1.192 | $635.878 |
| 6 | NCA Cerro El Plomo | $750.206.713 | 11,7% | 1.180 | $635.768 |
| 7 | NCA Camino el Alba | $679.414.862 | 10,6% | 1.275 | $532.874 |

**Observaciones:**
- **NCA Guardia Vieja es la sucursal dominante**, generando el 26,2% de los ingresos totales y siendo la única que supera el umbral de $1.000M anuales. Tiene además el mayor volumen de ventas (3.305), aunque con un ticket promedio bajo respecto a las sucursales más premium.
- Las sucursales **NCA Therapy, NCA Estoril y NCA Cerro El Plomo** tienen los **tickets promedio más altos** ($635k–$640k), lo que sugiere un perfil de cliente de mayor poder adquisitivo o un mix de tratamientos de mayor valor.
- **NCA Encomenderos** tiene el mayor número de ventas después de Guardia Vieja (1.727), pero un ticket promedio más bajo ($468k), lo que indica mayor rotación con tratamientos de menor precio.
- Las 5 sucursales principales concentran el **61,0%** de los ingresos.

---

## 3. Tendencia Mensual

### Ingresos y Volumen Enero–Diciembre 2025

| Mes | Ingresos (CLP) | N° Ventas | Ticket Prom. | Var. vs Mes Ant. |
|---|---:|:---:|---:|:---:|
| Enero | $612.492.221 | 1.037 | $590.639 | — |
| Febrero | $532.392.080 | 954 | $558.063 | -13,1% |
| Marzo | $471.314.235 | 935 | $504.079 | -11,5% |
| **Abril** | **$364.656.769** | **835** | **$436.715** | **-22,6%** |
| Mayo | $441.016.144 | 991 | $445.021 | +20,9% |
| Junio | $546.263.915 | 1.002 | $545.174 | +23,9% |
| Julio | $490.532.079 | 982 | $499.524 | -10,2% |
| Agosto | $501.501.508 | 904 | $554.758 | +2,2% |
| Septiembre | $537.911.900 | 888 | $605.757 | +7,3% |
| **Octubre** | **$721.298.358** | **1.135** | **$635.505** | **+34,1%** |
| Noviembre | $602.248.589 | 968 | $622.158 | -16,5% |
| Diciembre | $565.963.911 | 980 | $577.514 | -6,0% |

**Resumen de estacionalidad:**
- **Mes pico:** Octubre ($721M, +34,1% vs septiembre)
- **Mes valle:** Abril ($365M, el más bajo del año)
- **Rango de variación:** el mes más alto duplica ampliamente al más bajo (ratio 1,98x)
- **Coeficiente de variación mensual:** 17,1% — estabilidad moderada, con estacionalidad clara
- **Promedio mensual:** $532.299.309
- **Patrón detectado:** Caída sostenida en Q1 (enero→abril), recuperación progresiva en Q2-Q3, pico fuerte en octubre, y cierre de año moderado en noviembre-diciembre.

---

## 4. Top Productos

### Top 10 Artículos por Ingresos

| # | Artículo | Ingresos (CLP) | Part. % |
|:---:|---|---:|:---:|
| 1 | ONDA C. - Abdomen | $717.901.939 | 11,2% |
| 2 | MAXIMUS CORPORAL - abdomen | $424.525.907 | 6,6% |
| 3 | EMBODY - Abdomen | $325.515.336 | 5,1% |
| 4 | HIFU - abdomen | $309.263.183 | 4,8% |
| 5 | EXILIS CORPORAL - abdomen | $297.513.958 | 4,7% |
| 6 | LIPOESCULTURA TI - Abdomen | $271.794.805 | 4,3% |
| 7 | ONDA C. - Flancos | $253.668.825 | 4,0% |
| 8 | MAXIMUS C. - Abd y flancos | $248.341.141 | 3,9% |
| 9 | COCOON WELLNESS PRO | $231.982.310 | 3,6% |
| 10 | EXION - ABDOMEN/FLANCOS | $129.583.320 | 2,0% |

**Los Top 10 artículos concentran el 50,2% de los ingresos totales.**

### Top 10 Artículos por Cantidad Vendida

| # | Artículo | Unidades | Ingresos (CLP) |
|:---:|---|:---:|---:|
| 1 | ONDA C. - Abdomen | 3.430 | $717.901.939 |
| 2 | HIFU - abdomen | 2.140 | $309.263.183 |
| 3 | MAXIMUS CORPORAL - abdomen | 1.835 | $424.525.907 |
| 4 | LIPOESCULTURA TI - Abdomen | 1.462 | $271.794.805 |
| 5 | EXILIS CORPORAL - abdomen | 1.425 | $297.513.958 |
| 6 | ONDA C. - Flancos | 1.313 | $253.668.825 |
| 7 | MAXIMUS C. - Abd y flancos | 921 | $248.341.141 |
| 8 | EMBODY - Abdomen | 867 | $325.515.336 |
| 9 | HIFU - rostro | 716 | $88.488.389 |
| 10 | HIFU - flancos | 595 | $75.681.983 |

**Observaciones:**
- **ONDA C. - Abdomen** lidera tanto en ingresos (11,2%) como en unidades vendidas (3.430), siendo el producto estrella indiscutido.
- La zona **abdominal** domina el catálogo de ventas. Todos los top 10 por ingresos se concentran en tratamientos corporales de la zona abdomen/flancos.
- **HIFU** tiene alta demanda en unidades pero menor precio promedio por sesión que ONDA C., posicionándose como tratamiento de alta rotación a precio más accesible.
- El catálogo tiene **316 artículos**, pero los **10 principales generan la mitad de los ingresos**, evidenciando una distribución muy concentrada (tipo Pareto 80/20 agresivo).

---

## 5. Formas de Pago

| Forma de Pago | Ingresos (CLP) | Part. Ingresos | N° Transacciones | Part. Transacciones |
|---|---:|:---:|:---:|:---:|
| **Mercado Pago** | $3.230.282.235 | 50,6% | 13.427 | 43,8% |
| Tarjeta de Crédito | $2.062.431.895 | 32,3% | 9.686 | 31,6% |
| Tarjeta de Débito | $747.683.081 | 11,7% | 5.279 | 17,2% |
| Transferencia | $174.691.925 | 2,7% | 1.187 | 3,9% |
| Saldo por Pagar | $109.468.692 | 1,7% | 603 | 2,0% |
| Efectivo | $48.381.921 | 0,8% | 372 | 1,2% |
| WebPay | $11.071.960 | 0,2% | 53 | 0,2% |
| Cheque | $2.500.000 | 0,0% | 9 | 0,0% |
| Otro | $1.080.000 | 0,0% | 11 | 0,0% |

**Observaciones:**
- **Mercado Pago es la forma de pago dominante**, representando el 50,6% de los ingresos. Su ticket promedio por transacción ($240k) es superior al de débito, lo que indica que se usa tanto para pagos directos como para financiamiento en cuotas.
- **Tarjeta de Crédito** es la segunda forma de pago, con 32,3% de ingresos y un ticket promedio de $213k por transacción.
- Entre Mercado Pago y Tarjeta de Crédito cubren **82,9% de los ingresos totales**.
- El **efectivo representa solo el 0,8%**, evidenciando una clínica casi completamente digitalizada en sus cobros.
- **"Saldo por Pagar"** ($109M en 603 transacciones) podría representar deuda pendiente o pagos diferidos internos — merece seguimiento.

---

## 6. Análisis de Clientes

### Métricas de Base de Clientes

| Métrica | Valor |
|---|---|
| **Clientes únicos con pago** | 5.319 |
| **Clientes en base total** | 6.274 |
| **Compraron 1 sola vez** | 2.603 (48,9%) |
| **Recurrentes (2+ compras)** | 2.716 (51,1%) |
| **Frecuentes (3+ compras)** | 1.424 (26,8%) |
| **Muy frecuentes (5+ compras)** | 475 (8,9%) |
| **Promedio de compras por cliente** | 2,18 |
| **Máximo compras un cliente** | 24 |
| **LTV promedio** | $1.200.692 |
| **LTV mediana** | $928.000 |
| **Top 20% clientes generan** | 48,0% de ingresos |

### Top 15 Clientes por Gasto Total

| Cliente | Compras | Gasto Total (CLP) | Ticket Promedio |
|---|:---:|---:|---:|
| Correa, Javiera | 20 | $12.105.120 | $605.256 |
| Dell Orto, Andrea | 7 | $9.739.980 | $1.391.426 |
| Vasquez Medina, Claudia | 13 | $9.340.670 | $718.513 |
| Kass, Charline | 1 | $9.300.000 | $9.300.000 |
| Izquierdo, Paula | 14 | $9.245.970 | $660.426 |
| Sierralta, Natalia | 24 | $9.226.950 | $384.456 |
| Herrera, Elizabeth | 3 | $9.110.000 | $3.036.667 |
| Ortega Rubilar, Sandra | 11 | $8.560.000 | $778.182 |
| Olivares, Patricio | 10 | $8.350.000 | $835.000 |
| Garry, Andrea | 9 | $8.229.890 | $914.432 |
| Marin, Ximena | 20 | $8.135.000 | $406.750 |
| Lucy Bravo Riquelme | 9 | $7.760.000 | $862.222 |
| Pooley Donoso, Penelope | 8 | $7.620.000 | $952.500 |
| Campillay, Patricia | 5 | $7.618.000 | $1.523.600 |
| Bravo Ithurbisquy, Paula | 3 | $7.430.000 | $2.476.667 |

**Observaciones:**
- **Kass, Charline** y **Herrera, Elizabeth** se destacan por tickets altísimos en pocas visitas ($9,3M en 1 compra y $9,1M en 3), lo que sugiere compras de paquetes de alta gama o tratamientos de gran envergadura.
- **Sierralta, Natalia** (24 compras) y **Correa, Javiera** (20 compras) son los clientes más frecuentes del año, representando el perfil de paciente fiel de largo plazo.
- La **mediana LTV es $928k** vs un promedio de $1,2M, lo que indica una distribución sesgada hacia la derecha (unos pocos clientes con LTV muy alto elevan el promedio).
- El **top 20% de clientes genera el 48% de los ingresos** — patrón Pareto claro que justifica programas de fidelización diferenciados.

---

## 7. Descuentos y Cortesías

| Métrica | Valor |
|---|---|
| **Total descuentos otorgados** | $1.243.429.482 |
| **Registros con algún descuento** | 9.876 (19,9% del total) |
| **Descuento promedio (en registros con desc.)** | 99,9% |
| **Cortesías con 100% descuento** | 9.867 |

> La casi totalidad de los descuentos son **cortesías completas (100%)**, no descuentos parciales. Esto es coherente con el modelo de clínicas estéticas donde las sesiones de control o invitados se registran a precio cero.

### Descuentos por Sucursal

| Sucursal | Total Descuentos (CLP) |
|---|---:|
| NCA Face & Body | $583.396.758 |
| NCA Therapy | $471.458.700 |
| NCA Estoril | $78.034.282 |
| NCA Cerro El Plomo | $58.514.252 |
| NCA Encomenderos | $34.553.000 |
| NCA Camino el Alba | $16.394.990 |
| NCA Guardia Vieja | $1.110.000 |

**Observación notable:** NCA Face & Body y NCA Therapy concentran el **84,9% de todos los descuentos otorgados**, pero son sucursales con ingresos medios-altos. Esto puede indicar políticas de cortesía más permisivas en estas dos sedes, o que son las principales sucursales de presentación/captación de nuevos clientes. **NCA Guardia Vieja**, siendo la sucursal de mayor ingreso, otorga prácticamente cero cortesías ($1,1M), lo que refuerza su eficiencia comercial.

---

## 8. Insights Clave

### Insight 1: NCA Guardia Vieja es el motor del negocio — y opera de forma diferente

Con $1.675M en ingresos (26,2% del total) y 3.305 ventas únicas, Guardia Vieja duplica en volumen a cualquier otra sucursal. Sin embargo, su ticket promedio ($507k) es **el segundo más bajo** de la red. Esto sugiere un modelo de alta rotación con tratamientos más accesibles. Adicionalmente, prácticamente no otorga cortesías ($1,1M total versus $583M en Face & Body). Su eficiencia comercial merece ser replicada como benchmark.

### Insight 2: El catálogo está hiperconcentrado en tratamientos corporales del abdomen

Los 10 artículos más vendidos representan el **50,2% de los ingresos**, y todos corresponden a tratamientos corporales de la zona abdomen/flancos (ONDA C., MAXIMUS, HIFU, EMBODY, EXILIS, LIPOESCULTURA TI). Con 316 artículos en catálogo, el 80% de los ingresos probablemente viene de menos de 30–40 ítems. Esto es positivo para foco operacional, pero representa un riesgo de concentración si alguna tecnología cae en desuso o hay competencia de precios.

### Insight 3: La caída de abril es estructural y debe anticiparse

Abril 2025 registró solo $365M en ingresos, un -22,6% respecto a marzo y el valor más bajo del año. La caída desde enero ($612M) hasta abril ($365M) es un descenso acumulado del 40% en solo 4 meses. Este patrón estacional (verano chileno + Semana Santa) debería activar campañas proactivas de retención, prepagos y lanzamientos de paquetes en Q1 para suavizar la caída.

### Insight 4: Casi la mitad de los clientes compra solo una vez — hay una oportunidad de retención

El **48,9% de los clientes con pago registró solo 1 compra** en todo 2025. Con un LTV mediana de $928k y un promedio de $1,2M, convertir aunque sea el 10% de estos clientes de "una sola visita" en recurrentes representaría ingresos adicionales cercanos a **$240M anuales** (estimación: 260 clientes × $928k LTV). El programa de reactivación post-primera visita es la palanca de crecimiento de mayor impacto a corto plazo.

### Insight 5: Mercado Pago dominante y "Saldo por Pagar" como riesgo

Mercado Pago representa el 50,6% de los ingresos, lo que implica dependencia operativa y comisiones transaccionales significativas. Adicionalmente, existen $109M registrados como "Saldo por Pagar" en 603 transacciones — si parte de este monto no está siendo cobrado activamente, podría representar deuda incobrable. Se recomienda auditar este rubro y establecer un protocolo de seguimiento de cuentas pendientes.

---

## Anexo: Distribución de Precios (Registros con Pago)

| Rango de Precio Unitario | Registros | Part. % |
|---|:---:|:---:|
| < $10.000 | 2.113 | 6,9% |
| $10.000 – $30.000 | 1.028 | 3,4% |
| $30.000 – $60.000 | 1.237 | 4,0% |
| $60.000 – $100.000 | 4.048 | 13,2% |
| $100.000 – $200.000 | 10.133 | 33,1% |
| $200.000 – $500.000 | 10.918 | 35,7% |
| > $500.000 | 1.150 | 3,8% |

El grueso del catálogo opera en el rango **$100k–$500k por ítem** (68,8% de los registros), coherente con tratamientos de medicina estética de precio medio-alto en el mercado chileno.

---

## Metodología

- **Fuente:** `Reporte de ventas 2025.xlsx` — hoja `Sales`
- **Registros totales:** 49.693 líneas de detalle
- **Análisis de ingresos:** sobre 30.627 registros con `total_pagado > 0`
- **Ventas únicas:** identificadas por `no_venta` (número de venta), no por líneas
- **Clientes únicos para métricas:** sobre base de clientes con al menos una venta pagada (5.319)
- **Moneda:** CLP (pesos chilenos), sin ajuste inflacionario
- **Herramientas:** Python 3.12, pandas, numpy
- **Código fuente:** `salidas/eda_ventas_NCA_2025.py`

---

*Reporte generado por Claude Code para NCA Clínicas | 2026-03-25*
