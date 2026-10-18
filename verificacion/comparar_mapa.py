"""Revisión automática del mapa de condiciones.
1. Cada regla con caso: el caso la dispara, la base no (la causa es la esperada) y Python = web.
2. Cada huella está en el código de los dos lenguajes (la regla existe donde dice).
3. Cobertura: cada mensaje y cada límite del código tiene su regla en el catálogo.
4. Constantes y tablas: iguales en Python y en la web.
5. Datos iniciales: iguales en Python y en la web, con su origen.
Escribe resultado_mapa.json (lo lee la página) y muestra un resumen."""
import contextlib
import datetime
import io
import json
import math
import pathlib
import re
import subprocess
import sys

AQUI = pathlib.Path(__file__).parent
PROGRAMA_REPO = AQUI.parent / "python" / "DISENO_DE_TRANSFORMADOR.py"
PROGRAMA = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else PROGRAMA_REPO)
WEB = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else AQUI.parent / "web")
def paso(orden):
    """Corre un paso de la revisión; si falla, muestra su salida de error y corta."""
    r = subprocess.run(orden, capture_output=True, text=True)
    if r.returncode:
        print("Falló:", " ".join(orden), "\n", r.stdout[-2000:], r.stderr[-4000:], file=sys.stderr)
        sys.exit(r.returncode)


paso([sys.executable, str(AQUI / "reglas.py")])
paso([sys.executable, str(AQUI / "disparar.py"), str(PROGRAMA)])
paso(["node", str(AQUI / "disparar.js"), str(WEB)])

CAT = json.loads((AQUI / "reglas.json").read_text(encoding="utf-8"))
PY = json.loads((AQUI / "resultados_py.json").read_text(encoding="utf-8"))
JS = json.loads((AQUI / "resultados_js.json").read_text(encoding="utf-8"))
TXT_PY = PROGRAMA.read_text(encoding="utf-8")
TXT_JS = "".join((WEB / f).read_text(encoding="utf-8") for f in ("calc.js", "optimiza.js", "ui.js", "ui_busqueda.js"))
LOGICA_JS = {f: (WEB / f).read_text(encoding="utf-8") for f in ("calc.js", "optimiza.js")}


