"""Informe de patrimonio inmobiliario para bancos (2 páginas, PDF).

Uso: python3 scripts/build_informe_bancos.py [fecha dd-mm-aaaa]
Lee el Registro v2 embebido en dashboard/index.html (correr antes sync_dashboard.py),
escribe informe/patrimonio_inmobiliario.html y lo imprime a PDF con Playwright (node).
Separa las propiedades en cartera (con fecha de compra) de las que están en compra.
"""
import base64, datetime as dt, json, re, subprocess, sys, html as H
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "informe"
OUT.mkdir(exist_ok=True)
s = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
reg = json.loads(re.search(r"/\*REG_START\*/(.*?)/\*REG_END\*/", s, re.S).group(1))
hdr = reg["header"]
rows = [dict(zip(hdr, r)) for r in reg["rows"]]
fecha = sys.argv[1] if len(sys.argv) > 1 else dt.date.today().strftime("%d-%m-%Y")
MESES = "enero febrero marzo abril mayo junio julio agosto septiembre octubre noviembre diciembre".split()
d, m, y = fecha.split("-")
fecha_larga = f"{int(d)} de {MESES[int(m)-1]} de {y}"

def num(v):
    v = str(v or "").strip()
    if v in ("", "-"):
        return 0.0 if v == "-" else None
    try:
        return float(v.replace(",", "."))
    except ValueError:
        return None

NAMES = {
    "P01": ("Moneda 812, Of. 705", "Santiago"),
    "P03": ("Terrazas del Parque, Of. 202", "Huechuraba"),
    "P04": ("Work Center Miraflores, Mód. 42", "Renca"),
    "P05": ("Terrazas del Parque, Of. 401", "Huechuraba"),
    "P06": ("Edificio Europa, Of. 401", "Huechuraba"),
    "P07": ("Los Talaveras 120, Depto. 405", "Ñuñoa"),
    "P08": ("Edificio Ilumina, 4 deptos.", "Recoleta"),
    "P09": ("Nueva York 25, piso 3", "Santiago"),
    "P10": ("Huérfanos 1294, Of. 51", "Santiago"),
    "P11": ("Locales La Portada", "Independencia"),
    "P12": ("Patio Mayor, Of. 331", "Huechuraba"),
    "P13": ("Av. Matta 1088-1094", "Santiago"),
    "P14": ("Matta esq. San Diego 1108-1110", "Santiago"),
    "P15": ("San Diego 1126-1130", "Santiago"),
}
TASADOR = {  # nombre corto de la fuente de valor
    "P09": "Propiteq (estimación)",
}

def short_tasador(r):
    t = TASADOR.get(r["ID"]) or r["Tasador"]
    t = re.sub(r"\s*\(.*?\)", "", t)
    t = t.replace("Perito judicial V. Correa", "Perito judicial").replace("N. Latorre para ", "").replace("Roberto Nieto", "R. Nieto").replace(" para ", " / ").replace("Banco de Chile", "Bco. de Chile")
    return t

props = []
for r in rows:
    pid = r["ID"]
    name, comuna = NAMES.get(pid, (r["Nombre / dirección"], r["Comuna"]))
    p = dict(id=pid, name=name, comuna=comuna, tipo=r["Tipo"], m2=num(r["m² útiles"]) or 0,
             val=num(r["Valor comercial (UF)"]) or 0, bank=num(r["Valor banco (UF)"]),
             debt=num(r["Saldo insoluto hoy (UF)"]) or 0, div=num(r["Dividendo mensual (UF)"]) or 0,
             banco=r["Banco"], st=r["Estado"], rent=num(r["Arriendo mensual (UF)"]) or 0,
             cost=num(r["Costo total (UF)"]), ftas=r["Fecha de tasación"], tasador=short_tasador(r),
             compra=r["Fecha de compra"])
    if p["st"] != "Arrendada":
        p["rent"] = 0
    props.append(p)

cartera = sorted([p for p in props if p["st"] != "En compra"], key=lambda p: -p["val"])
compra = sorted([p for p in props if p["st"] == "En compra"], key=lambda p: -p["val"])
V = sum(p["val"] for p in cartera); D = sum(p["debt"] for p in cartera); E = V - D
RENT = sum(p["rent"] for p in cartera); DIV = sum(p["div"] for p in cartera)
M2 = sum(p["m2"] for p in cartera)
narr = sum(1 for p in cartera if p["st"] == "Arrendada")
VC = sum(p["val"] for p in compra)

