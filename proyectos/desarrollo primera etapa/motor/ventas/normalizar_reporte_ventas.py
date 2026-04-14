"""
Normalizar Reporte de Ventas + Generar Dashboard
=================================================
Normaliza un Excel mensual de ventas (formato "Reporte de Ventas"),
elimina duplicados por hash MD5 y genera un dashboard HTML interactivo.

USO:
    python normalizar_reporte_ventas.py --file "Reporte de ventas 2025.xlsx"
    python normalizar_reporte_ventas.py --file "Sales Feb.xlsx" --sheet "Sales" --output output/dashboard.html

COLUMNAS REQUERIDAS EN EL EXCEL:
    fecha, mes, id_del_cliente, cliente, no_de_venta, nombre_del_articulo,
    notas_de_venta, localidad, notas, color, tamano,
    precio_del_articulo_excluyendo_impuestos, cantidad,
    sub_total_excluyendo_impuestos, descuento_en, cantidad_de_descuento,
    impuesto, total_de_articulos, total_pagado_con_metodo_de_pago, forma_de_pago
"""

import argparse
import hashlib
import html
import re
import sys
import unicodedata
from pathlib import Path

import pandas as pd

# Paths relativos a este script
SKILL_DIR   = Path(__file__).parent.parent
DASHBOARD_SKILL = SKILL_DIR.parent / "dashboard-financiero-nca"
WORKSPACE   = SKILL_DIR.parent.parent

sys.path.insert(0, str(SKILL_DIR / "scripts"))
sys.path.insert(0, str(DASHBOARD_SKILL))

EXPECTED_COLS = [
    "fecha",
    "mes",
    "id_del_cliente",
    "cliente",
    "no_de_venta",
    "nombre_del_articulo",
    "notas_de_venta",
    "localidad",
    "notas",
    "color",
    "tamano",
    "precio_del_articulo_excluyendo_impuestos",
    "cantidad",
    "sub_total_excluyendo_impuestos",
    "descuento_en",
    "cantidad_de_descuento",
    "impuesto",
    "total_de_articulos",
    "total_pagado_con_metodo_de_pago",
    "forma_de_pago",
]


# -----------------------------------------------------------------------
# Utilidades de normalización
# -----------------------------------------------------------------------

def to_snake(text: str) -> str:
    value = str(text).strip().lower()
    value = "".join(ch for ch in unicodedata.normalize("NFD", value) if unicodedata.category(ch) != "Mn")
    value = value.replace("%", "")
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return re.sub(r"_+", "_", value).strip("_")


def normalize_text(value):
    if pd.isna(value):
        return None
    text = html.unescape(str(value)).strip()
    text = re.sub(r"\s+", " ", text)
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = text.upper()
    return text if text else None


def normalize_id(value):
    if pd.isna(value):
        return None
    text = html.unescape(str(value)).strip()
    text = "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^0-9A-Za-z]+", "", text).upper()
    return text if text else None


def canon(value):
    if value is None:
        return "~"
    if isinstance(value, float) and pd.isna(value):
        return "~"
    return str(value)


# -----------------------------------------------------------------------
# Normalización del DataFrame
# -----------------------------------------------------------------------

