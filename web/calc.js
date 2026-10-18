// ===== Cálculo: misma lógica que DISEÑO_DE_TRANSFORMADOR.py =====
// Orden del diseño: 1. NÚCLEO (fija el espacio: Hc limita la altura y De el diámetro)
//                   2. DEVANADOS dentro de la ventana ("Ajustar a la ventana": capas desde Hc − 2 x mínimo al yugo)
//                   3. DISTANCIAS ELÉCTRICAS (aislamiento mayor) que quedan, contra sus mínimos
// 1. Conductores de stock y reglas de fabricación
// Alambre esmaltado: calibre -> [sección de cobre mm², diámetro esmaltado mm]. El alambre no lleva papel.
const ALAMBRES = {
  8: [8.36, 3.44], 9: [6.63, 3.08], 10: [5.26, 2.72], 11: [4.17, 2.45], 12: [3.30, 2.18],
  13: [2.62, 1.98], 14: [2.08, 1.75], 15: [1.65, 1.565], 16: [1.309, 1.41], 17: [1.038, 1.25],
  18: [0.823, 1.12], 19: [0.652, 1.025], 20: [0.517, 0.905], 21: [0.410, 0.80], 22: [0.325, 0.72],
  23: [0.258, 0.655], 24: [0.204, 0.58], 25: [0.162, 0.52], 26: [0.128, 0.45], 27: [0.102, 0.41],
};
// Platina calata: [espesor (radial), ancho (axial)] en mm. Es la única que se envuelve con papel.
const PLATINAS = [[1.8, 10.0], [1.8, 12.0], [2.5, 12.0], [3.5, 12.0], [3.5, 14.0], [3.5, 15.5]];
// Sección de cobre de la platina: espesor x ancho (como la hoja de devanado): 3.5 x 14 -> 49 mm²
const seccionPlatina = (e, a) => e * a;
// Sección TOTAL de la espira: con platina se multiplica por 0.97 (como la hoja de datos de entrada:
// 12 platinas 3.5 x 14 -> 49 x 12 x 0.97 = 570.36 mm²); con alambre, sección x cantidad.
const FACTOR_SECCION_PLATINA = 0.97;
const seccionEspira = (conductor, seccion, cantidad) => seccion * cantidad * (conductor === "PLATINA" ? FACTOR_SECCION_PLATINA : 1);

const TIPOS = {
  "CONTINUO":      { max_cond: 3,  max_h: 3, h_fijo: null, radiales: [1],    secciones: 1 },
  "GALLETA":       { max_cond: 3,  max_h: 3, h_fijo: null, radiales: [1],    secciones: 2 },
  "FRANCÉS":       { max_cond: 18, max_h: 6, h_fijo: null, radiales: [2, 3], secciones: 1, capas_fijas: 2 },   // siempre 2 capas
  "HÉLICE SIMPLE": { max_cond: 24, max_h: 2, h_fijo: 2,    radiales: null,   secciones: 1, capas_fijas: 1 },   // una sola capa
  "HÉLICE DOBLE":  { max_cond: 48, max_h: 4, h_fijo: 4,    radiales: null,   secciones: 1, capas_fijas: 1 },   // una sola capa
};
const SEPARACION_GALLETA = 20.0;
const CLAVES = ["I", "II", "III"];
const NOMBRES = { I: "Devanado I", II: "Devanado II", III: "Devanado III" };
const COLORES = { I: "#c87533", II: "#8cc08c", III: "#7fa8d1" };
const PRINCIPAL = "I";
const GRUPOS = ["D", "Y", "YN"];

const K_FEM = 4.44, T_CHAPA = 0.27, RHO_FE = 7650.0, RHO_CU_20 = 0.017241, DENS_CU = 8.9;
const FACTOR_ELIPSE = 1;     // núcleo circular: factor elipse K = 1 (hoja de núcleo); ya no se digita
const K_VCC = 0.018;
const TABLA_ROGOWSKI = [[1, 0.96], [501, 0.98], [631, 1.02], [1001, 1.05], [1501, 1.10], [2501, 1.15]];
const FASES = 3, ERROR_RELACION_MAX = 0.5;
// Error de relación: hasta 0.3 % cumple; de 0.3 a 0.5 % se marca en rojo pero procede; más de 0.5 % no procede
const ERROR_RELACION_AVISO = 0.3;

// round() de Python: a la mitad, al par
function pyRound(x, dec = 0) {
  const f = 10 ** dec, y = x * f, r = Math.round(y);
  if (Math.abs(y - Math.trunc(y)) === 0.5) return (2 * Math.round(y / 2)) / f;
  return r / f;
}
// REDONDEO.MAS de Excel (valores positivos)
const redondeoMas = (x, dec = 0) => { const f = 10 ** dec; return Math.ceil(pyRound(x * f, 6)) / f; };
const redondear = (x) => Math.max(Math.floor(x + 0.5), 1);
// n() de las hojas: sin decimales si es entero, si no con 2
const nTexto = (x) => (Math.abs(x - pyRound(x)) < 1e-9 ? x.toFixed(0) : x.toFixed(2));

// 2. Núcleo
const COEFICIENTES_ANCHO = {
  1: [0.707], 2: [0.85, 0.526], 3: [0.906, 0.707, 0.424], 4: [0.934, 0.796, 0.605, 0.356],
  5: [0.95, 0.846, 0.707, 0.534, 0.313], 6: [0.959, 0.875, 0.768, 0.64, 0.483, 0.281],
  7: [0.967, 0.898, 0.812, 0.707, 0.584, 0.436, 0.255],
  8: [0.972, 0.91, 0.842, 0.755, 0.657, 0.541, 0.417, 0.239],
  9: [0.977, 0.929, 0.867, 0.794, 0.707, 0.608, 0.498, 0.37, 0.214],
  10: [0.979, 0.93, 0.884, 0.823, 0.748, 0.662, 0.578, 0.468, 0.346, 0.204],
};

function validarNucleo(dn, g, de, hc, k, anchos) {
  const e = [];
  if (dn <= 0 || de <= 0 || hc <= 0) e.push("Núcleo: Dn, De y Hc deben ser mayores que 0.");
  if (!anchos.length) e.push("Núcleo: ingresa al menos un ancho de escalón.");
  else if (dn > 0 && Math.max(...anchos) >= dn) e.push("Núcleo: los anchos de escalón deben ser menores que el diámetro Dn.");
  return e;
}

function calcularNucleo(dn, g, de, hc, k, anchos, fa = 1.0) {
  const escalones = [];
  let previas = 0, espesorTotal = 0, pesoTotal = 0, seccionBruta = 0;
  const nEsc = anchos.length;
  anchos.forEach((ancho, i) => {
    if (ancho === 0) return;
    const yGeom = dn * k * Math.sqrt(Math.max(1 - (ancho / dn) ** 2, 0));
    const acum = Math.trunc(pyRound((yGeom / T_CHAPA) / 10) * 10);
    let chapas = acum - previas;
    if (chapas < 0) chapas = 0;
    const esp = pyRound(chapas * T_CHAPA, 2);
    previas += chapas;
    espesorTotal += esp;
    const an = anchos[0] + hc + ancho, cn = 2 * de + ancho, eConst = hc + anchos[0];
    const area = cn * an - 2 * g ** 2 - (cn - 3 * ancho) * (an - 2 * ancho);
    const peso = (area * esp / 1e9) * RHO_FE;
    pesoTotal += peso;
    const optimo = nEsc >= 1 && nEsc <= 10 ? dn * COEFICIENTES_ANCHO[nEsc][i] : 0;
    seccionBruta += ancho * esp;
    escalones.push({ n: i + 1, ancho, ancho_optimo: optimo, espesor: esp, chapas, A: an, C: cn, E: eConst, peso });
  });
  return { dn, g, de, hc, k, escalones, peso: pesoTotal, espesor_total: espesorTotal,
           seccion_bruta: seccionBruta, factor_apilamiento: fa, seccion_neta: seccionBruta * fa };
}

// 2.1 Pérdidas en el núcleo (vacío): regresión cuadrática (polinomio de grado 2)
//   Pfe = c0 + c1·B + c2·B² por mínimos cuadrados, una curva para 50 Hz y otra para 60 Hz.
//   La inducción con que se leen las pérdidas es B = B real + 0.099 T.
//   Otra frecuencia: Pfe = a·f + b·f², a = (3600·P50 − 2500·P60) / 30000, b = (50·P60 − 60·P50) / 30000.
//   P0 = Pfe x peso del núcleo x factor de construcción.
const MATERIAL_NUCLEO = "chapa M4 de 0.27 mm";
const AUMENTO_B_PERDIDAS = 0.099;     // T: las pérdidas se leen con B real + 0.099
const TABLA_PERDIDAS = [   // [B (T), Pfe 50 Hz, Pfe 60 Hz] en W/kg
  [0.5, 0.10, 0.14], [0.6, 0.15, 0.18], [0.7, 0.18, 0.24], [0.8, 0.23, 0.31], [0.9, 0.29, 0.38],
  [1.0, 0.36, 0.46], [1.1, 0.43, 0.55], [1.2, 0.51, 0.65], [1.3, 0.60, 0.78], [1.4, 0.72, 0.91],
  [1.5, 0.84, 1.10], [1.6, 1.00, 1.30], [1.7, 1.22, 1.58], [1.8, 1.52, 1.96], [1.9, 1.90, 2.50],
];
// Regresión lineal por mínimos cuadrados (QR de Householder), con las mismas sumas que el programa en Python
function minimosCuadrados(filas, y) {
  const a = filas.map((f) => f.slice()), b = y.slice(), m = a.length, n = a[0].length;
  for (let j = 0; j < n; j++) {
    let norma = 0;
    for (let i = j; i < m; i++) norma += a[i][j] * a[i][j];
    norma = Math.sqrt(norma);
    const alfa = a[j][j] > 0 ? -norma : norma;
    const v = new Array(m).fill(0);
    v[j] = a[j][j] - alfa;
    for (let i = j + 1; i < m; i++) v[i] = a[i][j];
    let vv = 0;
    for (let i = j; i < m; i++) vv += v[i] * v[i];
    if (vv === 0) continue;
    for (let k = j; k < n; k++) {
      let t = 0;
      for (let i = j; i < m; i++) t += v[i] * a[i][k];
      t = 2 * t / vv;
      for (let i = j; i < m; i++) a[i][k] -= t * v[i];
    }
    let t = 0;
    for (let i = j; i < m; i++) t += v[i] * b[i];
    t = 2 * t / vv;
    for (let i = j; i < m; i++) b[i] -= t * v[i];
  }
  const c = new Array(n).fill(0);
  for (let j = n - 1; j >= 0; j--) {
    let t = b[j];
    for (let k = j + 1; k < n; k++) t -= a[j][k] * c[k];
    c[j] = t / a[j][j];
  }
  return c;
}
const ajustePerdidas = (col) => minimosCuadrados(TABLA_PERDIDAS.map(([b]) => [1, b, b * b]),
                                                 TABLA_PERDIDAS.map((fila) => fila[col]));
