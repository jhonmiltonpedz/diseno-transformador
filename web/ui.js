// ===== Interfaz: una sola pantalla, se recalcula con cada dato =====
const $ = (id) => document.getElementById(id);
const CLAVE_DATOS = "diseno-transformador.datos.v6";     // v6: datos del diseño de referencia y condiciones propias del diseño
const CLAVE_PESTANA = "diseno-transformador.pestana";
const CLAVE_TEMA = "diseno-transformador.tema";          // claro (por defecto) u oscuro
const CLAVE_AV = "diseno-transformador.avanzadas";       // tabla con «Ajuste de capas» y Devanado III
const copia = (o) => JSON.parse(JSON.stringify(o));

// ---------- formatos (los mismos de las hojas en Python) ----------
const F = {
  n: (x) => (Math.abs(x - Math.round(x)) < 1e-9 ? x.toFixed(0) : x.toFixed(2)),          // n()
  g: (x) => String(Number(Number(x).toPrecision(6))),                                       // {:g}
  miles(x, dec = 0) {                                                                        // {:,.0f}
    const t = Math.abs(x).toFixed(dec), [e, f] = t.split(".");
    const neg = x < 0 && Number(t) !== 0;
    return (neg ? "-" : "") + e.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : "");
  },
  signo: (x, dec = 2) => (x >= 0 ? "+" : "") + x.toFixed(dec),                                // {:+.2f}
  g5: (x) => String(Number(x.toPrecision(5))),                                               // {:.5g}
  titulo: (s) => s.toLowerCase().replace(/(^|\s)\S/g, (m) => m.toUpperCase()),
};
const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

// ---------- datos ----------
// Une lo que venga (guardado o pegado) sobre los datos de ejemplo, campo por campo y con su tipo.
function normalizar(o) {
  if (!o || typeof o !== "object" || !o.dev || typeof o.dev !== "object") return null;
  const base = copia(DATOS_EJEMPLO);
  const num = (v, def) => (typeof v === "number" && isFinite(v) ? v : def);
  const numOVacio = (v, def) => (v === null ? null : num(v, def));
  for (const c of Object.keys(base)) {
    if (c === "dev" || c === "anchos") continue;
    if (c === "barrera") { base.barrera = BARRERAS.includes(o.barrera) || o.barrera === null ? o.barrera : base.barrera; continue; }
    base[c] = c === "codigo" || c === "rep" ? (typeof o[c] === "string" ? o[c] : base[c]) : numOVacio(o[c], base[c]);
  }
  if (Array.isArray(o.anchos)) base.anchos = base.anchos.map((v, i) => num(o.anchos[i], i < o.anchos.length ? 0 : v));
  for (const k of CLAVES) {
    const w = o.dev[k], b = base.dev[k];
    if (!w || typeof w !== "object") continue;
    if (w.n_canales === undefined && typeof w.canales === "string") {   // formato anterior: "4+4"
      const [nc, mm] = canalesDe(w); w.n_canales = nc; if (nc > 0) w.canal_mm = mm;
    }
    for (const c of Object.keys(b)) {
      if (c === "calibre") {
        const cal = w.calibre;
        if (Array.isArray(cal) && ((cal[0] === "ALAMBRE" && ALAMBRES[cal[1]]) || (cal[0] === "PLATINA" && PLATINAS[cal[1]])))
          b.calibre = [cal[0], Number(cal[1])];
      } else if (c === "tipo") { if (TIPOS[w.tipo] || w.tipo === null) b.tipo = w.tipo; }
      else if (c === "conex" || c === "conex2") { if (GRUPOS.includes(w[c])) b[c] = w[c]; }
      else if (c === "modo") { if (["ventana", "capas", "epc"].includes(w.modo)) b.modo = w.modo; }
      else b[c] = numOVacio(w[c], b[c]);
    }
  }
  return base;
}
function leerGuardado() {
  try { const t = localStorage.getItem(CLAVE_DATOS); return t ? normalizar(JSON.parse(t)) : null; } catch (e) { return null; }
}
function guardar() { try { localStorage.setItem(CLAVE_DATOS, JSON.stringify(D)); } catch (e) { /* sin almacenamiento */ } }
let D = leerGuardado() || copia(DATOS_EJEMPLO);
let pestana = (() => { try { return localStorage.getItem(CLAVE_PESTANA) || "resumen"; } catch (e) { return "resumen"; } })();
let R = null;                 // último resultado
let DET = [];                 // datos que faltan, campo por campo (con su paso)
let LIM = null;               // límites del diseño con su % de uso (null si todavía no se calcula)
let expAbierta = null;        // resultado con la fórmula a la vista
const leerLocal = (k) => { try { return localStorage.getItem(k); } catch (e) { return null; } };
const ponerLocal = (k, v) => { try { localStorage.setItem(k, v); } catch (e) { /* sin almacenamiento */ } };
let avDev = leerLocal(CLAVE_AV) === "si";
// El Devanado III y el ajuste de capas a mano son opciones avanzadas: se ven si se abren o si ya se usan
const enUsoAvanzado = () => D.dev.III.kva !== 0 || CLAVES.some((k) => D.dev[k].modo !== "ventana");
const clavesVisibles = () => (avDev ? CLAVES : CLAVES.filter((k) => k !== "III"));

// ---------- tabla de devanados ----------
const CALIBRES = [...Object.keys(ALAMBRES).map((c) => ["ALAMBRE", Number(c)]), ...PLATINAS.map((p, i) => ["PLATINA", i])];
const textoCalibre = ([c, m]) => (c === "ALAMBRE" ? `${m}` : `${F.g(PLATINAS[m][0])}x${F.g(PLATINAS[m][1])}`);
const ROT = { kva: "potencia", kva2: "2ª potencia", volt: "tensión", volt2: "2ª tensión", conex: "grupo", conex2: "2º grupo",
  bil: "BIL", calibre: "calibre", cant: "cantidad de conductores", horiz: "horizontales", pos: "posición radial",
  tipo: "tipo de devanado", papel: "papel de platina", papel_capa: "papel entre capas", modo: "ajuste de capas",
  capas: "número de capas", epc: "espiras por capa", canal: "canal interior", yugo: "distancia mínima al yugo",
  n_canales: "N° de canales internos", canal_mm: "medida de cada canal interno (mm)", transp: "transposiciones",
  relleno: "relleno de los extremos (mm)", industrial: "tensión de prueba industrial (kV)" };
const LIMITES = { cant: [1, 48], horiz: [1, 6], capas: [1, 1000000], transp: [0, 100], n_canales: [0, 50] };

function celdaCampo(k, c, t, span = 1) {
  const lim = LIMITES[c] ? ` data-min="${LIMITES[c][0]}" data-max="${LIMITES[c][1]}"` : "";
  const modo = t === "text" ? "text" : t === "int" ? "numeric" : "decimal";
  return `<td${span > 1 ? ` colspan="${span}"` : ""}><input class="campo" data-k="${k}" data-c="${c}" data-t="${t}"${lim}
    inputmode="${modo}" autocomplete="off" spellcheck="false" placeholder="digitar" aria-label="${NOMBRES[k]}: ${ROT[c]}"></td>`;
}
function celdaLista(k, c, opciones, t = "sel", span = 1) {
  const vacia = c === "tipo" ? `<option value="">— digitar —</option>` : "";     // sin fuente: se elige
  const op = vacia + opciones.map(([v, txt]) => `<option value="${v}">${txt}</option>`).join("");
  return `<td${span > 1 ? ` colspan="${span}"` : ""}><select class="campo" data-k="${k}" data-c="${c}" data-t="${t}"
    aria-label="${NOMBRES[k]}: ${ROT[c]}">${op}</select></td>`;
}
const celdaCalc = (id, cls = "", span = 1) => `<td class="calc ${cls}" id="${id}"${span > 1 ? ` colspan="${span}"` : ""}></td>`;

// 1 · Datos del cliente: potencia, tensiones, grupos, BIL y prueba industrial de cada devanado, con sus corrientes
function construirCliente() {
  const G = GRUPOS.map((g) => [g, g]), CV = clavesVisibles();
  const fila = (rot, f) => `<tr><td class="r">${rot}</td>${CV.map(f).join("")}</tr>`;
  const sep = `<tr class="sep"><td colspan="${1 + 2 * CV.length}"></td></tr>`;
  $("tabla-cliente").classList.toggle("dos-dev", CV.length === 2);
  $("tabla-cliente").innerHTML = [
    `<colgroup><col class="r">${"<col>".repeat(2 * CV.length)}</colgroup>`,
    `<thead><tr><td></td>${CV.map((k) => `<th colspan="2" id="cabc-${k}">${NOMBRES[k]}</th>`).join("")}</tr></thead><tbody>`,
    fila("Potencia (kVA)", (k) => celdaCampo(k, "kva", "num") + celdaCampo(k, "kva2", "num")),
    fila("Tensión (V)", (k) => celdaCampo(k, "volt", "num") + celdaCampo(k, "volt2", "num")),
    fila("Grupo", (k) => celdaLista(k, "conex", G) + celdaLista(k, "conex2", G)),
    fila("BIL (kV)", (k) => celdaCampo(k, "bil", "num", 2)),
    fila("Prueba industrial (kV)<small>tensión aplicada · hoja de esfuerzos</small>", (k) => celdaCampo(k, "industrial", "num", 2)),
    sep,
    fila("I línea nominal (A)", (k) => celdaCalc(`x-${k}-il0`) + celdaCalc(`x-${k}-il1`)),
    fila("I fase nominal (A)", (k) => celdaCalc(`x-${k}-if0`) + celdaCalc(`x-${k}-if1`)),
    `</tbody>`,
  ].join("");
}

function construirTabla() {
  const CV = clavesVisibles();
  const fila = (rot, f) => `<tr><td class="r">${rot}</td>${CV.map(f).join("")}</tr>`;
  const doble = (rot, s1, s2, f) => `<tr><td class="r" rowspan="2">${rot}</td>${CV.map(() =>
    `<td class="sub">${s1}</td><td class="sub">${s2}</td>`).join("")}</tr><tr>${CV.map(f).join("")}</tr>`;
  const sep = `<tr class="sep"><td colspan="${1 + 2 * CV.length}"></td></tr>`;
  $("tabla-ingreso").classList.toggle("dos-dev", CV.length === 2);
  $("tabla-ingreso").innerHTML = [
    `<colgroup><col class="r">${"<col>".repeat(2 * CV.length)}</colgroup>`,
    `<thead><tr><td></td>${CV.map((k) => `<th colspan="2" id="cab-${k}">${NOMBRES[k]}</th>`).join("")}</tr></thead><tbody>`,
    fila("Calibre del conductor", (k) => celdaLista(k, "calibre", CALIBRES.map((c) => [c.join(":"), textoCalibre(c)]), "cal")
      + celdaCalc(`x-${k}-ais`, "ais")),
    doble("Arreglo de conductores", "Cantidad", "Horizontal", (k) => celdaCampo(k, "cant", "int") + celdaCampo(k, "horiz", "int")),
    fila("Sección (mm²)", (k) => celdaCalc(`x-${k}-sec`, "", 2)),
    fila("Densidad (A/mm²)", (k) => celdaCalc(`x-${k}-j0`, "dens") + celdaCalc(`x-${k}-j1`, "dens")),
    sep,
    fila("Posición radial<small>fija: el I es el externo</small>", (k) => celdaCalc(`x-${k}-pos`, "", 2)),
    fila("Tipo de devanado", (k) => celdaLista(k, "tipo", Object.keys(TIPOS).map((t) => [t, t]), "sel", 2)),
    doble("Papel (mm)<small>aislamiento menor</small>", "Platina", "Entre capas", (k) => celdaCampo(k, "papel", "num") + celdaCampo(k, "papel_capa", "num")),
    avDev ? fila("Ajuste de capas<small>avanzado: capas a mano</small>", (k) => celdaLista(k, "modo", [["ventana", "Ajustar a la ventana"], ["capas", "N° de capas"], ["epc", "Espiras por capa"]], "sel", 2)) : "",
    doble("Bobinado", "N° capas", "Esp. x capa", (k) => celdaCampo(k, "capas", "int") + celdaCampo(k, "epc", "num")),
    fila("Espiras", (k) => celdaCalc(`x-${k}-esp`, "", 2)),
    doble("Canales internos<small>dentro de la espira, entre conductores · mm</small>", "N° canales", "Medida", (k) => celdaCampo(k, "n_canales", "int") + celdaCampo(k, "canal_mm", "num")),
    fila("Transposiciones<small>cruces de conductores · completa = cantidad − 1</small>", (k) => celdaCampo(k, "transp", "int", 2)),
    `</tbody>`,
  ].join("");
}