def normalize_dataframe(df: pd.DataFrame, source_name: str) -> tuple:
    """
    Normaliza columnas, tipos y textos. Deduplica por hash MD5.
    Retorna (df_normalizado, df_duplicados).
    """
    df = df.copy()
    df.columns = [to_snake(c) for c in df.columns]

    missing = [c for c in EXPECTED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas esperadas: {missing}")

    df = df[EXPECTED_COLS]

    text_cols = [
        "mes", "cliente", "nombre_del_articulo", "notas_de_venta",
        "localidad", "notas", "color", "tamano", "forma_de_pago",
    ]
    for col in text_cols:
        df[col] = df[col].map(normalize_text)

    df["id_del_cliente"] = df["id_del_cliente"].map(normalize_id)

    parsed_date = pd.to_datetime(df["fecha"], errors="coerce", dayfirst=True)
    df["fecha"]         = parsed_date.dt.date
    df["periodo_carga"] = parsed_date.dt.strftime("%Y-%m")
    df["archivo_origen"] = source_name

    df["no_de_venta"] = pd.to_numeric(df["no_de_venta"], errors="coerce").round().astype("Int64")
    df["cantidad"]    = pd.to_numeric(df["cantidad"],    errors="coerce").round().astype("Int64")

    numeric_cols = [
        "precio_del_articulo_excluyendo_impuestos",
        "sub_total_excluyendo_impuestos",
        "descuento_en",
        "cantidad_de_descuento",
        "impuesto",
        "total_de_articulos",
        "total_pagado_con_metodo_de_pago",
    ]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Hash MD5 por fila para detectar duplicados
    payload = df[EXPECTED_COLS].astype(object).where(pd.notna(df[EXPECTED_COLS]), None)
    hashes = []
    for _, row in payload.iterrows():
        digest_input = "|".join(canon(row[c]) for c in EXPECTED_COLS)
        hashes.append(hashlib.md5(digest_input.encode("utf-8")).digest())
    df["row_hash"] = hashes

    df_dupes = df[df.duplicated(subset=["row_hash"], keep="first")].copy()
    df = df.drop_duplicates(subset=["row_hash"])

    if len(df_dupes):
        print(f"  Duplicados eliminados: {len(df_dupes):,} fila(s)")

    ordered = [
        "periodo_carga", "fecha", "mes", "id_del_cliente", "cliente",
        "no_de_venta", "nombre_del_articulo", "notas_de_venta", "localidad",
        "notas", "color", "tamano",
        "precio_del_articulo_excluyendo_impuestos", "cantidad",
        "sub_total_excluyendo_impuestos", "descuento_en", "cantidad_de_descuento",
        "impuesto", "total_de_articulos", "total_pagado_con_metodo_de_pago",
        "forma_de_pago", "archivo_origen", "row_hash",
    ]
    return df[ordered], df_dupes[ordered]


# -----------------------------------------------------------------------
# Generación del dashboard desde el DataFrame normalizado
# -----------------------------------------------------------------------

def generar_dashboard(df_norm: pd.DataFrame, file_path: Path, output_path: Path,
                      usuario: str, password: str, titulo: str):
    """Convierte df normalizado → dashboard HTML de ventas (jefa de sucursal)."""
    from generador_html_ventas import GeneradorDashboardVentas

    print(f"  [Ventas] {len(df_norm):,} filas → generando dashboard...")
    gen = GeneradorDashboardVentas(
        df_norm,
        usuario=usuario,
        password=password,
        titulo=titulo,
    )
    gen.generar_html(output_path)


# -----------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Normaliza Excel de ventas, elimina duplicados y genera dashboard HTML.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--file",               required=True,   help="Ruta al Excel de ventas")
    parser.add_argument("--sheet",              default=None,    help="Nombre de hoja (default: primera)")
    parser.add_argument("--output",             default=None,    help="Ruta HTML del dashboard (default: output/dashboard_<nombre>.html)")
    parser.add_argument("--output-normalized",  default=None,    help="Ruta para guardar Excel normalizado (opcional)")
    parser.add_argument("--output-duplicates",  default=None,    help="Ruta para guardar duplicados (default: junto al archivo de entrada)")
    parser.add_argument("--usuario",            default="admin", help="Usuario login dashboard (default: admin)")
    parser.add_argument("--password",           default="nca2026", help="Password login dashboard (default: nca2026)")
    parser.add_argument("--titulo",             default=None,    help="Titulo del dashboard")
    parser.add_argument("--sin-dashboard",      action="store_true", help="Solo normaliza, sin generar dashboard")
    args = parser.parse_args()

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Error: archivo no encontrado: {file_path}")
        sys.exit(1)

    titulo = args.titulo or file_path.stem.replace("_", " ").replace("-", " ").title()

    print(f"\n{'='*60}")
    print(f"  NORMALIZAR REPORTE DE VENTAS")
    print(f"{'='*60}")
    print(f"  Archivo: {file_path.name}")

    # ---- Leer ----
    xls = pd.ExcelFile(file_path)
    sheet_name = args.sheet if args.sheet else xls.sheet_names[0]
    print(f"  Hoja: {sheet_name}")
    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, engine="openpyxl")
    print(f"  {len(df_raw):,} filas cargadas.")

    # ---- Normalizar ----
    df_norm, df_dupes = normalize_dataframe(df_raw, file_path.name)
    print(f"  {len(df_norm):,} filas normalizadas.")

    # ---- Exportar duplicados ----
    out_dupes = (
        Path(args.output_duplicates) if args.output_duplicates
        else file_path.parent / f"duplicados_{file_path.stem}.xlsx"
    )
    out_dupes.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_dupes, engine="openpyxl") as writer:
        df_dupes.to_excel(writer, sheet_name="Duplicados", index=False)
    if len(df_dupes):
        print(f"  Duplicados exportados: {out_dupes} ({len(df_dupes):,} fila(s))")
    else:
        print(f"  Sin duplicados.")

    # ---- Exportar normalizado (opcional) ----
    if args.output_normalized:
        out_norm = Path(args.output_normalized)
        out_norm.parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(out_norm, engine="openpyxl") as writer:
            df_norm.to_excel(writer, sheet_name="Sales", index=False)
        print(f"  Normalizado exportado: {out_norm}")

    periods = sorted(df_norm["periodo_carga"].dropna().unique().tolist())
    print(f"  Periodos: {periods}")

    if args.sin_dashboard:
        print(f"\n{'='*60}")
        print(f"  NORMALIZADO (sin dashboard)")
        print(f"{'='*60}\n")
        return

    # ---- Generar dashboard ----
    if args.output:
        output_path = Path(args.output)
    else:
        output_dir = WORKSPACE / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        nombre_limpio = file_path.stem.lower().replace(" ", "_").replace("-", "_")
        output_path = output_dir / f"dashboard_{nombre_limpio}.html"

    print(f"\n  Generando dashboard HTML...")
    generar_dashboard(df_norm, file_path, output_path, args.usuario, args.password, titulo)

    print(f"\n{'='*60}")
    print(f"  COMPLETADO")
    print(f"{'='*60}")
    print(f"  Dashboard: {output_path}")
    print(f"  Usuario:   {args.usuario}")
    print(f"  Password:  {args.password}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
