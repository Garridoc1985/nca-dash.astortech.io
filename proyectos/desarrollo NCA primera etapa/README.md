# Exploración 1 · Motor de Dashboards

Dashboard funcional con ETL desde Excel, servidores Flask y visualizaciones interactivas.

**Alcance:** No utiliza agentes de IA. El ETL y la generación de visualizaciones son deterministas — pandas + lógica Python pura.

---

## Instalación

```bash
pip install -r requirements.txt
```

## Cómo correr

```bash
python -X utf8 servidor_nca.py     # http://localhost:5000
python -X utf8 servidor_ventas.py  # http://localhost:5001
```

Flujo: Login → subir Excel → dashboard HTML generado automáticamente en el navegador.

---

## Estructura

```
desarrollo primera etapa/
├── servidor_nca.py          # Flask NCA — puerto 5000
├── servidor_ventas.py       # Flask Ventas — puerto 5001
├── users.example.json       # Referencia de usuarios/contraseñas
├── motor/
│   ├── generador_nca.py     # Motor principal: 8 módulos financieros (1999 líneas)
│   ├── adaptador_excel.py   # ETL desde Excel NCA
│   └── ventas/
│       ├── generador_html_ventas.py       # Genera dashboard HTML de ventas
│       ├── normalizar_reporte_ventas.py   # Normaliza cualquier formato de reporte
│       └── analisis_financiero_nca.py     # Análisis financiero auxiliar
└── referencias/
    └── lecturas_fragiles.md  # Notas sobre hojas ETL con índice fijo
```

---

## Módulos del Dashboard NCA

| Módulo | Descripción |
|---|---|
| M1 EERR | Estado de Resultados por sucursal |
| M2 Flujo Caja | Proyección mensual 2026 + acumulado |
| M3 Ventas | Consolidado histórico 2024–2026 |
| M4 Detalle Ventas | Tratamientos y transacciones |
| M5 RRHH | Gastos de personal 2025 vs 2026 |
| M6 Gastos Adm/Op | Administrativos y operativos |
| M7 Gs No Op + Mkt | No operacionales y marketing |
| M8 Conclusiones | Alertas y plan de acción |

---

## Stack

- Python · Flask · pandas · numpy · openpyxl · Chart.js
- Autenticación configurable vía `users.json`
- Sin dependencias de agentes IA ni APIs externas

---

## Nota ETL

Las hojas **EERR** y **MARKETING** del Excel NCA se leen por índice de fila/columna fijo. No modificar la estructura del Excel sin revisar primero `referencias/lecturas_fragiles.md`.
