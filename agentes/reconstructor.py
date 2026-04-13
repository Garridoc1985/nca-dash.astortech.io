"""
Reconstructor — Agente 3 del pipeline Astor Tech
=================================================
Lee el Excel del cliente aplicando el mapa de columnas generado por el Mapper.
Devuelve DataFrames normalizados con los nombres de columna que el Generador espera.

Este agente es un módulo (importable) y también ejecutable directamente para debug.

USO como módulo:
    from agentes.reconstructor import reconstruir
    dfs = reconstruir("ruta.xlsx", "agentes/ultimo_mapa_columnas.json")
    # dfs["1 VENTA"] tiene columnas: Sucursal, Año, Mes, Importe

USO CLI:
    python agentes/reconstructor.py --file "ruta.xlsx"
    python agentes/reconstructor.py --file "ruta.xlsx" --mapa "agentes/ultimo_mapa_columnas.json"
"""

import json
from pathlib import Path
from typing import Any

import pandas as pd


# ─── Constantes ───────────────────────────────────────────────────────────────

SCHEMA_TIPOS = {
    "EERR":          "indice_fijo",
    "FLUJO":         "indice_fijo",
    "MARKETING":     "indice_fijo",
    "1 VENTA":       "columnas",
    "VENTAS DETALLE":"columnas",
    "2 RRHH":        "columnas",
    "3 GS ADMIN":    "columnas",
    "4 GS OP":       "columnas",
    "5 GS NO OP":    "columnas",
}


# ─── Lectura de hojas por índice fijo ─────────────────────────────────────────

def leer_hoja_indice_fijo(xl: pd.ExcelFile, hoja: str) -> pd.DataFrame:
    """
    Lee una hoja sin usar encabezados — devuelve el DataFrame crudo con índices numéricos.
    Usado para EERR, FLUJO, MARKETING donde el layout es posicional.
    """
    return pd.read_excel(xl, sheet_name=hoja, header=None)


# ─── Lectura de hojas por columnas con mapeo ──────────────────────────────────

def leer_hoja_columnas(xl: pd.ExcelFile, hoja: str,
                       mapa_hoja: dict | None) -> pd.DataFrame:
    """
    Lee una hoja con encabezados y aplica el mapa de columnas.
    mapa_hoja: dict {columna_esperada: {columna_real: ..., resolucion: ...}}
    Devuelve DataFrame con columnas renombradas al nombre esperado.
    """
    df = pd.read_excel(xl, sheet_name=hoja)

    if not mapa_hoja:
        return df

    # Construir dict de renombrado: real → esperado
    # Solo para columnas que son mapeos (resolucion != "directa" con columna_real != columna_esperada)
    rename_map = {}
    for col_esperada, info in mapa_hoja.items():
        col_real = info.get("columna_real")
        resolucion = info.get("resolucion", "directa")

        if col_real is None:
            # Columna ausente — no se puede mapear
            continue

        if col_real != col_esperada and resolucion in ("inferida", "directa"):
            # La columna existe en el Excel con otro nombre
            if col_real in df.columns:
                rename_map[col_real] = col_esperada

    if rename_map:
        df = df.rename(columns=rename_map)

    return df


# ─── Punto de entrada principal ───────────────────────────────────────────────

