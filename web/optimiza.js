// ===== Búsqueda por Vcc: combinaciones de conductores y diámetro del núcleo =====
// Mismo cálculo del diseño (núcleo -> devanados ajustados a la ventana -> distancias), con estas condiciones:
//   - Vcc objetivo ± tolerancia (par Devanado I – primer secundario)
//   - densidad de corriente de cada devanado entre J mín y J máx, con la corriente MAYOR (tensiones y tomas)
//   - inducción real entre B mín y B máx, con espiras enteras
//   - Dn fijo (si se da) o buscado en un rango; Hc fijo; De máximo (0 = se calcula el mínimo que entra)
// Las espiras no dependen de Dn (solo de las espiras de referencia), ni el radial y el axial de cada devanado:
// por eso los devanados candidatos se arman una vez por cada N y luego se combinan para cada Dn.
// Condiciones: J máxima y rango de B son las tuyas; Vcc, tolerancia y J mínima no tienen fuente (null: se digitan).
// Va aparte del diseño: Dn fijo (o el rango) y De máximo son propios de la búsqueda; «Usar» pasa la alternativa al diseño.
const OPT_EJEMPLO = { vcc: null, tol: null, jmin: null, jmax: 4.7, bmin: 1.65, bmax: 1.73, dnFijo: null,
  dnMin: null, dnMax: null, dnPaso: null, deMax: null, tipos: { I: [], II: [] }, orden: "peso", max: 40 };
const ROTULOS_BUSQUEDA = { vcc: "Vcc objetivo", tol: "tolerancia", jmin: "J mínima", jmax: "J máxima", bmin: "B mínima",
  bmax: "B máxima", dnFijo: "Dn fijo", deMax: "De máximo" };
const CONDUCTORES_TODOS = [...Object.keys(ALAMBRES).map((c) => ["ALAMBRE", Number(c)]), ...PLATINAS.map((p, i) => ["PLATINA", i])];

// Arreglos (cantidad, horizontales) que permite cada tipo de devanado
function arreglosTipo(tipo) {
  const r = TIPOS[tipo], out = [];
  for (let h = 1; h <= r.max_h; h++) {
    if (r.h_fijo !== null && h !== r.h_fijo) continue;
    for (let cant = h; cant <= r.max_cond; cant += h) {
      const rad = cant / h;
      if (r.radiales && !r.radiales.includes(rad)) continue;
      out.push([cant, h]);
    }
  }
  return out;
}

// Anchos de escalón para un Dn: los del diseño si es el mismo Dn; si no, los óptimos de la tabla
// con el mismo número de escalones, redondeados a 5 mm y siempre decrecientes.
function anchosParaDn(d, dn) {
  const usados = d.anchos.filter((a) => a > 0);
  if (Math.abs(dn - d.dn) < 1e-9) return usados;
  const n = Math.min(Math.max(usados.length, 1), 10), out = [];
  for (const c of COEFICIENTES_ANCHO[n]) {
    let a = Math.round(dn * c / 5) * 5;
    if (a >= dn) a -= 5;
    if (out.length && a >= out[out.length - 1]) a = out[out.length - 1] - 5;
    if (a > 0) out.push(a);
  }
  return out;
}

function validarBusqueda(d, o) {
  const vacios = Object.keys(ROTULOS_BUSQUEDA).filter((c) => vacio(o[c])).map((c) => ROTULOS_BUSQUEDA[c]);
  if (!vacio(o.dnFijo) && !(o.dnFijo > 0))
    for (const [c, r] of [["dnMin", "Dn mínimo"], ["dnMax", "Dn máximo"], ["dnPaso", "paso de Dn"]]) if (vacio(o[c])) vacios.push(r);
  if (vacios.length) return [`Búsqueda: digita ${vacios.join(", ")}.`];
  const e = [];
  if (!(o.vcc > 0) || !(o.tol > 0)) e.push("Búsqueda: el Vcc objetivo y su tolerancia deben ser mayores que 0.");
  if (!(o.jmin >= 0) || !(o.jmax > o.jmin)) e.push("Búsqueda: la densidad máxima debe ser mayor que la mínima.");
  if (!(o.bmin > 0) || !(o.bmax > o.bmin)) e.push("Búsqueda: la inducción máxima debe ser mayor que la mínima.");
  if (!(o.dnFijo > 0) && (!(o.dnMin > 0) || !(o.dnMax >= o.dnMin) || !(o.dnPaso > 0)))
    e.push("Búsqueda: el rango de Dn no es válido (mínimo, máximo y paso mayores que 0).");
  if (!(o.dnFijo > 0) && o.dnPaso > 0 && (o.dnMax - o.dnMin) / o.dnPaso > 400) e.push("Búsqueda: el rango de Dn tiene más de 400 valores; usa un paso mayor.");
  if (o.deMax < 0) e.push("Búsqueda: el De máximo no puede ser negativo (0 = se calcula).");
  return e;
}

