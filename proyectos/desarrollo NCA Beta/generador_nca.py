"""
Generador Dashboard NCA
========================
Genera un dashboard financiero completo (8 módulos + segmentación de costos por sucursal) desde el Excel de NCA.

USO:
    python -X utf8 scripts/generar_dashboard_nca.py
    python -X utf8 scripts/generar_dashboard_nca.py --file "ruta/al/archivo.xlsx" --output "output/mi_dashboard.html"

MÓDULOS:
    M1 - EERR          : Estado de Resultados por sucursal (último mes disponible 2026)
    M2 - Flujo Caja    : Proyección flujo mensual 2026 + acumulado
    M3 - Ventas        : Consolidado histórico 2024-2026
    M4 - Detalle Ventas: Tratamientos y transacciones
    M5 - RRHH          : Gastos de personal 2025 vs 2026
    M6 - Gastos Adm/Op : Administrativos y operativos
    M7 - Gs No Op + Mkt: No operacionales y marketing
    M8 - Conclusiones  : Alertas y plan de acción
"""

import argparse
import configparser
import json
import logging
import sys
from pathlib import Path

import pandas as pd

# Skill está en .claude/skills/dashboard-financiero-nca/ → workspace es 3 niveles arriba
SKILL_DIR     = Path(__file__).parent
WORKSPACE     = SKILL_DIR.parent.parent.parent
CONFIG_FILE   = WORKSPACE / "config.ini"

# ─── CONFIGURACIÓN DE LOGGING ──────────────────────────────────────────────────
# Crear directorio de logs si no existe
from datetime import datetime
LOGS_DIR = WORKSPACE / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Formato de logging
log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
log_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S'))

# Handler para archivo (con timestamp)
log_filename = LOGS_DIR / f"dashboard_nca_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_filename, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(log_formatter)

# Configurar logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

def cargar_configuracion():
    """
    Lee config.ini o pregunta al usuario por la ruta del Excel.

    Returns:
        Path: Ruta válida del archivo Excel de NCA

    Raises:
        SystemExit: Si no encuentra archivo válido
    """
    excel_path = None

    # Intenta leer config.ini
    if CONFIG_FILE.exists():
        try:
            logger.info(f"📖 Leyendo configuración desde: {CONFIG_FILE}")
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE, encoding='utf-8')
            excel_path = config.get('excel', 'ruta_nca', fallback=None)
            if excel_path and Path(excel_path).exists():
                logger.info(f"✅ Excel cargado desde config: {Path(excel_path).name}")
                return Path(excel_path)
            elif excel_path:
                logger.warning(f"⚠️  Ruta en config.ini no existe: {excel_path}")
        except Exception as e:
            logger.warning(f"⚠️  Error leyendo config.ini: {e}")

    # Si no hay config válida, intentar modo interactivo con fallback robusto
    # En Windows, isatty() puede dar True aunque sea subprocess → usar try/except
    logger.info("📁 Modo interactivo: solicitando ruta del Excel")
    try:
        print("\n⚠️  No se encontró config.ini válida.")
        print(f"   Config esperada en: {CONFIG_FILE}\n")
        ruta = input("📁 Ingresá la ruta completa al archivo Excel de NCA:\n   → ").strip()
    except EOFError:
        # Sin stdin disponible (subprocess, servidor web, etc.)
        # El argumento --file lo sobreescribe en main()
        logger.info("📁 EOFError en input — usando placeholder (--file lo sobreescribe)")
        return Path("placeholder_excel.xlsx")

    excel_path = Path(ruta)
    if not excel_path.exists():
        logger.error(f"❌ Archivo no encontrado: {ruta}")
        sys.exit(1)

    logger.info(f"✅ Excel cargado: {excel_path.name}")
    return excel_path

EXCEL_DEFAULT = cargar_configuracion()
OUTPUT_DEFAULT = WORKSPACE / "output" / "dashboard_nca.html"

# Nombres de hojas por defecto (NCA original)
SHEET_DEFAULTS = {
    "eerr":           "EERR",
    "flujo":          "FLUJO",
    "ventas":         "1 VENTA",
    "ventas_detalle": "VENTAS DETALLE",
    "rrhh":           "2 RRHH",
    "gs_admin":       "3 GS ADMIN",
    "gs_op":          "4 GS OP",
    "gs_no_op":       "5 GS NO OP",
    "marketing":      "MARKETING",
}

def cargar_sheet_map() -> dict:
    """
    Lee la sección [sheets] de config.ini para permitir mapeo personalizado de hojas.
    Si una clave no está en config, usa el nombre por defecto de SHEET_DEFAULTS.
    """
    mapping = dict(SHEET_DEFAULTS)
    if CONFIG_FILE.exists():
        try:
            config = configparser.ConfigParser()
            config.read(CONFIG_FILE, encoding='utf-8')
            if config.has_section('sheets'):
                for key in SHEET_DEFAULTS:
                    val = config.get('sheets', key, fallback=None)
                    if val:
                        mapping[key] = val.strip()
        except Exception as e:
            logger.warning(f"⚠️  Error leyendo [sheets] de config.ini: {e}")
    return mapping

SHEET_MAP = cargar_sheet_map()

MES_MAP = {
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sept": 9, "sep": 9, "oct": 10, "nov": 11, "dic": 12,
}
MES_LABELS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
              "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

# Estructura EERR: col_start → nombre sucursal
EERR_SUCURSALES = [
    (4,  "TOTAL"),
    (8,  "NCA Guardia Vieja"),
    (12, "NCA Camino el Alba"),
    (16, "NCA Cerro El Plomo"),
    (20, "NCA Encomenderos"),
    (24, "NCA Estoril"),
    (28, "NCA Vitacura"),
    (32, "Casa Matriz"),
]
# Filas de la hoja EERR
EERR_ROWS = {
    "ingresos":     5,
    "gs_personal":  8,
    "gs_admin":    13,
    "gs_op":       22,
    "gs_no_op":    31,
    "resultado":   42,
}


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _v(val, default=0.0):
    """Valor seguro — convierte a float o retorna default."""
    try:
        f = float(val)
        return f if pd.notna(f) else default
    except Exception:
        return default


def _mes_num(mes_str: str) -> int:
    return MES_MAP.get(str(mes_str).lower().strip(), 0)


def _pct(a, b, default=0.0):
    try:
        return a / b * 100 if b and b != 0 else default
    except Exception:
        return default


def categorizar_concepto(tipo_gasto: str) -> str:
    """Mapea 'Tipo de gasto' a categorías resumidas para mostrar en tabla"""
    if not tipo_gasto:
        return "Otro"

    tipo = tipo_gasto.lower().strip()

    # Mapeos (ordenados por especificidad)
    if "tgr" in tipo or "tesorería" in tipo:
        return "Deuda Fiscal"
    elif "digital" in tipo or "comunicación" in tipo:
        return "Inversión Digital"
    elif "financiero" in tipo or "banco" in tipo:
        return "Financiero"
    elif "marketing" in tipo or "publicidad" in tipo:
        return "Marketing"
    elif "soporte" in tipo or "sistemas" in tipo or "ti" in tipo:
        return "Soporte TI"
    elif "aseo" in tipo or "servicios" in tipo or "ss " in tipo:
        return "Servicios"
    elif "asesorías" in tipo or "honorarios" in tipo or "consultoría" in tipo:
        return "Asesorías"
    elif "leasing" in tipo or "arrendamiento" in tipo:
        return "Leasing"
    elif "inversión" in tipo:
        return "Inversión"
    else:
        # Devolver primeras palabras significativas
        palabras = tipo.split()
        return " ".join(palabras[:2]).title() if palabras else "Otro"


# ─── DEFAULTS PARA MÓDULOS SIN HOJA ──────────────────────────────────────────

_Z12 = [0.0] * 12  # lista de 12 ceros para series mensuales

_DEFAULTS = {
    "eerr":   {"anio": 2026, "mes": "N/D", "mes_num": 0, "sucursales": []},
    "flujo":  {"saldo_inicial": _Z12, "ingresos": _Z12, "gs_rrhh": _Z12,
               "gs_adm_op": _Z12, "gs_nop": _Z12, "utilidad_neta": _Z12,
               "flujo_caja": _Z12, "flujo_acum": _Z12,
               "ppm_pct": _Z12, "ppm_val": _Z12, "labels": MES_LABELS},
    "ventas": {"labels": MES_LABELS, "ventas_2024": _Z12, "ventas_2025": _Z12,
               "ventas_2026": _Z12, "total_2024": 0, "total_2025": 0, "total_2026": 0,
               "sucursales": [], "suc_data": {}, "ticket_2024": 0, "ticket_2025": 0,
               "trans_2024": 0, "trans_2025": 0, "top_trat": [],
               "ticket_suc": [], "tipo_prod": [], "total_txns": 0},
    "rrhh":   {"labels": MES_LABELS, "rrhh_2025": _Z12, "rrhh_2026": _Z12,
               "total_2025": 0, "total_2026": 0, "tipo_gasto": []},
    "adm_op": {"adm_tipo": [], "op_tipo": [], "adm_total": 0, "op_total": 0,
               "adm_series": {}, "op_series": {}},
    "no_op":  {"tipo": [], "proveedores": [], "total": 0,
               "total_2025": 0, "total_2026": 0, "digital_2025": 0, "digital_2026": 0},
    "mkt":    {"labels": MES_LABELS, "mkt_2024": _Z12, "mkt_2025": _Z12,
               "mkt_2026": _Z12, "total_mkt_2024": 0, "total_mkt_2025": 0,
               "total_mkt_2026": 0, "roi_data": []},
    "seg":    {"por_sucursal": [], "margen_pct_global": 0.0,
               "total_ingresos": 0, "total_costos": 0, "total_margen": 0},
}


def _leer_safe(fn, xl, key: str):
    """
    Ejecuta fn(xl) y devuelve su resultado.
    Si la hoja no existe (ValueError), registra el aviso y devuelve el dict vacío
    correspondiente, permitiendo que el dashboard se genere de todas formas.
    """
    try:
        return fn(xl)
    except ValueError as e:
        logger.warning(f"⚠️  Módulo '{key}' omitido — {e}")
        print(f"OMITIDO ({e})")
        return dict(_DEFAULTS[key])
    except Exception as e:
        logger.warning(f"⚠️  Módulo '{key}' con error inesperado — {e}")
        print(f"ERROR ({e})")
        return dict(_DEFAULTS[key])


# ─── ETL: EERR ────────────────────────────────────────────────────────────────

def leer_eerr(xl) -> dict:
    """Lee hoja EERR → dict con datos por sucursal del último mes disponible."""
    df = pd.read_excel(xl, sheet_name=SHEET_MAP["eerr"], header=None)

    # Determinar año/mes
    anio = _v(df.iloc[0, 3], 2026)
    mes_str = str(df.iloc[1, 3]).strip()
    mes_num = _mes_num(mes_str)

    sucursales = []
    for col_start, nombre in EERR_SUCURSALES:
        row = {}
        for key, row_idx in EERR_ROWS.items():
            row[key]      = _v(df.iloc[row_idx, col_start])
            row[key+"_ppto"] = _v(df.iloc[row_idx, col_start + 1])
            row[key+"_cumpl"] = _v(df.iloc[row_idx, col_start + 3])
        row["nombre"] = nombre
        sucursales.append(row)

    return {
        "anio": int(anio),
        "mes": mes_str.capitalize(),
        "mes_num": mes_num,
        "sucursales": sucursales,
    }


# ─── ETL: FLUJO ───────────────────────────────────────────────────────────────

def leer_flujo(xl) -> dict:
    """Lee hoja FLUJO → dict con datos de flujo mensual 2026."""
    df = pd.read_excel(xl, sheet_name=SHEET_MAP["flujo"], header=None)

    # Fila 2 tiene header (Item/Mes | fechas)
    # Cols 1-12 son los meses
    def get_row(label_partial):
        for i, row in df.iterrows():
            if str(row.iloc[0]).strip().lower().startswith(label_partial.lower()):
                return [_v(row.iloc[c]) for c in range(1, 13)]
        return [0.0] * 12

    ingresos      = get_row("Ingresos")
    gs_rrhh       = get_row("Costos RRHH")
    gs_adm_op     = get_row("Gastos de Adm")
    gs_nop        = get_row("Total Gastos No")
    utilidad_neta = get_row("Utilidad Neta")
    flujo_caja    = get_row("Flujo Caja")
    flujo_acum    = get_row("Flujo Caja Acumulado")
    ppm_pct       = get_row("% ppm")
    ppm_val       = get_row("ppm")
    saldo_ini     = _v(df.iloc[3, 1], 160_000_000)

    return {
        "saldo_inicial": saldo_ini,
        "ingresos":      ingresos,
        "gs_rrhh":       gs_rrhh,
        "gs_adm_op":     gs_adm_op,
        "gs_nop":        gs_nop,
        "utilidad_neta": utilidad_neta,
        "flujo_caja":    flujo_caja,
        "flujo_acum":    flujo_acum,
        "ppm_pct":       ppm_pct,
        "ppm_val":       ppm_val,
        "labels":        MES_LABELS,
    }


# ─── ETL: VENTAS ──────────────────────────────────────────────────────────────

def leer_ventas(xl) -> dict:
    """Lee 1 VENTA y VENTAS DETALLE → dict con consolidados y tratamientos."""
    # Mensual por año/mes/sucursal
    df1 = pd.read_excel(xl, sheet_name=SHEET_MAP["ventas"])
    df1["mes_num"] = df1["Mes"].apply(_mes_num)
    df1 = df1[df1["mes_num"] > 0]

    # Agregados por año/mes
    by_anio_mes = (
        df1.groupby(["Año", "mes_num"])["Venta"]
        .sum()
        .reset_index()
        .sort_values(["Año", "mes_num"])
    )

    def serie_anual(anio):
        sub = by_anio_mes[by_anio_mes["Año"] == anio]
        vals = [0.0] * 12
        for _, r in sub.iterrows():
            idx = int(r["mes_num"]) - 1
            if 0 <= idx < 12:
                vals[idx] = _v(r["Venta"])
        return vals

    ventas_2024 = serie_anual(2024)
    ventas_2025 = serie_anual(2025)

    # Por sucursal por año — solo históricos
    by_suc_anio = (
        df1.groupby(["Sucursal", "Año"])["Venta"]
        .sum()
        .reset_index()
    )
    sucursales = sorted(df1["Sucursal"].dropna().unique().tolist())

    suc_data = {}
    for suc in sucursales:
        suc_data[suc] = {}
        for anio in [2024, 2025]:
            sub = by_suc_anio[(by_suc_anio["Sucursal"] == suc) & (by_suc_anio["Año"] == anio)]
            suc_data[suc][anio] = _v(sub["Venta"].sum()) if len(sub) else 0.0

    # Ticket promedio mensual (transacciones desde VENTAS DETALLE)
    df_det = pd.read_excel(xl, sheet_name=SHEET_MAP["ventas_detalle"])
    df_det["Año"]     = df_det["Fecha Venta"].dt.year
    df_det["mes_num"] = df_det["Fecha Venta"].dt.month

    ticket_2024 = _ticket_serie(df_det, 2024)
    ticket_2025 = _ticket_serie(df_det, 2025)

    # Transacciones mensuales
    trans_2024 = _trans_serie(df_det, 2024)
    trans_2025 = _trans_serie(df_det, 2025)

    # Top tratamientos
    top_trat = (
        df_det.groupby("Tratamiento")
        .agg(sesiones=("Venta", "count"), ingresos=("Venta", "sum"))
        .reset_index()
        .sort_values("ingresos", ascending=False)
        .head(10)
    )
    top_trat["ticket_prom"] = top_trat["ingresos"] / top_trat["sesiones"]
    top_trat_list = top_trat.to_dict(orient="records")

    # Ticket por sucursal (promedio histórico)
    ticket_suc = (
        df_det.groupby("Sucursal")
        .agg(ventas=("Venta", "sum"), txns=("Venta", "count"))
        .reset_index()
    )
    ticket_suc["ticket"] = ticket_suc["ventas"] / ticket_suc["txns"]

    # Tipo producto mix
    tipo_prod = (
        df_det.groupby("Tipo Producto")["Venta"]
        .sum()
        .reset_index()
        .sort_values("Venta", ascending=False)
    )

    return {
        "labels":       MES_LABELS,
        "ventas_2024":  ventas_2024,
        "ventas_2025":  ventas_2025,
        "total_2024":   sum(ventas_2024),
        "total_2025":   sum(ventas_2025),
        "sucursales":   sucursales,
        "suc_data":     suc_data,
        "ticket_2024":  ticket_2024,
        "ticket_2025":  ticket_2025,
        "trans_2024":   trans_2024,
        "trans_2025":   trans_2025,
        "top_trat":     top_trat_list,
        "ticket_suc":   ticket_suc.to_dict(orient="records"),
        "tipo_prod":    tipo_prod.to_dict(orient="records"),
        "total_txns":   int(len(df_det)),
    }


