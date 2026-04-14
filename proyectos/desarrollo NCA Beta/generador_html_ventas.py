"""
Generador Dashboard de Ventas — Vista Jefa de Sucursal
=======================================================
Dashboard HTML autónomo con KPIs operacionales de ventas.
Secciones: Resumen | Sucursales | Tendencia | Artículos | Pagos | Detalle

USO:
    from generador_html_ventas import GeneradorDashboardVentas
    gen = GeneradorDashboardVentas(df_norm, usuario="admin", password="nca2026")
    gen.generar_html("output/dashboard_ventas.html")
"""
import json
import math
from pathlib import Path
import pandas as pd

PALETTE = [
    "#10b981", "#38bdf8", "#f59e0b", "#a78bfa", "#f472b6",
    "#34d399", "#60a5fa", "#fb923c", "#c084fc", "#4ade80",
    "#fbbf24", "#818cf8", "#2dd4bf", "#f87171", "#e879f9",
]


class GeneradorDashboardVentas:
    """
    Genera dashboard HTML autónomo orientado a jefa de sucursal.
    Recibe el DataFrame normalizado directamente.
    """

    def __init__(self, df_norm: pd.DataFrame, usuario: str = "admin",
                 password: str = "nca2026", titulo: str = "Reporte de Ventas"):
        self.df       = df_norm.copy()
        self.usuario  = usuario
        self.password = password
        self.titulo   = titulo
        self._preparar_datos()

    # ------------------------------------------------------------------
    # Preparación de datos
    # ------------------------------------------------------------------

    def _preparar_datos(self):
        df = self.df

        df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
        if "periodo_carga" not in df.columns:
            df["periodo_carga"] = df["fecha"].dt.strftime("%Y-%m")
        df["periodo_carga"]         = df["periodo_carga"].fillna("N/A")
        df["localidad"]             = df["localidad"].fillna("SIN SUCURSAL")
        df["nombre_del_articulo"]   = df["nombre_del_articulo"].fillna("SIN NOMBRE")
        df["forma_de_pago"]         = df["forma_de_pago"].fillna("SIN ESPECIFICAR")
        df["id_del_cliente"]        = df["id_del_cliente"].fillna("ANONIMO")
        df["cliente"]               = df["cliente"].fillna("")
        df["cantidad_de_descuento"] = pd.to_numeric(
            df.get("cantidad_de_descuento", 0), errors="coerce"
        ).fillna(0)

        # KPIs globales
        self.ingresos        = float(df["total_pagado_con_metodo_de_pago"].sum())
        self.num_ventas      = int(df["no_de_venta"].nunique())
        self.ticket_prom     = self.ingresos / self.num_ventas if self.num_ventas else 0
        self.articulos_vend  = int(df["cantidad"].sum()) if "cantidad" in df.columns else 0
        self.clientes_unicos = int(df["id_del_cliente"].nunique())
        self.descuentos      = float(df["cantidad_de_descuento"].sum())
        base = self.ingresos + self.descuentos
        self.pct_desc = round(self.descuentos / base * 100, 1) if base > 0 else 0

        # Periodos
        periodos = sorted(df["periodo_carga"].unique().tolist())
        self.periodo_inicio = periodos[0]  if periodos else ""
        self.periodo_fin    = periodos[-1] if periodos else ""

        # ---- Por localidad ----
        g = df.groupby("localidad").agg(
            ingresos=("total_pagado_con_metodo_de_pago", "sum"),
            ventas=("no_de_venta", "nunique"),
            cantidad=("cantidad", "sum"),
            clientes=("id_del_cliente", "nunique"),
            descuentos=("cantidad_de_descuento", "sum"),
        ).reset_index()
        g["ticket_prom"]   = (g["ingresos"] / g["ventas"].replace(0, 1)).round(0)
        g["participacion"] = (g["ingresos"] / g["ingresos"].sum() * 100).round(1)
        self.por_localidad = g.sort_values("ingresos", ascending=False)

        # ---- Tendencia mensual total ----
        tm = df.groupby("periodo_carga").agg(
            ingresos=("total_pagado_con_metodo_de_pago", "sum"),
            ventas=("no_de_venta", "nunique"),
            clientes=("id_del_cliente", "nunique"),
        ).reset_index().sort_values("periodo_carga")
        tm["mom"] = tm["ingresos"].pct_change() * 100
        self.tendencia = tm

        # ---- Tendencia por localidad ----
        tml = (
            df.groupby(["periodo_carga", "localidad"])["total_pagado_con_metodo_de_pago"]
            .sum()
            .reset_index()
        )
        self.tendencia_loc = tml

        # ---- Top artículos ----
        art = df.groupby("nombre_del_articulo").agg(
            ingresos=("total_pagado_con_metodo_de_pago", "sum"),
            cantidad=("cantidad", "sum"),
            ventas=("no_de_venta", "nunique"),
        ).reset_index()
        art["precio_prom"] = (art["ingresos"] / art["cantidad"].replace(0, 1)).round(0)
        art["pct"]         = (art["ingresos"] / art["ingresos"].sum() * 100).round(1)
        self.top_articulos = art.sort_values("ingresos", ascending=False).head(20)

        # ---- Formas de pago ----
        fp = df.groupby("forma_de_pago").agg(
            ingresos=("total_pagado_con_metodo_de_pago", "sum"),
            ventas=("no_de_venta", "nunique"),
        ).reset_index()
        fp["pct"] = (fp["ingresos"] / fp["ingresos"].sum() * 100).round(1)
        self.formas_pago = fp.sort_values("ingresos", ascending=False)

        # ---- Detalle (3 000 filas más recientes) ----
        cols = [
            "fecha", "periodo_carga", "localidad", "cliente", "no_de_venta",
            "nombre_del_articulo", "cantidad", "total_pagado_con_metodo_de_pago",
            "forma_de_pago", "cantidad_de_descuento",
        ]
        cols_ok = [c for c in cols if c in df.columns]
        det = df[cols_ok].sort_values("fecha", ascending=False).head(3000).copy()
        det["fecha"] = det["fecha"].dt.strftime("%Y-%m-%d")
        self.detalle = det

    # ------------------------------------------------------------------
    # Serialización JSON
    # ------------------------------------------------------------------

    def _to_json(self) -> str:
        def _safe_float(v):
            try:
                f = float(v)
                return 0 if (math.isnan(f) or math.isinf(f)) else f
            except Exception:
                return 0

        data: dict = {
            "meta": {
                "titulo":            self.titulo,
                "periodo_inicio":    self.periodo_inicio,
                "periodo_fin":       self.periodo_fin,
                "ingresos":          round(self.ingresos),
                "num_ventas":        self.num_ventas,
                "ticket_prom":       round(self.ticket_prom),
                "articulos_vendidos": self.articulos_vend,
                "clientes_unicos":   self.clientes_unicos,
                "descuentos":        round(self.descuentos),
                "pct_descuento":     self.pct_desc,
            },
            "localidades":   [],
            "tendencia":     [],
            "tendencia_loc": [],
            "top_articulos": [],
            "formas_pago":   [],
            "detalle":       [],
        }

        for _, r in self.por_localidad.iterrows():
            data["localidades"].append({
                "loc": str(r["localidad"]),
                "ing": round(_safe_float(r["ingresos"])),
                "ven": int(r["ventas"]),
                "tkt": round(_safe_float(r["ticket_prom"])),
                "pct": round(_safe_float(r["participacion"]), 1),
                "qty": int(r.get("cantidad", 0)),
                "cli": int(r.get("clientes", 0)),
                "dsc": round(_safe_float(r.get("descuentos", 0))),
            })

        for _, r in self.tendencia.iterrows():
            data["tendencia"].append({
                "p":   str(r["periodo_carga"]),
                "ing": round(_safe_float(r["ingresos"])),
                "ven": int(r["ventas"]),
                "cli": int(r.get("clientes", 0)),
                "mom": round(_safe_float(r["mom"]), 1),
            })

        for _, r in self.tendencia_loc.iterrows():
            data["tendencia_loc"].append({
                "p":   str(r["periodo_carga"]),
                "loc": str(r["localidad"]),
                "ing": round(_safe_float(r["total_pagado_con_metodo_de_pago"])),
            })

        for _, r in self.top_articulos.iterrows():
            data["top_articulos"].append({
                "art": str(r["nombre_del_articulo"]),
                "ing": round(_safe_float(r["ingresos"])),
                "qty": int(r.get("cantidad", 0)),
                "ven": int(r.get("ventas", 0)),
                "pp":  round(_safe_float(r.get("precio_prom", 0))),
                "pct": round(_safe_float(r.get("pct", 0)), 1),
            })

        for _, r in self.formas_pago.iterrows():
            data["formas_pago"].append({
                "forma": str(r["forma_de_pago"]),
                "ing":   round(_safe_float(r["ingresos"])),
                "ven":   int(r["ventas"]),
                "pct":   round(_safe_float(r["pct"]), 1),
            })

        for _, r in self.detalle.iterrows():
            data["detalle"].append({
                "f":    str(r.get("fecha", "")),
                "p":    str(r.get("periodo_carga", "")),
                "loc":  str(r.get("localidad", "")),
                "cli":  str(r.get("cliente", "")),
                "ven":  str(r.get("no_de_venta", "")),
                "art":  str(r.get("nombre_del_articulo", "")),
                "qty":  int(r.get("cantidad", 0)),
                "tot":  round(_safe_float(r.get("total_pagado_con_metodo_de_pago", 0))),
                "pago": str(r.get("forma_de_pago", "")),
                "dsc":  round(_safe_float(r.get("cantidad_de_descuento", 0))),
            })

        return json.dumps(data, ensure_ascii=False, default=str)

    # ------------------------------------------------------------------
    # Generación HTML
    # ------------------------------------------------------------------

    def generar_html(self, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        datos_json = self._to_json()
        html_content = (
            _TEMPLATE
            .replace("__DATOS__",  datos_json)
            .replace("__USER__",   self.usuario)
            .replace("__PASS__",   self.password)
            .replace("__TITULO__", self.titulo)
        )
        output_path.write_text(html_content, encoding="utf-8")
        print(f"  [Ventas] Dashboard guardado: {output_path}")


# ==============================================================================
# HTML TEMPLATE
# ==============================================================================

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__TITULO__</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;0,600;0,700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {
  --bg:      #0b0e13;
  --card:    #141922;
  --border:  #1e2a3a;
  --surface: #1b2231;
  --text:    #e2e8f0;
  --muted:   #64748b;
  --em:      #10b981;
  --em2:     #34d399;
  --cyan:    #38bdf8;
  --amber:   #f59e0b;
  --red:     #ef4444;
  --violet:  #a78bfa;
  --radius:  12px;
  --shadow:  0 4px 24px rgba(0,0,0,.4);
}
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
html { scroll-behavior:smooth; }
body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; font-size:15px; line-height:1.5; }

