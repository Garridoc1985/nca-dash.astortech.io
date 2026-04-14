# NCA Clínicas — Dashboard Financiero & Analítico

> Sistema de análisis financiero y de ventas para una red de 7 clínicas estéticas en Chile.
> Desarrollado por **Sebastián Garrido** y **Santiago Mujica** — Astor Tech · 2026

---

## Evolución de Exploraciones

### Exploración 1 · Motor de Dashboards
> Dashboard funcional con ETL desde Excel, servidores Flask y visualizaciones interactivas.

📄 [Ver documentación → `github/README_NCA_proyecto.md`](github/README_NCA_proyecto.md)

**Cómo corre:**
```bash
python -X utf8 servidor_nca.py     # http://localhost:5000
python -X utf8 servidor_ventas.py  # http://localhost:5001
```
Login → subir Excel → dashboard HTML generado automáticamente en el navegador.

> **Alcance:** no utiliza agentes de IA. El ETL y la generación de visualizaciones son deterministas — pandas + lógica Python pura.

**Qué incluye:**
- Dashboard Financiero NCA con 8 módulos (EERR, Flujo, Ventas, RRHH, Gastos, Marketing)
- Dashboard de Ventas con normalización automática de reportes
- Autenticación con usuarios configurables
- Stack: Python, Flask, pandas, Chart.js

---

### Exploración 2 · Adaptación Inteligente de Datos
> Sistema de 4 agentes que adapta el pipeline cuando el Excel del cliente cambia de estructura.

📄 [Ver documentación → `proyectos/desarrollo NCA con agentes/README.md`](proyectos/desarrollo%20NCA%20con%20agentes/README.md)

> **Origen:** creada para explorar cómo funciona un flujo con agentes e IA incorporada. Permite entender el comportamiento del pipeline cuando se delega a Claude AI la detección y resolución de cambios estructurales en los datos.

> **Alcance:** utiliza agentes de IA con Claude Haiku. El pipeline delega en Claude la interpretación semántica de columnas renombradas — lo que no es posible resolver de forma determinista. El resto del flujo (reconstrucción, generación del dashboard) sigue siendo Python puro.

**Qué incluye:**
- `inspector.py` — detecta diferencias entre el Excel real y el schema esperado
- `mapper.py` — usa Claude AI para mapear columnas renombradas
- `reconstructor.py` — normaliza DataFrames antes del ETL
- `generador.py` — orquesta el pipeline completo
- `adaptador_excel.py` — adaptación rápida sin IA (fuzzy matching)

---

### Exploración 3 · Infraestructura y Despliegue
> Configuración lista para producción en Windows, Ubuntu y VPS.

📄 [Ver documentación → `proyectos/desarrollo NCA Beta/README.md`](proyectos/desarrollo%20NCA%20Beta/README.md)

**Cómo corre:**
```bash
# Ubuntu / Hostinger
chmod +x "proyectos/desarrollo NCA Beta/setup.sh"
"proyectos/desarrollo NCA Beta/setup.sh"   # instala venv + dependencias
"proyectos/desarrollo NCA Beta/iniciar.sh" # levanta con Gunicorn en producción

# Windows
iniciar.bat instalar   # primera vez
iniciar.bat            # modo desarrollo
```

> **Alcance:** no utiliza agentes de IA. Es la capa de infraestructura y despliegue de los mismos servidores Flask de la Exploración 1, preparados para correr en producción. Los elementos desarrollados aquí — instalador, variables de entorno, servidor WSGI — fueron rescatados principalmente para robustecer y operacionalizar la Exploración 1.
>
> **Nota:** esta exploración se instala y corre en un VPS a definir con el cliente.

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
chmod +x "proyectos/desarrollo NCA Beta/setup.sh"
"proyectos/desarrollo NCA Beta/setup.sh"
"proyectos/desarrollo NCA Beta/iniciar.sh"
```

---

## Demo en vivo

| Dashboard | URL | Acceso |
|---|---|---|
| **Financiero** | [dashboardfinancieronca.netlify.app](https://dashboardfinancieronca.netlify.app/) | Público |
| **Ventas** | [dashboardventasnca.netlify.app](https://dashboardventasnca.netlify.app/) | admin / nca2026 |

---

*Repositorio privado · Solo colaboradores autorizados*