const COEF_PERDIDAS = { 50: ajustePerdidas(1), 60: ajustePerdidas(2) };
const B_TABLA_MIN = TABLA_PERDIDAS[0][0], B_TABLA_MAX = TABLA_PERDIDAS[TABLA_PERDIDAS.length - 1][0];
function pfeCurva(f, b) {
  const c = COEF_PERDIDAS[f];
  return c[0] + c[1] * b + c[2] * (b * b);
}
function perdidasEspecificas(b, f) {
  const p50 = pfeCurva(50, b), p60 = pfeCurva(60, b);
  const a = (3600 * p50 - 2500 * p60) / 30000, bb = (50 * p60 - 60 * p50) / 30000;
  const pfe = f === 50 ? p50 : f === 60 ? p60 : a * f + bb * (f * f);
  return { b, f, p50, p60, a, bb, pfe };
}
function calcularVacio(nuc, elec, wkgManual = 0, factor = 1) {
  const r = perdidasEspecificas(elec.b_real + AUMENTO_B_PERDIDAS, elec.frecuencia);
  r.b_real = elec.b_real;
  const manual = wkgManual > 0;
  r.pfe_regresion = r.pfe;
  if (manual) r.pfe = wkgManual;
  Object.assign(r, { manual, peso: nuc.peso, factor, p0: r.pfe * nuc.peso * factor,
    fuera_tabla: !(B_TABLA_MIN - 1e-9 <= r.b && r.b <= B_TABLA_MAX + 1e-9),
    fuera_frec: !(50 - 1e-9 <= r.f && r.f <= 60 + 1e-9) });
  return r;
}

// 3. Cálculo eléctrico
const esEstrella = (c) => c === "Y" || c === "YN";
const tensionFase = (v, c) => (esEstrella(c) ? v / Math.sqrt(3) : v);
function corrienteFase(kva, v, c) {
  const il = kva * 1000 / (Math.sqrt(3) * v);
  return esEstrella(c) ? il : il / Math.sqrt(3);
}

function calcularElectrico(specs, frecuencia, tapNom, variacion, nPasos, repCarga, seccionNeta, bObjetivo, nRefManual = 0) {
  const errores = [], activos = [];
  for (const k of CLAVES) {
    const s = specs[k];
    if (Math.min(s.kva, s.volt, s.kva2 || 0, s.volt2 || 0) < 0) errores.push(`${NOMBRES[k]}: potencias y tensiones no pueden ser negativas.`);
    else if (s.kva > 0 && s.volt > 0) activos.push(k);
    else if (s.kva > 0) errores.push(`${NOMBRES[k]}: tiene potencia pero le falta la primera tensión.`);
  }
  if (!activos.includes(PRINCIPAL)) errores.push(`Falta el ${NOMBRES[PRINCIPAL]} (principal): ingresa su potencia y su tensión.`);
  if (activos.length < 2) errores.push("Se necesitan al menos 2 devanados con potencia y tensión.");
  if (frecuencia <= 0 || bObjetivo <= 0 || seccionNeta <= 0) errores.push("Frecuencia, inducción objetivo y sección del núcleo deben ser mayores que 0.");
  if (nPasos < 1 || !(tapNom >= 1 && tapNom <= nPasos)) errores.push(`Tap: la posición nominal (${tapNom}) debe estar entre 1 y el N° de pasos (${nPasos}).`);
  if (variacion < 0 || (nPasos >= 1 && variacion * Math.max(nPasos - tapNom, 0) >= 100)) errores.push("Tap: el % de variación no es válido.");
  const repartos = (String(repCarga).match(/\d+(?:\.\d+)?/g) || []).map(Number);
  if (!repartos.length) errores.push("Reparto BT: escribe los porcentajes separados por guion, por ejemplo 100-0.");
  if (errores.length) return { errores, elec: null };

  const area = seccionNeta / 1e6, dev = {};
  for (const k of activos) {
    const s = specs[k];
    const entradas = [[s.volt, s.conex, s.kva]];
    if ((s.volt2 || 0) > 0) entradas.push([s.volt2, s.conex2 || s.conex, (s.kva2 || 0) > 0 ? s.kva2 : s.kva]);
    const tensiones = entradas.map(([v, c, p]) => ({ volt: v, conex: c, kva: p, v_fase: tensionFase(v, c),
      i_linea: p * 1000 / (Math.sqrt(3) * v), i_fase: corrienteFase(p, v, c) }));
    const t0 = tensiones[0];
    dev[k] = { clave: k, nombre: NOMBRES[k], kva: s.kva, volt: s.volt, conex: s.conex, bil: s.bil,
               v_fase: t0.v_fase, i_linea: t0.i_linea, i_fase: t0.i_fase, tensiones };
  }
  // Referencia: la menor tensión de fase de toda la tabla
  let ref = null, tRef = null;
  for (const k of activos) for (const t of dev[k].tensiones) if (tRef === null || t.v_fase < tRef.v_fase) { ref = k; tRef = t; }
  const nTeorico = tRef.v_fase / (K_FEM * frecuencia * bObjetivo * area);
  const nRef = nRefManual > 0 ? Math.trunc(nRefManual) : Math.trunc(redondeoMas(nTeorico, 0));
  const vEsp = tRef.v_fase / nRef;
  const bReal = vEsp / (K_FEM * frecuencia * area);
  for (const k of activos) {
    const d = dev[k];
    for (const t of d.tensiones) {
      t.n = t === tRef ? nRef : redondear(t.v_fase / vEsp);
      t.error = (t.n * vEsp - t.v_fase) / t.v_fase * 100;
    }
    d.n_nom = d.tensiones[0].n;
    d.n_max = Math.max(...d.tensiones.map((t) => t.n));
    d.i_max = Math.max(...d.tensiones.map((t) => t.i_fase));
    d.error = d.tensiones[0].error;
  }
  // Regulación en el devanado principal, sobre su primera tensión
  const at = dev[PRINCIPAL], taps = [];
  for (let p = 1; p <= nPasos; p++) {
    const factor = 1 + (tapNom - p) * variacion / 100;
    const vL = at.volt * factor, vF = tensionFase(vL, at.conex);
    const nP = p === tapNom ? at.n_nom : redondear(vF / vEsp);
    const vFReal = nP * vEsp;
    taps.push({ pos: p, pct: (factor - 1) * 100, v_linea: vL, v_fase: vF, espiras: nP,
                v_linea_real: vFReal * (esEstrella(at.conex) ? Math.sqrt(3) : 1),
                error: (vFReal - vF) / vF * 100, i_fase: corrienteFase(at.kva, vL, at.conex) });
  }
  at.n_max = Math.max(at.n_max, ...taps.map((t) => t.espiras));
  at.i_max = Math.max(at.i_max, ...taps.map((t) => t.i_fase));
  // Reparto de carga
  const secundarios = activos.filter((k) => k !== PRINCIPAL);
  let cargaTotal = 0;
  secundarios.forEach((k, idx) => {
    const pct = idx < repartos.length ? repartos[idx] : 0;
    const kvaCarga = pct / 100 * at.kva;
    dev[k].reparto = pct; dev[k].kva_carga = kvaCarga;
    dev[k].i_carga = corrienteFase(kvaCarga, dev[k].volt, dev[k].conex);
    cargaTotal += kvaCarga;
  });
  at.reparto = secundarios.reduce((s, k) => s + dev[k].reparto, 0);
  at.kva_carga = cargaTotal;
  at.i_carga = corrienteFase(cargaTotal, at.volt, at.conex);
  return { errores: [], elec: { activos, secundarios, dev, ref, ref_volt: tRef.volt, n_teorico: nTeorico, n_ref: nRef,
    n_ref_manual: nRefManual > 0, v_esp: vEsp, b_real: bReal, b_objetivo: bObjetivo, frecuencia,
    seccion_neta: seccionNeta, taps, tap_nom: tapNom, variacion, n_pasos: nPasos, rep_carga: String(repCarga) } };
}

function resumenEntrada(specs, cond) {
  const salida = {};
  for (const k of CLAVES) {
    const s = specs[k], c = cond[k];
    let seccion, calibre, aislante;
    if (c.conductor === "PLATINA") {
      const [e, a] = PLATINAS[c.medida];
      seccion = seccionPlatina(e, a); calibre = `${e}x${a}`; aislante = "PAPEL";
    } else { seccion = ALAMBRES[c.medida][0]; calibre = `${c.medida}`; aislante = "ESMALTE"; }
    const seccionTotal = seccionEspira(c.conductor, seccion, c.cantidad);
    const columnas = [[s.volt, s.conex, s.kva], [s.volt2 || 0, s.conex2 || s.conex, (s.kva2 || 0) > 0 ? s.kva2 : s.kva]]
      .map(([volt, conex, kva]) => {
        const usada = s.kva > 0 && kva > 0 && volt > 0;
        const iL = usada ? kva * 1000 / (Math.sqrt(3) * volt) : 0, iF = usada ? corrienteFase(kva, volt, conex) : 0;
        return { volt, conex, kva, usada, i_linea: iL, i_fase: iF, densidad: seccionTotal > 0 ? iF / seccionTotal : 0 };
      });
    salida[k] = { activo: s.kva > 0 && s.volt > 0, bil: s.bil, calibre, aislante, cantidad: c.cantidad,
                  horizontales: c.horizontales, seccion: seccionTotal, columnas };
  }
  return salida;
}

