"""
Inspector — Agente 1 del pipeline Astor Tech
=============================================
Analiza la estructura del Excel entrante y detecta si coincide
con el schema esperado. Si hay diferencias (columnas renombradas,
hojas nuevas, orden cambiado), las reporta para que Mapper las resuelva.

USO:
    python agentes/inspector.py --file "ruta/al/archivo.xlsx"
"""

import json
import sys
from pathlib import Path
from typing import Any

import anthropic
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ─── Schema esperado NCA ──────────────────────────────────────────────────────
# Define las hojas y columnas críticas que el generador necesita.
# Si el Excel del cliente cambia, el Inspector lo detecta aquí.

SCHEMA_ESPERADO = {
    "EERR": {
        "descripcion": "Estado de Resultados — lectura por índice fijo (filas/cols numéricas)",
        "tipo": "indice_fijo",
        "filas_minimas": 10,
    },
    "FLUJO": {
        "descripcion": "Flujo de Caja proyectado — lectura por índice fijo",
        "tipo": "indice_fijo",
        "filas_minimas": 5,
    },
    "1 VENTA": {
        "descripcion": "Ventas consolidadas por sucursal y año",
        "tipo": "columnas",
        "columnas_criticas": ["Sucursal", "Año", "Mes", "Venta"],
        "filas_minimas": 50,
    },
    "VENTAS DETALLE": {
        "descripcion": "Detalle de transacciones de venta",
        "tipo": "columnas",
        "columnas_criticas": ["Fecha Venta", "Sucursal", "Tratamiento", "Venta", "Tipo Producto"],
        "filas_minimas": 100,
    },
    "2 RRHH": {
        "descripcion": "Gastos de personal por sucursal y período",
        "tipo": "columnas",
        "columnas_criticas": ["Sucursal", "Año", "Mes", "Importe", "Tipo gasto"],
        "filas_minimas": 10,
    },
    "3 GS ADMIN": {
        "descripcion": "Gastos administrativos",
        "tipo": "columnas",
        "columnas_criticas": ["Tipo de gasto", "Monto Bruto", "Año"],
        "filas_minimas": 3,
    },
    "4 GS OP": {
        "descripcion": "Gastos operativos",
        "tipo": "columnas",
        "columnas_criticas": ["Tipo de gasto", "Monto Bruto", "Año"],
        "filas_minimas": 3,
    },
    "5 GS NO OP": {
        "descripcion": "Gastos no operacionales",
        "tipo": "columnas",
        "columnas_criticas": ["Tipo de gasto", "Monto Bruto", "Proveedor", "Año"],
        "filas_minimas": 3,
    },
    "MARKETING": {
        "descripcion": "Gastos de marketing — lectura por índice fijo",
        "tipo": "indice_fijo",
        "filas_minimas": 3,
    },
}


# ─── Extractor de estructura ──────────────────────────────────────────────────

def extraer_estructura(ruta_excel: str) -> dict[str, Any]:
    """Lee el Excel y extrae su estructura real sin procesar datos."""
    xl = pd.ExcelFile(ruta_excel)
    estructura = {
        "hojas_encontradas": xl.sheet_names,
        "hojas": {}
    }

    for hoja in xl.sheet_names:
        try:
            # Leer primeras 5 filas para inferir estructura
            df_head = pd.read_excel(xl, sheet_name=hoja, nrows=5, header=None)
            df_cols = pd.read_excel(xl, sheet_name=hoja, nrows=1)
            df_full = pd.read_excel(xl, sheet_name=hoja, header=None)

            estructura["hojas"][hoja] = {
                "filas_totales": len(df_full),
                "columnas_totales": len(df_full.columns),
                "primera_fila_valores": df_head.iloc[0].dropna().tolist()[:10],
                "columnas_inferidas": [str(c) for c in df_cols.columns.tolist()[:15]],
                "muestra_celda_a1": str(df_full.iloc[0, 0]) if not df_full.empty else "vacío",
            }
        except Exception as e:
            estructura["hojas"][hoja] = {"error": str(e)}

    return estructura


# ─── Comparador con schema esperado ──────────────────────────────────────────

def comparar_con_schema(estructura_real: dict) -> dict[str, Any]:
    """Compara estructura real vs schema esperado sin IA."""
    hojas_reales = set(estructura_real["hojas_encontradas"])
    hojas_esperadas = set(SCHEMA_ESPERADO.keys())

    reporte = {
        "hojas_ok": [],
        "hojas_faltantes": [],
        "hojas_nuevas": [],
        "problemas_columnas": [],
        "hojas_con_pocas_filas": [],
    }

    # Hojas faltantes y nuevas
    reporte["hojas_faltantes"] = list(hojas_esperadas - hojas_reales)
    reporte["hojas_nuevas"] = list(hojas_reales - hojas_esperadas)

    # Verificar hojas presentes
    for hoja, schema in SCHEMA_ESPERADO.items():
        if hoja not in hojas_reales:
            continue

        info = estructura_real["hojas"].get(hoja, {})
        if "error" in info:
            continue

        # Verificar filas mínimas
        if info.get("filas_totales", 0) < schema.get("filas_minimas", 0):
            reporte["hojas_con_pocas_filas"].append({
                "hoja": hoja,
                "filas_encontradas": info.get("filas_totales"),
                "filas_esperadas_minimo": schema["filas_minimas"],
            })

        # Verificar columnas críticas (solo hojas tipo "columnas")
        if schema["tipo"] == "columnas":
            cols_reales = set(info.get("columnas_inferidas", []))
            cols_criticas = set(schema.get("columnas_criticas", []))
            faltantes = cols_criticas - cols_reales
            if faltantes:
                reporte["problemas_columnas"].append({
                    "hoja": hoja,
                    "columnas_faltantes": list(faltantes),
                    "columnas_encontradas": list(cols_reales)[:10],
                })
            else:
                reporte["hojas_ok"].append(hoja)
        else:
            reporte["hojas_ok"].append(hoja)

    return reporte