def _ticket_serie(df, anio):
    sub = df[df["Año"] == anio]
    vals = [0.0] * 12
    for m in range(1, 13):
        rows = sub[sub["mes_num"] == m]
        if len(rows) > 0:
            vals[m - 1] = _v(rows["Venta"].sum()) / len(rows)
    return vals


def _trans_serie(df, anio):
    sub = df[df["Año"] == anio]
    vals = [0] * 12
    for m in range(1, 13):
        vals[m - 1] = int(len(sub[sub["mes_num"] == m]))
    return vals


# ─── ETL: RRHH ────────────────────────────────────────────────────────────────

def leer_rrhh(xl) -> dict:
    df = pd.read_excel(xl, sheet_name=SHEET_MAP["rrhh"])
    df["mes_num"] = df["Mes"].apply(_mes_num)
    df = df[df["mes_num"] > 0]

    def serie_mensual(anio):
        sub = df[df["Año"] == anio].groupby("mes_num")["Importe"].sum().reset_index()
        vals = [0.0] * 12
        for _, r in sub.iterrows():
            idx = int(r["mes_num"]) - 1
            if 0 <= idx < 12:
                vals[idx] = _v(r["Importe"])
        return vals

    rrhh_2025 = serie_mensual(2025)
    rrhh_2026 = serie_mensual(2026)

    # Por tipo gasto
    tipo_gasto = (
        df[df["Año"] >= 2025]
        .groupby("Tipo gasto")["Importe"]
        .sum()
        .reset_index()
        .sort_values("Importe", ascending=False)
    )

    # RRHH por sucursal — solo 2025 (histórico)
    rrhh_suc_2025 = df[df["Año"] == 2025].groupby("Sucursal")["Importe"].sum()

    # Ratio RRHH/Ventas por sucursal (2025)
    df_v1 = pd.read_excel(xl, sheet_name=SHEET_MAP["ventas"])
    v2025_suc = df_v1[df_v1["Año"] == 2025].groupby("Sucursal")["Venta"].sum()

    sucursales_ratio = sorted(set(list(rrhh_suc_2025.index) + list(v2025_suc.index)))
    ratio_suc = []
    for s in sucursales_ratio:
        # Excluir Casa Matriz (no es operativa, no genera ventas)
        if s == "Casa Matriz":
            continue
        rrhh_v = _v(rrhh_suc_2025.get(s, 0))
        venta_v = _v(v2025_suc.get(s, 0))
        ratio_suc.append({
            "suc":   s.replace("NCA ", ""),
            "rrhh":  _jnum(rrhh_v),
            "venta": _jnum(venta_v),
            "ratio": _jnum(_pct(rrhh_v, venta_v) if venta_v > 0 else 0, 1),
        })
    ratio_suc.sort(key=lambda x: x["ratio"], reverse=True)

    rrhh_suc = (
        df[df["Año"] == 2025]
        .groupby("Sucursal")["Importe"]
        .sum()
        .reset_index()
        .rename(columns={"Importe": "rrhh"})
    )

    return {
        "labels":     MES_LABELS,
        "rrhh_2025":  rrhh_2025,
        "total_2025": sum(rrhh_2025),
        "tipo_gasto": tipo_gasto.to_dict(orient="records"),
        "rrhh_suc":   rrhh_suc.to_dict(orient="records"),
        "ratio_suc":  ratio_suc,
    }


# ─── ETL: GASTOS ADMIN + OP ───────────────────────────────────────────────────

def leer_admin_op(xl) -> dict:
    df_adm = pd.read_excel(xl, sheet_name=SHEET_MAP["gs_admin"])
    df_op  = pd.read_excel(xl, sheet_name=SHEET_MAP["gs_op"])

    adm_tipo = (
        df_adm.groupby("Tipo de gasto")["Monto Bruto"]
        .sum()
        .reset_index()
        .sort_values("Monto Bruto", ascending=False)
    )
    op_tipo = (
        df_op.groupby("Tipo de gasto")["Monto Bruto"]
        .sum()
        .reset_index()
        .sort_values("Monto Bruto", ascending=False)
    )

    # Mensual
    def serie_mensual(df, col_anio="Año", col_mes="Mes"):
        df2 = df.copy()
        df2["mes_num"] = df2[col_mes].apply(_mes_num)
        by_m = df2.groupby(["Año", "mes_num"])["Monto Bruto"].sum().reset_index()
        anios = sorted(by_m["Año"].dropna().unique())
        series = {}
        for a in anios:
            sub = by_m[by_m["Año"] == a]
            vals = [0.0] * 12
            for _, r in sub.iterrows():
                idx = int(r["mes_num"]) - 1
                if 0 <= idx < 12:
                    vals[idx] = _v(r["Monto Bruto"])
            series[int(a)] = vals
        return series

    return {
        "adm_tipo":  adm_tipo.to_dict(orient="records"),
        "op_tipo":   op_tipo.to_dict(orient="records"),
        "adm_total": _v(df_adm["Monto Bruto"].sum()),
        "op_total":  _v(df_op["Monto Bruto"].sum()),
        "adm_series": serie_mensual(df_adm),
        "op_series":  serie_mensual(df_op),
    }


# ─── ETL: GASTOS NO OP ────────────────────────────────────────────────────────

def leer_no_op(xl) -> dict:
    df = pd.read_excel(xl, sheet_name=SHEET_MAP["gs_no_op"])

    tipo = (
        df.groupby("Tipo de gasto")["Monto Bruto"]
        .sum()
        .reset_index()
        .sort_values("Monto Bruto", ascending=False)
    )
    proveedores = (
        df.groupby("Proveedor")
        .agg({"Monto Bruto": "sum", "Tipo de gasto": lambda x: x.iloc[0]})
        .reset_index()
        .sort_values("Monto Bruto", ascending=False)
        .head(10)
    )

    # Totales — solo 2025 histórico
    total_by_year = df.groupby("Año")["Monto Bruto"].sum().to_dict()
    total_2025 = _v(total_by_year.get(2025, 0))

    # Digital — solo 2025 histórico
    df_dig = df[df["Tipo de gasto"].str.lower().str.contains("digital", na=False)]
    dig_by_year = df_dig.groupby("Año")["Monto Bruto"].sum().to_dict()
    digital_2025 = _v(dig_by_year.get(2025, 0))

    return {
        "tipo":         tipo.to_dict(orient="records"),
        "proveedores":  proveedores.to_dict(orient="records"),
        "total":        _v(df["Monto Bruto"].sum()),
        "total_2025":   total_2025,
        "digital_2025": digital_2025,
    }


# ─── ETL: MARKETING ───────────────────────────────────────────────────────────

def leer_marketing(xl) -> dict:
    df = pd.read_excel(xl, sheet_name=SHEET_MAP["marketing"], header=None)
    # Fila 3 es el header
    df.columns = df.iloc[3].tolist()
    df = df.iloc[4:16].reset_index(drop=True)
    df = df.dropna(how="all")

    meses, ventas24, ventas25, mkt24, mkt25 = [], [], [], [], []
    for _, row in df.iterrows():
        mes = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        if not mes or mes in ("nan", "Mes"):
            continue
        meses.append(mes.capitalize())
        ventas24.append(_v(row.iloc[2]))
        ventas25.append(_v(row.iloc[3]))
        mkt24.append(_v(row.iloc[7]))
        mkt25.append(_v(row.iloc[8]))

    def roi(v, m):
        if m and m > 0:
            return round(v / m, 1)
        return None

    roi_data = []
    for i, mes in enumerate(meses):
        roi_data.append({
            "mes": mes,
            "v24": ventas24[i], "m24": mkt24[i], "roi24": roi(ventas24[i], mkt24[i]),
            "v25": ventas25[i], "m25": mkt25[i], "roi25": roi(ventas25[i], mkt25[i]),
        })

    return {
        "labels":  meses,
        "mkt_2024": mkt24,
        "mkt_2025": mkt25,
        "total_mkt_2024": sum(mkt24),
        "total_mkt_2025": sum(mkt25),
        "roi_data":  roi_data,
    }


# ─── ETL: SEGMENTACIÓN DE COSTOS POR SUCURSAL ────────────────────────────────

def segmentar_costos(xl) -> dict:
    """
    Distribuye RRHH, Admin, Op y No Op por sucursal usando las reglas NCA:
      RRHH:        40% fijo (uniforme) + 60% según ventas
      Admin:       100% uniforme
      Operativo:   100% según sesiones (transacciones)
      No Operativo: 30% fijo (uniforme) + 70% según ventas
    Retorna dict con resumen por sucursal y totales globales.
    """
    # Ventas mensuales por sucursal (desde hoja 1 VENTA)
    df1 = pd.read_excel(xl, sheet_name=SHEET_MAP["ventas"])
    df1["mes_num"] = df1["Mes"].apply(_mes_num)
    df1 = df1[df1["mes_num"] > 0].copy()
    df1["Periodo"] = df1.apply(lambda r: f"{int(r['Año'])}-{int(r['mes_num']):02d}", axis=1)
    df_ventas_agg = (
        df1.groupby(["Periodo", "Sucursal"])["Venta"]
        .sum().reset_index().rename(columns={"Venta": "Ingresos"})
    )

    # Transacciones por periodo+sucursal (desde VENTAS DETALLE)
    df_det = pd.read_excel(xl, sheet_name=SHEET_MAP["ventas_detalle"])
    df_det["Año"]     = df_det["Fecha Venta"].dt.year
    df_det["mes_num"] = df_det["Fecha Venta"].dt.month
    df_det["Periodo"] = df_det.apply(lambda r: f"{int(r['Año'])}-{int(r['mes_num']):02d}", axis=1)
    df_trans = (
        df_det.groupby(["Periodo", "Sucursal"]).size()
        .reset_index(name="Num_Transacciones")
    )

    df_base = df_ventas_agg.merge(df_trans, on=["Periodo", "Sucursal"], how="left")
    df_base["Num_Transacciones"] = df_base["Num_Transacciones"].fillna(0)

    # Pesos de distribución por periodo
    tot_ing = df_base.groupby("Periodo")["Ingresos"].transform("sum")
    df_base["Pct_Ventas"]   = df_base["Ingresos"] / tot_ing.where(tot_ing > 0, 1)
    tot_ses = df_base.groupby("Periodo")["Num_Transacciones"].transform("sum")
    df_base["Pct_Sesiones"] = df_base["Num_Transacciones"] / tot_ses.where(tot_ses > 0, 1)
    n_suc = df_base.groupby("Periodo")["Sucursal"].transform("count")
    df_base["Pct_Uniforme"] = 1.0 / n_suc

    # Lee costos mensuales totales de cada hoja
    def costos_por_periodo(sheet, col_monto):
        df = pd.read_excel(xl, sheet_name=sheet)
        df.columns = [c.strip() for c in df.columns]
        df["mes_num"] = df["Mes"].apply(_mes_num)
        df = df[df["mes_num"] > 0].copy()
        df["Periodo"] = df.apply(lambda r: f"{int(r['Año'])}-{int(r['mes_num']):02d}", axis=1)
        return df.groupby("Periodo")[col_monto].sum().reset_index().rename(columns={col_monto: "C"})

    cst_rrhh  = costos_por_periodo("2 RRHH",     "Importe")
    cst_admin = costos_por_periodo("3 GS ADMIN",  "Monto Bruto")
    cst_op    = costos_por_periodo("4 GS OP",     "Monto Bruto")
    cst_no_op = costos_por_periodo("5 GS NO OP",  "Monto Bruto")

    # Aplica regla: pct_fijo uniforme + pct_var según columna dada
    def aplicar_regla(costos_df, pct_fijo, pct_var, col_var):
        m = df_base.merge(costos_df, on="Periodo", how="left")
        m["C"] = m["C"].fillna(0)
        return (m["C"] * pct_fijo * m["Pct_Uniforme"] + m["C"] * pct_var * m[col_var]).values

    df_base["RRHH"]          = aplicar_regla(cst_rrhh,  0.40, 0.60, "Pct_Ventas")
    df_base["Administrativo"]= aplicar_regla(cst_admin, 1.00, 0.00, "Pct_Uniforme")
    df_base["Operativo"]     = aplicar_regla(cst_op,    0.00, 1.00, "Pct_Sesiones")
    df_base["No_Operativo"]  = aplicar_regla(cst_no_op, 0.30, 0.70, "Pct_Ventas")
    df_base["Costos_Totales"]= df_base[["RRHH","Administrativo","Operativo","No_Operativo"]].sum(axis=1)
    df_base["Margen_Bruto"]  = df_base["Ingresos"] - df_base["Costos_Totales"]
    df_base["Margen_Pct"]    = (
        df_base["Margen_Bruto"] / df_base["Ingresos"].where(df_base["Ingresos"] > 0, 1) * 100
    )

    # Resumen por sucursal (totales históricos)
    suc = (
        df_base.groupby("Sucursal")
        .agg(
            Ingresos       =("Ingresos",        "sum"),
            RRHH           =("RRHH",            "sum"),
            Administrativo =("Administrativo",  "sum"),
            Operativo      =("Operativo",       "sum"),
            No_Operativo   =("No_Operativo",    "sum"),
            Costos_Totales =("Costos_Totales",  "sum"),
            Margen_Bruto   =("Margen_Bruto",    "sum"),
        )
        .reset_index()
    )
    suc["Margen_Pct"] = (
        suc["Margen_Bruto"] / suc["Ingresos"].where(suc["Ingresos"] > 0, 1) * 100
    )
    suc = suc.sort_values("Ingresos", ascending=False)

    tot_ing_g = float(df_base["Ingresos"].sum())
    tot_cos_g = float(df_base["Costos_Totales"].sum())
    tot_mar_g = float(df_base["Margen_Bruto"].sum())

    return {
        "por_sucursal": [
            {
                "suc":        r["Sucursal"].replace("NCA ", ""),
                "ingresos":   _jnum(r["Ingresos"]),
                "rrhh":       _jnum(r["RRHH"]),
                "admin":      _jnum(r["Administrativo"]),
                "op":         _jnum(r["Operativo"]),
                "no_op":      _jnum(r["No_Operativo"]),
                "costos":     _jnum(r["Costos_Totales"]),
                "margen":     _jnum(r["Margen_Bruto"]),
                "margen_pct": _jnum(r["Margen_Pct"], 1),
            }
            for _, r in suc.iterrows()
        ],
        "total_costos":      _jnum(tot_cos_g),
        "total_margen":      _jnum(tot_mar_g),
        "margen_pct_global": _jnum(tot_mar_g / tot_ing_g * 100 if tot_ing_g > 0 else 0, 1),
    }