// 4. Devanado
function validar(tipo, cantidad, horizontales, nEspiras, epc) {
  const r = TIPOS[tipo], e = [];
  if (cantidad < 1 || horizontales < 1) return ["La cantidad de conductores y las horizontales deben ser al menos 1."];
  if (cantidad > r.max_cond) e.push(`${tipo}: máximo ${r.max_cond} conductores por espira (ingresaste ${cantidad}).`);
  if (r.h_fijo !== null && horizontales !== r.h_fijo) e.push(`${tipo}: las horizontales son fijas = ${r.h_fijo}.`);
  else if (horizontales > r.max_h) e.push(`${tipo}: máximo ${r.max_h} horizontales.`);
  if (cantidad % horizontales) e.push(`${cantidad} conductores no se reparten en ${horizontales} horizontales (la cantidad debe ser múltiplo de las horizontales).`);
  else {
    const rad = cantidad / horizontales;
    if (r.radiales && r.radiales.length === 1 && r.radiales[0] === 1 && rad !== 1) e.push(`${tipo}: 1 radial fijo, solo se permite 1x1, 2x2 o 3x3.`);
    else if (r.radiales && !r.radiales.includes(rad)) e.push(`${tipo}: se permiten ${r.radiales.join(" o ")} verticales (radiales); ${cantidad} = ${horizontales} x ${rad} da ${rad}.`);
  }
  if (nEspiras < 1 || epc < 1) e.push("Las espiras totales y las espiras por capa deben ser al menos 1 (si ingresas capas, no pueden ser más que las espiras).");
  else if (r.capas_fijas) {                  // FRANCÉS: siempre 2 capas · HÉLICE: una sola capa
    const capas = Math.trunc(redondeoMas(espirasPorSeccion(tipo, nEspiras) / epc, 0));
    const regla = r.capas_fijas === 1 ? "es de una sola capa" : `es de ${r.capas_fijas} capas`;
    if (capas !== r.capas_fijas) e.push(`${tipo}: ${regla}; con ${nTexto(epc)} espiras por capa salen ${capas} ${capas === 1 ? "capa" : "capas"}.`);
  }
  return e;
}
const espirasPorSeccion = (tipo, n) => Math.trunc(redondeoMas(n / TIPOS[tipo].secciones, 0));
// Galleta: 2 bobinas en el mismo eje. La primera lleva REDONDEO.MAS(N / 2) espiras y la segunda el resto (con N impar,
// una espira menos); las dos se dimensionan con la mayor. null si el tipo no es de 2 bobinas.
function espirasPorBobina(tipo, n) {
  const r = TIPOS[tipo];
  if (!r || r.secciones < 2 || n === null || n === undefined) return null;
  const a = espirasPorSeccion(tipo, n);
  return [a, n - a];
}
const textoBobinas = (b) => `${b[0]} + ${b[1]}`;

// [espesor calato, ancho calato, papel, sección de cobre, nombre] de 1 conductor
function medidasConductor(conductor, medida, papelPlatina) {
  if (conductor === "PLATINA") {
    const [e, a] = PLATINAS[medida];
    return [e, a, papelPlatina, seccionPlatina(e, a), `Platina ${e} x ${a} mm`];
  }
  const [s, d] = ALAMBRES[medida];
  return [d, d, 0, s, `Alambre cal. ${medida} (Ø ${d} mm)`];
}

// Paso 2: el devanado se construye dentro de la ventana. Altura disponible = Hc − 2 x mínimo al yugo
// (galleta: menos la separación y entre 2). Espiras por capa que entran = ENTERO(disponible − transp.) / ancho − 1;
// capas = REDONDEO.MAS(espiras / esp. por capa que entran). capas = null si no entra ni una.
function ajusteVentana(tipo, conductor, medida, horizontales, papelPlatina, nEspiras, transp, hc, yugoMin) {
  const [, ancCal, papel] = medidasConductor(conductor, medida, papelPlatina);
  const anchoCond = papel + ancCal, anchoEspira = anchoCond * horizontales, nSec = TIPOS[tipo].secciones;
  const axialDisp = hc - 2 * yugoMin;
  const porSeccion = (axialDisp - (nSec - 1) * SEPARACION_GALLETA) / nSec;
  const util = Math.floor(pyRound(porSeccion - transp * anchoCond, 6));
  const epcLim = util / anchoEspira - 1;
  const nPorSec = espirasPorSeccion(tipo, nEspiras);
  // FRANCÉS: siempre 2 capas (espiras por capa = N / 2) · HÉLICE: una sola capa (todas las espiras en ella);
  // si no caben en la altura, el al yugo lo muestra (faltan mm)
  const fijas = TIPOS[tipo].capas_fijas || null;
  const capas = epcLim >= 1 ? (fijas || Math.trunc(redondeoMas(nPorSec / epcLim, 0))) : null;
  return { hc, yugo: yugoMin, axial_disp: axialDisp, por_seccion: porSeccion, util, epc_lim: epcLim, capas,
           n_por_sec: nPorSec, ancho_espira: anchoEspira, ancho_cond: anchoCond, n_sec: nSec,
           capas_fijas: fijas, entra_fijas: fijas ? epcLim >= nPorSec / fijas - 1e-9 : null };
}

function calcularDevanado(tipo, conductor, medida, cantidad, horizontales, papelPlatina, nEspiras, epc, papelCapa,
                          canales, transp, corriente = 0, capasIn = null, ventana = null) {
  const [espCal, ancCal, papel, seccion, nombre] = medidasConductor(conductor, medida, papelPlatina);
  const anchoCond = papel + ancCal, espCond = papel + espCal;
  const radiales = Math.trunc(cantidad / horizontales);
  const anchoEspira = anchoCond * horizontales, espesorEspira = espCond * radiales;
  const nSec = TIPOS[tipo].secciones, nPorSec = espirasPorSeccion(tipo, nEspiras);
  let capas, capasCalc;
  if (capasIn) { capas = Math.trunc(capasIn); epc = nPorSec / capas; capasCalc = capas; }
  else { capasCalc = nPorSec / epc; capas = Math.trunc(redondeoMas(capasCalc, 0)); }
  const sumaCanales = canales.reduce((a, b) => a + b, 0);
  const radialBruto = capas * (papelCapa + espesorEspira) + sumaCanales;
  const radial = redondeoMas(radialBruto);
  const axialBruto = (epc + 1) * anchoEspira;
  const axialRed = redondeoMas(axialBruto);
  const axialSeccion = axialRed + transp * anchoCond;
  const axialTotal = nSec * axialSeccion + (nSec - 1) * SEPARACION_GALLETA;
  const seccionTotal = seccionEspira(conductor, seccion, cantidad);      // platina: x 0.97
  return { tipo, conductor, medida, nombre, papel, esp_cal: espCal, anc_cal: ancCal, ancho_cond: anchoCond, esp_cond: espCond,
    seccion, seccion_total: seccionTotal, corriente, densidad: corriente > 0 ? corriente / seccionTotal : null,
    cantidad, horizontales, radiales, ancho_espira: anchoEspira, espesor_espira: espesorEspira,
    n_espiras: nEspiras, n_por_sec: nPorSec, esp_por_capa: epc, capas_calc: capasCalc, capas, modo_capas: !!capasIn, ventana,
    espiras_ultima: nPorSec - (capas - 1) * epc, papel_capa: papelCapa, canales, suma_canales: sumaCanales,
    radial_bruto: radialBruto, radial, transposiciones: transp, axial_bruto: axialBruto, axial_redondeado: axialRed,
    axial_seccion: axialSeccion, n_sec: nSec, axial_total: axialTotal };
}

// 5. Montaje, Vcc y verificaciones
function calcularMontaje(nuc, elec, lista, entreFases, tRef, tubo = 0) {
  const rhoT = RHO_CU_20 * (234.5 + tRef) / (234.5 + 20);
  const filas = [];
  let dPrev = nuc.dn;
  for (const item of lista) {
    const res = item.res, e = elec.dev[item.clave];
    const dInt = dPrev + 2 * item.canal, dExt = dInt + 2 * res.radial, dMed = (dInt + dExt) / 2;
    const lEsp = Math.PI * dMed, longFase = e.n_max * lEsp / 1000;
    const peso = FASES * longFase * res.seccion_total * DENS_CU / 1000;
    const rFase = rhoT * e.n_nom * lEsp / 1000 / res.seccion_total;
    const altura = res.axial_total + 2 * item.yugo;            // altura que necesita con el mínimo al yugo
    const alYugo = (nuc.hc - res.axial_total) / 2;             // lo que queda al yugo (devanado centrado)
    filas.push({ pos: item.pos, clave: item.clave, nombre: e.nombre, tipo: res.tipo, canal: item.canal, yugo: item.yugo,
      d_int: dInt, d_ext: dExt, d_med: dMed, radial: res.radial, axial: res.axial_total, axial_seccion: res.axial_seccion,
      n_sec: res.n_sec, seccion: res.seccion_total, capas: res.capas, radiales: res.radiales, n_canales: res.canales.length, ventana: !!res.ventana, altura, margen_hc: nuc.hc - altura, al_yugo: alYugo, margen_yugo: alYugo - item.yugo, l_espira: lEsp, long_fase: longFase, peso, r_fase: rFase,
      i_carga: e.i_carga, perdidas: FASES * e.i_carga ** 2 * rFase,
      j_nom: e.i_fase / res.seccion_total, j_max: e.i_max / res.seccion_total });
    dPrev = dExt;
  }
  const dTotal = dPrev + 2 * tubo, deMin = dTotal + entreFases;
  return { filas, t_ref: tRef, entre_fases: entreFases, d_dev: dPrev, tubo, d_total: dTotal, de_min: deMin,
    margen_de: nuc.de - deMin, entre_fases_real: nuc.de - dTotal, hc_min: Math.max(...filas.map((f) => f.altura)),
    peso_cu: filas.reduce((s, f) => s + f.peso, 0), perdidas: filas.reduce((s, f) => s + f.perdidas, 0) };
}

function kRogowski(i) {
  let v = TABLA_ROGOWSKI[0][1];
  for (const [desde, k] of TABLA_ROGOWSKI) if (i >= desde) v = k;
  return v;
}

