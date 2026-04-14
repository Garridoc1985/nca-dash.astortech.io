"""
Adaptador Robusto de Excel NCA
================================
Reemplaza las lecturas frágiles de generador_nca.py (basadas en posición fija)
por búsqueda dinámica de etiquetas.

Maneja automáticamente:
  - Filas/columnas desplazadas (se insertaron nuevas arriba o a la izquierda)
  - Filas/columnas eliminadas (retorna 0 sin lanzar error)
  - Etiquetas levemente renombradas (fuzzy matching)
  - Nuevas filas/columnas agregadas (simplemente se ignoran)

USO:
    from adaptador_excel import leer_eerr_robusto, leer_marketing_robusto
    # Reemplaza leer_eerr(xl) → leer_eerr_robusto(xl)
    # Reemplaza leer_marketing(xl) → leer_marketing_robusto(xl)
"""

import logging
from difflib import SequenceMatcher
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ─── SIMILITUD FUZZY ──────────────────────────────────────────────────────────

def _similitud(a: str, b: str) -> float:
    """Retorna similitud entre 0 y 1 entre dos strings (case-insensitive)."""
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def _mejor_match(texto: str, candidatos: list[str], umbral: float = 0.6) -> Optional[str]:
    """
    Encuentra el candidato más similar a `texto`.
    Retorna None si ninguno supera el umbral.
    """
    if not candidatos:
        return None
    scores = [(c, _similitud(texto, c)) for c in candidatos if isinstance(c, str)]
    if not scores:
        return None
    mejor, score = max(scores, key=lambda x: x[1])
    if score >= umbral:
        return mejor
    return None


# ─── BÚSQUEDA DINÁMICA EN DATAFRAME ──────────────────────────────────────────

def _buscar_fila(df: pd.DataFrame, etiqueta: str, col_buscar: int = 0) -> Optional[int]:
    """
    Busca la fila donde col_buscar contiene texto similar a `etiqueta`.
    Retorna el índice de fila o None si no la encuentra.
    """
    for i, row in df.iterrows():
        celda = str(row.iloc[col_buscar]).strip()
        if _similitud(etiqueta, celda) >= 0.7:
            return i
        # También intenta startswith fuzzy
        if celda.lower().startswith(etiqueta.lower()[:6]):
            return i
    return None


def _buscar_col(df: pd.DataFrame, nombre_col: str) -> Optional[int]:
    """
    Busca el índice de columna por nombre (fuzzy).
    Funciona tanto con headers como con columnas numéricas de posición.
    """
    cols_str = [str(c) for c in df.columns]
    match = _mejor_match(nombre_col, cols_str, umbral=0.65)
    if match is not None:
        return df.columns.tolist().index(df.columns[cols_str.index(match)])
    return None


def _v(val, default: float = 0.0) -> float:
    """Valor seguro — convierte a float o retorna default."""
    try:
        f = float(val)
        return f if pd.notna(f) else default
    except Exception:
        return default


# ─── LEER EERR ROBUSTO ────────────────────────────────────────────────────────

# Etiquetas que buscamos en columna 0 de la hoja EERR
EERR_ETIQUETAS = {
    "ingresos":    ["Ingresos", "Ingreso", "Total Ingresos", "Ventas"],
    "gs_personal": ["Gastos Personal", "RRHH", "Gasto Personal", "Personal"],
    "gs_admin":    ["Gastos Adm", "Gastos Administrativos", "Admin", "Gs Admin"],
    "gs_op":       ["Gastos Op", "Gastos Operacionales", "Operacional", "Gs Op"],
    "gs_no_op":    ["Gastos No Op", "No Operacional", "Gs No Op", "No Op"],
    "resultado":   ["Resultado", "Utilidad", "Resultado Neto", "Resultado Final"],
}

# Nombres de sucursales que buscamos en fila de headers de EERR
EERR_SUCURSAL_ETIQUETAS = [
    "TOTAL",
    "Guardia Vieja",
    "Camino el Alba",
    "Cerro El Plomo",
    "Encomenderos",
    "Estoril",
    "Vitacura",
    "Casa Matriz",
]

MES_MAP = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}

def _mes_num(mes_str: str) -> int:
    return MES_MAP.get(str(mes_str).lower().strip()[:4], 0)