uf = lambda x: f"{x:,.0f}".replace(",", ".")
uf1 = lambda x: f"{x:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
pct = lambda x: f"{x*100:.1f}".replace(".", ",") + "%"
e = H.escape

# Composición por tipo
tipos = {}
for p in cartera:
    t = {"Oficina": "Oficinas", "Local comercial": "Locales comerciales", "Bodega": "Bodegas",
         "Departamento": "Departamentos"}.get(p["tipo"], p["tipo"])
    tipos.setdefault(t, [0, 0]); tipos[t][0] += p["val"]; tipos[t][1] += 1
tipos = sorted(tipos.items(), key=lambda kv: -kv[1][0])

comunas = {}
for p in cartera:
    c = comunas.setdefault(p["comuna"], [0, 0]); c[0] += p["val"]; c[1] += 1
comunas = sorted(comunas.items(), key=lambda kv: -kv[1][0])

# Deuda por banco
bancos = {}
for p in cartera:
    if p["debt"]:
        b = bancos.setdefault(p["banco"], [0, 0, 0]); b[0] += p["debt"]; b[1] += p["div"]; b[2] += 1
bancos = sorted(bancos.items(), key=lambda kv: -kv[1][0])

NAVY, SKY, INK, MUTED, LINE = "#153852", "#4FA3BF", "#14222e", "#5b6b78", "#dfe6eb"
SKY_SOFT = "#cfe6ee"

# Gráfico: barras horizontales apiladas patrimonio + deuda por propiedad
def bars_svg():
    W, row, top, lab = 440, 38, 4, 168
    mx = max(p["val"] for p in cartera)
    sc = (W - lab - 44) / mx
    h = top + row * len(cartera) + 22
    out = [f'<svg viewBox="0 0 {W} {h}" width="100%" role="img" aria-label="Valor, deuda y patrimonio por propiedad">']
    for i, p in enumerate(cartera):
        y = top + i * row
        eq = (p["val"] - p["debt"]) * sc; db = p["debt"] * sc
        out.append(f'<text x="{lab-8}" y="{y+18}" text-anchor="end" class="bl">{e(p["name"])}</text>')
        out.append(f'<rect x="{lab}" y="{y+3}" width="{eq:.1f}" height="22" fill="{NAVY}" rx="2"/>')
        if db:
            out.append(f'<rect x="{lab+eq:.1f}" y="{y+3}" width="{db:.1f}" height="22" fill="{SKY_SOFT}" rx="2"/>')
        out.append(f'<text x="{lab+eq+db+6:.1f}" y="{y+18}" class="bv">{uf(p["val"])}</text>')
    yb = top + row * len(cartera) + 4
    out.append(f'<line x1="{lab}" x2="{lab}" y1="{top}" y2="{yb}" stroke="{LINE}"/>')
    out.append("</svg>")
    return "".join(out)

def donut_svg():
    import math
    R, r0, cx, cy = 58, 38, 64, 64
    cols = [NAVY, SKY, "#8fb9c9", "#9aa8b3"]
    a = -math.pi / 2; segs = []
    for i, (t, (v, n)) in enumerate(tipos):
        f = v / V; b = a + f * 2 * math.pi
        large = 1 if b - a > math.pi else 0
        p = lambda ang, rad: (cx + rad * math.cos(ang), cy + rad * math.sin(ang))
        x1, y1 = p(a, R); x2, y2 = p(b - 0.012, R); x3, y3 = p(b - 0.012, r0); x4, y4 = p(a, r0)
        segs.append(f'<path d="M{x1:.2f},{y1:.2f} A{R},{R} 0 {large} 1 {x2:.2f},{y2:.2f} L{x3:.2f},{y3:.2f} A{r0},{r0} 0 {large} 0 {x4:.2f},{y4:.2f} Z" fill="{cols[i%4]}"/>')
        a = b
    leg = "".join(f'<div class="lg"><i style="background:{cols[i%4]}"></i><span>{e(t)} <b>({n})</b></span><span class="num">{pct(v/V)}</span></div>'
                  for i, (t, (v, n)) in enumerate(tipos))
    return f'<div class="donut"><svg viewBox="0 0 128 128" width="118" height="118">{"".join(segs)}</svg><div class="legend">{leg}</div></div>'

logo = base64.b64encode((ROOT / "data/logo-kaiken.png").read_bytes()).decode()

