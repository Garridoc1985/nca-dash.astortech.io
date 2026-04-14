"""
Mapper — Agente 2 del pipeline Astor Tech
==========================================
Lee el reporte del Inspector y produce un diccionario de traducción
de columnas: nombre real en el Excel → nombre esperado en el schema.

Ese mapa es la "Rosetta Stone" del pipeline: los agentes siguientes
(Reconstructor, Generador) lo usan para leer el Excel correctamente
aunque las columnas hayan cambiado de nombre.

USO:
    python agentes/mapper.py
    python agentes/mapper.py --reporte "agentes/ultimo_reporte_inspector.json"
    python agentes/mapper.py --reporte "agentes/ultimo_reporte_inspector.json" --verbose
"""

import json
import sys
from pathlib import Path
from typing import Any

import anthropic
from dotenv import load_dotenv

load_dotenv()

# ─── Tipos de resolución ──────────────────────────────────────────────────────

RESOLUCION_DIRECTA = "directa"   # Mapeo claro, alta confianza
RESOLUCION_INFERIDA = "inferida" # Mapeo probable, requiere validación
RESOLUCION_AUSENTE = "ausente"   # Columna no existe en el Excel
RESOLUCION_IGNORAR = "ignorar"   # Diferencia no crítica para el pipeline


# ─── Construcción del prompt ──────────────────────────────────────────────────

def construir_prompt(reporte: dict) -> str:
    """Construye el prompt para Claude con el contexto del inspector."""

    problemas = reporte.get("reporte", {}).get("problemas_columnas", [])
    hojas_nuevas = reporte.get("reporte", {}).get("hojas_nuevas", [])
    analisis_previo = reporte.get("analisis_claude", "")

    return f"""Eres un experto en ETL financiero. Tu tarea es producir un mapa de columnas
para adaptar un archivo Excel real al schema esperado de un pipeline de datos.

## CONTEXTO DEL PIPELINE

El generador de dashboards espera columnas con nombres específicos por hoja.
Cuando el cliente entrega un Excel con nombres distintos, el pipeline falla.
Tu misión es construir el mapa de traducción: nombre_real → nombre_esperado.

## PROBLEMAS DETECTADOS POR EL INSPECTOR

```json
{json.dumps(problemas, ensure_ascii=False, indent=2)}
```

## ANÁLISIS PREVIO DEL INSPECTOR

{analisis_previo[:2000] if analisis_previo else "No disponible."}

## INSTRUCCIONES

Produce un JSON con esta estructura exacta:

```json
{{
  "version": "1.0",
  "mapa_columnas": {{
    "NOMBRE_HOJA": {{
      "columna_esperada_1": {{
        "columna_real": "nombre exacto en el Excel o null",
        "resolucion": "directa | inferida | ausente",
        "confianza": "alta | media | baja",
        "nota": "explicación breve"
      }}
    }}
  }},
  "columnas_ausentes": [
    {{
      "hoja": "nombre hoja",
      "columna": "nombre esperado",
      "impacto": "critico | mayor | menor",
      "alternativa": "descripción de qué hacer si no existe"
    }}
  ],
  "resumen": {{
    "mapeos_directos": 0,
    "mapeos_inferidos": 0,
    "columnas_ausentes": 0,
    "listo_para_pipeline": true
  }}
}}
```

## REGLAS

1. Usa los nombres EXACTOS como aparecen en "columnas_encontradas" del reporte
2. Si una columna ausente es crítica (bloquea el pipeline), márcala en "columnas_ausentes"
3. "listo_para_pipeline" = true solo si todas las columnas críticas tienen mapeo
4. Responde ÚNICAMENTE con el JSON, sin texto previo ni posterior

## HOJAS CON DIFERENCIAS A MAPEAR

Cubre estas hojas y solo estas: {[p['hoja'] for p in problemas]}"""


# ─── Llamada a Claude ─────────────────────────────────────────────────────────

def generar_mapa_con_claude(reporte: dict, verbose: bool = False) -> dict:
    """Usa Claude para generar el mapa de columnas."""
    client = anthropic.Anthropic()

    prompt = construir_prompt(reporte)

    if verbose:
        print("\n📤 Enviando prompt a Claude Haiku...")

    mensaje = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        messages=[{"role": "user", "content": prompt}]
    )

    respuesta_raw = mensaje.content[0].text.strip()

    if verbose:
        print(f"\n📥 Respuesta de Claude ({len(respuesta_raw)} chars):")
        print(respuesta_raw[:500] + ("..." if len(respuesta_raw) > 500 else ""))

    # Limpiar posibles bloques markdown
    if respuesta_raw.startswith("```"):
        lines = respuesta_raw.split("\n")
        # Remover primera y última línea si son ```json / ```
        respuesta_raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        mapa = json.loads(respuesta_raw)
        return mapa
    except json.JSONDecodeError as e:
        print(f"\n⚠️  Claude no devolvió JSON válido: {e}")
        print("Respuesta recibida:")
        print(respuesta_raw)
        # Retornar estructura vacía con error
        return {
            "version": "1.0",
            "error": "Claude no devolvió JSON válido",
            "respuesta_raw": respuesta_raw,
            "mapa_columnas": {},
            "columnas_ausentes": [],
            "resumen": {
                "mapeos_directos": 0,
                "mapeos_inferidos": 0,
                "columnas_ausentes": 0,
                "listo_para_pipeline": False,
            }
        }


# ─── Enriquecer con metadatos ─────────────────────────────────────────────────