def _detectar_cols_sucursal(df: pd.DataFrame) -> list[tuple[int, str]]:
    """
    Escanea todas las filas buscando los headers de sucursal.
    Retorna lista de (col_idx, nombre_sucursal).
    Maneja columnas agregadas, eliminadas o desplazadas.
    """
    resultado = []
    n_cols = len(df.columns)

    # Buscar en las primeras 10 filas
    for fila_idx in range(min(10, len(df))):
        fila = df.iloc[fila_idx]
        encontrados = []
        for col_idx in range(n_cols):
            celda = str(fila.iloc[col_idx]).strip()
            for etiqueta in EERR_SUCURSAL_ETIQUETAS:
                if _similitud(etiqueta, celda) >= 0.65:
                    encontrados.append((col_idx, etiqueta))
                    break

        if len(encontrados) >= 3:  # Si encontramos al menos 3 sucursales, usamos esta fila
            logger.info(f"[EERR] Headers de sucursal detectados en fila {fila_idx}: {[e[1] for e in encontrados]}")
            return encontrados

    # Fallback: usar posiciones originales
    logger.warning("[EERR] No se detectaron headers de sucursal — usando posiciones originales")
    return [(4, "TOTAL"), (8, "NCA Guardia Vieja"), (12, "NCA Camino el Alba"),
            (16, "NCA Cerro El Plomo"), (20, "NCA Encomenderos"),
            (24, "NCA Estoril"), (28, "NCA Vitacura"), (32, "Casa Matriz")]


def _detectar_fila_eerr(df: pd.DataFrame, clave: str) -> Optional[int]:
    """
    Busca la fila de un concepto EERR por múltiples etiquetas alternativas.
    Retorna índice de fila o None.
    """
    etiquetas = EERR_ETIQUETAS.get(clave, [clave])
    for etiqueta in etiquetas:
        fila = _buscar_fila(df, etiqueta, col_buscar=0)
        if fila is not None:
            logger.debug(f"[EERR] '{clave}' encontrado en fila {fila} con etiqueta '{etiqueta}'")
            return fila
    logger.warning(f"[EERR] '{clave}' NO encontrado — se usará 0")
    return None


def leer_eerr_robusto(xl) -> dict:
    """
    Versión robusta de leer_eerr().
    Detecta dinámicamente posición de filas y columnas de sucursales.
    """
    df = pd.read_excel(xl, sheet_name="EERR", header=None)

    # Año y mes — buscar en las primeras filas
    anio = 2026
    mes_str = "Marzo"
    for fila_idx in range(min(5, len(df))):
        for col_idx in range(len(df.columns)):
            val = str(df.iloc[fila_idx, col_idx]).strip()
            if val.isdigit() and int(val) in range(2020, 2035):
                anio = int(val)
            if _mes_num(val) > 0:
                mes_str = val.capitalize()

    logger.info(f"[EERR] Año={anio}, Mes={mes_str}")

    # Detectar columnas de sucursales
    cols_sucursales = _detectar_cols_sucursal(df)

    # Detectar filas de conceptos
    filas_conceptos = {}
    for clave in EERR_ETIQUETAS:
        filas_conceptos[clave] = _detectar_fila_eerr(df, clave)

    # Construir datos
    sucursales = []
    for col_start, nombre in cols_sucursales:
        row = {}
        for clave, fila_idx in filas_conceptos.items():
            if fila_idx is None:
                row[clave] = 0.0
                row[clave + "_ppto"] = 0.0
                row[clave + "_cumpl"] = 0.0
            else:
                # Valor real
                row[clave] = _v(df.iloc[fila_idx, col_start]) if col_start < len(df.columns) else 0.0
                # Presupuesto (col +1)
                row[clave + "_ppto"] = _v(df.iloc[fila_idx, col_start + 1]) if col_start + 1 < len(df.columns) else 0.0
                # Cumplimiento (col +3)
                row[clave + "_cumpl"] = _v(df.iloc[fila_idx, col_start + 3]) if col_start + 3 < len(df.columns) else 0.0
        row["nombre"] = nombre
        sucursales.append(row)

    return {
        "anio": anio,
        "mes": mes_str.capitalize(),
        "mes_num": _mes_num(mes_str),
        "sucursales": sucursales,
    }


# ─── LEER MARKETING ROBUSTO ──────────────────────────────────────────────────

# Nombres de columnas que buscamos en MARKETING
MKT_COL_ETIQUETAS = {
    "mes":      ["Mes", "Month", "Período", "Periodo"],
    "ventas24": ["Ventas 2024", "Venta 2024", "V 2024", "2024 Venta"],
    "ventas25": ["Ventas 2025", "Venta 2025", "V 2025", "2025 Venta"],
    "ventas26": ["Ventas 2026", "Venta 2026", "V 2026", "2026 Venta"],
    "mkt24":    ["Marketing 2024", "Mkt 2024", "Gasto Mkt 2024", "2024 Mkt"],
    "mkt25":    ["Marketing 2025", "Mkt 2025", "Gasto Mkt 2025", "2025 Mkt"],
    "mkt26":    ["Marketing 2026", "Mkt 2026", "Gasto Mkt 2026", "2026 Mkt"],
}