def reconstruir(
    ruta_excel: str,
    ruta_mapa: str = "agentes/ultimo_mapa_columnas.json",
    verbose: bool = False
) -> dict[str, Any]:
    """
    Lee el Excel aplicando el mapa de columnas del Mapper.

    Retorna:
        {
            "dfs": {
                "EERR": <DataFrame crudo por índice>,
                "1 VENTA": <DataFrame con columnas normalizadas>,
                ...
            },
            "advertencias": [...],
            "hojas_ignoradas": [...],
        }
    """
    resultado = {
        "dfs": {},
        "advertencias": [],
        "hojas_ignoradas": [],
    }

    # 1. Cargar mapa de columnas
    ruta_mapa_path = Path(ruta_mapa)
    if ruta_mapa_path.exists():
        with open(ruta_mapa_path, encoding="utf-8") as f:
            mapa = json.load(f)
        mapa_columnas = mapa.get("mapa_columnas", {})
    else:
        if verbose:
            print(f"  ⚠️  Mapa no encontrado en {ruta_mapa} — leyendo sin transformaciones")
        mapa_columnas = {}

    # 2. Abrir Excel
    xl = pd.ExcelFile(ruta_excel)
    hojas_disponibles = xl.sheet_names

    if verbose:
        print(f"  📂 Hojas en el Excel: {', '.join(hojas_disponibles)}")

    # 3. Leer cada hoja del schema
    for hoja, tipo in SCHEMA_TIPOS.items():
        if hoja not in hojas_disponibles:
            resultado["advertencias"].append(f"Hoja '{hoja}' no encontrada en el Excel")
            if verbose:
                print(f"  ❌ {hoja}: no encontrada")
            continue

        try:
            if tipo == "indice_fijo":
                df = leer_hoja_indice_fijo(xl, hoja)
                if verbose:
                    print(f"  ✅ {hoja}: leída por índice ({df.shape[0]}×{df.shape[1]})")

            else:  # columnas
                mapa_hoja = mapa_columnas.get(hoja, {})
                df = leer_hoja_columnas(xl, hoja, mapa_hoja)
                if verbose:
                    cols_preview = list(df.columns)[:6]
                    print(f"  ✅ {hoja}: {df.shape[0]} filas | cols: {cols_preview}")

            resultado["dfs"][hoja] = df

        except Exception as e:
            resultado["advertencias"].append(f"Error leyendo '{hoja}': {e}")
            if verbose:
                print(f"  ⚠️  {hoja}: error — {e}")

    # 4. Registrar hojas ignoradas (no son parte del schema)
    hojas_schema = set(SCHEMA_TIPOS.keys())
    resultado["hojas_ignoradas"] = [h for h in hojas_disponibles if h not in hojas_schema]

    return resultado


# ─── Validador ────────────────────────────────────────────────────────────────

def validar_dataframes(resultado: dict, verbose: bool = False) -> dict[str, list]:
    """
    Verifica que los DataFrames tengan las columnas esperadas.
    Retorna dict con problemas por hoja.
    """
    COLUMNAS_CRITICAS = {
        "1 VENTA":        ["Sucursal", "Año", "Mes", "Venta"],
        "VENTAS DETALLE": ["Fecha Venta", "Sucursal", "Tratamiento", "Venta", "Tipo Producto"],
        "2 RRHH":         ["Sucursal", "Año", "Mes", "Importe", "Tipo gasto"],
        "3 GS ADMIN":     ["Tipo de gasto", "Monto Bruto", "Año"],
        "4 GS OP":        ["Tipo de gasto", "Monto Bruto", "Año"],
        "5 GS NO OP":     ["Tipo de gasto", "Monto Bruto", "Proveedor", "Año"],
    }

    problemas = {}
    dfs = resultado.get("dfs", {})

    for hoja, cols_esperadas in COLUMNAS_CRITICAS.items():
        if hoja not in dfs:
            continue
        df = dfs[hoja]
        faltantes = [c for c in cols_esperadas if c not in df.columns]
        if faltantes:
            problemas[hoja] = faltantes
            if verbose:
                print(f"  ⚠️  {hoja}: columnas críticas faltantes: {faltantes}")
        elif verbose:
            print(f"  ✅ {hoja}: columnas críticas OK")

    return problemas


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstructor de datos — Astor Tech")
    parser.add_argument("--file", required=True, help="Ruta al archivo Excel")
    parser.add_argument(
        "--mapa",
        default="agentes/ultimo_mapa_columnas.json",
        help="Ruta al mapa de columnas del Mapper"
    )
    args = parser.parse_args()

    print(f"\n🔧 Reconstructor iniciando...")
    print("─" * 60)
    print(f"📄 Excel: {Path(args.file).name}")
    print(f"🗺️  Mapa:  {args.mapa}")
    print()

    resultado = reconstruir(args.file, args.mapa, verbose=True)

    print(f"\n🔍 Validando columnas críticas...")
    problemas = validar_dataframes(resultado, verbose=True)

    # Resumen
    dfs = resultado["dfs"]
    advertencias = resultado["advertencias"]
    ignoradas = resultado["hojas_ignoradas"]

    print(f"\n{'─'*60}")
    print(f"Hojas reconstruidas: {len(dfs)}/{len(SCHEMA_TIPOS)}")
    print(f"Hojas ignoradas:     {len(ignoradas)} ({', '.join(ignoradas[:5])}{'...' if len(ignoradas) > 5 else ''})")

    if advertencias:
        print(f"\nAdvertencias:")
        for a in advertencias:
            print(f"  ⚠️  {a}")

    if problemas:
        print(f"\nProblemas de columnas críticas:")
        for hoja, cols in problemas.items():
            print(f"  ❌ {hoja}: faltan {cols}")
        print(f"\nEstado: ⚠️  REQUIERE REVISIÓN")
    else:
        print(f"\nEstado: ✅ LISTO PARA GENERADOR")
