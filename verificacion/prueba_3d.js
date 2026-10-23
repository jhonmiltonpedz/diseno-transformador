// Verificación matemática del modelo 3D (web/modelo3d.js): que las mallas sean sólidos cerrados y que sus medidas,
// volúmenes y pesos sean los del cálculo. Uso: node verificacion/prueba_3d.js
const fs = require("fs"), vm = require("vm"), path = require("path");
const WEB = process.argv[2] || path.join(__dirname, "..", "web");
const ctx = {}; vm.createContext(ctx);
vm.runInContext(["calc.js", "optimiza.js", "modelo3d.js"].map((f) => fs.readFileSync(path.join(WEB, f), "utf8")).join("\n") +
  ";this.X={calcularTodo,buscarCombinaciones,aplicarAlternativa,DATOS_EJEMPLO,OPT_EJEMPLO,modelo3d,volumenMalla,aSTL,aOBJ,TANQUE_ESTIMADO,SEGMENTOS_3D,RHO_FE}", ctx);
const X = ctx.X, copia = (x) => JSON.parse(JSON.stringify(x));
let fallas = 0, pruebas = 0;
function ok(cond, texto) { pruebas++; if (!cond) { fallas++; console.log("  FALLA:", texto); } }
const cerca = (a, b, tol = 1e-6) => Math.abs(a - b) <= tol * Math.max(1, Math.abs(a), Math.abs(b));

// Sólido cerrado y orientado: cada arista se recorre una vez en cada sentido (vale también para varias piezas
// cerradas que se tocan, como las chapas de un escalón)
function cerrada(pos) {
  const k = (i) => `${pos[i].toFixed(5)},${pos[i + 1].toFixed(5)},${pos[i + 2].toFixed(5)}`, cuenta = new Map();
  for (let t = 0; t < pos.length; t += 9) {
    const v = [k(t), k(t + 3), k(t + 6)];
    if (v[0] === v[1] || v[1] === v[2] || v[0] === v[2]) return "triángulo degenerado";
    for (let j = 0; j < 3; j++) {
      const a = v[j], b = v[(j + 1) % 3], clave = a < b ? `${a}|${b}` : `${b}|${a}`;
      cuenta.set(clave, (cuenta.get(clave) || 0) + (a < b ? 1 : -1));
    }
  }
  for (const [c, n] of cuenta) if (n !== 0) return `arista sin pareja ${c}`;
  return "";
}
// Variedad estricta: cada arista la usan exactamente 2 triángulos, una vez en cada sentido (un solo sólido, sin
// caras internas ni vértices en T)
function variedad(pos) {
  const k = (i) => `${pos[i].toFixed(5)},${pos[i + 1].toFixed(5)},${pos[i + 2].toFixed(5)}`, vistas = new Set();
  for (let t = 0; t < pos.length; t += 9) {
    const v = [k(t), k(t + 3), k(t + 6)];
    for (let j = 0; j < 3; j++) {
      const a = `${v[j]}>${v[(j + 1) % 3]}`;
      if (vistas.has(a)) return `arista repetida ${a}`;
      vistas.add(a);
    }
  }
  for (const a of vistas) { const [x, y] = a.split(">"); if (!vistas.has(`${y}>${x}`)) return `arista sin pareja ${a}`; }
  return "";
}
function limites(pos) {
  const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
  for (let i = 0; i < pos.length; i += 3) for (let j = 0; j < 3; j++) { lo[j] = Math.min(lo[j], pos[i + j]); hi[j] = Math.max(hi[j], pos[i + j]); }
  return { lo, hi };
}