def _detectar_fila_header_mkt(df: pd.DataFrame) -> int:
    """
    Detecta en qué fila está el header de la tabla MARKETING.
    Busca la fila que contenga más palabras clave de columnas.
    """
    todas_etiquetas = [e for lista in MKT_COL_ETIQUETAS.values() for e in lista]

    mejor_fila = 3  # fallback original
    mejor_score = 0

    for fila_idx in range(min(15, len(df))):
        fila = df.iloc[fila_idx]
        score = 0
        for celda in fila:
            celda_str = str(celda).strip()
            for etiqueta in todas_etiquetas:
                if _similitud(etiqueta, celda_str) >= 0.65:
                    score += 1
                    break
        if score > mejor_score:
            mejor_score = score
            mejor_fila = fila_idx

    logger.info(f"[MARKETING] Header detectado en fila {mejor_fila} (score={mejor_score})")
    return mejor_fila


def _detectar_col_mkt(df_con_header: pd.DataFrame, clave: str) -> Optional[int]:
    """
    Encuentra el índice de columna en la hoja MARKETING para una clave dada.
    Usa fuzzy matching contra los nombres de columna detectados.
    """
    etiquetas = MKT_COL_ETIQUETAS.get(clave, [clave])
    cols = [str(c).strip() for c in df_con_header.columns]

    for etiqueta in etiquetas:
        match = _mejor_match(etiqueta, cols, umbral=0.60)
        if match is not None:
            idx = cols.index(match)
            logger.debug(f"[MARKETING] '{clave}' → columna '{match}' (idx={idx})")
            return idx

    # Último recurso: buscar por año en el nombre de columna
    if "24" in clave or "2024" in clave:
        for i, c in enumerate(cols):
            if "2024" in c or "24" in c:
                return i
    if "25" in clave or "2025" in clave:
        for i, c in enumerate(cols):
            if "2025" in c or "25" in c:
                return i
    if "26" in clave or "2026" in clave:
        for i, c in enumerate(cols):
            if "2026" in c or "26" in c:
                return i

    logger.warning(f"[MARKETING] Columna '{clave}' NO encontrada — se usará 0")
    return None


def leer_marketing_robusto(xl) -> dict:
    """
    Versión robusta de leer_marketing().
    Detecta dinámicamente fila de header y columnas de datos.
    """
    df_raw = pd.read_excel(xl, sheet_name="MARKETING", header=None)

    # Detectar fila de header
    fila_header = _detectar_fila_header_mkt(df_raw)

    # Aplicar header dinámico
    df = df_raw.copy()
    df.columns = df_raw.iloc[fila_header].tolist()
    df = df.iloc[fila_header + 1:].reset_index(drop=True)
    df = df.dropna(how="all")

    # Detectar índices de columnas relevantes
    col_idx = {}
    for clave in MKT_COL_ETIQUETAS:
        col_idx[clave] = _detectar_col_mkt(df, clave)

    # Leer filas de datos
    meses, ventas24, ventas25, ventas26, mkt24, mkt25, mkt26 = [], [], [], [], [], [], []

    for _, row in df.iterrows():
        # Columna de mes
        mes_val = ""
        if col_idx["mes"] is not None:
            mes_val = str(row.iloc[col_idx["mes"]]).strip() if col_idx["mes"] < len(row) else ""
        else:
            # Buscar en las primeras columnas algún nombre de mes
            for i in range(min(3, len(row))):
                if _mes_num(str(row.iloc[i])) > 0:
                    mes_val = str(row.iloc[i]).strip()
                    break

        if not mes_val or mes_val in ("nan", "Mes", "Month"):
            continue
        if _mes_num(mes_val) == 0:
            continue

        def _get(clave):
            idx = col_idx.get(clave)
            if idx is None or idx >= len(row):
                return 0.0
            return _v(row.iloc[idx])

        meses.append(mes_val.capitalize())
        ventas24.append(_get("ventas24"))
        ventas25.append(_get("ventas25"))
        ventas26.append(_get("ventas26"))
        mkt24.append(_get("mkt24"))
        mkt25.append(_get("mkt25"))
        mkt26.append(_get("mkt26"))

    logger.info(f"[MARKETING] {len(meses)} meses leídos: {meses}")

    def roi(v, m):
        return round(v / m, 1) if m and m > 0 else None

    roi_data = []
    for i, mes in enumerate(meses):
        roi_data.append({
            "mes": mes,
            "v24": ventas24[i], "m24": mkt24[i], "roi24": roi(ventas24[i], mkt24[i]),
            "v25": ventas25[i], "m25": mkt25[i], "roi25": roi(ventas25[i], mkt25[i]),
            "v26": ventas26[i], "m26": mkt26[i], "roi26": roi(ventas26[i], mkt26[i]),
        })

    return {
        "labels":        meses,
        "mkt_2024":      mkt24,
        "mkt_2025":      mkt25,
        "mkt_2026":      mkt26,
        "total_mkt_2024": sum(mkt24),
        "total_mkt_2025": sum(mkt25),
        "total_mkt_2026": sum(mkt26),
        "roi_data":      roi_data,
    }


