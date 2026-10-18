"""Catálogo de condiciones de DISEÑO_DE_TRANSFORMADOR (Python) y de la página web (calc.js / optimiza.js).

Cada regla dice: en qué paso está, qué tipo de condición es, de dónde sale (origen), qué dato la provoca
(causa), qué hace el programa (efecto), qué hacer (arreglo), en qué función está en cada lenguaje
(py / js), un texto que la identifica en el código (huella) y un caso de prueba que la dispara.

Tipos
  falta     dato sin fuente vacío: no calcula y marca el campo
  bloquea   dato no válido: no calcula y lo pone en «Revisa estos datos»
  limite    se calcula y el semáforo lo marca (cumple / cerca / procede / no cumple)
  aviso     se calcula y muestra un «Ojo»
  decide    condición que elige una fórmula o un valor
  corrige   el programa cambia el dato sin avisar
  descarta  la búsqueda deja fuera una combinación
  hueco     falta una condición: el programa calcula sin avisar con un dato que no tiene sentido

Revisión
  verificado  el caso la dispara igual en Python y en la web y la causa es la esperada
  dudoso      funciona como está escrito, pero la regla misma está por confirmar contigo
  hueco       falta una verificación
  sin-uso     no se puede disparar desde el diseño (código que no se usa)

Caso: lista de [ruta, valor] sobre base_mapa.json (un diseño que cumple todo).
Espera:
  {"error": texto}                     un mensaje de «Revisa estos datos» que contiene el texto
  {"falta": texto}                     un dato faltante cuyo rótulo contiene el texto
  {"limite": clave, "estado": e}       el límite con esa clave queda en ese estado
  {"valor": ruta, "op": op, "v": x}    op: == != < > len igual_base distinto_base mayor_base
  {"paso": n, "estado": e}             la barra de pasos marca el paso n con ese estado
  {"busqueda": {...}, "error"|"aviso": texto}
  "sin_error": True                    además, el programa no muestra ningún error (para los huecos)
"""
import json
import pathlib

ORIGENES = {
    "NUC": "Hoja de cálculo de núcleo",
    "DEV": "Hoja de cálculo de devanado",
    "DE": "Hoja de datos de entrada",
    "ESP": "Especificaciones del cliente",
    "VCC": "Hoja de cálculo de Vcc",
    "PER": "Curva de pérdidas de la chapa",
    "ESF": "Hoja de esfuerzos",
    "PES": "Cálculo de peso de devanados",
    "TU": "Criterio del diseñador",
    "TC": "Condiciones del diseñador (J y B)",
    "REF": "Diseño de referencia",
    "SUP": "Supuesto por validar",
    "PRG": "Control del programa",
    "FIS": "Física del transformador",
    "SF": "Sin fuente: se digita",
}
PASOS = {1: "Datos del cliente", 2: "Núcleo", 3: "Devanados", 4: "Distancias", 5: "Resultados", 6: "Búsqueda por Vcc"}
COMPUERTAS = {
    "c1": "¿Falta algún dato sin fuente?",
    "c2": "¿El núcleo es válido?",
    "c3": "Cálculo eléctrico, pérdidas y distancias",
    "c4": "Devanados dentro de la ventana",
    "c5": "Montaje, Vcc y esfuerzos",
    "c6": "Semáforo de límites",
    "c7": "Barra de pasos",
    "c8": "Búsqueda por Vcc",
}

REGLAS = []


def R(id, paso, tipo, titulo, condicion, origen, causa, efecto, arreglo, py, js, huella, caso=None, espera=None,
      revision="verificado", nota="", umbral="", compuerta=None):
    REGLAS.append(dict(id=id, paso=paso, tipo=tipo, titulo=titulo, condicion=condicion, umbral=umbral, origen=origen,
                       causa=causa, efecto=efecto, arreglo=arreglo, py=py, js=js, huella=huella, caso=caso,
                       espera=espera, revision=revision, nota=nota, compuerta=compuerta))


# =====================================================================
# Compuerta 1 · datos sin fuente vacíos (faltantes)
# =====================================================================
R("F-01", 1, "falta", "Dato general vacío",
  "Algún dato general sin fuente está vacío (frecuencia, reparto, pasos, % variación, tap, Dn, De, Hc, g, K, B, "
  "factor de apilamiento, espiras de referencia, W/kg, factor de construcción, tubo, entre fases, T°, barrera, "
  "tubo rígido, tubo núcleo–bobina).", "TU",
  "El campo quedó en blanco; los que no tienen fuente empiezan en blanco a propósito.",
  "No calcula. La barra de pasos marca «Faltan N datos» en el paso donde se digita y el campo se resalta.",
  "Digita el dato.", "faltantes / faltantes_detalle", "faltantes / faltantesDetalle",
  {"py": "Datos generales: ", "js": "Datos generales: "}, [["fa", None]], {"falta": "Factor de apilamiento"},
  compuerta="c1")
R("F-02", 1, "falta", "Potencia de un devanado vacía",
  "La potencia de un devanado está vacía.", "TU",
  "Se borró la potencia (un devanado sin uso lleva 0, no vacío).",
  "No calcula; pide la potencia en el paso 1.", "Pon la potencia o 0 si el devanado no se usa.",
  "faltantes_detalle", "faltantesDetalle", "}: potencia.",
  [["dev.II.kva", None]], {"falta": "Devanado II · potencia"}, compuerta="c1")
R("F-03", 3, "falta", "Dato de un devanado con potencia vacío",
  "Un devanado con potencia tiene vacío un dato que el cálculo usa (tipo, papel entre capas, canales, "
  "transposiciones, canal interior, yugo, relleno, prueba industrial, etc.).", "TU",
  "El dato no tiene fuente y no se digitó.", "No calcula; lo pide en el paso donde se digita (1, 3 o 4).",
  "Digita el dato.", "_pedir_devanado / faltantes_detalle", "pedirDevanado / faltantesDetalle",
  {"py": "falta.append(f\"{NOMBRES[k]}: \" + \", \".join(vacios)", "js": "falta.push(`${NOMBRES[k]}: ${vacios.join(\", \")}.`)"}, [["dev.I.transp", None]],
  {"falta": "Devanado I · transposiciones"}, compuerta="c1")
R("F-04", 3, "falta", "Platina pide papel",
  "Si el calibre es platina, el papel de platina es obligatorio; con alambre no se pide.", "DEV",
  "Platina elegida y papel vacío.", "No calcula; pide «papel de platina».", "Digita el papel de la platina.",
  "_pedir_devanado", "pedirDevanado", {"py": "pedir.append(\"papel\")", "js": "pedir.push(\"papel\")"},
  [["dev.II.papel", None]], {"falta": "Devanado II · papel de platina"}, compuerta="c1")
R("F-05", 3, "falta", "Canales internos piden medida",
  "Con 1 o más canales internos, la medida del canal es obligatoria.", "PRG",
  "N° de canales > 0 y medida vacía.", "No calcula; pide «medida de los canales internos».", "Digita la medida.",
  "_pedir_devanado", "pedirDevanado", {"py": "pedir.append(\"canal_mm\")", "js": "pedir.push(\"canal_mm\")"},
  [["dev.I.n_canales", 2], ["dev.I.canal_mm", None]], {"falta": "medida de los canales internos"}, compuerta="c1")
R("F-06", 3, "falta", "Modo de capas pide su dato",
  "Con «N° de capas» se pide el N° de capas; con «Espiras por capa», las espiras por capa; con «Ajustar a la "
  "ventana», ninguno.", "PRG", "Modo a mano y su dato vacío.", "No calcula; pide el dato del modo.",
  "Digita el dato o vuelve a «Ajustar a la ventana».", "_pedir_devanado", "pedirDevanado",
  {"py": "pedir.append(\"capas\")", "js": "pedir.push(\"capas\")"},
  [["dev.I.modo", "capas"], ["dev.I.capas", None]], {"falta": "Devanado I · N° de capas"}, compuerta="c1")

# =====================================================================
# Compuerta 2 · núcleo
# =====================================================================
R("N-01", 2, "bloquea", "Medidas del núcleo mayores que 0", "Dn, De y Hc deben ser mayores que 0 (K = 1 es fijo).", "PRG",
  "Algún dato del núcleo en 0 o negativo.", "No calcula; el paso 2 queda en «Revisar».", "Corrige el dato del núcleo.",
  "validar_nucleo", "validarNucleo", "Núcleo: Dn, De y Hc deben ser mayores que 0.",
  [["hc", 0]], {"error": "Dn, De y Hc deben ser mayores que 0"}, compuerta="c2")
R("N-02", 2, "bloquea", "Al menos un escalón", "Debe haber al menos un ancho de escalón mayor que 0.", "PRG",
  "Todos los anchos en 0.", "No calcula.", "Digita los anchos de escalón.", "validar_nucleo", "validarNucleo",
  "Núcleo: ingresa al menos un ancho de escalón.", [["anchos", [0] * 10]], {"error": "al menos un ancho"},
  compuerta="c2")
R("N-03", 2, "bloquea", "Escalones menores que Dn", "Ningún ancho de escalón puede ser igual o mayor que Dn.",
  "NUC", "Un ancho ≥ Dn.", "No calcula.", "Achica el escalón o aumenta Dn.", "validar_nucleo", "validarNucleo",
  "Núcleo: los anchos de escalón deben ser menores que el diámetro Dn.",
  [["anchos", [260, 230, 210, 190, 170, 130, 110, 95, 0, 0]]], {"error": "menores que el diámetro Dn"},
  compuerta="c2")
R("N-04", 2, "bloquea", "Factor de apilamiento entre 0 y 1", "0 < factor de apilamiento ≤ 1.", "PRG",
  "Factor 0, negativo o mayor que 1 (por ejemplo 96 en vez de 0.96).", "No calcula.", "Escríbelo como fracción.",
  "calcular_datos", "calcularTodo", "Núcleo: el factor de apilamiento debe estar entre 0 y 1.",
  [["fa", 96]], {"error": "factor de apilamiento"}, compuerta="c2")
R("N-05", 2, "bloquea", "De mayor que Dn",
  "La distancia entre ejes De debe ser mayor que Dn (De va de centro a centro de columnas).", "PRG",
  "De ≤ Dn: suele ser De digitado como otra medida.", "No calcula.", "Corrige De.", "calcular_datos (MSG_DE)",
  "calcularTodo", "la distancia entre ejes De debe ser mayor que el diámetro Dn", [["de", 250]],
  {"error": "De debe ser mayor que el diámetro Dn"}, compuerta="c2")