# ─── GENERADOR HTML ───────────────────────────────────────────────────────────

def _jnum(v, decimals=0):
    """Formatea número para JSON (redondea)."""
    try:
        return round(float(v), decimals)
    except Exception:
        return 0


def generar_html(data: dict, output_path: Path):
    eerr    = data["eerr"]
    flujo   = data["flujo"]
    ventas  = data["ventas"]
    rrhh    = data["rrhh"]
    adm_op  = data["adm_op"]
    no_op   = data["no_op"]
    mkt     = data["mkt"]
    seg     = data.get("seg", {})

    # ── KPIs globales para conclusiones (históricos, no proyecciones)
    tot25 = ventas["total_2025"]
    tot24 = ventas["total_2024"]
    var_venta = _pct(tot25 - tot24, tot24)
    rrhh_ratio = _pct(rrhh["total_2025"], tot25)
    flujo_min = min(flujo["flujo_acum"]) if flujo["flujo_acum"] else 0
    flujo_final = flujo["flujo_acum"][-1] if flujo["flujo_acum"] else 0
    ticket_avg_25 = [t for t in ventas["ticket_2025"] if t > 0]
    ticket_avg_24 = [t for t in ventas["ticket_2024"] if t > 0]
    ticket_var = _pct(
        (sum(ticket_avg_25) / len(ticket_avg_25)) - (sum(ticket_avg_24) / len(ticket_avg_24)),
        (sum(ticket_avg_24) / len(ticket_avg_24))
    ) if ticket_avg_24 and ticket_avg_25 else 0

    eerr_tot = next((s for s in eerr["sucursales"] if s["nombre"] == "TOTAL"), {})
    margen_op_pct = _pct(eerr_tot.get("resultado", 0), eerr_tot.get("ingresos", 1))

    # Participación sucursales en ventas 2025
    suc_totals = [(k, v.get(2025, 0)) for k, v in ventas["suc_data"].items()]
    suc_totals.sort(key=lambda x: x[1], reverse=True)
    total_suc = sum(v for _, v in suc_totals) or 1

    # RRHH ratio por sucursal
    rrhh_suc_map = {r["Sucursal"]: r["rrhh"] for r in rrhh["rrhh_suc"]}
    v25_suc = {
        k: sum(sv.get(anio, 0) for anio in [2025] for sv in [v])
        for k, v in ventas["suc_data"].items()
    }

    # Prepara JSON de datos para los charts
    DATA = {
        "eerr": {
            "anio": eerr["anio"],
            "mes":  eerr["mes"],
            "sucursales": [
                {
                    "nombre": s["nombre"],
                    "ingresos": _jnum(s["ingresos"]),
                    "ingresos_ppto": _jnum(s["ingresos_ppto"]),
                    "cumpl": _jnum(s["ingresos_cumpl"] * 100, 1),
                    "gs_personal": _jnum(s["gs_personal"]),
                    "gs_admin": _jnum(s["gs_admin"]),
                    "gs_op": _jnum(s["gs_op"]),
                    "gs_nop": _jnum(s["gs_no_op"]),
                    "resultado": _jnum(s["resultado"]),
                    "margen_pct": _jnum(_pct(s["resultado"], s["ingresos"]) if s["ingresos"] else 0, 1),
                }
                for s in eerr["sucursales"]
            ],
        },
        "flujo": {
            "labels":        MES_LABELS,
            "ingresos":      [_jnum(v) for v in flujo["ingresos"]],
            "gs_rrhh":       [_jnum(v) for v in flujo["gs_rrhh"]],
            "gs_adm_op":     [_jnum(v) for v in flujo["gs_adm_op"]],
            "gs_nop":        [_jnum(v) for v in flujo["gs_nop"]],
            "flujo_caja":    [_jnum(v) for v in flujo["flujo_caja"]],
            "flujo_acum":    [_jnum(v) for v in flujo["flujo_acum"]],
            "utilidad_neta": [_jnum(v) for v in flujo["utilidad_neta"]],
            "saldo_inicial": _jnum(flujo["saldo_inicial"]),
            "ppm_pct":       [_jnum(v) for v in flujo["ppm_pct"]],
            "ppm_val":       [_jnum(v) for v in flujo["ppm_val"]],
        },
        "ventas": {
            "labels":      MES_LABELS,
            "v2024":       [_jnum(v) for v in ventas["ventas_2024"]],
            "v2025":       [_jnum(v) for v in ventas["ventas_2025"]],
            "total_2024":  _jnum(ventas["total_2024"]),
            "total_2025":  _jnum(ventas["total_2025"]),
            "ticket_2024": [_jnum(v) for v in ventas["ticket_2024"]],
            "ticket_2025": [_jnum(v) for v in ventas["ticket_2025"]],
            "trans_2024":  ventas["trans_2024"],
            "trans_2025":  ventas["trans_2025"],
            "top_trat":    [
                {"nombre": r["Tratamiento"], "sesiones": int(r["sesiones"]),
                 "ingresos": _jnum(r["ingresos"]), "ticket": _jnum(r["ticket_prom"])}
                for r in ventas["top_trat"]
            ],
            "ticket_suc": [
                {"suc": r["Sucursal"], "ticket": _jnum(r["ticket"])}
                for r in ventas["ticket_suc"]
            ],
            "tipo_prod": [
                {"tipo": r["Tipo Producto"], "venta": _jnum(r["Venta"])}
                for r in ventas["tipo_prod"]
            ],
            "suc_totals": [{"suc": k, "v25": _jnum(v)} for k, v in suc_totals],
            "suc_data": {
                k: {
                    "2024": _jnum(ventas["suc_data"][k].get(2024, 0)),
                    "2025": _jnum(ventas["suc_data"][k].get(2025, 0)),
                }
                for k in ventas["suc_data"]
            },
            "total_txns": ventas["total_txns"],
        },
        "rrhh": {
            "labels":     MES_LABELS,
            "r2025":      [_jnum(v) for v in rrhh["rrhh_2025"]],
            "total_2025": _jnum(rrhh["total_2025"]),
            "tipo_gasto": [
                {"tipo": r["Tipo gasto"], "importe": _jnum(r["Importe"])}
                for r in rrhh["tipo_gasto"]
            ],
            "ratio_suc": rrhh.get("ratio_suc", []),
        },
        "adm_op": {
            "adm_tipo":  [{"tipo": r["Tipo de gasto"], "monto": _jnum(r["Monto Bruto"])} for r in adm_op["adm_tipo"]],
            "op_tipo":   [{"tipo": r["Tipo de gasto"], "monto": _jnum(r["Monto Bruto"])} for r in adm_op["op_tipo"]],
            "adm_total": _jnum(adm_op["adm_total"]),
            "op_total":  _jnum(adm_op["op_total"]),
        },
        "no_op": {
            "tipo":         [{"tipo": r["Tipo de gasto"], "monto": _jnum(r["Monto Bruto"])} for r in no_op["tipo"]],
            "proveedores":  [{"prov": r["Proveedor"], "monto": _jnum(r["Monto Bruto"]), "tipo": categorizar_concepto(r["Tipo de gasto"])} for r in no_op["proveedores"]],
            "total":        _jnum(no_op["total"]),
            "total_2025":   _jnum(no_op["total_2025"]),
            "digital_2025": _jnum(no_op["digital_2025"]),
        },
        "mkt": {
            "labels":      mkt["labels"],
            "mkt_2024":    [_jnum(v) for v in mkt["mkt_2024"]],
            "mkt_2025":    [_jnum(v) for v in mkt["mkt_2025"]],
            "total_2024":  _jnum(mkt["total_mkt_2024"]),
            "total_2025":  _jnum(mkt["total_mkt_2025"]),
            "roi_data":    mkt["roi_data"],
        },
        "seg": {
            "por_sucursal":      seg.get("por_sucursal", []),
            "total_costos":      seg.get("total_costos", 0),
            "total_margen":      seg.get("total_margen", 0),
            "margen_pct_global": seg.get("margen_pct_global", 0),
        },
        "kpis": {
            "var_ventas":  _jnum(var_venta, 1),
            "rrhh_ratio":  _jnum(rrhh_ratio, 1),
            "flujo_min":   _jnum(flujo_min),
            "flujo_final": _jnum(flujo_final),
            "ticket_var":  _jnum(ticket_var, 1),
            "margen_op":   _jnum(margen_op_pct, 1),
        },
    }

    data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NCA Clínicas — Análisis Financiero Integral</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,300;9..40,500;9..40,700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0b0e13;--s1:#141922;--s2:#1b2231;--bd:#273046;--tx:#e4e8f0;--tx2:#7f8ba3;--ac:#38bdf8;--gn:#22c55e;--rd:#ef4444;--am:#f59e0b;--pu:#a78bfa;--pk:#f472b6;--or:#fb923c;--tl:#2dd4bf}}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:var(--bg);color:var(--tx);font-family:'DM Sans',sans-serif;line-height:1.55}}
