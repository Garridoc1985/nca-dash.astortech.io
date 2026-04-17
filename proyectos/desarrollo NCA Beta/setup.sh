#!/bin/bash
# ============================================================
# setup.sh — Instalador automático NCA Dashboard
# Compatible con Ubuntu 20.04+, Debian, cualquier VPS
# ============================================================
# USO:
#   chmod +x setup.sh
#   ./setup.sh
# ============================================================

set -e

PYTHON_MIN="3.10"
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "============================================================"
echo "  INSTALADOR NCA DASHBOARD"
echo "============================================================"
echo ""

# ── 1. Verificar Python ────────────────────────────────────────
echo "[ 1/6 ] Verificando Python..."
if ! command -v python3 &>/dev/null; then
    echo "  Python3 no encontrado. Instalando..."
    sudo apt-get update -qq
    sudo apt-get install -y python3 python3-pip python3-venv
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "  Python $PYTHON_VERSION detectado"

# ── 2. Crear entorno virtual ──────────────────────────────────
echo "[ 2/6 ] Creando entorno virtual..."
cd "$APP_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "  Entorno virtual creado en ./venv"
else
    echo "  Entorno virtual ya existe"
fi

# Activar entorno virtual
source venv/bin/activate

# ── 3. Instalar dependencias ──────────────────────────────────
echo "[ 3/6 ] Instalando dependencias..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "  Dependencias instaladas"

# ── 4. Configurar .env ────────────────────────────────────────
echo "[ 4/6 ] Configurando variables de entorno..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Generar clave secreta aleatoria
    SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    sed -i "s/cambia_esto_por_una_clave_segura/$SECRET/" .env
    echo "  .env creado con clave secreta generada automáticamente"
else
    echo "  .env ya existe, no se sobreescribe"
fi

# ── 5. Crear directorios necesarios ───────────────────────────
echo "[ 5/6 ] Creando directorios..."
mkdir -p uploads output logs
echo "  uploads/ output/ logs/ listos"

# ── 6. Configurar users.json ──────────────────────────────────
echo "[ 6/6 ] Verificando usuarios..."
if [ ! -f "users.json" ]; then
    cp users.example.json users.json
    echo "  users.json creado desde ejemplo"
    echo ""
    echo "  IMPORTANTE: Edita users.json para cambiar la contraseña por defecto"
else
    echo "  users.json ya existe"
fi

# ── Fin ───────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo "  INSTALACION COMPLETADA"
echo "============================================================"
echo ""
echo "  Para iniciar el servidor:"
echo "    ./iniciar.sh"
echo ""
echo "  Para producción con Gunicorn:"
echo "    source venv/bin/activate"
echo "    gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app_nca"
echo ""
echo "  Dashboard Financiero NCA:  http://localhost:5000"
echo "  Dashboard de Ventas:       http://localhost:5001"
echo ""