def row_cartera(p):
    eqp = p["val"] - p["debt"]
    nota = "¹" if p["id"] == "P09" else ("²" if p["bank"] and p["bank"] < p["val"] else "")
    st = {"Arrendada": "Arrendada", "Vacante": "En habilitación"}.get(p["st"], p["st"])
    return (f'<tr><td class="l"><b>{e(p["name"])}</b><span class="sub">{e(p["comuna"])} · {e(p["tipo"]).replace('Local comercial','Locales')} · {uf(p["m2"])} m²</span></td>'
            f'<td class="l small">{e(p["tasador"])}{nota}<span class="sub">{e(p["ftas"])}</span></td>'
            f'<td class="num">{uf(p["val"])}</td><td class="num">{uf(p["debt"]) if p["debt"] else "—"}</td>'
            f'<td class="num b">{uf(eqp)}</td><td class="l small nw">{e(p["banco"]) if p["debt"] else "Sin deuda"}</td>'
            f'<td class="l small nw">{st}</td><td class="num">{uf1(p["rent"]) if p["rent"] else "—"}</td></tr>')

def row_compra(p):
    return (f'<tr><td class="l"><b>{e(p["name"])}</b><span class="sub">{e(p["comuna"])} · {e(p["tipo"])} · {uf(p["m2"])} m²</span></td>'
            f'<td class="l small">{e(p["tasador"])}<span class="sub">{e(p["ftas"])}</span></td>'
            f'<td class="num">{uf(p["val"])}</td><td class="num">{uf(p["cost"]) if p["cost"] else "—"}</td></tr>')

has_bank_note = any(p["bank"] and p["bank"] < p["val"] for p in cartera)
bank_note = ""
for p in cartera:
    if p["bank"] and p["bank"] < p["val"]:
        bank_note = f'² {e(p["name"])}: valor comercial del tasador; el valor visado por el banco es {uf(p["bank"])} UF.'