// 4 · Distancias eléctricas (aislamiento mayor): mínimos que se ingresan y lo que resulta
function construirDistancias() {
  const CV = clavesVisibles();
  const fila = (rot, f) => `<tr><td class="r">${rot}</td>${CV.map(f).join("")}</tr>`;
  $("tabla-distancias").innerHTML = [
    `<colgroup><col class="r">${"<col>".repeat(CV.length)}</colgroup>`,
    `<thead><tr><td></td>${CV.map((k) => `<th id="cabd-${k}">${NOMBRES[k]}</th>`).join("")}</tr></thead><tbody>`,
    fila("Canal interior (mm)<small>hacia el devanado de adentro; el más interno, hacia el núcleo</small>", (k) => celdaCampo(k, "canal", "num")),
    fila("Al yugo mínimo (mm)", (k) => celdaCampo(k, "yugo", "num")),
    fila("Al yugo resultante (mm)<small>(Hc − axial) / 2</small>", (k) => celdaCalc(`x-${k}-alyugo`, "res")),
    `<tr class="sep"><td colspan="${1 + CV.length}"></td></tr>`,
    fila("Relleno de los extremos (mm)<small>bloques arriba y abajo · hoja de esfuerzos</small>", (k) => celdaCampo(k, "relleno", "num")),
    `</tbody>`,
  ].join("");
  $("pares-fases").innerHTML = `
    <label for="g-tubo">Tubo enrollado exterior (mm)<small>sin fuente: se digita</small></label><input class="campo" id="g-tubo" data-c="tubo" data-t="num" inputmode="decimal" autocomplete="off">
    <label for="g-fases">Entre fases mínimo (mm)<small>sin fuente: se digita</small></label><input class="campo" id="g-fases" data-c="fases" data-t="num" inputmode="decimal" autocomplete="off">
    <span class="lbl">Entre fases resultante (mm)<small>De − Ø exterior con tubo</small></span><output class="res" id="x-fases"></output>`;
  $("pares-esfuerzos").innerHTML = `
    <label for="g-barrera">Barrera entre bobinas<small>HAWAYANO o TUBO · hoja de esfuerzos</small></label><select class="campo" id="g-barrera" data-c="barrera" data-t="sel"><option value="">— digitar —</option>${BARRERAS.map((b) => `<option value="${b}">${b}</option>`).join("")}</select>
    <label for="g-e_barrera">Espesor de la barrera (mm)<small>hoja de esfuerzos</small></label><input class="campo" id="g-e_barrera" data-c="e_barrera" data-t="num" inputmode="decimal" autocomplete="off" placeholder="digitar">
    <label for="g-tubo_rigido">Tubo rígido: largo extra (mm)<small>sobresale la mitad por cada extremo · hoja de esfuerzos</small></label><input class="campo" id="g-tubo_rigido" data-c="tubo_rigido" data-t="num" inputmode="decimal" autocomplete="off" placeholder="digitar">
    <label for="g-tubo_nucleo">Tubo núcleo–bobina (mm)<small>se suma al canal interior del más interno · hoja de esfuerzos</small></label><input class="campo" id="g-tubo_nucleo" data-c="tubo_nucleo" data-t="num" inputmode="decimal" autocomplete="off" placeholder="digitar">`;
}

// ---------- generales, núcleo y anchos ----------
const GRUPOS_NUCLEO = [
  ["Núcleo <span class='fuente'>hoja de núcleo y el diseño de referencia</span>", [["dn", "Diámetro Dn (mm)<small>diseño de referencia</small>", "num"], ["de", "Dist. entre ejes De (mm)<small>limita el diámetro · diseño de referencia</small>", "num"],
    ["hc", "Altura de ventana Hc (mm)<small>limita la altura</small>", "num"], ["g", "Traslape g (mm)", "num"]]],
  ["Flujo", [["bobj", "B máxima = objetivo (T)<small>tus condiciones</small>", "num"],
    ["b_min", "B mínima (T)<small>tus condiciones · vacía = no se verifica</small>", "num"],
    ["fa", "Factor de apilamiento<small>diseño de referencia</small>", "num"],
    ["tref", "T° de referencia (°C)<small>supuesto: 75 °C (IEC 60076-1)</small>", "num"]]],
  ["Pérdidas en el núcleo (vacío) <span class='fuente'>curva de pérdidas de la chapa</span>", [
    ["fconst", "Factor de construcción<small>1 = sin factor</small>", "num"], ["x-pfe", "Pfe con B real + 0.099 (W/kg)", "out"], ["x-p0", "P0 = Pfe x peso x factor (W)", "out"]]],
];
const GRUPOS_CLIENTE = [
  ["Generales", [["codigo", "Código<small>hoja de núcleo</small>", "text"], ["frec", "Frecuencia (Hz)<small>especificaciones del cliente</small>", "num"]]],
  ["Reparto y regulación <span class='fuente'>especificaciones y hoja de datos de entrada</span>", [["rep", "Reparto BT (%)", "text"], ["pasos", "N° de pasos", "int", 1, 99],
    ["variacion", "% variación por paso", "num"], ["tap", "Tap nominal", "int", 1, 99]]],
  ["Especificación · se verifica en el semáforo", [["vcc_obj", "Vcc objetivo (%)<small>sin fuente: se digita · vacío = no se verifica</small>", "num"],
    ["vcc_tol", "Tolerancia (± % del Vcc)<small>sin fuente: se digita</small>", "num"]]],
];
const GRUPOS_DEVANADOS = [
  ["Condición del conductor · se verifica en el semáforo", [["j_max", "J máxima (A/mm²)<small>tus condiciones · con la corriente mayor: tensiones y tomas · vacía = no se verifica</small>", "num"]]],
];
const htmlGrupos = (grupos) => grupos.map(([titulo, campos]) => `<div><p class="rotulo">${titulo}</p><div class="pares">${
    campos.map(([c, rot, t, lo, hi]) => {
      if (t === "out") return `<span class="lbl">${rot}</span><output class="res" id="${c}">—</output>`;
      const lim = lo !== undefined ? ` data-min="${lo}" data-max="${hi}"` : "";
      const modo = t === "text" ? "text" : t === "int" ? "numeric" : "decimal";
      return `<label for="g-${c}">${rot}</label><input class="campo" id="g-${c}" data-c="${c}" data-t="${t}"${lim}
        inputmode="${modo}" autocomplete="off" spellcheck="false">`;
    }).join("")}</div></div>`).join("");
function construirGrupos() {
  $("grupos-nucleo").innerHTML = htmlGrupos(GRUPOS_NUCLEO);
  $("grupos-cliente").innerHTML = htmlGrupos(GRUPOS_CLIENTE);
  $("grupos-devanados").innerHTML = htmlGrupos(GRUPOS_DEVANADOS);
  $("anchos").innerHTML = D.anchos.map((_, i) => `<div class="escalon"><label for="a-${i}">Esc. ${i + 1}</label>
    <input class="campo" id="a-${i}" data-c="anchos" data-i="${i}" data-t="num" inputmode="decimal" autocomplete="off">
    <span class="optimo" id="o-${i}"></span></div>`).join("");
}

// ---------- lectura y escritura de campos ----------
function leerCampo(el) {
  const t = el.dataset.t;
  if (t === "text") return el.value;
  if (t === "sel") return el.value === "" ? null : el.value;
  if (t === "seln") return el.value === "" ? null : Number(el.value);
  if (t === "cal") { const [c, m] = el.value.split(":"); return [c, Number(m)]; }
  const txt = String(el.value).trim();
  if (txt === "" && el.dataset.c !== "anchos") return null;          // vacío = sin digitar
  let v = parseFloat(txt.replace(",", "."));
  if (!isFinite(v)) v = 0;
  if (t === "int") {
    v = Math.trunc(v);
    if (el.dataset.min !== undefined) v = Math.max(v, Number(el.dataset.min));
    if (el.dataset.max !== undefined) v = Math.min(v, Number(el.dataset.max));
  }
  return v;
}
function valorDe(el) {
  const c = el.dataset.c;
  if (c === "anchos") return D.anchos[Number(el.dataset.i)];
  return el.dataset.k ? D.dev[el.dataset.k][c] : D[c];
}
function textoCampo(el, v) {
  if (v === null || v === undefined) return "";
  if (el.dataset.t === "cal") return v.join(":");
  if (typeof v === "number") return String(Number(v.toPrecision(12)));
  return String(v);
}
function aplicar(el) {
  const v = leerCampo(el), c = el.dataset.c;
  if (c === "anchos") D.anchos[Number(el.dataset.i)] = v;
  else if (el.dataset.k) D.dev[el.dataset.k][c] = v;
  else D[c] = v;
  ediciones++;
  guardar();
  recalcular();
}

// Escribe en pantalla los datos (menos el campo que se está escribiendo) y las celdas calculadas
function sincronizar(todo = false) {
  for (const el of document.querySelectorAll(".campo[data-c]")) {
    const k = el.dataset.k, c = el.dataset.c;
    if (k) {
      const w = D.dev[k], ll = R && R.llenado ? R.llenado[k] : null;
      if (c === "horiz") el.disabled = !!(ll && ll.horizFija);
      if (c === "papel") el.disabled = w.calibre[0] === "ALAMBRE";
      if (c === "epc") el.disabled = w.modo === "capas" || w.modo === "ventana";
      if (c === "capas") el.disabled = w.modo === "epc" || w.modo === "ventana";
    }
    if (el.tagName === "INPUT" && el.dataset.k) el.placeholder = el.disabled ? "—" : "digitar";
    el.classList.toggle("falta", faltaCampo(el));
    // el campo que se está escribiendo no se toca hasta que se sale de él (así se puede escribir "0." o "1,5")
    const escribiendo = !todo && el === document.activeElement && el.tagName !== "SELECT" && !el.disabled;
    const txt = textoCampo(el, valorDe(el));
    if (!escribiendo && el.value !== txt) el.value = txt;
  }
  pintarCalculadas();
  if ($("b-orden")) sincronizarBusqueda(todo);
}

// ¿Es un dato que el cálculo necesita y está vacío? (mismas reglas que faltantes)
function faltaCampo(el) {
  if (el.disabled || el.dataset.o) return false;
  const k = el.dataset.k, c = el.dataset.c, v = valorDe(el);
  if (!vacio(v)) return false;
  if (!k) return c in ROTULOS_GENERALES;
  const w = D.dev[k];
  if (c === "kva") return true;
  if (!(w.kva > 0)) return false;
  if (c === "canal_mm") return w.n_canales > 0;
  if (c === "capas") return w.modo === "capas";
  if (c === "epc") return w.modo === "epc";
  if (c === "papel") return w.calibre[0] === "PLATINA";
  return c in ROTULOS_DEVANADO;
}

function pintarCalculadas() {
  const pon = (id, t) => { const el = $(id); if (el) el.textContent = t; };
  const pos = posicionesRadiales(D.dev), nAct = Object.values(pos).filter((p) => p).length;
  for (const k of CLAVES) pon(`x-${k}-pos`, textoPosicion(pos[k], nAct));      // posición radial fija
  let usados = 0;
  for (const k of CLAVES) {
    const e = R && R.entrada ? R.entrada[k] : null;
    const cab = $(`cab-${k}`);
    if (!e || !cab) continue;
    if (e.activo) usados++;
    cab.classList.toggle("off", !e.activo);
    cab.innerHTML = `${NOMBRES[k]}${e.activo ? "" : " <small>sin uso</small>"}`;
    pon(`x-${k}-ais`, e.aislante);
    e.columnas.forEach((col, j) => {
      pon(`x-${k}-il${j}`, col.usada ? col.i_linea.toFixed(2) : "—");
      pon(`x-${k}-if${j}`, col.usada ? col.i_fase.toFixed(2) : "—");
      pon(`x-${k}-j${j}`, col.usada ? col.densidad.toFixed(4) : "—");
    });
    pon(`x-${k}-sec`, e.seccion.toFixed(2));
    const ll = R.llenado[k];
    {   // espiras del devanado; en la galleta, también las de cada una de sus 2 bobinas
      const el = $(`x-${k}-esp`), bob = ll.espiras === null ? null : espirasPorBobina(D.dev[k].tipo, ll.espiras);
      const txt = ll.espiras === null ? "—" : ll.espiras === ll.espirasNom ? `${ll.espiras}` : `${ll.espiras} (nominal ${ll.espirasNom})`;
      if (el) el.innerHTML = esc(txt) + (bob ? `<small class="bobinas">por bobina: ${textoBobinas(bob)}</small>` : "");
    }
    for (const id of [`cabd-${k}`, `cabc-${k}`]) {
      const c = $(id);
      if (c) { c.classList.toggle("off", !e.activo); c.innerHTML = cab.innerHTML; }
    }
  }
  // paso 4: distancias que resultan
  const mont = R && R.mont ? R.mont : null;
  const porClave = mont ? Object.fromEntries(mont.filas.map((f) => [f.clave, f])) : {};
  for (const k of CLAVES) {
    const el = $(`x-${k}-alyugo`), f = porClave[k];
    if (!el) continue;
    el.textContent = f ? F.n(f.al_yugo) : "—";
    el.dataset.ok = f ? (f.margen_yugo >= 0 ? "si" : "no") : "";
    el.title = f ? (f.margen_yugo >= 0 ? `sobran ${F.n(f.margen_yugo)} mm sobre el mínimo` : `faltan ${F.n(-f.margen_yugo)} mm por lado`) : "";
  }
  const vac = R ? R.vacio : null;
  $("x-pfe").textContent = vac ? vac.pfe.toFixed(4) : "—";
  $("x-p0").textContent = vac ? F.miles(vac.p0) : "—";
  $("x-p0").dataset.ok = vac ? "si" : "";
  const xf = $("x-fases");
  xf.textContent = mont ? F.n(mont.entre_fases_real) : "—";
  xf.dataset.ok = mont ? (mont.margen_de >= 0 ? "si" : "no") : "";
  $("nota-holgura").innerHTML = !mont ? "Las distancias resultantes aparecen cuando el núcleo y los devanados están completos."
    : mont.margen_de > 0 ? `Sobran <b>${F.n(mont.margen_de)} mm</b> entre fases sobre el mínimo: se pueden repartir en los canales radiales (1 mm más de canal suma 2 mm al diámetro, o sea hasta ${F.n(mont.margen_de / 2)} mm de canal en total).`
    : mont.margen_de === 0 ? "No sobra espacio entre fases: los canales radiales no se pueden agrandar sin cambiar el núcleo."
    : `<span class="mal">Faltan ${F.n(-mont.margen_de)} mm entre fases:</span> las bobinas de fases vecinas quedan muy juntas. Achica el radial (conductor, capas o canales) o aumenta De.`;
  const re = $("r-entra");
  re.textContent = !mont ? "—" : entraEnNucleo(mont) ? "todo entra en el núcleo" : "no entra en el núcleo";
  re.dataset.ok = !mont ? "" : entraEnNucleo(mont) ? "si" : "no";
  $("r-activos").textContent = `${usados} en uso`;
  const kvaI = D.dev[PRINCIPAL].kva, vI = D.dev[PRINCIPAL].volt;
  $("r-cliente").textContent = vacio(kvaI) || vacio(vI) ? "—" : `${F.g(kvaI)} kVA · ${F.miles(vI)} V · ${D.frec === null ? "—" : F.g(D.frec)} Hz`;
  const nuc = R ? R.nuc : null;
  $("r-seccion").textContent = nuc ? `${(nuc.seccion_neta / 100).toFixed(1)} cm² netos` : "—";
  let j = 0;
  D.anchos.forEach((a, i) => {
    const e = nuc && a > 0 ? nuc.escalones[j++] : null;
    $(`o-${i}`).textContent = e ? e.ancho_optimo.toFixed(1) : "";
  });
  $("chip-codigo").textContent = D.codigo || "sin código";
}