.ctn{{max-width:1440px;margin:0 auto;padding:20px 24px}}
h1{{font-size:26px;font-weight:700}}
h2{{font-size:19px;font-weight:700;color:var(--ac);border-left:3px solid var(--ac);padding-left:12px;margin-bottom:14px}}
h3{{font-size:13px;font-weight:600;color:var(--tx2);text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}}
.sub{{color:var(--tx2);font-size:13px;margin-bottom:28px}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:18px}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-bottom:18px}}
.g4{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}}
.c{{background:var(--s1);border:1px solid var(--bd);border-radius:10px;padding:18px}}
.kpi{{text-align:center;padding:14px 10px}}
.kpi .v{{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:600;color:var(--tx)}}
.kpi .v.up{{color:var(--gn)}}.kpi .v.dn{{color:var(--rd)}}.kpi .v.wn{{color:var(--am)}}
.kpi .l{{font-size:11px;color:var(--tx2);margin-top:3px}}
.kpi .d{{font-size:11px;margin-top:2px}}
.up{{color:var(--gn)}}.dn{{color:var(--rd)}}.wn{{color:var(--am)}}
.cw{{position:relative;height:300px}}.cw-s{{height:240px}}.cw-t{{height:360px}}
table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{text-align:left;padding:7px 8px;border-bottom:2px solid var(--bd);color:var(--tx2);font-weight:600;font-size:10px;text-transform:uppercase;letter-spacing:.4px}}
td{{padding:6px 8px;border-bottom:1px solid var(--bd);font-family:'JetBrains Mono',monospace;font-size:11px}}
tr:hover td{{background:var(--s2)}}
.sec{{margin-bottom:36px}}
.tg{{display:inline-block;padding:2px 7px;border-radius:4px;font-size:10px;font-weight:600}}
.tg-r{{background:rgba(239,68,68,.15);color:var(--rd)}}
.tg-g{{background:rgba(34,197,94,.15);color:var(--gn)}}
.tg-a{{background:rgba(245,158,11,.15);color:var(--am)}}
.tg-b{{background:rgba(56,189,248,.15);color:var(--ac)}}
.ib{{background:var(--s2);border-left:3px solid;padding:12px 14px;border-radius:0 8px 8px 0;margin-bottom:10px;font-size:12px}}
.ib.al{{border-color:var(--rd)}}.ib.ok{{border-color:var(--gn)}}.ib.act{{border-color:var(--ac)}}.ib.cau{{border-color:var(--am)}}
.ib b{{display:block;margin-bottom:3px}}
.dv{{height:1px;background:var(--bd);margin:36px 0}}
.nav{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:24px;position:sticky;top:0;background:var(--bg);padding:10px 0;z-index:10}}
.nav a{{padding:5px 12px;border-radius:5px;font-size:11px;font-weight:600;color:var(--tx2);text-decoration:none;background:var(--s1);border:1px solid var(--bd);transition:.2s}}
.nav a:hover{{color:var(--ac);border-color:var(--ac)}}
.mono{{font-family:'JetBrains Mono',monospace}}
/* Estilos para Conceptos en tabla de Proveedores */
.concepto{{display:inline-block;padding:4px 10px;border-radius:5px;font-size:10px;font-weight:600;text-transform:capitalize}}
.concepto-digital{{background:rgba(56,189,248,.2);color:#38bdf8}}
.concepto-financiero{{background:rgba(34,197,94,.2);color:#22c55e}}
.concepto-deuda{{background:rgba(239,68,68,.2);color:#ef4444}}
.concepto-marketing{{background:rgba(168,85,247,.2);color:#a78bfa}}
.concepto-soporte{{background:rgba(245,158,11,.2);color:#f59e0b}}
.concepto-servicios{{background:rgba(34,197,94,.15);color:#22c55e}}
.concepto-asesorias{{background:rgba(245,158,11,.15);color:#f59e0b}}
.concepto-leasing{{background:rgba(56,189,248,.15);color:#38bdf8}}
.concepto-otro{{background:rgba(127,139,180,.15);color:#7f8ba3}}
@media(max-width:900px){{.g2,.g3,.g4{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<a href="#main-content" class="skip-link">Saltar al contenido principal</a>
<div class="ctn" id="main-content">
<h1>NCA Clínicas — Análisis Financiero Integral</h1>
<p class="sub">EERR · Ventas · RRHH · Gastos · Marketing · KPIs — Datos reales ene 2024 a mar 2025</p>

<nav class="nav" aria-label="Módulos del dashboard">
<a href="#m1" aria-label="Módulo 1: Estado de Resultados">1·EERR</a><a href="#m2" aria-label="Módulo 2: Ventas Consolidadas">2·Ventas</a><a href="#m3" aria-label="Módulo 3: Detalle de Ventas">3·Detalle Ventas</a><a href="#m4" aria-label="Módulo 4: Gastos de Personal RRHH">4·RRHH</a><a href="#m5" aria-label="Módulo 5: Gastos Administrativos y Operativos">5·Gastos Adm/Op</a><a href="#m6" aria-label="Módulo 6: Gastos No Operacionales y Marketing">6·Gs No Op + Mkt</a><a href="#m7" aria-label="Módulo 7: Conclusiones y Plan de Acción">7·Conclusiones</a>
</nav>

<!-- === M1: EERR === -->
<section class="sec" id="m1">
<h2>Módulo 1 · Estado de Resultados — <span id="eerr-periodo"></span></h2>
<div class="g4" id="kpi-eerr"></div>
<div class="g2">
<div class="c"><h3>Cumplimiento Presupuesto por Sucursal</h3><div class="cw"><canvas id="c1"></canvas></div></div>
<div class="c"><h3>Resultado Operacional por Sucursal (M CLP)</h3><div class="cw"><canvas id="c2"></canvas></div></div>
</div>
<div class="c" style="margin-bottom:16px">
<h3>Detalle por Sucursal — <span id="eerr-periodo2"></span> (millones CLP)</h3>
<table>
<tr><th>Sucursal</th><th>Ingresos</th><th>Gs Personal</th><th>Gs Adm</th><th>Gs Op</th><th>Gs NoOp</th><th>Resultado</th><th>Margen</th><th>vs 2024</th></tr>
<tbody id="tbody-eerr"></tbody>
</table></div>
<div id="ib-eerr"></div>
</section>

<div class="dv"></div>


<!-- === M3: VENTAS === -->
<section class="sec" id="m2">
<h2>Módulo 2 · Ventas Consolidadas 2024–2025</h2>
<div class="g4" id="kpi-ventas"></div>
<div class="c" style="margin-bottom:16px"><h3>Evolución de Ventas Mensuales</h3><div class="cw cw-t"><canvas id="c6"></canvas></div></div>
<div class="g2">
<div class="c"><h3>Ventas Anuales por Sucursal</h3><div class="cw cw-t"><canvas id="c7"></canvas></div></div>
<div class="c"><h3>Participación Interna 2025</h3><div class="cw cw-t"><canvas id="c8"></canvas></div></div>
</div>
<div id="ib-ventas"></div>
</section>

<div class="dv"></div>

<!-- === M4: VENTAS DETALLE === -->
<section class="sec" id="m3">
<h2>Módulo 3 · Detalle de Ventas — <span id="tx-count"></span> Transacciones</h2>
<div class="g4" id="kpi-detalle"></div>
<div class="g2">
<div class="c"><h3>Top Tratamientos por Facturación</h3><div class="cw cw-t"><canvas id="c9"></canvas></div></div>
<div class="c"><h3>Ticket Promedio por Sucursal</h3><div class="cw"><canvas id="c10"></canvas></div></div>
</div>
<div class="g2">
<div class="c"><h3>Transacciones Mensuales (volumen)</h3><div class="cw"><canvas id="c11"></canvas></div></div>
<div class="c"><h3>Evolución Ticket Promedio Mensual</h3><div class="cw"><canvas id="c12"></canvas></div></div>
</div>
<div id="ib-detalle"></div>
</section>

<div class="dv"></div>

<!-- === M5: RRHH === -->
<section class="sec" id="m4">
<h2>Módulo 4 · Gastos de Personal (RRHH)</h2>
<div class="g4" id="kpi-rrhh"></div>
<div class="g2">
<div class="c"><h3>Evolución Mensual RRHH 2025</h3><div class="cw"><canvas id="c13"></canvas></div></div>
<div class="c"><h3>RRHH como % de Ventas por Sucursal (2025)</h3><div class="cw"><canvas id="c14"></canvas></div></div>
</div>
<div class="c" style="margin-bottom:16px"><h3>Composición del Gasto de Personal</h3><div class="cw cw-s"><canvas id="c15"></canvas></div></div>
<div class="c" style="margin-bottom:16px"><h3>Detalle Composición Personal (acumulado)</h3>
<table><tr><th>Tipo</th><th>Monto</th><th>% RRHH</th></tr><tbody id="tbody-rrhh"></tbody></table></div>
<div id="ib-rrhh"></div>
</section>

<div class="dv"></div>

<!-- === M6: GS ADM + OP === -->
<section class="sec" id="m5">
<h2>Módulo 5 · Gastos Administrativos y Operativos</h2>
<div class="g2">
<div class="c"><h3>Gastos Administrativos por Tipo</h3><div class="cw"><canvas id="c16"></canvas></div></div>
<div class="c"><h3>Gastos Operativos por Tipo</h3><div class="cw"><canvas id="c17"></canvas></div></div>
</div>
<div class="g2">
<div class="c">
<h3>Detalle Administrativo (M CLP, acumulado)</h3>
<table><tr><th>Tipo</th><th>Monto</th><th>%</th></tr><tbody id="tbody-adm"></tbody></table>
</div>
<div class="c">
<h3>Detalle Operativo (M CLP, acumulado)</h3>
<table><tr><th>Tipo</th><th>Monto</th><th>%</th></tr><tbody id="tbody-op"></tbody></table>
</div></div>
<div id="ib-adm"></div>
<!-- Segmentación por sucursal -->
<h2 style="margin-top:24px;font-size:16px;border-left-color:var(--am)">Costos Segmentados por Sucursal</h2>
<div class="g4" id="kpi-seg"></div>
<div class="g2">
<div class="c"><h3>Composición de Costos por Sucursal</h3><div class="cw"><canvas id="c_seg1"></canvas></div></div>
<div class="c"><h3>Margen Bruto % por Sucursal</h3><div class="cw"><canvas id="c_seg2"></canvas></div></div>
</div>
<div class="c" style="margin-bottom:16px">
<h3>Detalle de Costos y Márgenes por Sucursal</h3>
<table><tr><th>Sucursal</th><th>Ingresos</th><th>RRHH</th><th>Admin</th><th>Op</th><th>No Op</th><th>Costos</th><th>Margen</th><th>Margen %</th></tr>
<tbody id="tbody-seg"></tbody></table>
</div>
</section>

<div class="dv"></div>

<!-- === M7: GS NO OP + MKT === -->
<section class="sec" id="m6">
<h2>Módulo 6 · Gastos No Operacionales + Marketing</h2>
<div class="g4" id="kpi-nop"></div>
<div class="g2">
<div class="c"><h3>Distribución Gs No Operacionales (total acumulado)</h3><div class="cw cw-t"><canvas id="c18"></canvas></div></div>
<div class="c"><h3>Top 8 Proveedores No Operacionales</h3>
<table><tr><th>Proveedor</th><th>Total M</th><th>%</th><th>Concepto</th></tr><tbody id="tbody-prov"></tbody></table>
<h3 style="margin-top:14px">Marketing: Inversión vs ROI</h3>
<table><tr><th>Año</th><th>Inversión Mkt+Dig</th><th>Ventas</th><th>ROI aprox</th></tr><tbody id="tbody-mkt-roi"></tbody></table>
</div></div>
<div id="ib-nop"></div>
</section>

<div class="dv"></div>

<!-- === M8: CONCLUSIONES === -->
<section class="sec" id="m7">
<h2>Módulo 7 · Conclusiones y Plan de Acción</h2>
<div class="g3">
<div class="c" style="border-left:3px solid var(--rd)" id="col-alertas"></div>
<div class="c" style="border-left:3px solid var(--gn)" id="col-ok"></div>
<div class="c" style="border-left:3px solid var(--ac)" id="col-plan"></div>
</div>
<div class="c">
<h3>Resumen Ejecutivo — Indicadores Clave</h3>
<table><tr><th>Indicador</th><th>Valor</th><th>Tendencia</th><th>Status</th></tr>
<tbody id="tbody-resumen"></tbody></table>
</div>
</section>

</div><!-- /ctn -->

<script>
const D = {data_json};

// ── FORMAT HELPERS ────────────────────────────────────────────────────────
const CLP = v => '$'+Math.round(v).toLocaleString('es-CL');
const MM  = v => '$'+Math.round(v/1e6).toLocaleString('es-CL')+'M';
const PCT = v => (v>=0?'+':'')+v.toFixed(1)+'%';
const NUM = v => Math.round(v).toLocaleString('es-CL');
const CL = {{b:'#38bdf8',g:'#22c55e',r:'#ef4444',a:'#f59e0b',p:'#a78bfa',pk:'#f472b6',o:'#fb923c',t:'#2dd4bf'}};
// Paleta extendida para barras multicolor
const PALETTE = ['#38bdf8','#22c55e','#ef4444','#f59e0b','#a78bfa','#f472b6','#fb923c','#2dd4bf','#ec4899','#8b5cf6','#06b6d4','#10b981','#f97316','#6366f1','#d946ef','#14b8a6'];

Chart.defaults.color='#7f8ba3';
Chart.defaults.borderColor='#273046';
Chart.defaults.font.family="'DM Sans',sans-serif";
Chart.defaults.font.size=11;

function mkChart(id, type, labels, datasets, opts={{}}){{
  const ctx=document.getElementById(id);
  if(!ctx) return;
  ctx.setAttribute('role','img');
  if(!ctx.getAttribute('aria-label')){{
    const firstDs=datasets&&datasets[0]?datasets[0].label||'':'';
    ctx.setAttribute('aria-label','Gráfico financiero NCA'+(firstDs?' — '+firstDs:''));
  }}
  return new Chart(ctx,{{type,data:{{labels,datasets}},options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10,padding:10}}}},tooltip:{{callbacks:{{label:c=>CLP(c.raw)}}}}}},
    ...opts
  }}}});
}}

function kpiCard(label,val,sub,deltaClass=''){{
  const cls={{'dg':'up','dr':'dn','da':'wn'}}[deltaClass]||deltaClass;
  return `<div class="c kpi"><div class="v ${{cls}}">${{val}}</div><div class="l">${{label}}</div>${{sub?`<div class="d ${{cls}}">${{sub}}</div>`:''}}</div>`;
}}

// ── M1 EERR ───────────────────────────────────────────────────────────────
function buildEERR(){{
  const sucs = D.eerr.sucursales.filter(s=>s.nombre!=='TOTAL');
  const tot  = D.eerr.sucursales.find(s=>s.nombre==='TOTAL')||{{}};
  const periodo = D.eerr.mes+' '+D.eerr.anio;
  document.getElementById('eerr-periodo').textContent = periodo;
  document.getElementById('eerr-periodo2').textContent = periodo;

  // KPI cards
  const totCumpl = tot.cumpl||0;
  const totRes   = tot.resultado||0;
  const totIng   = tot.ingresos||1;
  const totMg    = _jn(totRes/totIng*100);
  document.getElementById('kpi-eerr').innerHTML =
    kpiCard('Ingresos 2025 Anual', MM(tot.ingresos||0), 'Año completo 12 meses', '') +
    kpiCard('vs 2024', (totCumpl).toFixed(1)+'%', totCumpl>=100?'Creció vs 2024':'Cayó vs 2024', totCumpl>=100?'dg':'dr') +
    kpiCard('Resultado Operacional', MM(totRes), 'Margen '+totMg.toFixed(1)+'%', totRes>=0?'dg':'dr') +
    kpiCard('Gastos Totales 2025', MM((tot.gs_personal||0)+(tot.gs_admin||0)+(tot.gs_op||0)+(tot.gs_nop||0)), '', 'wn');

  // C1 cumplimiento (excluye Casa Matriz)
  const sucsC1 = sucs.filter(s=>s.nombre!=='Casa Matriz');
  const cumpl = sucsC1.map(s=>s.cumpl);
  mkChart('c1','bar',sucsC1.map(s=>s.nombre.replace('NCA ','')),
    [{{label:'Ventas 2025 vs 2024 %',data:cumpl,backgroundColor:cumpl.map(v=>v>=100?CL.g:v>=80?CL.a:CL.r),borderRadius:4}}],
    {{scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>v+'%'}}}}}},plugins:{{legend:{{display:false}},
    tooltip:{{callbacks:{{label:c=>c.raw.toFixed(1)+'% vs 2024'}}}}}}}});

  // C2 resultado
  const res = sucs.map(s=>s.resultado/1e6);
  mkChart('c2','bar',sucs.map(s=>s.nombre.replace('NCA ','')),
    [{{label:'Resultado Op. $M',data:res,backgroundColor:res.map(v=>v>=0?CL.g:CL.r),borderRadius:4}}],
    {{scales:{{y:{{ticks:{{callback:v=>MM(v*1e6)}}}}}},plugins:{{legend:{{display:false}}}}}});

  // Tabla (9 columnas)
  const tbody=document.getElementById('tbody-eerr');
  [...sucs,tot].forEach(s=>{{
    if(!s) return;
    const mg=s.margen_pct||0;
    const cl=mg>60?'tg-g':mg>40?'tg-b':mg>20?'tg-a':'tg-r';
    const cu=s.cumpl||0;
    const cc=cu>=100?'tg-g':cu>=80?'tg-a':'tg-r';
    const bold=s.nombre==='TOTAL'?'font-weight:700':'';
    const resCls=s.resultado<0?'style="color:var(--rd)"':'style="color:var(--gn)"';
    tbody.innerHTML+=`<tr style="${{bold}}">
      <td>${{s.nombre}}</td>
      <td class="r">${{(s.ingresos/1e6).toFixed(1)}}</td>
      <td class="r">${{(s.gs_personal/1e6).toFixed(1)}}</td>
      <td class="r">${{((s.gs_admin||0)/1e6).toFixed(1)}}</td>
      <td class="r">${{((s.gs_op||0)/1e6).toFixed(1)}}</td>
      <td class="r">${{((s.gs_nop||0)/1e6).toFixed(1)}}</td>
      <td class="r" ${{resCls}}>${{(s.resultado/1e6).toFixed(1)}}</td>
      <td class="r">${{s.ingresos?`<span class="tg ${{cl}}">${{mg.toFixed(1)}}%</span>`:'—'}}</td>
      <td class="r">${{s.ingresos?`<span class="tg ${{cc}}">${{cu.toFixed(1)}}%</span>`:'—'}}</td>
    </tr>`;
  }});

  // Info boxes
  const ibEl = document.getElementById('ib-eerr');
  const top = sucs.filter(s=>s.ingresos>0).sort((a,b)=>b.cumpl-a.cumpl);
  if(top.length){{
    const best=top[0];
    const lowSucs=top.filter(s=>s.cumpl<80).reverse();
    const surplus=tot.ingresos-(tot.ingresos_ppto||tot.ingresos);
    if(totCumpl>=100){{
      const bestPct=(best.ingresos_ppto&&best.ingresos_ppto>0)?(best.ingresos/best.ingresos_ppto*100).toFixed(0):null;
      ibEl.innerHTML+=`<div class="ib ok"><b>🟢 Ingresos 2025 superan 2024 (${{surplus>0?'+':''}}${{MM(Math.abs(surplus))}}, ${{totCumpl.toFixed(1)}}%)</b>A nivel consolidado, el año 2025 creció vs 2024. ${{best.nombre.replace('NCA ','')}} lideró con ${{MM(best.ingresos)}} vs ${{MM(best.ingresos_ppto||best.ingresos)}} en 2024${{bestPct?' ('+bestPct+'%)':''}}.</div>`;
    }}
    if(lowSucs.length>=2)
      ibEl.innerHTML+=`<div class="ib al"><b>🔴 ${{lowSucs[0].nombre.replace('NCA ','')}} (${{lowSucs[0].cumpl.toFixed(1)}}%) y ${{lowSucs[1].nombre.replace('NCA ','')}} (${{lowSucs[1].cumpl.toFixed(1)}}%) cayeron vs 2024</b>${{lowSucs[0].nombre.replace('NCA ','')}} generó ${{MM(lowSucs[0].ingresos)}} vs ${{MM(lowSucs[0].ingresos_ppto||0)}} en 2024. ${{lowSucs[1].nombre.replace('NCA ','')}} ${{MM(lowSucs[1].ingresos)}} vs ${{MM(lowSucs[1].ingresos_ppto||0)}}. Estas sucursales requieren plan de acción comercial.</div>`;
    else if(lowSucs.length===1)
      ibEl.innerHTML+=`<div class="ib al"><b>🔴 ${{lowSucs[0].nombre.replace('NCA ','')}} (${{lowSucs[0].cumpl.toFixed(1)}}%) cayó vs 2024</b>Generó ${{MM(lowSucs[0].ingresos)}} vs ${{MM(lowSucs[0].ingresos_ppto||0)}} en 2024. Requiere plan de acción comercial.</div>`;
    const cm = sucs.find(s=>s.nombre==='Casa Matriz');
    const totalGs = sucs.reduce((s,r)=>s+((r.gs_personal||0)+(r.gs_admin||0)+(r.gs_op||0)+(r.gs_nop||0)),0)||1;
    if(cm && Math.abs(cm.resultado)>1e8){{
      const pctGs=(Math.abs(cm.resultado)/totalGs*100).toFixed(1);
      const nopAll=D.no_op.tipo.reduce((s,t)=>s+t.monto,0)||1;
      const nopDig=D.no_op.tipo.find(t=>(t.tipo||'').toLowerCase().includes('digital'))||{{monto:0}};
      const nopAsesor=D.no_op.tipo.find(t=>(t.tipo||'').toLowerCase().includes('asesor'))||{{monto:0}};
      const cmDigital=(cm.gs_nop||0)*(nopDig.monto/nopAll);
      const cmAsesor=(cm.gs_nop||0)*(nopAsesor.monto/nopAll);
      const digitalStr=cmDigital>1e6?', '+MM(cmDigital)+' en marketing digital':'';
      const asesorStr=cmAsesor>1e6?' y '+MM(cmAsesor)+' en asesorías':'';
      ibEl.innerHTML+=`<div class="ib cau"><b>🟡 Casa Matriz absorbe ${{MM(Math.abs(cm.resultado))}} sin generar ingresos directos</b>El ${{pctGs}}% de los gastos totales se concentran en Casa Matriz, incluyendo ${{MM(cm.gs_personal||0)}} en personal corporativo${{digitalStr}}${{asesorStr}}.</div>`;
    }}
  }}
}}
function _jn(v){{ return isNaN(v)||!isFinite(v)?0:v; }}

// ── M2 FLUJO ──────────────────────────────────────────────────────────────
function buildFlujo(){{
  const fl = D.flujo;
  const minAcum = Math.min(...fl.flujo_acum);
  const mesMin  = fl.labels[fl.flujo_acum.indexOf(minAcum)];
  const mesesNeg= fl.flujo_caja.filter(v=>v<0).length;

  document.getElementById('kpi-flujo').innerHTML =
    kpiCard('Saldo Inicial', MM(fl.saldo_inicial),'') +
    kpiCard('Flujo Acumulado Dic', MM(minAcum), mesMin, minAcum<0?'dr':'dg') +
    kpiCard('Piso ('+mesMin+')', MM(fl.flujo_acum[11]||0), '', (fl.flujo_acum[11]||0)<0?'dr':'dg') +
    kpiCard('Meses Flujo Negativo', mesesNeg+' de 12', '', mesesNeg>6?'dr':mesesNeg>3?'da':'dg');

  // C3 flujo caja + acumulado
  const fc = fl.flujo_caja;
  new Chart(document.getElementById('c3'),{{
    data:{{labels:fl.labels,datasets:[
      {{type:'bar',label:'Flujo Mes ($)',data:fc,backgroundColor:fc.map(v=>v>=0?'rgba(34,197,94,.7)':'rgba(239,68,68,.7)'),yAxisID:'y',order:2,borderRadius:3}},
      {{type:'line',label:'Acumulado ($)',data:fl.flujo_acum,borderColor:CL.a,borderWidth:2,pointRadius:3,fill:false,yAxisID:'y2',order:1}}
    ]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{position:'bottom',labels:{{boxWidth:10}}}},tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+MM(c.raw)}}}}}},
      scales:{{y:{{position:'left',ticks:{{callback:v=>MM(v)}}}},y2:{{position:'right',grid:{{drawOnChartArea:false}},ticks:{{callback:v=>MM(v)}}}}}}}}
  }});

  // C4 composicion egresos (RRHH + AdmOp total mensual stacked)
  mkChart('c4','bar',fl.labels,[
    {{label:'RRHH',    data:fl.gs_rrhh,   backgroundColor:'#ef4444',stack:'a'}},
    {{label:'Adm+Op',  data:fl.gs_adm_op, backgroundColor:'#f59e0b',stack:'a'}},
    {{label:'No Op',   data:fl.gs_nop,    backgroundColor:'#a78bfa',stack:'a'}}
  ],{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom'}}}},scales:{{x:{{stacked:true}},y:{{stacked:true,ticks:{{callback:v=>'$'+v+'M'}}}}}}}});

  // C5 utilidad neta
  const un = fl.utilidad_neta;
  mkChart('c5','bar',fl.labels,[
    {{label:'Utilidad Neta',data:un,backgroundColor:un.map(v=>v>=0?'rgba(34,197,94,.7)':'rgba(239,68,68,.7)'),borderRadius:4}}
  ],{{scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}},plugins:{{legend:{{display:false}}}}}});

  // Info boxes
  const ibFl = document.getElementById('ib-flujo');
  const primerNegIdx=fl.flujo_acum.findIndex(v=>v<0);
  const primerNegMes=primerNegIdx>=0?fl.labels[primerNegIdx]:null;
  if(primerNegMes)
    ibFl.innerHTML+=`<div class="ib al"><b>🔴 CRÍTICO: Caja real negativa desde ~${{primerNegMes}} (${{MM(fl.saldo_inicial)}} inicial - ${{MM(Math.abs(minAcum))}} mínimo acumulado = ${{MM(fl.saldo_inicial+minAcum)}} en ${{mesMin}})</b>Con saldo inicial de ${{MM(fl.saldo_inicial)}}, la empresa se queda sin efectivo entre ${{primerNegMes}} y ${{mesMin}}. El piso de ${{MM(minAcum)}} en ${{mesMin}} requiere inyección de capital.</div>`;
  // RRHH 2026 excluido — datos reales solo hasta marzo 2026
  const ppmPct = fl.ppm_pct||[], ppmVal = fl.ppm_val||[];
  const ppmIni = ppmPct[0]||0, ppmMax = Math.max(...ppmPct.filter(v=>v>0))||0;
  const ppmJumpIdx = ppmPct.findIndex(v=>v>ppmIni+0.005);
  const ppmJumpMes = ppmJumpIdx>=0 ? fl.labels[ppmJumpIdx] : null;
  const ppmAvgHigh = ppmJumpIdx>=0 ? ppmVal.slice(ppmJumpIdx).filter(v=>v>0).reduce((a,b)=>a+b,0)/(ppmVal.slice(ppmJumpIdx).filter(v=>v>0).length||1) : 0;
  const ppmAvgLow  = ppmVal.slice(0, ppmJumpIdx>=0?ppmJumpIdx:3).filter(v=>v>0).reduce((a,b)=>a+b,0)/(ppmVal.slice(0, ppmJumpIdx>=0?ppmJumpIdx:3).filter(v=>v>0).length||1);
  const ppmDelta = ppmAvgHigh - ppmAvgLow;
  if(ppmJumpMes)
    ibFl.innerHTML+=`<div class="ib act"><b>🔵 PPM sube de ${{(ppmIni*100).toFixed(0)}}% a ${{(ppmMax*100).toFixed(0)}}% desde ${{ppmJumpMes}} (+${{MM(ppmDelta)}}/mes de presión)</b>Evaluar si hay crédito fiscal acumulado para solicitar rebaja ante el SII. Los ${{MM(ppmDelta)}} adicionales mensuales son el segundo factor de destrucción de caja.</div>`;
  else
    ibFl.innerHTML+=`<div class="ib act"><b>🔵 PPM: evaluar crédito fiscal acumulado (piso ${{MM(minAcum)}})</b>Evaluar si hay crédito fiscal acumulado para solicitar rebaja ante el SII. Postergar pagos no urgentes y asegurar línea de crédito puente.</div>`;
}}