/* LOGIN */
#login-screen {
  position:fixed; inset:0; background:var(--bg); display:flex;
  align-items:center; justify-content:center; z-index:9999;
}
.login-box {
  background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
  padding:40px 48px; width:100%; max-width:400px; box-shadow:var(--shadow); text-align:center;
}
.login-icon { font-size:2.4rem; margin-bottom:4px; }
.login-title { font-size:1.3rem; font-weight:700; color:var(--em); margin-bottom:4px; }
.login-sub { color:var(--muted); font-size:.84rem; margin-bottom:28px; }
.login-box input {
  width:100%; background:#0d111a; border:1px solid var(--border); border-radius:8px;
  padding:10px 14px; color:var(--text); font-size:.95rem; margin-bottom:12px;
  outline:none; transition:border-color .2s;
}
.login-box input:focus { border-color:var(--em); }
.login-btn {
  width:100%; background:var(--em); color:#fff; border:none; border-radius:8px;
  padding:11px; font-size:1rem; font-weight:600; cursor:pointer;
  transition:opacity .2s; margin-top:4px;
}
.login-btn:hover { opacity:.88; }
.login-err { color:var(--red); font-size:.82rem; margin-top:10px; min-height:1.2em; }

/* NAV */
nav {
  position:sticky; top:0; z-index:100;
  background:#0d111aee; backdrop-filter:blur(14px);
  border-bottom:1px solid var(--border);
  display:flex; align-items:center; padding:0 28px; height:52px; gap:0;
}
.nav-brand { font-size:.95rem; font-weight:700; color:var(--em); margin-right:20px; white-space:nowrap; letter-spacing:-.3px; }
.nav-links { display:flex; gap:2px; flex:1; overflow-x:auto; }
nav a { color:var(--muted); font-size:.81rem; font-weight:500; padding:7px 11px; border-radius:6px; transition:color .15s,background .15s; white-space:nowrap; text-decoration:none; }
nav a:hover,nav a.active { color:var(--text); background:var(--surface); }
.nav-right { margin-left:auto; display:flex; align-items:center; gap:14px; }
.nav-period { font-size:.74rem; color:var(--muted); white-space:nowrap; font-family:'JetBrains Mono',monospace; }
.logout-btn {
  background:transparent; border:1px solid var(--border); color:var(--muted);
  border-radius:6px; padding:5px 12px; font-size:.78rem; cursor:pointer;
  transition:border-color .15s, color .15s; white-space:nowrap;
}
.logout-btn:hover { border-color:var(--red); color:var(--red); }