R("N-06", 2, "decide", "Chapas por escalón",
  "Chapas acumuladas = redondeo a decenas de (Dn·K·√(1 − (ancho/Dn)²) / 0,27); las del escalón = acumuladas − "
  "anteriores; si sale negativo queda en 0.", "NUC", "Fórmula de la hoja de corte.",
  "Cada escalón lleva un múltiplo de 10 chapas; el peso es área x espesor x 7650 kg/m³.", "—",
  "calcular_nucleo", "calcularNucleo", {"py": "chapas_acum_teoricas = int(round(", "js": "const acum = Math.trunc("},
  revision="verificado", nota="Comparado contra la hoja de núcleo: 6 núcleos idénticos.")
R("H-01", 2, "hueco", "Anchos de escalón desordenados",
  "No se verifica que los anchos vayan de mayor a menor.", "PRG",
  "Un escalón más ancho que el anterior (por ejemplo 230, 250, 210…).",
  "Calcula sin avisar: ese escalón queda con 0 chapas y el área del yugo usa el primer ancho como el mayor.",
  "Agregar: «Núcleo: los anchos de escalón deben ir de mayor a menor».", "calcular_nucleo", "calcularNucleo",
  {"py": "if chapas_esc < 0:", "js": "if (chapas < 0) chapas = 0"},
  [["anchos", [230, 250, 210, 190, 170, 130, 110, 95, 0, 0]]], {"valor": "nuc.escalones.1.chapas", "op": "==", "v": 0, "sin_error": True},
  revision="hueco", compuerta="c2")
R("H-02", 2, "hueco", "Traslape g negativo", "No se verifica el traslape g.", "PRG", "g negativo.",
  "Calcula sin avisar con un peso de núcleo distinto.", "Agregar: g ≥ 0.", "validar_nucleo", "validarNucleo",
  {"py": "def validar_nucleo", "js": "function validarNucleo"}, [["g", -50]],
  {"valor": "nuc.peso", "op": "distinto_base", "sin_error": True}, revision="hueco", compuerta="c2")

# =====================================================================
# Compuerta 3 · cálculo eléctrico (datos del cliente, paso 1) y pérdidas (paso 2)
# =====================================================================
R("E-01", 1, "bloquea", "Sin negativos en potencias y tensiones", "Potencias y tensiones ≥ 0.", "PRG",
  "Un valor negativo.", "No calcula.", "Corrige el signo.", "calcular_electrico", "calcularElectrico",
  ": potencias y tensiones no pueden ser negativas.", [["dev.II.volt2", -230]], {"error": "no pueden ser negativas"},
  compuerta="c3")
R("E-02", 1, "bloquea", "Potencia sin tensión", "Un devanado con potencia necesita su primera tensión.", "PRG",
  "Potencia > 0 y tensión 0.", "No calcula.", "Digita la tensión o pon la potencia en 0.", "calcular_electrico",
  "calcularElectrico", ": tiene potencia pero le falta la primera tensión.", [["dev.II.volt", 0]],
  {"error": "le falta la primera tensión"}, compuerta="c3")
R("E-03", 1, "bloquea", "Devanado I obligatorio", "El Devanado I (principal, lleva los taps) debe tener potencia y tensión.",
  "TU", "Potencia del Devanado I en 0.", "No calcula.", "El primario va en el Devanado I.", "calcular_electrico",
  "calcularElectrico", "(principal): ingresa su potencia y su tensión.", [["dev.I.kva", 0]],
  {"error": "Falta el Devanado I"}, compuerta="c3")
R("E-04", 1, "bloquea", "Al menos 2 devanados", "Debe haber al menos 2 devanados con potencia y tensión.", "FIS",
  "Solo un devanado con potencia.", "No calcula.", "Activa el secundario.", "calcular_electrico", "calcularElectrico",
  "Se necesitan al menos 2 devanados con potencia y tensión.", [["dev.II.kva", 0]], {"error": "al menos 2 devanados"},
  compuerta="c3")
R("E-05", 1, "bloquea", "Frecuencia y B mayores que 0", "Frecuencia, inducción objetivo y sección neta > 0.", "PRG",
  "Frecuencia o B en 0.", "No calcula.", "Corrige el dato.", "calcular_electrico", "calcularElectrico",
  "Frecuencia, inducción objetivo y sección del núcleo deben ser mayores que 0.", [["frec", 0]],
  {"error": "Frecuencia, inducción objetivo"}, compuerta="c3")
R("E-06", 1, "bloquea", "Tap nominal dentro de los pasos", "1 ≤ tap nominal ≤ N° de pasos.", "PRG",
  "Tap nominal mayor que los pasos.", "No calcula.", "Corrige el tap o los pasos.", "calcular_electrico",
  "calcularElectrico", "debe estar entre 1 y el N° de pasos", [["tap", 7]], {"error": "posición nominal (7)"},
  compuerta="c3")
R("E-07", 1, "bloquea", "% de variación válido",
  "% de variación ≥ 0 y la toma más baja no llega a 0 V (variación x pasos bajo el nominal < 100).", "PRG",
  "Variación negativa o tan grande que la toma más baja queda en 0 V o menos.", "No calcula.", "Corrige el %.",
  "calcular_electrico", "calcularElectrico", "Tap: el % de variación no es válido.", [["variacion", 60]],
  {"error": "% de variación no es válido"}, compuerta="c3")
R("E-08", 1, "bloquea", "Reparto con números", "El reparto de carga debe tener al menos un número (100-0).", "ESP",
  "Reparto escrito sin números.", "No calcula.", "Escribe los porcentajes separados por guion.", "calcular_electrico",
  "calcularElectrico", "Reparto BT: escribe los porcentajes separados por guion", [["rep", "todo"]],
  {"error": "Reparto BT"}, compuerta="c3")
R("H-03", 1, "hueco", "Reparto que no suma 100 %",
  "No se verifica que el reparto sume 100 % ni que haya tantos números como secundarios.", "ESP",
  "Reparto «150» o «60-60».",
  "Calcula sin avisar: el primario carga la suma (150 % = 1500 kVA) y las pérdidas I²R salen con esa carga.",
  "Agregar: el reparto debe sumar 100 %; o avisar cuando no suma.", "calcular_electrico", "calcularElectrico",
  {"py": "at[\"reparto\"] = sum", "js": "at.reparto = secundarios.reduce"}, [["rep", "150"]],
  {"valor": "elec.dev.I.kva_carga", "op": "==", "v": 1500, "sin_error": True}, revision="hueco", compuerta="c3")
R("E-10", 1, "decide", "Estrella o triángulo",
  "Y y YN: V fase = V línea / √3 e I fase = I línea. D: V fase = V línea e I fase = I línea / √3.", "FIS",
  "Grupo de cada tensión.", "Cambia espiras y corrientes.", "—", "tension_fase / corriente_fase",
  "tensionFase / corrienteFase", {"py": "def es_estrella", "js": "const esEstrella"},
  [["dev.I.conex", "D"]], {"valor": "elec.dev.I.v_fase", "op": "==", "v": 22900})
R("E-11", 1, "decide", "Tensión de referencia",
  "Las espiras de referencia salen de la MENOR tensión de fase de toda la tabla (incluidas las 2ª tensiones).",
  "DE", "La menor tensión de fase.", "Esa tensión fija el V/espira; las demás se redondean.", "—",
  "calcular_electrico", "calcularElectrico", {"py": "# Referencia: la menor tensión de fase", "js": "// Referencia: la menor tensión de fase"},
  [["dev.I.volt2", 100]], {"valor": "elec.ref", "op": "==", "v": "I"})
R("E-12", 2, "decide", "Espiras de referencia de la B objetivo",
  "N = REDONDEO.MAS(V fase de referencia / (4,44·f·B objetivo·Sn)): así la B real nunca pasa la objetivo. Ya no se dan a mano.", "DE",
  "B objetivo y núcleo.", "Fija el V/espira y todas las espiras.", "Para cambiar N, cambia la B objetivo o el núcleo.",
  "calcular_electrico", "calcularElectrico", {"py": "int(redondeo_mas(n_teorico, 0))", "js": "Math.trunc(redondeoMas(nTeorico, 0))"},
  [["bobj", 1.4]], {"valor": "elec.n_ref", "op": "mayor_base"},
  nota="Antes se podían dar a mano en «Opciones avanzadas» del núcleo; esa opción se quitó (H-04 ya no aplica).")
R("E-13", 1, "decide", "Segunda tensión",
  "Si la 2ª tensión > 0 se calcula como derivación; si la 2ª potencia es 0 usa la 1ª; si el 2º grupo falta usa el 1º. "
  "El devanado se arma con las espiras de la que necesita más.", "DE", "2ª tensión en 0.",
  "Con 0 el devanado tiene una sola tensión.", "—", "calcular_electrico", "calcularElectrico",
  {"py": "if s.get(\"volt2\", 0.0) > 0:", "js": "if ((s.volt2 || 0) > 0)"},
  [["dev.II.volt2", 0]], {"valor": "elec.dev.II.tensiones", "op": "len", "v": 1})
R("E-14", 1, "decide", "Taps en el Devanado I",
  "Toma p: V = V nominal x (1 + (tap nominal − p) x % / 100); la nominal usa las espiras nominales, las demás se redondean. "
  "El devanado se arma con la toma de más espiras.", "DE", "Pasos, % de variación y tap nominal.",
  "Fija las espiras máximas del Devanado I.", "—", "calcular_electrico", "calcularElectrico",
  {"py": "factor = 1.0 + (tap_nom - p) * variacion / 100.0", "js": "const factor = 1 + (tapNom - p) * variacion / 100"},
  [["pasos", 1], ["tap", 1]], {"valor": "elec.dev.I.n_max", "op": "==", "v": "$elec.dev.I.n_nom"})
R("E-15", 1, "decide", "Reparto de carga entre secundarios",
  "Cada secundario, en orden, toma su % del reparto; si faltan números, 0 %. El primario carga la suma.", "ESP",
  "Texto del reparto.", "Fija las corrientes de carga para las pérdidas I²R.", "—", "calcular_electrico",
  "calcularElectrico", {"py": "pct = repartos[idx] if idx < len(repartos) else 0", "js": "const pct = idx < repartos.length ? repartos[idx] : 0"},
  [["rep", "50-50"]], {"valor": "elec.dev.II.reparto", "op": "==", "v": 50})