function calcularVcc(elec, mont) {
  const porClave = Object.fromEntries(mont.filas.map((f) => [f.clave, f]));
  const atE = elec.dev[PRINCIPAL], sFe = elec.seccion_neta / 100, bKg = elec.b_real * 10;
  const pares = [];
  for (const k of elec.secundarios) {
    if (!porClave[k] || !porClave[PRINCIPAL]) continue;
    const aF = porClave[PRINCIPAL], sF = porClave[k];
    const [dentro, fuera] = aF.pos < sF.pos ? [aF, sF] : [sF, aF];
    const secE = elec.dev[k], sBase = Math.min(atE.kva, secE.kva);
    const iSec = corrienteFase(sBase, secE.volt, secE.conex), iAt = corrienteFase(sBase, atE.volt, atE.conex);
    const lam = (fuera.d_int - dentro.d_ext) / 2, dM = (aF.d_med + sF.d_med) / 2, hEq = (aF.axial + sF.axial) / 2;
    const kR = kRogowski(iSec);
    const reactiva = (secE.n_nom * iSec) * (Math.PI * dM) * (lam + (aF.radial + sF.radial) / 3) * kR * K_VCC / (hEq * bKg * sFe);
    const perdidas = FASES * (iSec ** 2 * sF.r_fase + iAt ** 2 * aF.r_fase);
    const activa = perdidas / (sBase * 10);
    pares.push({ par: `${atE.nombre} – ${secE.nombre}`, clave: k, s_base: sBase, n: secE.n_nom, i: iSec, d_m: dM, lam,
      e_pri: aF.radial, e_sec: sF.radial, h_eq: hEq, k_r: kR, b_kg: bKg, s_fe: sFe, perdidas,
      ux: reactiva, ur: activa, uz: Math.hypot(reactiva, activa) });
  }
  return pares;
}

function estadoError(e) {
  const a = Math.abs(e);
  return a > ERROR_RELACION_MAX ? "no" : a > ERROR_RELACION_AVISO ? "procede" : "ok";
}
const TEXTO_ERROR = { ok: "cumple", procede: "en rojo, procede", no: "no procede" };
const signoTexto = (x) => `${x >= 0 ? "+" : "-"}${Math.abs(x).toFixed(2)}`;
// Punto de verificación del error de relación: cada tensión de cada devanado y cada toma de la regulación
function erroresRelacion(elec) {
  const out = [];
  for (const k of elec.activos) elec.dev[k].tensiones.forEach((t, j) =>
    out.push({ quien: `${elec.dev[k].nombre} · ${j ? "2ª" : "1ª"} tensión ${milesTexto(t.volt)} V`, espiras: t.n, error: t.error, estado: estadoError(t.error) }));
  for (const t of elec.taps)
    out.push({ quien: `Toma ${t.pos}${t.pos === elec.tap_nom ? " (nominal)" : ""} · ${signoTexto(t.pct)} % · ${milesTexto(t.v_linea)} V`, espiras: t.espiras,
      error: t.error, estado: estadoError(t.error) });
  return out;
}

function verificaciones(nuc, elec, mont, fmt) {
  const v = [], b = elec.b_real;
  v.push([b <= elec.b_objetivo + 1e-9, `Inducción real ${b.toFixed(3)} T frente al objetivo de ${fmt.g(elec.b_objetivo)} T.`]);
  const errs = elec.taps.map((t) => Math.abs(t.error)).concat(elec.activos.flatMap((k) => elec.dev[k].tensiones.map((t) => Math.abs(t.error))));
  const mx = Math.max(...errs);
  const er = estadoError(mx);
  v.push([er === "ok" ? true : er === "procede" ? "procede" : false, `Error máximo de relación ${mx.toFixed(2)} % (admisible ${fmt.g(ERROR_RELACION_MAX)} %; en rojo desde ${fmt.g(ERROR_RELACION_AVISO)} %)${er === "ok" ? "" : `: ${TEXTO_ERROR[er]}`}.`]);
  for (const f of mont.filas) {
    const txt = f.margen_yugo >= 0 ? `sobran ${fmt.n(f.margen_yugo)} mm` : `faltan ${fmt.n(-f.margen_yugo)} mm por lado`;
    v.push([f.margen_yugo >= 0, `Altura ${f.nombre}: axial ${fmt.n(f.axial)} mm en ventana Hc = ${fmt.n(nuc.hc)} mm; al yugo quedan (${fmt.n(nuc.hc)} − ${fmt.n(f.axial)}) / 2 = ${fmt.n(f.al_yugo)} mm (mínimo ${fmt.n(f.yugo)}: ${txt}).`]);
  }
  const txt = mont.margen_de >= 0 ? `sobran ${fmt.n(mont.margen_de)} mm` : `faltan ${fmt.n(-mont.margen_de)} mm`;
  v.push([mont.margen_de >= 0, `Entre fases: De ${fmt.n(nuc.de)} − Ø exterior con tubo ${fmt.n(mont.d_total)} (Ø último devanado ${fmt.n(mont.d_dev)} + 2 x ${fmt.n(mont.tubo)}) = ${fmt.n(mont.entre_fases_real)} mm entre bobinas vecinas (mínimo ${fmt.n(mont.entre_fases)}: ${txt}).`]);
  return v;
}
const entraEnNucleo = (mont) => mont.filas.every((f) => f.margen_yugo >= 0) && mont.margen_de >= 0;
// Lo que no entra en el núcleo (el núcleo es el que limita), con los mm que faltan
function textosNoEntra(nuc, mont) {
  const n = nTexto, t = [];
  for (const f of mont.filas) if (f.margen_yugo < 0)
    t.push(`${f.nombre}: axial ${n(f.axial)} mm en Hc = ${n(nuc.hc)} mm deja ${n(f.al_yugo)} mm al yugo y el mínimo es ${n(f.yugo)} mm (faltan ${n(-f.margen_yugo)} mm por lado).`);
  if (mont.margen_de < 0)
    t.push(`Entre fases: De ${n(nuc.de)} − Ø exterior con tubo ${n(mont.d_total)} = ${n(mont.entre_fases_real)} mm y el mínimo es ${n(mont.entre_fases)} mm (faltan ${n(-mont.margen_de)} mm): las bobinas de fases vecinas quedan muy juntas.`);
  return t;
}

const leerCanales = (t) => (String(t).match(/\d+(?:\.\d+)?/g) || []).map(Number).filter((v) => v > 0);   // formato anterior "4+4"
// Canales internos de refrigeración (aislamiento menor): N° de canales, todos de la misma medida en mm
const canalesInternos = (n, mm) => (Math.trunc(n) > 0 && mm > 0 ? new Array(Math.trunc(n)).fill(mm) : []);
function canalesDe(w) {   // [N°, medida, lista] de un devanado (acepta también el formato anterior "4+4")
  if (w.n_canales === null) return [null, w.canal_mm, []];        // sin digitar (devanado sin uso)
  if (w.n_canales !== undefined) return [w.n_canales, w.canal_mm, canalesInternos(w.n_canales, w.canal_mm)];
  const l = leerCanales(w.canales || "");
  return [l.length, l.length ? l.reduce((a, b) => a + b, 0) / l.length : 0, l];
}

// Posición radial FIJA: el Devanado I es siempre el externo; hacia el núcleo siguen el II y luego el III.
// Solo cuentan los devanados con potencia; el más interno es la posición 1 (junto al núcleo).
const ORDEN_RADIAL = ["III", "II", "I"];        // del núcleo hacia afuera
const NOTA_POSICION = "El Devanado I es siempre el externo; hacia el núcleo siguen el II y luego el III (el más interno va junto al núcleo). La posición radial no se digita: sale de este orden.";
function posicionesRadiales(dev) {
  const activos = ORDEN_RADIAL.filter((k) => (dev[k].kva || 0) > 0);
  return Object.fromEntries(CLAVES.map((k) => [k, activos.includes(k) ? activos.indexOf(k) + 1 : null]));
}
function conPosiciones(d) {           // copia de los datos con la posición del orden fijo
  const c = JSON.parse(JSON.stringify(d)), p = posicionesRadiales(c.dev);
  for (const k of CLAVES) c.dev[k].pos = p[k];
  return c;
}
const textoPosicion = (p, n) => (p === null ? "—" : p === n ? `${p} · externo` : p === 1 ? `${p} · junto al núcleo` : `${p}`);

// Datos que se digitan (no tienen fuente): si alguno está vacío (null) no se calcula
const ROTULOS_GENERALES = { frec: "frecuencia", rep: "reparto de carga", pasos: "N° de pasos", variacion: "% de variación",
  tap: "tap nominal", dn: "diámetro Dn", de: "distancia entre ejes De", hc: "altura de ventana Hc", g: "traslape g",
  bobj: "B máxima (objetivo)", fa: "factor de apilamiento", fconst: "factor de construcción", tubo: "tubo enrollado exterior", fases: "entre fases mínimo",
  tref: "T° de referencia", barrera: "barrera entre bobinas (hawayano o tubo)", e_barrera: "espesor de la barrera",
  tubo_rigido: "tubo rígido: largo extra", tubo_nucleo: "tubo núcleo–bobina" };
const ROTULOS_DEVANADO = { kva: "potencia", kva2: "2ª potencia", volt: "tensión", volt2: "2ª tensión", conex: "grupo",
  conex2: "2º grupo", calibre: "calibre", cant: "cantidad de conductores", horiz: "horizontales", pos: "posición radial",
  tipo: "tipo de devanado", papel: "papel de platina", papel_capa: "papel entre capas", capas: "N° de capas",
  epc: "espiras por capa", n_canales: "N° de canales internos", canal_mm: "medida de los canales internos",
  transp: "transposiciones", canal: "canal interior", yugo: "distancia mínima al yugo",
  relleno: "relleno de los extremos", industrial: "tensión de prueba industrial" };
const vacio = (v) => v === null || v === undefined || v === "";
// Datos sin fuente que todavía no se digitaron (los que el cálculo usa)
// Datos de un devanado con potencia que el cálculo necesita
function pedirDevanado(w) {
  const pedir = ["kva2", "volt", "volt2", "conex", "conex2", "calibre", "cant", "horiz", "tipo", "papel_capa",
    "n_canales", "transp", "canal", "yugo", "relleno", "industrial"];
  if (!vacio(w.calibre) && w.calibre[0] === "PLATINA") pedir.push("papel");
  if (!vacio(w.n_canales) && w.n_canales > 0) pedir.push("canal_mm");
  if (w.modo === "capas") pedir.push("capas"); else if (w.modo === "epc") pedir.push("epc");
  return pedir;
}
function faltantes(d) {
  const falta = [];
  const gen = Object.keys(ROTULOS_GENERALES).filter((c) => vacio(d[c])).map((c) => ROTULOS_GENERALES[c]);
  if (gen.length) falta.push(`Datos generales: ${gen.join(", ")}.`);
  for (const k of CLAVES) {
    const w = d.dev[k];
    if (vacio(w.kva)) { falta.push(`${NOMBRES[k]}: potencia.`); continue; }
    if (w.kva <= 0) continue;                 // devanado sin potencia: no se usa
    const pedir = pedirDevanado(w);
    const vacios = Object.keys(ROTULOS_DEVANADO).filter((c) => pedir.includes(c) && vacio(w[c])).map((c) => ROTULOS_DEVANADO[c]);
    if (vacios.length) falta.push(`${NOMBRES[k]}: ${vacios.join(", ")}.`);
  }
  return falta;
}
// Lo mismo, dato por dato y con el paso de la pantalla donde se digita
// (1 datos del cliente, 2 núcleo, 3 devanados, 4 distancias eléctricas)
const PASO_GENERAL = { frec: 1, rep: 1, pasos: 1, variacion: 1, tap: 1, dn: 2, de: 2, hc: 2, g: 2, bobj: 2, fa: 2,
  fconst: 2, tubo: 4, fases: 4, tref: 2, barrera: 4, e_barrera: 4, tubo_rigido: 4, tubo_nucleo: 4 };