/* LAYOUT */
main { max-width:1380px; margin:0 auto; padding:32px 24px 80px; }
section { margin-bottom:56px; }
.sec-title {
  font-size:1.05rem; font-weight:700; color:var(--text);
  margin-bottom:20px; display:flex; align-items:center; gap:10px;
}
.sec-title .badge {
  font-size:.7rem; font-weight:600; background:var(--em); color:#fff;
  padding:2px 8px; border-radius:20px; letter-spacing:.04em;
}
.sec-title::after { content:''; flex:1; height:1px; background:var(--border); }

/* KPI CARDS */
.kpi-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:14px; }
@media(max-width:1100px) { .kpi-grid { grid-template-columns:repeat(3,1fr); } }
@media(max-width:640px)  { .kpi-grid { grid-template-columns:repeat(2,1fr); } }
.kpi-card {
  background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
  padding:20px 18px; position:relative; overflow:hidden;
  transition:border-color .2s, box-shadow .2s;
}
.kpi-card:hover { border-color:var(--em); box-shadow:0 0 0 1px var(--em)22; }
.kpi-card::before { content:''; position:absolute; top:0; left:0; right:0; height:3px; border-radius:var(--radius) var(--radius) 0 0; }
.kpi-card.em::before  { background:linear-gradient(90deg,var(--em),var(--em2)); }
.kpi-card.cy::before  { background:var(--cyan); }
.kpi-card.am::before  { background:var(--amber); }
.kpi-card.vi::before  { background:var(--violet); }
.kpi-card.re::before  { background:var(--red); }
.kpi-label { font-size:.71rem; font-weight:600; text-transform:uppercase; letter-spacing:.07em; color:var(--muted); margin-bottom:9px; }
.kpi-value { font-size:1.15rem; font-weight:700; font-family:'JetBrains Mono',monospace; color:var(--text); line-height:1.2; word-break:break-all; }
.kpi-sub { font-size:.77rem; color:var(--muted); margin-top:6px; }