// Devanados candidatos de la clave k con las espiras y corrientes de elec
function candidatosDevanado(k, elec, d, o) {
  const w = d.dev[k], e = elec.dev[k], out = [];
  const tipos = o.tipos[k] && o.tipos[k].length ? o.tipos[k] : [w.tipo];
  const canales = canalesDe(w)[2];
  for (const tipo of tipos) for (const [cant, horiz] of arreglosTipo(tipo)) for (const [cond, med] of CONDUCTORES_TODOS) {
    if (cond === "PLATINA" && vacio(w.papel)) continue;           // sin papel digitado: solo alambres
    const sec = medidasConductor(cond, med, w.papel)[3], s = seccionEspira(cond, sec, cant), jmax = e.i_max / s;
    if (jmax > o.jmax + 1e-9 || jmax < o.jmin - 1e-9) continue;
    const v = ajusteVentana(tipo, cond, med, horiz, w.papel, e.n_max, w.transp, d.hc, w.yugo);
    if (v.capas === null || (v.capas_fijas && !v.entra_fijas)) continue;   // FRANCÉS en sus 2 capas, HÉLICE en una
    const epc = espirasPorSeccion(tipo, e.n_max) / v.capas;
    if (validar(tipo, cant, horiz, e.n_max, epc).length) continue;
    const res = calcularDevanado(tipo, cond, med, cant, horiz, w.papel, e.n_max, epc, w.papel_capa, canales, w.transp, e.i_fase, v.capas, v);
    out.push({ clave: k, tipo, conductor: cond, medida: med, cant, horiz, res, s, jnom: e.i_fase / s, jmax });
  }
  return out;
}

// Devanado que no se optimiza (el III, si se usa): tal como está en la tabla
function devanadoFijo(k, elec, d) {
  const w = d.dev[k], e = elec.dev[k], canales = canalesDe(w)[2];
  const r = TIPOS[w.tipo];
  let cant = Math.min(Math.max(Math.trunc(w.cant), 1), r.max_cond), horiz = Math.min(Math.max(Math.trunc(w.horiz), 1), r.max_h);
  if (r.h_fijo !== null) horiz = r.h_fijo; else if (r.radiales && r.radiales.length === 1 && r.radiales[0] === 1) horiz = cant;
  let ventana = null, capasIn = w.modo === "capas" ? w.capas : null;
  if (w.modo === "ventana") {
    ventana = ajusteVentana(w.tipo, w.calibre[0], w.calibre[1], horiz, w.papel, e.n_max, w.transp, d.hc, w.yugo);
    if (ventana.capas === null || (ventana.capas_fijas && !ventana.entra_fijas)) return null;
    capasIn = ventana.capas;
  }
  const epc = capasIn ? espirasPorSeccion(w.tipo, e.n_max) / capasIn : w.epc;
  if (validar(w.tipo, cant, horiz, e.n_max, epc).length) return null;
  const res = calcularDevanado(w.tipo, w.calibre[0], w.calibre[1], cant, horiz, w.papel, e.n_max, epc, w.papel_capa, canales, w.transp, e.i_fase, capasIn, ventana);
  const s = res.seccion_total;
  return { clave: k, tipo: w.tipo, conductor: w.calibre[0], medida: w.calibre[1], cant, horiz, res, s, jnom: e.i_fase / s, jmax: e.i_max / s, fijo: true };
}

// Datos del diseño con una alternativa aplicada (para cargarla en la pantalla y para verificarla)
function aplicarAlternativa(d, alt, o) {
  const n = JSON.parse(JSON.stringify(d));
  n.dn = alt.dn;
  n.anchos = alt.anchos.concat(new Array(10 - alt.anchos.length).fill(0)).slice(0, 10);
  n.de = alt.de;               // las espiras salen de la B objetivo del diseño, que no se toca: la búsqueda va aparte
  for (const c of alt.devanados) if (!c.fijo)
    Object.assign(n.dev[c.clave], { tipo: c.tipo, calibre: [c.conductor, c.medida], cant: c.cant, horiz: c.horiz, modo: "ventana" });
  return n;
}

