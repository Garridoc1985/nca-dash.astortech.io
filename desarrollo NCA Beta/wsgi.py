"""
wsgi.py — Punto de entrada WSGI para producción
================================================
Usado por Gunicorn (Linux/Ubuntu/Hostinger) en lugar de app.run().

Gunicorn NCA Dashboard:
    gunicorn --bind 0.0.0.0:5000 wsgi:app_nca

Gunicorn Dashboard Ventas:
    gunicorn --bind 0.0.0.0:5001 wsgi:app_ventas

Con múltiples workers (recomendado en producción):
    gunicorn --bind 0.0.0.0:5000 --workers 2 wsgi:app_nca
"""

import sys
from pathlib import Path

# Asegurar que el directorio raíz esté en el path
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from servidor_nca import app as app_nca
from servidor_ventas import app as app_ventas

# Aliases para compatibilidad con distintos runners
application = app_nca   # Nombre estándar WSGI (Apache mod_wsgi, etc.)
app = app_nca           # Gunicorn por defecto usa este módulo

if __name__ == "__main__":
    app_nca.run(debug=False, host="0.0.0.0", port=5000)
