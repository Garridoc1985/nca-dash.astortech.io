"""
Generador — Agente 4 del pipeline Astor Tech
=============================================
Orquesta el pipeline completo:
    Inspector → Mapper → Reconstructor → generador_nca.py

Cuando el Excel del cliente tiene columnas renombradas, este agente
adapta los datos antes de pasarlos al motor de generación existente.

Estrategia de integración:
    1. Reconstructor normaliza los DataFrames (columnas corregidas)
    2. Se escribe un Excel temporal con los datos normalizados
    3. El Excel temporal se pasa al motor generador_nca.py existente
    4. El motor no sabe que hubo adaptación — ve el schema esperado

USO:
    python agentes/generador.py --file "ruta/al/archivo.xlsx"
    python agentes/generador.py --file "ruta.xlsx" --output "output/dashboard.html"
    python agentes/generador.py --file "ruta.xlsx" --skip-inspect  # usa reporte previo
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

# Agregar directorio actual y workspace al path para imports entre agentes
_THIS_DIR = str(Path(__file__).parent)
_WORKSPACE_PATH = str(Path(__file__).parent.parent.parent)
if _THIS_DIR not in sys.path:
    sys.path.insert(0, _THIS_DIR)
if _WORKSPACE_PATH not in sys.path:
    sys.path.insert(0, _WORKSPACE_PATH)


# ─── Rutas del workspace ─────────────────────────────────────────────────────

AGENTES_DIR   = Path(__file__).parent
WORKSPACE     = AGENTES_DIR.parent
GENERADOR_NCA = WORKSPACE / ".claude/skills/dashboard-financiero-nca/generador_nca.py"
OUTPUT_DIR    = WORKSPACE / "output"

# Hojas que se leen por índice fijo (no necesitan normalización de columnas)
HOJAS_INDICE_FIJO = {"EERR", "FLUJO", "MARKETING"}


# ─── Paso 1: Inspector ────────────────────────────────────────────────────────

def ejecutar_inspector(ruta_excel: str, skip: bool = False) -> dict:
    """Corre el Inspector si no hay reporte previo o si skip=False."""
    ruta_reporte = AGENTES_DIR / "ultimo_reporte_inspector.json"

    if skip and ruta_reporte.exists():
        print("  ⏩ Inspector: usando reporte previo")
        with open(ruta_reporte, encoding="utf-8") as f:
            return json.load(f)

    print("  🔍 Inspector: analizando estructura del Excel...")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(AGENTES_DIR / "inspector.py"),
         "--file", ruta_excel, "--json"],
        capture_output=True, text=True, encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(f"Inspector falló:\n{result.stderr}")

    with open(ruta_reporte, encoding="utf-8") as f:
        return json.load(f)


# ─── Paso 2: Mapper ───────────────────────────────────────────────────────────

def ejecutar_mapper(reporte: dict, skip: bool = False) -> dict:
    """Corre el Mapper si hay problemas de columnas."""
    ruta_mapa = AGENTES_DIR / "ultimo_mapa_columnas.json"

    # ¿Hay algo que mapear?
    problemas = reporte.get("reporte", {}).get("problemas_columnas", [])

    if not problemas:
        print("  ✅ Mapper: sin diferencias de columnas — salteando")
        # Crear mapa vacío
        mapa = {
            "version": "1.0",
            "mapa_columnas": {},
            "columnas_ausentes": [],
            "hojas_sin_cambios": reporte.get("reporte", {}).get("hojas_ok", []),
            "resumen": {"listo_para_pipeline": True}
        }
        ruta_mapa.write_text(json.dumps(mapa, ensure_ascii=False, indent=2), encoding="utf-8")
        return mapa

    if skip and ruta_mapa.exists():
        print("  ⏩ Mapper: usando mapa previo")
        with open(ruta_mapa, encoding="utf-8") as f:
            return json.load(f)

    print(f"  🗺️  Mapper: generando mapa para {len(problemas)} hojas con diferencias...")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(AGENTES_DIR / "mapper.py"),
         "--reporte", str(AGENTES_DIR / "ultimo_reporte_inspector.json")],
        capture_output=True, text=True, encoding="utf-8"
    )

    if result.returncode != 0:
        raise RuntimeError(f"Mapper falló:\n{result.stderr}")

    with open(ruta_mapa, encoding="utf-8") as f:
        return json.load(f)


# ─── Paso 3: Reconstructor ───────────────────────────────────────────────────

def ejecutar_reconstructor(ruta_excel: str, mapa: dict) -> dict:
    """Importa y ejecuta el Reconstructor para obtener DataFrames normalizados."""
    from reconstructor import reconstruir, validar_dataframes

    print("  🔧 Reconstructor: normalizando DataFrames...")
    resultado = reconstruir(
        ruta_excel,
        ruta_mapa=str(AGENTES_DIR / "ultimo_mapa_columnas.json"),
        verbose=False
    )

    problemas = validar_dataframes(resultado)
    if problemas:
        print(f"  ⚠️  Columnas críticas faltantes tras normalización:")
        for hoja, cols in problemas.items():
            print(f"     {hoja}: {cols}")
        # No bloqueamos — puede que el generador tolere los faltantes

    dfs_ok = len(resultado["dfs"])
    print(f"  ✅ Reconstructor: {dfs_ok} hojas normalizadas")
    return resultado


# ─── Paso 4: Excel temporal ──────────────────────────────────────────────────

def crear_excel_temporal(ruta_excel_original: str, dfs_normalizados: dict) -> Path:
    """
    Crea un Excel temporal que mezcla:
    - Hojas de índice fijo: copiadas tal cual del original
    - Hojas de columnas: reemplazadas por los DataFrames normalizados

    El resultado es un Excel que el motor generador_nca.py puede leer
    sin saber que hubo transformaciones.
    """
    ruta_original = Path(ruta_excel_original)
    xl_original = pd.ExcelFile(ruta_original)

    # Directorio temporal
    tmp_dir = Path(tempfile.mkdtemp())
    ruta_temp = tmp_dir / f"nca_normalizado_{ruta_original.stem}.xlsx"

    with pd.ExcelWriter(ruta_temp, engine="openpyxl") as writer:
        for hoja in xl_original.sheet_names:
            if hoja in HOJAS_INDICE_FIJO:
                # Copiar sin encabezados (índice fijo — se lee posicionalmente)
                df_raw = pd.read_excel(xl_original, sheet_name=hoja, header=None)
                df_raw.to_excel(writer, sheet_name=hoja, index=False, header=False)

            elif hoja in dfs_normalizados:
                # Usar DataFrame normalizado (columnas ya corregidas)
                df = dfs_normalizados[hoja]
                df.to_excel(writer, sheet_name=hoja, index=False)

            else:
                # Hoja auxiliar (PRESUPUESTO, KPIs, etc.) — copiar tal cual
                try:
                    df_raw = pd.read_excel(xl_original, sheet_name=hoja, header=None)
                    df_raw.to_excel(writer, sheet_name=hoja, index=False, header=False)
                except Exception:
                    pass  # Ignorar hojas que fallen

    return ruta_temp


# ─── Paso 5: Llamar al generador NCA ─────────────────────────────────────────

def llamar_generador_nca(ruta_excel_temp: Path, ruta_output: Path) -> bool:
    """Llama al motor generador_nca.py con el Excel normalizado."""
    ruta_output.parent.mkdir(parents=True, exist_ok=True)

    print(f"  📊 Generador NCA: construyendo dashboard HTML...")
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(GENERADOR_NCA),
         "--file", str(ruta_excel_temp),
         "--output", str(ruta_output)],
        capture_output=False,  # Mostrar output en tiempo real
        text=True,
        encoding="utf-8"
    )

    return result.returncode == 0


# ─── Pipeline completo ────────────────────────────────────────────────────────

def generar(ruta_excel: str,
            ruta_output: str | None = None,
            skip_inspect: bool = False) -> Path | None:
    """
    Ejecuta el pipeline completo: Inspector → Mapper → Reconstructor → Generador.

    Args:
        ruta_excel:    Ruta al Excel del cliente (puede tener columnas renombradas)
        ruta_output:   Ruta HTML de salida (opcional — usa output/ por defecto)
        skip_inspect:  Reusar reportes previos del Inspector y Mapper

    Returns:
        Path al HTML generado, o None si falló
    """
    ruta_excel = str(Path(ruta_excel).resolve())
    nombre_base = Path(ruta_excel).stem

    if ruta_output is None:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        ruta_output_path = OUTPUT_DIR / f"dashboard_{nombre_base}.html"
    else:
        ruta_output_path = Path(ruta_output)

    ruta_temp = None

    try:
        print(f"\n{'='*62}")
        print(f"  PIPELINE ASTOR TECH")
        print(f"{'='*62}")
        print(f"  Excel: {Path(ruta_excel).name}\n")

        # Paso 1: Inspector
        reporte = ejecutar_inspector(ruta_excel, skip=skip_inspect)
        estado_inspector = reporte.get("estado", "?")
        print(f"  Estado Inspector: {estado_inspector}\n")

        # Paso 2: Mapper
        mapa = ejecutar_mapper(reporte, skip=skip_inspect)
        listo = mapa.get("resumen", {}).get("listo_para_pipeline", True)

        # Paso 3: Reconstructor
        resultado_rec = ejecutar_reconstructor(ruta_excel, mapa)
        dfs = resultado_rec["dfs"]
        advertencias = resultado_rec.get("advertencias", [])

        if advertencias:
            print(f"\n  Advertencias del Reconstructor:")
            for a in advertencias:
                print(f"    ⚠️  {a}")

        # Paso 4: Excel temporal (solo si hubo remapeo de columnas)
        hay_remapeo = bool(mapa.get("mapa_columnas"))
        if hay_remapeo:
            print(f"\n  📝 Creando Excel temporal con columnas normalizadas...")
            ruta_temp = crear_excel_temporal(ruta_excel, dfs)
            print(f"  ✅ Excel temporal: {ruta_temp.name}")
            excel_para_generar = str(ruta_temp)
        else:
            print(f"\n  ⏩ Sin remapeo necesario — usando Excel original")
            excel_para_generar = ruta_excel

        # Paso 5: Generador NCA
        print()
        exito = llamar_generador_nca(Path(excel_para_generar), ruta_output_path)

        if exito:
            size_mb = ruta_output_path.stat().st_size / 1e6
            print(f"\n{'='*62}")
            print(f"  ✅ PIPELINE COMPLETADO")
            print(f"{'='*62}")
            print(f"  Dashboard: {ruta_output_path}")
            print(f"  Tamaño:    {size_mb:.1f} MB")
            print(f"{'='*62}\n")
            return ruta_output_path
        else:
            print(f"\n  ❌ El generador NCA falló — revisar logs en logs/")
            return None

    finally:
        # Limpiar Excel temporal
        if ruta_temp and ruta_temp.parent.exists():
            try:
                shutil.rmtree(ruta_temp.parent)
            except Exception:
                pass


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Pipeline Astor Tech — Inspector→Mapper→Reconstructor→Generador"
    )
    parser.add_argument("--file",         required=True, help="Ruta al Excel del cliente")
    parser.add_argument("--output",       default=None,  help="Ruta HTML de salida")
    parser.add_argument("--skip-inspect", action="store_true",
                        help="Reusar reporte Inspector y mapa Mapper previos")
    args = parser.parse_args()

    resultado = generar(
        ruta_excel=args.file,
        ruta_output=args.output,
        skip_inspect=args.skip_inspect,
    )

    if resultado is None:
        sys.exit(1)
