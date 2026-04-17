#!/bin/bash
# ============================================================
# iniciar.sh — Inicia NCA Dashboard (desarrollo o producción)
# Compatible con: Ubuntu, Debian, macOS, cualquier VPS
# ============================================================
# USO:
#   ./iniciar.sh              → Inicia dashboard financiero NCA (puerto 5000)
#   ./iniciar.sh ventas       → Inicia dashboard de ventas (puerto 5001)
#   ./iniciar.sh ambos        → Inicia ambos servidores
#   ./iniciar.sh prod         → Modo producción con Gunicorn
# ============================================================

set -e
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

MODO="${1:-nca}"

# ── Cargar .env si existe ──────────────────────────────────────
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

NCA_PORT="${NCA_PORT:-5000}"
VENTAS_PORT="${VENTAS_PORT:-5001}"

# ── Activar entorno virtual si existe ─────────────────────────
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# ── Verificar instalación básica ──────────────────────────────
if ! python3 -c "import flask" &>/dev/null; then
    echo "Dependencias no instaladas. Ejecuta primero: ./setup.sh"
    exit 1
fi

# ── Verificar users.json ──────────────────────────────────────
if [ ! -f "users.json" ]; then
    if [ -f "users.example.json" ]; then
        cp users.example.json users.json
        echo "users.json creado desde ejemplo"
    else
        echo "Error: users.json no encontrado"
        exit 1
    fi
fi

mkdir -p uploads output logs

echo ""
echo "============================================================"
echo "  NCA DASHBOARD"
echo "============================================================"

# ── Modo producción (Gunicorn) ────────────────────────────────
if [ "$MODO" = "prod" ]; then
    if ! command -v gunicorn &>/dev/null; then
        echo "Gunicorn no instalado. Ejecuta: pip install gunicorn"
        exit 1
    fi
    echo "  Modo: PRODUCCION (Gunicorn)"
    echo "  Dashboard NCA:    http://0.0.0.0:$NCA_PORT"
    echo ""
    gunicorn --bind "0.0.0.0:$NCA_PORT" \
             --workers 2 \
             --timeout 120 \
             --access-logfile logs/access_nca.log \
             --error-logfile logs/error_nca.log \
             wsgi:app_nca
    exit 0
fi

# ── Modo ambos servidores ────────────────────────────────────
if [ "$MODO" = "ambos" ]; then
    echo "  Iniciando ambos servidores en background..."
    echo "  Dashboard NCA:    http://localhost:$NCA_PORT"
    echo "  Dashboard Ventas: http://localhost:$VENTAS_PORT"
    echo "  Para detener: kill \$(cat logs/nca.pid) \$(cat logs/ventas.pid)"
    echo ""
    python3 -X utf8 servidor_nca.py &
    echo $! > logs/nca.pid
    python3 -X utf8 servidor_ventas.py &
    echo $! > logs/ventas.pid
    wait
    exit 0
fi

# ── Dashboard de Ventas ──────────────────────────────────────
if [ "$MODO" = "ventas" ]; then
    echo "  Dashboard Ventas: http://localhost:$VENTAS_PORT"
    echo "  CTRL+C para detener"
    echo "============================================================"
    echo ""
    python3 -X utf8 servidor_ventas.py
    exit 0
fi

# ── Dashboard NCA (default) ──────────────────────────────────
echo "  Dashboard NCA:  http://localhost:$NCA_PORT"
echo "  CTRL+C para detener"
echo "============================================================"
echo ""
python3 -X utf8 servidor_nca.py