// ── M3 VENTAS ─────────────────────────────────────────────────────────────
function buildVentas(){{
  const v = D.ventas;
  const pct25 = ((v.total_2025-v.total_2024)/v.total_2024*100).toFixed(1);
  const tickAvg25 = v.ticket_2025.filter(t=>t>0).reduce((a,b)=>a+b,0)/(v.ticket_2025.filter(t=>t>0).length||1);
  const tickAvg24 = v.ticket_2024.filter(t=>t>0).reduce((a,b)=>a+b,0)/(v.ticket_2024.filter(t=>t>0).length||1);
  const tickVar   = ((tickAvg25-tickAvg24)/tickAvg24*100).toFixed(1);

  document.getElementById('kpi-ventas').innerHTML =
    kpiCard('Venta 2024', MM(v.total_2024),'') +
    kpiCard('Venta 2025', MM(v.total_2025), PCT(parseFloat(pct25)), parseFloat(pct25)>=0?'dg':'dr') +
    kpiCard('Promedio Mensual 2025', MM(v.total_2025/12), '', '') +
    kpiCard('Var. Ticket 2024→2025', PCT(parseFloat(tickVar)), '', parseFloat(tickVar)>=0?'dg':'dr');

  // C6 lineas 3 años
  mkChart('c6','line',v.labels,[
    {{label:'2024',data:v.v2024,borderColor:CL.p,borderWidth:2,pointRadius:2,fill:false,tension:.3}},
    {{label:'2025',data:v.v2025,borderColor:CL.a,borderWidth:2,pointRadius:2,fill:false,tension:.3}},
  ],{{scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}}}});

  // C7 barras por sucursal — suc_data keys son strings en JSON
  const sucs = v.suc_totals.map(s=>s.suc.replace('NCA ',''));
  mkChart('c7','bar',sucs,[
    {{label:'2024',data:v.suc_totals.map(s=>v.suc_data?.[s.suc]?.['2024']||0),backgroundColor:'rgba(167,139,250,.6)',borderRadius:3}},
    {{label:'2025',data:v.suc_totals.map(s=>v.suc_data?.[s.suc]?.['2025']||0),backgroundColor:'rgba(245,158,11,.6)',borderRadius:3}},
  ],{{scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}}}});

  // C8 donut participacion 2025
  new Chart(document.getElementById('c8'),{{type:'doughnut',data:{{
    labels:v.suc_totals.map(s=>s.suc.replace('NCA ','')),
    datasets:[{{data:v.suc_totals.map(s=>v.suc_data?.[s.suc]?.['2025']||0),backgroundColor:v.suc_totals.map((_,i)=>PALETTE[i%PALETTE.length]),borderWidth:0}}]
  }},options:{{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'right',labels:{{boxWidth:10}}}},tooltip:{{callbacks:{{label:c=>c.label+': '+MM(c.raw)}}}}  }}}}}});

  // C11 transacciones
  mkChart('c11','line',v.labels,[
    {{label:'2024',data:v.trans_2024,borderColor:CL.p,borderWidth:2,pointRadius:2,fill:false,tension:.3}},
    {{label:'2025',data:v.trans_2025,borderColor:CL.a,borderWidth:2,pointRadius:2,fill:false,tension:.3}}
  ],{{plugins:{{tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+NUM(c.raw)}}}}  }},scales:{{y:{{ticks:{{callback:v=>NUM(v)}}}}}}}});

  // C12 ticket
  mkChart('c12','line',v.labels,[
    {{label:'Ticket 2024',data:v.ticket_2024,borderColor:CL.p,borderWidth:2,pointRadius:2,fill:false,tension:.3}},
    {{label:'Ticket 2025',data:v.ticket_2025,borderColor:CL.a,borderWidth:2,pointRadius:2,fill:false,tension:.3}}
  ],{{scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}}}});

  // Info boxes
  const ibV = document.getElementById('ib-ventas');
  if(ibV){{
    if(parseFloat(pct25)>0) ibV.innerHTML+=`<div class="ib ok"><b>🟢 Ventas 2025 crecieron +${{pct25}}% vs 2024</b>Estacionalidad consistente: Q4 (oct-nov) generan los mejores meses del año.</div>`;
    else ibV.innerHTML+=`<div class="ib al"><b>🔴 Caída en ventas 2025 (${{pct25}}% vs 2024)</b>Revisar mix de productos y canales de captación.</div>`;
    // Face & Body contraction
    const fbKey=Object.keys(v.suc_data).find(k=>k.toLowerCase().includes('face'));
    if(fbKey){{
      const fb24=v.suc_data[fbKey]['2024']||0, fb25=v.suc_data[fbKey]['2025']||0;
      if(fb24>0&&fb25<fb24*0.85)
        ibV.innerHTML+=`<div class="ib cau"><b>🟡 ${{fbKey.replace('NCA ','')}}: contracción del ${{((fb24-fb25)/fb24*100).toFixed(0)}}% desde 2024</b>Pasó de ${{MM(fb24)}} (2024) a ${{MM(fb25)}} (2025). Revisar mix de tratamientos y estrategia comercial.</div>`;
    }}
    if(parseFloat(tickVar)<-10) ibV.innerHTML+=`<div class="ib al"><b>🔴 Ticket promedio cayó de ${{CLP(v.ticket_2024[0])}} (ene-24) a ${{CLP(v.ticket_2025[11])}} (dic-25): ${{tickVar}}%</b>La caída sostenida del ticket sugiere más descuentos, promociones agresivas o migración hacia tratamientos de menor valor.</div>`;
  }}
}}