function buscarCombinaciones(d, o) {
  d = conPosiciones(d);                       // el Devanado I es siempre el externo
  const falta = faltantes(d);
  const salida = { errores: falta.length ? falta.map((x) => `Para buscar, primero digita estos datos. ${x}`) : validarBusqueda(d, o), resultados: [], avisos: [],
    cuenta: { dn: 0, n: 0, combinaciones: 0, cumplen: 0, candidatos: {}, rechazoDe: 0, rechazoVcc: 0, vccMin: Infinity, vccMax: -Infinity, sinN: [], nRelacion: [], nFijo: [] } };
  if (salida.errores.length) return salida;
  const specs = {};
  for (const k of CLAVES) { const w = d.dev[k]; specs[k] = { kva: w.kva, kva2: w.kva2, volt: w.volt, volt2: w.volt2, conex: w.conex, conex2: w.conex2, bil: w.bil }; }
  // Dn a evaluar
  const dns = [];
  if (o.dnFijo > 0) dns.push(o.dnFijo);
  else for (let i = 0; o.dnMin + i * o.dnPaso <= o.dnMax + 1e-9; i++) dns.push(Math.round((o.dnMin + i * o.dnPaso) * 1000) / 1000);
  // Prueba eléctrica con una espira cualquiera: errores de datos, devanados activos y la tensión de referencia
  const prueba = calcularElectrico(specs, d.frec, d.tap, d.variacion, d.pasos, d.rep, 1e5, d.bobj, 1);
  if (prueba.errores.length) { salida.errores = prueba.errores; return salida; }
  const activos = prueba.elec.activos, sec = prueba.elec.secundarios[0];
  const optimiza = ["I", sec];
  const posiciones = activos.map((k) => d.dev[k].pos);
  if (new Set(posiciones).size !== posiciones.length) { salida.errores = ["Cada devanado debe ir en una posición radial distinta."]; return salida; }
  const orden = [...activos].sort((a, b) => d.dev[a].pos - d.dev[b].pos);
  let vfRef = Infinity;
  for (const k of activos) for (const t of prueba.elec.dev[k].tensiones) vfRef = Math.min(vfRef, t.v_fase);
  const rhoT = RHO_CU_20 * (234.5 + d.tref) / (234.5 + 20), K_TERM = 3 * DENS_CU / 1e6;
  const porN = new Map();    // N -> { elec, cand: {k: [...]}, fijos }
  const todos = [];
  for (const dn of dns) {
    const anchos = anchosParaDn(d, dn);
    if (validarNucleo(dn, d.g, 1, d.hc, FACTOR_ELIPSE, anchos).length) continue;
    const nuc0 = calcularNucleo(dn, d.g, 0, d.hc, FACTOR_ELIPSE, anchos, d.fa), nuc1 = calcularNucleo(dn, d.g, 1, d.hc, FACTOR_ELIPSE, anchos, d.fa);
    const w0 = nuc0.peso, w1 = nuc1.peso - nuc0.peso, sNeta = nuc0.seccion_neta, area = sNeta / 1e6;
    salida.cuenta.dn++;
    // espiras: las mismas del diseño, REDONDEO.MAS con la B máxima (el diseño ya no las da a mano)
    const nLo = Math.max(1, Math.trunc(redondeoMas(vfRef / (K_FEM * d.frec * o.bmax * area), 0)));
    const nHi = Math.floor(vfRef / (K_FEM * d.frec * o.bmin * area) + 1e-9);
    if (nHi < nLo) {      // ninguna cantidad entera de espiras deja B en el rango con este Dn
      const bDe = (N) => vfRef / N / (K_FEM * d.frec * area);
      salida.cuenta.sinN.push({ dn, n1: nHi, b1: nHi >= 1 ? bDe(nHi) : null, n2: nLo, b2: bDe(nLo) });
    }
    for (const N of nLo <= nHi ? [nLo] : []) {       // B de esas espiras dentro del rango
      if (!porN.has(N)) {
        const { errores, elec } = calcularElectrico(specs, d.frec, d.tap, d.variacion, d.pasos, d.rep, sNeta, d.bobj, N);
        let ok = !errores.length, errMax = null;
        if (ok) {
          const errs = elec.taps.map((t) => Math.abs(t.error)).concat(elec.activos.flatMap((k) => elec.dev[k].tensiones.map((t) => Math.abs(t.error))));
          errMax = Math.max(...errs);
          ok = errMax <= ERROR_RELACION_MAX;          // de 0.3 a 0.5 % procede (se marca en rojo en los resultados)
          if (!ok) salida.cuenta.nRelacion.push([N, errMax]);
        }
        const ent = { ok, elec, cand: {}, fijos: {}, errMax };
        if (ok) {
          for (const k of optimiza) ent.cand[k] = candidatosDevanado(k, elec, d, o);
          for (const k of activos) if (!optimiza.includes(k)) {
            ent.fijos[k] = devanadoFijo(k, elec, d);
            if (!ent.fijos[k]) { ent.ok = false; salida.cuenta.nFijo.push([N, k]); }
          }
          for (const k of optimiza) salida.cuenta.candidatos[k] = Math.max(salida.cuenta.candidatos[k] || 0, ent.cand[k].length);
        }
        porN.set(N, ent);
      }
      const ent = porN.get(N);
      if (!ent.ok) continue;
      salida.cuenta.n++;
      const elec = ent.elec, vEsp = vfRef / N, b = vEsp / (K_FEM * d.frec * area);
      const pfe = perdidasEspecificas(b + AUMENTO_B_PERDIDAS, d.frec).pfe;
      const at = elec.dev.I, se = elec.dev[sec];
      const sBase = Math.min(at.kva, se.kva), iSec = corrienteFase(sBase, se.volt, se.conex), iAt = corrienteFase(sBase, at.volt, at.conex);
      const kR = kRogowski(iSec), bKg = b * 10, sFe = sNeta / 100;
      const lista1 = ent.cand.I, lista2 = ent.cand[sec];
      for (let i1 = 0; i1 < lista1.length; i1++) for (let i2 = 0; i2 < lista2.length; i2++) {
        salida.cuenta.combinaciones++;
        const elegido = { I: lista1[i1], [sec]: lista2[i2], ...ent.fijos };
        // montaje del núcleo hacia afuera
        let dPrev = dn, cu = 0, pcu = 0;
        const geo = {};
        for (const k of orden) {
          const c = elegido[k], w = d.dev[k], dInt = dPrev + 2 * w.canal, dExt = dInt + 2 * c.res.radial, dMed = (dInt + dExt) / 2;
          const lEsp = Math.PI * dMed, e = elec.dev[k];
          const rFase = rhoT * e.n_nom * lEsp / 1000 / c.s;
          cu += K_TERM * e.n_max * lEsp * c.s;       // = 3 · N · l/1000 · s · 8.9 / 1000
          pcu += FASES * e.i_carga ** 2 * rFase;
          geo[k] = { dInt, dExt, dMed, rFase, radial: c.res.radial, axial: c.res.axial_total, pos: w.pos };
          dPrev = dExt;
        }
        const dTotal = dPrev + 2 * d.tubo;
        let de;
        if (o.deMax > 0) { if (dTotal + d.fases > o.deMax + 1e-9) { salida.cuenta.rechazoDe++; continue; } de = o.deMax; }
        else de = Math.ceil((dTotal + d.fases) / 5 - 1e-9) * 5;
        const gA = geo.I, gS = geo[sec], [dentro, fuera] = gA.pos < gS.pos ? [gA, gS] : [gS, gA];
        const lam = (fuera.dInt - dentro.dExt) / 2, dM = (gA.dMed + gS.dMed) / 2, hEq = (gA.axial + gS.axial) / 2;
        const ux = (se.n_nom * iSec) * (Math.PI * dM) * (lam + (gA.radial + gS.radial) / 3) * kR * K_VCC / (hEq * bKg * sFe);
        const ur = FASES * (iSec ** 2 * gS.rFase + iAt ** 2 * gA.rFase) / (sBase * 10);
        const uz = Math.hypot(ux, ur);
        if (uz < salida.cuenta.vccMin) salida.cuenta.vccMin = uz;
        if (uz > salida.cuenta.vccMax) salida.cuenta.vccMax = uz;
        if (Math.abs(uz - o.vcc) > o.vcc * o.tol / 100 + 1e-12) { salida.cuenta.rechazoVcc++; continue; }
        const nucleo = w0 + w1 * de, p0 = pfe * nucleo * d.fconst;
        todos.push({ dn, anchos, n: N, b, de, uz, ux, ur, cobre: cu, nucleo, p0, pcu, peso: cu + nucleo, perdidas: p0 + pcu, error: ent.errMax,
          devanados: orden.map((k) => elegido[k]), dTotal, lam });
      }
    }
  }
  salida.cuenta.cumplen = todos.length;
  salida.avisos = explicarBusqueda(salida.cuenta, o, optimiza, d).concat(
    optimiza.filter((k) => vacio(d.dev[k].papel)).map((k) => `${NOMBRES[k]}: sin papel de platina digitado, solo se probaron alambres.`));
  // Frente de Pareto en (peso activo, pérdidas totales)
  const porPeso = todos.map((r, i) => i).sort((a, b) => todos[a].peso - todos[b].peso || todos[a].perdidas - todos[b].perdidas);
  let mejor = Infinity;
  for (const i of porPeso) if (todos[i].perdidas < mejor - 1e-9) { todos[i].pareto = true; mejor = todos[i].perdidas; }
  const criterio = {
    peso: (a, b) => a.peso - b.peso || a.perdidas - b.perdidas,
    perdidas: (a, b) => a.perdidas - b.perdidas || a.peso - b.peso,
    vcc: (a, b) => Math.abs(a.uz - o.vcc) - Math.abs(b.uz - o.vcc) || a.peso - b.peso,
    cobre: (a, b) => a.cobre - b.cobre || a.perdidas - b.perdidas,
  }[o.orden] || ((a, b) => a.peso - b.peso);
  todos.sort(criterio);
  salida.todos = todos;
  salida.resultados = todos.slice(0, o.max).map((r) => {
    // verificación: la alternativa cargada en el diseño completo debe dar lo mismo
    const nd = aplicarAlternativa(d, r, o), v = calcularTodo(nd);
    const igual = (a, b) => Math.abs(a - b) <= 1e-6 * Math.max(1, Math.abs(b));
    r.verificado = !v.errores.length && !!v.pares && igual(v.pares[0].uz, r.uz) && igual(v.mont.peso_cu, r.cobre)
      && igual(v.nuc.peso, r.nucleo) && igual(v.vacio.p0, r.p0) && igual(v.mont.perdidas, r.pcu) && entraEnNucleo(v.mont);
    r.datos = nd;
    return r;
  });
  return salida;
}