R("V-01", 2, "aviso", "Inducción real frente a la objetivo",
  "Verificación: B real ≤ B objetivo. Siempre cumple: las espiras salen de la B objetivo con REDONDEO.MAS.", "TC",
  "No se puede dar desde que las espiras no se dan a mano.", "Se lista en las verificaciones de la hoja.",
  "Se puede quitar de las verificaciones.", "verificaciones", "verificaciones", revision="sin-uso", huella=
  {"py": "Inducción real {b:.3f} T frente al objetivo", "js": "Inducción real ${b.toFixed(3)} T frente al objetivo"})
R("P-01", 2, "bloquea", "Factor de construcción mayor que 0",
  "Factor de construcción > 0.", "PER", "Factor de construcción 0.", "No calcula.",
  "Pon 1 si no hay factor.", "calcular_datos", "calcularTodo", "Pérdidas en el núcleo: el factor de construcción debe ser mayor que 0.",
  [["fconst", 0]], {"error": "factor de construcción debe ser mayor que 0"}, compuerta="c3")
R("P-02", 2, "decide", "Pfe de la tabla", "Pfe sale siempre de la regresión cuadrática de la chapa M4 0.27 mm (ya no hay W/kg a mano).",
  "PER", "Siempre.", "P0 = Pfe x peso x factor.", "—", "calcular_datos / calcular_vacio", "calcularTodo / calcularVacio",
  {"py": "calcular_vacio(nuc, elec, 0.0, d[\"fconst\"])", "js": "calcularVacio(nuc, elec, 0, d.fconst)"},
  nota="Antes se podía dar a mano en «Opciones avanzadas» del núcleo; esa opción se quitó.")
R("P-03", 2, "decide", "B para leer las pérdidas", "Las pérdidas se leen con B real + 0,099 T.", "PER",
  "Siempre.", "Pfe sale de la curva con esa B.", "—", "calcular_vacio", "calcularVacio",
  {"py": "AUMENTO_B_PERDIDAS = 0.099", "js": "const AUMENTO_B_PERDIDAS = 0.099"})
R("P-04", 2, "decide", "Frecuencia de las pérdidas", "50 y 60 Hz usan su curva; otra frecuencia: Pfe = a·f + b·f².", "PER",
  "Frecuencia distinta de 50 y 60.", "Interpola o extrapola entre las dos curvas.", "—", "perdidas_especificas",
  "perdidasEspecificas", {"py": "a = (3600.0 * p50 - 2500.0 * p60) / 30000.0", "js": "const a = (3600 * p50 - 2500 * p60) / 30000"},
  [["frec", 55]], {"valor": "vacio.pfe", "op": "distinto_base"})
R("A-01", 2, "aviso", "B fuera de la tabla de pérdidas", "B + 0,099 fuera de 0,5 a 1,9 T: Pfe es una extrapolación.",
  "PER", "Inducción muy alta o muy baja.", "Calcula y muestra «Ojo» en Pérdidas en el núcleo.",
  "Revisa B; el valor de Pfe es menos confiable.", "calcular_vacio / html_vacio", "calcularVacio / ui",
  {"py": "\"fuera_tabla\":", "js": "fuera_tabla:"}, [["bobj", 2.5]], {"valor": "vacio.fuera_tabla", "op": "==", "v": True})
R("A-02", 2, "aviso", "Frecuencia fuera de 50–60 Hz", "Frecuencia fuera de 50–60 Hz: Pfe = a·f + b·f² se extrapola.",
  "PER", "Frecuencia 70 Hz, por ejemplo.", "Calcula y muestra «Ojo».", "Revisa la frecuencia.", "calcular_vacio",
  "calcularVacio", {"py": "\"fuera_frec\":", "js": "fuera_frec:"}, [["frec", 70]],
  {"valor": "vacio.fuera_frec", "op": "==", "v": True})

# =====================================================================
# Compuerta 3 · distancias y esfuerzos (datos)
# =====================================================================
R("X-01", 4, "bloquea", "Entre fases y tubo sin negativos", "Entre fases mínimo ≥ 0 y tubo enrollado ≥ 0.", "PRG",
  "Valor negativo.", "No calcula.", "Corrige el signo.", "calcular_datos", "calcularTodo",
  "La distancia entre fases y el tubo enrollado no pueden ser negativos.", [["tubo", -1]],
  {"error": "entre fases y el tubo enrollado"}, compuerta="c3")
R("X-02", 4, "bloquea", "Barrera y tubos sin negativos", "Espesor de barrera, tubo rígido y tubo núcleo–bobina ≥ 0.",
  "PRG", "Valor negativo.", "No calcula.", "Corrige el signo.", "errores_esfuerzos", "calcularTodo",
  "Esfuerzos: la barrera, el tubo rígido y el tubo núcleo–bobina no pueden ser negativos.", [["tubo_rigido", -2]],
  {"error": "tubo rígido"}, compuerta="c3")
R("X-03", 4, "bloquea", "Barrera HAWAYANO o TUBO", "La barrera entre bobinas es HAWAYANO o TUBO.", "ESF",
  "Otro texto (solo pasa al cargar datos guardados; en pantalla es una lista).", "No calcula.", "Elige la barrera.",
  "errores_esfuerzos", "calcularTodo", "Esfuerzos: la barrera entre bobinas es HAWAYANO o TUBO.",
  [["barrera", "CARTON"]], {"error": "HAWAYANO o TUBO"}, compuerta="c3")
R("X-04", 4, "bloquea", "Relleno y prueba industrial sin negativos", "Relleno ≥ 0 y prueba industrial ≥ 0.", "PRG",
  "Valor negativo.", "No calcula.", "Corrige el signo.", "errores_esfuerzos", "calcularTodo",
  ": el relleno y la tensión de prueba industrial no pueden ser negativos.", [["dev.I.relleno", -1]],
  {"error": "el relleno y la tensión de prueba industrial"}, compuerta="c3")
R("X-05", 3, "decide", "Posición radial fija",
  "El Devanado I es siempre el externo; hacia el núcleo siguen el II y el III. La posición no se digita.", "TU",
  "Siempre (aunque los datos traigan otra posición).", "El más interno va junto al núcleo.", "—",
  "posiciones_radiales / con_posiciones", "posicionesRadiales / conPosiciones",
  {"py": "ORDEN_RADIAL = [\"III\", \"II\", \"I\"]", "js": "const ORDEN_RADIAL = [\"III\", \"II\", \"I\"]"},
  [["dev.I.pos", 1], ["dev.II.pos", 2]], {"valor": "lista.1.clave", "op": "==", "v": "I", "sin_base": True})
R("X-06", 3, "bloquea", "Misma posición radial",
  "Dos devanados no pueden ir en la misma posición radial.", "PRG",
  "No se puede dar: la posición sale del orden fijo (X-05).", "—", "Se puede borrar.", "calcular_datos",
  "calcularTodo", "tienen la misma posición radial", revision="sin-uso",
  nota="Quedó del tiempo en que la posición se digitaba. La búsqueda tiene la misma comprobación (B-08).",
  compuerta="c3")

# =====================================================================
# Compuerta 4 · devanados dentro de la ventana
# =====================================================================
R("D-01", 3, "corrige", "Cantidad y horizontales al límite del tipo",
  "Antes de validar, la cantidad se lleva a 1…máximo del tipo y las horizontales a 1…máximo; hélice usa sus "
  "horizontales fijas y continuo/galleta horizontales = cantidad.", "DEV",
  "Cantidad o horizontales fuera del rango del tipo.",
  "El programa cambia el número en la pantalla sin avisar (por eso D-02 a D-05 nunca aparecen en el diseño).",
  "Decidir: dejarlo así (la pantalla ya muestra el número corregido) o avisar con D-02/D-05.",
  "calcular_datos / ajustar_tabla", "calcularTodo", {"py": "cant = min(max(cant, 1), r[\"max_cond\"])", "js": "cant = Math.min(Math.max(Math.trunc(cant), 1), r.max_cond)"},
  [["dev.I.cant", 30]], {"valor": "llenado.I.cant", "op": "==", "v": 3, "sin_error": True, "sin_base": True}, revision="dudoso",
  compuerta="c4")
R("D-00", 3, "bloquea", "Cantidad y horizontales al menos 1", "La cantidad de conductores y las horizontales deben ser al menos 1.",
  "PRG", "No se dispara en el diseño: D-01 lleva la cantidad y las horizontales a 1 o más antes de validar.", "—", "—", "validar", "validar",
  "La cantidad de conductores y las horizontales deben ser al menos 1.", revision="sin-uso", compuerta="c4")
R("D-02", 3, "bloquea", "Máximo de conductores del tipo", "Cantidad ≤ máximo del tipo (continuo 3, francés 18, hélice simple 24, doble 48).",
  "DEV", "No se dispara en el diseño: D-01 corrige antes.", "—", "—", "validar", "validar",
  "conductores por espira (ingresaste", revision="sin-uso", nota="Sirve de respaldo; la búsqueda solo arma arreglos válidos.",
  compuerta="c4")
R("D-03", 3, "bloquea", "Horizontales fijas de la hélice", "Hélice simple 2 y doble 4 horizontales.", "DEV",
  "No se dispara en el diseño: D-01 las fija.", "—", "—", "validar", "validar", ": las horizontales son fijas = ",
  revision="sin-uso", compuerta="c4")
R("D-04", 3, "bloquea", "Máximo de horizontales", "Horizontales ≤ máximo del tipo.", "DEV",
  "No se dispara en el diseño: D-01 corrige.", "—", "—", "validar", "validar", "horizontales.",
  revision="sin-uso", compuerta="c4")
R("D-05", 3, "bloquea", "Continuo y galleta: 1 radial", "Continuo y galleta: solo 1x1, 2x2 o 3x3.", "DEV",
  "No se dispara en el diseño: D-01 pone horizontales = cantidad.", "—", "—", "validar", "validar",
  ": 1 radial fijo, solo se permite 1x1, 2x2 o 3x3.", revision="sin-uso", compuerta="c4")
R("D-06", 3, "bloquea", "Cantidad múltiplo de horizontales", "La cantidad debe repartirse exacta en las horizontales.",
  "DEV", "Francés con 5 conductores en 2 horizontales.", "No calcula.", "Usa una cantidad múltiplo.",
  "validar", "validar", " conductores no se reparten en ", [["dev.II.tipo", "FRANCÉS"], ["dev.II.cant", 5], ["dev.II.horiz", 2]],
  {"error": "no se reparten en 2 horizontales"}, compuerta="c4")