const PASO_CLIENTE_DEV = ["kva", "kva2", "volt", "volt2", "conex", "conex2", "bil", "industrial"];   // datos del cliente
const PASO_DIST_DEV = ["canal", "yugo", "relleno"];                    // distancias eléctricas
const pasoDev = (c) => (PASO_CLIENTE_DEV.includes(c) ? 1 : PASO_DIST_DEV.includes(c) ? 4 : 3);
const mayuscula = (t) => t.charAt(0).toUpperCase() + t.slice(1);
function faltantesDetalle(d) {
  const out = [];
  for (const c of Object.keys(ROTULOS_GENERALES))
    if (vacio(d[c])) out.push({ paso: PASO_GENERAL[c], k: null, c, rotulo: mayuscula(ROTULOS_GENERALES[c]) });
  for (const k of CLAVES) {
    const w = d.dev[k];
    if (vacio(w.kva)) { out.push({ paso: 1, k, c: "kva", rotulo: `${NOMBRES[k]} · potencia` }); continue; }
    if (w.kva <= 0) continue;
    const pedir = pedirDevanado(w);
    for (const c of Object.keys(ROTULOS_DEVANADO))
      if (pedir.includes(c) && vacio(w[c]))
        out.push({ paso: pasoDev(c), k, c, rotulo: `${NOMBRES[k]} · ${ROTULOS_DEVANADO[c]}` });
  }
  return out.sort((a, b) => a.paso - b.paso);
}

// 6. Esfuerzos dieléctricos (hoja de esfuerzos): tensión de prueba industrial / distancia
//   Núcleo – bobina más interna: E = prueba industrial / (canal interior + tubo núcleo–bobina) < 1.8 kV/mm (máx. 2)
//   Bobina – bobina, por contorneo: E = prueba industrial (la mayor de las dos) / contorno < 0.8 kV/mm, con
//     lado = canal interior / 2 a cada lado de la barrera · s = tubo rígido / 2 (sobresale por lado) · R = radial de la bobina de afuera
//     d1 = √(lado² + (relleno de adentro + s)²) · d2 = lado + 0.75·R · d3 = √((0.75·R)² + s²) · d4 = relleno de afuera
//     d5 = √((relleno de afuera + s)² + lado²) · contorno HAWAYANO = d1 + barrera + d2 + d3 + d4 · TUBO = d1 + barrera + d5
const ESFUERZO_BOB_BOB = 0.8, ESFUERZO_BOB_NUC = 1.8, ESFUERZO_BOB_NUC_MAX = 2.0, FACTOR_RADIAL_CONTORNO = 0.75;
const BARRERAS = ["HAWAYANO", "TUBO"];
// 1 decimal con el .5 hacia arriba (igual en Python: 26.25 -> 26.3)
const unoTexto = (x) => (Math.floor(x * 10 + 0.5) / 10).toFixed(1);
const kvmm = (E) => (isFinite(E) ? E.toFixed(2) : "∞");      // sin distancia: esfuerzo infinito
function esfuerzosDielectricos(mont, dev, d) {
  const out = [], f = mont.filas, n = nTexto, g = gTexto, r1 = unoTexto;
  if (!f.length) return out;
  const a = f[0], ua = dev[a.clave].industrial, dist0 = a.canal + d.tubo_nucleo, e0 = dist0 > 0 ? ua / dist0 : Infinity;
  out.push({ clave: `nuc-${a.clave}`, tipo: "bob-nuc", nombre: `Núcleo – ${a.nombre}`, tension: ua, distancia: dist0, esfuerzo: e0, partes: null,
    lineas: [`Distancia = canal interior del ${a.nombre} + tubo núcleo–bobina = ${n(a.canal)} + ${g(d.tubo_nucleo)} = ${n(dist0)} mm`,
      `E = prueba industrial ${a.nombre} / distancia = ${g(ua)} kV / ${n(dist0)} mm = ${kvmm(e0)} kV/mm`] });
  for (let i = 1; i < f.length; i++) {
    const bi = f[i - 1], bo = f[i], wi = dev[bi.clave], wo = dev[bo.clave];
    const lado = bo.canal / 2, s = d.tubo_rigido / 2, R = FACTOR_RADIAL_CONTORNO * bo.radial, eb = d.e_barrera;
    const d1 = Math.hypot(lado, wi.relleno + s), d2 = lado + R, d3 = Math.hypot(R, s), d4 = wo.relleno, d5 = Math.hypot(wo.relleno + s, lado);
    const tubo = d.barrera === "TUBO", total = tubo ? d1 + eb + d5 : d1 + eb + d2 + d3 + d4;
    const U = Math.max(wi.industrial, wo.industrial), E = total > 0 ? U / total : Infinity;
    const lineas = [
      `lado = canal interior del ${bo.nombre} / 2 = ${n(bo.canal)} / 2 = ${n(lado)} mm · s = tubo rígido / 2 = ${g(d.tubo_rigido)} / 2 = ${g(s)} mm · 0.75·R = 0.75 x ${n(bo.radial)} = ${n(R)} mm`,
      `d1 = √(lado² + (relleno ${bi.nombre} + s)²) = √(${n(lado)}² + (${g(wi.relleno)} + ${g(s)})²) = ${r1(d1)} mm`];
    if (tubo) lineas.push(`d5 = √((relleno ${bo.nombre} + s)² + lado²) = √((${g(wo.relleno)} + ${g(s)})² + ${n(lado)}²) = ${r1(d5)} mm`,
      `Contorno (TUBO) = d1 + tubo + d5 = ${r1(d1)} + ${g(eb)} + ${r1(d5)} = ${r1(total)} mm`);
    else lineas.push(`d2 = lado + 0.75·R = ${n(lado)} + ${n(R)} = ${r1(d2)} mm · d3 = √((0.75·R)² + s²) = √(${n(R)}² + ${g(s)}²) = ${r1(d3)} mm · d4 = relleno ${bo.nombre} = ${g(d4)} mm`,
      `Contorno (HAWAYANO) = d1 + hawayano + d2 + d3 + d4 = ${r1(d1)} + ${g(eb)} + ${r1(d2)} + ${r1(d3)} + ${r1(d4)} = ${r1(total)} mm`);
    lineas.push(`E = prueba industrial (la mayor: ${g(U)} kV) / contorno = ${g(U)} / ${r1(total)} = ${kvmm(E)} kV/mm`);
    out.push({ clave: `bob-${bi.clave}-${bo.clave}`, tipo: "bob-bob", nombre: `${bi.nombre} – ${bo.nombre}`, tension: U, distancia: total, esfuerzo: E,
      partes: { d1, e: eb, d2, d3, d4, d5 }, lineas });
  }
  return out;
}
// Estado de un esfuerzo: bobina–bobina hasta 0.8 kV/mm; núcleo–bobina hasta 1.8 kV/mm y de 1.8 a 2 en rojo pero procede
function limiteEsfuerzo(x) {
  const g = gTexto, E = x.esfuerzo;
  const base = { clave: `esf-${x.clave}`, paso: 4, nombre: `Esfuerzo ${x.nombre}`, valor: isFinite(E) ? `${E.toFixed(2)} kV/mm` : "sin distancia", formula: x.lineas.join("; ") };
  if (x.tipo === "bob-bob") {
    const u = E / ESFUERZO_BOB_BOB;
    return { ...base, limite: `máx. ${g(ESFUERZO_BOB_BOB)} kV/mm`, uso: u, estado: u > 1 + 1e-9 ? "no" : u >= 0.9 - 1e-12 ? "cerca" : "ok", nota: "" };
  }
  const u = E / ESFUERZO_BOB_NUC;
  const est = E > ESFUERZO_BOB_NUC_MAX + 1e-9 ? "no" : E > ESFUERZO_BOB_NUC + 1e-9 ? "procede" : u >= 0.9 - 1e-12 ? "cerca" : "ok";
  return { ...base, limite: `${g(ESFUERZO_BOB_NUC)} kV/mm (máx. ${g(ESFUERZO_BOB_NUC_MAX)})`, uso: u, estado: est,
    nota: est === "procede" ? `de ${g(ESFUERZO_BOB_NUC)} a ${g(ESFUERZO_BOB_NUC_MAX)} kV/mm, procede` : est === "no" ? `pasa de ${g(ESFUERZO_BOB_NUC_MAX)} kV/mm` : "" };
}

