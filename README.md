# NCA Clínicas — Dashboard Financiero & Analítico

> Sistema de análisis financiero y de ventas para una red de 7 clínicas estéticas en Chile.
> Desarrollado por **Sebastián Garrido** y **Santiago Mujica** — Astor Tech · 2026

---

## Etapas del desarrollo

### Etapa 1 — Temprana · Producto base
> Dashboard funcional con ETL desde Excel, servidores Flask y visualizaciones interactivas.

📄 [Ver documentación → `.claude/skills/README_NCA_proyecto.md`](.claude/skills/README_NCA_proyecto.md)

**Qué incluye:**
- Dashboard Financiero NCA con 8 módulos (EERR, Flujo, Ventas, RRHH, Gastos, Marketing)
- Dashboard de Ventas con normalización automática de reportes
- Autenticación con usuarios configurables
- Stack: Python, Flask, pandas, Chart.js

---

### Etapa 2 — Media · Pipeline IA de adaptación automática
> Sistema de 4 agentes que adapta el pipeline cuando el Excel del cliente cambia de estructura.

📄 [Ver documentación → `agentes/README.md`](agentes/README.md)

**Qué incluye:**
- `inspector.py` — detecta diferencias entre el Excel real y el schema esperado
- `mapper.py` — usa Claude AI para mapear columnas renombradas
- `reconstructor.py` — normaliza DataFrames antes del ETL
- `generador.py` — orquesta el pipeline completo
- `adaptador_excel.py` — adaptación rápida sin IA (fuzzy matching)

---

### Etapa 3 — Avanzada · Despliegue multi-plataforma
> Configuración lista para producción en Windows, Ubuntu y Hostinger VPS.

📄 [Ver documentación → `desarrollo NCA Beta/README.md`](desarrollo%20NCA%20Beta/README.md)

**Qué incluye:**
- Instalador automático para Ubuntu/Hostinger (`setup.sh`)
- Servidor WSGI con Gunicorn para producción (`wsgi.py`)
- Variables de entorno seguras (`.env.example`)
- Launchers para Windows (`iniciar.bat`) y Linux/Mac (`iniciar.sh`)

---

## Inicio rápido

**Windows:**
```
iniciar.bat instalar   ← primera vez
iniciar.bat            ← dashboard financiero  http://localhost:5000
iniciar.bat ventas     ← dashboard de ventas   http://localhost:5001
```

**Ubuntu / Hostinger:**
```bash
chmod +x "desarrollo NCA Beta/setup.sh"
"desarrollo NCA Beta/setup.sh"
"desarrollo NCA Beta/iniciar.sh"
```

---

## Demo en vivo

| Dashboard | URL | Acceso |
|---|---|---|
| **Financiero** | [dashboardfinancieronca.netlify.app](https://dashboardfinancieronca.netlify.app/) | Público |
| **Ventas** | [dashboardventasnca.netlify.app](https://dashboardventasnca.netlify.app/) | admin / nca2026 |

---

*Repositorio privado · Solo colaboradores autorizados*