/* FILTER BAR */
.filter-bar { display:flex; gap:10px; flex-wrap:wrap; margin-bottom:18px; align-items:center; }
.filter-bar label { font-size:.78rem; color:var(--muted); }
.filter-bar select, .filter-bar input {
  background:var(--card); border:1px solid var(--border); border-radius:8px;
  color:var(--text); padding:7px 12px; font-size:.83rem; outline:none;
  cursor:pointer; min-width:150px; transition:border-color .2s;
}
.filter-bar select:focus, .filter-bar input:focus { border-color:var(--em); }

/* CHART GRIDS */
.chart-grid { display:grid; gap:20px; }
.chart-grid.col2 { grid-template-columns:1fr 1fr; }
.chart-grid.col3 { grid-template-columns:1fr 1fr 1fr; }
@media(max-width:960px) { .chart-grid.col2,.chart-grid.col3 { grid-template-columns:1fr; } }
.chart-card {
  background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
  padding:22px 22px 20px; box-shadow:var(--shadow);
}
.chart-card-title { font-size:.78rem; font-weight:600; text-transform:uppercase; letter-spacing:.06em; color:var(--muted); margin-bottom:16px; }
.chart-wrap canvas { max-height:280px; }
.chart-wrap.tall canvas { max-height:340px; }
.chart-wrap.xtall canvas { max-height:460px; }

/* TABLES */
.table-wrap { overflow-x:auto; border-radius:8px; }
table { width:100%; border-collapse:collapse; font-size:.84rem; }
thead th {
  background:var(--surface); color:var(--muted); font-size:.69rem;
  font-weight:600; text-transform:uppercase; letter-spacing:.07em;
  padding:10px 14px; text-align:left; border-bottom:1px solid var(--border); white-space:nowrap;
}
tbody tr { border-bottom:1px solid var(--border); transition:background .12s; }
tbody tr:hover { background:var(--surface); }
tbody td { padding:10px 14px; color:var(--text); }
.mono { font-family:'JetBrains Mono',monospace; }
.nowrap { white-space:nowrap; }