// ── M4 DETALLE VENTAS ─────────────────────────────────────────────────────
function buildDetalle(){{
  const v = D.ventas;

  // C9 top tratamientos
  const tr = v.top_trat.slice(0,10);
  mkChart('c9','bar',tr.map(t=>t.nombre.length>25?t.nombre.substring(0,23)+'…':t.nombre),
    [{{label:'Ingresos',data:tr.map(t=>t.ingresos),backgroundColor:tr.map((_,i)=>PALETTE[i%PALETTE.length]),borderRadius:4,indexAxis:'y'}}],
    {{indexAxis:'y',plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>MM(c.raw)}}}}}},scales:{{x:{{ticks:{{callback:v=>MM(v)}}}},y:{{ticks:{{font:{{size:10}}}}}}}}}});

  // C10 ticket por sucursal
  const ts = v.ticket_suc.sort((a,b)=>b.ticket-a.ticket);
  mkChart('c10','bar',ts.map(t=>t.suc.replace('NCA ','')),
    [{{label:'Ticket Prom.',data:ts.map(t=>t.ticket),backgroundColor:ts.map((_,i)=>PALETTE[i%PALETTE.length]),borderRadius:4}}],
    {{plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>CLP(c.raw)}}}}}},scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}}}});

  // KPI cards M4
  const txKpi = document.getElementById('kpi-detalle');
  if(txKpi){{
    const tickAll = [...v.ticket_2024,...v.ticket_2025].filter(t=>t>0);
    const tickGlobal = tickAll.length? tickAll.reduce((a,b)=>a+b,0)/tickAll.length : 0;
    const svcPct = v.tipo_prod?.length? v.tipo_prod.filter(t=>(t.tipo||'').toLowerCase().includes('serv')).reduce((a,p)=>a+p.venta,0)/(v.tipo_prod.reduce((a,p)=>a+p.venta,0)||1)*100 : 97.8;
    txKpi.innerHTML =
      kpiCard('Transacciones Totales', (v.total_txns/1000).toFixed(1)+'K', '', '') +
      kpiCard('Ticket Promedio Global', CLP(tickGlobal), '', '') +
      kpiCard('Servicios (del total)', svcPct.toFixed(1)+'%', '', '') +
      kpiCard('Tratamientos Distintos', v.top_trat.length, '', '');
  }}

  // Info boxes
  const ibD = document.getElementById('ib-detalle');
  if(ibD && tr.length){{
    const top1 = tr[0];
    const top5ing = tr.slice(0,5).reduce((a,t)=>a+t.ingresos,0);
    const totalIng = v.top_trat.reduce((a,t)=>a+t.ingresos,0)||1;
    ibD.innerHTML+=`<div class="ib ok"><b>🟢 ${{top1.nombre}} lidera con ${{MM(top1.ingresos)}} (${{(top1.ingresos/totalIng*100).toFixed(1)}}% del total)</b>Los 5 tratamientos top concentran el ${{(top5ing/totalIng*100).toFixed(0)}}% de la facturación.</div>`;
    const tickAvg25b = v.ticket_2025.filter(t=>t>0).reduce((a,b)=>a+b,0)/(v.ticket_2025.filter(t=>t>0).length||1);
    const tickAvg24b = v.ticket_2024.filter(t=>t>0).reduce((a,b)=>a+b,0)/(v.ticket_2024.filter(t=>t>0).length||1);
    const tvar = ((tickAvg25b-tickAvg24b)/tickAvg24b*100);
    if(tvar<-15) ibD.innerHTML+=`<div class="ib al"><b>🔴 Ticket promedio cayó de ${{CLP(v.ticket_2024[0])}} (ene-24) a ${{CLP(v.ticket_2025[11])}} (dic-25): ${{tvar.toFixed(0)}}%</b>La caída sostenida del ticket sugiere más descuentos, promociones agresivas o migración hacia tratamientos de menor valor.</div>`;
    if(ts.length>=2) ibD.innerHTML+=`<div class="ib act"><b>🔵 ${{ts[0].suc.replace('NCA ','')}} (${{CLP(ts[0].ticket)}}) y ${{ts[1].suc.replace('NCA ','')}} (${{CLP(ts[1].ticket)}}) tienen los tickets más altos</b>Pese a su problema de costos, estas sucursales capturan los tratamientos de mayor valor. Optimizar su mix comercial.</div>`;
    else if(ts.length) ibD.innerHTML+=`<div class="ib act"><b>🔵 ${{ts[0].suc.replace('NCA ','')}} tiene el ticket más alto (${{CLP(ts[0].ticket)}})</b>Captura tratamientos de mayor valor. Optimizar su mix comercial.</div>`;
  }}
}}
// ── M5 RRHH ───────────────────────────────────────────────────────────────
function buildRRHH(){{
  const r = D.rrhh;
  const ratio   = (r.total_2025/D.ventas.total_2025*100).toFixed(1);
  const mensual_2025 = r.r2025.filter(v=>v>0).length ? r.r2025.reduce((s,v)=>s+v,0)/r.r2025.filter(v=>v>0).length : 0;

  document.getElementById('kpi-rrhh').innerHTML =
    kpiCard('RRHH 2025', MM(r.total_2025),'') +
    kpiCard('RRHH/Ventas 2025', ratio+'%', '', parseFloat(ratio)>50?'dr':parseFloat(ratio)>35?'da':'dg') +
    kpiCard('Costo Mensual 2025', MM(mensual_2025),'') +
    kpiCard('Meses con Datos', r.r2025.filter(v=>v>0).length+' de 12', '', '');

  // C13 lineas
  mkChart('c13','line',r.labels,[
    {{label:'2025',data:r.r2025,borderColor:CL.p,borderWidth:2,pointRadius:2,fill:false,tension:.3}}
  ],{{scales:{{y:{{ticks:{{callback:v=>MM(v)}}}}}}}});

  // C15 donut composicion
  const tg = r.tipo_gasto;
  const total_tg = tg.reduce((s,t)=>s+t.importe,0);
  new Chart(document.getElementById('c15'),{{type:'doughnut',data:{{
    labels:tg.map(t=>t.tipo),
    datasets:[{{data:tg.map(t=>t.importe),backgroundColor:[CL.b,CL.r,CL.a],borderWidth:0}}]
  }},options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{boxWidth:10}}}},tooltip:{{callbacks:{{label:c=>c.label+': '+(c.raw/total_tg*100).toFixed(1)+'% ('+MM(c.raw)+')'}}}}}}}}}});

  // C14 ratio RRHH/Ventas por sucursal
  const rs = r.ratio_suc || [];
  if(rs.length){{
    const ratios = rs.map(s=>s.ratio);
    mkChart('c14','bar',rs.map(s=>s.suc),[
      {{label:'RRHH/Ventas %',data:ratios,
        backgroundColor:ratios.map(v=>v>100?CL.r:v>45?CL.a:CL.g),borderRadius:4}}
    ],{{
      scales:{{y:{{beginAtZero:true,ticks:{{callback:v=>v+'%'}}}}}},
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{
        label:c=>c.dataset.label+': '+c.raw.toFixed(1)+'%',
        afterLabel:c=>{{
          const s=rs[c.dataIndex];
          return 'RRHH: '+MM(s.rrhh)+'  Ventas: '+MM(s.venta);
        }}
      }}}}}}
    }});
  }}

  // Tabla
  const tbody=document.getElementById('tbody-rrhh');
  if(tbody) tg.forEach(t=>{{
    tbody.innerHTML+=`<tr>
      <td>${{t.tipo}}</td>
      <td class="r">${{MM(t.importe)}}</td>
      <td class="r">${{(t.importe/r.total_2025*100).toFixed(1)}}%</td>
    </tr>`;
  }});

  // Info boxes
  const ibR = document.getElementById('ib-rrhh');
  if(ibR){{
    const ratioN = parseFloat(ratio);
    if(ratioN>70) ibR.innerHTML+=`<div class="ib al"><b>🔴 CRÍTICO: RRHH/Ventas en ${{ratio}}% — muy sobre umbral recomendado</b>Un nivel saludable para estética es 35-45%. El ratio actual requiere plan de reducción de costos de personal.</div>`;
    // Per-sucursal worst analysis
    const worstSucs=(r.ratio_suc||[]).filter(s=>s.ratio>90).slice(0,2);
    if(worstSucs.length>=2)
      ibR.innerHTML+=`<div class="ib al"><b>🔴 ${{worstSucs[0].suc}} (${{worstSucs[0].ratio.toFixed(0)}}%) y ${{worstSucs[1].suc}} (${{worstSucs[1].ratio.toFixed(0)}}%) pagan más en personal que lo que facturan</b>Estas unidades operan con RRHH mayor a sus ingresos. Requiere revisión inmediata de dotación y productividad.</div>`;
    else if(worstSucs.length===1)
      ibR.innerHTML+=`<div class="ib al"><b>🔴 ${{worstSucs[0].suc}} (${{worstSucs[0].ratio.toFixed(0)}}%) opera con RRHH que supera sus ingresos</b>Requiere revisión inmediata de dotación y productividad por box/profesional.</div>`;
    else if(ratioN>50) ibR.innerHTML+=`<div class="ib al"><b>🔴 RRHH/Ventas en ${{ratio}}% — sobre umbral crítico</b>Representa un riesgo operacional severo que requiere plan de reducción de costos de personal.</div>`;
    else if(ratioN>35) ibR.innerHTML+=`<div class="ib cau"><b>🟡 RRHH Elevado: ratio ${{ratio}}% por encima del umbral recomendado (35%)</b>Monitorear evolución y revisar eficiencia por sucursal.</div>`;
    else ibR.innerHTML+=`<div class="ib ok"><b>🟢 RRHH Controlado: ratio ${{ratio}}% dentro de rango saludable</b>Mantener estructura actual y revisar bonos para asegurar sostenibilidad.</div>`;
    const bonos = tg.find(t=>(t.tipo||'').toLowerCase().includes('bono'));
    if(bonos && bonos.importe/r.total_2025>0.35) ibR.innerHTML+=`<div class="ib act"><b>🔵 Bonos (${{MM(bonos.importe)}} = ${{(bonos.importe/r.total_2025*100).toFixed(0)}}% del total RRHH) superan a remuneraciones fijas</b>Revisar la política de bonos: deben estar condicionados a cumplimiento de presupuesto.</div>`;
  }}
}}

// ── M6 ADM + OP ──────────────────────────────────────────────────────────
function buildAdmOp(){{
  const ao = D.adm_op;
  const total = ao.adm_total+ao.op_total;

  mkChart('c16','bar',ao.adm_tipo.map(t=>t.tipo),
    [{{label:'$',data:ao.adm_tipo.map(t=>t.monto),backgroundColor:ao.adm_tipo.map((_,i)=>PALETTE[i%PALETTE.length]),borderRadius:4,indexAxis:'y'}}],
    {{indexAxis:'y',plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>MM(c.raw)}}}}}},scales:{{x:{{ticks:{{callback:v=>MM(v)}}}},y:{{ticks:{{font:{{size:10}}}}}}}}}});

  mkChart('c17','bar',ao.op_tipo.map(t=>t.tipo),
    [{{label:'$',data:ao.op_tipo.map(t=>t.monto),backgroundColor:ao.op_tipo.map((_,i)=>PALETTE[i%PALETTE.length]),borderRadius:4,indexAxis:'y'}}],
    {{indexAxis:'y',plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>MM(c.raw)}}}}}},scales:{{x:{{ticks:{{callback:v=>MM(v)}}}},y:{{ticks:{{font:{{size:10}}}}}}}}}});

  // Tabla Administrativo
  const tbAdm = document.getElementById('tbody-adm');
  if(tbAdm){{
    ao.adm_tipo.forEach(t=>{{
      const pct = ao.adm_total? (t.monto/ao.adm_total*100).toFixed(1) : '0.0';
      const cls = parseFloat(pct)>20?'tg-b':parseFloat(pct)>10?'tg-a':'';
      tbAdm.innerHTML+=`<tr><td>${{t.tipo}}</td><td class="r">${{(t.monto/1e6).toFixed(1)}}</td><td class="r">${{cls?`<span class="tg ${{cls}}">${{pct}}%</span>`:pct+'%'}}</td></tr>`;
    }});
    tbAdm.innerHTML+=`<tr style="font-weight:700"><td>TOTAL</td><td class="r">${{(ao.adm_total/1e6).toFixed(1)}}M</td><td class="r">100%</td></tr>`;
  }}

  // Tabla Operativo
  const tbOp = document.getElementById('tbody-op');
  if(tbOp){{
    ao.op_tipo.forEach(t=>{{
      const pct = ao.op_total? (t.monto/ao.op_total*100).toFixed(1) : '0.0';
      const cls = parseFloat(pct)>50?'tg-b':parseFloat(pct)>15?'tg-a':'';
      tbOp.innerHTML+=`<tr><td>${{t.tipo}}</td><td class="r">${{(t.monto/1e6).toFixed(1)}}</td><td class="r">${{cls?`<span class="tg ${{cls}}">${{pct}}%</span>`:pct+'%'}}</td></tr>`;
    }});
    tbOp.innerHTML+=`<tr style="font-weight:700"><td>TOTAL</td><td class="r">${{(ao.op_total/1e6).toFixed(1)}}M</td><td class="r">100%</td></tr>`;
  }}

  // Info boxes
  const ibA = document.getElementById('ib-adm');
  if(ibA){{
    const retiro = ao.adm_tipo.find(t=>(t.tipo||'').toLowerCase().includes('retiro'));
    const finiq  = ao.adm_tipo.find(t=>(t.tipo||'').toLowerCase().includes('finiq'));
    if(retiro && ao.adm_total && retiro.monto/ao.adm_total>0.20)
      ibA.innerHTML+=`<div class="ib cau"><b>🟡 Retiros de socios (${{MM(retiro.monto)}}) son el 2do mayor gasto administrativo</b>Presionan la caja en un momento donde el flujo ya es crítico. Considerar postergar retiros.</div>`;
    if(finiq && ao.adm_total && finiq.monto/ao.adm_total>0.10)
      ibA.innerHTML+=`<div class="ib cau"><b>🟡 Finiquitos (${{MM(finiq.monto)}}) señalan rotación elevada</b>Ciclos de contratación-desvinculación costosos combinados con RRHH alto.</div>`;
    const opPct = D.ventas.total_2025? (ao.op_total/D.ventas.total_2025*100).toFixed(1) : 0;
    if(parseFloat(opPct)<12)
      ibA.innerHTML+=`<div class="ib ok"><b>🟢 Costos operativos directos controlados (~${{opPct}}% de ventas)</b>Consumibles y operación representan un ratio sano para el sector.</div>`;
  }}
}}

// ── M6 SEGMENTACIÓN POR SUCURSAL ─────────────────────────────────────────────
function buildSegmentacion(){{
  const seg = D.seg;
  if(!seg || !seg.por_sucursal || !seg.por_sucursal.length) return;
  const s = seg.por_sucursal;
  const labels = s.map(r=>r.suc);

  document.getElementById('kpi-seg').innerHTML =
    kpiCard('Costos Totales Seg.', MM(seg.total_costos),'') +
    kpiCard('Margen Bruto Global', MM(seg.total_margen),'') +
    kpiCard('Margen % Global', seg.margen_pct_global.toFixed(1)+'%','') +
    kpiCard('Sucursales', s.length,'');

  // Stacked bar: RRHH + Admin + Op + No Op por sucursal
  mkChart('c_seg1','bar',labels,[
    {{label:'RRHH',     data:s.map(r=>r.rrhh),   backgroundColor:'rgba(56,189,248,.85)',  stack:'c'}},
    {{label:'Admin',    data:s.map(r=>r.admin),  backgroundColor:'rgba(167,139,250,.85)', stack:'c'}},
    {{label:'Op',       data:s.map(r=>r.op),     backgroundColor:'rgba(251,146,60,.85)',  stack:'c'}},
    {{label:'No Op',    data:s.map(r=>r.no_op),  backgroundColor:'rgba(244,114,182,.85)', stack:'c'}},
  ],{{
    scales:{{
      x:{{stacked:true,ticks:{{font:{{size:10}}}}}},
      y:{{stacked:true,ticks:{{callback:v=>MM(v)}}}}
    }},
    plugins:{{tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+MM(c.raw)}}}}}}
  }});

  // Bar: Margen % por sucursal
  mkChart('c_seg2','bar',labels,
    [{{label:'Margen %',data:s.map(r=>r.margen_pct),
      backgroundColor:s.map(r=>r.margen_pct>=50?'rgba(34,197,94,.8)':r.margen_pct>=30?'rgba(245,158,11,.8)':'rgba(239,68,68,.8)'),
      borderRadius:4}}],
    {{
      plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>c.raw.toFixed(1)+'%'}}}}}},
      scales:{{y:{{ticks:{{callback:v=>v+'%'}}}}}}
    }});

  // Tabla detalle
  const tbody=document.getElementById('tbody-seg');
  s.forEach(r=>{{
    const mgtg=r.margen_pct>=50?'tg-g':r.margen_pct>=30?'tg-a':'tg-r';
    tbody.innerHTML+=`<tr>
      <td style="font-weight:600">${{r.suc}}</td>
      <td class="r">${{MM(r.ingresos)}}</td>
      <td class="r">${{MM(r.rrhh)}}</td>
      <td class="r">${{MM(r.admin)}}</td>
      <td class="r">${{MM(r.op)}}</td>
      <td class="r">${{MM(r.no_op)}}</td>
      <td class="r">${{MM(r.costos)}}</td>
      <td class="r">${{MM(r.margen)}}</td>
      <td class="r"><span class="tg ${{mgtg}}">${{r.margen_pct.toFixed(1)}}%</span></td>
    </tr>`;
  }});
}}

