"""Dispara cada regla del catálogo en DISEÑO_DE_TRANSFORMADOR.py y guarda lo que pasó (resultados_py.json).
La misma lógica está en disparar.js para la página web; comparar_mapa.py compara las dos."""
import contextlib
import copy
import io
import json
import math
import pathlib
import sys

AQUI = pathlib.Path(__file__).parent
PROGRAMA_REPO = AQUI.parent / "python" / "DISENO_DE_TRANSFORMADOR.py"
PROGRAMA = sys.argv[1] if len(sys.argv) > 1 else str(PROGRAMA_REPO)
g = {}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(pathlib.Path(PROGRAMA).read_text(encoding="utf-8"), "dt", "exec"), g)

CAT = json.loads((AQUI / "reglas.json").read_text(encoding="utf-8"))
BASE = json.loads((AQUI / "base_mapa.json").read_text(encoding="utf-8"))


def poner(d, ruta, valor, cond=None):
    partes = ruta.split(".")
    for p in partes[:-1]:
        d = d[p]
    d[partes[-1]] = valor


def tomar(obj, ruta):
    partes = ruta.split(".")
    if partes[0] == "limites":
        L = {x["clave"]: x for x in (obj["limites"] or [])}
        x = L.get(partes[1])
        return None if x is None else x.get(partes[2])
    for p in partes:
        if obj is None:
            return None
        if isinstance(obj, list):
            i = int(p)
            obj = obj[i] if i < len(obj) else None
        else:
            obj = obj.get(p)
    return obj


def limpio(v):
    if isinstance(v, float) and not math.isfinite(v):
        return "inf"
    if isinstance(v, dict):
        return {k: limpio(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [limpio(x) for x in v]
    return v


def calcular(d, cond):
    s = g["calcular_datos"](copy.deepcopy(d))
    L = None
    if s.get("mont"):
        L = g["limites_diseno"](s["nuc"], s["elec"], s["mont"], s["pares"], g["condiciones_diseno"](d), s["esf"])   # las del diseño
        s["gobierna"] = g["limite_gobernante"](L)["clave"]
    s["limites"] = L
    s["pasos"] = g["estado_pasos"](g["faltantes_detalle"](d), [] if s.get("faltan") else s["errores"], L, bool(s.get("nuc")))
    s["faltan_detalle"] = g["faltantes_detalle"](d)
    return s


def igual(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        return abs(a - b) <= 1e-9 * max(1.0, abs(b))
    return a == b


def evaluar(regla, d, cond, base_s=None):
    e = regla["espera"]
    out = {"dispara": False, "detalle": None, "errores": []}
    if "busqueda" in e:
        o = dict(e["busqueda"])
        o.setdefault("tipos", {"I": [], "II": [], "III": []})
        r = g["buscar_combinaciones"](copy.deepcopy(d), o)
        lista = r["errores"] if "error" in e else r["avisos"]
        texto = e.get("error") or e.get("aviso")
        hit = [x for x in lista if texto in x]
        out.update(dispara=bool(hit), detalle=hit[0] if hit else None, errores=r["errores"][:3] + r["avisos"][:3])
        return out
    s = calcular(d, cond)
    out["errores"] = s["errores"][:3]
    if "error" in e:
        hit = [x for x in s["errores"] if e["error"] in x]
        out.update(dispara=bool(hit) and not s.get("faltan"), detalle=hit[0] if hit else None)
    elif "falta" in e:
        hit = [x for x in s["faltan_detalle"] if e["falta"] in x["rotulo"]]
        out.update(dispara=bool(hit), detalle=[hit[0]["paso"], hit[0]["rotulo"]] if hit else None)
    elif "limite" in e:
        L = {x["clave"]: x for x in (s["limites"] or [])}
        x = L.get(e["limite"])
        out.update(dispara=bool(x) and x["estado"] == e["estado"],
                   detalle=[x["estado"], x["valor"], x.get("nota", "")] if x else None)
    elif "paso" in e:
        x = s["pasos"][e["paso"] - 1]
        out.update(dispara=x["estado"] == e["estado"], detalle=[x["estado"], x["texto"]])
    elif "valor" in e:
        v = tomar(s, e["valor"])
        op, ref = e["op"], e.get("v")
        if isinstance(ref, str) and ref.startswith("$"):
            ref = tomar(s, ref[1:])
        b = tomar(base_s, e["valor"]) if base_s is not None else None
        if v is None:
            ok = False
        elif op == "==":
            ok = igual(v, ref)
        elif op == "!=":
            ok = not igual(v, ref)
        elif op == "<":
            ok = v < ref
        elif op == ">":
            ok = v > ref
        elif op == "len":
            ok = len(v) == ref
        elif op == "igual_base":
            ok = igual(v, b)
        elif op == "distinto_base":
            ok = not igual(v, b)
        elif op == "menor_base":
            ok = b is not None and v < b
        elif op == "mayor_base":
            ok = b is not None and v > b
        else:
            raise ValueError(op)
        out.update(dispara=bool(ok), detalle=limpio(len(v) if op == "len" else v))
    if e.get("sin_error"):
        out["con_error"] = bool(s["errores"])
        out["dispara"] = out["dispara"] and not s["errores"]
    return out


def correr():
    base_s = calcular(BASE, {})
    res = {"_base": {"errores": base_s["errores"], "limites": [[x["clave"], x["estado"], limpio(x["uso"])] for x in base_s["limites"] or []],
                     "gobierna": base_s.get("gobierna")}}
    for r in CAT["reglas"]:
        if not r["espera"]:
            continue
        d, cond = copy.deepcopy(BASE), {}
        for ruta, valor in r["caso"] or []:
            poner(d, ruta, valor, cond)
        caso = evaluar(r, d, cond, base_s)
        base = evaluar(r, copy.deepcopy(BASE), {}, base_s)
        res[r["id"]] = {"caso": caso, "base": base}
    return res


if __name__ == "__main__":
    salida = AQUI / (sys.argv[2] if len(sys.argv) > 2 else "resultados_py.json")
    salida.write_text(json.dumps(limpio(correr()), ensure_ascii=False, indent=1), encoding="utf-8")
    print("guardado", salida.name)