/* TAGS */
.tag { display:inline-block; padding:2px 9px; border-radius:4px; font-size:.7rem; font-weight:700; text-transform:uppercase; letter-spacing:.04em; }
.tag.em { background:#10b98118; color:var(--em); }
.tag.am { background:#f59e0b18; color:var(--amber); }
.tag.re { background:#ef444418; color:var(--red); }
.tag.cy { background:#38bdf818; color:var(--cyan); }
.tag.vi { background:#a78bfa18; color:var(--violet); }

/* MOM */
.mom-pos { color:var(--em); font-weight:600; }
.mom-neg { color:var(--red); font-weight:600; }

/* PROGRESS BAR */
.pbar-wrap { display:inline-flex; align-items:center; gap:6px; }
.pbar { background:var(--surface); border-radius:20px; overflow:hidden; width:80px; height:5px; display:inline-block; vertical-align:middle; }
.pbar-inner { height:100%; border-radius:20px; }
.pbar-label { font-size:.76rem; color:var(--muted); }

/* RANK */
.rank { font-weight:700; font-size:.9rem; }
.rank-1 { color:#fbbf24; }
.rank-2 { color:#94a3b8; }
.rank-3 { color:#d97706; }

/* PAGINATION */
.pag { display:flex; gap:6px; justify-content:flex-end; margin-top:14px; flex-wrap:wrap; align-items:center; }
.pag-info { font-size:.77rem; color:var(--muted); margin-right:8px; }
.pag button {
  background:var(--surface); border:1px solid var(--border); color:var(--text);
  border-radius:6px; padding:4px 11px; font-size:.78rem; cursor:pointer; transition:background .15s;
}
.pag button:hover,.pag button.active { background:var(--em); color:#fff; border-color:var(--em); }

/* SCROLLBAR */
::-webkit-scrollbar { width:5px; height:5px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:var(--border); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:var(--muted); }
</style>
</head>
<body>

<!-- ===== LOGIN ===== -->
<div id="login-screen">
  <div class="login-box">
    <div class="login-icon">🏪</div>
    <div class="login-title">Dashboard de Ventas</div>
    <div class="login-sub">__TITULO__</div>
    <input type="text" id="lu" placeholder="Usuario" autocomplete="username">
    <input type="password" id="lp" placeholder="Contraseña" autocomplete="current-password">
    <button class="login-btn" onclick="doLogin()">Ingresar</button>
    <div class="login-err" id="lerr"></div>
  </div>
</div>

<!-- ===== NAV ===== -->
<nav id="main-nav" style="display:none">
  <span class="nav-brand">🏪 Ventas</span>
  <div class="nav-links">
    <a href="#resumen"    class="active">Resumen</a>
    <a href="#sucursales">Sucursales</a>
    <a href="#tendencia"> Tendencia</a>
    <a href="#articulos"> Artículos</a>
    <a href="#pagos">     Pagos</a>
    <a href="#detalle">   Detalle</a>
  </div>
  <div class="nav-right">
    <span class="nav-period" id="nav-period"></span>
    <button class="logout-btn" onclick="doLogout()">Cerrar sesión</button>
  </div>
</nav>

<!-- ===== MAIN ===== -->
<main id="main-content" style="display:none">

<!-- RESUMEN -->
<section id="resumen">
  <div class="sec-title">Resumen General <span class="badge">KPIs</span></div>
  <div class="kpi-grid" id="kpi-grid"></div>
</section>

<!-- SUCURSALES -->
<section id="sucursales">
  <div class="sec-title">Rendimiento por Sucursal</div>
  <div class="chart-grid col2">
    <div class="chart-card">
      <div class="chart-card-title">Ingresos por Sucursal ($)</div>
      <div class="chart-wrap tall"><canvas id="chart-suc-bar"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Participación en Ventas Totales</div>
      <div class="chart-wrap tall"><canvas id="chart-suc-donut"></canvas></div>
    </div>
  </div>
  <div class="chart-card" style="margin-top:20px">
    <div class="chart-card-title">Ranking de Sucursales</div>
    <div class="table-wrap"><table id="tbl-suc"></table></div>
  </div>
</section>

<!-- TENDENCIA -->
<section id="tendencia">
  <div class="sec-title">Tendencia Mensual</div>
  <div class="chart-card">
    <div class="chart-card-title">Ingresos Mensuales — Total Consolidado</div>
    <div class="chart-wrap"><canvas id="chart-tend"></canvas></div>
  </div>
  <div class="chart-card" style="margin-top:20px">
    <div class="chart-card-title">Ingresos Mensuales — Por Sucursal</div>
    <div class="chart-wrap tall"><canvas id="chart-tend-loc"></canvas></div>
  </div>
  <div class="chart-card" style="margin-top:20px">
    <div class="chart-card-title">Variación Mensual (MoM)</div>
    <div class="table-wrap"><table id="tbl-tend"></table></div>
  </div>
</section>

<!-- ARTÍCULOS -->
<section id="articulos">
  <div class="sec-title">Top Artículos</div>
  <div class="chart-grid col2">
    <div class="chart-card">
      <div class="chart-card-title">Top 15 — Por Ingresos ($)</div>
      <div class="chart-wrap xtall"><canvas id="chart-art-ing"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Top 15 — Por Unidades Vendidas</div>
      <div class="chart-wrap xtall"><canvas id="chart-art-qty"></canvas></div>
    </div>
  </div>
  <div class="chart-card" style="margin-top:20px">
    <div class="chart-card-title">Ranking Completo (Top 20)</div>
    <div class="table-wrap"><table id="tbl-art"></table></div>
  </div>
</section>

<!-- PAGOS -->
<section id="pagos">
  <div class="sec-title">Formas de Pago</div>
  <div class="chart-grid col2">
    <div class="chart-card">
      <div class="chart-card-title">Distribución por Monto</div>
      <div class="chart-wrap"><canvas id="chart-pago-donut"></canvas></div>
    </div>
    <div class="chart-card">
      <div class="chart-card-title">Detalle por Forma de Pago</div>
      <div class="table-wrap" style="margin-top:4px"><table id="tbl-pago"></table></div>
    </div>
  </div>
</section>

<!-- DETALLE -->
<section id="detalle">
  <div class="sec-title">Detalle de Ventas</div>
  <div class="filter-bar">
    <label>Sucursal</label>
    <select id="fil-loc" onchange="renderDetalle()"><option value="">Todas</option></select>
    <label>Mes</label>
    <select id="fil-mes" onchange="renderDetalle()"><option value="">Todos</option></select>
    <label>Buscar</label>
    <input type="text" id="fil-txt" placeholder="Cliente / Artículo / N° Venta…" oninput="renderDetalle()" style="min-width:220px">
  </div>
  <div class="chart-card">
    <div class="table-wrap"><table id="tbl-det"></table></div>
    <div class="pag" id="pag-det"></div>
  </div>
</section>

</main>

<script>
const D = __DATOS__;
const _AUTH = {u:"__USER__", p:"__PASS__"};

const PALETTE = [
  "#10b981","#38bdf8","#f59e0b","#a78bfa","#f472b6",
  "#34d399","#60a5fa","#fb923c","#c084fc","#4ade80",
  "#fbbf24","#818cf8","#2dd4bf","#f87171","#e879f9"
];

// ---- Formato ----
const clp  = v => { if(v==null||isNaN(v)) return '$0'; return '$'+Math.round(v).toLocaleString('es-CL'); };
const num  = v => (v||0).toLocaleString('es-CL');
const pct  = v => (v||0).toFixed(1)+'%';
const momH = v => {
  if(!v || isNaN(v)) return '<span style="color:var(--muted)">—</span>';
  const s = v>0?'+':''; const c = v>0?'mom-pos':'mom-neg';
  return `<span class="${c}">${s}${v.toFixed(1)}%</span>`;
};
const truncate = (s,n) => s&&s.length>n ? s.slice(0,n-1)+'…' : (s||'');
const pbar = (pct,color) =>
  `<div class="pbar-wrap"><div class="pbar"><div class="pbar-inner" style="width:${Math.min(pct,100)}%;background:${color}"></div></div><span class="pbar-label">${pct.toFixed(1)}%</span></div>`;

// ---- Login ----
function doLogin(){
  const u=document.getElementById('lu').value.trim();
  const p=document.getElementById('lp').value;
  if(u===_AUTH.u && p===_AUTH.p){
    document.getElementById('login-screen').style.display='none';
    document.getElementById('main-nav').style.display='flex';
    document.getElementById('main-content').style.display='block';
    initDashboard();
  } else {
    document.getElementById('lerr').textContent = 'Usuario o contraseña incorrectos.';
  }
}
document.addEventListener('keydown', e => { if(e.key==='Enter') doLogin(); });

function doLogout(){
  document.getElementById('main-nav').style.display='none';
  document.getElementById('main-content').style.display='none';
  document.getElementById('login-screen').style.display='flex';
  document.getElementById('lu').value='';
  document.getElementById('lp').value='';
  document.getElementById('lerr').textContent='';
}

// ---- Init ----
function initDashboard(){
  document.getElementById('nav-period').textContent = D.meta.periodo_inicio + ' → ' + D.meta.periodo_fin;
  renderKPIs();
  renderSucursales();
  renderTendencia();
  renderArticulos();
  renderPagos();
  initFiltros();
  renderDetalle();
  // Nav scroll spy
  const secs  = document.querySelectorAll('section[id]');
  const links = document.querySelectorAll('nav a');
  new IntersectionObserver(entries => {
    entries.forEach(e => {
      if(e.isIntersecting){
        links.forEach(a=>a.classList.remove('active'));
        const l = document.querySelector(`nav a[href="#${e.target.id}"]`);
        if(l) l.classList.add('active');
      }
    });
  }, {threshold:.25}).observe;
  secs.forEach(s=>new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting){
        links.forEach(a=>a.classList.remove('active'));
        const l=document.querySelector(`nav a[href="#${e.target.id}"]`);
        if(l) l.classList.add('active');
      }
    });
  },{threshold:.25}).observe(s));
}

// ---- KPIs ----
function renderKPIs(){
  const m = D.meta;
  const cards = [
    {label:'Ingresos Totales',     val:clp(m.ingresos),          sub:`${m.periodo_inicio} — ${m.periodo_fin}`, color:'em'},
    {label:'N° Ventas',            val:num(m.num_ventas),         sub:'boletas / tickets únicos',              color:'cy'},
    {label:'Ticket Promedio',      val:clp(m.ticket_prom),        sub:'ingreso por venta',                     color:'am'},
    {label:'Artículos Vendidos',   val:num(m.articulos_vendidos), sub:'unidades totales',                      color:'vi'},
    {label:'Clientes Únicos',      val:num(m.clientes_unicos),    sub:'IDs distintos atendidos',               color:'cy'},
    {label:'Descuentos Otorgados', val:clp(m.descuentos),         sub:`${m.pct_descuento}% del monto bruto`,  color:'re'},
  ];
  document.getElementById('kpi-grid').innerHTML = cards.map(c=>
    `<div class="kpi-card ${c.color}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.val}</div>
      <div class="kpi-sub">${c.sub}</div>
    </div>`
  ).join('');
}

// ---- Sucursales ----
function renderSucursales(){
  const locs   = D.localidades;
  const labels = locs.map(l=>l.loc);
  const ings   = locs.map(l=>l.ing);
  const colors = labels.map((_,i)=>PALETTE[i%PALETTE.length]);

  new Chart(document.getElementById('chart-suc-bar'),{
    type:'bar',
    data:{ labels, datasets:[{label:'Ingresos',data:ings,backgroundColor:colors,borderRadius:6}] },
    options:{
      indexAxis:'y', responsive:true, maintainAspectRatio:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>clp(c.raw)}}},
      scales:{
        x:{ticks:{callback:v=>clp(v),font:{size:10}},grid:{color:'#1e2a3a'}},
        y:{grid:{display:false},ticks:{font:{size:11}}}
      }
    }
  });

  new Chart(document.getElementById('chart-suc-donut'),{
    type:'doughnut',
    data:{ labels, datasets:[{data:ings,backgroundColor:colors,borderWidth:2,borderColor:'#141922'}] },
    options:{
      responsive:true,
      plugins:{
        legend:{position:'right',labels:{color:'#e2e8f0',boxWidth:12,padding:10,font:{size:11}}},
        tooltip:{callbacks:{label:c=>`${c.label}: ${pct(c.dataset.data[c.dataIndex]/c.dataset.data.reduce((a,b)=>a+b,0)*100)}`}}
      }
    }
  });

  const rankSym = ['🥇','🥈','🥉'];
  const rows = locs.map((l,i)=>`<tr>
    <td class="nowrap"><span class="rank rank-${i<3?i+1:''}">${rankSym[i]||i+1}</span></td>
    <td class="nowrap">${l.loc}</td>
    <td class="mono nowrap">${clp(l.ing)}</td>
    <td class="nowrap">${pbar(l.pct,colors[i])}</td>
    <td class="mono nowrap">${num(l.ven)}</td>
    <td class="mono nowrap">${clp(l.tkt)}</td>
    <td class="mono nowrap">${num(l.cli)}</td>
    <td class="mono nowrap" style="color:var(--red)">${l.dsc>0?clp(l.dsc):'—'}</td>
  </tr>`).join('');
  document.getElementById('tbl-suc').innerHTML =
    `<thead><tr><th>#</th><th>Sucursal</th><th>Ingresos</th><th>Participación</th><th>Ventas</th><th>Ticket Prom.</th><th>Clientes</th><th>Descuentos</th></tr></thead><tbody>${rows}</tbody>`;
}

// ---- Tendencia ----
function renderTendencia(){
  const t = D.tendencia;
  const labels = t.map(r=>r.p);

  new Chart(document.getElementById('chart-tend'),{
    type:'line',
    data:{ labels, datasets:[{
      label:'Ingresos', data:t.map(r=>r.ing),
      borderColor:'#10b981', backgroundColor:'#10b98115',
      fill:true, tension:.35, pointBackgroundColor:'#10b981', pointRadius:5, pointHoverRadius:7
    }]},
    options:{
      responsive:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>clp(c.raw)}}},
      scales:{
        y:{ticks:{callback:v=>clp(v)},grid:{color:'#1e2a3a'}},
        x:{grid:{color:'#1e2a3a'}}
      }
    }
  });

  // Por sucursal
  const allLocs = [...new Set(D.tendencia_loc.map(r=>r.loc))].sort();
  const allP    = [...new Set(D.tendencia_loc.map(r=>r.p))].sort();
  const dsLoc   = allLocs.map((loc,i)=>({
    label: loc,
    data: allP.map(p=>{ const row=D.tendencia_loc.find(r=>r.p===p&&r.loc===loc); return row?row.ing:0; }),
    borderColor: PALETTE[i%PALETTE.length],
    backgroundColor:'transparent',
    tension:.35, pointRadius:3, borderWidth:2,
  }));
  new Chart(document.getElementById('chart-tend-loc'),{
    type:'line',
    data:{ labels:allP, datasets:dsLoc },
    options:{
      responsive:true,
      plugins:{
        legend:{position:'right',labels:{color:'#e2e8f0',boxWidth:10,padding:8,font:{size:11}}},
        tooltip:{callbacks:{label:c=>`${c.dataset.label}: ${clp(c.raw)}`}}
      },
      scales:{y:{ticks:{callback:v=>clp(v)},grid:{color:'#1e2a3a'}},x:{grid:{color:'#1e2a3a'}}}
    }
  });

  // MoM table
  const rows = t.map(r=>`<tr>
    <td class="mono nowrap">${r.p}</td>
    <td class="mono nowrap">${clp(r.ing)}</td>
    <td class="nowrap">${momH(r.mom)}</td>
    <td class="mono nowrap">${num(r.ven)}</td>
    <td class="mono nowrap">${num(r.cli)}</td>
  </tr>`).join('');
  document.getElementById('tbl-tend').innerHTML =
    `<thead><tr><th>Periodo</th><th>Ingresos</th><th>Var. MoM</th><th>Ventas</th><th>Clientes</th></tr></thead><tbody>${rows}</tbody>`;
}

