// ===== 5 · Modelo 3D: vista con three.js (se carga de internet solo al abrir la pestaña), corte, capas y exportar a CAD =====
// La geometría sale de modelo3d() (modelo3d.js), que no necesita three.js: exportar a STL u OBJ funciona aunque la vista no cargue.
const CLAVE_3D = "diseno-transformador.3d.v1";     // holguras del tanque, capas y corte: van aparte de los datos del diseño
const MODULOS_3D = ["three", "three/addons/controls/OrbitControls.js"];   // resueltos por el importmap de la plantilla
const CAPAS_3D = [["nucleo", "Núcleo", COLORES_3D.nucleo], ["devanados", "Devanados", COLORES_3D.I], ["aislamiento", "Aislamiento", COLORES_3D.aislamiento],
  ["tanque", "Tanque", COLORES_3D.tanque]];
const CORTES_3D = [["", "Sin corte"], ["y", "Vertical"], ["z", "Horizontal"]];   // vertical: quita el frente (y < corte) · horizontal: quita lo de arriba (z > corte)
const VISTAS_3D = [["iso", "Isométrica", [-0.95, -1.55, 0.95]], ["frente", "Frente", [0, -1, 0]], ["planta", "Planta", [0, -1e-4, 1]], ["lado", "Lado", [1, 0, 0]]];
const HOLGURAS_3D = [["lateral", "Lateral", "de la bobina o el yugo a la pared"], ["frente", "Frente y atrás", "de la bobina a la pared"],
  ["fondo", "Abajo", "del yugo al fondo"], ["superior", "Arriba", "del yugo a la tapa (aceite y cámara)"], ["pared", "Pared", "espesor de la plancha"],
  ["tapa", "Tapa", "espesor"]];
const V3 = { tanque: { ...TANQUE_ESTIMADO }, capas: { nucleo: true, devanados: true, aislamiento: true, tanque: true }, corte: "", cortePos: { y: 0, z: 0 },
  fuente: -1, vista: "iso", cache: null, M: null, f: null };
try {
  const g = JSON.parse(leerLocal(CLAVE_3D) || "null");
  if (g) {
    for (const k of Object.keys(V3.tanque)) if (g.tanque && typeof g.tanque[k] === "number" && g.tanque[k] >= 0) V3.tanque[k] = g.tanque[k];
    for (const k of Object.keys(V3.capas)) if (g.capas && typeof g.capas[k] === "boolean") V3.capas[k] = g.capas[k];
    V3.corte = g.corte === "y" || g.corte === "z" ? g.corte : "";
  }
} catch (e) { /* sin almacenamiento o dato viejo */ }
const guardar3d = () => ponerLocal(CLAVE_3D, JSON.stringify({ tanque: V3.tanque, capas: V3.capas, corte: V3.corte }));

// Diseño que se dibuja: el actual o una alternativa de la búsqueda por Vcc
function fuente3d() {
  const res = (BUSQ && BUSQ.r && BUSQ.r.resultados) || [];
  if (V3.fuente >= res.length) V3.fuente = -1;
  if (V3.fuente < 0) return { r: R, d: D, titulo: "Diseño actual", sufijo: "" };
  const alt = res[V3.fuente];
  if (!V3.cache || V3.cache.alt !== alt) {
    let r;
    try { r = calcularTodo(copia(alt.datos)); } catch (ex) { r = { errores: [ex.message] }; }
    V3.cache = { alt, r };
  }
  return { r: V3.cache.r, d: alt.datos, titulo: `Alternativa ${V3.fuente + 1}`, sufijo: `-alt${V3.fuente + 1}` };
}
function calcular3d() {
  const f = fuente3d();
  let M = null;
  try { M = modelo3d(f.r, f.d, V3.tanque); } catch (ex) { M = null; }
  V3.M = M; V3.f = f;
  return M;
}