// Límites del diseño con su % de uso (uso = exigido / disponible; más de 100 % no cumple, desde 90 % está cerca).
// cond: tus condiciones { jmax, bmin, bmax, vcc, tol } (las que falten no se verifican).
const gTexto = (x) => String(Number(Number(x).toPrecision(6)));
function limitesDiseno(nuc, elec, mont, pares, cond = {}, esf = []) {
  const L = [], n = nTexto;
  const estado = (uso) => (uso > 1 + 1e-9 ? "no" : uso >= 0.9 - 1e-12 ? "cerca" : "ok");
  const usoMin = (min, real) => (min <= 0 ? 0 : real > 0 ? min / real : Infinity);
  let u = usoMin(mont.entre_fases, mont.entre_fases_real);
  L.push({ clave: "fases", paso: 4, nombre: "Entre fases", valor: `${n(mont.entre_fases_real)} mm`, limite: `mín. ${n(mont.entre_fases)} mm`, uso: u, estado: estado(u),
    nota: estado(u) === "no" ? `faltan ${n(mont.entre_fases - mont.entre_fases_real)} mm` : "",
    formula: `De − Ø exterior con tubo = ${n(nuc.de)} − ${n(mont.d_total)} = ${n(mont.entre_fases_real)} mm; uso = mínimo / real = ${n(mont.entre_fases)} / ${n(mont.entre_fases_real)}` });
  for (const f of mont.filas) {
    u = usoMin(f.yugo, f.al_yugo);
    // con «Ajustar a la ventana» el devanado llena la altura hasta el mínimo: estar cerca es lo buscado, no un aviso
    const ajustado = f.ventana && u <= 1 + 1e-9, est = ajustado ? "ok" : estado(u);
    L.push({ clave: `yugo-${f.clave}`, paso: 4, nombre: `Al yugo · ${f.nombre}`, valor: `${n(f.al_yugo)} mm`, limite: `mín. ${n(f.yugo)} mm`, uso: u, estado: est,
      nota: est === "no" ? `faltan ${n(f.yugo - f.al_yugo)} mm por lado` : ajustado ? "ajustado a la ventana" : "", ajustado,
      formula: `(Hc − axial) / 2 = (${n(nuc.hc)} − ${n(f.axial)}) / 2 = ${n(f.al_yugo)} mm; uso = mínimo / real = ${n(f.yugo)} / ${n(f.al_yugo)}` });
  }
  // canales internos: van entre conductores vecinos en la dirección radial, dentro de la espira (entre sus conductores
  // radiales) y, si el devanado tiene varias capas, también entre capas: caben radiales x capas − 1
  for (const f of mont.filas) if (f.n_canales > 0) {
    const huecos = f.radiales * f.capas, caben = Math.max(huecos - 1, 0), uC = caben > 0 ? f.n_canales / caben : Infinity, est = f.n_canales > caben ? "no" : "ok";
    const capaT = f.capas === 1 ? "capa" : "capas";
    L.push({ clave: `canales-${f.clave}`, paso: 3, nombre: `Canales internos · ${f.nombre}`, valor: `${f.n_canales} entre ${huecos} conductores radiales`,
      limite: `máx. ${caben} (radiales x capas − 1)`, uso: uC, estado: est, nota: est === "no" ? `caben ${caben}` : "",
      formula: `los canales van entre conductores vecinos en la dirección radial (dentro de la espira y entre capas): ${f.radiales} ${f.radiales === 1 ? "radial" : "radiales"} x ${f.capas} ${capaT} − 1 = ${caben} ${caben === 1 ? "espacio" : "espacios"}; uso = ${f.n_canales} / ${caben}` });
  }
  for (const x of esf || []) L.push(limiteEsfuerzo(x));
  if (!vacio(cond.jmax) && cond.jmax > 0) for (const f of mont.filas) {
    const e = elec.dev[f.clave], sec = e.i_max / f.j_max;
    u = f.j_max / cond.jmax;
    L.push({ clave: `j-${f.clave}`, paso: 3, nombre: `Densidad · ${f.nombre}`, valor: `${f.j_max.toFixed(2)} A/mm²`, limite: `máx. ${gTexto(cond.jmax)} A/mm²`, uso: u, estado: estado(u),
      formula: `J = I máxima / sección = ${e.i_max.toFixed(2)} / ${sec.toFixed(2)} = ${f.j_max.toFixed(2)} A/mm²; uso = ${f.j_max.toFixed(2)} / ${gTexto(cond.jmax)}` });
  }
  if (!vacio(cond.bmax) && cond.bmax > 0) {
    const b = elec.b_real, bajo = !vacio(cond.bmin) && b < cond.bmin - 1e-9;
    u = b / cond.bmax;
    L.push({ clave: "b", paso: 2, nombre: "Inducción B", valor: `${b.toFixed(3)} T`, limite: vacio(cond.bmin) ? `máx. ${gTexto(cond.bmax)} T` : `${gTexto(cond.bmin)} a ${gTexto(cond.bmax)} T`,
      uso: u, estado: bajo ? "no" : estado(u), nota: bajo ? `bajo el mínimo de ${gTexto(cond.bmin)} T` : "",
      formula: `B = V/espira / (4.44 · f · sección neta) = ${elec.v_esp.toFixed(3)} / (4.44 · ${gTexto(elec.frecuencia)} · ${(elec.seccion_neta / 1e6).toFixed(5)}) = ${b.toFixed(3)} T; uso = ${b.toFixed(3)} / ${gTexto(cond.bmax)}` });
  }
  const errs = elec.taps.map((t) => Math.abs(t.error)).concat(elec.activos.flatMap((k) => elec.dev[k].tensiones.map((t) => Math.abs(t.error))));
  const mx = Math.max(...errs);
  u = mx / ERROR_RELACION_MAX;
  const er = estadoError(mx), A = gTexto(ERROR_RELACION_AVISO), M = gTexto(ERROR_RELACION_MAX);
  L.push({ clave: "relacion", paso: 3, nombre: "Error de relación", valor: `${mx.toFixed(2)} %`, limite: `máx. ${M} % · rojo desde ${A} %`, uso: u, estado: er,
    nota: er === "procede" ? `de ${A} a ${M} %, procede` : er === "no" ? `pasa de ${M} %, no procede` : "",
    formula: `el mayor error entre tensiones y tomas = ${mx.toFixed(2)} %; uso = ${mx.toFixed(2)} / ${M}. Hasta ${A} % cumple; de ${A} a ${M} % se marca en rojo pero procede; más de ${M} % no procede` });
  if (!vacio(cond.vcc) && !vacio(cond.tol) && cond.vcc > 0 && cond.tol > 0) for (const p of pares) {
    const tolAbs = cond.vcc * cond.tol / 100;
    u = Math.abs(p.uz - cond.vcc) / tolAbs;
    L.push({ clave: `vcc-${p.clave}`, paso: 5, nombre: `Vcc · ${p.par}`, valor: `${p.uz.toFixed(2)} %`, limite: `${gTexto(cond.vcc)} ± ${gTexto(cond.tol)} %`, uso: u, estado: estado(u),
      formula: `|Vcc − objetivo| / tolerancia = |${p.uz.toFixed(2)} − ${gTexto(cond.vcc)}| / (${gTexto(cond.vcc)} x ${gTexto(cond.tol)} %) = ${Math.abs(p.uz - cond.vcc).toFixed(2)} / ${tolAbs.toFixed(3)}` });
  }
  return L;
}
// El límite que gobierna: el que no cumple o, si todos cumplen, el de mayor uso
function limiteGobernante(L) {
  if (!L.length) return null;
  const malos = L.filter((x) => x.estado === "no"), libres = L.filter((x) => !x.ajustado);
  return (malos.length ? malos : libres.length ? libres : L).reduce((a, b) => (b.uso > a.uso ? b : a));
}

// % de uso como texto (redondeo hacia arriba en .5, igual en Python)
// (hasta 100 % se trunca y desde ahí se sube: 89.7 % se lee 89 % y cumple; 100.4 % se lee 101 % y no cumple)
const pctNum = (uso) => (uso <= 1 ? Math.floor(uso * 100 + 1e-9) : Math.ceil(uso * 100 - 1e-9));
const pctTexto = (uso) => (!isFinite(uso) || uso > 9.99 ? "> 999 %" : `${pctNum(uso)} %`);
const descLimite = (x) => (x.nota ? `${x.nombre}: ${x.nota}` : `${x.nombre} · ${pctTexto(x.uso)}`);
const PASOS = [[1, "Datos del cliente"], [2, "Núcleo"], [3, "Devanados"], [4, "Distancias"], [5, "Resultados"]];
const ULTIMO_PASO = PASOS.length;           // el de resultados
const PESO_ESTADO = { ok: 0, cerca: 1, procede: 2, no: 3 };
// Estado de cada paso para la barra de pasos: ok · cerca · falta · no · pend, con un texto corto.
// det = faltantesDetalle(d); errores = los que impiden calcular; L = limitesDiseno (null si no se calculó); nucOk = el núcleo se pudo calcular
function estadoPasos(det, errores, L, nucOk) {
  const out = [];
  const peor = (lista) => lista.reduce((a, b) => (PESO_ESTADO[b.estado] > PESO_ESTADO[a.estado] || (b.estado === a.estado && b.uso > a.uso) ? b : a));
  for (const [p, nombre] of PASOS) {
    const falta = det.filter((x) => x.paso === p).length;
    let estado, texto;
    if (p < ULTIMO_PASO && falta) { estado = "falta"; texto = `Faltan ${falta} ${falta === 1 ? "dato" : "datos"}`; }
    else if (p === ULTIMO_PASO && det.length) { estado = "pend"; texto = `Faltan ${det.length} ${det.length === 1 ? "dato" : "datos"} en los pasos 1 a ${ULTIMO_PASO - 1}`; }
    else if (!L) {
      // sin núcleo, lo que hay que revisar está en el núcleo; con núcleo, en los devanados
      const aqui = errores.length && ((p === 2 && !nucOk) || (p === 3 && nucOk));
      if (aqui) { estado = "no"; texto = `Revisar ${errores.length} ${errores.length === 1 ? "dato" : "datos"}`; }
      else if (p === ULTIMO_PASO || (p === 4 && errores.length) || (p === 3 && !nucOk)) { estado = "pend"; texto = "Se calcula al completar lo anterior"; }
      else { estado = "ok"; texto = "Completo"; }
    } else {
      const mios = p === ULTIMO_PASO ? L : L.filter((x) => x.paso === p);
      if (!mios.length) { estado = "ok"; texto = "Completo"; }
      else {
        const w = p === ULTIMO_PASO ? limiteGobernante(L) : peor(mios);
        const hay = ["no", "procede", "cerca"].find((e) => mios.some((x) => x.estado === e)) || "ok";
        estado = hay;
        texto = p === ULTIMO_PASO ? `Gobierna: ${descLimite(w)}` : hay === "ok" ? `Cumple · máx. ${pctTexto(w.uso)}` : descLimite(w);
      }
    }
    out.push({ paso: p, nombre, estado, texto });
  }
  return out;
}

