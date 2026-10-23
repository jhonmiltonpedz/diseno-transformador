// ======================================================================
// MODELO 3D DE LA PARTE ACTIVA (Y DE UN TANQUE ESTIMADO)
// Se genera solo con el resultado del cálculo (calcularTodo): ninguna medida se dibuja «a ojo».
// Ejes en mm: x a lo largo del núcleo (fases A, B y C en x = −De, 0 y +De), y = profundidad (el espesor de
// las chapas), z = vertical, con el centro de la ventana en z = 0.
// Cada pieza es una malla de triángulos cerrada (sólidos que no se cruzan), lista para STL u OBJ.
//
//  Núcleo: cada escalón es un marco de chapas (la misma forma con que se calcula su peso):
//    rectángulo exterior C x A con las 4 esquinas cortadas a 45° (traslape g), menos las 2 ventanas.
//    C = 2·De + a,  A = Hc + a₁ + a,  ventana = (De − a) x (Hc + a₁ − a)   (a = ancho del escalón)
//    El escalón 1 (el más ancho) va al centro; cada escalón siguiente se reparte mitad y mitad a los lados.
//    Todo el núcleo es un solo sólido cerrado, sin caras internas (así el corte se ve limpio y el STL es válido).
//    Volumen x 7650 kg/m³ = peso del núcleo calculado (se verifica en verificacion/prueba_3d.js).
//  Devanados: tubos de eje vertical alrededor de cada columna, con los diámetros y la altura del montaje.
//    Los canales internos de refrigeración se reparten parejos a lo largo del radial (supuesto de dibujo);
//    la galleta son 2 bobinas separadas 20 mm.
//  Aislamiento: barrera entre devanados (al centro del canal, con el tubo rígido que sobresale), tubo
//    núcleo–bobina, tubo enrollado exterior y calzas (8 por extremo) que llenan la distancia al yugo.
//  Tanque: estimado, con holguras que se pueden cambiar (no hay cálculo térmico ni de radiadores).
// ======================================================================
const SEGMENTOS_3D = 96;                          // lados de los cilindros
const HOLGURA_CAD = 0.01;                         // mm: dos piezas que se tocan no comparten vértices (el STL queda en sólidos sueltos)
const CALZAS_POR_EXTREMO = 8, ANCHO_CALZA = 30;   // mm
const TANQUE_ESTIMADO = { lateral: 60, frente: 60, fondo: 50, superior: 200, pared: 4, tapa: 6 };   // mm
const COLORES_3D = { nucleo: "#9aa3ab", I: "#b4612a", II: "#d98a45", III: "#e9b27c", aislamiento: "#d8c49b", tanque: "#7e98ad" };
const FASES_3D = ["A", "B", "C"];