# ─── Análisis con Claude ──────────────────────────────────────────────────────

def analizar_con_claude(estructura_real: dict, reporte_basico: dict) -> str:
    """Usa Claude para interpretar diferencias y sugerir mapeos."""

    # Solo llamar a Claude si hay problemas reales
    hay_problemas = (
        reporte_basico["hojas_faltantes"]
        or reporte_basico["problemas_columnas"]
        or reporte_basico["hojas_con_pocas_filas"]
    )

    if not hay_problemas:
        return "✅ Estructura compatible con el schema esperado. No se requiere intervención."

    client = anthropic.Anthropic()

    prompt = f"""Eres un experto en ETL de datos financieros. Analiza las diferencias entre el
schema esperado y la estructura real de un archivo Excel de una clínica estética.

SCHEMA ESPERADO:
{json.dumps(SCHEMA_ESPERADO, ensure_ascii=False, indent=2)}

ESTRUCTURA REAL DEL ARCHIVO:
{json.dumps(estructura_real, ensure_ascii=False, indent=2)}

PROBLEMAS DETECTADOS:
{json.dumps(reporte_basico, ensure_ascii=False, indent=2)}

Tu tarea:
1. Para cada columna faltante, sugiere cuál columna real podría ser su equivalente (si existe)
2. Para cada hoja faltante, indica si hay alguna hoja con nombre similar
3. Evalúa si los problemas son críticos (bloquean el pipeline) o menores (se pueden ignorar)
4. Da una recomendación concisa de acción para el agente Mapper

Responde en español, de forma estructurada y concisa."""

    mensaje = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return mensaje.content[0].text


# ─── Main ─────────────────────────────────────────────────────────────────────

def inspeccionar(ruta_excel: str) -> dict[str, Any]:
    """Punto de entrada principal del Inspector."""
    print(f"\n🔍 Inspector iniciando análisis: {Path(ruta_excel).name}")
    print("─" * 60)

    # 1. Extraer estructura real
    print("📊 Extrayendo estructura del Excel...")
    estructura_real = extraer_estructura(ruta_excel)
    hojas = estructura_real["hojas_encontradas"]
    print(f"   Hojas encontradas ({len(hojas)}): {', '.join(hojas)}")

    # 2. Comparar con schema
    print("\n🔎 Comparando con schema esperado...")
    reporte = comparar_con_schema(estructura_real)

    if reporte["hojas_ok"]:
        print(f"   ✅ OK: {', '.join(reporte['hojas_ok'])}")
    if reporte["hojas_faltantes"]:
        print(f"   ❌ Faltantes: {', '.join(reporte['hojas_faltantes'])}")
    if reporte["hojas_nuevas"]:
        print(f"   🆕 Nuevas (no esperadas): {', '.join(reporte['hojas_nuevas'])}")
    if reporte["problemas_columnas"]:
        for p in reporte["problemas_columnas"]:
            print(f"   ⚠️  {p['hoja']}: faltan columnas {p['columnas_faltantes']}")

    # 3. Análisis Claude (solo si hay problemas)
    print("\n🤖 Consultando Claude para análisis semántico...")
    analisis_claude = analizar_con_claude(estructura_real, reporte)
    print(f"\n{analisis_claude}")

    # 4. Resultado final
    resultado = {
        "archivo": str(ruta_excel),
        "hojas_encontradas": hojas,
        "reporte": reporte,
        "analisis_claude": analisis_claude,
        "estado": "OK" if not (reporte["hojas_faltantes"] or reporte["problemas_columnas"]) else "REVISAR",
    }

    print(f"\n{'─'*60}")
    print(f"Estado final: {'✅ LISTO PARA PROCESAR' if resultado['estado'] == 'OK' else '⚠️  REQUIERE REVISIÓN'}")

    return resultado


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inspector de estructura Excel — Astor Tech")
    parser.add_argument("--file", required=True, help="Ruta al archivo Excel")
    parser.add_argument("--json", action="store_true", help="Exportar resultado como JSON")
    args = parser.parse_args()

    resultado = inspeccionar(args.file)

    if args.json:
        output_path = Path("agentes/ultimo_reporte_inspector.json")
        output_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n📄 Reporte guardado en: {output_path}")