// Fórmula con los valores de cada resultado principal y de dónde sale (se muestra al tocar el resultado)
const milesTexto = (x, dec = 0) => {
  const t = Math.abs(x).toFixed(dec), [e, f] = t.split(".");
  return (x < 0 && Number(t) !== 0 ? "-" : "") + e.replace(/\B(?=(\d{3})+(?!\d))/g, ",") + (f ? "." + f : "");
};
function explicacionesResultados(nuc, elec, mont, pares, vac) {
  const n = nTexto, g = gTexto, X = [];
  for (const p of pares)
    X.push({ clave: `vcc-${p.clave}`, nombre: `Vcc ${PRINCIPAL}–${p.clave}`, valor: `${p.uz.toFixed(2)} %`, lineas: [
      `Vcc_reactiva = (N·I)·(π·Dm)·(λ + (e1 + e2)/3)·kR·K / (Heq·B·Sfe) = (${p.n}·${p.i.toFixed(2)})·(π·${p.d_m.toFixed(1)})·(${n(p.lam)} + (${n(p.e_pri)} + ${n(p.e_sec)})/3)·${g(p.k_r)}·${g(K_VCC)} / (${n(p.h_eq)}·${p.b_kg.toFixed(3)}·${p.s_fe.toFixed(2)}) = ${p.ux.toFixed(4)} %`,
      `Vcc_activa = Pcu / (S·10) = ${p.perdidas.toFixed(1)} / (${g(p.s_base)}·10) = ${p.ur.toFixed(4)} %`,
      `Vcc = √(Vcc_reactiva² + Vcc_activa²) = √(${p.ux.toFixed(4)}² + ${p.ur.toFixed(4)}²) = ${p.uz.toFixed(4)} %`],
      fuente: `Cálculo de Vcc · K = ${g(K_VCC)} con B en kG, Sfe en cm² y medidas en mm · kR del cuadro de Rogowski con I = ${p.i.toFixed(1)} A` });
  const area = elec.seccion_neta / 1e6, vRef = elec.v_esp * elec.n_ref, ref = elec.dev[elec.ref];
  X.push({ clave: "b", nombre: "B real", valor: `${elec.b_real.toFixed(3)} T`, lineas: [
    `B = (V/espira) / (4.44 · f · Sn) = ${elec.v_esp.toFixed(4)} / (4.44 · ${g(elec.frecuencia)} · ${area.toFixed(6)} m²) = ${elec.b_real.toFixed(4)} T`],
    fuente: `Ley de Faraday E = 4.44·f·N·B·A · Sn = sección neta del núcleo (${(nuc.seccion_neta / 100).toFixed(1)} cm²)` });
  const lineasV = [`V/espira = V fase de referencia / N de referencia = ${vRef.toFixed(2)} / ${elec.n_ref} = ${elec.v_esp.toFixed(4)} V`];
  lineasV.push(elec.n_ref_manual ? `N de referencia = ${elec.n_ref} (ingresadas a mano)`
    : `N de referencia = REDONDEO.MAS(V fase / (4.44 · f · B objetivo · Sn)) = REDONDEO.MAS(${vRef.toFixed(2)} / (4.44 · ${g(elec.frecuencia)} · ${g(elec.b_objetivo)} · ${area.toFixed(6)})) = REDONDEO.MAS(${elec.n_teorico.toFixed(2)}) = ${elec.n_ref}`);
  X.push({ clave: "vesp", nombre: "V / espira", valor: `${elec.v_esp.toFixed(3)} V`, lineas: lineasV,
    fuente: `la menor tensión de fase del diseño: ${ref.nombre}, ${g(elec.ref_volt)} V de línea` });
  const lineasCu = mont.filas.map((f) => `${f.nombre}: ${FASES} · (${elec.dev[f.clave].n_max} esp. · ${f.l_espira.toFixed(1)} mm / 1000) · ${f.seccion.toFixed(2)} mm² · ${g(DENS_CU)} / 1000 = ${f.peso.toFixed(1)} kg`);
  lineasCu.push(`Total = ${mont.filas.map((f) => f.peso.toFixed(1)).join(" + ")} = ${mont.peso_cu.toFixed(1)} kg`);
  X.push({ clave: "cobre", nombre: `Cobre ${FASES} fases`, valor: `${mont.peso_cu.toFixed(1)} kg`, lineas: lineasCu,
    fuente: `fases · largo del conductor por fase (espiras x espira media π·Dm) · sección por espira · densidad del cobre ${g(DENS_CU)} kg/dm³` });
  X.push({ clave: "nucleo", nombre: "Núcleo", valor: `${nuc.peso.toFixed(0)} kg`, lineas: [
    `Peso = Σ escalones = ${nuc.escalones.map((e) => e.peso.toFixed(1)).join(" + ")} = ${nuc.peso.toFixed(1)} kg`],
    fuente: `hoja de corte de núcleo · área de cada escalón x espesor x ${g(RHO_FE)} kg/m³ · plancha de ${g(T_CHAPA)} mm` });
  X.push({ clave: "p0", nombre: "Pérdidas en vacío", valor: `${milesTexto(vac.p0)} W`, lineas: [
    `B para pérdidas = B real + ${g(AUMENTO_B_PERDIDAS)} = ${vac.b_real.toFixed(4)} + ${g(AUMENTO_B_PERDIDAS)} = ${vac.b.toFixed(4)} T`,
    vac.manual ? `Pfe = ${vac.pfe.toFixed(4)} W/kg (a mano)` : `Pfe = c0 + c1·B + c2·B² (${g(vac.f)} Hz) con B = ${vac.b.toFixed(4)} T = ${vac.pfe.toFixed(4)} W/kg`,
    `P0 = Pfe x peso x factor = ${vac.pfe.toFixed(4)} x ${vac.peso.toFixed(1)} x ${g(vac.factor)} = ${vac.p0.toFixed(1)} W`],
    fuente: `Curva de pérdidas de la chapa · regresión cuadrática de la tabla ${MATERIAL_NUCLEO}` });
  const rho = RHO_CU_20 * (234.5 + mont.t_ref) / (234.5 + 20);
  const lineasR = [`ρ a ${g(mont.t_ref)} °C = ${g(RHO_CU_20)} · (234.5 + ${g(mont.t_ref)}) / (234.5 + 20) = ${rho.toFixed(6)} Ω·mm²/m`];
  for (const f of mont.filas)
    lineasR.push(`${f.nombre}: ${FASES} · I² · R = ${FASES} · ${f.i_carga.toFixed(2)}² · ${(f.r_fase * 1000).toFixed(3)} mΩ = ${f.perdidas.toFixed(1)} W (R = ρ · ${elec.dev[f.clave].n_nom} esp. · ${f.l_espira.toFixed(1)} mm / 1000 / ${f.seccion.toFixed(2)} mm²)`);
  lineasR.push(`Total = ${mont.filas.map((f) => f.perdidas.toFixed(1)).join(" + ")} = ${mont.perdidas.toFixed(1)} W`);
  X.push({ clave: "pcu", nombre: "Pérdidas I²R carga", valor: `${milesTexto(mont.perdidas)} W`, lineas: lineasR,
    fuente: `corriente continua con el reparto de carga ${elec.rep_carga}; sin pérdidas adicionales` });
  return X;
}