R("D-07", 3, "bloquea", "Francés: 2 o 3 radiales", "Francés: cantidad / horizontales = 2 o 3 verticales.", "DEV",
  "Francés 4 conductores en 4 horizontales (1 radial).", "No calcula.", "Usa 2 o 3 radiales.", "validar", "validar",
  " verticales (radiales); ", [["dev.II.tipo", "FRANCÉS"], ["dev.II.cant", 4], ["dev.II.horiz", 4]],
  {"error": "se permiten 2 o 3 verticales"}, compuerta="c4")
R("D-08", 3, "bloquea", "Espiras por capa al menos 1", "Espiras totales ≥ 1 y espiras por capa ≥ 1.", "PRG",
  "Más capas que espiras.", "No calcula.", "Baja las capas.", "validar", "validar",
  "Las espiras totales y las espiras por capa deben ser al menos 1",
  [["dev.I.modo", "capas"], ["dev.I.capas", 5000]], {"error": "espiras por capa deben ser al menos 1"}, compuerta="c4")
R("D-09", 3, "bloquea", "Francés: 2 capas", "El francés es de 2 capas; con capas o espiras por capa a mano debe dar 2.",
  "TU", "Francés con 3 capas a mano.", "No calcula.", "Usa «Ajustar a la ventana» o 2 capas.", "validar", "validar",
  "espiras por capa salen",
  [["dev.II.tipo", "FRANCÉS"], ["dev.II.cant", 4], ["dev.II.horiz", 2], ["dev.II.modo", "capas"], ["dev.II.capas", 3]],
  {"error": "es de 2 capas"}, compuerta="c4")
R("D-10", 3, "bloquea", "Hélice: una sola capa", "La hélice (simple y doble) es de una sola capa.", "TU",
  "Hélice con 2 capas a mano.", "No calcula.", "Usa «Ajustar a la ventana» o 1 capa.", "validar", "validar",
  "es de una sola capa", [["dev.II.modo", "capas"], ["dev.II.capas", 2]], {"error": "es de una sola capa"},
  compuerta="c4")
R("D-11", 3, "bloquea", "Papeles, canal y yugo sin negativos", "Papeles, canal interior y distancia al yugo ≥ 0.",
  "PRG", "Valor negativo.", "No calcula.", "Corrige el signo.", "calcular_bobinado", "calcularTodo",
  "Papeles, canal interior y distancia al yugo no pueden ser negativos.", [["dev.I.papel_capa", -0.1]],
  {"error": "Papeles, canal interior"}, compuerta="c4")
R("D-12", 3, "bloquea", "Medida de canales internos", "Con 1 o más canales internos, la medida debe ser > 0 mm.",
  "PRG", "Canales con medida 0.", "No calcula.", "Digita la medida.", "calcular_bobinado", "calcularTodo",
  "Canales internos: con 1 o más canales, la medida de cada canal debe ser mayor que 0 mm.",
  [["dev.I.n_canales", 2], ["dev.I.canal_mm", 0]], {"error": "la medida de cada canal"}, compuerta="c4")
R("D-13", 3, "bloquea", "No entra ni una espira por capa",
  "Con «Ajustar a la ventana»: (Hc − 2 x yugo − transposiciones x ancho) / ancho de espira − 1 < 1.", "DEV",
  "Hc chica, yugo grande o muchas transposiciones.", "No calcula; dice cuántos mm deja la ventana.",
  "Sube Hc, baja el yugo o las transposiciones.", "calcular_bobinado", "calcularTodo", "no entra en la ventana: Hc ",
  [["hc", 100]], {"error": "no cabe ni una espira por capa"}, compuerta="c4")
R("D-14", 3, "decide", "Capas desde la ventana",
  "«Ajustar a la ventana»: útil = ENTERO(Hc − 2 x yugo − transp x ancho conductor); espiras por capa = útil / ancho espira − 1; "
  "capas = REDONDEO.MAS(espiras / esp. por capa).", "DEV", "Modo ventana.", "Capas y espiras por capa se llenan solas.", "—",
  "ajuste_ventana", "ajusteVentana", {"py": "epc_lim = util / ancho_espira - 1", "js": "const epcLim = util / anchoEspira - 1"},
  [["hc", 700]], {"valor": "llenado.I.capas", "op": "<", "v": 10})
R("D-15", 3, "decide", "Francés: siempre 2 capas en la ventana", "Con «Ajustar a la ventana», el francés va en 2 capas.",
  "TU", "Tipo francés.", "Si no entran en la altura, igual calcula y «Al yugo» dice los mm que faltan.", "—",
  "ajuste_ventana", "ajusteVentana", {"py": "fijas = TIPOS[tipo].get(\"capas_fijas\")", "js": "const fijas = TIPOS[tipo].capas_fijas || null"},
  [["dev.II.tipo", "FRANCÉS"], ["dev.II.cant", 4], ["dev.II.horiz", 2]], {"valor": "llenado.II.capas", "op": "==", "v": 2})
R("D-16", 3, "decide", "Hélice: siempre 1 capa en la ventana", "Con «Ajustar a la ventana», la hélice va en 1 capa.",
  "TU", "Tipo hélice.", "Si no entra, «Al yugo» marca no cumple con los mm que faltan.", "—", "ajuste_ventana",
  "ajusteVentana", {"py": "\"entra_fijas\":", "js": "entra_fijas:"}, [["hc", 480]],
  {"limite": "yugo-II", "estado": "no"})
R("D-17", 3, "decide", "Capas o espiras por capa a mano",
  "«N° de capas»: espiras por capa = N / capas. «Espiras por capa»: capas = REDONDEO.MAS(N / esp. por capa).", "DEV",
  "Modo a mano.", "Luego se verifica que entre.", "—", "calcular_datos / calcular_devanado", "calcularTodo / calcularDevanado",
  {"py": "if capas_in:", "js": "if (capasIn) {"}, [["dev.I.modo", "capas"], ["dev.I.capas", 14]],
  {"valor": "llenado.I.capas", "op": "==", "v": 14})
R("D-18", 3, "decide", "Galleta: 2 secciones", "Galleta: 2 devanados en el mismo eje, cada uno con la mitad de las espiras y 20 mm entre ellos.",
  "DEV", "Tipo galleta.", "Axial total = 2 x axial de sección + 20.", "—", "calcular_devanado", "calcularDevanado",
  {"py": "SEPARACION_GALLETA = 20.0", "js": "const SEPARACION_GALLETA = 20.0"}, [["dev.I.tipo", "GALLETA"]],
  {"valor": "lista.1.res.n_sec", "op": "==", "v": 2})
R("D-23", 3, "decide", "Galleta: espiras de cada bobina",
  "La galleta son 2 bobinas en el mismo eje: la primera lleva REDONDEO.MAS(N / 2) espiras y la segunda el resto (con N impar, "
  "una espira menos). Las dos se dimensionan con la mayor.", "DEV", "Tipo galleta.",
  "La tabla muestra «por bobina: a + b» bajo las espiras y la hoja del devanado da a + b = N (y las nominales).", "—",
  "espiras_por_bobina / pintar_espiras", "espirasPorBobina / pintarCalculadas",
  {"py": "def espiras_por_bobina(tipo, n_espiras):", "js": "function espirasPorBobina(tipo, n)"})
R("D-19", 3, "decide", "Transposiciones ocupan altura", "Cada transposición suma el ancho de un conductor al axial.",
  "DEV", "Transposiciones > 0.", "Sube el axial; con «Ajustar a la ventana» resta espiras por capa.", "—",
  "calcular_devanado / ajuste_ventana", "calcularDevanado / ajusteVentana",
  {"py": "axial_seccion = axial_redondeado + transposiciones * ancho_cond", "js": "const axialSeccion = axialRed + transp * anchoCond"},
  [["dev.I.transp", 6]], {"valor": "lista.1.res.axial_seccion", "op": "distinto_base"})
R("H-05", 3, "hueco", "Transposiciones negativas", "No se verifica que las transposiciones sean ≥ 0.", "PRG",
  "Transposiciones −3.", "Calcula sin avisar y el devanado gana altura útil.", "Agregar: transposiciones ≥ 0.",
  "calcular_bobinado", "calcularTodo", {"py": "def calcular_bobinado", "js": "function calcularTodo"},
  [["dev.II.transp", -3]], {"valor": "lista.0.res.axial_seccion", "op": "menor_base", "sin_error": True},
  revision="hueco")
R("D-20", 3, "decide", "Alambre sin papel", "Con alambre el papel es 0 aunque esté vacío; con platina se usa el digitado.",
  "DEV", "Calibre alambre.", "El diámetro esmaltado ya es la medida final.", "—", "calcular_datos", "calcularTodo",
  {"py": "papel = 0.0 if w[\"papel\"] is None and w[\"calibre\"][0] == \"ALAMBRE\"", "js": "const papel = vacio(w.papel) && w.calibre[0] === \"ALAMBRE\" ? 0 : w.papel"},
  [["dev.I.papel", None]], {"valor": "mont.peso_cu", "op": "igual_base"})
R("D-21", 3, "decide", "Sección de la espira con platina x 0,97", "Platina: sección x cantidad x 0,97; alambre: sección x cantidad.",
  "DE", "Calibre platina.", "Baja la sección y sube la densidad.", "—", "seccion_espira", "seccionEspira",
  {"py": "FACTOR_SECCION_PLATINA = 0.97", "js": "const FACTOR_SECCION_PLATINA = 0.97"}, [],
  {"valor": "lista.0.res.seccion_total", "op": "==", "v": 526.225})
R("D-22", 3, "decide", "Radial y axial redondeados",
  "Radial = REDONDEO.MAS(capas x (papel entre capas + espesor de espira) + Σ canales). Axial = REDONDEO.MAS((espiras por capa + 1) x ancho de espira) + transp x ancho.",
  "DEV", "Siempre.", "Medidas en mm enteros, como la hoja.", "—", "calcular_devanado", "calcularDevanado",
  {"py": "axial_bruto = (esp_por_capa + 1) * ancho_espira", "js": "const axialBruto = (epc + 1) * anchoEspira"},
  nota="Comparado contra la hoja de devanado: 2304 combinaciones idénticas.")

# =====================================================================
# Compuerta 5 · montaje, Vcc y esfuerzos
# =====================================================================
R("M-01", 4, "decide", "Diámetros del núcleo hacia afuera",
  "Ø interior = Ø anterior + 2 x canal interior (el primero parte de Dn); Ø exterior = Ø interior + 2 x radial; "
  "Ø total = último + 2 x tubo enrollado.", "DEV", "Siempre.", "Fija espira media, peso y Vcc.", "—",
  "calcular_montaje", "calcularMontaje", {"py": "d_int = d_prev + 2.0 * item[\"canal\"]", "js": "const dInt = dPrev + 2 * item.canal"})