def igual(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) <= 1e-9 * max(1.0, abs(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(igual(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(igual(a[k], b[k]) for k in a)
    return a == b


def necesita_base(r):
    e = r["espera"]
    if not r["caso"] or e.get("sin_base"):
        return False
    return not str(e.get("op", "")).endswith("_base")


# 1 y 2. Reglas
filas = {}
for r in CAT["reglas"]:
    h = r["huella"]
    hp, hj = (h["py"], h["js"]) if isinstance(h, dict) else (h, h)
    f = {"huella_py": hp in TXT_PY, "huella_js": r["js"] == "—" or hj in TXT_JS, "probada": bool(r["espera"])}
    if r["espera"]:
        p, j = PY[r["id"]], JS[r["id"]]
        f["paridad"] = igual(p["caso"]["dispara"], j["caso"]["dispara"]) and igual(p["caso"]["detalle"], j["caso"]["detalle"]) \
            and igual(p["base"]["dispara"], j["base"]["dispara"])
        f["dispara"] = p["caso"]["dispara"] and j["caso"]["dispara"]
        f["base_limpia"] = (not p["base"]["dispara"] and not j["base"]["dispara"]) if necesita_base(r) else None
        f["detalle"] = p["caso"]["detalle"]
        f["detalle_js"] = j["caso"]["detalle"]
        f["errores"] = p["caso"]["errores"]
    ok = f["huella_py"] and f["huella_js"] and (not f["probada"] or (f["paridad"] and f["dispara"] and f["base_limpia"] is not False))
    f["prueba"] = "pasa" if ok else "falla"
    filas[r["id"]] = f

# 3. Cobertura: mensajes y límites del código sin regla
huellas_py = [(r["huella"]["py"] if isinstance(r["huella"], dict) else r["huella"]) for r in CAT["reglas"]]
huellas_js = [(r["huella"]["js"] if isinstance(r["huella"], dict) else r["huella"]) for r in CAT["reglas"]]
RE_PY = re.compile(r"""\b(?:errores|err|e|err_vac|err_nuc|t|falta|faltas)\.append\(\s*f?["']|return \[f?["']|L\.append\(\{"clave"|err_elec\) \+ \[""")
RE_JS = re.compile(r"""\b(?:e|errores|errNuc|errVac|err|falta|t)\.push\(\s*[`"]|return \[\s*[`"]|L\.push\(\{ clave""")


def sitios(texto, regex, huellas, nombre):
    lineas, out = texto.splitlines(), []
    for i, l in enumerate(lineas):
        if regex.search(l):
            # la sentencia completa: desde la línea hasta que cierran los paréntesis (mensajes partidos en varias líneas)
            j, abiertos = i, 0
            while j < len(lineas) and j < i + 6:
                abiertos += lineas[j].count("(") + lineas[j].count("[") + lineas[j].count("{") - lineas[j].count(")") - lineas[j].count("]") - lineas[j].count("}")
                j += 1
                if abiertos <= 0:
                    break
            trozo = "\n".join(lineas[i:j])
            regla = next((h for h in huellas if h in trozo), None)
            out.append({"archivo": nombre, "linea": i + 1, "codigo": l.strip()[:160], "con_regla": regla is not None})
    return out


cob = sitios(TXT_PY, RE_PY, huellas_py, PROGRAMA.name)
for nombre, t in LOGICA_JS.items():
    cob += sitios(t, RE_JS, huellas_js, nombre)

# 4 y 5. Constantes y datos iniciales
g = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(TXT_PY, "dt", "exec"), g)
nombres = [c[0] for c in CAT["constantes"]]
js_c = json.loads(subprocess.run(["node", "-e", """
const fs = require('fs'), vm = require('vm'), ctx = {}; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(process.argv[1] + '/calc.js', 'utf8') + fs.readFileSync(process.argv[1] + '/optimiza.js', 'utf8') +
  ';this.X={' + process.argv[2] + ',DATOS_EJEMPLO,OPT_EJEMPLO}', ctx);
console.log(JSON.stringify(ctx.X));""", str(WEB), ",".join(nombres)], check=True, capture_output=True, text=True).stdout)


def a_json(v):
    return json.loads(json.dumps(v, default=list))


def norm_tipos(t):
    return {k: {c: v for c, v in r.items() if v is not None} for k, r in t.items()}


constantes = []
for nombre, que, origen in CAT["constantes"]:
    vp, vj = a_json(g[nombre]), js_c[nombre]
    if nombre == "TIPOS":
        vp, vj = norm_tipos(vp), norm_tipos(vj)
    constantes.append({"nombre": nombre, "que": que, "origen": origen, "valor": vp, "igual": igual(vp, vj)})

datos_py = a_json(g["leer_datos"]())
datos_py["dev"] = a_json(g["VALORES_TABLA"])    # por devanado, los valores de origen (la pantalla ya llenó las capas calculadas)
datos_js = js_c["DATOS_EJEMPLO"]
origen_datos = []
for campo, rotulo, paso, origen in CAT["origen_datos"]:
    if campo.startswith("dev.*."):
        c = campo[6:]
        vp = {k: datos_py["dev"][k].get(c) for k in ("I", "II", "III")}
        vj = {k: datos_js["dev"][k].get(c) for k in ("I", "II", "III")}
    else:
        vp, vj = datos_py.get(campo), datos_js.get(campo)
    origen_datos.append({"campo": campo, "rotulo": rotulo, "paso": paso, "origen": origen, "valor": vp, "igual": igual(vp, vj),
                         "vacio_ok": (origen != "SF") or all(v in (None, "") for v in (vp.values() if isinstance(vp, dict) else [vp]))})
busq_py = {k: (g["wb"][k].value if hasattr(g["wb"][k], "value") else None) for k in ("jmax", "bmin", "bmax")}
busq_py = {k: g["_leer"](g["wb"][k]) for k in ("jmax", "bmin", "bmax", "vcc", "tol", "jmin")}
busq_js = {k: js_c["OPT_EJEMPLO"][k] for k in busq_py}
for k, rot, ori in (("jmax", "J máxima (búsqueda)", "TC"), ("bmin", "B mínima (búsqueda)", "TC"), ("bmax", "B máxima (búsqueda)", "TC"),
                    ("vcc", "Vcc objetivo", "SF"), ("tol", "Tolerancia de Vcc", "SF"), ("jmin", "J mínima", "SF")):
    origen_datos.append({"campo": "busqueda." + k, "rotulo": rot, "paso": 6, "origen": ori, "valor": busq_py[k],
                         "igual": igual(busq_py[k], busq_js[k]), "vacio_ok": ori != "SF" or busq_py[k] is None})

# Resumen
reglas = CAT["reglas"]
cuenta = lambda f: sum(1 for r in reglas if f(r))
resumen = {
    "reglas": len(reglas),
    "probadas": cuenta(lambda r: filas[r["id"]]["probada"]),
    "pasan": cuenta(lambda r: filas[r["id"]]["prueba"] == "pasa"),
    "fallan": [r["id"] for r in reglas if filas[r["id"]]["prueba"] == "falla"],
    "huecos": cuenta(lambda r: r["revision"] == "hueco"),
    "dudosos": cuenta(lambda r: r["revision"] == "dudoso"),
    "sin_uso": cuenta(lambda r: r["revision"] == "sin-uso"),
    "sitios": len(cob), "sitios_sin_regla": [s for s in cob if not s["con_regla"]],
    "constantes": len(constantes), "constantes_distintas": [c["nombre"] for c in constantes if not c["igual"]],
    "datos": len(origen_datos), "datos_distintos": [d["campo"] for d in origen_datos if not d["igual"]],
    "sin_fuente_con_valor": [d["campo"] for d in origen_datos if not d["vacio_ok"]],
    "base_errores": PY["_base"]["errores"], "base_limites": PY["_base"]["limites"], "base_gobierna": PY["_base"]["gobierna"],
}
salida = {"generado": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "resumen": resumen, "filas": filas,
          "cobertura": cob, "constantes": constantes, "origen_datos": origen_datos}
(AQUI / "resultado_mapa.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")

print(f"{resumen['reglas']} reglas · {resumen['probadas']} con caso · pasan {resumen['pasan']} · fallan {len(resumen['fallan'])}")
for i in resumen["fallan"]:
    r = next(x for x in reglas if x["id"] == i)
    f = filas[i]
    print("  FALLA", i, r["titulo"], {k: f.get(k) for k in ("huella_py", "huella_js", "paridad", "dispara", "base_limpia")},
          "| py:", json.dumps(PY.get(i, {}), ensure_ascii=False)[:300], "| js:", json.dumps(JS.get(i, {}), ensure_ascii=False)[:200])
print(f"cobertura: {len(cob)} sitios de mensaje o límite · sin regla {len(resumen['sitios_sin_regla'])}")
for s in resumen["sitios_sin_regla"]:
    print("  SIN REGLA", s["archivo"], s["linea"], s["codigo"])
print(f"constantes: {len(constantes)} · distintas {resumen['constantes_distintas']}")
print(f"datos iniciales: {len(origen_datos)} · distintos {resumen['datos_distintos']} · sin fuente con valor {resumen['sin_fuente_con_valor']}")
print("huecos", resumen["huecos"], "· dudosos", resumen["dudosos"], "· sin uso", resumen["sin_uso"])
print("base:", resumen["base_errores"], resumen["base_gobierna"])
sys.exit(1 if resumen["fallan"] or resumen["sitios_sin_regla"] or resumen["constantes_distintas"] or resumen["datos_distintos"] else 0)