function revisar(nombre, d, debeEntrar) {
  console.log(`· ${nombre}`);
  const r = X.calcularTodo(copia(d)), M = X.modelo3d(r, d);
  if (!M) { ok(false, "no se generó el modelo"); return; }
  const nuc = r.nuc, mont = r.mont, n = X.SEGMENTOS_3D, poligono = (n / 2) * Math.sin((2 * Math.PI) / n);   // área del polígono / r²
  // 1. todas las piezas son sólidos cerrados con volumen positivo
  for (const m of M.partes) {
    const c = cerrada(m.pos), vr = variedad(m.pos);
    ok(c === "", `${m.nombre}: ${c}`);
    ok(vr === "", `${m.nombre}: ${vr}`);
    ok(X.volumenMalla(m) > 0, `${m.nombre}: volumen ${X.volumenMalla(m)}`);
    ok(m.pos.length === m.nor.length, `${m.nombre}: normales`);
  }
  // y todas juntas (como quedan en el STL): piezas que se tocan no comparten aristas, así cada una es un sólido suelto
  const todo = variedad(M.partes.flatMap((m) => Array.from(m.pos)));
  ok(todo === "", `piezas que comparten aristas: ${todo}`);
  // 2. núcleo: medidas exteriores y peso = volumen x 7650 kg/m³
  const mn = M.partes.find((m) => m.id === "nucleo"), bn = limites(mn.pos), esc = nuc.escalones.filter((e) => e.ancho > 0 && e.espesor > 0);
  const a1 = esc[0].ancho, prof = esc.reduce((s, e) => s + e.espesor, 0);
  ok(cerca(bn.hi[0] - bn.lo[0], 2 * nuc.de + a1), `núcleo: largo ${bn.hi[0] - bn.lo[0]} ≠ 2·De + a₁`);
  ok(cerca(bn.hi[2] - bn.lo[2], nuc.hc + 2 * a1), `núcleo: alto ${bn.hi[2] - bn.lo[2]} ≠ Hc + 2·a₁`);
  ok(cerca(bn.hi[1] - bn.lo[1], prof), `núcleo: profundidad ${bn.hi[1] - bn.lo[1]} ≠ Σ espesores`);
  const vn = variedad(mn.pos);
  ok(vn === "", `núcleo: no es un solo sólido sin caras internas: ${vn}`);
  ok(cerca((X.volumenMalla(mn) / 1e9) * X.RHO_FE, nuc.peso, 1e-9), `núcleo: peso del modelo ${(X.volumenMalla(mn) / 1e9) * X.RHO_FE} ≠ calculado ${nuc.peso}`);
  // 3. devanados: diámetros, altura, centrado en la ventana y volumen (polígono de n lados)
  const canales = Object.fromEntries(r.lista.map((it) => [it.clave, it.res.canales]));
  for (const f of mont.filas) {
    const ms = M.partes.filter((m) => m.clave === f.clave);
    ok(ms.length === 3, `${f.nombre}: ${ms.length} fases`);
    const sumaCan = canales[f.clave].reduce((s, c) => s + c, 0), cobre = (f.radial - sumaCan) / (canales[f.clave].length + 1);
    let esperado = 0, ri = f.d_int / 2;
    for (let k = 0; k <= canales[f.clave].length; k++) { esperado += poligono * ((ri + cobre) ** 2 - ri ** 2); ri += cobre + (canales[f.clave][k] || 0); }
    esperado *= f.n_sec * f.axial_seccion;
    ms.forEach((m, i) => {
      const b = limites(m.pos), xc = [-nuc.de, 0, nuc.de][i], vd = variedad(m.pos);
      ok(vd === "", `${m.nombre}: ${vd}`);
      ok(cerca(b.hi[0] - b.lo[0], f.d_ext) && cerca((b.hi[0] + b.lo[0]) / 2, xc), `${m.nombre}: diámetro exterior ${b.hi[0] - b.lo[0]} ≠ ${f.d_ext}`);
      ok(cerca(b.hi[2] - b.lo[2], f.axial) && cerca(b.hi[2] + b.lo[2], 0), `${m.nombre}: altura ${b.hi[2] - b.lo[2]} ≠ ${f.axial} o no está centrado`);
      ok(cerca(X.volumenMalla(m), esperado, 1e-9), `${m.nombre}: volumen ${X.volumenMalla(m)} ≠ ${esperado}`);
    });
    if (f.n_sec > 1) {   // la galleta: 2 bobinas separadas 20 mm (no hay cobre en z = 0)
      const zs = ms[0].pos.filter((_, i) => i % 3 === 2);
      ok(!zs.some((z) => Math.abs(z) < 10 - 1e-9), `${f.nombre}: la galleta no deja el espacio de 20 mm entre bobinas`);
    }
  }
  // 4. lo que debe y no debe chocar
  const choca = M.avisos.length > 0;
  ok(choca === !debeEntrar, `avisos de choque: ${JSON.stringify(M.avisos)} (se esperaba ${debeEntrar ? "ninguno" : "alguno"})`);
  if (debeEntrar) {
    ok(nuc.de >= mont.d_total, "fases vecinas se cruzan");
    ok(mont.filas[0].d_int / 2 > M.medidas.nucleo.r_esquina, "el núcleo toca el devanado interno");
    ok(mont.filas.every((f) => f.axial <= nuc.hc), "un devanado no entra en la ventana");
  }
  // 5. todo dentro del tanque
  const tq = M.partes.find((m) => m.id === "tanque"), T = M.medidas.tanque, zf = -(nuc.hc + 2 * a1) / 2 - T.holguras.fondo;
  for (const m of M.partes) if (m !== tq) {
    const b = limites(m.pos);
    ok(b.lo[0] >= -T.largo / 2 && b.hi[0] <= T.largo / 2 && b.lo[1] >= -T.ancho / 2 && b.hi[1] <= T.ancho / 2 && b.lo[2] >= zf && b.hi[2] <= zf + T.alto,
      `${m.nombre}: se sale del tanque`);
  }
  ok(T.aceite_l > 0 && T.aceite_l < T.volumen_interior_l, `aceite ${T.aceite_l} L`);
  // 6. exportar: STL binario y OBJ (re-leído: cada objeto sigue cerrado con los vértices compartidos)
  const nt = M.partes.reduce((s, m) => s + m.pos.length / 9, 0), stl = X.aSTL(M.partes), dv = new DataView(stl);
  ok(stl.byteLength === 84 + 50 * nt && dv.getUint32(80, true) === nt, "STL: tamaño o cantidad de triángulos");
  let vStl = 0;
  for (let t = 0, o = 84; t < nt; t++, o += 50) {
    const p = Array.from({ length: 9 }, (_, j) => dv.getFloat32(o + 12 + 4 * j, true));
    vStl += (p[0] * (p[4] * p[8] - p[5] * p[7]) - p[1] * (p[3] * p[8] - p[5] * p[6]) + p[2] * (p[3] * p[7] - p[4] * p[6])) / 6;
  }
  const vTot = M.partes.reduce((s, m) => s + X.volumenMalla(m), 0);
  ok(cerca(vStl, vTot, 1e-4), `STL: volumen ${vStl} ≠ ${vTot}`);
  const obj = X.aOBJ(M.partes).split("\n"), objetos = [];
  const vs = [];
  for (const l of obj) {
    if (l.startsWith("o ")) objetos.push([]);
    else if (l.startsWith("v ")) vs.push(l.slice(2).split(" ").map(Number));
    else if (l.startsWith("f ")) objetos[objetos.length - 1].push(...l.slice(2).split(" ").map(Number));
  }
  ok(objetos.length === M.partes.length, "OBJ: un objeto por pieza");
  ok(objetos.reduce((s, f) => s + f.length / 3, 0) === nt, "OBJ: cantidad de triángulos");
  objetos.forEach((f, i) => {
    const pos = []; for (const k of f) pos.push(...vs[k - 1]);
    const c = cerrada(pos); ok(c === "", `OBJ ${M.partes[i].id}: ${c}`);
  });
  console.log(`  ${M.partes.length} piezas, ${nt} triángulos · núcleo ${M.medidas.nucleo.peso_modelo.toFixed(2)} kg · tanque ${T.largo.toFixed(0)} x ${T.ancho.toFixed(0)} x ${T.alto.toFixed(0)} mm · aceite ≈ ${T.aceite_l.toFixed(0)} L` +
    (M.avisos.length ? ` · avisos: ${M.avisos.join(" | ")}` : ""));
}