// ---------- cálculo ----------
function recalcular() {
  let r;
  try { r = calcularTodo(D); }
  catch (ex) { r = { errores: [`No se pudo calcular con estos datos: ${ex.message}`], llenado: null, entrada: null, falla: true }; }
  if (r.llenado) {
    for (const k of CLAVES) {
      const w = D.dev[k], ll = r.llenado[k];
      w.cant = ll.cant; w.horiz = ll.horiz;
      // ajustadas a la ventana: salen las dos del cálculo (vacías si el devanado no se pudo calcular, nunca las de antes)
      if (w.modo === "ventana") { w.capas = ll.capas; w.epc = ll.epc; }
      else if (ll.espiras !== null) {
        if (w.modo === "capas") w.epc = ll.epc;
        else if (w.modo === "epc") w.capas = ll.capas;
      }
    }
  }
  R = r;
  if (enUsoAvanzado() && !avDev) ponerAvanzadas(true);     // si se usan, se quedan a la vista
  evaluar();
  sincronizar();
  pintarPasos();
  pintarEstado();
  pintarResultado();
}
// Datos que faltan y límites con las condiciones del propio diseño (Vcc en el paso 1, B en el 2, J en el 3)
const condiciones = () => condicionesDiseno(D);
function evaluar() {
  DET = faltantesDetalle(D);
  LIM = R && R.pares && R.vacio ? limitesDiseno(R.nuc, R.elec, R.mont, R.pares, condiciones(), R.esf) : null;
}

