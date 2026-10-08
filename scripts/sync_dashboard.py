"""Inyecta los datos del Registro de propiedades v2 en el dashboard.

Uso: python3 scripts/sync_dashboard.py <valores.json> [dashboard/index.html]

<valores.json> es la respuesta de Google Sheets get_values sobre Propiedades!A1:AD
(objeto con "values": [[encabezados], [fila], ...]). Reemplaza el bloque entre
/*REG_START*/ y /*REG_END*/ y sale con código 0 si cambió, 3 si no hubo cambios.
"""
import json, re, sys, datetime as dt

src = sys.argv[1]
html = sys.argv[2] if len(sys.argv) > 2 else "dashboard/index.html"
vals = json.load(open(src))
vals = vals.get("values", vals)
header, rows = vals[0], [r + [""] * (len(vals[0]) - len(r)) for r in vals[1:] if any(c.strip() for c in r)]
today = dt.date.today().strftime("%d-%m-%Y")
s = open(html, encoding="utf-8").read()
m = re.search(r"/\*REG_START\*/(.*?)/\*REG_END\*/", s, re.S)
old = json.loads(m.group(1) or "{}")
# Se compara por ID e ignorando columnas calculadas por la planilla: el orden de filas
# y el saldo/plusvalía que cambian solos no son cambios de datos.
CALC = {"Saldo insoluto hoy (UF)", "Plusvalía sobre costo (%)"}
def norm(h, rs):
    keep = [i for i, c in enumerate(h) if c not in CALC]
    return sorted(tuple(r[i] if i < len(r) else "" for i in keep) for r in rs)
changed_data = old.get("header") != header or norm(header, rows) != norm(old.get("header") or header, old.get("rows") or [])
same_month = (old.get("asof") or "")[3:] == today[3:]
if not changed_data and same_month:
    print("Sin cambios"); sys.exit(3)
reg = {"asof": today, "synced": dt.datetime.now().strftime("%d-%m-%Y %H:%M"), "header": header, "rows": rows}
s = s[:m.start(1)] + json.dumps(reg, ensure_ascii=False, separators=(",", ":")) + s[m.end(1):]
open(html, "w", encoding="utf-8").write(s)
print("Datos del registro cambiaron" if changed_data else "Mes nuevo: se actualizan saldos", len(rows), "filas")