R("H-06", 4, "hueco", "Tubo núcleo–bobina no mueve el diámetro",
  "El tubo núcleo–bobina suma a la distancia del esfuerzo, pero no al diámetro de los devanados.", "ESF",
  "Tubo núcleo–bobina 5 mm.", "El esfuerzo usa canal + 5; los diámetros, el peso y el Vcc no cambian.",
  "Confirmar: ¿el tubo va dentro del canal interior (está bien) o se suma (el Ø interior debe crecer)?",
  "calcular_montaje / esfuerzos_dielectricos", "calcularMontaje / esfuerzosDielectricos",
  {"py": "dist0 = a[\"canal\"] + d[\"tubo_nucleo\"]", "js": "dist0 = a.canal + d.tubo_nucleo"},
  [["tubo_nucleo", 5]], {"valor": "mont.filas.0.d_int", "op": "igual_base", "sin_error": True}, revision="dudoso")
R("H-07", 4, "hueco", "Espesor de la barrera no mueve el diámetro",
  "El espesor de la barrera (hawayano o tubo) suma al contorno, pero no al diámetro del devanado de afuera.", "ESF",
  "Barrera de 8 mm.", "El contorno crece 6 mm; los diámetros no cambian.",
  "Confirmar: ¿la barrera va dentro del canal interior?", "calcular_montaje / esfuerzos_dielectricos",
  "calcularMontaje / esfuerzosDielectricos", {"py": "eb = d[\"e_barrera\"]", "js": "eb = d.e_barrera"},
  [["e_barrera", 8]], {"valor": "mont.filas.1.d_int", "op": "igual_base", "sin_error": True}, revision="dudoso")
R("A-03", 4, "aviso", "Los devanados no entran en el núcleo",
  "Si algún devanado deja al yugo menos que su mínimo, o entre fases queda menos que el mínimo, se muestra el aviso rojo "
  "«Los devanados no entran en el núcleo» con los mm que faltan.", "TU", "Devanado alto o grueso para el núcleo.",
  "Calcula todo y muestra el aviso arriba de los resultados (el núcleo es el que limita).",
  "Achica el devanado o cambia el núcleo.", "html_no_entra", "textosNoEntra",
  "y el mínimo es", nota="Comparado en los 48 casos de Python = web (campo no_entra).", compuerta="c5")
R("M-02", 5, "decide", "Peso de cobre", "Peso = 3 fases x espiras máximas x π·Dm x sección x 8,9 kg/dm³.", "PES",
  "Siempre.", "Usa las espiras de la toma máxima.", "—", "calcular_montaje", "calcularMontaje",
  {"py": "peso = FASES * long_fase * res[\"seccion_total\"] * DENS_CU / 1000.0", "js": "const peso = FASES * longFase * res.seccion_total * DENS_CU / 1000"})
R("H-08", 5, "hueco", "Peso de cobre sin las conexiones",
  "El cálculo de peso de devanados suma 0,3 m de conductor en cada punta (2 puntas x 3 fases); este programa no.", "PES",
  "Siempre.", "El cobre sale algo menor que en el cálculo de peso de devanados (unos kg según la sección).",
  "Decidir si se suma el peso de conexiones.", "calcular_montaje", "calcularMontaje",
  {"py": "long_fase = e[\"n_max\"] * l_espira / 1000.0", "js": "const lEsp = Math.PI * dMed, longFase = e.n_max * lEsp / 1000"},
  revision="dudoso")
R("M-03", 5, "decide", "Resistencia y pérdidas I²R",
  "ρ(T) = 0,017241 x (234,5 + T) / (234,5 + 20); R = ρ x espiras nominales x π·Dm / sección; Pcu = 3 x I carga² x R.",
  "FIS", "Siempre.", "Pérdidas en corriente continua, sin adicionales.", "—", "calcular_montaje", "calcularMontaje",
  {"py": "rho_t = RHO_CU_20 * (234.5 + t_ref) / (234.5 + 20.0)", "js": "const rhoT = RHO_CU_20 * (234.5 + tRef) / (234.5 + 20)"})
R("H-09", 5, "hueco", "T° de referencia sin rango", "No se verifica la T° de referencia.", "PRG",
  "T° −300 °C (o 7500 por 75.00 mal digitado).", "Calcula sin avisar: por debajo de −234,5 °C las pérdidas salen negativas.",
  "Agregar: T° entre 20 y 120 °C, por ejemplo.", "calcular_montaje", "calcularMontaje",
  {"py": "rho_t = RHO_CU_20 * (234.5 + t_ref)", "js": "const rhoT = RHO_CU_20 * (234.5 + tRef)"},
  [["tref", -300]], {"valor": "mont.perdidas", "op": "<", "v": 0, "sin_error": True}, revision="hueco")
R("M-04", 5, "decide", "Vcc entre el Devanado I y cada secundario",
  "Vcc reactiva = (N·I)·(π·Dm)·(λ + (e1 + e2)/3)·kR·K / (Heq·B·Sfe); activa = Pcu / (S·10); Vcc = √(reactiva² + activa²). "
  "S = la menor de las dos potencias.", "VCC", "Siempre.", "Un Vcc por par I–secundario.", "—", "calcular_vcc", "calcularVcc",
  {"py": "* k_r * K_VCC / (h_eq * b_kg * s_fe)", "js": "* kR * K_VCC / (hEq * bKg * sFe)"})
R("M-05", 5, "decide", "kR del cuadro de Rogowski",
  "kR según la corriente del secundario: desde 1 A 0,96; 501 A 0,98; 631 A 1,02; 1001 A 1,05; 1501 A 1,10; 2501 A 1,15.",
  "VCC", "Corriente del secundario.", "Factor de la reactiva.", "—", "k_rogowski", "kRogowski",
  {"py": "TABLA_ROGOWSKI = [(1, 0.96)", "js": "const TABLA_ROGOWSKI = [[1, 0.96]"}, [],
  {"valor": "pares.0.k_r", "op": "==", "v": 1.05})
R("H-10", 5, "hueco", "Constante K del Vcc", "K = 0,018 (hoja de Excel). La nota del PDF dice K = 17,77/1000 = 0,01777.",
  "VCC", "Siempre.", "Con 0,018 la Vcc reactiva sale 1,3 % más alta que con 0,01777.", "Confirmar cuál K usar.",
  "calcular_vcc", "calcularVcc", {"py": "K_VCC = 0.018", "js": "const K_VCC = 0.018"}, revision="dudoso")
R("H-11", 5, "decide", "π exacto frente a 3,1416", "El programa usa π exacto; la hoja de Vcc usa 3,1416.", "VCC",
  "Siempre.", "Diferencia de 0,0002 %: no cambia ningún resultado visible.", "Ninguno.", "calcular_vcc", "calcularVcc",
  {"py": "(math.pi * d_m)", "js": "(Math.PI * dM)"}, nota="Diferencia despreciable.")
R("S-01", 4, "decide", "Esfuerzo núcleo – bobina interna",
  "E = prueba industrial de la bobina interna / (canal interior + tubo núcleo–bobina).", "ESF", "Siempre.",
  "Se compara con 1,8 kV/mm (máx. 2).", "—", "esfuerzos_dielectricos", "esfuerzosDielectricos",
  {"py": "e0 = ua / dist0 if dist0 > 0 else math.inf", "js": "e0 = dist0 > 0 ? ua / dist0 : Infinity"})
R("S-02", 4, "decide", "Contorno bobina – bobina",
  "lado = canal/2; s = tubo rígido/2; R = 0,75 x radial de afuera; HAWAYANO = d1 + e + d2 + d3 + d4; TUBO = d1 + e + d5. "
  "E = la mayor prueba industrial / contorno.", "ESF", "Barrera elegida.", "Reproduce la hoja: 94,91 mm → 0,74 kV/mm.",
  "—", "esfuerzos_dielectricos", "esfuerzosDielectricos",
  {"py": "FACTOR_RADIAL_CONTORNO = 0.75", "js": "FACTOR_RADIAL_CONTORNO = 0.75"}, [["barrera", "TUBO"]],
  {"valor": "esf.1.distancia", "op": "distinto_base"},
  nota="Supuestos por confirmar: canal/2 a cada lado de la barrera, s = tubo rígido / 2, d4 = relleno de afuera.")
R("H-12", 4, "hueco", "Prueba industrial en 0 kV", "Una prueba industrial de 0 kV se acepta y el esfuerzo sale 0 (cumple).",
  "ESF", "Prueba industrial 0 en los dos devanados.", "Los esfuerzos cumplen sin haber verificado nada.",
  "Agregar: prueba industrial > 0 en cada devanado con potencia.", "errores_esfuerzos", "calcularTodo",
  {"py": "def errores_esfuerzos", "js": "d.dev[k].industrial < 0"},
  [["dev.I.industrial", 0], ["dev.II.industrial", 0]], {"limite": "esf-bob-II-I", "estado": "ok", "sin_error": True},
  revision="hueco")
R("H-13", 1, "hueco", "BIL no se usa", "El BIL se pide en el paso 1, pero ningún cálculo ni verificación lo usa.", "DE",
  "BIL 1 kV en el Devanado I.", "Calcula igual: no se compara con la tensión ni con la prueba industrial.",
  "Decidir: tabla BIL → prueba industrial / distancias, o una verificación BIL según la tensión.",
  "calcular_electrico", "calcularElectrico", {"py": "\"bil\": s[\"bil\"]", "js": "bil: s.bil"},
  [["dev.I.bil", 1]], {"valor": "mont.peso_cu", "op": "igual_base", "sin_error": True}, revision="hueco")

# =====================================================================
# Compuerta 6 · semáforo de límites
# =====================================================================
R("L-01", 4, "limite", "Entre fases", "Entre fases real = De − Ø exterior con tubo ≥ mínimo. Uso = mínimo / real.", "PRG",
  "De chico o devanados gruesos.", "No cumple con los mm que faltan.", "Sube De o achica los devanados.",
  "limites_diseno", "limitesDiseno", {"py": "\"clave\": \"fases\"", "js": "clave: \"fases\""}, [["fases", 80]],
  {"limite": "fases", "estado": "no"}, umbral="mínimo digitado", compuerta="c6")
