# Pipeline Astor Tech — Sistema Multi-Agente de Adaptación Automática

> **Estado:** Operativo ✅ | **Versión:** 1.0 | **Fecha:** Abril 2026

---

## ¿Qué es esto?

Un sistema de 4 agentes de IA que automatiza la generación de dashboards financieros **incluso cuando el Excel del cliente cambia de estructura**.

Antes, si el cliente entregaba un Excel con columnas renombradas (ej. `Venta` → `Importe Total`), el pipeline fallaba y había que intervenir manualmente. Ahora el sistema detecta, interpreta y adapta los datos automáticamente antes de generar el dashboard.

---

## El problema que resuelve

```
Cliente entrega Excel v1       →  Pipeline genera dashboard ✅
Cliente entrega Excel v2
  (columnas renombradas)       →  Pipeline fallaba ❌ (antes)
                               →  Pipeline se adapta ✅ (ahora)
```

---

## Arquitectura: 4 agentes en secuencia

```
Excel del cliente
       │
       ▼
┌─────────────┐
│  INSPECTOR  │  Analiza la estructura del Excel
│             │  Detecta columnas faltantes o renombradas
│ inspector.py│  Usa Claude Haiku para análisis semántico
└──────┬──────┘
       │  ultimo_reporte_inspector.json
       ▼
┌─────────────┐
│   MAPPER    │  Lee el reporte del Inspector
│             │  Genera un mapa: columna_real → columna_esperada
│  mapper.py  │  Usa Claude Haiku para inferir equivalencias
└──────┬──────┘
       │  ultimo_mapa_columnas.json
       ▼
┌──────────────────┐
│  RECONSTRUCTOR   │  Lee el Excel con el mapa aplicado
│                  │  Renombra columnas al nombre que el generador espera
│ reconstructor.py │  Valida que todos los datos críticos estén presentes
└────────┬─────────┘
         │  DataFrames normalizados
         ▼
┌─────────────┐
│  GENERADOR  │  Orquesta los 3 agentes anteriores
│             │  Crea Excel temporal si hubo cambios
│ generador.py│  Llama al motor ETL → produce dashboard HTML
└──────┬──────┘
       │
       ▼
  Dashboard HTML
  (se abre en cualquier navegador)
```

---

## Cómo ejecutarlo

### Comando único

```bash
python -X utf8 proyectos/desarrollo NCA con agentes/generador.py --file "ruta/al/archivo.xlsx"
```

### Con ruta de salida personalizada

```bash
python -X utf8 proyectos/desarrollo NCA con agentes/generador.py \
  --file "inputs/EERR_NCA_Final.xlsx" \
  --output "output/dashboard_cliente.html"
```

### Reutilizando análisis previo (más rápido)

```bash
python -X utf8 proyectos/desarrollo NCA con agentes/generador.py \
  --file "inputs/EERR_NCA_Final.xlsx" \
  --skip-inspect
```

### Agentes individuales (para debug)

```bash
# Solo inspección
python -X utf8 proyectos/desarrollo NCA con agentes/inspector.py --file "archivo.xlsx" --json

# Solo mapeo (requiere reporte del inspector)
python -X utf8 proyectos/desarrollo NCA con agentes/mapper.py

# Solo reconstrucción (requiere mapa del mapper)
python -X utf8 proyectos/desarrollo NCA con agentes/reconstructor.py --file "archivo.xlsx"
```

---

## Archivos generados por el pipeline

| Archivo | Generado por | Contenido |
|---|---|---|
| `proyectos/desarrollo NCA con agentes/ultimo_reporte_inspector.json` | Inspector | Estructura real del Excel + diferencias vs. schema |
| `proyectos/desarrollo NCA con agentes/ultimo_mapa_columnas.json` | Mapper | Traducción columna_real → columna_esperada |
| `output/dashboard_*.html` | Generador | Dashboard financiero listo para el navegador |
| `logs/dashboard_nca_*.log` | Generador | Log detallado de la ejecución |

---

## Schema esperado (qué columnas necesita el generador)

| Hoja | Tipo lectura | Columnas críticas |
|---|---|---|
| EERR | Índice fijo | — (layout posicional) |
| FLUJO | Índice fijo | — (layout posicional) |
| MARKETING | Índice fijo | — (layout posicional) |
| 1 VENTA | Columnas | `Sucursal`, `Año`, `Mes`, `Venta` |
| VENTAS DETALLE | Columnas | `Fecha Venta`, `Sucursal`, `Tratamiento`, `Venta`, `Tipo Producto` |
| 2 RRHH | Columnas | `Sucursal`, `Año`, `Mes`, `Importe`, `Tipo gasto` |
| 3 GS ADMIN | Columnas | `Tipo de gasto`, `Monto Bruto`, `Año` |
| 4 GS OP | Columnas | `Tipo de gasto`, `Monto Bruto`, `Año` |
| 5 GS NO OP | Columnas | `Tipo de gasto`, `Monto Bruto`, `Proveedor`, `Año` |

> Las hojas de índice fijo se leen por posición (fila/columna numérica), no por nombre de columna. No modificar su estructura.

---

## Ejemplo real: resultado de la primera ejecución

```
Inspector → 18 hojas encontradas, 9 del schema, 9 auxiliares
Mapper    → Sin diferencias (schema ya coincide con el Excel actual)
Reconstructor → 9/9 hojas normalizadas, todas las columnas críticas OK
Generador → Dashboard HTML generado en 11 segundos
```

**Datos procesados:**
- 52.919 transacciones de venta
- 7 sucursales
- EERR: Enero 2026 — 8 sucursales
- Margen global: 41.5%

---

## Stack

| Componente | Tecnología |
|---|---|
| Agentes IA | Anthropic API — Claude Haiku 4.5 |
| ETL | Python 3.12, pandas, openpyxl |
| Dashboard | Chart.js 4.4, HTML/CSS/JS (self-contained) |
| Orquestación | Python nativo (subprocess) |

---

## Estructura de archivos

```
proyectos/desarrollo NCA con agentes/
├── inspector.py              # Agente 1: detecta diferencias de estructura
├── mapper.py                 # Agente 2: genera mapa de columnas con IA
├── reconstructor.py          # Agente 3: normaliza DataFrames
├── generador.py              # Agente 4: orquesta pipeline completo
├── ultimo_reporte_inspector.json   # Salida del Inspector
└── ultimo_mapa_columnas.json       # Salida del Mapper
```

---

## Próximos pasos posibles

- [ ] Interfaz web (Flask) para subir Excel y descargar dashboard sin tocar terminal
- [ ] Soporte multi-cliente (diferentes schemas por cliente)
- [ ] Notificación automática al detectar cambios críticos en el Excel
- [ ] Tests automáticos con Excels sintéticos

---

*Desarrollado por Sebastián Garrido — Astor Tech · 2026*