// ---------- la pestaña ----------
function vista3d() {
  const M = calcular3d(), f = V3.f, res = (BUSQ && BUSQ.r && BUSQ.r.resultados) || [], mm = (x) => F.miles(x, 0);
  const opciones = [`<option value="-1">Diseño actual</option>`, ...res.map((a, i) =>
    `<option value="${i}"${i === V3.fuente ? " selected" : ""}>Alternativa ${i + 1} · Dn ${F.g(a.dn)} · De ${F.g(a.de)} · Vcc ${a.uz.toFixed(2)} %</option>`)].join("");
  const fuente = `<label class="v3d-fuente">Modelo de <select class="campo" id="v3d-fuente">${opciones}</select></label>`;
  if (!M) return [`<div class="v3d-barra">${fuente}</div>`,
    bloque("Modelo 3D", `<p class="vacio">${f.r && f.r.errores && f.r.errores.length ? `Este diseño no se puede dibujar: ${esc(f.r.errores[0])}` : "Faltan datos para dibujar el transformador."}</p>`)].join("");
  const barra = `<div class="v3d-barra">${fuente}
    <div class="segmentos" role="group" aria-label="Vista">${VISTAS_3D.map(([k, t]) => `<button type="button" data-v3d-vista="${k}" aria-pressed="${k === V3.vista}">${t}</button>`).join("")}</div>
    <span class="v3d-corte"><span class="segmentos" role="group" aria-label="Corte">${CORTES_3D.map(([k, t]) =>
      `<button type="button" data-v3d-corte="${k}" aria-pressed="${k === V3.corte}">${t}</button>`).join("")}</span>
      <input type="range" id="v3d-corte-pos" step="1" aria-label="Posición del corte, en mm" hidden>
      <output id="v3d-corte-txt" for="v3d-corte-pos" hidden></output></span></div>`;
  const lienzo = `<div class="v3d-lienzo" id="v3d-lienzo"><p class="v3d-msg" id="v3d-msg">Cargando la vista 3D…</p>
    <div class="v3d-etiqueta" id="v3d-etiqueta" hidden></div><span class="v3d-ejes">mm · x largo · y fondo · z alto</span></div>`;
  const capas = `<div class="v3d-capas">${CAPAS_3D.map(([k, t, c]) =>
    `<label><input type="checkbox" data-v3d-capa="${k}"${V3.capas[k] ? " checked" : ""}><span class="muestra" style="background:${c}"></span>${t}</label>`).join("")}
    <span class="v3d-ayuda">Arrastra para girar · rueda o pellizco para acercar · clic derecho o dos dedos para mover</span></div>`;
  const exporta = `<div class="v3d-exporta"><button class="boton chico principal" type="button" data-v3d-exporta="stl">Descargar STL</button>
    <button class="boton chico" type="button" data-v3d-exporta="obj">Descargar OBJ</button>
    <span class="nota">En mm, con las capas visibles. Cada pieza es un sólido cerrado: se abre en SolidWorks, Inventor, Fusion, FreeCAD o AutoCAD. El OBJ trae un objeto por pieza.</span></div>`;
  const avisos = M.avisos.length ? `<section class="alerta"><h3>Choques en el modelo</h3><ul class="errores">${M.avisos.map((a) => `<li>${esc(a)}</li>`).join("")}</ul></section>` : "";
  const m = M.medidas, n = m.nucleo, t = m.tanque, igual = Math.abs(n.peso_modelo - n.peso_calculado) <= 1e-6 * n.peso_calculado;
  const nucleo = lista([["Largo x alto", `${mm(n.largo)} x ${mm(n.alto)} mm`], ["Profundidad (Σ espesores)", `${F.n(n.profundidad)} mm`],
    ["Volumen de chapas", `${F.miles(n.volumen_l, 1)} L`], ["Peso del modelo (x 7650 kg/m³)", `${F.miles(n.peso_modelo, 1)} kg`, true],
    ["Peso del cálculo", `${F.miles(n.peso_calculado, 1)} kg ${igual ? "✓" : "✗"}`], ["Radio de la esquina más alejada", `${F.miles(n.r_esquina, 1)} mm`]]);
  const tanque = lista([["Largo x ancho x alto (interior)", `${mm(t.largo)} x ${mm(t.ancho)} x ${mm(t.alto)} mm`],
    ["Volumen interior", `${F.miles(t.volumen_interior_l)} L`], ["Aceite (interior − parte activa)", `${F.miles(t.aceite_l)} L`, true]]);
  const holguras = `<div class="pares v3d-holguras">${HOLGURAS_3D.map(([k, rot, sub]) =>
    `<label for="v3t-${k}">${rot}<small>${sub}</small></label><input class="campo" id="v3t-${k}" data-v3t="${k}" inputmode="decimal" autocomplete="off" value="${F.g(V3.tanque[k])}">`).join("")}</div>`;
  const filasDev = m.devanados.map((w) => `<tr><td>${esc(w.nombre)}</td><td>${F.miles(w.d_int, 1)}</td><td>${F.miles(w.d_ext, 1)}</td><td>${F.miles(w.alto, 1)}</td>
    <td>${w.secciones}</td><td>${w.canales}</td><td${w.al_yugo < 0 ? ' class="no"' : ""}>${F.miles(w.al_yugo, 1)}</td></tr>`).join("");
  const tablaDev = `<div class="tabla"><table class="corte"><thead><tr><th>Devanado</th><th>Ø int.</th><th>Ø ext.</th><th>Alto</th><th>Bobinas</th><th>Canales int.</th><th>Al yugo (c/lado)</th></tr></thead>
    <tbody>${filasDev}</tbody></table></div>` +
    (m.barreras.length ? `<p class="nota-tabla">Barreras: ${m.barreras.map((b) => `${esc(b.entre)}: Ø ${F.miles(2 * b.r, 1)} mm, ${F.g(b.espesor)} mm de espesor, ${F.miles(b.alto, 0)} mm de alto`).join(" · ")}.</p>` : "");
  const como = `<ul class="v3d-como">
    <li><b>Núcleo:</b> un marco de chapas por escalón, el mismo con que se calcula su peso: C = 2·De + a, A = Hc + a₁ + a, ventanas (De − a) x (Hc + a₁ − a) y las 4 esquinas cortadas g. El escalón 1 va al centro y cada uno de los siguientes, mitad a cada lado. Su volumen x 7650 kg/m³ da el peso del cálculo.</li>
    <li><b>Devanados:</b> tubos con los Ø interior y exterior y la altura del montaje, centrados en la ventana. Los canales internos se reparten parejos a lo largo del radial (supuesto de dibujo); la galleta son 2 bobinas separadas 20 mm.</li>
    <li><b>Aislamiento:</b> barrera al centro del canal entre devanados (con el largo extra del tubo rígido), tubo núcleo–bobina, tubo enrollado y 8 calzas por extremo hasta el yugo (de dibujo).</li>
    <li><b>Tanque:</b> estimado con las holguras de al lado; no sale de un cálculo térmico (sin radiadores ni accesorios).</li>
    <li><b>Verificado:</b> <code>verificacion/prueba_3d.js</code> comprueba que cada pieza sea un sólido cerrado y que medidas, volúmenes y peso coincidan con el cálculo, también en las alternativas de la búsqueda.</li></ul>`;
  return [
    `<p class="encabezado">Modelo 3D de <b>${esc(f.titulo.toLowerCase())}</b>, generado con el cálculo: núcleo por escalones, devanados con sus canales, aislamiento mayor y un tanque estimado · <b>${F.miles(m.triangulos)}</b> triángulos.</p>`,
    avisos,
    `<section class="v3d">${barra}${lienzo}${capas}${exporta}</section>`,
    bloque("Devanados en el modelo (mm)", tablaDev),
    `<div class="dos">${bloque("Núcleo", nucleo)}${bloque("Tanque (estimado)", tanque + holguras)}</div>`,
    bloque("Cómo se genera", como),
  ].join("");
}