R("L-02", 4, "limite", "Al yugo", "Al yugo = (Hc − axial) / 2 ≥ mínimo. Uso = mínimo / real.", "DEV",
  "Devanado más alto que la ventana.", "No cumple con los mm que faltan por lado.", "Baja el axial o sube Hc.",
  "limites_diseno", "limitesDiseno", {"py": "\"clave\": f\"yugo-{f['clave']}\"", "js": "clave: `yugo-${f.clave}`"},
  [["dev.I.modo", "capas"], ["dev.I.capas", 6]], {"limite": "yugo-I", "estado": "no"}, umbral="mínimo digitado",
  compuerta="c6")
R("L-03", 4, "decide", "Al yugo ajustado a la ventana",
  "Con «Ajustar a la ventana» y uso ≤ 100 %, el yugo es «ajustado a la ventana»: cumple y no gobierna.", "PRG",
  "Modo ventana.", "Estar cerca del mínimo es lo buscado, no un aviso.", "—", "limites_diseno / limite_gobernante",
  "limitesDiseno / limiteGobernante", {"py": "\"ajustado a la ventana\"", "js": "\"ajustado a la ventana\""}, [],
  {"valor": "limites.yugo-I.nota", "op": "==", "v": "ajustado a la ventana"}, compuerta="c6")
R("L-04", 3, "limite", "Canales internos",
  "Los canales van dentro de la espira, entre conductores (y entre capas si hay varias): N° de canales ≤ radiales x capas − 1.", "TU",
  "Más canales que espacios entre conductores radiales (por ejemplo 6 canales en una hélice de 5 radiales).", "No cumple: «caben N».",
  "Quita canales o usa más conductores radiales.", "limites_diseno", "limitesDiseno",
  {"py": "\"clave\": f\"canales-{f['clave']}\"", "js": "clave: `canales-${f.clave}`"},
  [["dev.II.n_canales", 6], ["dev.II.canal_mm", 4]], {"limite": "canales-II", "estado": "no"}, umbral="radiales x capas − 1",
  compuerta="c6", nota="Antes el límite era capas − 1 (solo entre capas): una hélice de 1 capa no admitía canales.")
R("L-05", 4, "limite", "Esfuerzo núcleo – bobina",
  "Hasta 1,8 kV/mm cumple; de 1,8 a 2 en rojo pero procede; más de 2 no cumple.", "ESF",
  "Prueba industrial alta o canal interior chico.", "Rojo «procede» o no cumple.", "Sube el canal interior o pon tubo.",
  "limite_esfuerzo", "limiteEsfuerzo", {"py": "ESFUERZO_BOB_NUC_MAX = 2.0", "js": "ESFUERZO_BOB_NUC_MAX = 2.0"},
  [["dev.II.industrial", 19]], {"limite": "esf-nuc-II", "estado": "procede"}, umbral="1,8 kV/mm (máx. 2)",
  compuerta="c6")
R("L-06", 4, "limite", "Esfuerzo núcleo – bobina sobre 2 kV/mm", "Más de 2 kV/mm no cumple.", "ESF",
  "Prueba industrial muy alta para el canal.", "No cumple.", "Sube el canal interior.", "limite_esfuerzo", "limiteEsfuerzo",
  {"py": "f\"pasa de {ESFUERZO_BOB_NUC_MAX:g} kV/mm\"", "js": "`pasa de ${g(ESFUERZO_BOB_NUC_MAX)} kV/mm`"},
  [["dev.II.industrial", 25]], {"limite": "esf-nuc-II", "estado": "no"}, umbral="2 kV/mm", compuerta="c6")
R("L-07", 4, "limite", "Esfuerzo bobina – bobina", "Contorneo ≤ 0,8 kV/mm.", "ESF", "Canal, relleno o barrera chicos.",
  "No cumple.", "Sube relleno, canal o usa hawayano.", "limite_esfuerzo", "limiteEsfuerzo",
  {"py": "ESFUERZO_BOB_BOB = 0.8", "js": "ESFUERZO_BOB_BOB = 0.8"}, [["dev.I.industrial", 90]],
  {"limite": "esf-bob-II-I", "estado": "no"}, umbral="0,8 kV/mm", compuerta="c6")
R("L-08", 3, "limite", "Densidad de corriente", "J = I máxima / sección ≤ J máxima de las condiciones del diseñador.", "TC",
  "Conductor chico.", "No cumple.", "Sube la sección.", "limites_diseno", "limitesDiseno",
  {"py": "\"clave\": f\"j-{f['clave']}\"", "js": "clave: `j-${f.clave}`"}, [["j_max", 4.5]],
  {"limite": "j-II", "estado": "no"}, umbral="4,7 A/mm² (condición del diseñador, paso 3)", compuerta="c6")
R("L-09", 2, "limite", "Inducción B", "B real ≤ B máxima; si hay B mínima, B real ≥ B mínima.", "TC",
  "Espiras de referencia o núcleo fuera de rango.", "No cumple («bajo el mínimo»).", "Cambia Dn o las espiras.",
  "limites_diseno", "limitesDiseno", {"py": "bajo el mínimo de", "js": "bajo el mínimo de"}, [["b_min", 1.6]],
  {"limite": "b", "estado": "no"}, umbral="1,65 a 1,73 T (condición del diseñador, paso 2)", compuerta="c6")
R("L-10", 3, "limite", "Error de relación en rojo (procede)",
  "Hasta 0,3 % cumple; de 0,3 a 0,5 % se marca en rojo pero procede; más de 0,5 % no procede.", "TU",
  "Una tensión o una toma que no da espiras enteras.", "Rojo «procede».", "Revisa tensiones o espiras de referencia.",
  "estado_error / limites_diseno", "estadoError / limitesDiseno", {"py": "\"clave\": \"relacion\"", "js": "clave: \"relacion\""},
  [["dev.II.volt", 458]], {"limite": "relacion", "estado": "procede"}, umbral="0,3 % / 0,5 %", compuerta="c6")
R("L-11", 3, "limite", "Error de relación sobre 0,5 %", "Más de 0,5 % no procede.", "TU",
  "Tensiones que no salen con espiras enteras.", "No cumple.", "Revisa tensiones o espiras.", "estado_error",
  "estadoError", {"py": "ERROR_RELACION_MAX = 0.5", "js": "ERROR_RELACION_MAX = 0.5"}, [["dev.II.volt", 456]],
  {"limite": "relacion", "estado": "no"}, umbral="0,5 %", compuerta="c6")
R("L-12", 5, "limite", "Vcc dentro de la tolerancia", "|Vcc − objetivo| ≤ objetivo x tolerancia %.", "TU",
  "Vcc objetivo y tolerancia del diseño (paso 1).", "No cumple.", "Usa la búsqueda por Vcc.", "limites_diseno", "limitesDiseno",
  {"py": "\"clave\": f\"vcc-{p['clave']}\"", "js": "clave: `vcc-${p.clave}`"}, [["vcc_obj", 6]],
  {"limite": "vcc-II", "estado": "no"}, umbral="objetivo ± tolerancia", compuerta="c6")
R("L-16", 5, "decide", "Condiciones del semáforo: las del diseño",
  "El semáforo usa las condiciones del propio diseño: Vcc objetivo y tolerancia (paso 1), B mínima y B máxima = objetivo "
  "(paso 2) y J máxima (paso 3). Las vacías no se verifican. La búsqueda por Vcc tiene las suyas y no las cambia.", "TU",
  "Condición del diseño digitada o vacía.", "Cambia los límites del semáforo.", "—", "condiciones_diseno / condiciones_ui",
  "condicionesDiseno", {"py": "def condiciones_diseno(d):", "js": "const condicionesDiseno = (d) =>"},
  [["b_min", 1.6]], {"valor": "limites.b.limite", "op": "==", "v": "1.6 a 1.76 T"}, compuerta="c6",
  nota="Antes las condiciones del semáforo eran las del panel de búsqueda.")
R("L-13", 5, "decide", "Cerca del límite", "Desde 90 % de uso el límite se marca «cerca» (ámbar).", "PRG",
  "Uso ≥ 90 %.", "Ámbar.", "—", "limites_diseno", "limitesDiseno", {"py": "uso >= 0.9 - 1e-12", "js": "uso >= 0.9 - 1e-12"},
  [["j_max", 4.7]], {"limite": "j-I", "estado": "cerca"}, compuerta="c6")
R("L-14", 5, "decide", "Límite que gobierna",
  "Gobierna el que no cumple; si todos cumplen, el de mayor uso (sin contar los yugos ajustados).", "PRG",
  "Siempre.", "Se muestra en el paso 5.", "—", "limite_gobernante", "limiteGobernante",
  {"py": "def limite_gobernante", "js": "function limiteGobernante"}, [["dev.I.industrial", 90]],
  {"valor": "gobierna", "op": "==", "v": "esf-bob-II-I"}, compuerta="c6")
R("L-15", 5, "decide", "% de uso mostrado", "Hasta 100 % se trunca y desde ahí se sube (89,7 % → 89 %; 100,4 % → 101 %).",
  "PRG", "Siempre.", "El % nunca contradice el color.", "—", "pct_texto", "pctTexto",
  {"py": "def pct_texto", "js": "const pctTexto"}, compuerta="c6")

# =====================================================================
# Compuerta 7 · barra de pasos
# =====================================================================
R("B-P1", 5, "decide", "Paso con datos faltantes", "Un paso con datos vacíos se marca «Faltan N datos».", "TU",
  "Dato vacío.", "Ámbar en ese paso; el 5 queda pendiente.", "—", "estado_pasos", "estadoPasos",
  {"py": "Faltan {falta}", "js": "`Faltan ${falta}"}, [["tubo", None]], {"paso": 4, "estado": "falta"}, compuerta="c7")
R("B-P2", 5, "decide", "Dónde se muestra un error",
  "Sin núcleo, los errores se muestran en el paso 2; con núcleo, en el paso 3.", "PRG", "Error que impide calcular.",
  "«Revisar N datos» en ese paso.", "—", "estado_pasos", "estadoPasos",
  {"py": "aqui = errores and ((p == 2 and not nuc_ok) or (p == 3 and nuc_ok))", "js": "const aqui = errores.length && ((p === 2 && !nucOk) || (p === 3 && nucOk))"},
  [["de", 250]], {"paso": 2, "estado": "no"}, compuerta="c7")
