#!/usr/bin/env python3
"""
Servidor Web — Dashboard de Ventas
Login + upload de Excel → genera dashboard interactivo.

Uso:
    python -X utf8 servidor_ventas.py
    Abre: http://localhost:5001
    Login: admin / admin123
"""
import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from functools import wraps
from pathlib import Path

from flask import (Flask, request, session, redirect, url_for,
                   render_template_string, send_file, jsonify)

# ─── CONFIG ───────────────────────────────────────────────────────────────────

WORKSPACE    = Path(__file__).resolve().parent
UPLOAD_DIR   = WORKSPACE / "uploads"
OUTPUT_DIR   = WORKSPACE / "output"
GENERADOR    = WORKSPACE / ".claude" / "skills" / "data-analytics-pro" / "scripts" / "normalizar_reporte_ventas.py"
USERS_FILE   = WORKSPACE / "users.json"
PORT         = 5001
SECRET_KEY   = "ventas-dashboard-2026"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── LOGGING ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(WORKSPACE / "servidor_ventas.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── FLASK ────────────────────────────────────────────────────────────────────

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ─── AUTH ─────────────────────────────────────────────────────────────────────

def _cargar_usuarios() -> dict:
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if "usuarios" in data and isinstance(data["usuarios"], list):
                return {u["usuario"]: u["contraseña"] for u in data["usuarios"]}
            if isinstance(data, dict):
                return data
        except Exception as e:
            logger.warning(f"⚠️  No se pudo leer users.json: {e}")
    logger.warning("⚠️  users.json no encontrado — usando credenciales por defecto (admin/admin123)")
    return {"admin": "admin123"}

USUARIOS = _cargar_usuarios()

def verificar_usuario(username: str, password: str) -> bool:
    return USUARIOS.get(username) == password

def login_requerido(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("usuario"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ─── TEMPLATES ────────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard de Ventas — Login</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0e13;--card:#141922;--border:#1e2a3a;--text:#e2e8f0;--muted:#64748b;--em:#10b981;--red:#ef4444;--radius:12px;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;}
.box{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:44px 48px;width:100%;max-width:400px;text-align:center;}
.icon{font-size:2.4rem;margin-bottom:8px;}
h1{font-size:1.3rem;font-weight:700;color:var(--em);margin-bottom:4px;}
.sub{color:var(--muted);font-size:.84rem;margin-bottom:28px;}
input{width:100%;background:#0d111a;border:1px solid var(--border);border-radius:8px;padding:10px 14px;color:var(--text);font-size:.95rem;margin-bottom:12px;outline:none;transition:border-color .2s;}
input:focus{border-color:var(--em);}
button{width:100%;background:var(--em);color:#fff;border:none;border-radius:8px;padding:11px;font-size:1rem;font-weight:600;cursor:pointer;transition:opacity .2s;margin-top:4px;}
button:hover{opacity:.88;}
.err{color:var(--red);font-size:.82rem;margin-top:10px;min-height:1.2em;}
</style>
</head>
<body>
<div class="box">
  <div class="icon">📊</div>
  <h1>Dashboard de Ventas</h1>
  <p class="sub">Ingresa tus credenciales para continuar</p>
  <form method="POST" action="/login">
    <input type="text" name="username" placeholder="Usuario" autocomplete="username" required>
    <input type="password" name="password" placeholder="Contraseña" autocomplete="current-password" required>
    <button type="submit">Ingresar</button>
  </form>
  {% if error %}<p class="err">{{ error }}</p>{% endif %}
</div>
</body>
</html>"""

UPLOAD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard de Ventas — Cargar Excel</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0e13;--card:#141922;--border:#1e2a3a;--surface:#1b2231;--text:#e2e8f0;--muted:#64748b;--em:#10b981;--em2:#34d399;--red:#ef4444;--amber:#f59e0b;--radius:12px;--shadow:0 4px 24px rgba(0,0,0,.4);}
*{box-sizing:border-box;margin:0;padding:0;}
html{scroll-behavior:smooth;}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;}
nav{position:sticky;top:0;z-index:100;background:#0d111aee;backdrop-filter:blur(14px);border-bottom:1px solid var(--border);display:flex;align-items:center;padding:0 28px;height:52px;gap:16px;}
.nav-brand{font-size:.95rem;font-weight:700;color:var(--em);}
.nav-right{margin-left:auto;display:flex;align-items:center;gap:14px;}
.nav-user{font-size:.78rem;color:var(--muted);font-family:'JetBrains Mono',monospace;}
.logout-btn{background:transparent;border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:5px 12px;font-size:.78rem;cursor:pointer;transition:border-color .15s,color .15s;text-decoration:none;}
.logout-btn:hover{border-color:var(--red);color:var(--red);}
main{max-width:800px;margin:0 auto;padding:48px 24px 80px;}
h1{font-size:1.5rem;font-weight:700;margin-bottom:8px;}
.sub{color:var(--muted);font-size:.9rem;margin-bottom:40px;}
.upload-card{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:40px;box-shadow:var(--shadow);}
.drop-zone{border:2px dashed var(--border);border-radius:10px;padding:48px 24px;text-align:center;cursor:pointer;transition:border-color .2s,background .2s;margin-bottom:24px;}
.drop-zone:hover,.drop-zone.drag-over{border-color:var(--em);background:rgba(16,185,129,.04);}
.drop-icon{font-size:2.8rem;margin-bottom:12px;}
.drop-title{font-size:1.05rem;font-weight:600;margin-bottom:6px;}
.drop-sub{color:var(--muted);font-size:.84rem;}
input[type=file]{display:none;}
.file-name{font-family:'JetBrains Mono',monospace;font-size:.82rem;color:var(--em);margin-top:12px;min-height:1.2em;}
.field-row{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px;}
@media(max-width:600px){.field-row{grid-template-columns:1fr;}}
.field label{display:block;font-size:.82rem;color:var(--muted);margin-bottom:6px;font-weight:500;}
.field input{width:100%;background:#0d111a;border:1px solid var(--border);border-radius:8px;padding:9px 13px;color:var(--text);font-size:.9rem;outline:none;transition:border-color .2s;}
.field input:focus{border-color:var(--em);}
.submit-btn{width:100%;background:var(--em);color:#fff;border:none;border-radius:10px;padding:13px;font-size:1rem;font-weight:600;cursor:pointer;transition:opacity .2s;}
.submit-btn:hover:not(:disabled){opacity:.88;}
.submit-btn:disabled{opacity:.45;cursor:not-allowed;}
.progress-wrap{display:none;margin-top:28px;}
.progress-bar{height:4px;background:var(--border);border-radius:4px;overflow:hidden;}
.progress-fill{height:100%;width:0;background:linear-gradient(90deg,var(--em),var(--em2));transition:width .3s;border-radius:4px;}
.progress-label{font-size:.82rem;color:var(--muted);margin-top:8px;text-align:center;}
.info-box{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:20px 24px;margin-top:32px;}
.info-title{font-size:.82rem;font-weight:600;color:var(--muted);margin-bottom:12px;text-transform:uppercase;letter-spacing:.06em;}
.col-list{display:flex;flex-wrap:wrap;gap:8px;}
.col-tag{font-family:'JetBrains Mono',monospace;font-size:.74rem;background:var(--card);border:1px solid var(--border);border-radius:6px;padding:3px 9px;color:var(--text);}
</style>
</head>
<body>

<nav>
  <span class="nav-brand">📊 Dashboard de Ventas</span>
  <div class="nav-right">
    <span class="nav-user">{{ usuario }}</span>
    <a href="/logout" class="logout-btn">Salir</a>
  </div>
</nav>

<main>
  <h1>Cargar datos de ventas</h1>
  <p class="sub">Sube un archivo Excel con tus transacciones para generar el dashboard interactivo.</p>

  <div class="upload-card">
    <form id="uploadForm" method="POST" action="/procesar" enctype="multipart/form-data">

      <div class="drop-zone" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <div class="drop-icon">📂</div>
        <div class="drop-title">Arrastra tu Excel aquí</div>
        <div class="drop-sub">o haz clic para seleccionar — .xlsx, .xls</div>
        <div class="file-name" id="fileName"></div>
        <input type="file" id="fileInput" name="archivo" accept=".xlsx,.xls" onchange="onFileChange(this)">
      </div>

      <div class="field-row">
        <div class="field">
          <label>Título del dashboard (opcional)</label>
          <input type="text" name="titulo" placeholder="Ej: Reporte Ventas Q1 2026">
        </div>
        <div class="field">
          <label>Nombre de hoja (opcional)</label>
          <input type="text" name="sheet" placeholder="Ej: Ventas (por defecto: primera hoja)">
        </div>
      </div>

      <button type="submit" class="submit-btn" id="submitBtn" disabled>
        Generar Dashboard
      </button>
    </form>

    <div class="progress-wrap" id="progressWrap">
      <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
      <div class="progress-label" id="progressLabel">Procesando...</div>
    </div>

    <div class="info-box">
      <div class="info-title">Columnas detectadas automáticamente</div>
      <div class="col-list">
        <span class="col-tag">Fecha Venta</span>
        <span class="col-tag">Localidad / Sucursal</span>
        <span class="col-tag">Cliente / RUT</span>
        <span class="col-tag">Vendedor</span>
        <span class="col-tag">Artículo / Tratamiento</span>
        <span class="col-tag">Cantidad</span>
        <span class="col-tag">Total / Monto</span>
        <span class="col-tag">Forma de Pago</span>
        <span class="col-tag">Descuento</span>
      </div>
    </div>
  </div>
</main>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const submitBtn = document.getElementById('submitBtn');

function onFileChange(input){
  if(input.files.length){
    document.getElementById('fileName').textContent = '✓ ' + input.files[0].name;
    submitBtn.disabled = false;
  }
}

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const files = e.dataTransfer.files;
  if(files.length && (files[0].name.endsWith('.xlsx') || files[0].name.endsWith('.xls'))){
    fileInput.files = files;
    onFileChange(fileInput);
  }
});

document.getElementById('uploadForm').addEventListener('submit', function(){
  submitBtn.disabled = true;
  submitBtn.textContent = 'Generando...';
  const pw = document.getElementById('progressWrap');
  pw.style.display = 'block';
  const fill = document.getElementById('progressFill');
  const label = document.getElementById('progressLabel');
  let pct = 0;
  const steps = [
    [10, 'Leyendo Excel...'],
    [30, 'Detectando columnas...'],
    [55, 'Calculando KPIs...'],
    [80, 'Generando HTML...'],
    [95, 'Finalizando...'],
  ];
  let i = 0;
  const iv = setInterval(() => {
    if(i < steps.length){ pct = steps[i][0]; label.textContent = steps[i][1]; i++; }
    fill.style.width = pct + '%';
  }, 1200);
});
</script>
</body>
</html>"""

ERROR_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Error — Dashboard Ventas</title>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0e13;--card:#141922;--border:#1e2a3a;--text:#e2e8f0;--red:#ef4444;--muted:#64748b;--radius:12px;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:24px;}
.box{background:var(--card);border:1px solid var(--border);border-radius:var(--radius);padding:40px 48px;max-width:600px;width:100%;text-align:center;}
.icon{font-size:2.4rem;margin-bottom:12px;}
h1{font-size:1.2rem;font-weight:700;color:var(--red);margin-bottom:8px;}
.msg{color:var(--muted);font-size:.9rem;margin-bottom:28px;line-height:1.6;}
a{display:inline-block;background:var(--border);color:var(--text);padding:10px 24px;border-radius:8px;text-decoration:none;font-weight:600;font-size:.9rem;}
a:hover{background:#2d3a4a;}
</style>
</head>
<body>
<div class="box">
  <div class="icon">⚠️</div>
  <h1>Error al procesar el archivo</h1>
  <p class="msg">{{ mensaje }}</p>
  <a href="/upload">← Volver e intentar de nuevo</a>
</div>
</body>
</html>"""

# ─── RUTAS ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if session.get("usuario"):
        return redirect(url_for("upload"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        u = request.form.get("username", "").strip()
        p = request.form.get("password", "").strip()
        if verificar_usuario(u, p):
            session["usuario"] = u
            logger.info(f"✅ Login: {u}")
            return redirect(url_for("upload"))
        error = "Usuario o contraseña incorrectos."
        logger.warning(f"Login fallido: {u}")
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    usuario = session.pop("usuario", None)
    if usuario:
        logger.info(f"Logout: {usuario}")
    return redirect(url_for("login"))


@app.route("/upload")
@login_requerido
def upload():
    return render_template_string(UPLOAD_HTML, usuario=session["usuario"])


@app.route("/procesar", methods=["POST"])
@login_requerido
def procesar():
    archivo = request.files.get("archivo")
    titulo  = request.form.get("titulo", "").strip() or None
    sheet   = request.form.get("sheet",  "").strip() or None

    if not archivo or not archivo.filename:
        return render_template_string(ERROR_HTML, mensaje="No se recibió ningún archivo.")

    ext = Path(archivo.filename).suffix.lower()
    if ext not in (".xlsx", ".xls"):
        return render_template_string(ERROR_HTML, mensaje="Solo se aceptan archivos .xlsx y .xls.")

    ts        = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre    = f"{ts}_{Path(archivo.filename).name.replace(' ', '_')}"
    ruta_xl   = UPLOAD_DIR / nombre
    ruta_html = OUTPUT_DIR / f"dashboard_ventas_{ts}.html"

    archivo.save(str(ruta_xl))
    logger.info(f"📥 Excel guardado: {ruta_xl.name}")

    # Construir comando
    cmd = [sys.executable, "-X", "utf8", str(GENERADOR),
           "--file",   str(ruta_xl),
           "--output", str(ruta_html)]
    if titulo:
        cmd += ["--titulo", titulo]
    if sheet:
        cmd += ["--sheet", sheet]

    logger.info(f"⚙️  Ejecutando: {' '.join(cmd)}")

    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
    except subprocess.TimeoutExpired:
        return render_template_string(ERROR_HTML,
            mensaje="El proceso tardó más de 2 minutos. El archivo puede ser muy grande.")
    except Exception as e:
        logger.exception(e)
        return render_template_string(ERROR_HTML, mensaje=f"Error inesperado: {e}")

    if resultado.returncode != 0:
        stderr = resultado.stderr[-1500:] if resultado.stderr else "(sin detalle)"
        logger.error(f"Generador falló:\n{stderr}")
        return render_template_string(ERROR_HTML,
            mensaje=f"El generador encontró un error:\n{stderr}")

    if not ruta_html.exists():
        return render_template_string(ERROR_HTML,
            mensaje="El archivo HTML no fue generado. Revisa que el Excel tenga datos válidos.")

    logger.info(f"✅ Dashboard generado: {ruta_html.name}")
    session["ultimo_dashboard"] = str(ruta_html)
    return redirect(url_for("ver_dashboard"))


@app.route("/dashboard")
@login_requerido
def ver_dashboard():
    ruta = session.get("ultimo_dashboard")
    if not ruta or not Path(ruta).exists():
        return redirect(url_for("upload"))
    return send_file(ruta, mimetype="text/html")


@app.route("/health")
def health():
    return jsonify({"status": "ok", "port": PORT})


# ─── MAIN ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print(f"\n{'='*62}")
    print(f"  SERVIDOR DASHBOARD DE VENTAS")
    print(f"{'='*62}")
    print(f"  URL    : http://localhost:{PORT}")
    print(f"  Login  : admin / admin123")
    print(f"  Detener: Ctrl+C")
    print(f"{'='*62}\n")

    if not GENERADOR.exists():
        print(f"  ⚠  Generador no encontrado: {GENERADOR}")
        sys.exit(1)

    app.run(host="0.0.0.0", port=PORT, debug=False)
