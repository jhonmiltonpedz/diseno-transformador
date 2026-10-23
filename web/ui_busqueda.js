// ===== 4 · Búsqueda por Vcc: panel, pestaña de resultados, gráfico y «Usar» =====
const CLAVE_BUSQ = "diseno-transformador.busqueda.v3";   // v3: va aparte del diseño (Dn y De propios)
const ORDENES = { peso: "Menor peso (cobre + núcleo)", perdidas: "Menores pérdidas (P0 + I²R)", vcc: "Vcc más cercano al objetivo", cobre: "Menor cobre" };
function normalizarBusqueda(o) {
  const b = copia(OPT_EJEMPLO);
  if (!o || typeof o !== "object") return b;
  for (const k of Object.keys(b)) {
    if (k === "tipos") { for (const t of ["I", "II"]) if (o.tipos && Array.isArray(o.tipos[t])) b.tipos[t] = o.tipos[t].filter((x) => TIPOS[x]); }
    else if (typeof o[k] === "number" && isFinite(o[k]) && (typeof b[k] === "number" || b[k] === null)) b[k] = o[k];
    else if (o[k] === null && typeof b[k] !== "boolean" && typeof b[k] !== "string") b[k] = null;
    else if (b[k] !== null && typeof b[k] === typeof o[k]) b[k] = o[k];
  }
  if (!ORDENES[b.orden]) b.orden = "peso";
  return b;
}
let O = (() => { try { const t = localStorage.getItem(CLAVE_BUSQ); return normalizarBusqueda(t ? JSON.parse(t) : null); } catch (e) { return normalizarBusqueda(null); } })();
function guardarBusqueda() { try { localStorage.setItem(CLAVE_BUSQ, JSON.stringify(O)); } catch (e) { /* sin almacenamiento */ } }
let BUSQ = null;          // { r, o, ediciones }: la última búsqueda
let ediciones = 0;        // cambios hechos a mano en los datos (para saber si la búsqueda quedó vieja)

const GRUPOS_BUSQ = [
  ["Condiciones", [["vcc", "Vcc objetivo (%)<small>sin fuente: se digita</small>"], ["tol", "Tolerancia (± % del Vcc)<small>sin fuente: se digita</small>"],
    ["jmin", "J mínima (A/mm²)<small>sin fuente: se digita (0 = sin mínimo)</small>"], ["jmax", "J máxima (A/mm²)<small>tus condiciones · con la corriente mayor: tensiones y tomas</small>"],
    ["bmin", "B mínima (T)<small>tus condiciones</small>"], ["bmax", "B máxima (T)<small>tus condiciones</small>"]]],
  ["Núcleo a buscar", [["dnFijo", "Dn fijo (mm)<small>0 = buscar en el rango</small>"], ["dnMin", "Dn mínimo (mm)"], ["dnMax", "Dn máximo (mm)"], ["dnPaso", "Paso de Dn (mm)"],
    ["deMax", "De máximo (mm)<small>0 = el mínimo que entra</small>"], ["max", "Resultados a mostrar", "int"]]],
];
function construirBusqueda() {
  $("grupos-busqueda").innerHTML = GRUPOS_BUSQ.map(([titulo, campos]) => `<div><p class="rotulo">${titulo}</p><div class="pares">${
    campos.map(([c, rot, t]) => `<label for="b-${c}">${rot}</label><input class="campo" id="b-${c}" data-o="${c}" data-t="${t || "num"}"
      inputmode="decimal" autocomplete="off" placeholder="digitar">`).join("")}</div></div>`).join("");
  const chips = (k) => Object.keys(TIPOS).map((t) => `<label class="chip-tipo"><input type="checkbox" data-ot="${k}" value="${t}"><span>${F.titulo(t)}</span></label>`).join("");
  $("tipos-busqueda").innerHTML = `
    <div><p class="rotulo">Tipos que se prueban · Devanado I <span class="nota-k" id="hint-I"></span></p><div class="chips">${chips("I")}</div></div>
    <div><p class="rotulo">Tipos que se prueban · secundario <span class="nota-k" id="hint-II"></span></p><div class="chips">${chips("II")}</div></div>
    <div class="fila-busq">
      <label class="lbl-orden" for="b-orden">Ordenar por</label>
      <select class="campo" id="b-orden">${Object.entries(ORDENES).map(([v, t]) => `<option value="${v}">${t}</option>`).join("")}</select>
      <button class="boton principal" id="b-buscar" type="button">Buscar combinaciones</button>
    </div>
    <p class="nota" id="busq-estado" role="status"></p>`;
}
// La búsqueda va aparte del diseño: sus condiciones, Dn y De son propios (no cambian el diseño ni su semáforo).
// Lo único que la une al diseño es «Usar», que pasa la alternativa elegida.
function sincronizarBusqueda(todo = false) {
  for (const el of document.querySelectorAll("[data-o]")) {
    const c = el.dataset.o, v = O[c];
    const escribiendo = !todo && el === document.activeElement;
    const txt = vacio(v) ? "" : String(Number(Number(v).toPrecision(12)));
    if (!escribiendo && el.value !== txt) el.value = txt;
    el.classList.toggle("falta", vacio(v) && (c in ROTULOS_BUSQUEDA || (O.dnFijo === 0 && ["dnMin", "dnMax", "dnPaso"].includes(c))));
  }
  for (const el of document.querySelectorAll("[data-ot]")) el.checked = O.tipos[el.dataset.ot].includes(el.value);
  $("b-orden").value = O.orden;
  const sec = D.dev.II.kva > 0 && D.dev.II.volt > 0 ? "II" : "III";
  const tipoTabla = (t) => (t ? F.titulo(t) : "el de la tabla (todavía sin elegir)");
  $("hint-I").textContent = `· nada marcado = ${tipoTabla(D.dev.I.tipo)}`;
  $("hint-II").textContent = `· nada marcado = ${tipoTabla(D.dev[sec].tipo)}`;
}
function opcionesBusqueda() {
  const o = copia(O);
  o.tipos = { I: O.tipos.I.slice(), II: O.tipos.II.slice(), III: O.tipos.II.slice() };   // el secundario puede ser el II o el III
  return o;
}
function correrBusqueda() {
  $("busq-estado").textContent = "Buscando combinaciones…";
  setTimeout(() => {
    const t0 = performance.now();
    let r;
    try { r = buscarCombinaciones(D, opcionesBusqueda()); }
    catch (ex) { r = { errores: [`No se pudo buscar con estos datos: ${ex.message}`], resultados: [], avisos: [], cuenta: {} }; }
    BUSQ = { r, o: copia(O), ediciones, ms: performance.now() - t0 };
    $("busq-estado").textContent = r.errores.length ? r.errores[0]
      : `${F.miles(r.cuenta.cumplen)} combinaciones cumplen de ${F.miles(r.cuenta.combinaciones)} evaluadas · resultados en la pestaña «Búsqueda».`;
    pestana = "busqueda";
    pintarResultado();
  }, 20);
}

