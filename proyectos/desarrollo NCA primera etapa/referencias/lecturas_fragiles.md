# Lecturas Frágiles — generador_nca.py

## Mapa de riesgo ETL

| Función | Hoja | Tipo de lectura | Riesgo |
|---|---|---|---|
| `leer_eerr()` | EERR | `iloc[fila, col]` fijos | **Alto** — si insertas fila/columna se rompe |
| `leer_flujo()` | FLUJO | Busca por texto de la primera celda | **Bajo** — flexible, busca "Ingresos", "Flujo Caja", etc. |
| `leer_marketing()` | MARKETING | `iloc[3]` header + `iloc[4:16]` filas fijas | **Medio** — si agregas meses más allá de fila 15 no los lee |
| Resto (RRHH, GS ADMIN, etc.) | varias | `pd.read_excel(..., header=0)` | **Ninguno** — lee todas las filas dinámicamente |

---

## Zonas frágiles en detalle

### Hoja EERR — Riesgo Alto

Usa índices fijos definidos en constantes al tope del script:

```python
EERR_SUCURSALES = [
    (4,  "TOTAL"),
    (8,  "NCA Guardia Vieja"),
    (12, "NCA Camino el Alba"),
    ...
]
EERR_ROWS = {
    "ingresos":   5,
    "gs_personal": 8,
    ...
}
```

**Qué puede romperlo:**
- Insertar o eliminar una fila en la hoja EERR
- Insertar o eliminar una columna antes de la columna D

**Qué NO lo rompe:**
- Actualizar números dentro de las celdas existentes
- Agregar datos en otras hojas

**Regla:** Nunca modificar la estructura (filas/columnas) de la hoja EERR. Solo actualizar valores.

---

### Hoja MARKETING — Riesgo Medio

```python
df.columns = df.iloc[3].tolist()   # fila 3 es el header
df = df.iloc[4:16]                 # filas 4 a 15 = 12 meses
```

**Qué puede romperlo:**
- Agregar meses más allá de la fila 15 (solo lee hasta fila 15)
- Mover el header a una fila distinta de la fila 3

**Qué NO lo rompe:**
- Actualizar valores de ventas y marketing dentro del rango existente

**Regla:** Mantener exactamente 12 meses en las filas 4–15. No insertar filas encima del header.

---

## Conclusión

Si solo actualizas números dentro del mismo formato Excel, ambos dashboards funcionan correctamente.
El riesgo aparece únicamente si reestructuras el Excel (insertar/eliminar filas o columnas).