// Cálculo completo a partir de los datos de la pantalla (d = objeto de datos, ver DATOS_EJEMPLO).
// Devuelve también el dato de bobinado que se llena solo (espiras por capa o N° de capas).
function calcularTodo(d) {
  d = conPosiciones(d);                       // el Devanado I es siempre el externo
  const salida = { errores: [], llenado: {}, entrada: null };
  const specs = {}, cond = {}, bob = {};
  for (const k of CLAVES) {
    const w = d.dev[k];
    // reglas del tipo sobre el arreglo de conductores
    const r = TIPOS[w.tipo];                  // devanado sin uso: puede no tener tipo
    let cant = w.cant, horiz = w.horiz;
    if (r && !vacio(cant) && !vacio(horiz)) {
      cant = Math.min(Math.max(Math.trunc(cant), 1), r.max_cond);
      horiz = Math.min(Math.max(Math.trunc(horiz), 1), r.max_h);
      if (r.h_fijo !== null) horiz = r.h_fijo;
      else if (r.radiales && r.radiales.length === 1 && r.radiales[0] === 1) horiz = cant;
    }
    salida.llenado[k] = { cant, horiz, horizFija: !!r && (r.h_fijo !== null || (r.radiales && r.radiales[0] === 1 && r.radiales.length === 1)),
                          // con «Ajustar a la ventana» las capas salen del cálculo: hasta calcular, quedan vacías
                          capas: w.modo === "ventana" ? null : w.capas, epc: w.modo === "ventana" ? null : w.epc, espiras: null, espirasNom: null };
    specs[k] = { kva: w.kva, kva2: w.kva2, volt: w.volt, volt2: w.volt2, conex: w.conex, conex2: w.conex2, bil: w.bil };
    cond[k] = { conductor: w.calibre[0], medida: w.calibre[1], cantidad: cant, horizontales: horiz };
  }
  salida.specs = specs; salida.cond = cond;
  // corrientes y densidades: se muestran si la parte eléctrica está completa, aunque falten datos de bobinado
  if (CLAVES.every((k) => Object.values(specs[k]).every((v) => !vacio(v)) && !vacio(cond[k].cantidad) && !vacio(cond[k].horizontales)))
    salida.entrada = resumenEntrada(specs, cond);
  const falta = faltantes(d);
  if (falta.length) { salida.errores = falta; salida.faltan = true; return salida; }

  const anchos = d.anchos.filter((a) => a > 0);
  const errNuc = validarNucleo(d.dn, d.g, d.de, d.hc, FACTOR_ELIPSE, anchos);
  if (d.fa <= 0 || d.fa > 1) errNuc.push("Núcleo: el factor de apilamiento debe estar entre 0 y 1.");
  if (d.de <= d.dn) errNuc.push("Núcleo: la distancia entre ejes De debe ser mayor que el diámetro Dn (De va de centro a centro de las columnas).");
  if (errNuc.length) { salida.errores = errNuc; return salida; }
  const nuc = calcularNucleo(d.dn, d.g, d.de, d.hc, FACTOR_ELIPSE, anchos, d.fa);
  salida.nuc = nuc;

  // las espiras de referencia salen siempre de la B objetivo (REDONDEO.MAS): ya no se dan a mano
  const { errores: errElec, elec } = calcularElectrico(specs, d.frec, d.tap, d.variacion, d.pasos, d.rep, nuc.seccion_neta, d.bobj, 0);
  salida.elec = elec;
  for (const k of CLAVES) {
    const w = d.dev[k], e = elec ? elec.dev[k] : null, ll = salida.llenado[k];
    ll.espiras = e ? e.n_max : null; ll.espirasNom = e ? e.n_nom : null;
    ll.capas = w.modo === "ventana" ? null : w.capas; ll.epc = w.modo === "ventana" ? null : w.epc;
    if (e && w.modo !== "ventana") {          // con «Ajustar a la ventana» se llenan después del bobinado
      const nSec = espirasPorSeccion(w.tipo, e.n_max);
      if (w.modo === "capas") ll.epc = redondeoMas(nSec / w.capas, 2);
      else if (w.epc > 0) ll.capas = Math.trunc(redondeoMas(nSec / w.epc, 0));
    }
    const [nCan, mmCan, canales] = canalesDe(w);
    const papel = vacio(w.papel) && w.calibre[0] === "ALAMBRE" ? 0 : w.papel;   // alambre: sin papel
    bob[k] = { pos: w.pos, tipo: w.tipo, papel, papel_capa: w.papel_capa, modo: w.modo, capas: ll.capas,
               epc: ll.epc, canal: w.canal, yugo: w.yugo, n_canales: nCan, canal_mm: mmCan, canales, transp: w.transp };
  }
  salida.bob = bob;

  // pérdidas en el núcleo con la inducción real: Pfe siempre de la regresión de la tabla M4 0.27 mm
  const errVac = [];
  if (d.fconst <= 0) errVac.push("Pérdidas en el núcleo: el factor de construcción debe ser mayor que 0.");
  else if (elec) salida.vacio = calcularVacio(nuc, elec, 0, d.fconst);
  const errores = [...errElec, ...errVac];
  if (elec) {
    const porPos = {};
    for (const k of elec.activos) (porPos[bob[k].pos] = porPos[bob[k].pos] || []).push(NOMBRES[k]);
    for (const pos of Object.keys(porPos).sort()) if (porPos[pos].length > 1)
      errores.push(`${porPos[pos].join(" y ")} tienen la misma posición radial (${pos}): cada devanado va en una posición distinta.`);
  }
  if (d.fases < 0 || d.tubo < 0) errores.push("La distancia entre fases y el tubo enrollado no pueden ser negativos.");
  if (Math.min(d.e_barrera, d.tubo_rigido, d.tubo_nucleo) < 0) errores.push("Esfuerzos: la barrera, el tubo rígido y el tubo núcleo–bobina no pueden ser negativos.");
  if (!BARRERAS.includes(d.barrera)) errores.push("Esfuerzos: la barrera entre bobinas es HAWAYANO o TUBO.");
  if (elec) for (const k of elec.activos) if (d.dev[k].relleno < 0 || d.dev[k].industrial < 0)
    errores.push(`${NOMBRES[k]}: el relleno y la tensión de prueba industrial no pueden ser negativos.`);
  const lista = [];
  if (elec) {
    for (const k of [...elec.activos].sort((a, b) => bob[a].pos - bob[b].pos)) {
      const b = bob[k], c = cond[k], e = elec.dev[k];
      const nEsp = e.n_max;
      let ventana = null, capasIn = b.modo === "capas" ? b.capas : null;
      if (b.modo === "ventana") {
        ventana = ajusteVentana(b.tipo, c.conductor, c.medida, c.horizontales, b.papel, nEsp, b.transp, nuc.hc, b.yugo);
        if (ventana.capas === null) {
          const tr = b.transp > 0 ? `; las ${b.transp} transposiciones ocupan ${b.transp} x ${ventana.ancho_cond.toFixed(2)} = ${(b.transp * ventana.ancho_cond).toFixed(1)} mm` : "";
          errores.push(`${NOMBRES[k]}: no entra en la ventana: Hc ${nTexto(nuc.hc)} − 2 x ${nTexto(b.yugo)} al yugo deja ${nTexto(ventana.axial_disp)} mm${tr} y con espiras de ${ventana.ancho_espira.toFixed(2)} mm de ancho no cabe ni una espira por capa.`);
          continue;
        }
        capasIn = ventana.capas;
      }
      const epc = capasIn ? espirasPorSeccion(b.tipo, nEsp) / capasIn : b.epc;
      const err = validar(b.tipo, c.cantidad, c.horizontales, nEsp, epc);
      if (Math.min(b.canal, b.yugo, b.papel, b.papel_capa) < 0) err.push("Papeles, canal interior y distancia al yugo no pueden ser negativos.");
      if (b.n_canales < 0 || (b.n_canales > 0 && !(b.canal_mm > 0))) err.push("Canales internos: con 1 o más canales, la medida de cada canal debe ser mayor que 0 mm.");
      if (err.length) { errores.push(...err.map((x) => `${NOMBRES[k]}: ${x}`)); continue; }
      const res = calcularDevanado(b.tipo, c.conductor, c.medida, c.cantidad, c.horizontales, b.papel, nEsp, epc,
                                   b.papel_capa, b.canales, b.transp, e.i_fase, capasIn, ventana);
      lista.push({ pos: b.pos, clave: k, res, canal: b.canal, yugo: b.yugo });
    }
  }
  salida.lista = lista;
  for (const it of lista) if (it.res.ventana) {   // capas y espiras por capa que salieron de la ventana
    salida.llenado[it.clave].capas = it.res.capas;
    salida.llenado[it.clave].epc = redondeoMas(it.res.esp_por_capa, 2);
  }
  if (errores.length) { salida.errores = errores; return salida; }
  salida.mont = calcularMontaje(nuc, elec, lista, d.fases, d.tref, d.tubo);
  salida.pares = calcularVcc(elec, salida.mont);
  salida.esf = esfuerzosDielectricos(salida.mont, d.dev, d);
  return salida;
}

// Datos de origen, del diseño de referencia: núcleo Dn 259 / De 510 / 6 espiras de referencia y los
// 17 datos que faltaban. Los marcados «referencia» salen del diseño de referencia; los marcados «supuesto» hay que validarlos.
//   código, Hc, g y K: hoja de núcleo · anchos: los óptimos de tabla para Dn 259 · frecuencia y reparto: especificaciones del cliente ·
//   potencias, tensiones, grupos, BIL, calibre, cantidad, horizontales, pasos, % variación y tap: hoja de datos de entrada ·
//   factor de construcción 1: Curva de pérdidas de la chapa · K = 1, espiras de referencia de la B objetivo y Pfe de la tabla: fijos · B máxima 1.73 T, B mínima 1.65 T y J máxima 4.7 A/mm²: tus condiciones ·
//   barrera, tubos, relleno y prueba industrial: hoja de esfuerzos · Vcc objetivo y tolerancia: sin fuente (vacíos = no se verifican)
const DATOS_EJEMPLO = {
  codigo: "TR-1000-22.9", frec: 60, rep: "100-0", pasos: 5, variacion: 2.5, tap: 3,
  dn: 259, de: 510, hc: 440, g: 5, bobj: 1.73,   // con B objetivo 1.73 salen 6 espiras de referencia: B real 1,729 T
  fa: 0.97,            // diseño de referencia (factor de apilamiento)
  fconst: 1,
  tubo: 1,             // diseño de referencia
  fases: 9,            // diseño de referencia (el entre fases que resulta en él); supuesto como mínimo
  tref: 75,            // supuesto: IEC 60076-1, 75 °C para cobre en aceite (el diseño de referencia usa 2,42 W/kg·(A/mm²)², equivale a ~83 °C)
  // condiciones del semáforo, propias del diseño (la búsqueda por Vcc tiene las suyas aparte)
  vcc_obj: null, vcc_tol: null,   // paso 1 · sin fuente: se digitan (vacíos = el Vcc no se verifica)
  b_min: 1.65,                    // paso 2 · tus condiciones (la B máxima es la B objetivo)
  j_max: 4.7,                     // paso 3 · tus condiciones · con la corriente mayor: tensiones y tomas
  barrera: "HAWAYANO", e_barrera: 2, tubo_rigido: 10, tubo_nucleo: 0,
  anchos: [250, 235, 220, 195, 170, 140, 110, 60, 0, 0],   // ancho óptimo de tabla para Dn 259, 8 escalones, a 5 mm
  dev: {
    I: { kva: 1000, kva2: 0, volt: 22900, volt2: 10000, conex: "D", conex2: "Y", bil: 75, calibre: ["ALAMBRE", 9], cant: 2, horiz: 2,
         tipo: "CONTINUO",   // diseño de referencia · AT = C. CONT. (1 bobina axial, 1 radial)
         papel: null, papel_capa: 1,   // diseño de referencia
         modo: "ventana", capas: null, epc: null,
         n_canales: 2, canal_mm: 3,    // diseño de referencia
         transp: 0,
         canal: 10,                    // diseño de referencia = 4+2+4 (canal + hawayano + canal)
         yugo: 20,                     // diseño de referencia = 40 entre los dos extremos
         relleno: 15, industrial: 70 },
    II: { kva: 1000, kva2: 0, volt: 460, volt2: 230, conex: "Y", conex2: "Y", bil: 20, calibre: ["PLATINA", 4], cant: 12, horiz: 2,
         tipo: "HÉLICE SIMPLE",   // diseño de referencia · BT = HELICE (1 capa, ≥2 radiales, PT axial par)
         papel: 0.4, papel_capa: 0,   // diseño de referencia
         modo: "ventana", capas: null, epc: null,
         n_canales: 3, canal_mm: 3,   // diseño de referencia: 3 canales dentro de la espira, entre los conductores radiales
         transp: 3,                   // máximo que cabe en Hc = 440 (el diseño de referencia usa 11 con 8 espiras; aquí hay 12)
         canal: 8,                    // diseño de referencia = 3+2+3 (canal + tubo rígido + canal adicional)
         yugo: 10,                    // diseño de referencia = 20 entre los dos extremos
         relleno: 15, industrial: 3 },
    III: { kva: 0, kva2: 0, volt: 220, volt2: 20, conex: "Y", conex2: "D", bil: 20, calibre: ["PLATINA", 0], cant: 4, horiz: 2,
         tipo: null, papel: null, papel_capa: null, modo: "ventana", capas: null, epc: null, canal: null,
         yugo: null, n_canales: null, canal_mm: null, transp: null, relleno: null, industrial: null },
  },
};
// Condiciones del semáforo: las del propio diseño, no las de la búsqueda por Vcc. Las vacías no se verifican.
const condicionesDiseno = (d) => ({ jmax: d.j_max, bmin: d.b_min, bmax: d.bobj, vcc: d.vcc_obj, tol: d.vcc_tol });

if (typeof module !== "undefined") module.exports = { calcularTodo, condicionesDiseno, espirasPorBobina, textoBobinas, faltantes, faltantesDetalle, limitesDiseno, limiteGobernante, estadoPasos, explicacionesResultados, pctTexto, descLimite, erroresRelacion, estadoError, esfuerzosDielectricos, limiteEsfuerzo, DATOS_EJEMPLO, calcularNucleo, calcularElectrico, calcularDevanado, verificaciones, entraEnNucleo, textosNoEntra, COEF_PERDIDAS, perdidasEspecificas };