// ---- Artículos ----
function renderArticulos(){
  const arts  = D.top_articulos;
  const top15 = arts.slice(0,15);
  const labs  = top15.map(a=>truncate(a.art,30));

  new Chart(document.getElementById('chart-art-ing'),{
    type:'bar',
    data:{ labels:labs, datasets:[{label:'Ingresos',data:top15.map(a=>a.ing),backgroundColor:'#10b981',borderRadius:4}] },
    options:{
      indexAxis:'y', responsive:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>clp(c.raw)}}},
      scales:{x:{ticks:{callback:v=>clp(v),font:{size:10}},grid:{color:'#1e2a3a'}},y:{grid:{display:false},ticks:{font:{size:10}}}}
    }
  });

  new Chart(document.getElementById('chart-art-qty'),{
    type:'bar',
    data:{ labels:labs, datasets:[{label:'Unidades',data:top15.map(a=>a.qty),backgroundColor:'#38bdf8',borderRadius:4}] },
    options:{
      indexAxis:'y', responsive:true,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>num(c.raw)+' uds.'}}},
      scales:{x:{grid:{color:'#1e2a3a'},ticks:{font:{size:10}}},y:{grid:{display:false},ticks:{font:{size:10}}}}
    }
  });

  const rankSym = ['🥇','🥈','🥉'];
  const rows = arts.map((a,i)=>`<tr>
    <td class="nowrap"><span class="rank rank-${i<3?i+1:''}">${rankSym[i]||i+1}</span></td>
    <td>${a.art}</td>
    <td class="mono nowrap">${clp(a.ing)}</td>
    <td class="nowrap">${pbar(a.pct,'#10b981')}</td>
    <td class="mono nowrap">${num(a.qty)}</td>
    <td class="mono nowrap">${clp(a.pp)}</td>
    <td class="mono nowrap">${num(a.ven)}</td>
  </tr>`).join('');
  document.getElementById('tbl-art').innerHTML =
    `<thead><tr><th>#</th><th>Artículo</th><th>Ingresos</th><th>Participación</th><th>Cantidad</th><th>Precio Prom.</th><th>Ventas</th></tr></thead><tbody>${rows}</tbody>`;
}