R("B-P3", 5, "decide", "Estado de cada paso", "Cada paso toma el peor estado de sus límites (no > procede > cerca > cumple).",
  "PRG", "Límites del paso.", "Color del paso.", "—", "estado_pasos", "estadoPasos",
  {"py": "PESO_ESTADO = {\"ok\": 0, \"cerca\": 1, \"procede\": 2, \"no\": 3}", "js": "const PESO_ESTADO = { ok: 0, cerca: 1, procede: 2, no: 3 }"},
  [["fases", 80]], {"paso": 4, "estado": "no"}, compuerta="c7")

# =====================================================================
# Compuerta 8 · búsqueda por Vcc
# =====================================================================
OPC = {"vcc": 3.1, "tol": 7.5, "jmin": 2.0, "jmax": 5.0, "bmin": 1.5, "bmax": 1.76, "dn_fijo": 257, "dn_min": None,
       "dn_max": None, "dn_paso": None, "de_max": 0, "orden": "peso", "max": 3}


def O(**kw):
    o = dict(OPC)
    o.update(kw)
    return o


R("Q-01", 6, "bloquea", "Diseño completo para buscar", "La búsqueda pide primero los datos del diseño que faltan.", "TU",
  "Dato del diseño vacío.", "No busca.", "Completa el diseño.", "buscar_combinaciones", "buscarCombinaciones",
  "Para buscar, primero digita estos datos.", [["tref", None]], {"busqueda": O(), "error": "Para buscar"}, compuerta="c8")
R("Q-02", 6, "bloquea", "Condiciones de la búsqueda vacías",
  "Vcc objetivo, tolerancia, J mín/máx, B mín/máx, Dn fijo y De máximo (o el rango de Dn) deben estar digitados.", "TU",
  "Vcc objetivo vacío (no tiene fuente).", "No busca.", "Digita la condición.", "validar_busqueda", "validarBusqueda",
  {"py": "\"Búsqueda: digita \"", "js": "`Búsqueda: digita "}, [], {"busqueda": O(vcc=None), "error": "Búsqueda: digita Vcc objetivo"},
  compuerta="c8")
R("Q-03", 6, "bloquea", "Vcc y tolerancia > 0", "Vcc objetivo y tolerancia mayores que 0.", "PRG", "Tolerancia 0.",
  "No busca.", "Corrige.", "validar_busqueda", "validarBusqueda", "Búsqueda: el Vcc objetivo y su tolerancia deben ser mayores que 0.",
  [], {"busqueda": O(tol=0), "error": "Vcc objetivo y su tolerancia"}, compuerta="c8")
R("Q-04", 6, "bloquea", "J máxima > J mínima", "0 ≤ J mínima < J máxima.", "TC", "J mínima mayor que la máxima.",
  "No busca.", "Corrige.", "validar_busqueda", "validarBusqueda", "Búsqueda: la densidad máxima debe ser mayor que la mínima.",
  [], {"busqueda": O(jmin=6), "error": "densidad máxima"}, compuerta="c8")
R("Q-05", 6, "bloquea", "B máxima > B mínima", "0 < B mínima < B máxima.", "TC", "B mínima mayor que la máxima.",
  "No busca.", "Corrige.", "validar_busqueda", "validarBusqueda", "Búsqueda: la inducción máxima debe ser mayor que la mínima.",
  [], {"busqueda": O(bmin=1.8), "error": "inducción máxima"}, compuerta="c8")
R("Q-06", 6, "bloquea", "Rango de Dn válido", "Sin Dn fijo: mínimo > 0, máximo ≥ mínimo y paso > 0.", "PRG",
  "Paso de Dn 0.", "No busca.", "Corrige el rango.", "validar_busqueda", "validarBusqueda",
  "Búsqueda: el rango de Dn no es válido (mínimo, máximo y paso mayores que 0).", [],
  {"busqueda": O(dn_fijo=0, dn_min=200, dn_max=260, dn_paso=0), "error": "rango de Dn no es válido"}, compuerta="c8")
R("Q-07", 6, "bloquea", "Rango de Dn de hasta 400 valores", "El rango de Dn no puede tener más de 400 valores.", "PRG",
  "Paso muy fino.", "No busca.", "Usa un paso mayor.", "validar_busqueda", "validarBusqueda",
  "Búsqueda: el rango de Dn tiene más de 400 valores; usa un paso mayor.", [],
  {"busqueda": O(dn_fijo=0, dn_min=100, dn_max=400, dn_paso=0.5), "error": "más de 400 valores"}, compuerta="c8")
R("Q-08", 6, "bloquea", "De máximo no negativo", "De máximo ≥ 0 (0 = se calcula el mínimo que entra).", "PRG",
  "De máximo negativo.", "No busca.", "Corrige.", "validar_busqueda", "validarBusqueda",
  "Búsqueda: el De máximo no puede ser negativo (0 = se calcula).", [], {"busqueda": O(de_max=-1), "error": "De máximo no puede ser negativo"},
  compuerta="c8")
R("B-08", 6, "bloquea", "Búsqueda: posición radial distinta", "Cada devanado en una posición radial distinta.", "PRG",
  "No se puede dar: la posición es fija.", "—", "Se puede borrar.", "buscar_combinaciones", "buscarCombinaciones",
  "Cada devanado debe ir en una posición radial distinta.", revision="sin-uso", compuerta="c8")
R("Q-09", 6, "descarta", "Densidad fuera del rango", "Se descarta el conductor si J máxima queda fuera de J mín … J máx.",
  "TC", "Conductor chico o grande.", "No aparece en los resultados.", "—", "candidatos_devanado", "candidatosDevanado",
  "deja la densidad máxima entre",
  [], {"busqueda": O(jmin=4.99, jmax=5.0), "aviso": "deja la densidad máxima entre"}, compuerta="c8")
R("Q-10", 6, "descarta", "No entra en la ventana o en sus capas fijas",
  "Se descarta si no cabe ni una espira por capa, o si francés no entra en 2 capas o hélice en 1.", "TU",
  "Ventana chica.", "No aparece.", "—", "candidatos_devanado", "candidatosDevanado",
  {"py": "(v[\"capas_fijas\"] and not v[\"entra_fijas\"])", "js": "v.capas_fijas && !v.entra_fijas"}, compuerta="c8")
R("Q-11", 6, "descarta", "N con error de relación > 0,5 %", "Se descartan las espiras de referencia con error > 0,5 % (de 0,3 a 0,5 sí entran, en rojo).",
  "TU", "Tensiones que no dan espiras enteras.", "Aviso si no queda ninguna.", "—", "buscar_combinaciones", "buscarCombinaciones",
  {"py": "ok = err_max <= ERROR_RELACION_MAX", "js": "errMax <= ERROR_RELACION_MAX"}, compuerta="c8")
R("Q-20", 6, "aviso", "Algunos Dn sin espiras enteras", "Si solo algunos Dn del rango no tienen N entero con B en el rango, avisa cuántos se saltaron.",
  "TC", "Rango de B angosto para parte de los Dn.", "Aviso; los demás Dn sí se usan.", "—", "explicar_busqueda", "explicarBusqueda",
  "Dn no tienen espiras enteras con B en el rango y se saltaron.", compuerta="c8")
R("Q-21", 6, "aviso", "Ningún N con error de relación admisible",
  "Si todos los N enteros que dejan B en el rango tienen error de relación > 0,5 %, avisa con los 3 primeros.", "TU",
  "Tensiones que no salen con espiras enteras.", "Aviso; no hay resultados.", "Revisa tensiones o amplía el rango de B.",
  "explicar_busqueda", "explicarBusqueda", "Con las espiras enteras que dejan B en el rango, el error de relación pasa de ",
  compuerta="c8")
R("Q-12", 6, "descarta", "B sin espiras enteras en el rango", "Si ningún N entero deja B entre B mín y B máx, ese Dn se salta.",
  "TC", "Rango de B angosto.", "Aviso con las B de las espiras vecinas.", "—", "buscar_combinaciones / explicar_busqueda",
  "buscarCombinaciones / explicarBusqueda", "una cantidad entera de espiras que deje B entre", [],
  {"busqueda": O(bmin=1.6, bmax=1.7), "aviso": "no hay una cantidad entera de espiras"}, compuerta="c8")
R("Q-13", 6, "descarta", "No entra en el De máximo", "Con De máximo > 0 se descarta si Ø total + entre fases > De máximo.",
  "PRG", "De máximo chico.", "Aviso si se descartan todas.", "—", "buscar_combinaciones", "buscarCombinaciones",
  "Ninguna combinación entra en De = ", [], {"busqueda": O(de_max=300), "aviso": "Ninguna combinación entra en De"},
  compuerta="c8")
R("Q-14", 6, "descarta", "Vcc fuera de la tolerancia", "Se descarta si |Vcc − objetivo| > objetivo x tolerancia.", "TU",
  "Vcc objetivo inalcanzable.", "Aviso con el rango de Vcc que sí se alcanza.", "Cambia canal, Hc o tipos.",
  "buscar_combinaciones", "buscarCombinaciones", "El Vcc que se alcanza va de ", [],
  {"busqueda": O(vcc=20, tol=1), "aviso": "El Vcc que se alcanza va de"}, compuerta="c8")
R("Q-15", 6, "aviso", "Ningún Dn del rango sirve",
  "Si el núcleo no es válido para ningún Dn, avisa que revises los anchos.", "PRG",
  "Hc en 0 en el diseño (o anchos ≥ Dn).", "Aviso; el texto solo nombra los anchos.",
  "Mejorar el texto: «revisa Hc y los anchos de escalón».", "explicar_busqueda", "explicarBusqueda",
  "Ningún Dn del rango sirve: revisa que los anchos de escalón sean menores que Dn.", [["hc", 0]],
  {"busqueda": O(), "aviso": "Ningún Dn del rango sirve"}, revision="dudoso",
  nota="Con Hc = 0 el diseño ya avisa (N-01), pero la búsqueda culpa a los anchos.", compuerta="c8")
R("Q-16", 6, "aviso", "Devanado III fijo no entra", "El Devanado III no se optimiza: si no entra con esas espiras, ese N se descarta.",
  "PRG", "Devanado III con potencia y ventana chica.", "Aviso.", "Ajusta el Devanado III.", "explicar_busqueda", "explicarBusqueda",
  "(no se optimiza: va como está en la tabla) no entra en la ventana con esas espiras.", compuerta="c8")
R("Q-17", 6, "descarta", "Platina sin papel: solo alambres", "Sin papel de platina digitado, la búsqueda prueba solo alambres.",
  "DEV", "Papel vacío.", "Aviso.", "Digita el papel para probar platinas.", "candidatos_devanado", "candidatosDevanado",
  {"py": "sin papel de platina digitado, solo se probaron alambres.", "js": "sin papel de platina digitado, solo se probaron alambres."},
  compuerta="c8")