# ─── WRAPPER: LECTURA ROBUSTA DE HOJAS CON HEADER ────────────────────────────

def leer_hoja_con_header_robusto(xl, sheet_name: str, cols_requeridas: list[str]) -> pd.DataFrame:
    """
    Lee una hoja con header de columnas.
    Si una columna requerida no existe, la crea con valor 0.
    Si hay columnas renombradas, intenta mapearlas con fuzzy matching.

    Útil para hojas: 1 VENTA, 2 RRHH, 3 GS ADMIN, 4 GS OP, 5 GS NO OP, VENTAS DETALLE
    """
    try:
        df = pd.read_excel(xl, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"[{sheet_name}] Error al leer hoja: {e}")
        # Retorna DataFrame vacío con las columnas requeridas
        return pd.DataFrame(columns=cols_requeridas)

    df.columns = [str(c).strip() for c in df.columns]
    cols_actuales = list(df.columns)

    for col_req in cols_requeridas:
        if col_req in cols_actuales:
            continue  # ya existe exacta

        # Intenta fuzzy match
        match = _mejor_match(col_req, cols_actuales, umbral=0.65)
        if match:
            logger.info(f"[{sheet_name}] Columna '{col_req}' mapeada desde '{match}'")
            df = df.rename(columns={match: col_req})
        else:
            logger.warning(f"[{sheet_name}] Columna '{col_req}' no encontrada — se agrega con 0")
            df[col_req] = 0

    return df


# ─── DIAGNÓSTICO ─────────────────────────────────────────────────────────────

def diagnosticar_excel(xl) -> dict:
    """
    Analiza el Excel y reporta qué hojas/columnas están presentes vs esperadas.
    Retorna dict con resumen de compatibilidad.
    """
    HOJAS_ESPERADAS = {
        "EERR": [],
        "FLUJO": [],
        "1 VENTA": ["Año", "Mes", "Sucursal", "Venta"],
        "VENTAS DETALLE": ["Fecha Venta", "Sucursal", "Tratamiento", "Venta"],
        "2 RRHH": ["Año", "Mes", "Sucursal", "Importe", "Tipo gasto"],
        "3 GS ADMIN": ["Año", "Mes", "Tipo de gasto", "Monto Bruto"],
        "4 GS OP": ["Año", "Mes", "Tipo de gasto", "Monto Bruto"],
        "5 GS NO OP": ["Tipo de gasto", "Monto Bruto", "Proveedor"],
        "MARKETING": [],
    }

    reporte = {}
    hojas_presentes = xl.sheet_names

    for hoja, cols_req in HOJAS_ESPERADAS.items():
        if hoja not in hojas_presentes:
            reporte[hoja] = {"estado": "FALTA_HOJA", "detalle": "Hoja no encontrada en el Excel"}
            logger.warning(f"[DIAGNÓSTICO] Hoja '{hoja}' NO encontrada")
            continue

        if not cols_req:
            reporte[hoja] = {"estado": "OK", "detalle": "Hoja presente (sin validación de columnas)"}
            continue

        try:
            df = pd.read_excel(xl, sheet_name=hoja, nrows=1)
            cols_act = [str(c).strip() for c in df.columns]
            faltantes = []
            mapeadas = []

            for col in cols_req:
                if col in cols_act:
                    continue
                match = _mejor_match(col, cols_act, umbral=0.65)
                if match:
                    mapeadas.append(f"'{col}' → '{match}'")
                else:
                    faltantes.append(col)

            if not faltantes and not mapeadas:
                reporte[hoja] = {"estado": "OK", "detalle": "Todas las columnas presentes"}
            elif not faltantes:
                reporte[hoja] = {"estado": "ADAPTADO", "detalle": f"Columnas renombradas: {', '.join(mapeadas)}"}
            else:
                reporte[hoja] = {"estado": "COLUMNAS_FALTANTES", "detalle": f"No encontradas: {', '.join(faltantes)}"}

        except Exception as e:
            reporte[hoja] = {"estado": "ERROR", "detalle": str(e)}

    return reporte