// ---- Pagos ----
function renderPagos(){
  const fp     = D.formas_pago;
  const labels = fp.map(f=>f.forma);
  const data   = fp.map(f=>f.ing);
  const colors = labels.map((_,i)=>PALETTE[i%PALETTE.length]);
  const total  = data.reduce((a,b)=>a+b,0);

  new Chart(document.getElementById('chart-pago-donut'),{
    type:'doughnut',
    data:{ labels, datasets:[{data,backgroundColor:colors,borderWidth:2,borderColor:'#141922'}] },
    options:{
      responsive:true,
      plugins:{
        legend:{position:'bottom',labels:{color:'#e2e8f0',boxWidth:12,padding:12,font:{size:11}}},
        tooltip:{callbacks:{label:c=>`${c.label}: ${clp(c.raw)} (${pct(c.raw/total*100)})`}}
      }
    }
  });

  const tagColors = ['em','cy','am','vi','re'];
  const rows = fp.map((f,i)=>`<tr>
    <td class="nowrap"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${colors[i]};margin-right:8px;vertical-align:middle"></span>${f.forma}</td>
    <td class="mono nowrap">${clp(f.ing)}</td>
    <td class="mono nowrap">${num(f.ven)}</td>
    <td class="nowrap"><span class="tag ${tagColors[i%tagColors.length]}">${f.pct.toFixed(1)}%</span></td>
  </tr>`).join('');
  document.getElementById('tbl-pago').innerHTML =
    `<thead><tr><th>Forma de Pago</th><th>Monto</th><th>Ventas</th><th>Participación</th></tr></thead><tbody>${rows}</tbody>`;
}

