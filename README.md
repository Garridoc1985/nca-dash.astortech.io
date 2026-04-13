# NCA Clínicas — Dashboard Financiero & Analítico

> Sistema de análisis financiero y de ventas construido sobre 52.000+ transacciones reales de una red de 7 clínicas estéticas en Chile. Automatiza reportes que antes tomaban horas, entregando dashboards interactivos en menos de 30 segundos.

---

## Razón de ser

NCA Clínicas manejaba sus reportes financieros en Excel de forma manual. El proceso era lento, propenso a errores y dependía de una persona para producir los análisis. Este sistema reemplaza ese proceso completo:

1. El usuario sube el Excel → el sistema lo procesa y genera el dashboard automáticamente
2. Si el Excel cambia de estructura (columnas nuevas, filas eliminadas), el sistema **se adapta solo** sin errores
3. Disponible como aplicación web local o desplegable en servidor (Ubuntu, Hostinger)

---

## Demo en vivo

| Dashboard | URL | Acceso |
|---|---|---|
| **Financiero** (EERR, Flujo, RRHH, Gastos) | [dashboardfinancieronca.netlify.app](https://dashboardfinancieronca.netlify.app/) | Público |
| **Ventas** (49.693 registros) | [dashboardventasnca.netlify.app](https://dashboardventasnca.netlify.app/) | admin / nca2026 |

---

## Flujo completo del sistema

```
Excel NCA (.xlsx)
      │
      ▼
┌─────────────────────────────────────────────────┐
│  CAPA 1 · Diagnóstico (adaptador_excel.py)      │
│  • Detecta cambios de estructura en el Excel    │
│  • Busca columnas/filas por contenido, no posición │
│  • Auto-mapea renombradas con fuzzy matching    │
│  • Columnas eliminadas → retorna 0 sin error    │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  CAPA 2 · Pipeline IA (agentes/)                │
│  • inspector.py   → analiza estructura vs schema│
│  • mapper.py      → usa Claude AI para mapear  │
│  • reconstructor.py → normaliza DataFrames     │
│  • generador.py   → orquesta el pipeline       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  CAPA 3 · ETL + Generación (generador_nca.py)   │
│  • Lee 9 hojas del Excel                        │
│  • Calcula KPIs, tendencias, alertas            │
│  • Genera HTML con Chart.js (8 módulos)         │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  CAPA 4 · Servidor Web (servidor_nca.py)        │
│  • Login con usuarios configurables             │
│  • Upload del Excel vía interfaz web            │
│  • Entrega el dashboard HTML al navegador       │
└─────────────────────────────────────────────────┘
```

---

## Módulos del Dashboard Financiero

| Módulo | Contenido |
|---|---|
| **M1 · EERR** | Estado de Resultados por sucursal — ingresos, costos, margen, cumplimiento presupuesto |
| **M2 · Flujo de Caja** | Proyección mensual 2026, acumulado, composición de egresos |
| **M3 · Ventas** | Consolidado histórico 2024–2026 por sucursal |
| **M4 · Detalle Ventas** | Tratamientos, transacciones, formas de pago, top productos |
| **M5 · RRHH** | Gastos de personal 2025 vs 2026 por sucursal |
| **M6 · Gastos Adm/Op** | Gastos administrativos y operativos desglosados |
| **M7 · No Op + Mkt** | Gastos no operacionales y marketing con ROI |
| **M8 · Conclusiones** | Alertas automáticas, KPIs críticos, plan de acción |

---

## Dashboard de Ventas

Recibe cualquier formato de reporte de ventas, lo normaliza y genera:

- Ingresos por sucursal y período
- Top productos por ingresos y volumen
- Distribución de formas de pago
- Análisis de clientes: recurrencia, LTV, segmentación
- Tendencia mensual y estacionalidad

---

## Hallazgos clave (datos 2025)

Sobre **49.693 registros** y **$6.387M CLP** en ingresos anuales:

- **NCA Guardia Vieja** genera el 26,2% de ingresos con la menor tasa de cortesías (benchmark de eficiencia)
- **Top 10 tratamientos** concentran el 50,2% de ingresos — zona abdominal domina el catálogo
- **48,9% de los clientes** compran solo una vez → oportunidad de retención estimada en +$240M CLP anuales
- **Abril** es el mes valle estructural (-40% vs enero) → anticipar con campañas en Q1
- **Mercado Pago** representa el 50,6% de los ingresos — dependencia operativa relevante

---

## Estructura del proyecto

```
nca-dash.astortech.io/
│
├── servidor_nca.py              # App Flask — dashboard financiero (puerto 5000)
├── servidor_ventas.py           # App Flask — dashboard de ventas (puerto 5001)
├── users.example.json           # Estructura de usuarios (sin contraseñas reales)
├── config.example.ini           # Configuración de rutas de ejemplo
│
├── .claude/skills/
│   ├── dashboard-financiero-nca/
│   │   ├── generador_nca.py     # Motor ETL + HTML financiero (1.999 líneas)
│   │   └── adaptador_excel.py  # Auto-adaptación a cambios de estructura del Excel
│   └── data-analytics-pro/scripts/
│       ├── normalizar_reporte_ventas.py
│       ├── generador_html_ventas.py
│       └── analisis_financiero_nca.py
│
├── agentes/                     # Pipeline IA para adaptación avanzada
│   ├── PIPELINE_ASTOR_TECH.md  # Documentación del pipeline
│   ├── inspector.py             # Agente 1: detecta diferencias de estructura
│   ├── mapper.py                # Agente 2: mapea columnas con Claude AI
│   ├── reconstructor.py         # Agente 3: normaliza DataFrames
│   └── generador.py             # Agente 4: orquesta el pipeline completo
│
└── desarrollo NCA Beta/         # Archivos de instalación y despliegue
    ├── requirements.txt         # Dependencias Python
    ├── wsgi.py                  # Punto de entrada para Gunicorn (producción)
    ├── .env.example             # Plantilla de variables de entorno
    ├── setup.sh                 # Instalador automático Ubuntu/Hostinger
    ├── iniciar.sh               # Launcher Linux/Mac
    └── iniciar.bat              # Launcher Windows
```

---

## Instalación

### Windows (primera vez)

```
iniciar.bat instalar   ← instala dependencias
iniciar.bat            ← inicia dashboard financiero
iniciar.bat ventas     ← inicia dashboard de ventas
iniciar.bat ambos      ← inicia ambos
```

### Ubuntu / Hostinger VPS

```bash
git clone https://github.com/Garridoc1985/nca-dash.astortech.io
cd nca-dash.astortech.io
chmod +x "desarrollo NCA Beta/setup.sh"
"desarrollo NCA Beta/setup.sh"         # instala todo automáticamente
"desarrollo NCA Beta/iniciar.sh" prod  # arranca con Gunicorn
```

### Manual (cualquier plataforma)

```bash
pip install -r "desarrollo NCA Beta/requirements.txt"
cp users.example.json users.json       # editar con tus credenciales
python -X utf8 servidor_nca.py         # http://localhost:5000
python -X utf8 servidor_ventas.py      # http://localhost:5001
```

---

## Stack técnico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12, Flask 3.0 |
| Producción | Gunicorn (WSGI) |
| ETL / Análisis | pandas, openpyxl |
| Adaptación Excel | difflib (fuzzy matching) |
| Pipeline IA | Anthropic Claude API (agentes/) |
| Visualización | Chart.js 4.4, HTML/CSS/JS |
| Autenticación | Session-based, users.json |

---

## Notas de privacidad

- Repositorio **privado** — solo colaboradores autorizados tienen acceso
- `users.json`, `uploads/` y `output/` están en `.gitignore`
- El código no expone credenciales ni datos de pacientes

---

## Equipo

**Sebastián Garrido** — Product & Data Analyst  
[GitHub](https://github.com/Garridoc1985) · Santiago, Chile · 2026

**Santiago Mujica** — Co-desarrollador  
[GitHub](https://github.com/chacknorris) · Astor Tech