// ---------- pasos con su estado ----------
const ICONO = { ok: "✓", cerca: "⚠", falta: "⚠", procede: "!", no: "✗", pend: "○" };
function pintarPasos() {
  const P = estadoPasos(DET, R.faltan ? [] : R.errores, LIM, !!R.nuc);
  $("pasos-nav").innerHTML = P.map((p) => `<button type="button" class="paso-nav" data-ir="${p.paso}" data-est="${p.estado}">
    <span class="num" aria-hidden="true">${p.paso}</span><span class="nom">${p.nombre}</span>
    <span class="est"><span aria-hidden="true">${ICONO[p.estado]}</span> ${esc(p.texto)}</span></button>`).join("");
}
const suave = () => (matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth");
function irAPaso(p) {
  if (p === ULTIMO_PASO) {
    if (pestana !== "resumen" && !R.errores.length) { pestana = "resumen"; pintarResultado(); }
    $(`panel-${ULTIMO_PASO}`).scrollIntoView({ block: "start", behavior: suave() });
    return;
  }
  const primero = DET.find((x) => x.paso === p);
  if (primero) { enfocarCampo(primero.k, primero.c); return; }
  $(`panel-${p}`).scrollIntoView({ block: "start", behavior: suave() });
}
// Lleva a la celda de un dato (abre las opciones avanzadas si está ahí) y la resalta un momento
function enfocarCampo(k, c) {
  if (k === "III" && !avDev) ponerAvanzadas(true);
  const el = k ? document.querySelector(`.campo[data-k="${k}"][data-c="${c}"]`) : $(`g-${c}`);
  if (!el) return;
  const det = el.closest("details");
  if (det && !det.open) det.open = true;
  el.scrollIntoView({ block: "center", behavior: suave() });
  el.focus({ preventScroll: true });
  el.classList.add("resalta");
  setTimeout(() => el.classList.remove("resalta"), 1800);
}
// Datos que faltan agrupados por paso, cada uno con enlace a su celda
function htmlFaltan(det) {
  return `<div class="faltan">${PASOS.slice(0, ULTIMO_PASO - 1).map(([p, nom]) => [p, nom, det.filter((x) => x.paso === p)]).filter((g) => g[2].length)
    .map(([p, nom, xs]) => `<div class="grupo-f"><span>${p} · ${nom}:</span>${xs.map((x) =>
      `<button type="button" class="chip-falta" data-k="${x.k || ""}" data-c="${x.c}">${esc(x.rotulo)}</button>`).join("")}</div>`).join("")}</div>`;
}
document.addEventListener("click", (ev) => {
  const chip = ev.target.closest && ev.target.closest(".chip-falta");
  if (chip) { enfocarCampo(chip.dataset.k || null, chip.dataset.c); return; }
  const paso = ev.target.closest && ev.target.closest(".paso-nav");
  if (paso) irAPaso(Number(paso.dataset.ir));
});

// ---------- opciones avanzadas ----------
function ponerAvanzadas(abrir) {
  avDev = abrir;
  ponerLocal(CLAVE_AV, abrir ? "si" : "no");
  $("av-devanados").open = abrir;
  construirCliente(); construirTabla(); construirDistancias(); sincronizar(true);
}
$("av-devanados").addEventListener("toggle", (ev) => {
  const det = ev.currentTarget;
  if (det.open === avDev) return;
  if (!det.open && enUsoAvanzado()) {
    det.open = true;
    avisar("El Devanado III o el ajuste de capas a mano están en uso: se quedan a la vista.");
    return;
  }
  ponerAvanzadas(det.open);
});

// ---------- tema ----------
let tema = leerLocal(CLAVE_TEMA) === "oscuro" ? "oscuro" : "claro";
function ponerTema() {
  if (tema === "oscuro") document.documentElement.dataset.tema = "oscuro";
  else delete document.documentElement.dataset.tema;
  $("b-tema").textContent = tema === "oscuro" ? "Tema: oscuro" : "Tema: claro";
}
$("b-tema").addEventListener("click", () => { tema = tema === "oscuro" ? "claro" : "oscuro"; ponerLocal(CLAVE_TEMA, tema); ponerTema(); });

// ---------- estado ----------
function pintarEstado() {
  const el = $("estado"), r = R;
  if (r.faltan) {
    el.dataset.tipo = "aviso";
    el.innerHTML = `<span class="ico" aria-hidden="true">⚠</span>Faltan <b>${DET.length}</b> ${DET.length === 1 ? "dato" : "datos"} sin fuente: <strong>digítalos para calcular</strong>. Toca uno para ir a su celda.${htmlFaltan(DET)}`;
    return;
  }
  if (r.errores.length) {
    el.dataset.tipo = "error";
    el.innerHTML = `<span class="ico" aria-hidden="true">✗</span>` + (r.falla ? esc(r.errores[0])
      : `No se puede calcular todavía: <strong>${r.errores.length} ${r.errores.length === 1 ? "dato por revisar" : "datos por revisar"}</strong>. ${esc(r.errores[0])}`);
    return;
  }
  const vcc = r.pares.map((p) => `Vcc ${PRINCIPAL}–${p.clave} <b>${p.uz.toFixed(2)} %</b>`).join(" · ");
  const cifras = `${vcc} · B real <b>${r.elec.b_real.toFixed(3)} T</b> · cobre <b>${r.mont.peso_cu.toFixed(1)} kg</b> · núcleo <b>${r.nuc.peso.toFixed(0)} kg</b> · vacío <b>${F.miles(r.vacio.p0)} W</b>`;
  const g = limiteGobernante(LIM), malos = LIM.filter((x) => x.estado === "no"), cerca = LIM.filter((x) => x.estado === "cerca");
  const procede = LIM.filter((x) => x.estado === "procede");
  const gob = `gobierna <strong>${esc(descLimite(g))}</strong>`;
  if (malos.length) {
    el.dataset.tipo = "error";
    const noEntra = textosNoEntra(r.nuc, r.mont).length ? "No entra en el núcleo · " : "";
    el.innerHTML = `<span class="ico" aria-hidden="true">✗</span>${noEntra}<strong>${malos.length} ${malos.length === 1 ? "límite no cumple" : "límites no cumplen"}</strong>: ${gob} &nbsp;·&nbsp; ${cifras}`;
  } else if (procede.length) {
    el.dataset.tipo = "procede";
    el.innerHTML = `<span class="ico" aria-hidden="true">!</span>Marca en rojo, pero procede: <strong>${esc(procede[0].nombre)} ${esc(procede[0].valor)}</strong> (de ${F.g(ERROR_RELACION_AVISO)} a ${F.g(ERROR_RELACION_MAX)} %) · ${gob} &nbsp;·&nbsp; ${cifras}`;
  } else if (cerca.length) {
    el.dataset.tipo = "aviso";
    el.innerHTML = `<span class="ico" aria-hidden="true">⚠</span>Cumple, pero cerca del límite: ${gob} &nbsp;·&nbsp; ${cifras}`;
  } else {
    el.dataset.tipo = "ok";
    el.innerHTML = `<span class="ico" aria-hidden="true">✓</span>Cumple los ${LIM.length} límites: ${gob} &nbsp;·&nbsp; ${cifras}`;
  }
}

// ---------- piezas de las hojas ----------
const lista = (pares) => `<dl class="lista">${pares.map(([k, v, fuerte]) =>
  `<dt>${k}</dt><dd${fuerte ? ' class="fuerte"' : ""}>${v}</dd>`).join("")}</dl>`;
const bloque = (titulo, cuerpo, extra = "") => `<section${extra}><h3>${titulo}</h3>${cuerpo}</section>`;
const cifra = (rot, val, destaca) => `<div class="cifra${destaca ? " destaca" : ""}"><span>${rot}</span><b>${val}</b></div>`;
function tablaHtml(enc, filas, total) {
  const tr = (c, cls) => `<tr${cls ? ` class="${cls}"` : ""}>${c.map((x) => `<td>${x}</td>`).join("")}</tr>`;
  return `<div class="tabla"><table><thead><tr>${enc.map((h) => `<th>${h}</th>`).join("")}</tr></thead><tbody>${
    filas.map((f) => tr(f)).join("")}${total ? tr(total, "total") : ""}</tbody></table></div>`;
}
function tablaPasos(pasos) {
  return `<div class="tabla"><table class="pasos"><thead><tr><th>Concepto</th><th>Fórmula</th><th>Valor</th></tr></thead><tbody>${
    pasos.map(([c, f, v, fuerte]) => `<tr${fuerte ? ' class="fuerte"' : ""}><td>${c}</td><td class="f">${f}</td><td><b>${v}</b></td></tr>`).join("")
  }</tbody></table></div>`;
}

// ---------- dibujos ----------
function svgMontaje(nuc, mont) {
  const medio = nuc.de / 2, hc = nuc.hc;
  const anchoMax = Math.max(medio, mont.d_total / 2), altoMax = Math.max(hc, mont.hc_min);
  const s = Math.min(330 / anchoMax, 280 / altoMax), yugo = 16;
  const x0 = 30, y0 = 8 + yugo + Math.max((altoMax - hc) / 2 * s, 0);
  const wV = medio * s, hV = hc * s, wTot = Math.max(anchoMax * s, wV);
  const f = (v) => v.toFixed(1), p = [];
  p.push(`<rect class="nuc" x="${x0}" y="${f(y0 - yugo)}" width="${f(wV)}" height="${yugo}"/>`,
    `<rect class="nuc" x="${x0}" y="${f(y0 + hV)}" width="${f(wV)}" height="${yugo}"/>`,
    `<rect class="nuc" x="${x0}" y="${f(y0)}" width="${f(nuc.dn / 2 * s)}" height="${f(hV)}"/>`,
    `<line class="eje" x1="${x0}" y1="${f(y0 - yugo - 6)}" x2="${x0}" y2="${f(y0 + hV + yugo + 6)}"/>`,
    `<line class="limite" x1="${f(x0 + wV)}" y1="${f(y0 - yugo - 6)}" x2="${f(x0 + wV)}" y2="${f(y0 + hV + yugo + 6)}"/>`);
  const ultima = mont.filas[mont.filas.length - 1];
  for (const fi of mont.filas) {
    const x = x0 + fi.d_int / 2 * s, w = fi.radial * s, ySup = y0 + (hc - fi.axial) / 2 * s;
    const mal = fi.margen_yugo < 0 || (fi.pos === ultima.pos && mont.margen_de < 0);
    // zona útil: entre las líneas de distancia mínima al yugo
    p.push(`<line class="util" x1="${f(x - 3)}" y1="${f(y0 + fi.yugo * s)}" x2="${f(x + w + 3)}" y2="${f(y0 + fi.yugo * s)}"/>`,
      `<line class="util" x1="${f(x - 3)}" y1="${f(y0 + (hc - fi.yugo) * s)}" x2="${f(x + w + 3)}" y2="${f(y0 + (hc - fi.yugo) * s)}"/>`);
    for (let k = 0; k < fi.n_sec; k++) {
      const y = ySup + k * (fi.axial_seccion + SEPARACION_GALLETA) * s;
      p.push(`<rect class="dev${mal ? " mal" : ""}" x="${f(x)}" y="${f(y)}" width="${f(w)}" height="${f(fi.axial_seccion * s)}" fill="${COLORES[fi.clave]}"/>`);
    }
    const yc = y0 + hV / 2, xc = x + w / 2;
    p.push(`<text class="rot" x="${f(xc)}" y="${f(yc)}" text-anchor="middle" dy="3" transform="rotate(-90 ${f(xc)} ${f(yc)})">${fi.nombre}</text>`);
  }
  if (mont.tubo > 0) {
    const alto = Math.max(...mont.filas.map((fi) => fi.axial));
    p.push(`<rect class="tubo" x="${f(x0 + mont.d_dev / 2 * s)}" y="${f(y0 + (hc - alto) / 2 * s)}" width="${f(Math.max(mont.tubo * s, 1.5))}" height="${f(alto * s)}"/>`);
  }
  const xl = x0 + (nuc.de - mont.entre_fases) / 2 * s;      // hasta aquí puede llegar el Ø exterior con tubo
  p.push(`<line class="limite2" x1="${f(xl)}" y1="${f(y0)}" x2="${f(xl)}" y2="${f(y0 + hV)}"/>`);
  const yt = y0 + hV + yugo + 18;
  p.push(`<text class="t" x="${x0}" y="${f(yt)}">eje columna</text>`,
    `<text class="t rojo" x="${f(x0 + wV)}" y="${f(yt)}" text-anchor="end">De/2 = ${F.n(medio)}</text>`,
    `<text class="t" x="${x0 - 8}" y="${f(y0 + hV / 2)}" text-anchor="middle" transform="rotate(-90 ${x0 - 8} ${f(y0 + hV / 2)})">Hc = ${F.n(hc)}</text>`);
  const W = Math.round(x0 + wTot + 12), H = Math.round(yt + 8 + Math.max((altoMax - hc) / 2 * s, 0));
  return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Media ventana con los devanados">${p.join("")}</svg>`;
}

function svgEspira(res) {
  const H = res.horizontales, Rr = res.radiales, a = res.ancho_cond, e = res.esp_cond;
  const s = Math.min(220 / (Rr * e), 150 / (H * a), 40), x0 = 34, y0 = 14, W = Rr * e * s, A = H * a * s;
  const f = (v) => v.toFixed(1), p = [];
  for (let i = 0; i < H; i++) for (let j = 0; j < Rr; j++) {
    const x = x0 + j * e * s, y = y0 + i * a * s;
    if (res.conductor === "PLATINA") {
      const pp = res.papel / 2 * s;
      p.push(`<rect class="papel" x="${f(x)}" y="${f(y)}" width="${f(e * s)}" height="${f(a * s)}"/>`,
        `<rect class="cobre" x="${f(x + pp)}" y="${f(y + pp)}" width="${f(Math.max(e * s - 2 * pp, 0.5))}" height="${f(Math.max(a * s - 2 * pp, 0.5))}"/>`);
    } else {
      const r = e * s / 2;
      p.push(`<circle class="alambre" cx="${f(x + r)}" cy="${f(y + r)}" r="${f(Math.max(r - 0.6, 0.5))}"/>`);
    }
  }
  const yc = y0 + A + 10, xc = x0 - 12;
  p.push(`<line class="cota" x1="${x0}" y1="${f(yc)}" x2="${f(x0 + W)}" y2="${f(yc)}"/>`,
    `<line class="cota" x1="${x0}" y1="${f(yc - 4)}" x2="${x0}" y2="${f(yc + 4)}"/>`,
    `<line class="cota" x1="${f(x0 + W)}" y1="${f(yc - 4)}" x2="${f(x0 + W)}" y2="${f(yc + 4)}"/>`,
    `<text class="t" x="${f(x0 + W / 2)}" y="${f(yc + 14)}" text-anchor="middle">${res.espesor_espira.toFixed(2)}</text>`,
    `<line class="cota" x1="${xc}" y1="${y0}" x2="${xc}" y2="${f(y0 + A)}"/>`,
    `<line class="cota" x1="${xc - 4}" y1="${y0}" x2="${xc + 4}" y2="${y0}"/>`,
    `<line class="cota" x1="${xc - 4}" y1="${f(y0 + A)}" x2="${xc + 4}" y2="${f(y0 + A)}"/>`,
    `<text class="t" x="${xc - 5}" y="${f(y0 + A / 2)}" text-anchor="middle" transform="rotate(-90 ${xc - 5} ${f(y0 + A / 2)})">${res.ancho_espira.toFixed(2)}</text>`);
  const Wt = Math.round(x0 + W + 8), Ht = Math.round(yc + 20);
  return `<svg width="${Wt}" height="${Ht}" viewBox="0 0 ${Wt} ${Ht}" role="img" aria-label="Corte de una espira">${p.join("")}</svg>`;
}

// ---------- vistas ----------
const TEXTO_MODO = { ventana: "Ajustadas a la ventana", capas: "Ingresadas", epc: "Salen de esp. x capa" };

function bloqueNoEntra(r) {
  const t = textosNoEntra(r.nuc, r.mont);
  return t.length ? bloque("No entra en el núcleo", `<ul class="errores">${t.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>
    <p class="vacio">Achica el devanado (conductor, capas, canales o «Ajustar a la ventana») o cambia el núcleo.</p>`, ' class="alerta"') : "";
}

const listaLimites = (nuc, mont) => lista([
  ["Altura de ventana Hc (limita la altura)", `${F.n(nuc.hc)} mm`, true],
  ["Altura que piden los devanados con el mínimo al yugo", `${F.n(mont.hc_min)} mm`],
  ["Distancia entre ejes De (limita el diámetro)", `${F.n(nuc.de)} mm`, true],
  ["Ø exterior con tubo", `${F.n(mont.d_total)} mm`],
  ["De que piden los devanados con el mínimo entre fases", `${F.n(mont.de_min)} mm`],
]);

// Semáforo de límites: % de uso de cada uno (la raya es el 100 %); al tocar una fila se ve su fórmula
const TEXTO_ESTADO = { ok: "cumple", cerca: "cerca del límite", procede: "en rojo", no: "no cumple" };
function bloqueLimites(L) {
  if (!L) return "";
  const g = limiteGobernante(L);
  const orden = [...L].sort((a, b) => PESO_ESTADO[b.estado] - PESO_ESTADO[a.estado] || (b.uso - a.uso));
  const ancho = (u) => (Math.min(isFinite(u) ? u : 1.2, 1.2) / 1.2 * 100).toFixed(1);
  const filas = orden.map((x) => `<button type="button" class="lim" data-est="${x.estado}" aria-expanded="false">
    <span class="ic" aria-hidden="true">${ICONO[x.estado]}</span>
    <span class="nom">${esc(x.nombre)}<small>${TEXTO_ESTADO[x.estado]}${x.nota ? ` · ${esc(x.nota)}` : ""}</small></span>
    <span class="barra" aria-hidden="true"><i style="width:${ancho(x.uso)}%"></i><b></b></span>
    <span class="pct">${pctTexto(x.uso)}</span>
    <span class="val">${esc(x.valor)} · ${esc(x.limite)}</span>
    <span class="formula" hidden>${esc(x.formula)}</span></button>`).join("");
  const C = condiciones(), sin = [];
  if (vacio(C.vcc) || vacio(C.tol)) sin.push("Vcc objetivo y tolerancia (paso 1)");
  if (vacio(C.bmax)) sin.push("B máxima (paso 2)");
  if (vacio(C.jmax)) sin.push("J máxima (paso 3)");
  const nota = sin.length ? `<p class="nota-lim">Sin ${sin.join(", ")}: no se verifica${sin.length > 1 ? "n" : ""}.</p>` : "";
  return bloque("Límites del diseño · % de uso", `<p class="encabezado" style="margin-bottom:8px"><span aria-hidden="true">${ICONO[g.estado]}</span> Gobierna: <b>${esc(descLimite(g))}</b> (${TEXTO_ESTADO[g.estado]}).</p>
    <div class="limites">${filas}</div>
    <p class="nota-lim">Uso = lo exigido / lo disponible. ✗ más de 100 % no cumple · ⚠ desde 90 % está cerca · ! error de relación de ${F.g(ERROR_RELACION_AVISO)} a ${F.g(ERROR_RELACION_MAX)} %: en rojo, procede · la raya marca el 100 %. Toca una fila para ver su fórmula.</p>${nota}`);
}
const PESTANA_DE = { b: "electrico", vesp: "electrico", cobre: "electrico", pcu: "electrico", nucleo: "nucleo", p0: "nucleo" };
function htmlExplica(x) {
  const ir = x.clave.startsWith("vcc") ? "vcc" : PESTANA_DE[x.clave];
  return `<h4>${esc(x.nombre)} = ${esc(x.valor)}</h4>${x.lineas.map((t) => `<p class="m" style="margin:0">${esc(t)}</p>`).join("")}
    <p class="fuente-exp">Fuente: ${esc(x.fuente)}</p><div><button type="button" class="boton chico" data-ir-pestana="${ir}">Ver el desarrollo completo</button></div>`;
}
function vistaResumen(r) {
  const { nuc, elec, mont, pares } = r;
  const X = explicacionesResultados(nuc, elec, mont, pares, r.vacio);
  const cifras = X.map((x) => `<button type="button" class="cifra${x.clave.startsWith("vcc") ? " destaca" : ""}" data-exp="${x.clave}" aria-expanded="${x.clave === expAbierta}" aria-controls="explica">
    <span>${esc(x.nombre)}</span><b>${esc(x.valor)}</b><span class="toca">ver fórmula</span></button>`);
  const abierta = X.find((x) => x.clave === expAbierta);
  const items = verificaciones(nuc, elec, mont, F);
  const lis = items.map(([ok, t]) => `<li${ok === "procede" ? ' class="procede"' : ok ? "" : ' class="no"'}>${esc(t)}</li>`).join("");
  return [
    bloqueNoEntra(r),
    `<div class="cifras">${cifras.join("")}</div>`,
    `<div class="explica" id="explica"${abierta ? "" : " hidden"}>${abierta ? htmlExplica(abierta) : ""}</div>`,
    bloqueLimites(LIM),
    `<details class="detalle-verif"><summary>Detalle de las verificaciones en texto (${items.length})</summary><ul class="verif">${lis}</ul></details>`,
    `<div class="dos">${bloque("Ventana (media sección)", `<div class="dibujo">${svgMontaje(nuc, mont)}</div><p class="pie-dibujo">Líneas punteadas: mínimo al yugo de cada devanado y hasta dónde puede llegar el Ø exterior con el mínimo entre fases.</p>`)}${bloque("Límites del núcleo", listaLimites(nuc, mont))}</div>`,
  ].join("");
}
// tocar un resultado muestra su fórmula; tocar un límite, la suya
$("resultado").addEventListener("click", (ev) => {
  const c = ev.target.closest("button[data-exp]");
  if (c) {
    expAbierta = expAbierta === c.dataset.exp ? null : c.dataset.exp;
    const X = explicacionesResultados(R.nuc, R.elec, R.mont, R.pares, R.vacio), x = X.find((y) => y.clave === expAbierta);
    const caja = $("explica");
    caja.hidden = !x; caja.innerHTML = x ? htmlExplica(x) : "";
    for (const b of document.querySelectorAll("button[data-exp]")) b.setAttribute("aria-expanded", String(b.dataset.exp === expAbierta));
    return;
  }
  const l = ev.target.closest("button.lim");
  if (l) {
    const f = l.querySelector(".formula"), abrir = f.hidden;
    f.hidden = !abrir; l.setAttribute("aria-expanded", String(abrir));
    return;
  }
  const ir = ev.target.closest("button[data-ir-pestana]");
  if (ir) { pestana = ir.dataset.irPestana; ponerLocal(CLAVE_PESTANA, pestana); pintarResultado(); $(`panel-${ULTIMO_PASO}`).scrollIntoView({ block: "start", behavior: suave() }); }
});

// Esfuerzos dieléctricos (hoja de esfuerzos): tabla como la hoja, dibujo del contorno y desarrollo
function svgContorno(x, relIn, relOut, canal, radial, colIn, colOut) {
  const lado = canal / 2, s = D.tubo_rigido / 2, R = FACTOR_RADIAL_CONTORNO * radial, e = D.e_barrera;
  const k = 300 / Math.max(30 + 2 * lado + e + radial, 1), altoCu = 60, f = (v) => v.toFixed(1);
  const y0 = 40 + (Math.max(relIn, relOut, 1) + s) * k, xb = 20;
  const xb1 = xb + 30 * k + lado * k, eb = Math.max(e * k, 2), xa = xb1 + eb + lado * k;
  const yt = y0 - (Math.max(relIn, relOut) + s) * k;
  const rect = (x0, y, w, h, cls, fill) => `<rect class="${cls}" x="${f(x0)}" y="${f(y)}" width="${f(w)}" height="${f(h)}"${fill ? ` fill="${fill}"` : ""}/>`;
  const p = [rect(xb, y0, 30 * k, altoCu, "dev", colIn), rect(xb, y0 - relIn * k, 30 * k, relIn * k, "relleno"),
    rect(xa, y0, radial * k, altoCu, "dev", colOut), rect(xa, y0 - relOut * k, radial * k, relOut * k, "relleno"),
    rect(xb1, yt, eb, y0 + altoCu - yt, "papel")];
  let pts, nombres;
  if (D.barrera === "HAWAYANO") {
    pts = [[xb + 30 * k, y0], [xb1, yt], [xb1 + eb, yt], [xa + R * k, yt], [xa, y0 - relOut * k], [xa, y0]];
    nombres = ["d1", "", "d2", "d3", "d4"];
    p.push(`<path class="hawayano" d="M${f(xb1 + eb)} ${f(yt)} L${f(xa + radial * k + 4)} ${f(yt)} L${f(xa + radial * k + 4)} ${f(yt + 6)}"/>`);
  } else {
    pts = [[xb + 30 * k, y0], [xb1, yt], [xb1 + eb, yt], [xa, y0]];
    nombres = ["d1", "", "d5"];
  }
  p.push(`<polyline class="contorno" points="${pts.map(([a, b]) => `${f(a)},${f(b)}`).join(" ")}"/>`);
  const DESPLAZA = { d1: [-18, 4], d2: [-6, -6], d3: [-6, 16], d4: [4, 4], d5: [6, 4] };      // rótulos fuera de las líneas
  pts.slice(1).forEach(([a2, b2], i) => {
    const [a1, b1] = pts[i], t = nombres[i];
    if (t) p.push(`<text class="rot-c" x="${f((a1 + a2) / 2 + DESPLAZA[t][0])}" y="${f((b1 + b2) / 2 + DESPLAZA[t][1])}">${t}</text>`);
  });
  const W = Math.round(xa + radial * k + 30), H = Math.round(y0 + altoCu + 8);
  p.push(`<text class="t" x="${xb}" y="${f(y0 + altoCu - 4)}">${esc(x.nombre.split(" – ")[0])}</text>`, `<text class="t" x="${f(xa)}" y="${f(y0 + altoCu - 4)}">${esc(x.nombre.split(" – ")[1])}</text>`);
  return `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="Contorno entre ${esc(x.nombre)}: ${nombres.filter(Boolean).join(", ")}">${p.join("")}</svg>`;
}
function bloqueEsfuerzos(r) {
  if (!r.esf || !r.esf.length) return "";
  const por = Object.fromEntries(r.mont.filas.map((f) => [f.clave, f])), dibujos = [], u1 = unoTexto;
  const filas = r.esf.map((x) => {
    const L = limiteEsfuerzo(x), e = L.estado, mal = e === "no" || e === "procede";
    const est = `<span class="${mal ? "no" : ""}"><span aria-hidden="true">${ICONO[e]}</span> ${TEXTO_ESTADO[e]}</span>`;
    const val = `<b${mal ? ' class="no"' : ""}>${kvmm(x.esfuerzo)}</b>`;
    if (x.tipo === "bob-nuc")
      return [`${esc(x.nombre)}<small class="sub-par">núcleo – bobina</small>`, val, esc(L.limite), est, F.g(x.tension), `<b>${F.n(x.distancia)}</b>`, "—", "—", "—", "—", "—", "—"];
    const q = x.partes, tubo = D.barrera === "TUBO", [ci, co] = x.clave.split("-").slice(1);
    dibujos.push(`<figure class="contorno-fig"><figcaption>${esc(x.nombre)}</figcaption>${svgContorno(x, D.dev[ci].relleno, D.dev[co].relleno, por[co].canal, por[co].radial, COLORES[ci], COLORES[co])}</figure>`);
    return [`${esc(x.nombre)}<small class="sub-par">contorneo · ${D.barrera}</small>`, val, esc(L.limite), est, F.g(x.tension), `<b>${u1(x.distancia)}</b>`,
      u1(q.d1), F.g(q.e), tubo ? "—" : u1(q.d2), tubo ? "—" : u1(q.d3), tubo ? "—" : u1(q.d4), tubo ? u1(q.d5) : "—"];
  });
  const det = r.esf.map((x) => `<p class="m" style="margin:4px 0"><b>${esc(x.nombre)}:</b> ${x.lineas.map(esc).join(" · ")}</p>`).join("");
  return bloque("Esfuerzos dieléctricos · hoja de esfuerzos (prueba industrial / distancia)",
    tablaHtml(["Par", "E (kV/mm)", "Límite", "Estado", "Prueba (kV)", "Distancia (mm)", "d1", "Barrera", "d2", "d3", "d4", "d5"], filas)
    + (dibujos.length ? `<div class="contornos dibujo">${dibujos.join("")}</div><p class="pie-dibujo">Sin escala. Línea punteada: el contorno por encima de la barrera, desde el cobre de la bobina de adentro hasta el de la de afuera.${D.barrera === "HAWAYANO" ? " En azul, el hawayano que cubre el extremo de la bobina de afuera." : ""}</p>` : "")
    + `<details class="detalle-verif"><summary>Desarrollo del cálculo</summary>${det}</details>`
    + `<p class="nota-tabla">Entre bobinas se usa la mayor de las dos pruebas industriales y el canal interior se reparte por mitades a cada lado de la barrera. Límites de la hoja de esfuerzos: bobina–bobina ${F.g(ESFUERZO_BOB_BOB)} kV/mm; núcleo–bobina ${F.g(ESFUERZO_BOB_NUC)} kV/mm, de ${F.g(ESFUERZO_BOB_NUC)} a ${F.g(ESFUERZO_BOB_NUC_MAX)} en rojo pero procede.</p>`);
}

function vistaDistancias(r) {
  const { nuc, mont } = r, resPor = Object.fromEntries(r.lista.map((i) => [i.clave, i.res]));
  const filasMont = mont.filas.map((f) => {
    const res = resPor[f.clave];
    return [`${f.pos} · <b>${f.nombre}</b>`, F.titulo(res.tipo), TEXTO_MODO[D.dev[f.clave].modo], res.capas, F.n(res.esp_por_capa),
      F.n(f.canal), F.n(f.d_int), F.n(f.radial), F.n(f.d_ext), F.n(f.d_med), F.n(f.axial)];
  });
  const margen = (x) => (x >= 0 ? `<span class="si">+${F.n(x)}</span>` : `<span class="no">−${F.n(-x)} (faltan)</span>`);
  const filas = [];
  let anterior = "Núcleo";
  for (const f of mont.filas) { filas.push([`${anterior} → ${f.nombre} (canal interior)`, "radial", "—", F.n(f.canal), "ingresado"]); anterior = f.nombre; }
  for (const f of mont.filas) filas.push([`${f.nombre} → yugo (arriba y abajo)`, "axial", F.n(f.yugo), F.n(f.al_yugo), margen(f.margen_yugo)]);
  filas.push(["Tubo enrollado exterior", "radial", "—", F.n(mont.tubo), "ingresado"]);
  filas.push(["Entre fases (bobina con bobina)", "radial", F.n(mont.entre_fases), F.n(mont.entre_fases_real), margen(mont.margen_de)]);
  const nota = mont.margen_de > 0
    ? `Sobran ${F.n(mont.margen_de)} mm entre fases: se pueden repartir en los canales radiales (1 mm más de canal suma 2 mm al diámetro, o sea hasta ${F.n(mont.margen_de / 2)} mm de canal en total).`
    : "No sobra espacio entre fases: no se puede agrandar ningún canal radial sin cambiar el núcleo.";
  return [
    `<p class="encabezado">Con el núcleo y los devanados ya fijos, esto es lo que queda: <b>aislamiento mayor</b> entre partes (núcleo, devanados, yugo y fases vecinas). El aislamiento menor (papel de platina, papel entre capas y canales internos) va dentro de cada devanado.</p>`,
    bloqueNoEntra(r),
    bloque("3 · Devanados dentro de la ventana (mm, del núcleo hacia afuera)", tablaHtml(["Pos. · Dev.", "Tipo", "Ajuste de capas", "N° capas", "Esp. x capa", "Canal int.", "Ø int.", "Radial", "Ø ext.", "Ø medio", "Axial"], filasMont)),
    bloque("4 · Distancias eléctricas: aislamiento mayor (mm)", tablaHtml(["Aislamiento mayor", "Dirección", "Mínimo", "Resultante", "Margen"], filas) + `<p class="nota-tabla">${nota}</p>`),
    bloqueEsfuerzos(r),
    `<div class="dos">${bloque("Ventana (media sección)", `<div class="dibujo">${svgMontaje(nuc, mont)}</div><p class="pie-dibujo">Líneas punteadas: mínimo al yugo de cada devanado y hasta dónde puede llegar el Ø exterior con el mínimo entre fases.</p>`)}${bloque("Límites del núcleo", listaLimites(nuc, mont))}</div>`,
  ].join("");
}

function vistaElectrico(r) {
  const { nuc, elec, mont, lista: items } = r, dev = elec.dev;
  const resPor = Object.fromEntries(items.map((i) => [i.clave, i.res])), monPor = Object.fromEntries(mont.filas.map((f) => [f.clave, f]));
  const filas = [];
  for (const k of elec.activos) {
    const d = dev[k], res = resPor[k], m = monPor[k];
    d.tensiones.forEach((tn, j) => {
      let esp = `${tn.n}`;
      if (j === 0 && k === PRINCIPAL && elec.n_pasos > 1)
        esp += ` (tomas ${Math.min(...elec.taps.map((t) => t.espiras))}–${Math.max(...elec.taps.map((t) => t.espiras))})`;
      const pri = j === 0;
      filas.push([pri ? `<b>${d.nombre}</b>` : "&nbsp;&nbsp;2ª tensión", pri ? m.pos : "", tn.conex, F.miles(tn.volt), F.miles(tn.v_fase, 1),
        tn.i_linea.toFixed(1), tn.i_fase.toFixed(1), esp, htmlError(tn.error), pri ? F.titulo(res.tipo) : "",
        pri ? `${res.cantidad} x ${res.nombre.replace(" mm", "")}` : "", pri ? res.seccion_total.toFixed(2) : "",
        (tn.i_fase / res.seccion_total).toFixed(2)]);
    });
  }
  const ref = dev[elec.ref];
  const origen = elec.n_ref_manual ? "ingresadas" : `REDONDEO.MAS(${elec.n_teorico.toFixed(2)})`;
  const flujo = [
    ["Sección bruta del núcleo", `${(nuc.seccion_bruta / 100).toFixed(1)} cm²`], ["Factor de apilamiento", F.g(nuc.factor_apilamiento)],
    ["Sección neta", `${(nuc.seccion_neta / 100).toFixed(1)} cm²`, true], ["Inducción objetivo", `${F.g(elec.b_objetivo)} T`],
    [`Espiras de referencia (${ref.nombre}, ${F.g(elec.ref_volt)} V)`, `${elec.n_ref} (${origen})`],
    ["Voltios por espira", `${elec.v_esp.toFixed(3)} V`, true], ["Inducción real", `${elec.b_real.toFixed(3)} T`, true],
    ["Peso del núcleo", `${nuc.peso.toFixed(0)} kg`],
  ];
  flujo.push([`Pérdidas específicas Pfe (${MATERIAL_NUCLEO}${r.vacio.manual ? ", a mano" : ""})`, `${r.vacio.pfe.toFixed(4)} W/kg`],
    ["Pérdidas en el núcleo (vacío) P0", `${F.miles(r.vacio.p0)} W`, true]);
  const taps = elec.taps.map((t) => [`${t.pos}${t.pos === elec.tap_nom ? " (nominal)" : ""}`, `${F.signo(t.pct)}%`, F.miles(t.v_linea),
    t.espiras, F.miles(t.v_linea_real), htmlError(t.error)]);
  const cu = mont.filas.map((f) => [`<b>${f.nombre}</b>`, f.l_espira.toFixed(0), f.long_fase.toFixed(1), f.peso.toFixed(1),
    F.g5(f.r_fase), `${F.g(dev[f.clave].reparto)}%`, f.i_carga.toFixed(1), F.miles(f.perdidas)]);
  return [
    bloque("Cálculo eléctrico", tablaHtml(["Dev.", "Pos.", "Grupo", "V línea", "V fase", "I línea (A)", "I fase (A)", "Espiras",
      "Error rel.", "Tipo", "Conductor", "mm²", "J (A/mm²)"], filas)),
    `<div class="dos">${bloque("Núcleo y flujo", lista(flujo))}${bloque(`Regulación en el ${dev[PRINCIPAL].nombre} · posición 1 = mayor tensión`,
      tablaHtml(["Posición", "Variación", "V línea", "Espiras", "V línea real", "Error"], taps))}</div>`,
    bloque(`Verificación del error de relación · máx. ${F.g(ERROR_RELACION_MAX)} %, en rojo desde ${F.g(ERROR_RELACION_AVISO)} % pero procede`,
      tablaHtml(["Tensión / toma", "Espiras", "Error", "Estado"], erroresRelacion(elec).map((x) => [esc(x.quien), x.espiras, htmlError(x.error, true),
        `<span class="${x.estado === "ok" ? "" : "no"}"><span aria-hidden="true">${ICONO[x.estado]}</span> ${TEXTO_ERROR[x.estado]}</span>`]))
      + `<p class="nota-tabla">Hasta ${F.g(ERROR_RELACION_AVISO)} % cumple · de ${F.g(ERROR_RELACION_AVISO)} a ${F.g(ERROR_RELACION_MAX)} % se marca en rojo pero <b>procede</b> · más de ${F.g(ERROR_RELACION_MAX)} % <b>no procede</b>.</p>`),
    bloque("Cobre, resistencia y pérdidas en carga", tablaHtml(["Dev.", "Espira media (mm)", "Conductor por fase (m)", `Cobre ${FASES} fases (kg)`,
      `R fase a ${F.g(mont.t_ref)} °C (Ω)`, "Carga", "I fase (A)", "I²R (W)"], cu,
      ["TOTAL", "", "", mont.peso_cu.toFixed(1), "", "", "", F.miles(mont.perdidas)])
      + `<p class="nota-tabla">Pérdidas I²R en corriente continua con el reparto de carga ${esc(elec.rep_carga)}; no incluyen pérdidas adicionales.</p>`),
  ].join("");
}

// Error de relación en una celda: normal hasta 0.3 %; en rojo de 0.3 a 0.5 % (procede) y más de 0.5 % (no procede)
function htmlError(e, corto = false) {
  const er = estadoError(e);
  return er === "ok" ? `${F.signo(e)}%` : `<span class="no"><span aria-hidden="true">${ICONO[er]}</span> ${F.signo(e)}%${corto ? "" : ` · ${TEXTO_ERROR[er]}`}</span>`;
}

// Ecuación de la curva ajustada
function ecuacionPerdidas(f) {
  const c = COEF_PERDIDAS[f], t = (x) => `${x < 0 ? "−" : "+"} ${Math.abs(x).toFixed(5)}`;
  return `Pfe = ${c[0] < 0 ? "−" : ""}${Math.abs(c[0]).toFixed(5)} ${t(c[1])}·B ${t(c[2])}·B²`;
}

// Gráfico: tabla del fabricante, las dos curvas de la regresión y el punto del diseño (con lectura al pasar el cursor)
const GRAF = { W: 640, H: 300, ml: 46, mr: 14, mt: 14, mb: 40 };
function graficoPerdidas(vac) {
  const { W, H, ml, mr, mt, mb } = GRAF, b0 = 0.4, b1 = Math.max(2.0, Math.ceil((vac.b + 0.05) * 10) / 10);
  const pmax = Math.max(pfeCurva(60, b1), vac.pfe, 2.5), ymax = Math.ceil(pmax / 0.5) * 0.5;
  const X = (b) => ml + (b - b0) / (b1 - b0) * (W - ml - mr), Y = (q) => mt + (1 - q / ymax) * (H - mt - mb);
  const f = (v) => v.toFixed(1), o = [];
  const paso = ymax > 3 ? 1 : 0.5;
  for (let q = 0; q <= ymax + 1e-9; q += paso)
    o.push(`<line class="rej" x1="${ml}" x2="${W - mr}" y1="${f(Y(q))}" y2="${f(Y(q))}"/>`,
      `<text class="eje" x="${ml - 7}" y="${f(Y(q) + 4)}" text-anchor="end">${q.toFixed(1)}</text>`);
  for (let i = 0; b0 + i * 0.2 <= b1 + 1e-9; i++) {
    const b = b0 + i * 0.2;
    o.push(`<text class="eje" x="${f(X(b))}" y="${H - mb + 17}" text-anchor="middle">${b.toFixed(1)}</text>`);
  }
  o.push(`<text class="eje titulo" x="${f((ml + W - mr) / 2)}" y="${H - 5}" text-anchor="middle">Inducción B (T)</text>`,
    `<text class="eje titulo" x="12" y="${f((mt + H - mb) / 2)}" text-anchor="middle" transform="rotate(-90 12 ${f((mt + H - mb) / 2)})">Pfe (W/kg)</text>`);
  const tramo = (fr, desde, hasta) => {
    let d = "";
    for (let i = 0; desde + i * 0.01 <= hasta + 1e-9; i++) { const b = desde + i * 0.01; d += `${d ? "L" : "M"}${f(X(b))} ${f(Y(pfeCurva(fr, b)))}`; }
    return d;
  };
  for (const fr of [50, 60]) {
    o.push(`<path class="curva s${fr} extra" d="${tramo(fr, b0, B_TABLA_MIN)}"/>`, `<path class="curva s${fr}" d="${tramo(fr, B_TABLA_MIN, B_TABLA_MAX)}"/>`,
      `<path class="curva s${fr} extra" d="${tramo(fr, B_TABLA_MAX, b1)}"/>`);
  }
  for (const [b, p50, p60] of TABLA_PERDIDAS)
    o.push(`<circle class="punto s50" cx="${f(X(b))}" cy="${f(Y(p50))}" r="4"/>`, `<circle class="punto s60" cx="${f(X(b))}" cy="${f(Y(p60))}" r="4"/>`);
  const xc = X(vac.b), yc = Y(vac.pfe), izq = xc > (ml + W - mr) / 2;
  o.push(`<line class="guia" x1="${f(xc)}" x2="${f(xc)}" y1="${f(yc)}" y2="${f(Y(0))}"/>`,
    `<circle class="calc" cx="${f(xc)}" cy="${f(yc)}" r="6"/>`,
    `<text class="valor" x="${f(xc + (izq ? -12 : 12))}" y="${f(yc - 10)}" text-anchor="${izq ? "end" : "start"}">${vac.pfe.toFixed(4)} W/kg</text>`,
    `<text class="eje" x="${f(xc + (izq ? -12 : 12))}" y="${f(yc + 6)}" text-anchor="${izq ? "end" : "start"}">${vac.b.toFixed(3)} T (B real + ${F.g(AUMENTO_B_PERDIDAS)}) · ${F.g(vac.f)} Hz${vac.manual ? " · a mano" : ""}</text>`,
    `<line class="cruz" x1="0" x2="0" y1="${mt}" y2="${H - mb}" visibility="hidden"/>`,
    `<rect class="toque" x="${ml}" y="${mt}" width="${W - ml - mr}" height="${H - mt - mb}"/>`);
  return `<div class="graf-caja"><div class="leyenda-graf"><span><i class="k s50"></i>Regresión 50 Hz</span><span><i class="k s60"></i>Regresión 60 Hz</span>
    <span><i class="pt"></i>Tabla del fabricante</span><span><i class="pc"></i>Punto del diseño</span><span class="nota-k">punteado: fuera de la tabla</span></div>
    <div class="graf-desliza"><svg class="graf" viewBox="0 0 ${W} ${H}" data-b0="${b0}" data-b1="${b1}" tabindex="0" role="img"
      aria-label="Pérdidas específicas de la plancha ${MATERIAL_NUCLEO} contra la inducción, a 50 y 60 Hz; el diseño trabaja a ${vac.b.toFixed(3)} T con ${vac.pfe.toFixed(4)} W/kg">${o.join("")}</svg></div>
    <div class="tip" hidden></div></div>`;
}
function conectarGrafico() {
  const svg = document.querySelector("svg.graf");
  if (!svg) return;
  const { W, ml, mr, mt, H, mb } = GRAF, b0 = Number(svg.dataset.b0), b1 = Number(svg.dataset.b1);
  const caja = svg.closest(".graf-caja"), cruz = svg.querySelector(".cruz"), tip = caja.querySelector(".tip");
  let bAct = null;
  const mostrar = (b, px) => {
    b = Math.min(Math.max(Math.round(b * 100) / 100, b0), b1); bAct = b;
    const x = ml + (b - b0) / (b1 - b0) * (W - ml - mr);
    cruz.setAttribute("x1", x.toFixed(1)); cruz.setAttribute("x2", x.toFixed(1)); cruz.setAttribute("visibility", "visible");
    tip.replaceChildren();
    const fila = (cls, nombre, valor) => {
      const d = document.createElement("div"); d.className = "fila-tip";
      if (cls) { const k = document.createElement("i"); k.className = `k ${cls}`; d.append(k); }
      const v = document.createElement("b"); v.textContent = valor; const n = document.createElement("span"); n.textContent = nombre;
      d.append(v, n); tip.append(d);
    };
    const t = document.createElement("div"); t.className = "tit-tip"; t.textContent = `B = ${b.toFixed(2)} T`; tip.append(t);
    fila("s60", "60 Hz regresión", `${pfeCurva(60, b).toFixed(4)} W/kg`);
    fila("s50", "50 Hz regresión", `${pfeCurva(50, b).toFixed(4)} W/kg`);
    const enTabla = TABLA_PERDIDAS.find(([tb]) => Math.abs(tb - b) < 0.005);
    if (enTabla) fila("", "tabla 60 / 50 Hz", `${enTabla[2].toFixed(2)} / ${enTabla[1].toFixed(2)}`);
    if (b < B_TABLA_MIN || b > B_TABLA_MAX) fila("", "fuera de la tabla", "extrapolado");
    tip.hidden = false;
    const c = caja.getBoundingClientRect(), r = svg.getBoundingClientRect();
    const xPx = r.left - c.left + x / W * r.width, ancho = tip.offsetWidth;
    tip.style.left = `${Math.max(4, Math.min(xPx + (xPx > c.width / 2 ? -ancho - 12 : 12), c.width - ancho - 4))}px`;
    tip.style.top = `${Math.max(r.top - c.top + (mt + 8) / H * r.height, 30)}px`;
  };
  const ocultar = () => { cruz.setAttribute("visibility", "hidden"); tip.hidden = true; };
  svg.addEventListener("pointermove", (ev) => {
    const r = svg.getBoundingClientRect(), x = (ev.clientX - r.left) / r.width * W;
    if (x < ml - 4 || x > W - mr + 4) { ocultar(); return; }
    mostrar(b0 + (x - ml) / (W - ml - mr) * (b1 - b0));
  });
  svg.addEventListener("pointerleave", ocultar);
  svg.addEventListener("blur", ocultar);
  svg.addEventListener("keydown", (ev) => {
    if (ev.key !== "ArrowLeft" && ev.key !== "ArrowRight") return;
    ev.preventDefault();
    mostrar((bAct ?? Number(svg.dataset.bdis || 1.5)) + (ev.key === "ArrowRight" ? 0.01 : -0.01));
  });
  svg.addEventListener("focus", () => mostrar(Number(R.vacio.b)));
}

function vistaVacio(vac, nuc) {
  if (!vac) return bloque("Pérdidas en el núcleo (vacío)", `<p class="vacio">Aparecen cuando el cálculo eléctrico está completo: necesitan la inducción real.</p>`);
  const b = vac.b, f = vac.f;
  const pasos = [
    ["Inducción real", "V/espira / (4.44 · f · sección neta)", `${vac.b_real.toFixed(4)} T`],
    ["Inducción para pérdidas B", `B real + ${F.g(AUMENTO_B_PERDIDAS)} = ${vac.b_real.toFixed(4)} + ${F.g(AUMENTO_B_PERDIDAS)}`, `${b.toFixed(4)} T`],
    ["Frecuencia", "dato", `${F.g(f)} Hz`],
    ["Curva de 50 Hz", `c0 + c1·B + c2·B² con B = ${b.toFixed(4)}`, `${vac.p50.toFixed(4)} W/kg`],
    ["Curva de 60 Hz", `c0 + c1·B + c2·B² con B = ${b.toFixed(4)}`, `${vac.p60.toFixed(4)} W/kg`],
  ];
  let origen = `curva de ${F.g(f)} Hz`;
  if (f !== 50 && f !== 60) {
    pasos.push(["a (histéresis)", `(3600·P50 − 2500·P60) / 30000 = (3600 x ${vac.p50.toFixed(4)} − 2500 x ${vac.p60.toFixed(4)}) / 30000`, vac.a.toFixed(7)],
      ["b (parásitas)", `(50·P60 − 60·P50) / 30000 = (50 x ${vac.p60.toFixed(4)} − 60 x ${vac.p50.toFixed(4)}) / 30000`, vac.bb.toFixed(7)]);
    origen = `a·f + b·f² = ${vac.a.toFixed(7)} x ${F.g(f)} + ${vac.bb.toFixed(7)} x ${F.g(f)}²`;
  }
  pasos.push(["Pfe", vac.manual ? `dato a mano (la regresión da ${vac.pfe_regresion.toFixed(4)} con ${origen})` : origen, `${vac.pfe.toFixed(4)} W/kg`, true],
    ["Peso del núcleo", "hoja de corte de núcleo", `${vac.peso.toFixed(1)} kg`],
    ["Factor de construcción", "dato", F.g(vac.factor)],
    ["P0", `Pfe x peso x factor = ${vac.pfe.toFixed(4)} x ${vac.peso.toFixed(1)} x ${F.g(vac.factor)}`, `${F.miles(vac.p0)} W`, true]);
  const avisos = [];
  if (vac.fuera_tabla) avisos.push(`La inducción ${b.toFixed(3)} T está fuera de la tabla (${F.g(B_TABLA_MIN)} a ${F.g(B_TABLA_MAX)} T): Pfe es una extrapolación de la regresión.`);
  if (vac.fuera_frec) avisos.push(`La frecuencia ${F.g(f)} Hz está fuera de 50–60 Hz: Pfe = a·f + b·f² se extrapola.`);
  return [
    `<div class="cifras grandes">${cifra(`Pfe con B real + ${F.g(AUMENTO_B_PERDIDAS)}`, `${vac.pfe.toFixed(4)} W/kg`)}${cifra("Peso del núcleo", `${vac.peso.toFixed(0)} kg`)}${cifra("Pérdidas en vacío P0", `${F.miles(vac.p0)} W`, true)}</div>`,
    avisos.length ? `<ul class="avisos">${avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul>` : "",
    bloque(`Pérdidas en el núcleo (vacío) · ${MATERIAL_NUCLEO}`, graficoPerdidas(vac)),
    bloque("Desarrollo del cálculo", tablaPasos(pasos) + `<p class="nota-tabla">Regresión cuadrática por mínimos cuadrados sobre la tabla del fabricante (${TABLA_PERDIDAS.length} puntos): el polinomio de grado 2. Las pérdidas se leen con B real + ${F.g(AUMENTO_B_PERDIDAS)} T.<br>
      50 Hz: <span class="m">${ecuacionPerdidas(50)}</span><br>60 Hz: <span class="m">${ecuacionPerdidas(60)}</span></p>`),
  ].join("");
}

function tablaFabricante() {
  const filas = TABLA_PERDIDAS.map(([b, p50, p60]) => {
    const r50 = pfeCurva(50, b), r60 = pfeCurva(60, b);
    return [b.toFixed(1), p50.toFixed(2), r50.toFixed(4), F.signo(r50 - p50, 4), p60.toFixed(2), r60.toFixed(4), F.signo(r60 - p60, 4)];
  });
  return bloque("Tabla del fabricante contra la regresión (W/kg)", tablaHtml(["B (T)", "50 Hz tabla", "50 Hz regresión", "Error", "60 Hz tabla", "60 Hz regresión", "Error"], filas));
}

function vistaNucleo(r) {
  const nuc = r.nuc;
  const datos = lista([
    ["Dist. entre ejes de columna (De)", `${F.g(nuc.de)} mm`], ["Altura de ventana (Hc)", `${F.g(nuc.hc)} mm`],
    ["Diámetro de núcleo (Dn)", `${F.g(nuc.dn)} mm`], ["Traslape (g)", `${F.g(nuc.g)} mm`],
    ["Número de escalones (Ne)", `${nuc.escalones.length}`], ["Espesor de plancha", `${T_CHAPA} mm`],
    ["Sección neta", `${(nuc.seccion_neta / 100).toFixed(1)} cm²`, true],
  ]);
  const seccion = tablaHtml(["Esc.", "Ancho real", "Ancho óptimo", "Espesor"],
    nuc.escalones.map((e) => [e.n, `<b>${F.g(e.ancho)}</b>`, `<span class="opt">${e.ancho_optimo.toFixed(1)}</span>`, e.espesor.toFixed(2)]),
    ["Espesor total", "", "", `${nuc.espesor_total.toFixed(2)} mm`]);
  const corte = nuc.escalones.map((e) => `<tr><td>${e.n}</td><td>${e.espesor.toFixed(2)}</td><td>${e.chapas * 2}</td><td>${e.A.toFixed(0)}</td>
    <td>${e.ancho.toFixed(0)}</td><td>${e.chapas * 2}</td><td>${e.C.toFixed(0)}</td><td>${e.ancho.toFixed(0)}</td><td>${e.chapas}</td>
    <td>${e.E.toFixed(0)}</td><td>${e.ancho.toFixed(0)}</td><td><b>${e.peso.toFixed(1)}</b></td></tr>`).join("");
  const tablaCorte = `<div class="tabla"><table class="corte"><thead>
    <tr><th rowspan="2">Esc.</th><th rowspan="2">Espesor</th><th colspan="3">Columna lateral</th><th colspan="3">Yugo</th><th colspan="3">Columna central</th><th rowspan="2">Peso (kg)</th></tr>
    <tr><th>Cant.</th><th>A</th><th>B</th><th>Cant.</th><th>C</th><th>D</th><th>Cant.</th><th>E</th><th>F</th></tr></thead>
    <tbody>${corte}<tr class="total"><td colspan="11">Peso total</td><td>${nuc.peso.toFixed(0)} kg</td></tr></tbody></table></div>`;
  return [
    `<p class="encabezado">Núcleo · <b>step lap core</b> · plancha <b>M4 0.27 mm</b>: pérdidas en vacío, sección y corte de planchas.</p>`,
    vistaVacio(r.vacio, nuc),
    `<div class="dos">${bloque("Datos", datos)}${bloque("Sección", seccion)}</div>`,
    bloque("Corte de planchas (mm)", tablaCorte),
    tablaFabricante(),
  ].join("");
}

// canales internos como N° x medida (o 0 si no hay)
function textoCanales(c) {
  if (!c.length) return "0";
  return c.every((x) => x === c[0]) ? `${c.length} x ${F.g(c[0])}` : c.map(F.g).join(" + ");
}

function vistaDevanado(r, k) {
  const res = r.lista.find((i) => i.clave === k).res, e = r.elec.dev[k], m = r.mont.filas.find((f) => f.clave === k);
  const platina = res.conductor === "PLATINA", galleta = res.n_sec > 1, H = res.horizontales, Rr = res.radiales, v = res.ventana;
  const canales = textoCanales(res.canales), n = F.n, epc = n(res.esp_por_capa);
  const datos = [
    ["Devanado · posición radial", `<b>${e.nombre}</b> · ${m.pos}`],
    ["Tensión de fase · grupo", `${F.miles(e.v_fase, 1)} V · ${e.conex}`],
    ...e.tensiones.slice(1).map((tn) => ["2ª tensión: línea · grupo · espiras", `${F.miles(tn.volt)} V · ${tn.conex} · ${tn.n} espiras`]),
    ["Tipo de devanado", `<b>${res.tipo}</b>`],
    ["Disposición (cant. = horiz. x rad.)", `${res.cantidad} = ${H} x ${Rr}`],
    ["Espiras totales (N)", e.n_max !== e.n_nom ? `${res.n_espiras} (las máximas; nominal ${e.n_nom})` : `${res.n_espiras}`],
    ...(galleta ? [["Espiras por galleta", (() => { const b = espirasPorBobina(res.tipo, res.n_espiras), bn = espirasPorBobina(res.tipo, e.n_nom);
      return `${textoBobinas(b)} = ${res.n_espiras}${e.n_max !== e.n_nom ? ` (nominal ${textoBobinas(bn)} = ${e.n_nom})` : ""} · se dimensiona con ${res.n_por_sec}`; })()]] : []),
    ...(v ? [["Altura disponible en la ventana", `${n(v.axial_disp)} mm (Hc ${n(v.hc)} − 2 x ${n(v.yugo)})`]] : []),
    [`Espiras por capa${res.modo_capas ? " (calculadas)" : ""}`, epc],
    [`Capas${v ? " (ajustadas a la ventana)" : res.modo_capas ? " (ingresadas)" : ""}`, `${res.capas} (última: ${n(res.espiras_ultima)} esp.)`],
    ["Papel entre capas (aisl. menor)", `${F.g(res.papel_capa)} mm`], ["Canales internos: N° x medida (aisl. menor)", res.canales.length ? `${canales} mm` : "sin canales"],
    ["Transposiciones", `${res.transposiciones}`], ["Canal interior (aisl. mayor)", `${n(m.canal)} mm`],
    ["Al yugo: resultante / mínimo (aisl. mayor)", `${n(m.al_yugo)} / ${n(m.yugo)} mm`, true],
  ];
  const cond = platina
    ? [["Platina calata (esp. x ancho)", `${F.g(res.esp_cal)} x ${F.g(res.anc_cal)} mm`], ["Papel que la envuelve (aisl. menor)", `${F.g(res.papel)} mm`]]
    : [["Alambre esmaltado", `Cal. ${res.medida}`], ["Ø esmaltado (sin papel)", `${F.g(res.ancho_cond)} mm`]];
  cond.push(["1 conductor: radial x axial", `${res.esp_cond.toFixed(2)} x ${res.ancho_cond.toFixed(2)} mm`],
    ["Sección por conductor", `${res.seccion.toFixed(3)} mm²`], [`Sección por espira (x${res.cantidad}${platina ? ` x ${F.g(FACTOR_SECCION_PLATINA)}` : ""})`, `${res.seccion_total.toFixed(2)} mm²`, true],
    ["Corriente de fase nominal", `${e.i_fase.toFixed(1)} A`], ["Densidad de corriente", `${m.j_nom.toFixed(2)} A/mm²`, true]);
  if (Math.abs(e.i_max - e.i_fase) > 1e-9)
    cond.push(["Corriente máxima (entre tensiones y tomas)", `${e.i_max.toFixed(1)} A`], ["Densidad máxima", `${m.j_max.toFixed(2)} A/mm²`]);
  cond.push(["Espira media", `${m.l_espira.toFixed(0)} mm`], [`Peso de cobre (${FASES} fases)`, `${m.peso.toFixed(1)} kg`]);

  const fAnc = platina ? `papel + ancho calato = ${F.g(res.papel)} + ${F.g(res.anc_cal)}` : "Ø esmaltado (el alambre no lleva papel)";
  const fEsp = platina ? `papel + espesor calato = ${F.g(res.papel)} + ${F.g(res.esp_cal)}` : "Ø esmaltado (el alambre no lleva papel)";
  const nCap = galleta ? "espiras por galleta" : "N";
  const pasos = galleta ? [["Espiras por galleta", `REDONDEO.MAS(N / 2) = REDONDEO.MAS(${res.n_espiras} / 2)`, `${res.n_por_sec}`]] : [];
  let pasosCapas;
  if (v) {
    pasosCapas = [["Altura disponible", `Hc − 2 x al yugo mín. = ${n(v.hc)} − 2 x ${n(v.yugo)}`, `${n(v.axial_disp)} mm`]];
    let disp = "disponible";
    if (galleta) {
      pasosCapas.push(["Altura por galleta", `(disponible − separación) / 2 = (${n(v.axial_disp)} − ${F.g(SEPARACION_GALLETA)}) / 2`, `${n(v.por_seccion)} mm`]);
      disp = "por galleta";
    }
    pasosCapas.push(
      ["Espiras por capa que entran", `ENTERO(${disp} − transp. x ancho cond.) / ancho por espira − 1 = ENTERO(${n(v.por_seccion)} − ${res.transposiciones} x ${res.ancho_cond.toFixed(2)}) / ${res.ancho_espira.toFixed(2)} − 1 = ${v.util} / ${res.ancho_espira.toFixed(2)} − 1`, v.epc_lim.toFixed(2)],
      v.capas_fijas ? ["Capas", `${res.tipo}: ${v.capas_fijas === 1 ? "una sola capa" : `siempre ${v.capas_fijas} capas`}${v.entra_fijas ? "" : ` · <span class="no">no caben: entran ${v.epc_lim.toFixed(2)} espiras por capa y se necesitan ${n(res.n_por_sec / v.capas_fijas)}</span>`}`, `${res.capas}`]
        : ["Capas", `REDONDEO.MAS(${nCap} / esp. por capa que entran) = REDONDEO.MAS(${res.n_por_sec} / ${v.epc_lim.toFixed(2)} = ${(res.n_por_sec / v.epc_lim).toFixed(2)})`, `${res.capas}`],
      ["Espiras por capa", `${nCap} / capas = ${res.n_por_sec} / ${res.capas}`, epc]);
  } else if (res.modo_capas) {
    pasosCapas = [["Capas", "dato ingresado", `${res.capas}`], ["Espiras por capa", `${nCap} / capas = ${res.n_por_sec} / ${res.capas}`, epc]];
  } else {
    pasosCapas = [["Capas", `REDONDEO.MAS(${nCap} / esp. por capa) = REDONDEO.MAS(${res.n_por_sec} / ${epc} = ${res.capas_calc.toFixed(2)})`, `${res.capas}`]];
  }
  pasos.push(
    ["Ancho de 1 conductor (axial)", fAnc, `${res.ancho_cond.toFixed(2)} mm`],
    ["Espesor de 1 conductor (radial)", fEsp, `${res.esp_cond.toFixed(2)} mm`],
    ["Radiales (verticales)", `cantidad / horizontales = ${res.cantidad} / ${H}`, `${Rr}`],
    ["Ancho por espira", `(papel + ancho calato) x horizontales = ${res.ancho_cond.toFixed(2)} x ${H}`, `${res.ancho_espira.toFixed(2)} mm`],
    ["Espesor por espira", `(papel + espesor calato) x radiales = ${res.esp_cond.toFixed(2)} x ${Rr}`, `${res.espesor_espira.toFixed(2)} mm`],
    ...pasosCapas,
    ["Suma de canales", res.canales.length ? `N° de canales x medida = ${canales}` : "sin canales internos", `${res.suma_canales.toFixed(2)} mm`],
    ["RADIAL", `REDONDEO.MAS(${res.capas} x (${F.g(res.papel_capa)} + ${res.espesor_espira.toFixed(2)}) + ${res.suma_canales.toFixed(2)}) = REDONDEO.MAS(${res.radial_bruto.toFixed(2)})`, `${n(res.radial)} mm`, true],
    [`AXIAL${galleta ? " (1 galleta)" : ""}`, `REDONDEO.MAS((${epc} + 1) x ${res.ancho_espira.toFixed(2)} = ${res.axial_bruto.toFixed(2)}) + ${res.transposiciones} x ${res.ancho_cond.toFixed(2)}`, `${n(res.axial_seccion)} mm`, true]);
  if (galleta) pasos.push(["AXIAL TOTAL", `2 galletas x ${n(res.axial_seccion)} + separación ${F.g(SEPARACION_GALLETA)}`, `${n(res.axial_total)} mm`, true]);
  pasos.push(["Ø interior", `Ø anterior + 2 x canal = ${n(m.d_int - 2 * m.canal)} + 2 x ${n(m.canal)}`, `${n(m.d_int)} mm`],
    ["Ø exterior", `Ø interior + 2 x radial = ${n(m.d_int)} + 2 x ${n(res.radial)}`, `${n(m.d_ext)} mm`]);

  const espira = `<div class="dibujo">${svgEspira(res)}<p class="pie-dibujo">↕ axial: ${H} horizontales · ↔ radial: ${Rr} radiales<br>
    Ancho <b>${res.ancho_espira.toFixed(2)}</b> mm · Espesor <b>${res.espesor_espira.toFixed(2)}</b> mm${galleta ?
    `<br>2 galletas iguales, separadas ${F.g(SEPARACION_GALLETA)} mm axialmente` : ""}</p></div>`;
  return [
    `<p class="encabezado">${res.tipo} · <b>${res.nombre}</b> · ${res.cantidad} en paralelo (${H} x ${Rr})</p>`,
    `<div class="cifras grandes">${cifra("Dimensión radial", `${n(res.radial)} mm`, true)}${cifra(`Dimensión axial${galleta ? " total" : ""}`,
      `${n(res.axial_total)} mm`, true)}${cifra("Ø interior / Ø exterior", `${n(m.d_int)} / ${n(m.d_ext)} mm`)}${
      `<div class="cifra${m.margen_yugo >= 0 ? "" : " mal"}"><span>Al yugo (mín. ${n(m.yugo)})</span><b>${n(m.al_yugo)} mm</b></div>`}</div>`,
    `<div class="tres">${bloque("Datos", lista(datos))}${bloque("Conductor", lista(cond))}${bloque("Espira", espira)}</div>`,
    bloque("Desarrollo del cálculo", tablaPasos(pasos)),
  ].join("");
}

function vistaVcc(r) {
  const { nuc, elec, mont } = r, at = elec.dev[PRINCIPAL];
  const por = Object.fromEntries(mont.filas.map((f) => [f.clave, f]));
  const partes = r.pares.map((p) => {
    const aF = por[PRINCIPAL], sF = por[p.clave], sec = elec.dev[p.clave];
    const [dentro, fuera] = aF.pos < sF.pos ? [aF, sF] : [sF, aF];
    const iAt = corrienteFase(p.s_base, at.volt, at.conex);
    const fI = esEstrella(sec.conex) ? `S·1000 / (√3·V) = ${F.g(p.s_base)}·1000 / (√3·${F.g(sec.volt)})`
      : `S·1000 / (3·V) = ${F.g(p.s_base)}·1000 / (3·${F.g(sec.volt)})`;
    const pasos = [
      ["Potencia (kVA)", `menor potencia del par = mín(${F.g(at.kva)}, ${F.g(sec.kva)})`, F.miles(p.s_base)],
      ["Tensión · grupo", `${sec.nombre}, 1ª tensión`, `${F.miles(sec.volt)} V · ${sec.conex}`],
      ["I_fase", fI, `${p.i.toFixed(2)} A`],
      ["N", `espiras del ${sec.nombre} (nominales)`, `${p.n}`],
      ["Dm", `((Dint + e) ${aF.nombre} + (Dint + e) ${sF.nombre}) / 2 = ((${F.n(aF.d_int)} + ${F.n(aF.radial)}) + (${F.n(sF.d_int)} + ${F.n(sF.radial)})) / 2`, `${p.d_m.toFixed(1)} mm`],
      ["Lambda", `(Ø int. ${fuera.nombre} − Ø ext. ${dentro.nombre}) / 2 = (${F.n(fuera.d_int)} − ${F.n(dentro.d_ext)}) / 2`, `${F.n(p.lam)} mm`],
      ["eAT / eBT", `radial ${aF.nombre} / radial ${sF.nombre}`, `${F.n(p.e_pri)} / ${F.n(p.e_sec)} mm`],
      ["Heq", `(H ${aF.nombre} + H ${sF.nombre}) / 2 = (${F.n(aF.axial)} + ${F.n(sF.axial)}) / 2`, `${F.n(p.h_eq)} mm`],
      ["B", `inducción real x 10 = ${elec.b_real.toFixed(4)} x 10`, `${p.b_kg.toFixed(2)} kG`],
      ["Sfe", `sección neta / 100 = ${nuc.seccion_neta.toFixed(1)} / 100`, `${p.s_fe.toFixed(1)} cm²`],
      ["kR", `cuadro de Rogowski con I_fase = ${p.i.toFixed(1)} A`, F.g(p.k_r)],
      ["Perd_Cu", `${FASES}·(I²·R ${sF.nombre} + I²·R ${aF.nombre}) = ${FASES}·(${p.i.toFixed(2)}²·${F.g5(sF.r_fase)} + ${iAt.toFixed(2)}²·${F.g5(aF.r_fase)})`, `${F.miles(p.perdidas, 1)} W`],
      ["Vcc_reactiva", `(N·I_fase)·(π·Dm)·(Lambda + (eAT + eBT)/3)·kR·K / (Heq·B·Sfe) = (${p.n}·${p.i.toFixed(2)})·(π·${p.d_m.toFixed(1)})·(${F.n(p.lam)} + (${F.n(p.e_pri)} + ${F.n(p.e_sec)})/3)·${F.g(p.k_r)}·${F.g(K_VCC)} / (${F.n(p.h_eq)}·${p.b_kg.toFixed(3)}·${p.s_fe.toFixed(2)})`, `${p.ux.toFixed(4)} %`, true],
      ["Vcc_Activa", `Perd_Cu / (Potencia·10) = ${F.miles(p.perdidas, 1)} / (${F.g(p.s_base)}·10)`, `${p.ur.toFixed(4)} %`, true],
      ["Vcc", "√(Vcc_reactiva² + Vcc_Activa²)", `${p.uz.toFixed(4)} %`, true],
    ];
    return bloque(p.par, `<div class="cifras">${cifra("Vcc_reactiva", `${p.ux.toFixed(2)} %`)}${cifra("Vcc_Activa", `${p.ur.toFixed(2)} %`)}${
      cifra("Vcc", `${p.uz.toFixed(2)} %`, true)}</div>${tablaPasos(pasos)}`, ' class="par"');
  });
  return [
    `<p class="encabezado">Tensión de cortocircuito por par de devanados · K = <b>${F.g(K_VCC)}</b> con B en kilogauss, Sfe en cm² y medidas en mm. N e I_fase son los del secundario con su primera tensión; kR sale del cuadro de Rogowski con esa corriente.</p>`,
    ...partes,
  ].join("");
}

function vistaErrores(r) {
  if (r.faltan) return bloque("Faltan estos datos (no tienen fuente, se digitan)", `<p class="vacio" style="margin-bottom:8px">Toca uno para ir a su celda.</p>${htmlFaltan(DET)}`)
    + (r.nuc ? `<p class="vacio">Mientras tanto, la hoja de corte de núcleo ya está lista en su pestaña.</p>` : "");
  const items = r.errores.map((e) => `<li>${esc(e)}</li>`).join("");
  return bloque("Revisa estos datos antes de calcular", `<ul class="errores">${items}</ul>`)
    + (r.nuc ? `<p class="vacio">Mientras tanto, la hoja de corte de núcleo ya está lista en su pestaña.</p>` : "");
}

// ---------- pestañas ----------
function pestanasDisponibles(r) {
  if (r.errores.length) return [["errores", "Revisar datos"], ...(r.nuc ? [["nucleo", "Núcleo"]] : []), ...(BUSQ ? [["busqueda", "Búsqueda"]] : [])];
  const devs = CLAVES.filter((k) => r.lista.some((i) => i.clave === k)).map((k) => [`dev-${k}`, NOMBRES[k]]);
  return [["resumen", "Resumen"], ["electrico", "1 · Cálculo eléctrico"], ["nucleo", "2 · Núcleo"], ...devs.map(([id, t]) => [id, `3 · ${t}`]),
    ["distancias", "4 · Distancias"], ["vcc", "Vcc"], ...(BUSQ ? [["busqueda", "Búsqueda"]] : [])];
}
function pintarResultado() {
  const r = R, disp = pestanasDisponibles(r);
  const activa = disp.some(([id]) => id === pestana) ? pestana : disp[0][0];
  $("pestanas").innerHTML = disp.map(([id, txt]) =>
    `<button type="button" role="tab" data-p="${id}" aria-selected="${id === activa}">${txt}</button>`).join("");
  let html;
  if (activa === "errores") html = vistaErrores(r);
  else if (activa === "nucleo") html = vistaNucleo(r);
  else if (activa === "resumen") html = vistaResumen(r);
  else if (activa === "electrico") html = vistaElectrico(r);
  else if (activa === "vcc") html = vistaVcc(r);
  else if (activa === "distancias") html = vistaDistancias(r);
  else if (activa === "busqueda") html = vistaBusqueda();
  else html = vistaDevanado(r, activa.slice(4));
  $("resultado").innerHTML = html;
  if (activa === "nucleo") conectarGrafico();
  if (activa === "busqueda") conectarGraficoBusqueda();
}
$("pestanas").addEventListener("click", (ev) => {
  const b = ev.target.closest("button[data-p]");
  if (!b) return;
  pestana = b.dataset.p;
  ponerLocal(CLAVE_PESTANA, pestana);
  pintarResultado();
  $(`panel-${ULTIMO_PASO}`).scrollTop = 0;          // con dos columnas los resultados tienen su propio desplazamiento
});
// alto de la barra fija de arriba: los resultados quedan fijos justo debajo
function medirBarra() {
  const b = document.querySelector(".barra");
  if (b) document.documentElement.style.setProperty("--alto-barra", `${Math.ceil(b.getBoundingClientRect().height)}px`);
}
window.addEventListener("resize", medirBarra);
medirBarra();

// ---------- acciones ----------
let temporizadorAviso = null;
function avisar(texto) {
  let el = $("aviso-copia");
  if (!el) { el = document.createElement("div"); el.id = "aviso-copia"; el.className = "aviso-copia"; el.setAttribute("role", "status"); document.body.appendChild(el); }
  el.textContent = texto; el.hidden = false;
  clearTimeout(temporizadorAviso);
  temporizadorAviso = setTimeout(() => { el.hidden = true; }, 2600);
}
function abrirCargar(texto = "") {
  $("panel-cargar").hidden = false;
  $("texto-cargar").value = texto;
  $("nota-cargar").className = "nota";
  $("nota-cargar").textContent = "Pega los datos copiados con «Copiar datos» en otro equipo o navegador.";
  $("texto-cargar").focus();
}
$("b-cargar").addEventListener("click", () => ($("panel-cargar").hidden ? abrirCargar() : ($("panel-cargar").hidden = true)));
$("b-cargar-no").addEventListener("click", () => { $("panel-cargar").hidden = true; });
$("b-cargar-ok").addEventListener("click", () => {
  let nuevo = null;
  try { nuevo = normalizar(JSON.parse($("texto-cargar").value)); } catch (e) { nuevo = null; }
  if (!nuevo) {
    $("nota-cargar").className = "nota error";
    $("nota-cargar").textContent = "Ese texto no son datos de este programa. Cópialos con «Copiar datos» y pégalos completos.";
    return;
  }
  D = nuevo; ediciones++; guardar(); recalcular(); sincronizar(true);
  $("panel-cargar").hidden = true;
  avisar("Datos cargados.");
});
$("b-copiar").addEventListener("click", () => {
  const texto = JSON.stringify(D);
  const respaldo = () => {
    abrirCargar(texto);
    $("texto-cargar").select();
    $("nota-cargar").textContent = "No se pudo copiar automáticamente: el texto ya está seleccionado, cópialo con Ctrl+C.";
  };
  try { navigator.clipboard.writeText(texto).then(() => avisar("Datos copiados. Pégalos en «Cargar datos» donde los necesites."), respaldo); }
  catch (e) { respaldo(); }
});
let confirmacion = null;
$("b-ejemplo").addEventListener("click", (ev) => {
  const b = ev.currentTarget;
  const igual = JSON.stringify(D) === JSON.stringify(normalizar(copia(DATOS_EJEMPLO)));
  if (!confirmacion && !igual) {
    b.textContent = "¿Reemplazar tus datos? Sí";
    b.classList.add("peligro");
    confirmacion = setTimeout(() => { b.textContent = "Datos de origen"; b.classList.remove("peligro"); confirmacion = null; }, 4000);
    return;
  }
  clearTimeout(confirmacion); confirmacion = null;
  b.textContent = "Datos de origen"; b.classList.remove("peligro");
  D = copia(DATOS_EJEMPLO); ediciones++; guardar(); recalcular(); sincronizar(true);
  avisar("Se cargaron los datos de origen: los que no tienen fuente quedan vacíos para digitarlos.");
});

// ---------- arranque ----------
document.addEventListener("input", (ev) => { const el = ev.target; if (el.classList && el.classList.contains("campo") && el.dataset.c) aplicar(el); });
document.addEventListener("change", (ev) => { const el = ev.target; if (el.classList && el.classList.contains("campo") && el.dataset.c) { aplicar(el); sincronizar(true); } });
document.addEventListener("focusout", (ev) => { if (ev.target.classList && ev.target.classList.contains("campo")) setTimeout(() => sincronizar(true), 0); });
ponerTema();
$("av-devanados").open = avDev;
construirCliente();
construirTabla();
construirGrupos();
construirDistancias();
construirBusqueda();
$("fecha").textContent = new Date().toLocaleDateString("es-PE", { day: "2-digit", month: "short", year: "2-digit" });
recalcular();
sincronizar(true);
