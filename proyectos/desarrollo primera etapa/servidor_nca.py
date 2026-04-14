#!/usr/bin/env python3
"""
Servidor NCA - Login + Upload + Dashboard
==========================================
Flujo:
  1. Login con usuario/contraseña
  2. Carga del archivo Excel de NCA
  3. Generación automática del dashboard con generador_nca.py
  4. Visualización del dashboard en el navegador

USO:
    python servidor_nca.py
    Abre: http://localhost:5000
"""

import sys, os, json, subprocess, logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, session, send_file
from werkzeug.utils import secure_filename

# ─── Rutas ───────────────────────────────────────────────────────────────────
WORKSPACE      = Path(__file__).parent
UPLOAD_DIR     = WORKSPACE / "uploads"
OUTPUT_DIR     = WORKSPACE / "output"
USERS_FILE     = WORKSPACE / "users.json"
SKILL_DIR      = WORKSPACE / ".claude" / "skills" / "dashboard-financiero-nca"
GENERADOR      = SKILL_DIR / "generador_nca.py"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ─── App ─────────────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = "nca_dashboard_2026_secretkey"
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 100 MB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(WORKSPACE / "servidor_nca.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ─── Usuarios ─────────────────────────────────────────────────────────────────
def _cargar_usuarios() -> dict:
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            if "usuarios" in data:
                return {u["usuario"]: u for u in data["usuarios"]}
            if isinstance(data, dict):
                return {k: {"usuario": k, "contraseña": v, "nombre": k} for k, v in data.items()}
        except Exception as e:
            logger.warning(f"⚠️  No se pudo leer users.json: {e}")
    logger.warning("⚠️  users.json no encontrado — usando credenciales por defecto (admin/admin123)")
    return {"admin": {"usuario": "admin", "contraseña": "admin123", "nombre": "Administrador"}}

USUARIOS = _cargar_usuarios()

# ─── HTML ─────────────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCA — Acceso</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{
    font-family:'Segoe UI',sans-serif;
    background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);
    min-height:100vh;display:flex;align-items:center;justify-content:center;
  }
  .card{
    background:rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.1);
    border-radius:16px;
    padding:48px 40px;
    width:100%;max-width:420px;
    backdrop-filter:blur(20px);
    box-shadow:0 25px 50px rgba(0,0,0,0.5);
  }
  .logo{text-align:center;margin-bottom:32px}
  .logo h1{color:#fff;font-size:2rem;font-weight:700;letter-spacing:3px}
  .logo p{color:rgba(255,255,255,0.4);font-size:.85rem;margin-top:4px}
  .form-group{margin-bottom:20px}
  label{display:block;color:rgba(255,255,255,0.6);font-size:.8rem;font-weight:600;
    text-transform:uppercase;letter-spacing:1px;margin-bottom:8px}
  input{
    width:100%;padding:14px 16px;
    background:rgba(255,255,255,0.08);
    border:1px solid rgba(255,255,255,0.15);
    border-radius:8px;color:#fff;font-size:.95rem;
    outline:none;transition:.2s;
  }
  input:focus{border-color:#4f8ef7;background:rgba(79,142,247,0.08)}
  input::placeholder{color:rgba(255,255,255,0.25)}
  .btn{
    width:100%;padding:15px;
    background:linear-gradient(135deg,#4f8ef7,#8b5cf6);
    border:none;border-radius:8px;
    color:#fff;font-size:1rem;font-weight:600;
    cursor:pointer;transition:.2s;letter-spacing:.5px;
    margin-top:8px;
  }
  .btn:hover{opacity:.9;transform:translateY(-1px)}
  .btn:active{transform:translateY(0)}
  .error{
    background:rgba(239,68,68,0.15);
    border:1px solid rgba(239,68,68,0.3);
    color:#fca5a5;padding:12px 16px;
    border-radius:8px;font-size:.85rem;
    margin-bottom:20px;display:none
  }
  .error.show{display:block}
  .spinner{display:none;text-align:center;margin-top:12px}
  .spinner.show{display:block}
  .dot{display:inline-block;width:8px;height:8px;border-radius:50%;
    background:#4f8ef7;margin:0 3px;animation:bounce .8s infinite}
  .dot:nth-child(2){animation-delay:.15s}
  .dot:nth-child(3){animation-delay:.3s}
  @keyframes bounce{0%,80%,100%{transform:scale(0.6)}40%{transform:scale(1)}}
</style>
</head>
<body>
<div class="card">
  <div class="logo">
    <h1>NCA</h1>
    <p>Dashboard Financiero · Análisis Clínicas</p>
  </div>
  <div class="error" id="err">{{ error }}</div>
  <form method="POST" action="/login" onsubmit="handleSubmit()">
    <div class="form-group">
      <label>Usuario</label>
      <input type="text" name="usuario" placeholder="Ingresa tu usuario" required autofocus>
    </div>
    <div class="form-group">
      <label>Contraseña</label>
      <input type="password" name="contrasena" placeholder="••••••••" required>
    </div>
    <button class="btn" type="submit">Acceder</button>
    <div class="spinner" id="spin">
      <div class="dot"></div><div class="dot"></div><div class="dot"></div>
    </div>
  </form>
</div>
<script>
  const err = document.getElementById('err');
  if(err.textContent.trim()) err.classList.add('show');
  function handleSubmit(){
    document.getElementById('spin').classList.add('show');
  }
</script>
</body>
</html>"""


UPLOAD_HTML = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NCA — Cargar Archivo</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{
    font-family:'Segoe UI',sans-serif;
    background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 50%,#16213e 100%);
    min-height:100vh;display:flex;flex-direction:column;align-items:center;
    justify-content:center;padding:20px;
  }
  header{
    position:fixed;top:0;left:0;right:0;
    background:rgba(15,15,26,0.9);
    backdrop-filter:blur(10px);
    border-bottom:1px solid rgba(255,255,255,0.08);
    padding:16px 32px;display:flex;justify-content:space-between;align-items:center;
    z-index:100;
  }
  header h2{color:#fff;font-size:1.1rem;font-weight:600;letter-spacing:2px}
  .user-info{color:rgba(255,255,255,0.5);font-size:.85rem;display:flex;align-items:center;gap:12px}
  .logout{color:#ef4444;text-decoration:none;font-size:.8rem;font-weight:600;
    padding:6px 14px;border:1px solid rgba(239,68,68,0.3);border-radius:6px;
    transition:.2s}
  .logout:hover{background:rgba(239,68,68,0.1)}
  .container{width:100%;max-width:560px;margin-top:60px}
  .card{
    background:rgba(255,255,255,0.05);
    border:1px solid rgba(255,255,255,0.1);
    border-radius:16px;padding:48px 40px;
    backdrop-filter:blur(20px);
    box-shadow:0 25px 50px rgba(0,0,0,0.5);
  }
  h1{color:#fff;font-size:1.6rem;font-weight:700;margin-bottom:8px}
  .subtitle{color:rgba(255,255,255,0.4);font-size:.9rem;margin-bottom:32px}
  .drop-zone{
    border:2px dashed rgba(79,142,247,0.4);
    border-radius:12px;padding:48px 32px;
    text-align:center;cursor:pointer;
    transition:.2s;background:rgba(79,142,247,0.03);
  }
  .drop-zone:hover,.drop-zone.drag-over{
    border-color:#4f8ef7;background:rgba(79,142,247,0.08)
  }
  .drop-icon{font-size:3rem;margin-bottom:16px}
  .drop-text{color:#fff;font-size:1rem;font-weight:600;margin-bottom:8px}
  .drop-sub{color:rgba(255,255,255,0.4);font-size:.85rem}
  .drop-sub span{color:#4f8ef7;font-weight:600}
  input[type=file]{display:none}
  .file-selected{
    display:none;margin-top:20px;
    background:rgba(79,142,247,0.1);
    border:1px solid rgba(79,142,247,0.3);
    border-radius:8px;padding:16px;
    display:none;align-items:center;gap:12px;
  }
  .file-selected.show{display:flex}
  .file-icon{font-size:1.8rem}
  .file-info{flex:1}
  .file-name{color:#fff;font-size:.9rem;font-weight:600}
  .file-size{color:rgba(255,255,255,0.4);font-size:.8rem;margin-top:2px}
  .btn-generate{
    width:100%;padding:16px;margin-top:24px;
    background:linear-gradient(135deg,#4f8ef7,#8b5cf6);
    border:none;border-radius:10px;
    color:#fff;font-size:1rem;font-weight:700;
    cursor:pointer;transition:.2s;letter-spacing:.5px;
    display:none;
  }
  .btn-generate.show{display:block}
  .btn-generate:hover{opacity:.9;transform:translateY(-1px)}
  /* Loading overlay */
  .overlay{
    display:none;position:fixed;inset:0;
    background:rgba(15,15,26,0.95);
    z-index:999;flex-direction:column;
    align-items:center;justify-content:center;gap:24px;
  }
  .overlay.show{display:flex}
  .loader{
    width:80px;height:80px;
    border:4px solid rgba(79,142,247,0.2);
    border-top:4px solid #4f8ef7;
    border-radius:50%;animation:spin 1s linear infinite;
  }
  @keyframes spin{to{transform:rotate(360deg)}}
  .load-title{color:#fff;font-size:1.3rem;font-weight:700}
  .load-steps{color:rgba(255,255,255,0.4);font-size:.9rem;text-align:center}
  .step{opacity:.4;transition:.3s}
  .step.active{opacity:1;color:#4f8ef7}
  .step.done{opacity:.6;color:#22c55e}
  .progress{width:320px;height:4px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden}
  .progress-bar{height:100%;background:linear-gradient(90deg,#4f8ef7,#8b5cf6);
    width:0%;transition:width .5s ease;border-radius:4px}
  .error-box{
    display:none;margin-top:20px;
    background:rgba(239,68,68,0.1);
    border:1px solid rgba(239,68,68,0.3);
    color:#fca5a5;padding:14px 16px;
    border-radius:8px;font-size:.85rem;
  }
  .error-box.show{display:block}
</style>
</head>
<body>
<header>
  <h2>NCA · DASHBOARD</h2>
  <div class="user-info">
    <span>👤 {{ usuario }}</span>
    <a class="logout" href="/logout">Cerrar sesión</a>
  </div>
</header>

<div class="container">
  <div class="card">
    <h1>📊 Cargar Excel NCA</h1>
    <p class="subtitle">Carga el archivo Excel para generar el dashboard financiero completo con 8 módulos de análisis.</p>

    <form id="uploadForm" method="POST" action="/procesar" enctype="multipart/form-data">
      <div class="drop-zone" id="dropZone">
        <div class="drop-icon">📂</div>
        <div class="drop-text">Arrastra tu archivo aquí</div>
        <div class="drop-sub">o <span>haz clic para seleccionar</span></div>
        <div class="drop-sub" style="margin-top:8px">Formatos: .xlsx · .xls · Máx 100 MB</div>
        <input type="file" name="archivo" id="fileInput" accept=".xlsx,.xls">
      </div>

      <div class="file-selected" id="fileSelected">
        <div class="file-icon">📗</div>
        <div class="file-info">
          <div class="file-name" id="fileName">—</div>
          <div class="file-size" id="fileSize">—</div>
        </div>
        <span style="cursor:pointer;color:rgba(255,255,255,0.3);font-size:1.2rem" onclick="clearFile()">✕</span>
      </div>

      <div class="error-box" id="errorBox"></div>

      <button class="btn-generate" id="btnGenerate" type="button" onclick="generarDashboard()">
        ⚡ Generar Dashboard NCA
      </button>
    </form>
  </div>
</div>

<!-- Loading Overlay -->
<div class="overlay" id="overlay">
  <div class="loader"></div>
  <div class="load-title">Generando Dashboard</div>
  <div class="progress"><div class="progress-bar" id="progressBar"></div></div>
  <div class="load-steps" id="loadSteps">
    <div class="step" id="s1">📥 Leyendo archivo Excel…</div>
    <div class="step" id="s2">📊 Procesando EERR y Flujo de Caja…</div>
    <div class="step" id="s3">📈 Analizando Ventas y RRHH…</div>
    <div class="step" id="s4">💰 Segmentando costos por sucursal…</div>
    <div class="step" id="s5">🎨 Generando dashboard HTML…</div>
  </div>
</div>

<script>
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if(file) setFile(file);
});

fileInput.addEventListener('change', e => {
  if(e.target.files[0]) setFile(e.target.files[0]);
});

function setFile(file) {
  const ext = file.name.split('.').pop().toLowerCase();
  if(!['xlsx','xls'].includes(ext)) {
    showError('Solo se aceptan archivos Excel (.xlsx, .xls)');
    return;
  }
  if(file.size > 100*1024*1024) {
    showError('El archivo excede el límite de 100 MB');
    return;
  }
  document.getElementById('errorBox').classList.remove('show');
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = (file.size/1024/1024).toFixed(2) + ' MB';
  document.getElementById('fileSelected').classList.add('show');
  document.getElementById('btnGenerate').classList.add('show');

  // Sincronizar con input file
  const dt = new DataTransfer();
  dt.items.add(file);
  fileInput.files = dt.files;
}

function clearFile() {
  fileInput.value = '';
  document.getElementById('fileSelected').classList.remove('show');
  document.getElementById('btnGenerate').classList.remove('show');
}

function showError(msg) {
  const b = document.getElementById('errorBox');
  b.textContent = '⚠️ ' + msg;
  b.classList.add('show');
}

function animateSteps() {
  const steps = ['s1','s2','s3','s4','s5'];
  const pcts  = [15, 35, 55, 75, 90];
  steps.forEach((id, i) => {
    setTimeout(() => {
      if(i > 0) document.getElementById(steps[i-1]).className = 'step done';
      document.getElementById(id).className = 'step active';
      document.getElementById('progressBar').style.width = pcts[i] + '%';
    }, i * 2800);
  });
}

function generarDashboard() {
  if(!fileInput.files[0]) { showError('Selecciona un archivo primero'); return; }
  document.getElementById('overlay').classList.add('show');
  animateSteps();
  document.getElementById('uploadForm').submit();
}
</script>
</body>
</html>"""


# ─── Rutas Flask ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if session.get("usuario"):
        return redirect(url_for("upload"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        usuario  = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "")
        if usuario in USUARIOS and USUARIOS[usuario]["contraseña"] == contrasena:
            session["usuario"] = usuario
            session["nombre"]  = USUARIOS[usuario].get("nombre", usuario)
            logger.info(f"✅ Login: {usuario}")
            return redirect(url_for("upload"))
        else:
            error = "Usuario o contraseña incorrectos"
            logger.warning(f"❌ Login fallido: {usuario}")
    return render_template_string(LOGIN_HTML, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/upload")
def upload():
    if not session.get("usuario"):
        return redirect(url_for("login"))
    return render_template_string(UPLOAD_HTML, usuario=session.get("nombre", session.get("usuario")))


@app.route("/procesar", methods=["POST"])
def procesar():
    if not session.get("usuario"):
        return redirect(url_for("login"))

    if "archivo" not in request.files:
        return redirect(url_for("upload"))

    archivo = request.files["archivo"]
    if not archivo.filename:
        return redirect(url_for("upload"))

    # Guardar Excel
    ext      = Path(archivo.filename).suffix.lower()
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre   = f"{ts}_{secure_filename(archivo.filename)}"
    ruta_xl  = UPLOAD_DIR / nombre
    archivo.save(str(ruta_xl))
    logger.info(f"📥 Excel guardado: {ruta_xl.name}")

    ruta_html = OUTPUT_DIR / f"dashboard_nca_{ts}.html"

    # Ejecutar generador NCA
    cmd = [
        sys.executable, "-X", "utf8",
        str(GENERADOR),
        "--file",   str(ruta_xl),
        "--output", str(ruta_html),
    ]
    logger.info(f"⚙️  Ejecutando generador NCA: {' '.join(cmd)}")

    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
            stdin=subprocess.DEVNULL,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )
        if resultado.returncode != 0:
            logger.error(f"❌ Error generador:\n{resultado.stderr}")
            return _error_page(f"Error al generar el dashboard:<br><pre>{resultado.stderr[-1500:]}</pre>")

        if not ruta_html.exists():
            return _error_page("El dashboard no fue generado. Verifica que el Excel tenga el formato correcto.")

        logger.info(f"✅ Dashboard generado: {ruta_html.name}")
        # Guardar ruta en sesión para servirla
        session["ultimo_dashboard"] = str(ruta_html)
        return redirect(url_for("ver_dashboard"))

    except subprocess.TimeoutExpired:
        return _error_page("El proceso tardó demasiado (>3 min). El archivo puede ser muy grande.")
    except Exception as e:
        logger.exception(e)
        return _error_page(str(e))


@app.route("/api/whoami")
def whoami():
    """Retorna nombre del usuario en sesión (usado por el dashboard)."""
    if not session.get("usuario"):
        return jsonify({"nombre": ""}), 401
    return jsonify({
        "nombre": session.get("nombre", session.get("usuario", "")),
        "usuario": session.get("usuario", "")
    })


@app.route("/dashboard")
def ver_dashboard():
    if not session.get("usuario"):
        return redirect(url_for("login"))
    ruta = session.get("ultimo_dashboard")
    if not ruta or not Path(ruta).exists():
        return redirect(url_for("upload"))
    return send_file(ruta, mimetype="text/html")


@app.route("/nuevo")
def nuevo():
    """Permite cargar otro archivo."""
    if not session.get("usuario"):
        return redirect(url_for("login"))
    session.pop("ultimo_dashboard", None)
    return redirect(url_for("upload"))


def _error_page(msg):
    return render_template_string(f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Error — NCA</title>
<style>
  body{{font-family:'Segoe UI',sans-serif;
    background:linear-gradient(135deg,#0f0f1a,#1a1a2e);
    min-height:100vh;display:flex;align-items:center;justify-content:center}}
  .card{{background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.3);
    border-radius:16px;padding:48px 40px;max-width:600px;text-align:center}}
  h1{{color:#fca5a5;font-size:1.5rem;margin-bottom:16px}}
  p{{color:rgba(255,255,255,0.6);line-height:1.6}}
  pre{{text-align:left;font-size:.75rem;color:#fca5a5;margin-top:16px;
    max-height:200px;overflow:auto;background:rgba(0,0,0,0.3);padding:12px;border-radius:8px}}
  a{{display:inline-block;margin-top:24px;padding:12px 28px;
    background:rgba(255,255,255,0.1);color:#fff;border-radius:8px;
    text-decoration:none;font-weight:600}}
  a:hover{{background:rgba(255,255,255,0.15)}}
</style></head>
<body><div class="card">
  <h1>⚠️ Error al generar el dashboard</h1>
  <p>{msg}</p>
  <a href="/upload">← Volver e intentar de nuevo</a>
</div></body></html>""")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  SERVIDOR NCA DASHBOARD")
    print("="*60)
    print(f"\n  🚀 Iniciando servidor...")
    print(f"  📊 Abre en el navegador: http://localhost:5000\n")
    print(f"  🔑 Credenciales:")
    for u, d in USUARIOS.items():
        print(f"     {u} / {d['contraseña']}")
    print("\n" + "="*60 + "\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