const base = copia(X.DATOS_EJEMPLO);
revisar("Diseño de ejemplo (De 510: las fases se cruzan)", base, false);
revisar("Diseño de ejemplo con De 525", Object.assign(copia(base), { de: 525 }), true);
const gal = copia(base); gal.de = 560; Object.assign(gal.dev.I, { tipo: "GALLETA", calibre: ["ALAMBRE", 9], cant: 1, horiz: 1, n_canales: 0 });
const rg = X.calcularTodo(copia(gal));
if (rg.mont && !rg.errores.length) revisar("Galleta en AT (2 bobinas)", gal, rg.mont.entre_fases_real >= 0 && rg.mont.filas.every((f) => f.al_yugo >= 0));
else console.log("· Galleta en AT: el diseño no se calcula:", rg.errores);
// alternativas de la búsqueda por Vcc (el modelo 3D también se genera para ellas)
const busq = X.buscarCombinaciones(copia(base), Object.assign(copia(X.OPT_EJEMPLO), { vcc: 5, tol: 10, jmin: 2, dnFijo: 259, deMax: 600, max: 3 }));
ok(busq.resultados.length === 3, `la búsqueda de prueba dio ${busq.resultados.length} alternativas`);
(busq.resultados || []).slice(0, 3).forEach((alt, i) => {
  const d = alt.datos || X.aplicarAlternativa(base, alt, X.OPT_EJEMPLO), rr = X.calcularTodo(copia(d));
  revisar(`Alternativa ${i + 1} de la búsqueda (Dn ${alt.dn}, De ${d.de})`, d, rr.mont.entre_fases_real >= 0 && rr.mont.filas.every((f) => f.al_yugo >= 0));
});
console.log(`\n${pruebas - fallas}/${pruebas} comprobaciones del modelo 3D correctas`);
process.exit(fallas ? 1 : 0);