// Por qué no salen combinaciones (o salen pocas): en qué condición se quedaron
function explicarBusqueda(c, o, optimiza, d) {
  const t = [], f2 = (x) => x.toFixed(2), f3 = (x) => x.toFixed(3);
  if (!c.dn) t.push("Ningún Dn del rango sirve: revisa que los anchos de escalón sean menores que Dn.");
  if (Math.abs(o.bmax - d.bobj) > 1e-9) t.push(`La B máxima de la búsqueda (${o.bmax} T) no es la B objetivo del diseño (${d.bobj} T): el diseño calcula sus espiras con la suya, así que una alternativa puede no reproducirse («Verif.» ✗) y no se puede usar.`);
  if (c.sinN.length && c.sinN.length === c.dn) {
    const s = c.sinN[0];
    t.push(`${c.dn === 1 ? `Con Dn ${s.dn} no hay` : "En ningún Dn del rango hay"} una cantidad entera de espiras que deje B entre ${o.bmin} y ${o.bmax} T` +
      (c.dn === 1 ? `: ${s.n2} espiras dan ${f3(s.b2)} T${s.b1 ? ` y ${s.n1} dan ${f3(s.b1)} T` : ""}. Cambia Dn o el rango de B.` : "."));
  } else if (c.sinN.length) t.push(`${c.sinN.length} de los ${c.dn} Dn no tienen espiras enteras con B en el rango y se saltaron.`);
  if (!c.n && c.nRelacion.length)
    t.push(`Con las espiras enteras que dejan B en el rango, el error de relación pasa de ${ERROR_RELACION_MAX} %: ` +
      c.nRelacion.slice(0, 3).map(([n, e]) => `${n} espiras dan ${f2(e)} %`).join(", ") + ". Revisa las tensiones o amplía el rango de B.");
  if (!c.n && c.nFijo.length)
    t.push(`El ${NOMBRES[c.nFijo[0][1]]} (no se optimiza: va como está en la tabla) no entra en la ventana con esas espiras.`);
  for (const k of optimiza) if (c.n && c.candidatos[k] === 0)
    t.push(`Ningún conductor del ${NOMBRES[k]} (${(o.tipos[k] && o.tipos[k].length ? o.tipos[k] : [d.dev[k].tipo]).join(", ")}) deja la densidad máxima entre ${o.jmin} y ${o.jmax} A/mm² y entra en la ventana.`);
  if (c.rechazoDe && !c.cumplen && c.rechazoDe === c.combinaciones) t.push(`Ninguna combinación entra en De = ${o.deMax} mm con ${d.fases} mm entre fases.`);
  if (c.combinaciones && !c.cumplen && Number.isFinite(c.vccMin))
    t.push(`El Vcc que se alcanza va de ${f2(c.vccMin)} a ${f2(c.vccMax)} %, fuera de ${o.vcc} % ± ${o.tol} %. Cambia el canal entre devanados, la altura de ventana o los tipos de devanado.`);
  return t;
}

if (typeof module !== "undefined") module.exports = { buscarCombinaciones, OPT_EJEMPLO, aplicarAlternativa, arreglosTipo, anchosParaDn };
