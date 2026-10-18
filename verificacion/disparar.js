// Dispara cada regla del catálogo en la página web (calc.js + optimiza.js) y guarda lo que pasó (resultados_js.json).
// Misma lógica que disparar.py.
const fs = require("fs"), vm = require("vm"), path = require("path");
const AQUI = __dirname, WEB = process.argv[2] || path.join(AQUI, "..", "web");
const ctx = {}; vm.createContext(ctx);
vm.runInContext(fs.readFileSync(path.join(WEB, "calc.js"), "utf8") + fs.readFileSync(path.join(WEB, "optimiza.js"), "utf8") +
  ";this.X={calcularTodo,condicionesDiseno,faltantesDetalle,limitesDiseno,limiteGobernante,estadoPasos,buscarCombinaciones}", ctx);
const X = ctx.X;
const leer = (f) => JSON.parse(fs.readFileSync(path.join(AQUI, f), "utf8"));
const CAT = leer("reglas.json"), BASE = leer("base_mapa.json");
const copia = (x) => JSON.parse(JSON.stringify(x));
const MAPA_BUSQ = { dn_fijo: "dnFijo", dn_min: "dnMin", dn_max: "dnMax", dn_paso: "dnPaso", de_max: "deMax" };

function poner(d, ruta, valor, cond) {
  const p = ruta.split(".");
  for (const k of p.slice(0, -1)) d = d[k];
  d[p[p.length - 1]] = valor;
}
function tomar(obj, ruta) {
  const p = ruta.split(".");
  if (p[0] === "limites") {
    const x = (obj.limites || []).find((l) => l.clave === p[1]);
    return x === undefined ? null : (x[p[2]] === undefined ? null : x[p[2]]);
  }
  for (const k of p) {
    if (obj === null || obj === undefined) return null;
    obj = Array.isArray(obj) ? obj[Number(k)] : obj[k];
  }
  return obj === undefined ? null : obj;
}
const limpio = (v) => (typeof v === "number" && !isFinite(v) ? "inf" : v);
function calcular(d, cond) {
  const s = X.calcularTodo(copia(d));
  let L = null;
  if (s.mont) { L = X.limitesDiseno(s.nuc, s.elec, s.mont, s.pares, X.condicionesDiseno(d), s.esf); s.gobierna = X.limiteGobernante(L).clave; }
  s.limites = L;
  s.pasos = X.estadoPasos(X.faltantesDetalle(d), s.faltan ? [] : s.errores, L, !!s.nuc);
  s.faltan_detalle = X.faltantesDetalle(d);
  return s;
}
const igual = (a, b) => (typeof a === "number" && typeof b === "number" ? Math.abs(a - b) <= 1e-9 * Math.max(1, Math.abs(b)) : a === b);

function evaluar(regla, d, cond, baseS) {
  const e = regla.espera, out = { dispara: false, detalle: null, errores: [] };
  if (e.busqueda) {
    const o = { tipos: { I: [], II: [] } };
    for (const [k, v] of Object.entries(e.busqueda)) o[MAPA_BUSQ[k] || k] = v;
    const r = X.buscarCombinaciones(copia(d), o);
    const lista = "error" in e ? r.errores : r.avisos, texto = e.error || e.aviso;
    const hit = lista.filter((x) => x.includes(texto));
    Object.assign(out, { dispara: hit.length > 0, detalle: hit[0] || null, errores: r.errores.slice(0, 3).concat(r.avisos.slice(0, 3)) });
    return out;
  }
  const s = calcular(d, cond);
  out.errores = s.errores.slice(0, 3);
  if ("error" in e) {
    const hit = s.errores.filter((x) => x.includes(e.error));
    Object.assign(out, { dispara: hit.length > 0 && !s.faltan, detalle: hit[0] || null });
  } else if ("falta" in e) {
    const hit = s.faltan_detalle.filter((x) => x.rotulo.includes(e.falta));
    Object.assign(out, { dispara: hit.length > 0, detalle: hit.length ? [hit[0].paso, hit[0].rotulo] : null });
  } else if ("limite" in e) {
    const x = (s.limites || []).find((l) => l.clave === e.limite);
    Object.assign(out, { dispara: !!x && x.estado === e.estado, detalle: x ? [x.estado, x.valor, x.nota || ""] : null });
  } else if ("paso" in e) {
    const x = s.pasos[e.paso - 1];
    Object.assign(out, { dispara: x.estado === e.estado, detalle: [x.estado, x.texto] });
  } else if ("valor" in e) {
    const v = tomar(s, e.valor), op = e.op;
    let ref = e.v;
    if (typeof ref === "string" && ref.startsWith("$")) ref = tomar(s, ref.slice(1));
    const b = baseS ? tomar(baseS, e.valor) : null;
    let ok;
    if (v === null) ok = false;
    else if (op === "==") ok = igual(v, ref);
    else if (op === "!=") ok = !igual(v, ref);
    else if (op === "<") ok = v < ref;
    else if (op === ">") ok = v > ref;
    else if (op === "len") ok = v.length === ref;
    else if (op === "igual_base") ok = igual(v, b);
    else if (op === "distinto_base") ok = !igual(v, b);
    else if (op === "menor_base") ok = b !== null && v < b;
    else if (op === "mayor_base") ok = b !== null && v > b;
    else throw new Error(op);
    Object.assign(out, { dispara: !!ok, detalle: limpio(op === "len" ? v.length : v) });
  }
  if (e.sin_error) { out.con_error = s.errores.length > 0; out.dispara = out.dispara && !s.errores.length; }
  return out;
}

const baseS = calcular(BASE, {});
const res = { _base: { errores: baseS.errores, limites: (baseS.limites || []).map((x) => [x.clave, x.estado, limpio(x.uso)]), gobierna: baseS.gobierna } };
for (const r of CAT.reglas) {
  if (!r.espera) continue;
  const d = copia(BASE), cond = {};
  for (const [ruta, valor] of r.caso || []) poner(d, ruta, valor, cond);
  res[r.id] = { caso: evaluar(r, d, cond, baseS), base: evaluar(r, copia(BASE), {}, baseS) };
}
const salida = path.join(AQUI, process.argv[3] || "resultados_js.json");
fs.writeFileSync(salida, JSON.stringify(res, null, 1));
console.log("guardado", path.basename(salida));