// ---- Detalle ----
let _page = 0;
const PAGE_SIZE = 50;
let _filtered = [];

function initFiltros(){
  const locs  = [...new Set(D.detalle.map(r=>r.loc).filter(Boolean))].sort();
  const meses = [...new Set(D.detalle.map(r=>r.p).filter(Boolean))].sort();
  const sLoc  = document.getElementById('fil-loc');
  const sMes  = document.getElementById('fil-mes');
  locs.forEach(l=>{ const o=document.createElement('option'); o.value=l; o.textContent=l; sLoc.appendChild(o); });
  meses.forEach(m=>{ const o=document.createElement('option'); o.value=m; o.textContent=m; sMes.appendChild(o); });
}

function renderDetalle(){
  const loc = document.getElementById('fil-loc').value;
  const mes = document.getElementById('fil-mes').value;
  const txt = document.getElementById('fil-txt').value.toLowerCase().trim();
  _filtered = D.detalle.filter(r=>{
    if(loc && r.loc!==loc) return false;
    if(mes && r.p!==mes)   return false;
    if(txt && ![r.cli||'',r.art||'',String(r.ven||'')].some(s=>s.toLowerCase().includes(txt))) return false;
    return true;
  });
  _page = 0;
  renderPage();
}

function renderPage(){
  const start = _page * PAGE_SIZE;
  const rows  = _filtered.slice(start, start+PAGE_SIZE).map(r=>`<tr>
    <td class="mono nowrap">${r.f}</td>
    <td class="nowrap">${r.loc}</td>
    <td class="nowrap">${truncate(r.cli,25)}</td>
    <td class="mono nowrap">${r.ven}</td>
    <td>${truncate(r.art,42)}</td>
    <td class="mono nowrap">${num(r.qty)}</td>
    <td class="mono nowrap">${clp(r.tot)}</td>
    <td class="nowrap"><span class="tag cy" style="font-size:.67rem">${r.pago}</span></td>
    <td class="mono nowrap" style="color:var(--red)">${r.dsc>0?clp(r.dsc):'—'}</td>
  </tr>`).join('');
  document.getElementById('tbl-det').innerHTML =
    `<thead><tr><th>Fecha</th><th>Sucursal</th><th>Cliente</th><th>N° Venta</th><th>Artículo</th><th>Cant.</th><th>Total</th><th>Forma Pago</th><th>Descuento</th></tr></thead><tbody>${rows}</tbody>`;

  const pages = Math.ceil(_filtered.length/PAGE_SIZE);
  let pag = `<span class="pag-info">${_filtered.length.toLocaleString('es-CL')} registros</span>`;
  const visPages = Math.min(pages, 20);
  for(let i=0;i<visPages;i++){
    pag += `<button class="${i===_page?'active':''}" onclick="_page=${i};renderPage()">${i+1}</button>`;
  }
  if(pages>20) pag += `<span style="color:var(--muted);font-size:.77rem"> … ${pages} páginas total</span>`;
  document.getElementById('pag-det').innerHTML = pag;
}
</script>
</body>
</html>"""