doc = f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<title>Kaiken · Patrimonio inmobiliario</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;600;700&display=swap">
<style>
@page{{size:Letter;margin:0}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:Inter,"Liberation Sans",sans-serif;color:{INK};font-size:9.4pt;line-height:1.4;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{width:8.5in;height:11in;padding:.5in .55in .45in;position:relative;overflow:hidden;page-break-after:always;display:flex;flex-direction:column;gap:14px}}
.page:last-child{{page-break-after:auto}}
h1,h2{{font-family:Montserrat,Inter,sans-serif;margin:0;color:{NAVY}}}
h1{{font-size:21pt;font-weight:700;letter-spacing:-.01em}}
h2{{font-size:10.5pt;font-weight:700;letter-spacing:.02em;text-transform:uppercase}}
.top{{display:flex;justify-content:space-between;align-items:flex-end;border-bottom:3px solid {NAVY};padding-bottom:12px}}
.top img{{height:44px}}
.meta{{text-align:right;color:{MUTED};font-size:8.6pt;line-height:1.5}}
.meta b{{color:{INK}}}
.lead{{color:{MUTED};margin:2px 0 0}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.kpi{{border:1px solid {LINE};border-radius:6px;padding:10px 12px;display:flex;flex-direction:column;gap:2px}}
.kpi .l{{font-size:7.6pt;text-transform:uppercase;letter-spacing:.07em;color:{MUTED};font-weight:600}}
.kpi .v{{font-family:Montserrat,Inter,sans-serif;font-size:16.5pt;font-weight:700;color:{NAVY};font-variant-numeric:tabular-nums}}
.kpi .v small{{font-size:9pt;font-weight:600;color:{MUTED}}}
.kpi .s{{font-size:8pt;color:{MUTED}}}
.kpi.hero{{background:{NAVY};border-color:{NAVY}}}
.kpi.hero .l,.kpi.hero .s,.kpi.hero .v small{{color:#bcd7e2}} .kpi.hero .v{{color:#fff}}
.kpi.accent{{border-top:3px solid {SKY}}}
.sec{{display:flex;flex-direction:column;gap:8px}}
.sechead{{display:flex;justify-content:space-between;align-items:baseline;border-bottom:1px solid {LINE};padding-bottom:4px}}
.sechead span{{color:{MUTED};font-size:8pt}}
.grid{{display:grid;grid-template-columns:1.45fr 1fr;gap:20px}}
.bl{{font-size:9.6px;fill:{INK}}} .bv{{font-size:9.2px;fill:{MUTED};font-variant-numeric:tabular-nums}}
.key{{display:flex;gap:14px;font-size:8pt;color:{MUTED}}} .key i{{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:5px;vertical-align:-1px}}
.donut{{display:flex;gap:12px;align-items:center}}
.legend{{display:flex;flex-direction:column;gap:5px;flex:1}}
.lg{{display:grid;grid-template-columns:10px 1fr auto;gap:6px;align-items:center;font-size:8.4pt}} .lg i{{width:10px;height:10px;border-radius:2px}} .lg b{{color:{MUTED};font-weight:500}}
table{{width:100%;border-collapse:collapse;font-size:8.2pt}} td.nw{{white-space:nowrap}}
th{{font-size:7pt;text-transform:uppercase;letter-spacing:.06em;color:{MUTED};font-weight:600;text-align:right;padding:5px 6px;border-bottom:1.5px solid {NAVY}}}
td{{padding:4px 6px;border-bottom:1px solid {LINE};text-align:right;vertical-align:top}}
th.l,td.l{{text-align:left}}
td.num,.num{{font-variant-numeric:tabular-nums;white-space:nowrap}} td.b{{font-weight:700;color:{NAVY}}}
.sub{{display:block;color:{MUTED};font-size:7.4pt;font-weight:400}}
.small{{font-size:7.8pt}}
tfoot td{{font-weight:700;border-top:1.5px solid {NAVY};border-bottom:0;color:{NAVY}}}
.mini td,.mini th{{padding:4px 6px}}
.notes{{font-size:7.5pt;color:{MUTED};line-height:1.45;margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:2px}}
.foot{{margin-top:auto;display:flex;justify-content:space-between;font-size:7.4pt;color:{MUTED};border-top:1px solid {LINE};padding-top:6px}}
.band{{background:#f1f6f8;border-radius:6px;padding:10px 12px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}}
.band div{{display:flex;flex-direction:column}} .band b{{font-family:Montserrat,Inter,sans-serif;font-size:11.5pt;color:{NAVY};font-variant-numeric:tabular-nums}} .band span{{font-size:7.6pt;color:{MUTED}}}
</style></head><body>

<section class="page">
  <div class="top">
    <div><img src="data:image/png;base64,{logo}" alt="Kaiken"></div>
    <div class="meta"><b>Importadora Hevia SpA</b> · RUT 76.872.717-1<br>Área inmobiliaria · Cifras al {fecha_larga}<br>Montos en UF</div>
  </div>
  <div>
    <h1>Patrimonio inmobiliario</h1>
    <p class="lead">{len(cartera)} propiedades en cartera en la Región Metropolitana, valorizadas según su última tasación, y {len(compra)} {"activo adicional" if len(compra)==1 else "activos adicionales"} en proceso de compra.</p>
  </div>
  <div class="kpis">
    <div class="kpi hero"><span class="l">Patrimonio neto</span><span class="v">{uf(E)} <small>UF</small></span><span class="s">Valor de tasación menos deuda</span></div>
    <div class="kpi accent"><span class="l">Valor de tasación</span><span class="v">{uf(V)} <small>UF</small></span><span class="s">{len(cartera)} propiedades · {uf(M2)} m²</span></div>
    <div class="kpi accent"><span class="l">Deuda hipotecaria</span><span class="v">{uf(D)} <small>UF</small></span><span class="s">{sum(b[2] for _,b in bancos)} créditos en {len(bancos)} bancos</span></div>
    <div class="kpi accent"><span class="l">Deuda / valor (LTV)</span><span class="v">{pct(D/V)}</span><span class="s">{sum(1 for p in cartera if not p['debt'])} propiedades sin deuda</span></div>
  </div>
  <div class="band">
    <div><b>{uf1(RENT)} UF</b><span>Arriendo mensual ({narr} propiedades arrendadas)</span></div>
    <div><b>{uf1(DIV)} UF</b><span>Dividendos mensuales</span></div>
    <div><b>{pct(RENT*12/V)}</b><span>Rentabilidad bruta sobre tasación</span></div>
    <div><b>{uf(VC)} UF</b><span>Valor de tasación de activos en compra</span></div>
  </div>
  <div class="grid">
    <div class="sec">
      <div class="sechead"><h2>Valor por propiedad</h2><span>UF</span></div>
      <div class="key"><span><i style="background:{NAVY}"></i>Patrimonio neto</span><span><i style="background:{SKY_SOFT}"></i>Deuda hipotecaria</span><span>Cifra = valor de tasación</span></div>
      {bars_svg()}
    </div>
    <div class="sec">
      <div class="sechead"><h2>Composición</h2><span>% del valor</span></div>
      {donut_svg()}
      <div class="sechead" style="margin-top:10px"><h2>Deuda por banco</h2><span>UF</span></div>
      <table class="mini"><thead><tr><th class="l">Banco</th><th>Saldo</th><th>Dividendo</th></tr></thead><tbody>
      {''.join(f'<tr><td class="l">{e(b)} <span class="sub" style="display:inline">({n[2]})</span></td><td class="num">{uf(n[0])}</td><td class="num">{uf1(n[1])}</td></tr>' for b,n in bancos)}
      </tbody><tfoot><tr><td class="l">Total</td><td class="num">{uf(D)}</td><td class="num">{uf1(DIV)}</td></tr></tfoot></table>
      <div class="sechead" style="margin-top:10px"><h2>Por comuna</h2><span>UF</span></div>
      <table class="mini"><thead><tr><th class="l">Comuna</th><th>Propiedades</th><th>Valor</th></tr></thead><tbody>
      {''.join(f'<tr><td class="l">{e(c)}</td><td class="num">{n[1]}</td><td class="num">{uf(n[0])}</td></tr>' for c,n in comunas)}
      </tbody></table>
    </div>
  </div>
  <div class="foot"><span>Kaiken · Importadora Hevia SpA · Informe de patrimonio inmobiliario</span><span>1 / 2</span></div>
</section>

<section class="page">
  <div class="top">
    <div><img src="data:image/png;base64,{logo}" alt="Kaiken" style="height:34px"></div>
    <div class="meta">Cifras al {fecha_larga} · Montos en UF</div>
  </div>
  <div class="sec">
    <div class="sechead"><h2>Detalle de propiedades en cartera</h2><span>Ordenadas por valor de tasación</span></div>
    <table><thead><tr><th class="l" style="width:30%">Propiedad</th><th class="l">Tasación</th><th>Valor</th><th>Deuda</th><th>Patrimonio</th><th class="l">Acreedor</th><th class="l">Estado</th><th>Arriendo/mes</th></tr></thead>
    <tbody>{''.join(row_cartera(p) for p in cartera)}</tbody>
    <tfoot><tr><td class="l">Total cartera</td><td></td><td class="num">{uf(V)}</td><td class="num">{uf(D)}</td><td class="num">{uf(E)}</td><td></td><td></td><td class="num">{uf1(RENT)}</td></tr></tfoot></table>
  </div>
  <div class="sec">
    <div class="sechead"><h2>Activos en proceso de compra</h2><span>No incluidos en los totales de la cartera</span></div>
    <table><thead><tr><th class="l">Propiedad</th><th class="l">Tasación</th><th>Valor de tasación</th><th>Costo de compra</th></tr></thead>
    <tbody>{''.join(row_compra(p) for p in compra)}</tbody>
    <tfoot><tr><td class="l">Total en compra</td><td></td><td class="num">{uf(VC)}</td><td class="num">{uf(sum(p['cost'] or 0 for p in compra))}</td></tr></tfoot></table>
  </div>
  <ul class="notes">
    <li>Valor: valor comercial de la última tasación de cada activo; si hay más de una, se usa la mayor. Deuda: saldo insoluto estimado a la fecha según monto, tasa, plazo y fecha del primer dividendo de cada crédito (diferencia de 0,5% o menos con las tablas de los bancos).</li>
    <li>¹ Valor basado en estimación de mercado (Propiteq), no en tasación bancaria.{(' ' + bank_note) if has_bank_note else ''}</li>
    <li>"En habilitación": oficinas recibidas en 2026 y remodeladas, aún sin arrendatario. Arriendo: renta mensual vigente de los contratos.</li>
  </ul>
  <div class="foot"><span>Kaiken · Importadora Hevia SpA · RUT 76.872.717-1</span><span>2 / 2</span></div>
</section>
</body></html>"""

(OUT / "patrimonio_inmobiliario.html").write_text(doc, encoding="utf-8")
pdf = OUT / f"Kaiken - Patrimonio inmobiliario {fecha}.pdf"
js = f"""const {{chromium}}=require('playwright');(async()=>{{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://{OUT/'patrimonio_inmobiliario.html'}',{{waitUntil:'networkidle'}});await p.evaluate(()=>document.fonts.ready);
await p.pdf({{path:{json.dumps(str(pdf))},format:'Letter',printBackground:true,margin:{{top:0,bottom:0,left:0,right:0}}}});await b.close()}})()"""
subprocess.run(["node", "-e", js], check=True, cwd="/tmp")
print(pdf)
print(f"Cartera: {len(cartera)} props, valor {V:.0f}, deuda {D:.1f}, patrimonio {E:.1f}, LTV {D/V:.3f}, renta {RENT}, div {DIV:.2f}; en compra {VC:.0f}")