// ── M7 NO OP + MKT ────────────────────────────────────────────────────────
function buildNoOp(){{
  const nop = D.no_op;
  document.getElementById('kpi-nop').innerHTML =
    kpiCard('Gs No Op 2025+2026', MM(nop.total),'') +
    kpiCard('Inversión Digital (hist.)', MM((nop.tipo.find(t=>t.tipo.toLowerCase().includes('digital'))||{{monto:0}}).monto),'') +
    kpiCard('Mkt Tradicional 2025', MM(D.mkt.total_2025),'') +
    kpiCard('Sin datos 2026', '—', 'Datos reales hasta mar 2026','');

  const NOP_LABELS={{'Inversión digital':'Inv.Digital','Gs Financieros - Bancos':'Gs Fin Bancos','Gs Financieros - TGR':'Gs Fin TGR','Gs Financieros':'Gs Financ.','Asesorías, Honorarios y Consultorías':'Asesorías','Soporte a sistemas TI':'Soporte TI','Gs Marketing y Publicidad':'Mkt Trad.','Ss Aseo':'Ss Aseo','Otros gastos':'Otros','Ss de Seguridad':'Ss Seguridad','Ss de Música ambiental':'Ss Música','Ss Generales':'Ss Generales','Ss Jardinería':'Ss Jardinería'}};
  mkChart('c18','bar',nop.tipo.map(t=>NOP_LABELS[t.tipo]||t.tipo),
    [{{label:'$',data:nop.tipo.map(t=>t.monto),backgroundColor:nop.tipo.map((_,i)=>PALETTE[i%PALETTE.length]),borderRadius:4,indexAxis:'y'}}],
    {{indexAxis:'y',plugins:{{legend:{{display:false}},tooltip:{{callbacks:{{label:c=>MM(c.raw)}}}}}},scales:{{x:{{ticks:{{callback:v=>MM(v)}}}},y:{{grid:{{display:false}},ticks:{{font:{{size:10}}}}}}}}}});

  // Tabla proveedores
  const tbody=document.getElementById('tbody-prov');
  const conceptoClase = (tipo) => {{
    const t = tipo.toLowerCase();
    if(t.includes('digital')) return 'concepto-digital';
    if(t.includes('deuda')) return 'concepto-deuda';
    if(t.includes('marketing')) return 'concepto-marketing';
    if(t.includes('soporte')) return 'concepto-soporte';
    if(t.includes('servicios')) return 'concepto-servicios';
    if(t.includes('asesoría')) return 'concepto-asesorias';
    if(t.includes('leasing')) return 'concepto-leasing';
    if(t.includes('financiero')) return 'concepto-financiero';
    return 'concepto-otro';
  }};
  nop.proveedores.forEach(p=>{{
    const cls = conceptoClase(p.tipo);
    tbody.innerHTML+=`<tr>
      <td style="font-size:12px">${{p.prov}}</td>
      <td class="r">${{MM(p.monto)}}</td>
      <td class="r">${{(p.monto/nop.total*100).toFixed(1)}}%</td>
      <td><span class="concepto ${{cls}}">${{p.tipo}}</span></td>
    </tr>`;
  }});

  // Tabla marketing (año/inversión/ventas/ROI)
  const tbody2=document.getElementById('tbody-mkt-roi');
  if(tbody2){{
    const mktSummary = [
      {{anio:'2024', inv: D.mkt.total_2024, ventas: D.ventas.total_2024}},
      {{anio:'2025', inv: D.mkt.total_2025, ventas: D.ventas.total_2025}},
      // 2026 excluido — datos reales solo hasta marzo 2026
    ];
    mktSummary.forEach(r=>{{
      const roi = r.inv>0? (r.ventas/r.inv).toFixed(1)+'x' : 'S/D';
      tbody2.innerHTML+=`<tr>
        <td>${{r.anio}}</td>
        <td class="r">${{MM(r.inv)}}</td>
        <td class="r">${{MM(r.ventas)}}</td>
        <td class="r">${{roi}}</td>
      </tr>`;
    }});
  }}

  // Info boxes
  const ibN = document.getElementById('ib-nop');
  if(ibN){{
    const nop = D.no_op;
    // Comparaciones 2026 excluidas — datos reales solo hasta marzo 2026
    const nopDig = nop.tipo.find(t=>(t.tipo||'').toLowerCase().includes('digital'))||{{monto:0}};
    const nopGsFin = nop.tipo.filter(t=>(t.tipo||'').toLowerCase().includes('financ')||t.tipo.toLowerCase().includes('banco')||t.tipo.toLowerCase().includes('tgr')).reduce((s,t)=>s+t.monto,0);
    if(nop.digital_2025>0) ibN.innerHTML+=`<div class="ib ok"><b>🟢 Gs No Operacionales 2025: ${{MM(nop.total_2025)}}</b>Incluye gastos financieros, inversión digital (${{MM(nop.digital_2025)}}) y otros costos no operacionales del año completo.</div>`;
    const topProv = (nop.proveedores||[]).sort((a,b)=>b.monto-a.monto)[0];
    if(topProv && nop.total && topProv.monto/nop.total>0.20) ibN.innerHTML+=`<div class="ib cau"><b>🟡 Concentración en un solo proveedor digital: ${{topProv.prov}} (${{MM(topProv.monto)}}, ${{(topProv.monto/nop.total*100).toFixed(0)}}% del total No Op)</b>Toda la inversión digital se canaliza por un proveedor. Riesgo de dependencia y falta de benchmarking de costo/resultado.</div>`;
    ibN.innerHTML+=`<div class="ib act"><b>🔵 Datos 2026 disponibles solo hasta marzo</b>Las comparaciones interanuales de gastos no operacionales y marketing se actualizarán cuando estén disponibles los datos completos.</div>`;
  }}
}}

// ── M8 CONCLUSIONES ───────────────────────────────────────────────────────
function buildConclusiones(){{
  const k = D.kpis;
  const vv = D.ventas;
  const fl = D.flujo;

  const alertas = [];
  const oks = [];

  // ── ALERTAS (4) ──────────────────────────────────────────────────────────
  // 1. Crisis de caja inminente
  const minAcumC = Math.min(...fl.flujo_acum);
  const mesMinC  = fl.labels[fl.flujo_acum.indexOf(minAcumC)]||'';
  const primerNegC = fl.flujo_acum.findIndex(v=>v<0);
  const primerNegMesC = primerNegC>=0 ? fl.labels[primerNegC] : null;
  if(minAcumC<0) {{
    const agotaMes = primerNegMesC ? primerNegMesC+'-'+(fl.labels[Math.min(primerNegC+1,11)]||mesMinC) : mesMinC;
    alertas.push({{cls:'al',titulo:'Crisis de caja inminente',
      txt:'Flujo acumulado llega a '+MM(minAcumC)+' en '+mesMinC+'. Con '+MM(fl.saldo_inicial)+' de saldo, la caja se agota entre '+agotaMes+'.'}});
  }}

  // 2. RRHH insostenible (base 2025 — datos reales completos)
  if(k.rrhh_ratio>60) alertas.push({{cls:'al',titulo:'RRHH insostenible',
    txt:'El ratio RRHH/Ventas 2025 es '+k.rrhh_ratio+'% (referencia saludable: 35-45%). Destruye cualquier margen operacional.'}});
  else if(k.rrhh_ratio>45) alertas.push({{cls:'al',titulo:'RRHH Crítico',
    txt:'El ratio RRHH/Ventas 2025 es '+k.rrhh_ratio+'% (referencia saludable: 35-45%). Requiere plan de reducción.'}});

  // 3. F&B + Therapy superpasan ventas en personal
  const sucOverRrhh = (D.rrhh.ratio_suc||[]).filter(s=>s.ratio>100).slice(0,2);
  if(sucOverRrhh.length>=2) {{
    alertas.push({{cls:'al',titulo:sucOverRrhh[0].suc.replace('NCA ','')+' + '+sucOverRrhh[1].suc.replace('NCA ',''),
      txt:'RRHH supera '+sucOverRrhh[0].ratio.toFixed(0)+'–'+sucOverRrhh[1].ratio.toFixed(0)+'% de sus ventas. Operan a pérdida antes de cualquier otro gasto.'}});
  }} else if(sucOverRrhh.length===1) {{
    alertas.push({{cls:'al',titulo:sucOverRrhh[0].suc.replace('NCA ',''),
      txt:'RRHH supera '+sucOverRrhh[0].ratio.toFixed(0)+'% de sus ventas. Opera a pérdida antes de cualquier otro gasto.'}});
  }}

  // 4. Ticket promedio cae
  const tickIni = vv.ticket_2024&&vv.ticket_2024[0]>0 ? vv.ticket_2024[0] : 0;
  const tickFin = vv.ticket_2025&&vv.ticket_2025[11]>0 ? vv.ticket_2025[11] : 0;
  const tickCaidaPct = tickIni>0 ? Math.round((tickFin-tickIni)/tickIni*100) : 0;
  if(tickCaidaPct<=-20) alertas.push({{cls:'cau',titulo:'Ticket promedio cae '+Math.abs(tickCaidaPct)+'%',
    txt:'De '+CLP(tickIni)+' a '+CLP(tickFin)+' en 2 años, señal de commoditización.'}});
  else if(tickCaidaPct<0) alertas.push({{cls:'cau',titulo:'Ticket promedio en caída',
    txt:'Cayó '+Math.abs(tickCaidaPct)+'% desde '+CLP(tickIni)+'. Revisar estrategia de pricing.'}});

  // ── OKS (6) ──────────────────────────────────────────────────────────────
  // 1. Ingresos sobre presupuesto
  const tot26 = D.eerr.sucursales.find(s=>s.nombre==='TOTAL')||{{}};
  if((tot26.cumpl||0)>=100) oks.push({{cls:'ok',titulo:'Ingresos '+D.eerr.mes+' sobre presupuesto ('+tot26.cumpl.toFixed(1)+'%)',
    txt:'La demanda responde.'}});

  // 2. Mejor performer EERR
  const bestSuc = D.eerr.sucursales.filter(s=>s.nombre!=='TOTAL'&&s.ingresos>0).sort((a,b)=>b.cumpl-a.cumpl)[0];
  if(bestSuc&&bestSuc.cumpl>150) oks.push({{cls:'ok',titulo:bestSuc.nombre.replace('NCA ','')+' sorprende con '+bestSuc.cumpl.toFixed(0)+'% de cumplimiento',
    txt:'Investigar drivers replicables.'}});

  // 3. Gs No Op — sin comparación 2026 (datos solo hasta marzo)

  // 4. Costos operativos controlados
  const totalVentas = vv.total_2025||1;
  const opPctC = D.adm_op.op_total ? (D.adm_op.op_total/totalVentas*100).toFixed(1) : null;
  if(opPctC&&parseFloat(opPctC)<12) oks.push({{cls:'ok',titulo:'Costos operativos directos controlados (~'+opPctC+'% de ventas)',
    txt:'Buena gestión de insumos.'}});

  // 5. Cartera diversificada
  const trats = D.tratamientos||[];
  const totalIngT = trats.reduce((s,t)=>s+t.ingresos,0)||1;
  const top5Pct = trats.slice(0,5).reduce((s,t)=>s+t.ingresos,0)/totalIngT*100;
  if(trats.length>=5&&top5Pct<85) oks.push({{cls:'ok',titulo:'Cartera diversificada',
    txt:'5 tratamientos top concentran '+top5Pct.toFixed(0)+'% con buen balance.'}});

  // 6. Q4 flujo positivo
  const q4vals = fl.flujo_caja.slice(9,11); // Oct-Nov (índices 9-10)
  if(q4vals.every(v=>v>0)) oks.push({{cls:'ok',titulo:'Q4 fuerte',
    txt:'Oct-Nov generan flujos positivos que alivian parcialmente.'}});

  // Render col-alertas (formato p+b+br como reference)
  const colA = document.getElementById('col-alertas');
  if(colA){{
    let aHtml='<h3 style="color:var(--rd)">🔴 Alertas Críticas</h3><p style="font-size:12px;margin-top:6px">';
    alertas.forEach((a,i)=>{{ aHtml+=`<b>${{i+1}}. ${{a.titulo}}:</b> ${{a.txt}}${{i<alertas.length-1?'<br><br>':''}}`; }});
    colA.innerHTML=aHtml+'</p>';
  }}

  // Render col-ok (mismo formato)
  const colO = document.getElementById('col-ok');
  if(colO){{
    let oHtml='<h3 style="color:var(--gn)">🟢 Lo que Funciona</h3><p style="font-size:12px;margin-top:6px">';
    oks.forEach((o,i)=>{{ oHtml+=`<b>${{i+1}}. ${{o.titulo}}:</b> ${{o.txt}}${{i<oks.length-1?'<br><br>':''}}`; }});
    colO.innerHTML=oHtml+'</p>';
  }}

  // Render col-plan — bullets específicos igual al reference
  const colP = document.getElementById('col-plan');
  if(colP){{
    const sucsBadPlan = D.eerr.sucursales.filter(s=>s.nombre!=='TOTAL'&&s.ingresos>0&&s.cumpl<70).map(s=>s.nombre.replace('NCA ','')).join(' y ')||'sucursales bajo rendimiento';
    const topProvPlan = (D.no_op.proveedores||[]).sort((a,b)=>b.monto-a.monto)[0];
    const topProvStr = topProvPlan ? topProvPlan.prov : 'proveedor digital';
    let pHtml='<h3 style="color:var(--ac)">🔵 Acciones Recomendadas</h3><p style="font-size:12px;margin-top:6px">';
    pHtml+=`<b>Inmediato (0-30 días):</b><br>`;
    if(sucOverRrhh.length>=1) pHtml+=`• Auditar dotación de ${{sucOverRrhh.map(s=>s.suc.replace('NCA ','')).join(' y ')}} — reducir a breakeven<br>`;
    if(minAcumC<0) pHtml+=`• Negociar línea de crédito revolving para puente ${{primerNegMesC||mesMinC}}-${{mesMinC}}<br>`;
    pHtml+=`• Congelar retiros de socios hasta estabilizar caja<br><br>`;
    pHtml+=`<b>Corto plazo (1-3 meses):</b><br>`;
    pHtml+=`• Reformular bonos: atar 100% a cumplimiento de ppto<br>`;
    pHtml+=`• Evaluar rebaja PPM ante SII<br>`;
    pHtml+=`• Plan comercial para ${{sucsBadPlan}}<br>`;
    pHtml+=`• Diversificar proveedores de marketing digital<br><br>`;
    pHtml+=`<b>Largo plazo (3-12 meses):</b><br>`;
    pHtml+=`• Fijar techo de RRHH en 45% de ventas por sucursal<br>`;
    pHtml+=`• KPIs de productividad por box/profesional<br>`;
    pHtml+=`• Redistribuir costos Casa Matriz como % por sucursal<br>`;
    pHtml+=`• Estrategia de ticket: subir valor promedio a $280K+</p>`;
    colP.innerHTML=pHtml;
  }}

  // Tabla resumen ejecutivo — filas que coinciden con reference
  const tbRes = document.getElementById('tbody-resumen');
  if(tbRes){{
    const tot26 = D.eerr.sucursales.find(s=>s.nombre==='TOTAL')||{{}};
    const sucsBad = D.eerr.sucursales.filter(s=>s.nombre!=='TOTAL'&&s.ingresos>0&&s.cumpl<70);
    const txns25 = (vv.trans_2025||[]).reduce((s,v)=>s+v,0);
    const txns24 = (vv.trans_2024||[]).reduce((s,v)=>s+v,0);
    const txnVar = txns24>0 ? ((txns25-txns24)/txns24*100).toFixed(1) : 0;
    const mesesNeg = fl.flujo_acum.filter(v=>v<0).length;
    const provMkt = (D.no_op.proveedores||[]).filter(p=>p.tipo&&p.tipo.toLowerCase().includes('digital'));
    const nProvNop = provMkt.length;
    const topProvNop = provMkt.sort((a,b)=>b.monto-a.monto)[0];
    const totalMkt = provMkt.reduce((s,p)=>s+p.monto,0);
    const topProvPct = topProvNop&&totalMkt?(topProvNop.monto/totalMkt*100).toFixed(0):0;
    const tickAvg25 = vv.ticket_2025&&vv.ticket_2025.filter(t=>t>0).length ? vv.ticket_2025.filter(t=>t>0).reduce((a,b)=>a+b,0)/vv.ticket_2025.filter(t=>t>0).length : 0;
    const rows = [
      ['Ventas 2025', MM(vv.total_2025), PCT(k.var_ventas)+' vs 2024', k.var_ventas>=0?'tg-g':'tg-r', k.var_ventas>=0?'OK':'ALERTA'],
      ['Cumplimiento Ppto '+D.eerr.mes+' '+D.eerr.anio, (tot26.cumpl||0).toFixed(1)+'%', (tot26.cumpl||0)>=100?'Sobre meta':'Bajo meta', (tot26.cumpl||0)>=100?'tg-g':'tg-a', (tot26.cumpl||0)>=100?'OK':'RIESGO'],
      ['RRHH / Ventas 2025', k.rrhh_ratio+'%', k.rrhh_ratio>70?'+'+((k.rrhh_ratio-45).toFixed(0))+'pp vs umbral':'ref. 35-45%', k.rrhh_ratio>70?'tg-r':k.rrhh_ratio>50?'tg-a':'tg-g', k.rrhh_ratio>70?'CRÍTICO':k.rrhh_ratio>50?'ALERTA':'OK'],
      ['Ticket Promedio 2025', tickAvg25>0?CLP(tickAvg25):'—', PCT(k.ticket_var)+' vs 2024', k.ticket_var>=-10?'tg-g':'tg-a', k.ticket_var>=-10?'OK':'ALERTA'],
      ['Gs No Operacionales 2025', MM(D.no_op.total_2025||D.no_op.total), 'Dato real completo', 'tg-a', 'REVISAR'],
      ['Margen Operacional 2025', k.margen_op.toFixed(1)+'%', 'año completo', k.margen_op>30?'tg-g':k.margen_op>20?'tg-a':'tg-r', k.margen_op>30?'SANO':k.margen_op>20?'ALERTA':'CRÍTICO'],
      ['Sucursales <70% Cumpl.', sucsBad.length+' de '+(D.eerr.sucursales.filter(s=>s.nombre!=='TOTAL'&&s.ingresos>0).length), sucsBad.map(s=>s.nombre.replace('NCA ','')).join('+'), sucsBad.length>0?'tg-a':'tg-g', sucsBad.length>0?'RIESGO':'OK'],
      ['Transacciones 2025', txns25>0?NUM(txns25):'—', txns25>0?txnVar+'% vs 2024':'sin dato', txns25>0?(parseFloat(txnVar)>=0?'tg-g':'tg-a'):'tg-a', txns25>0?(parseFloat(txnVar)>=0?'OK':'ALERTA'):'REVISAR'],
      ['Concentración Mkt', topProvNop?'1 proveedor':'—', topProvNop?(topProvNop.prov+' '+topProvPct+'%'):'—', (nProvNop===1||parseInt(topProvPct)>50)?'tg-r':'tg-g', (nProvNop===1||parseInt(topProvPct)>50)?'RIESGO':'OK'],
    ];
    rows.forEach(([ind,val,tend,cls,lbl])=>{{
      tbRes.innerHTML+=`<tr>
        <td style="font-size:12px">${{ind}}</td>
        <td class="mono">${{val}}</td>
        <td class="${{parseFloat(tend)>0?'up':parseFloat(tend)<0?'dn':'mono'}}">${{tend}}</td>
        <td>${{cls&&lbl?`<span class="tg ${{cls}}">${{lbl}}</span>`:''}}</td>
      </tr>`;
    }});
  }}
}}

