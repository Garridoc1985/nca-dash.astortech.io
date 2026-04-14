# NCA Clínicas — Dashboard Financiero & Analítico

> **Caso de estudio real:** sistema de análisis de datos construido sobre 52.000+ transacciones financieras y 49.693 registros de ventas de una red de 7 clínicas estéticas en Chile.

## Demo en vivo

| Dashboard | URL | Acceso |
|---|---|---|
| **Financiero** (EERR, Flujo, RRHH, Gastos) | [dashboardfinancieronca.netlify.app](https://dashboardfinancieronca.netlify.app/) | Público |
| **Ventas** (49.693 registros, análisis clientes) | [dashboardventasnca.netlify.app](https://dashboardventasnca.netlify.app/) | Usuario: `admin` / Pass: `nca2026` |

---

## Descripción

Aplicación web local (Flask) que automatiza el proceso de:

1. **Ingesta** de archivos Excel con datos financieros y de ventas
2. **ETL** y normalización de datos con pandas
3. **Generación** de dashboards HTML interactivos con Chart.js
4. **Visualización** en el navegador, sin dependencias de servicios externos

El sistema reemplazó un proceso manual de reportes en Excel que tomaba varias horas, entregando análisis en menos de 30 segundos.

---

## Stack Técnico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Flask |
| ETL / Análisis | pandas, numpy |
| Visualización | Chart.js 4.4, HTML/CSS/JS |
| Datos | Excel (.xlsx), MySQL (`nca_db`) |
| Autenticación | Session-based, users.json |

---

## Módulos del Dashboard Financiero (`servidor_nca.py`)

| Módulo | Contenido |
|---|---|
| **M1 · EERR** | Estado de Resultados por sucursal — ingresos, costos, margen, cumplimiento presupuesto |
| **M2 · Flujo de Caja** | Proyección mensual 2026, acumulado, composición de egresos |
| **M3 · Ventas** | Consolidado histórico 2024–2026 por sucursal |
| **M4 · Detalle Ventas** | Tratamientos, transacciones, formas de pago, top productos |
| **M5 · RRHH** | Gastos de personal 2025 vs 2026 por sucursal |
| **M6 · Gastos Adm/Op** | Gastos administrativos y operativos desglosados |
| **M7 · No Op + Mkt** | Gastos no operacionales y marketing |
| **M8 · Conclusiones** | Alertas automáticas, KPIs críticos, plan de acción |

---

## Dashboard de Ventas (`servidor_ventas.py`)

Recibe **cualquier formato de reporte de ventas**, lo normaliza automáticamente y genera visualizaciones de:

- Ingresos por sucursal y por período
- Top productos por ingresos y por volumen
- Distribución de formas de pago
- Análisis de clientes: recurrencia, LTV, segmentación
- Tendencia mensual y estacionalidad

---

## Hallazgos Clave (Datos 2025)

Sobre **49.693 registros** y **$6.387M CLP** en ingresos anuales:

- **NCA Guardia Vieja** genera el 26,2% de los ingresos de la red, con la menor tasa de cortesías (eficiencia comercial benchmark)
- **Top 10 tratamientos** concentran el 50,2% de los ingresos — zona abdominal domina el catálogo
- **48,9% de los clientes** compran solo una vez → oportunidad de retención estimada en +$240M CLP anuales
- **Abril** es el mes valle estructural (-40% vs enero) → anticipar con campañas proactivas en Q1
- **Mercado Pago** representa el 50,6% de los ingresos — dependencia operativa relevante

---

## Estructura del Proyecto

```
nca-dash.astortech.io/
├── servidor_nca.py              # App Flask — dashboard financiero (puerto 5000)
├── servidor_ventas.py           # App Flask — dashboard de ventas (puerto 5001)
├── proyectos/
│   ├── desarrollo NCA con agentes/   # Pipeline multi-agente (prompt caching)
│   │   ├── inspector.py              # Agente 1: detecta diferencias de estructura
│   │   ├── mapper.py                 # Agente 2: genera mapa columna_real → esperada
│   │   ├── reconstructor.py          # Agente 3: normaliza DataFrames con el mapa
│   │   └── generador.py              # Agente 4: orquesta pipeline completo
│   └── desarrollo NCA Beta/          # Scripts de despliegue (Linux/Windows)
│       ├── setup.sh / iniciar.sh
│       └── iniciar.bat
├── .claude/skills/
│   ├── dashboard-financiero-nca/
│   │   ├── generador_nca.py          # Motor ETL + generación HTML (1.999 líneas)
│   │   └── adaptador_excel.py        # Adaptador robusto con fuzzy matching
│   └── data-analytics-pro/scripts/
│       ├── normalizar_reporte_ventas.py
│       └── generador_html_ventas.py
├── users.example.json           # Estructura de usuarios (sin contraseñas reales)
└── output/                      # Dashboards HTML generados (git-ignored)
```

---

## Pipeline Multi-Agente (`proyectos/desarrollo NCA con agentes/`)

Cuando el cliente entrega un Excel con columnas renombradas, el pipeline se adapta automáticamente sin intervención manual:

```
Excel del cliente
      │
      ▼
  Inspector    →  Detecta columnas faltantes o renombradas (Claude Haiku + prompt caching)
      │
      ▼
   Mapper      →  Genera mapa: columna_real → columna_esperada (Claude Haiku)
      │
      ▼
Reconstructor  →  Normaliza DataFrames aplicando el mapa
      │
      ▼
 Generador     →  Llama a generador_nca.py con datos normalizados → dashboard HTML
```

**Prompt caching:** el system prompt del Inspector (schema NCA + instrucciones) se cachea con `cache_control: ephemeral`, reduciendo latencia y costo en ejecuciones repetidas sobre el mismo tipo de archivo.

**Uso:**
```bash
python "proyectos/desarrollo NCA con agentes/generador.py" --file "ruta/al/archivo.xlsx"
```

---

## Instalación y Uso

### Requisitos

```bash
pip install flask pandas numpy openpyxl
```

### Dashboard Financiero

```bash
python -X utf8 servidor_nca.py
# Abre: http://localhost:5000
```

Flujo: Login → subir Excel NCA → dashboard generado automáticamente

### Dashboard de Ventas

```bash
python -X utf8 servidor_ventas.py
# Abre: http://localhost:5001
```

Flujo: Login → subir reporte de ventas → normalización → visualización

### Credenciales de prueba

Ver `users.example.json` para la estructura. Crear `users.json` con tus credenciales locales (no incluido en el repo por seguridad).

---

## Notas de Privacidad

- Los archivos en `inputs/` contienen datos reales de un cliente — el repositorio es **privado**
- El código no expone credenciales ni datos sensibles en texto plano
- `users.json` y `uploads/` están en `.gitignore`

---

## Autor

**Sebastián Garrido** — Product & Data Analyst
[GitHub](https://github.com/Garridoc1985) · Santiago, Chile · 2026