R("Q-22", 6, "decide", "Búsqueda aparte del diseño",
  "La búsqueda tiene sus propias condiciones, Dn y De: no cambia el diseño ni su semáforo. «Usar» pasa Dn, anchos, "
  "De, tipo, conductor y arreglo; no toca la B objetivo ni las demás condiciones del diseño.", "TU",
  "Siempre.", "La búsqueda se puede probar sin mover el diseño.", "—", "aplicar_alternativa / leer_busqueda",
  "aplicarAlternativa / opcionesBusqueda", {"py": "n[\"de\"] = alt[\"de\"]", "js": "n.de = alt.de;"},
  compuerta="c8", nota="Antes el Dn y el De de la búsqueda estaban enlazados con el núcleo del paso 2 y su B máxima con la B objetivo.")
R("Q-23", 6, "aviso", "B máxima de la búsqueda distinta de la B objetivo",
  "Si la B máxima de la búsqueda no es la B objetivo del diseño, avisa que el diseño puede dar otras espiras y que esas "
  "alternativas no se verifican ni se pueden usar.", "TU", "B máxima de la búsqueda cambiada.", "Aviso; «Usar» solo en las verificadas.",
  "Pon la misma B en los dos si quieres usar las alternativas.", "explicar_busqueda", "explicarBusqueda",
  "no es la B objetivo del diseño", [], {"busqueda": O(bmax=1.75), "aviso": "no es la B objetivo del diseño"}, compuerta="c8")
R("Q-24", 6, "decide", "Espiras de la búsqueda = las del diseño",
  "Para cada Dn, la búsqueda usa las mismas espiras que daría el diseño: REDONDEO.MAS con la B máxima; si con ellas la B "
  "queda bajo la B mínima, ese Dn se salta.", "TU", "Siempre.", "Las alternativas se pueden cargar en el diseño tal cual.", "—",
  "buscar_combinaciones", "buscarCombinaciones",
  {"py": "for N in ([n_lo] if n_lo <= n_hi else []):", "js": "for (const N of nLo <= nHi ? [nLo] : [])"}, compuerta="c8",
  nota="Antes probaba todas las espiras enteras con B en el rango y «Usar» las fijaba a mano.")
R("Q-18", 6, "decide", "Anchos óptimos para otro Dn", "Mismo Dn del diseño: sus anchos; otro Dn: anchos óptimos de la tabla redondeados a 5 mm y decrecientes.",
  "NUC", "Dn distinto del diseño.", "Núcleo de cada alternativa.", "—", "anchos_para_dn", "anchosParaDn",
  {"py": "a = math.floor(dn * c / 5 + 0.5) * 5", "js": "let a = Math.round(dn * c / 5) * 5"}, compuerta="c8")
R("Q-19", 6, "decide", "Cada alternativa verificada", "Las primeras alternativas se recalculan con el diseño completo y se marcan «verificado».",
  "TU", "Siempre.", "Garantiza que la búsqueda y el diseño dan lo mismo.", "—", "buscar_combinaciones", "buscarCombinaciones",
  {"py": "r[\"verificado\"] = (not v[\"errores\"]", "js": "verificado"}, compuerta="c8")
R("H-14", 6, "hueco", "Dos caminos de cálculo en Python",
  "En Python, la pantalla (calcular_todo) repite el flujo de calcular_datos en vez de llamarlo.", "PRG",
  "Un cambio hecho en uno solo de los dos.", "La pantalla y la búsqueda podrían dar números distintos.",
  "Hoy la prueba «calcular_datos = pantalla» lo vigila; conviene que calcular_todo llame a calcular_datos.",
  "calcular_todo / calcular_datos", "—", {"py": "def calcular_todo():", "js": "function calcularTodo"}, revision="dudoso")


# Origen de cada dato de la pantalla: (campo, rótulo, paso, origen). El valor inicial se lee del programa.
ORIGEN_DATOS = [
    ("codigo", "Código", 1, "NUC"), ("frec", "Frecuencia (Hz)", 1, "ESP"), ("rep", "Reparto de carga", 1, "ESP"),
    ("pasos", "N° de pasos", 1, "DE"), ("variacion", "% de variación", 1, "DE"), ("tap", "Tap nominal", 1, "DE"), ("vcc_obj", "Vcc objetivo (%)", 1, "SF"), ("vcc_tol", "Tolerancia del Vcc (± %)", 1, "SF"),
    ("dev.*.kva", "Potencia (kVA)", 1, "DE"), ("dev.*.kva2", "2ª potencia", 1, "DE"), ("dev.*.volt", "Tensión (V)", 1, "DE"),
    ("dev.*.volt2", "2ª tensión", 1, "DE"), ("dev.*.conex", "Grupo", 1, "DE"), ("dev.*.conex2", "2º grupo", 1, "DE"),
    ("dev.*.bil", "BIL (kV)", 1, "DE"), ("dev.*.industrial", "Prueba industrial (kV)", 1, "ESF"),
    ("dn", "Dn (mm)", 2, "REF"), ("de", "De (mm)", 2, "REF"), ("hc", "Hc (mm)", 2, "NUC"), ("g", "Traslape g (mm)", 2, "NUC"),
    ("anchos", "Anchos de escalón (mm) · óptimos de tabla para Dn 259", 2, "NUC"), ("bobj", "B máxima (T)", 2, "TC"),
    ("fa", "Factor de apilamiento", 2, "REF"), ("b_min", "B mínima (T)", 2, "TC"),
    ("fconst", "Factor de construcción", 2, "PER"), ("tref", "T° de referencia (°C)", 2, "SUP"),
    ("dev.*.calibre", "Calibre", 3, "DE"), ("dev.*.cant", "Cantidad de conductores", 3, "DE"), ("dev.*.horiz", "Horizontales", 3, "DE"),
    ("dev.*.tipo", "Tipo de devanado", 3, "REF"), ("dev.*.papel", "Papel de platina", 3, "REF"), ("dev.*.papel_capa", "Papel entre capas", 3, "REF"),
    ("dev.*.modo", "Modo de capas", 3, "PRG"), ("dev.*.capas", "N° de capas (a mano)", 3, "SF"), ("dev.*.epc", "Espiras por capa (a mano)", 3, "SF"),
    ("dev.*.n_canales", "N° de canales internos", 3, "REF"), ("dev.*.canal_mm", "Medida de canales internos", 3, "REF"),
    ("dev.*.transp", "Transposiciones", 3, "SUP"), ("j_max", "J máxima (A/mm²)", 3, "TC"),
    ("dev.*.canal", "Canal interior (mm)", 4, "REF"), ("dev.*.yugo", "Distancia mínima al yugo (mm)", 4, "REF"),
    ("dev.*.relleno", "Relleno de los extremos (mm)", 4, "ESF"), ("tubo", "Tubo enrollado exterior (mm)", 4, "REF"),
    ("fases", "Entre fases mínimo (mm)", 4, "SUP"), ("barrera", "Barrera entre bobinas", 4, "ESF"), ("e_barrera", "Espesor de la barrera (mm)", 4, "ESF"),
    ("tubo_rigido", "Tubo rígido: largo extra (mm)", 4, "ESF"), ("tubo_nucleo", "Tubo núcleo–bobina (mm)", 4, "ESF"),
]
# Constantes y tablas: (nombre en el código, qué es, origen)
CONSTANTES = [
    ("K_FEM", "4,44 de E = 4,44·f·N·B·A", "FIS"), ("FACTOR_ELIPSE", "Factor elipse K del núcleo (circular, fijo)", "NUC"), ("T_CHAPA", "Espesor de plancha M4 (mm)", "NUC"),
    ("RHO_FE", "Densidad del fierro (kg/m³)", "NUC"), ("COEFICIENTES_ANCHO", "Anchos óptimos por N° de escalones", "NUC"),
    ("ALAMBRES", "Alambres de stock: sección y Ø esmaltado", "DEV"), ("PLATINAS", "Platinas de stock: espesor x ancho", "DEV"),
    ("TIPOS", "Reglas de cada tipo de devanado", "DEV"), ("SEPARACION_GALLETA", "Separación entre galletas (mm)", "DEV"),
    ("FACTOR_SECCION_PLATINA", "Factor de sección de la platina", "DE"), ("RHO_CU_20", "Resistividad del cobre a 20 °C (Ω·mm²/m)", "PES"),
    ("DENS_CU", "Densidad del cobre (kg/dm³)", "PES"), ("K_VCC", "K de la fórmula de Vcc", "VCC"),
    ("TABLA_ROGOWSKI", "Cuadro de Rogowski (A desde, kR)", "VCC"), ("TABLA_PERDIDAS", "Tabla de pérdidas de la chapa M4 0.27 mm (B, W/kg 50 y 60 Hz)", "PER"),
    ("AUMENTO_B_PERDIDAS", "B extra para leer pérdidas (T)", "PER"), ("ERROR_RELACION_AVISO", "Error de relación: rojo desde (%)", "TU"),
    ("ERROR_RELACION_MAX", "Error de relación: máximo (%)", "TU"), ("ESFUERZO_BOB_BOB", "Bobina–bobina máx. (kV/mm)", "ESF"),
    ("ESFUERZO_BOB_NUC", "Núcleo–bobina (kV/mm)", "ESF"), ("ESFUERZO_BOB_NUC_MAX", "Núcleo–bobina máx. (kV/mm)", "ESF"),
    ("FACTOR_RADIAL_CONTORNO", "Fracción del radial en el contorno", "ESF"), ("BARRERAS", "Barreras posibles", "ESF"),
    ("ORDEN_RADIAL", "Orden radial del núcleo hacia afuera", "TU"), ("FASES", "Fases", "FIS"),
]


def guardar(ruta):
    for r in REGLAS:
        r["paso_nombre"] = PASOS[r["paso"]]
        r["origen_nombre"] = ORIGENES[r["origen"]]
    ids = [r["id"] for r in REGLAS]
    assert len(ids) == len(set(ids)), "ids repetidos"
    pathlib.Path(ruta).write_text(json.dumps({"reglas": REGLAS, "origenes": ORIGENES, "pasos": PASOS,
                                              "compuertas": COMPUERTAS, "origen_datos": ORIGEN_DATOS,
                                              "constantes": CONSTANTES}, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    guardar(pathlib.Path(__file__).with_name("reglas.json"))
    print(len(REGLAS), "reglas")