// ---------- la escena (three.js) ----------
// slider del corte: el rango es el del modelo en ese eje
function controlCorte3d() {
  const s = $("v3d-corte-pos"), o = $("v3d-corte-txt"), ax = V3.corte;
  if (!s || !V3.M) return;
  for (const b of document.querySelectorAll("[data-v3d-corte]")) b.setAttribute("aria-pressed", String(b.dataset.v3dCorte === ax));
  s.hidden = o.hidden = !ax;
  if (!ax) return;
  const lo = Math.floor(V3.M.caja[ax][0]), hi = Math.ceil(V3.M.caja[ax][1]);
  V3.cortePos[ax] = Math.min(Math.max(V3.cortePos[ax], lo), hi);
  s.min = lo; s.max = hi; s.value = V3.cortePos[ax];
  o.textContent = `${ax} = ${V3.cortePos[ax]} mm`;
}
const E3 = { T: null, OC: null, promesa: null, fallo: "", renderer: null, scene: null, camera: null, controls: null, plano: null, ray: null,
  raiz: null, capas: {}, pick: [], corteObjs: [], tapas: [], mat: new Map(), linea: null, lineaTanque: null, M: null, host: null, ro: null,
  encuadrado: false, pendiente: false, ultimoPuntero: null };
function cargarTres() {
  if (!E3.promesa) E3.promesa = Promise.all(MODULOS_3D.map((m) => import(m))).then(([T, C]) => { E3.T = T; E3.OC = C.OrbitControls; E3.fallo = ""; })
    .catch((ex) => { E3.promesa = null; E3.fallo = "No se pudo cargar three.js: la vista 3D lo trae de internet."; throw ex; });
  return E3.promesa;
}
function iniciar3d() {
  const T = E3.T, r = new T.WebGLRenderer({ antialias: true, stencil: true });
  r.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  r.localClippingEnabled = true;
  r.domElement.setAttribute("role", "img");
  r.domElement.setAttribute("aria-label", "Modelo 3D del transformador: arrastra para girar");
  E3.renderer = r;
  E3.scene = new T.Scene();
  E3.camera = new T.PerspectiveCamera(32, 1.6, 10, 100000);
  E3.camera.up.set(0, 0, 1);                               // z vertical
  E3.scene.add(E3.camera);
  E3.scene.add(new T.AmbientLight(0xffffff, 0.75));
  const l1 = new T.DirectionalLight(0xffffff, 2.1), l2 = new T.DirectionalLight(0xffffff, 0.55);
  l1.position.set(-1500, 1800, 0); l2.position.set(1800, -900, 0);   // van con la cámara: la luz siempre viene de arriba a la izquierda
  E3.camera.add(l1, l2);
  E3.controls = new E3.OC(E3.camera, r.domElement);
  E3.controls.zoomToCursor = true;
  E3.controls.addEventListener("change", pintar3d);
  E3.plano = new T.Plane(new T.Vector3(0, 1, 0), 1e7);     // deja y ≥ −constante
  E3.ray = new T.Raycaster();
  E3.linea = new T.LineBasicMaterial({ transparent: true, opacity: 0.28, clippingPlanes: [E3.plano] });
  E3.lineaTanque = new T.LineBasicMaterial({ transparent: true, opacity: 0.45, clippingPlanes: [E3.plano] });
  r.domElement.addEventListener("pointermove", (ev) => { E3.ultimoPuntero = ev; if (!E3.esperaPick) { E3.esperaPick = true; requestAnimationFrame(senalar3d); } });
  r.domElement.addEventListener("pointerleave", () => { E3.ultimoPuntero = null; const e = $("v3d-etiqueta"); if (e) e.hidden = true; });
  E3.ro = new ResizeObserver(tamano3d);
  new MutationObserver(() => { colores3d(); pintar3d(); }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-tema"] });
}
function material3d(p) {
  const T = E3.T, k = `${p.grupo}|${p.color}|${!!p.transparente}`;
  if (!E3.mat.has(k)) {
    const base = { color: new T.Color(p.color), clippingPlanes: [E3.plano] };
    E3.mat.set(k, p.grupo === "tanque"
      ? new T.MeshStandardMaterial({ ...base, transparent: true, opacity: 0.09, depthWrite: false, side: T.DoubleSide, roughness: 0.55, metalness: 0.15 })
      : p.transparente ? new T.MeshStandardMaterial({ ...base, transparent: true, opacity: 0.4, depthWrite: false, roughness: 0.8, metalness: 0 })
      : new T.MeshStandardMaterial({ ...base, roughness: p.grupo === "aislamiento" ? 0.85 : 0.42, metalness: p.grupo === "devanados" ? 0.35 : p.grupo === "nucleo" ? 0.22 : 0 }));
  }
  return E3.mat.get(k);
}
// Corte con tapas: el stencil cuenta cuántas veces se entra y se sale de cada sólido detrás del plano; donde queda
// dentro de uno se pinta la tapa, del color de la pieza (como el ejemplo «clipping stencil» de three.js)
function stencil3d(geo, orden) {
  const T = E3.T, g = new T.Group();
  for (const [lado, op] of [[T.BackSide, T.IncrementWrapStencilOp], [T.FrontSide, T.DecrementWrapStencilOp]]) {
    const mat = new T.MeshBasicMaterial({ side: lado, depthWrite: false, depthTest: false, colorWrite: false, stencilWrite: true,
      stencilFunc: T.AlwaysStencilFunc, stencilFail: op, stencilZFail: op, stencilZPass: op, clippingPlanes: [E3.plano] });
    const malla = new T.Mesh(geo, mat);
    malla.renderOrder = orden; malla.userData.matPropio = true;
    g.add(malla);
  }
  return g;
}
function construir3d(M) {
  const T = E3.T;
  if (E3.raiz) {
    E3.scene.remove(E3.raiz);
    E3.raiz.traverse((o) => { if (o.geometry && o.geometry !== E3.geoTapa) o.geometry.dispose(); if (o.userData.matPropio) o.material.dispose(); });
    if (E3.geoTapa) E3.geoTapa.dispose();
  }
  const raiz = new T.Group(), porColor = new Map();
  E3.capas = {}; E3.pick = []; E3.corteObjs = []; E3.tapas = [];
  for (const [k] of CAPAS_3D) { E3.capas[k] = new T.Group(); raiz.add(E3.capas[k]); }
  for (const p of M.partes) {
    const geo = new T.BufferGeometry();
    geo.setAttribute("position", new T.BufferAttribute(new Float32Array(p.pos), 3));
    geo.setAttribute("normal", new T.BufferAttribute(new Float32Array(p.nor), 3));
    geo.computeBoundingSphere();
    const malla = new T.Mesh(geo, material3d(p)), bordes = new T.LineSegments(new T.EdgesGeometry(geo, 25), p.grupo === "tanque" ? E3.lineaTanque : E3.linea);
    malla.renderOrder = 20; bordes.renderOrder = 21; malla.userData.nombre = p.nombre;
    E3.capas[p.grupo].add(malla, bordes);
    if (p.grupo !== "tanque" && !p.transparente) E3.pick.push(malla);   // bajo el tubo enrollado se nombra el devanado
    if (!porColor.has(p.color)) porColor.set(p.color, { grupo: p.grupo, geos: [] });
    porColor.get(p.color).geos.push(geo);
  }
  const c = M.caja, lado = 2.4 * Math.max(c.x[1] - c.x[0], c.y[1] - c.y[0], c.z[1] - c.z[0]);
  E3.geoTapa = new T.PlaneGeometry(lado, lado);                         // plano x-y; se gira para el corte vertical
  E3.centro = [(c.x[0] + c.x[1]) / 2, (c.y[0] + c.y[1]) / 2, (c.z[0] + c.z[1]) / 2];
  let orden = 1;
  for (const [color, { grupo, geos }] of porColor) {
    for (const geo of geos) { const s = stencil3d(geo, orden); E3.capas[grupo].add(s); E3.corteObjs.push(s); }
    // polygonOffset: la tapa gana en profundidad a las caras que llegan justo hasta el plano de corte
    const mat = new T.MeshStandardMaterial({ color: new T.Color(color).multiplyScalar(0.82), roughness: 0.9, metalness: 0, side: T.DoubleSide,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
      stencilWrite: true, stencilRef: 0, stencilFunc: T.NotEqualStencilFunc, stencilFail: T.ReplaceStencilOp, stencilZFail: T.ReplaceStencilOp, stencilZPass: T.ReplaceStencilOp });
    const tapa = new T.Mesh(E3.geoTapa, mat);
    tapa.renderOrder = orden + 0.5; tapa.userData.matPropio = true;
    tapa.onAfterRender = (rend) => rend.clearStencil();
    E3.capas[grupo].add(tapa); E3.corteObjs.push(tapa); E3.tapas.push(tapa);
    orden++;
  }
  E3.raiz = raiz;
  E3.scene.add(raiz);
}
function aplicarCapas3d() { for (const [k] of CAPAS_3D) if (E3.capas[k]) E3.capas[k].visible = !!V3.capas[k]; }
function aplicarCorte3d() {
  if (!E3.plano) return;
  const ax = V3.corte, pos = ax ? V3.cortePos[ax] : 0, [cx, cy, cz] = E3.centro;
  if (!ax) E3.plano.set(new E3.T.Vector3(0, 1, 0), 1e7);                       // nada cortado
  else if (ax === "y") E3.plano.set(new E3.T.Vector3(0, 1, 0), -pos);         // deja y ≥ corte
  else E3.plano.set(new E3.T.Vector3(0, 0, -1), pos);                         // deja z ≤ corte
  for (const o of E3.corteObjs) o.visible = !!ax;
  for (const t of E3.tapas) {
    if (ax === "y") { t.rotation.set(Math.PI / 2, 0, 0); t.position.set(cx, pos, cz); }   // mirando al frente (−y)
    else { t.rotation.set(0, 0, 0); t.position.set(cx, cy, pos); }                         // mirando arriba (+z)
  }
}
function colores3d() {
  if (!E3.scene) return;
  const css = getComputedStyle(document.documentElement), v = (n, x) => css.getPropertyValue(n).trim() || x;
  E3.scene.background = new E3.T.Color(v("--campo", "#f5f7f9"));
  E3.linea.color.set(v("--fg", "#1b2127"));
  E3.lineaTanque.color.set(v("--fg-2", "#3c4651"));
}
function tamano3d() {
  const h = E3.host;
  if (!h || !E3.renderer || !h.isConnected) return;
  const w = h.clientWidth, alto = h.clientHeight;
  if (!w || !alto) return;
  E3.renderer.setSize(w, alto, false);
  E3.camera.aspect = w / alto;
  E3.camera.updateProjectionMatrix();
  pintar3d();
}
function pintar3d() {
  if (E3.pendiente || !E3.renderer) return;
  E3.pendiente = true;
  requestAnimationFrame(() => { E3.pendiente = false; if (E3.host && E3.host.isConnected) E3.renderer.render(E3.scene, E3.camera); });
}
function encuadrar3d(vista) {
  const T = E3.T, c = V3.M.caja, cam = E3.camera;
  const centro = new T.Vector3((c.x[0] + c.x[1]) / 2, (c.y[0] + c.y[1]) / 2, (c.z[0] + c.z[1]) / 2);
  const radio = 0.5 * Math.hypot(c.x[1] - c.x[0], c.y[1] - c.y[0], c.z[1] - c.z[0]);
  const fv = (cam.fov * Math.PI) / 180, fh = 2 * Math.atan(Math.tan(fv / 2) * cam.aspect);
  const dist = (radio / Math.sin(Math.min(fv, fh) / 2)) * 0.9, dir = new T.Vector3(...VISTAS_3D.find(([k]) => k === vista)[2]).normalize();
  cam.position.copy(centro).addScaledVector(dir, dist);
  cam.near = dist / 60; cam.far = dist * 20; cam.updateProjectionMatrix();
  E3.controls.target.copy(centro);
  E3.controls.update();
  pintar3d();
}
// nombre de la pieza bajo el puntero (las cortadas no cuentan)
function senalar3d() {
  E3.esperaPick = false;
  const ev = E3.ultimoPuntero, et = $("v3d-etiqueta");
  if (!ev || !et || !E3.renderer) return;
  const b = E3.renderer.domElement.getBoundingClientRect();
  E3.ray.setFromCamera(new E3.T.Vector2(((ev.clientX - b.left) / b.width) * 2 - 1, -((ev.clientY - b.top) / b.height) * 2 + 1), E3.camera);
  const ax = V3.corte, pos = ax ? V3.cortePos[ax] : 0;
  const hit = E3.ray.intersectObjects(E3.pick.filter((m) => m.parent.visible), false)
    .find((h) => !ax || (ax === "y" ? h.point.y >= pos - 0.5 : h.point.z <= pos + 0.5));
  et.hidden = !hit;
  if (hit) et.textContent = hit.object.userData.nombre;
}
function conectar3d() {
  const host = $("v3d-lienzo"), msg = $("v3d-msg");
  if (!host || !V3.M) return;
  controlCorte3d();
  if (E3.fallo && !E3.promesa) { msg.textContent = `${E3.fallo} Las descargas STL y OBJ funcionan igual.`; return; }
  if (!E3.T) {
    cargarTres().then(() => conectar3d(), () => { const m = $("v3d-msg"); if (m) m.textContent = `${E3.fallo} Las descargas STL y OBJ funcionan igual.`; });
    return;
  }
  try {
    if (!E3.renderer) iniciar3d();
    E3.host = host;
    host.prepend(E3.renderer.domElement);
    msg.hidden = true;
    E3.ro.disconnect(); E3.ro.observe(host);
    colores3d();
    if (E3.M !== V3.M) { construir3d(V3.M); E3.M = V3.M; }
    aplicarCapas3d(); aplicarCorte3d();
    tamano3d();
    if (!E3.encuadrado) { encuadrar3d(V3.vista); E3.encuadrado = true; }
  } catch (ex) {
    msg.hidden = false;
    msg.textContent = `No se pudo mostrar la vista 3D en este navegador (${ex.message}). Las descargas STL y OBJ funcionan igual.`;
  }
}
function descargar3d(tipo) {
  const M = V3.M;
  if (!M) return;
  const partes = M.partes.filter((p) => V3.capas[p.grupo]);
  if (!partes.length) { avisar("No hay capas visibles para exportar."); return; }
  const blob = new Blob([tipo === "stl" ? aSTL(partes) : aOBJ(partes)], { type: tipo === "stl" ? "model/stl" : "model/obj" });
  const a = document.createElement("a"), nombre = String(V3.f.d.codigo || "transformador").replace(/[^\w.-]+/g, "_");
  a.href = URL.createObjectURL(blob);
  a.download = `${nombre}-3d${V3.f.sufijo}.${tipo}`;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  avisar(`${tipo.toUpperCase()} listo: ${partes.length} piezas, ${F.miles(partes.reduce((s, p) => s + p.pos.length / 9, 0))} triángulos, en mm.`);
}

// --- eventos de la pestaña (no cambian el diseño) ---
document.addEventListener("click", (ev) => {
  const t = ev.target.closest && ev.target.closest("[data-v3d-vista], [data-v3d-corte], [data-v3d-exporta], button.ver3d");
  if (!t) return;
  if (t.dataset.v3dCorte !== undefined) {
    V3.corte = t.dataset.v3dCorte; guardar3d();
    controlCorte3d(); aplicarCorte3d(); pintar3d();
  } else if (t.dataset.v3dVista) {
    V3.vista = t.dataset.v3dVista;
    for (const b of document.querySelectorAll("[data-v3d-vista]")) b.setAttribute("aria-pressed", String(b === t));
    if (E3.renderer && V3.M) encuadrar3d(V3.vista);
  } else if (t.dataset.v3dExporta) descargar3d(t.dataset.v3dExporta);
  else {                                              // «3D» en la tabla de la búsqueda
    V3.fuente = Number(t.dataset.alt);
    pestana = "3d"; ponerLocal(CLAVE_PESTANA, pestana); pintarResultado();
    $(`panel-${ULTIMO_PASO}`).scrollTop = 0;
  }
});
document.addEventListener("input", (ev) => {
  const el = ev.target;
  if (el.id === "v3d-corte-pos") {
    V3.cortePos[V3.corte] = Number(el.value);
    $("v3d-corte-txt").textContent = `${V3.corte} = ${el.value} mm`;
    aplicarCorte3d(); pintar3d();
  }
});
document.addEventListener("change", (ev) => {
  const el = ev.target;
  if (el.id === "v3d-fuente") { V3.fuente = Number(el.value); pintarResultado(); }
  else if (el.dataset && el.dataset.v3dCapa) {
    V3.capas[el.dataset.v3dCapa] = el.checked; guardar3d();
    aplicarCapas3d(); pintar3d();
  } else if (el.dataset && el.dataset.v3t) {
    const v = parseFloat(String(el.value).trim().replace(",", "."));
    if (isFinite(v) && v >= 0) { V3.tanque[el.dataset.v3t] = v; guardar3d(); }
    pintarResultado();
  }
});