// --- pestaña de resultados ---
const textoCond = (c) => (c.conductor === "ALAMBRE" ? `cal. ${c.medida}` : `${F.g(PLATINAS[c.medida][0])}x${F.g(PLATINAS[c.medida][1])}`);
const textoDev = (c) => `<b>${F.titulo(c.tipo)}</b> · ${textoCond(c)} · ${c.cant} (${c.horiz}x${c.cant / c.horiz}) · ${c.res.capas} ${c.res.capas === 1 ? "capa" : "capas"} · J ${c.jmax.toFixed(2)}${c.fijo ? " · <i>de la tabla</i>" : ""}`;

function marcas(min, max, n = 6) {
  const paso0 = (max - min) / n, pot = 10 ** Math.floor(Math.log10(paso0 || 1)), f = paso0 / pot;
  const paso = (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * pot, out = [];
  for (let v = Math.ceil(min / paso) * paso; v <= max + 1e-9; v += paso) out.push(Math.round(v / paso) * paso);
  return out;
}
const GRAFB = { W: 680, H: 320, ml: 64, mr: 16, mt: 14, mb: 44 };
function graficoBusqueda(todos, actual) {
  const { W, H, ml, mr, mt, mb } = GRAFB;
  const xs = todos.map((p) => p.peso).concat(actual ? [actual.peso] : []), ys = todos.map((p) => p.perdidas).concat(actual ? [actual.perdidas] : []);
  let x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
  const px = (x1 - x0) * 0.05 || 20, py = (y1 - y0) * 0.06 || 50; x0 -= px; x1 += px; y0 -= py; y1 += py;
  const X = (v) => ml + (v - x0) / (x1 - x0) * (W - ml - mr), Y = (v) => mt + (1 - (v - y0) / (y1 - y0)) * (H - mt - mb);
  const f = (v) => v.toFixed(1), o = [];
  for (const v of marcas(y0, y1)) o.push(`<line class="rej" x1="${ml}" x2="${W - mr}" y1="${f(Y(v))}" y2="${f(Y(v))}"/><text class="eje" x="${ml - 7}" y="${f(Y(v) + 4)}" text-anchor="end">${F.miles(v)}</text>`);
  for (const v of marcas(x0, x1)) o.push(`<text class="eje" x="${f(X(v))}" y="${H - mb + 17}" text-anchor="middle">${F.miles(v)}</text>`);
  o.push(`<text class="eje titulo" x="${f((ml + W - mr) / 2)}" y="${H - 6}" text-anchor="middle">Peso activo: cobre + núcleo (kg)</text>`,
    `<text class="eje titulo" x="13" y="${f((mt + H - mb) / 2)}" text-anchor="middle" transform="rotate(-90 13 ${f((mt + H - mb) / 2)})">Pérdidas: P0 + I²R (W)</text>`);
  for (const p of todos) if (!p.pareto) o.push(`<circle class="pt-todo" cx="${f(X(p.peso))}" cy="${f(Y(p.perdidas))}" r="3.5"/>`);
  const frente = todos.filter((p) => p.pareto).sort((a, b) => a.peso - b.peso);
  if (frente.length > 1) o.push(`<path class="linea-par" d="${frente.map((p, i) => `${i ? "L" : "M"}${f(X(p.peso))} ${f(Y(p.perdidas))}`).join("")}"/>`);
  for (const p of frente) o.push(`<circle class="pt-par" cx="${f(X(p.peso))}" cy="${f(Y(p.perdidas))}" r="4.5"/>`);
  const m = todos[0];
  o.push(`<circle class="pt-mejor" cx="${f(X(m.peso))}" cy="${f(Y(m.perdidas))}" r="8"/><text class="valor" x="${f(X(m.peso) + 11)}" y="${f(Y(m.perdidas) - 9)}">1</text>`);
  if (actual) o.push(`<rect class="pt-act" x="${f(X(actual.peso) - 5)}" y="${f(Y(actual.perdidas) - 5)}" width="10" height="10" transform="rotate(45 ${f(X(actual.peso))} ${f(Y(actual.perdidas))})"/>`);
  o.push(`<circle class="foco" r="9" visibility="hidden"/>`, `<rect class="toque" x="${ml}" y="${mt}" width="${W - ml - mr}" height="${H - mt - mb}"/>`);
  GRAFB.escala = { x0, x1, y0, y1 };
  return `<div class="graf-caja"><div class="leyenda-graf"><span><i class="pt-k todo"></i>Cumplen</span><span><i class="pt-k par"></i>Frente de Pareto</span>
    <span><i class="pc"></i>1.º de la lista</span>${actual ? `<span><i class="pa"></i>Diseño actual (Vcc ${actual.uz.toFixed(2)} %)</span>` : ""}</div>
    <div class="graf-desliza"><svg class="graf grafb" viewBox="0 0 ${W} ${H}" role="img" aria-label="Combinaciones que cumplen: peso activo contra pérdidas totales; ${frente.length} en el frente de Pareto">${o.join("")}</svg></div>
    <div class="tip" hidden></div></div>`;
}
function conectarGraficoBusqueda() {
  const svg = document.querySelector("svg.grafb");
  if (!svg || !BUSQ) return;
  const caja = svg.closest(".graf-caja"), tip = caja.querySelector(".tip"), foco = svg.querySelector(".foco");
  const { W, H, ml, mr, mt, mb, escala: e } = GRAFB, todos = BUSQ.r.todos;
  const X = (v) => ml + (v - e.x0) / (e.x1 - e.x0) * (W - ml - mr), Y = (v) => mt + (1 - (v - e.y0) / (e.y1 - e.y0)) * (H - mt - mb);
  const ocultar = () => { tip.hidden = true; foco.setAttribute("visibility", "hidden"); };
  svg.addEventListener("pointermove", (ev) => {
    const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width * W, y = (ev.clientY - r.top) / r.height * H;
    let mejor = null, dmin = (24 / r.width * W) ** 2;
    for (const p of todos) { const dx = X(p.peso) - x, dy = Y(p.perdidas) - y, d2 = dx * dx + dy * dy; if (d2 < dmin) { dmin = d2; mejor = p; } }
    if (!mejor) { ocultar(); return; }
    foco.setAttribute("cx", X(mejor.peso).toFixed(1)); foco.setAttribute("cy", Y(mejor.perdidas).toFixed(1)); foco.setAttribute("visibility", "visible");
    tip.replaceChildren();
    const linea = (valor, nombre) => { const dv = document.createElement("div"); dv.className = "fila-tip sin-k"; const b = document.createElement("b"); b.textContent = valor; const s = document.createElement("span"); s.textContent = nombre; dv.append(b, s); tip.append(dv); };
    const t = document.createElement("div"); t.className = "tit-tip";
    const puesto = todos.indexOf(mejor) + 1;
    t.textContent = `#${puesto} · Dn ${F.g(mejor.dn)} · N ${mejor.n} · B ${mejor.b.toFixed(3)} T${mejor.pareto ? " · Pareto" : ""}`; tip.append(t);
    linea(`${mejor.uz.toFixed(2)} %`, "Vcc");
    linea(`${F.miles(mejor.peso)} kg`, `cobre ${F.miles(mejor.cobre)} + núcleo ${F.miles(mejor.nucleo)}`);
    linea(`${F.miles(mejor.perdidas)} W`, `P0 ${F.miles(mejor.p0)} + I²R ${F.miles(mejor.pcu)}`);
    for (const c of mejor.devanados) if (!c.fijo) linea(`${F.titulo(c.tipo)} ${textoCond(c)}`, `${NOMBRES[c.clave]} · ${c.cant} (${c.horiz}x${c.cant / c.horiz}) · J ${c.jmax.toFixed(2)}`);
    tip.hidden = false;
    const cr = caja.getBoundingClientRect(), xp = r.left - cr.left + X(mejor.peso) / W * r.width, yp = r.top - cr.top + Y(mejor.perdidas) / H * r.height, an = tip.offsetWidth, al = tip.offsetHeight;
    tip.style.left = `${Math.max(4, Math.min(xp + (xp > cr.width / 2 ? -an - 14 : 14), cr.width - an - 4))}px`;
    tip.style.top = `${Math.max(4, Math.min(yp - al / 2, cr.height - al - 4))}px`;
  });
  svg.addEventListener("pointerleave", ocultar);
}

function vistaBusqueda() {
  if (!BUSQ) return bloque("Búsqueda por Vcc", `<p class="vacio">Completa las condiciones del panel Búsqueda y pulsa «Buscar combinaciones».</p>`);
  const { r, o } = BUSQ, c = r.cuenta;
  if (r.errores.length) return bloque("Revisa estos datos antes de buscar", `<ul class="errores">${r.errores.map((e) => `<li>${esc(e)}</li>`).join("")}</ul>`, ' class="alerta"');
  const vieja = BUSQ.ediciones !== ediciones;
  const rango = o.dnFijo > 0 ? `Dn ${F.g(o.dnFijo)} mm` : `Dn ${F.g(o.dnMin)} a ${F.g(o.dnMax)} mm cada ${F.g(o.dnPaso)}`;
  const resumen = `<p class="encabezado"><b>${F.miles(c.cumplen)}</b> combinaciones cumplen de <b>${F.miles(c.combinaciones)}</b> evaluadas (${Math.round(BUSQ.ms)} ms) · ${rango} · B ${o.bmin}–${o.bmax} T · J ${o.jmin}–${o.jmax} A/mm² · Vcc ${o.vcc} % ± ${o.tol} % · ${o.deMax > 0 ? `De ≤ ${F.g(o.deMax)} mm` : "De: el mínimo que entra"}.</p>`;
  const avisos = r.avisos.length ? `<ul class="avisos">${r.avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>` : "";
  const aviejo = vieja ? `<section class="alerta"><h3>Los datos cambiaron después de buscar</h3><p class="vacio">Estos resultados son de los datos anteriores. Vuelve a pulsar «Buscar combinaciones» para usarlos.</p></section>` : "";
  if (!r.resultados.length) return [aviejo, resumen, bloque("Ninguna combinación cumple", `<ul class="errores">${(r.avisos.length ? r.avisos : ["No hay combinaciones con estas condiciones."]).map((a) => `<li>${esc(a)}</li>`).join("")}</ul>`, ' class="alerta"')].join("");
  const actual = R && R.pares && R.vacio ? { peso: R.mont.peso_cu + R.nuc.peso, perdidas: R.vacio.p0 + R.mont.perdidas, uz: R.pares[0].uz } : null;
  const filas = r.resultados.map((a, i) => {
    const sec = a.devanados.find((x) => x.clave !== "I" && !x.fijo), dI = a.devanados.find((x) => x.clave === "I");
    const err = estadoError(a.error) === "ok" ? a.error.toFixed(2) : `<span class="no"><span aria-hidden="true">!</span> ${a.error.toFixed(2)} · procede</span>`;
    return [`<b>${i + 1}</b>`, F.g(a.dn), a.n, a.b.toFixed(3), F.g(a.de), `<b>${a.uz.toFixed(2)}</b>`, err, textoDev(dI), textoDev(sec),
      F.miles(a.cobre), F.miles(a.nucleo), F.miles(a.p0), F.miles(a.pcu), `<b>${F.miles(a.peso)}</b>`, `<b>${F.miles(a.perdidas)}</b>`,
      a.pareto ? "✓" : "", a.verificado ? "✓" : '<span class="no">✗</span>',
      `<span class="acciones-alt"><button class="boton chico usar" type="button" data-alt="${i}"${vieja || !a.verificado ? " disabled" : ""}>Usar</button><button class="boton chico ver3d" type="button" data-alt="${i}" title="Ver la alternativa ${i + 1} en el modelo 3D"${vieja ? " disabled" : ""}>3D</button></span>`];
  });
  const tablaR = `<div class="tabla"><table class="busq"><thead><tr>${["#", "Dn (mm)", "N ref.", "B (T)", "De (mm)", "Vcc (%)", "Error rel. máx. (%)", "Devanado I", "Secundario", "Cobre (kg)", "Núcleo (kg)", "P0 (W)", "I²R (W)", "Peso total (kg)", "Pérdidas totales (W)", "Pareto", "Verif.", ""].map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    filas.map((f) => `<tr>${f.map((x, j) => `<td${j === 7 || j === 8 ? ' class="dev"' : ""}>${x}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
  return [
    aviejo, resumen, avisos,
    bloque(`Peso contra pérdidas · ${F.miles(c.cumplen)} combinaciones`, graficoBusqueda(r.todos, actual)),
    bloque(`Las ${r.resultados.length} primeras por ${ORDENES[o.orden].toLowerCase()}`, tablaR +
      `<p class="nota-tabla">J = densidad con la corriente mayor (tensiones y tomas). Pareto = ninguna otra es más liviana y con menos pérdidas a la vez. Verif. = cargada en el diseño completo da los mismos números. Todas usan «Ajustar a la ventana» con la Hc, papeles, canales y distancias de la pantalla; los anchos de escalón son los óptimos de la tabla para cada Dn (los del diseño si Dn no cambia). El kR es el del cuadro por corriente. Las espiras son las mismas que da el diseño: REDONDEO.MAS con la B máxima. «Usar» carga la alternativa en el diseño: Dn, anchos, De, tipo, conductor y arreglo; las condiciones del diseño (B objetivo, J máxima, Vcc objetivo) no cambian. «3D» la muestra en el modelo 3D sin cargarla.</p>`),
  ].join("");
}

// --- eventos del panel (solo cambian la búsqueda) ---
function leerOpcion(el) {
  if (String(el.value).trim() === "") return null;                   // vacío = sin digitar
  let v = parseFloat(String(el.value).trim().replace(",", "."));
  if (!isFinite(v)) v = 0;
  if (el.dataset.t === "int") v = Math.min(Math.max(Math.trunc(v), 1), 500);
  return v;
}
document.addEventListener("input", (ev) => {
  const el = ev.target;
  if (el.dataset && el.dataset.o) { O[el.dataset.o] = leerOpcion(el); guardarBusqueda(); }
});
document.addEventListener("change", (ev) => {
  const el = ev.target;
  if (el.dataset && el.dataset.o) {
    O[el.dataset.o] = leerOpcion(el); guardarBusqueda();
    sincronizarBusqueda(true);
  }
  else if (el.dataset && el.dataset.ot) {
    const k = el.dataset.ot, set = new Set(O.tipos[k]);
    if (el.checked) set.add(el.value); else set.delete(el.value);
    O.tipos[k] = Object.keys(TIPOS).filter((t) => set.has(t)); guardarBusqueda();
  }
  else if (el.id === "b-orden") { O.orden = el.value; guardarBusqueda(); if (BUSQ && BUSQ.ediciones === ediciones) correrBusqueda(); }
});
document.addEventListener("click", (ev) => {
  if (ev.target.id === "b-buscar") correrBusqueda();
  const b = ev.target.closest && ev.target.closest("button.usar");
  if (b && BUSQ && !b.disabled) {
    const i = Number(b.dataset.alt), alt = BUSQ.r.resultados[i];
    D = normalizar(copia(alt.datos)); guardar(); recalcular(); sincronizar(true);
    BUSQ.ediciones = ediciones;           // cargar una alternativa no deja vieja la búsqueda
    pestana = "resumen"; pintarResultado();
    avisar(`Alternativa ${i + 1} cargada en el diseño: Dn ${F.g(alt.dn)} mm, Vcc ${alt.uz.toFixed(2)} %.`);
  }
});