def enriquecer_mapa(mapa_claude: dict, reporte_inspector: dict) -> dict:
    """Agrega metadatos del inspector al mapa generado."""
    mapa_claude["archivo_origen"] = reporte_inspector.get("archivo", "desconocido")
    mapa_claude["hojas_nuevas_ignoradas"] = reporte_inspector.get("reporte", {}).get("hojas_nuevas", [])

    # Agregar hojas_ok al mapa (columnas ya correctas — no necesitan traducción)
    hojas_ok = reporte_inspector.get("reporte", {}).get("hojas_ok", [])
    mapa_claude["hojas_sin_cambios"] = hojas_ok

    return mapa_claude


# ─── Renderizar resumen legible ───────────────────────────────────────────────

def imprimir_resumen(mapa: dict) -> None:
    """Muestra el mapa de forma legible en consola."""
    print("\n📋 MAPA DE COLUMNAS GENERADO")
    print("─" * 60)

    mapa_cols = mapa.get("mapa_columnas", {})

    for hoja, columnas in mapa_cols.items():
        print(f"\n📂 {hoja}")
        for col_esperada, info in columnas.items():
            col_real = info.get("columna_real")
            resolucion = info.get("resolucion", "?")
            confianza = info.get("confianza", "?")

            if resolucion == RESOLUCION_AUSENTE:
                icono = "❌"
                desc = "NO ENCONTRADA"
            elif resolucion == RESOLUCION_DIRECTA:
                icono = "✅"
                desc = f'"{col_real}"'
            elif resolucion == RESOLUCION_INFERIDA:
                icono = "🟡"
                desc = f'"{col_real}" (inferido)'
            else:
                icono = "⚪"
                desc = str(col_real)

            print(f"   {icono} {col_esperada:20} → {desc}")
            if info.get("nota"):
                print(f"      └─ {info['nota']}")

    # Columnas ausentes
    ausentes = mapa.get("columnas_ausentes", [])
    if ausentes:
        print("\n⚠️  COLUMNAS AUSENTES EN EL EXCEL:")
        for item in ausentes:
            icono = "🔴" if item.get("impacto") == "critico" else "🟠"
            print(f"   {icono} [{item['hoja']}] {item['columna']} — {item.get('impacto', '?').upper()}")
            if item.get("alternativa"):
                print(f"      └─ {item['alternativa']}")

    # Hojas sin cambios
    sin_cambios = mapa.get("hojas_sin_cambios", [])
    if sin_cambios:
        print(f"\n✅ Hojas sin cambios: {', '.join(sin_cambios)}")

    # Resumen final
    resumen = mapa.get("resumen", {})
    print(f"\n{'─'*60}")
    print(f"Mapeos directos:  {resumen.get('mapeos_directos', '?')}")
    print(f"Mapeos inferidos: {resumen.get('mapeos_inferidos', '?')}")
    print(f"Columnas ausentes: {resumen.get('columnas_ausentes', '?')}")
    listo = resumen.get("listo_para_pipeline", False)
    print(f"\nEstado: {'✅ LISTO PARA PIPELINE' if listo else '⚠️  REQUIERE REVISIÓN MANUAL'}")


# ─── Main ─────────────────────────────────────────────────────────────────────

def mapear(ruta_reporte: str = str(Path(__file__).parent / "ultimo_reporte_inspector.json"),
           verbose: bool = False) -> dict[str, Any]:
    """Punto de entrada principal del Mapper."""

    print(f"\n🗺️  Mapper iniciando...")
    print("─" * 60)

    # 1. Leer reporte del Inspector
    ruta = Path(ruta_reporte)
    if not ruta.exists():
        print(f"❌ No se encontró el reporte: {ruta_reporte}")
        print("   Ejecuta primero: python agentes/inspector.py --file 'ruta.xlsx' --json")
        sys.exit(1)

    print(f"📄 Leyendo reporte del Inspector: {ruta.name}")
    with open(ruta, encoding="utf-8") as f:
        reporte = json.load(f)

    # Verificar si hay algo que mapear
    problemas = reporte.get("reporte", {}).get("problemas_columnas", [])
    if not problemas:
        print("\n✅ No hay columnas que mapear — el Inspector no reportó diferencias.")
        mapa = {
            "version": "1.0",
            "mapa_columnas": {},
            "columnas_ausentes": [],
            "hojas_sin_cambios": reporte.get("reporte", {}).get("hojas_ok", []),
            "hojas_nuevas_ignoradas": reporte.get("reporte", {}).get("hojas_nuevas", []),
            "archivo_origen": reporte.get("archivo", ""),
            "resumen": {
                "mapeos_directos": 0,
                "mapeos_inferidos": 0,
                "columnas_ausentes": 0,
                "listo_para_pipeline": True,
            }
        }
    else:
        hojas_con_problemas = [p["hoja"] for p in problemas]
        print(f"🔎 Hojas a mapear ({len(hojas_con_problemas)}): {', '.join(hojas_con_problemas)}")

        # 2. Generar mapa con Claude
        print("\n🤖 Generando mapa de columnas con Claude...")
        mapa = generar_mapa_con_claude(reporte, verbose=verbose)

        # 3. Enriquecer con metadatos
        mapa = enriquecer_mapa(mapa, reporte)

    # 4. Mostrar resumen
    imprimir_resumen(mapa)

    # 5. Guardar
    output_path = Path(__file__).parent / "ultimo_mapa_columnas.json"
    output_path.write_text(
        json.dumps(mapa, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"\n💾 Mapa guardado en: {output_path}")

    return mapa


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Mapper de columnas — Astor Tech")
    parser.add_argument(
        "--reporte",
        default=str(Path(__file__).parent / "ultimo_reporte_inspector.json"),
        help="Ruta al reporte JSON del Inspector"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar prompt y respuesta de Claude"
    )
    args = parser.parse_args()

    mapear(ruta_reporte=args.reporte, verbose=args.verbose)