// ── INIT ──────────────────────────────────────────────────────────────────
buildEERR();
buildVentas();
buildDetalle();
buildRRHH();
buildAdmOp();
buildSegmentacion();
buildNoOp();
buildConclusiones();

// Highlight nav on scroll — usa clase CSS .active (no inline styles)
const sections = document.querySelectorAll('section[id]');
const navLinks  = document.querySelectorAll('.nav a');
window.addEventListener('scroll',()=>{{
  let curr='';
  sections.forEach(s=>{{ if(window.scrollY>=s.offsetTop-80) curr=s.id; }});
  navLinks.forEach(a=>{{
    const isActive=a.getAttribute('href')==='#'+curr;
    a.classList.toggle('active',isActive);
    a.setAttribute('aria-current',isActive?'true':'false');
  }});
}},{{passive:true}});
</script>

<!-- Barra de sesión NCA (inyectada por servidor) -->
<style>
#nca-bar{{
  position:fixed!important;top:12px!important;right:16px!important;
  z-index:2147483647!important;display:flex!important;align-items:center!important;
  gap:8px!important;padding:7px 14px!important;
  background:rgba(10,10,20,0.93)!important;
  backdrop-filter:blur(14px)!important;
  border-radius:10px!important;border:1px solid rgba(255,255,255,0.13)!important;
  box-shadow:0 4px 24px rgba(0,0,0,0.55)!important;
  font-family:'Segoe UI',sans-serif!important;
}}
#nca-bar .u{{color:rgba(255,255,255,0.55)!important;font-size:12px!important;margin-right:2px!important}}
#nca-bar a{{
  padding:5px 13px!important;border-radius:6px!important;
  font-size:12px!important;font-weight:600!important;
  text-decoration:none!important;transition:all .2s!important;cursor:pointer!important;
}}
#nca-bar .n{{background:rgba(79,142,247,0.18)!important;border:1px solid rgba(79,142,247,0.4)!important;color:#93c5fd!important}}
#nca-bar .n:hover{{background:rgba(79,142,247,0.35)!important;color:#fff!important}}
#nca-bar .x{{background:rgba(239,68,68,0.18)!important;border:1px solid rgba(239,68,68,0.4)!important;color:#fca5a5!important}}
#nca-bar .x:hover{{background:rgba(239,68,68,0.35)!important;color:#fff!important}}
</style>
<div id="nca-bar">
  <span class="u" id="nca-user"></span>
  <a class="n" id="nca-nuevo" href="/nuevo" style="display:none">📂 Nuevo archivo</a>
  <a class="x" id="nca-logout" href="/logout" style="display:none">Cerrar sesión</a>
</div>
<script>
// Solo mostrar la barra si se está sirviendo desde el servidor Flask (no archivo local)
(function(){{
  if(window.location.protocol==='http:'||window.location.protocol==='https:'){{
    document.getElementById('nca-nuevo').style.display='';
    document.getElementById('nca-logout').style.display='';
    // Obtener nombre de usuario desde el servidor
    fetch('/api/whoami').then(r=>r.json()).then(d=>{{
      if(d.nombre) document.getElementById('nca-user').textContent='👤 '+d.nombre;
    }}).catch(()=>{{}});
  }}
}})();
</script>

</body>
</html>"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    """
    Función principal: orquesta la lectura del Excel, ETL y generación del dashboard.

    Flujo:
    1. Valida archivo Excel
    2. Lee y procesa 8 módulos de datos (EERR, Flujo, Ventas, RRHH, etc)
    3. Genera HTML con 8 secciones interactivas
    4. Guarda output y reporta ubicación

    Raises:
        SystemExit: Si hay error crítico en configuración o datos
    """
    try:
        parser = argparse.ArgumentParser(description="Genera dashboard NCA desde el Excel.")
        parser.add_argument("--file",   default=str(EXCEL_DEFAULT), help="Ruta al Excel de NCA")
        parser.add_argument("--output", default=str(OUTPUT_DEFAULT), help="Ruta HTML de salida")
        args = parser.parse_args()

        excel_path  = Path(args.file)
        output_path = Path(args.output)

        # Validar Excel
        if not excel_path.exists():
            logger.error(f"❌ Archivo no encontrado: {excel_path}")
            sys.exit(1)
        logger.info(f"✅ Archivo Excel validado: {excel_path.name}")

        # Crear directorio output si no existe
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"📂 Directorio output listo: {output_path.parent}")

        print(f"\n{'='*60}")
        print(f"  DASHBOARD NCA")
        print(f"{'='*60}")
        print(f"  Archivo: {excel_path.name}\n")

        xl = pd.ExcelFile(excel_path, engine="openpyxl")
        hojas_disponibles = xl.sheet_names
        logger.info(f"📖 Excel abierto con {len(hojas_disponibles)} hojas: {hojas_disponibles}")

        # Diagnóstico: verificar qué hojas esperadas existen
        faltantes = [k for k, v in SHEET_MAP.items() if v not in hojas_disponibles]
        if faltantes:
            print(f"\n  ⚠️  Hojas disponibles en el Excel:")
            for h in hojas_disponibles:
                print(f"       · {h}")
            print(f"\n  ⚠️  Módulos sin hoja mapeada (se saltarán): {', '.join(faltantes)}")
            print(f"     → Actualiza [sheets] en config.ini para mapearlos.")
            print()
        else:
            logger.info("✅ Todas las hojas requeridas encontradas")

        # ETL: Leyendo módulos con validación (hojas faltantes se omiten con datos vacíos)
        print("  Leyendo EERR...", end=" ", flush=True)
        eerr = _leer_safe(leer_eerr, xl, "eerr")
        logger.info(f"EERR: {eerr['mes']} {eerr['anio']} - {len(eerr['sucursales'])} sucursales")
        if eerr['sucursales']:
            print(f"OK ({eerr['mes']} {eerr['anio']})")

        print("  Leyendo Flujo de Caja...", end=" ", flush=True)
        flujo = _leer_safe(leer_flujo, xl, "flujo")
        neg_meses = len([v for v in flujo['flujo_caja'] if v < 0])
        logger.info(f"Flujo: {neg_meses} meses con flujo negativo")
        if any(flujo['flujo_caja']):
            print(f"OK ({neg_meses} meses negativos)")

        print("  Leyendo Ventas...", end=" ", flush=True)
        ventas = _leer_safe(leer_ventas, xl, "ventas")
        logger.info(f"Ventas: {ventas['total_txns']:,} transacciones")
        if ventas['total_txns']:
            print(f"OK ({ventas['total_txns']:,} transacciones)")

        print("  Leyendo RRHH...", end=" ", flush=True)
        rrhh = _leer_safe(leer_rrhh, xl, "rrhh")
        logger.info(f"RRHH: 2025=${rrhh['total_2025']/1e9:.2f}B")
        if rrhh['total_2025']:
            print(f"OK (2025: ${rrhh['total_2025']/1e9:.2f}B)")

        print("  Leyendo Gastos Adm+Op...", end=" ", flush=True)
        adm_op = _leer_safe(leer_admin_op, xl, "adm_op")
        logger.info(f"Admin+Op: Adm=${adm_op['adm_total']/1e6:.0f}M | Op=${adm_op['op_total']/1e6:.0f}M")
        if adm_op['adm_total'] or adm_op['op_total']:
            print(f"OK (Adm: ${adm_op['adm_total']/1e6:.0f}M | Op: ${adm_op['op_total']/1e6:.0f}M)")

        print("  Leyendo Gastos No Operacionales...", end=" ", flush=True)
        no_op = _leer_safe(leer_no_op, xl, "no_op")
        logger.info(f"No Op: ${no_op['total']/1e6:.0f}M - {len(no_op['proveedores'])} proveedores")
        if no_op['total']:
            print(f"OK (${no_op['total']/1e6:.0f}M total)")

        print("  Leyendo Marketing...", end=" ", flush=True)
        mkt = _leer_safe(leer_marketing, xl, "mkt")
        logger.info(f"Marketing: 2024=${mkt['total_mkt_2024']/1e6:.0f}M | 2025=${mkt['total_mkt_2025']/1e6:.0f}M")
        if mkt['total_mkt_2024'] or mkt['total_mkt_2025']:
            print(f"OK")

        print("  Segmentando costos por sucursal...", end=" ", flush=True)
        seg = _leer_safe(segmentar_costos, xl, "seg")
        n_suc = len(seg.get("por_sucursal", []))
        logger.info(f"Segmentación: {n_suc} sucursales | Margen global={seg['margen_pct_global']:.1f}%")
        if n_suc:
            print(f"OK ({n_suc} sucursales | Margen global: {seg['margen_pct_global']:.1f}%)")

        # Generar HTML
        print("\n  Generando HTML...", flush=True)
        generar_html({
            "eerr":   eerr,
            "flujo":  flujo,
            "ventas": ventas,
            "rrhh":   rrhh,
            "adm_op": adm_op,
            "no_op":  no_op,
            "mkt":    mkt,
            "seg":    seg,
        }, output_path)
        logger.info(f"📊 HTML generado: {output_path.name} ({output_path.stat().st_size/1e6:.1f}MB)")

        # Resumen final
        print(f"\n{'='*60}")
        print(f"  ✅ DASHBOARD GENERADO EXITOSAMENTE")
        print(f"{'='*60}")
        print(f"  Archivo: {output_path}")
        print(f"  Tamaño: {output_path.stat().st_size/1e6:.1f}MB")
        print(f"  Abre en cualquier navegador — sin login requerido")
        print(f"{'='*60}\n")
        logger.info(f"✅ Ejecución completada exitosamente")

    except FileNotFoundError as e:
        logger.error(f"❌ Error de archivo: {e}")
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error inesperado: {e}", exc_info=True)
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
    finally:
        # Información final de logs
        logger.info(f"📋 Log completo guardado en: {log_filename}")
        print(f"📋 Log guardado: {log_filename}\n")


if __name__ == "__main__":
    main()
