# Desarrollo NCA Beta — Guía de Instalación y Despliegue

Archivos necesarios para instalar y ejecutar el sistema NCA Dashboard en cualquier plataforma: Windows, Ubuntu o cualquier VPS.

---

## Contenido de esta carpeta

| Archivo | Propósito |
|---|---|
| `requirements.txt` | Dependencias Python del proyecto |
| `wsgi.py` | Punto de entrada WSGI para Gunicorn (producción) |
| `.env.example` | Plantilla de variables de entorno |
| `setup.sh` | Instalador automático para Ubuntu/VPS |
| `iniciar.sh` | Launcher para Linux/Mac |
| `iniciar.bat` | Launcher para Windows |

---

## Instalación en Windows

**Primera vez:**
```
iniciar.bat instalar
```

**Iniciar servidores:**
```
iniciar.bat              → Dashboard Financiero NCA  (http://localhost:5000)
iniciar.bat ventas       → Dashboard de Ventas       (http://localhost:5001)
iniciar.bat ambos        → Ambos servidores en paralelo
```

---

## Instalación en Ubuntu / VPS

```bash
# 1. Clonar el repositorio
git clone https://github.com/Garridoc1985/nca-dash.astortech.io
cd nca-dash.astortech.io

# 2. Dar permisos al instalador
chmod +x "proyectos/desarrollo NCA Beta/setup.sh"

# 3. Ejecutar instalador (crea venv, instala dependencias, configura .env)
"proyectos/desarrollo NCA Beta/setup.sh"

# 4. Iniciar en modo desarrollo
"proyectos/desarrollo NCA Beta/iniciar.sh"

# 5. Iniciar en modo producción (Gunicorn)
"proyectos/desarrollo NCA Beta/iniciar.sh" prod
```

---

## Variables de entorno

Copia `.env.example` como `.env` en la raíz del proyecto y completa los valores:

```bash
cp "proyectos/desarrollo NCA Beta/.env.example" .env
```

| Variable | Descripción |
|---|---|
| `FLASK_SECRET_KEY` | Clave secreta Flask (generar aleatoria en producción) |
| `NCA_PORT` | Puerto dashboard financiero (default: 5000) |
| `VENTAS_PORT` | Puerto dashboard ventas (default: 5001) |
| `FLASK_ENV` | `development` o `production` |
| `EXCEL_NCA_PATH` | Ruta al Excel NCA (opcional, se puede subir por interfaz) |
| `ANTHROPIC_API_KEY` | API key de Anthropic (solo para agentes IA) |

---

## Modo producción con Gunicorn

Para servidores Ubuntu/VPS en producción:

```bash
source venv/bin/activate

# Dashboard Financiero
gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 wsgi:app_nca

# Dashboard de Ventas
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 120 wsgi:app_ventas
```

---

## Requisitos mínimos

| Componente | Versión |
|---|---|
| Python | 3.10 o superior |
| RAM | 512 MB mínimo (1 GB recomendado) |
| Disco | 200 MB libres |
| OS | Windows 10+, Ubuntu 20.04+, Debian 11+ |

---

## Solución de problemas comunes

**`ModuleNotFoundError: No module named 'flask'`**
```bash
pip install -r "proyectos/desarrollo NCA Beta/requirements.txt"
```

**`users.json no encontrado`**
```bash
cp users.example.json users.json
# Edita users.json con tus credenciales
```

**Puerto en uso**
```bash
# Cambiar puerto en .env:
NCA_PORT=5010
```

**Error al leer Excel**
El sistema incluye `adaptador_excel.py` que detecta y corrige automáticamente cambios de estructura en el Excel. Si persiste el error, revisa el log en `logs/`.

---

## Estructura de usuarios (`users.json`)

```json
{
  "usuarios": [
    {
      "usuario": "admin",
      "contraseña": "tu_contraseña_segura",
      "nombre": "Administrador"
    }
  ]
}
```

---

*NCA Clínicas · Astor Tech · 2026*