// ---------- vectores ----------
const v3 = (x, y, z) => [x, y, z];
const resta = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const suma = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const punto = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cruz = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const unitario = (a) => { const l = Math.hypot(a[0], a[1], a[2]) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const centro = (pts) => pts.reduce((s, p) => suma(s, p), [0, 0, 0]).map((c) => c / pts.length);

// ---------- mallas ----------
function nuevaMalla(id, nombre, grupo, color) { return { id, nombre, grupo, color, pos: [], nor: [], solidos: 0 }; }
function triangulo(m, a, b, c, na, nb, nc) { m.pos.push(...a, ...b, ...c); m.nor.push(...na, ...nb, ...nc); }
// Normal de un polígono plano (método de Newell)
function normalNewell(pts) {
  const n = [0, 0, 0];
  for (let i = 0; i < pts.length; i++) {
    const a = pts[i], b = pts[(i + 1) % pts.length];
    n[0] += (a[1] - b[1]) * (a[2] + b[2]); n[1] += (a[2] - b[2]) * (a[0] + b[0]); n[2] += (a[0] - b[0]) * (a[1] + b[1]);
  }
  return n;
}
// Cara plana convexa, con su normal hacia «hacia»
function caraPlana(m, pts, hacia) {
  let p = pts, n = normalNewell(pts);
  if (punto(n, hacia) < 0) { p = pts.slice().reverse(); n = [-n[0], -n[1], -n[2]]; }
  n = unitario(n);
  for (let i = 1; i < p.length - 1; i++) triangulo(m, p[0], p[i], p[i + 1], n, n, n);
}
// Polígono plano en abanico desde su centro (sirve con vértices alineados, donde el abanico desde un vértice
// daría triángulos sin área)
function abanico(m, pts, hacia) {
  const c = centro(pts);
  let p = pts, n = normalNewell(pts);
  if (punto(n, hacia) < 0) { p = pts.slice().reverse(); n = [-n[0], -n[1], -n[2]]; }
  n = unitario(n);
  for (let i = 0; i < p.length; i++) triangulo(m, c, p[i], p[(i + 1) % p.length], n, n, n);
}
// Lazos del marco de un escalón en el plano x-z: contorno exterior (con las esquinas cortadas g) y las 2 ventanas,
// más la cara partida en yugos y columnas. Todos los escalones tienen los mismos vértices en el mismo orden.
function lazosMarco(De, E, a, g) {
  const C2 = De + a / 2, zt = E / 2 + a / 2, zb = E / 2 - a / 2, x1 = -De + a / 2, x2 = -a / 2, x3 = a / 2, x4 = De - a / 2, ch = g > 0;
  const ext = [[-C2, -zb], ...(ch ? [[-C2, -zt + g], [-C2 + g, -zt], [C2 - g, -zt], [C2, -zt + g]] : [[-C2, -zt], [C2, -zt]]), [C2, -zb],
    [C2, zb], ...(ch ? [[C2, zt - g], [C2 - g, zt], [-C2 + g, zt], [-C2, zt - g]] : [[C2, zt], [-C2, zt]]), [-C2, zb]];
  const kB = ch ? 5 : 3;
  return { ext,
    ventanas: [[[x1, -zb], [x2, -zb], [x2, zb], [x1, zb]], [[x3, -zb], [x4, -zb], [x4, zb], [x3, zb]]],
    yugoInf: [...ext.slice(0, kB + 1), [x4, -zb], [x3, -zb], [x2, -zb], [x1, -zb]],
    yugoSup: [...ext.slice(kB + 1), [x1, zb], [x2, zb], [x3, zb], [x4, zb]],
    columnas: [[[-C2, -zb], [x1, -zb], [x1, zb], [-C2, zb]], [[x2, -zb], [x3, -zb], [x3, zb], [x2, zb]], [[x4, -zb], [C2, -zb], [C2, zb], [x4, zb]]] };
}
// Prisma convexo: polígono base (en orden) desplazado por «ext»
function prisma(m, base, ext) {
  const tope = base.map((p) => suma(p, ext)), c = centro(base.concat(tope));
  caraPlana(m, base, resta(centro(base), c));
  caraPlana(m, tope, resta(centro(tope), c));
  for (let i = 0; i < base.length; i++) {
    const j = (i + 1) % base.length, lado = [base[i], base[j], tope[j], tope[i]];
    caraPlana(m, lado, resta(centro(lado), c));
  }
  m.solidos++;
}
// Caja abierta arriba (fondo y 4 paredes en un solo sólido cerrado): interior ±lx x ±ly, de z0 a z1, pared «p»
function cajaAbierta(m, lx, ly, z0, z1, p) {
  const ext = [v3(-lx - p, -ly - p, 0), v3(lx + p, -ly - p, 0), v3(lx + p, ly + p, 0), v3(-lx - p, ly + p, 0)];
  const int = [v3(-lx, -ly, 0), v3(lx, -ly, 0), v3(lx, ly, 0), v3(-lx, ly, 0)];
  const a = (q, z) => v3(q[0], q[1], z), cz = v3(0, 0, (z0 + z1) / 2);
  caraPlana(m, ext.map((q) => a(q, z0 - p)), v3(0, 0, -1));          // fondo por fuera
  caraPlana(m, int.map((q) => a(q, z0)), v3(0, 0, 1));                // fondo por dentro
  for (let i = 0; i < 4; i++) {
    const j = (i + 1) % 4;
    const fuera = [a(ext[i], z0 - p), a(ext[j], z0 - p), a(ext[j], z1), a(ext[i], z1)];
    caraPlana(m, fuera, resta(centro(fuera), cz));                     // pared por fuera
    const dentro = [a(int[i], z0), a(int[j], z0), a(int[j], z1), a(int[i], z1)];
    caraPlana(m, dentro, resta(cz, centro(dentro)));                   // pared por dentro
    caraPlana(m, [a(ext[i], z1), a(ext[j], z1), a(int[j], z1), a(int[i], z1)], v3(0, 0, 1));   // borde de arriba
  }
  m.solidos++;
}
// Caja alineada con los ejes
function caja(m, x0, x1, y0, y1, z0, z1) {
  prisma(m, [v3(x0, y0, z0), v3(x1, y0, z0), v3(x1, y1, z0), v3(x0, y1, z0)], v3(0, 0, z1 - z0));
}
// Tubo de eje vertical en (cx, cy): radios r1 < r2, alturas z0 < z1. Paredes con normales suaves (radiales).
function tubo(m, cx, cy, r1, r2, z0, z1, n = SEGMENTOS_3D) {
  const ang = Array.from({ length: n + 1 }, (_, j) => (2 * Math.PI * (j % n)) / n);
  const cs = ang.map(Math.cos), sn = ang.map(Math.sin);
  const P = (r, j, z) => v3(cx + r * cs[j], cy + r * sn[j], z);
  for (let j = 0; j < n; j++) {
    const k = j + 1, na = v3(cs[j], sn[j], 0), nb = v3(cs[k], sn[k], 0);
    const ia = v3(-cs[j], -sn[j], 0), ib = v3(-cs[k], -sn[k], 0);
    triangulo(m, P(r2, j, z0), P(r2, k, z0), P(r2, k, z1), na, nb, nb);        // pared exterior
    triangulo(m, P(r2, j, z0), P(r2, k, z1), P(r2, j, z1), na, nb, na);
    triangulo(m, P(r1, j, z0), P(r1, k, z1), P(r1, k, z0), ia, ib, ib);        // pared interior
    triangulo(m, P(r1, j, z0), P(r1, j, z1), P(r1, k, z1), ia, ia, ib);
    caraPlana(m, [P(r1, j, z1), P(r2, j, z1), P(r2, k, z1), P(r1, k, z1)], v3(0, 0, 1));    // tapa de arriba
    caraPlana(m, [P(r1, j, z0), P(r2, j, z0), P(r2, k, z0), P(r1, k, z0)], v3(0, 0, -1));   // tapa de abajo
  }
  m.solidos++;
}
// Calza radial (bloque entre r1 y r2, de ancho «w», centrado en el ángulo «t»); la cara de afuera se recorta
// para que sus esquinas no pasen del radio r2
function calza(m, cx, cy, r1, r2, t, w, z0, z1) {
  const u = v3(Math.cos(t), Math.sin(t), 0), q = v3(-Math.sin(t), Math.cos(t), 0), h = w / 2, r2c = Math.sqrt(r2 * r2 - h * h);
  const P = (r, s) => v3(cx + r * u[0] + s * q[0], cy + r * u[1] + s * q[1], z0);
  prisma(m, [P(r1, -h), P(r2c, -h), P(r2c, h), P(r1, h)], v3(0, 0, z1 - z0));
}

// ---------- el modelo ----------
// r = calcularTodo(d); d = los datos del diseño; t = holguras del tanque (mm)
function modelo3d(r, d, t = TANQUE_ESTIMADO) {
  if (!r || !r.mont || !r.nuc || (r.errores && r.errores.length)) return null;
  const nuc = r.nuc, mont = r.mont, partes = [], avisos = [];
  const esc = nuc.escalones.filter((e) => e.ancho > 0 && e.espesor > 0);
  const a1 = esc[0].ancho, E = nuc.hc + a1, g = Math.max(0, nuc.g || 0);
  const xs = [-nuc.de, 0, nuc.de];

  // --- núcleo: UN sólido cerrado, sin caras internas, con los marcos de todos los escalones. El marco de cada escalón
  //     queda dentro del anterior (mismos ejes, columnas más angostas, yugos más delgados, ventanas más altas), así que
  //     entre dos paquetes vecinos la única cara es el anillo «marco k − marco k+1». El escalón 1 va al centro.
  const mNuc = nuevaMalla("nucleo", "Núcleo", "nucleo", COLORES_3D.nucleo);
  const gc = Math.min(g, ...esc.map((e) => e.ancho)), LM = esc.map((e) => lazosMarco(nuc.de, E, e.ancho, gc));
  const Y = [esc[0].espesor / 2];                                       // caras de los paquetes, del centro hacia afuera
  for (let i = 1; i < esc.length; i++) Y.push(Y[i - 1] + esc[i].espesor / 2);
  const P = (q, y) => v3(q[0], y, q[1]);
  const pared = (lazo, ya, yb, adentro) => {
    const c = centro(lazo.map((q) => P(q, 0)));
    lazo.forEach((q, j) => {
      const w = lazo[(j + 1) % lazo.length], med = v3((q[0] + w[0]) / 2, 0, (q[1] + w[1]) / 2);
      caraPlana(mNuc, [P(q, ya), P(w, ya), P(w, yb), P(q, yb)], adentro ? resta(c, med) : resta(med, c));
    });
  };
  esc.forEach((e, i) => {
    for (const [ya, yb] of i === 0 ? [[-Y[0], Y[0]]] : [[Y[i - 1], Y[i]], [-Y[i], -Y[i - 1]]]) {
      pared(LM[i].ext, ya, yb, false);
      for (const v of LM[i].ventanas) pared(v, ya, yb, true);
    }
  });
  for (const sg of [1, -1]) {
    const hacia = v3(0, sg, 0);
    for (let i = 0; i < esc.length - 1; i++) {                          // anillos entre paquetes vecinos
      const y = sg * Y[i];
      for (const [a, b] of [[LM[i].ext, LM[i + 1].ext], ...LM[i].ventanas.map((v, k) => [v, LM[i + 1].ventanas[k]])])
        a.forEach((q, j) => { const k = (j + 1) % a.length; caraPlana(mNuc, [P(q, y), P(a[k], y), P(b[k], y), P(b[j], y)], hacia); });
    }
    const u = LM[esc.length - 1], y = sg * Y[esc.length - 1];          // cara del último paquete: el marco entero
    for (const pol of [u.yugoInf, u.yugoSup]) abanico(mNuc, pol.map((q) => P(q, y)), hacia);
    for (const col of u.columnas) caraPlana(mNuc, col.map((q) => P(q, y)), hacia);
  }
  mNuc.solidos = 1;
  partes.push(mNuc);
  // esquinas del escalón dentro del círculo de Dn (con el redondeo a 10 chapas pueden pasarse un poco)
  let rEsquina = 0, yA = 0;
  for (const e of esc) { yA += e.espesor; rEsquina = Math.max(rEsquina, Math.hypot(e.ancho / 2, yA / 2)); }

  // --- devanados, del núcleo hacia afuera, en las 3 fases
  const canalesDe = Object.fromEntries((r.lista || []).map((it) => [it.clave, (it.res && it.res.canales) || []]));
  const filas = mont.filas, alto = (f) => f.axial;
  for (const f of filas) {
    const can = canalesDe[f.clave] || [], sumaCan = can.reduce((s, c) => s + c, 0);
    const cobre = (f.radial - sumaCan) / (can.length + 1);
    const tramos = f.n_sec > 1
      ? [[-f.axial / 2, -f.axial / 2 + f.axial_seccion], [f.axial / 2 - f.axial_seccion, f.axial / 2]]
      : [[-f.axial / 2, f.axial / 2]];
    xs.forEach((xc, fi) => {
      const m = nuevaMalla(`dev-${f.clave}-${FASES_3D[fi]}`, `${f.nombre} · fase ${FASES_3D[fi]}`, "devanados", COLORES_3D[f.clave] || COLORES_3D.I);
      for (const [z0, z1] of tramos) {
        let ri = f.d_int / 2;
        for (let k = 0; k <= can.length; k++) {
          tubo(m, xc, 0, ri, ri + cobre, z0, z1);
          ri += cobre + (k < can.length ? can[k] : 0);
        }
      }
      m.clave = f.clave;
      partes.push(m);
    });
    if (f.al_yugo < 0) avisos.push(`${f.nombre}: es ${(-2 * f.al_yugo).toFixed(1)} mm más alto que la ventana: choca con los yugos.`);
  }
  if (mont.entre_fases_real < 0) avisos.push(`Entre fases: las bobinas de fases vecinas se cruzan ${(-mont.entre_fases_real).toFixed(1)} mm.`);
  if (filas.length && rEsquina > filas[0].d_int / 2 - (d.tubo_nucleo || 0))
    avisos.push(`Núcleo: una esquina de escalón (r = ${rEsquina.toFixed(1)} mm) toca el devanado interno.`);

  // --- aislamiento mayor
  const mAis = nuevaMalla("aislamiento", "Aislamiento (barreras, tubos y calzas)", "aislamiento", COLORES_3D.aislamiento);
  const mTubo = nuevaMalla("tubo-exterior", "Tubo enrollado exterior", "aislamiento", COLORES_3D.aislamiento);
  mTubo.transparente = true;                                            // en la vista deja ver el cobre
  const hTubo = (h) => Math.min(h + (d.tubo_rigido || 0), nuc.hc);     // el tubo rígido sobresale, sin pasar la ventana
  const barreras = [];
  for (const xc of xs) {
    if (filas.length && d.tubo_nucleo > 0) {                            // tubo núcleo–bobina
      const r2 = filas[0].d_int / 2, r1 = Math.max(r2 - d.tubo_nucleo, rEsquina + 0.5), h = hTubo(alto(filas[0]));
      if (r2 - r1 > 0.1) tubo(mAis, xc, 0, r1, r2, -h / 2, h / 2);
    }
    for (let i = 1; i < filas.length; i++) {                             // barrera al centro del canal entre devanados
      const ra = filas[i - 1].d_ext / 2, rb = filas[i].d_int / 2, e = Math.min(d.e_barrera || 0, (rb - ra) * 0.8);
      if (e > 0) {
        const mid = (ra + rb) / 2, h = hTubo(Math.max(alto(filas[i - 1]), alto(filas[i])));
        tubo(mAis, xc, 0, mid - e / 2, mid + e / 2, -h / 2, h / 2);
        if (xc === xs[0]) barreras.push({ entre: `${filas[i - 1].nombre} – ${filas[i].nombre}`, r: mid, espesor: e, alto: h });
      }
    }
    if (filas.length && mont.tubo > 2 * HOLGURA_CAD) {                  // tubo enrollado exterior (va sobre el último devanado)
      const u = filas[filas.length - 1];
      tubo(mTubo, xc, 0, u.d_ext / 2 + HOLGURA_CAD, u.d_ext / 2 + mont.tubo, -u.axial / 2, u.axial / 2);
    }
    for (const f of filas) {                                             // calzas: llenan la distancia al yugo
      if (f.al_yugo < 1) continue;
      const w = Math.min(ANCHO_CALZA, (Math.PI * f.d_int) / CALZAS_POR_EXTREMO / 3);
      for (let j = 0; j < CALZAS_POR_EXTREMO; j++) {
        const ang = (2 * Math.PI * (j + 0.5)) / CALZAS_POR_EXTREMO;
        calza(mAis, xc, 0, f.d_int / 2, f.d_ext / 2, ang, w, f.axial / 2, nuc.hc / 2);
        calza(mAis, xc, 0, f.d_int / 2, f.d_ext / 2, ang, w, -nuc.hc / 2, -f.axial / 2);
      }
    }
  }
  if (mAis.solidos) partes.push(mAis);
  if (mTubo.solidos) partes.push(mTubo);

  // --- tanque estimado (paredes, fondo y tapa)
  const dTot = mont.d_total, prof = esc.reduce((s, e) => s + e.espesor, 0);
  const altoNucleo = E + a1, L = 2 * nuc.de + Math.max(dTot, a1) + 2 * t.lateral, W = Math.max(dTot, prof) + 2 * t.frente;
  const zf = -altoNucleo / 2 - t.fondo, zt = altoNucleo / 2 + t.superior, p = Math.max(t.pared, 1), ala = 20;
  const mTan = nuevaMalla("tanque", "Tanque (estimado)", "tanque", COLORES_3D.tanque);
  cajaAbierta(mTan, L / 2, W / 2, zf, zt, p);                                           // fondo y paredes: un solo sólido
  caja(mTan, -L / 2 - p - ala, L / 2 + p + ala, -W / 2 - p - ala, W / 2 + p + ala, zt, zt + Math.max(t.tapa, 1));   // tapa con ala
  partes.push(mTan);

  // --- medidas y volúmenes (volumen exacto de cada malla, por el teorema de la divergencia)
  const vol = (ms) => ms.reduce((s, m) => s + volumenMalla(m), 0);
  const vNuc = volumenMalla(mNuc), vDev = vol(partes.filter((m) => m.grupo === "devanados")), vAis = vol(partes.filter((m) => m.grupo === "aislamiento"));
  const vInterior = L * W * (zt - zf);
  const medidas = {
    nucleo: { largo: 2 * nuc.de + a1, alto: altoNucleo, profundidad: prof, volumen_l: vNuc / 1e6, peso_modelo: (vNuc / 1e9) * RHO_FE,
      peso_calculado: nuc.peso, r_esquina: rEsquina },
    devanados: filas.map((f) => ({ clave: f.clave, nombre: f.nombre, d_int: f.d_int, d_ext: f.d_ext, alto: f.axial, secciones: f.n_sec,
      canales: (canalesDe[f.clave] || []).length, al_yugo: f.al_yugo })),
    barreras,
    tanque: { largo: L, ancho: W, alto: zt - zf, volumen_interior_l: vInterior / 1e6,
      aceite_l: (vInterior - vNuc - vDev - vAis) / 1e6, holguras: { ...t } },
    triangulos: partes.reduce((s, m) => s + m.pos.length / 9, 0),
  };
  return { partes, medidas, avisos, caja: { x: [-L / 2 - p - ala, L / 2 + p + ala], y: [-W / 2 - p - ala, W / 2 + p + ala], z: [zf - p, zt + t.tapa] } };
}

// Volumen encerrado por una malla cerrada: Σ a·(b × c) / 6
function volumenMalla(m) {
  let v = 0;
  const p = m.pos;
  for (let i = 0; i < p.length; i += 9)
    v += p[i] * (p[i + 4] * p[i + 8] - p[i + 5] * p[i + 7]) - p[i + 1] * (p[i + 3] * p[i + 8] - p[i + 5] * p[i + 6]) + p[i + 2] * (p[i + 3] * p[i + 7] - p[i + 4] * p[i + 6]);
  return v / 6;
}

// ---------- exportar a CAD (mm) ----------
// STL binario: todas las piezas en un solo archivo (cada sólido es cerrado)
function aSTL(partes) {
  const n = partes.reduce((s, m) => s + m.pos.length / 9, 0), buf = new ArrayBuffer(84 + 50 * n), dv = new DataView(buf);
  const titulo = "Transformador - parte activa y tanque estimado - mm";
  for (let i = 0; i < 80; i++) dv.setUint8(i, i < titulo.length ? titulo.charCodeAt(i) & 0x7f : 0x20);
  dv.setUint32(80, n, true);
  let o = 84;
  for (const m of partes) {
    const p = m.pos;
    for (let i = 0; i < p.length; i += 9) {
      const a = [p[i], p[i + 1], p[i + 2]], b = [p[i + 3], p[i + 4], p[i + 5]], c = [p[i + 6], p[i + 7], p[i + 8]];
      const nn = unitario(cruz(resta(b, a), resta(c, a)));
      for (const x of nn.concat(a, b, c)) { dv.setFloat32(o, x, true); o += 4; }
      dv.setUint16(o, 0, true); o += 2;
    }
  }
  return buf;
}
// OBJ: un objeto por pieza (núcleo, cada devanado de cada fase, aislamiento, tanque) con vértices compartidos
function aOBJ(partes) {
  const lineas = ["# Transformador: parte activa y tanque estimado", "# Unidades: mm · x a lo largo del núcleo, y profundidad, z vertical"];
  let base = 0;
  for (const m of partes) {
    const indice = new Map(), vs = [], fs = [];
    for (let i = 0; i < m.pos.length; i += 3) {
      const clave = `${m.pos[i].toFixed(4)} ${m.pos[i + 1].toFixed(4)} ${m.pos[i + 2].toFixed(4)}`;
      let k = indice.get(clave);
      if (k === undefined) { k = vs.length + 1; indice.set(clave, k); vs.push(`v ${clave}`); }
      fs.push(k + base);
    }
    lineas.push(`o ${m.id}`, `g ${m.grupo}`, ...vs);
    for (let i = 0; i < fs.length; i += 3) lineas.push(`f ${fs[i]} ${fs[i + 1]} ${fs[i + 2]}`);
    base += vs.length;
  }
  return lineas.join("\n") + "\n";
}

if (typeof module !== "undefined") module.exports = { modelo3d, volumenMalla, aSTL, aOBJ, TANQUE_ESTIMADO, SEGMENTOS_3D };
