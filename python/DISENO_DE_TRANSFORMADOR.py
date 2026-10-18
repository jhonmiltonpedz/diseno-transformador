# DISEÑO DE TRANSFORMADOR  (DATOS DEL CLIENTE -> NÚCLEO -> DEVANADOS -> DISTANCIAS ELÉCTRICAS)
# Une la hoja de núcleo y la hoja de devanado en una sola hoja de diseño.
# El NÚCLEO es el que limita: la altura de ventana Hc limita la altura de las bobinas y la distancia
# entre ejes De limita su diámetro (las bobinas de fases vecinas no se deben chocar). Por eso el diseño
# sigue este orden, y la pantalla también:
#   1. DATOS DEL CLIENTE -> potencia, tensiones, grupos, BIL y prueba industrial de cada devanado; frecuencia,
#                     reparto de carga y regulación (N° de pasos, % de variación, tap nominal). Con ellos, las
#                     corrientes de línea y de fase.
#   2. NÚCLEO      -> Dn, De, Hc y escalones: sección neta, V/espira, inducción real, corte, peso y
#                     pérdidas en el núcleo (vacío): Pfe sale de la regresión cuadrática de la tabla de la chapa
#                     M4 0.27 mm con B = B real + 0.099 y la frecuencia; P0 = Pfe x peso x factor de construcción.
#   3. DEVANADOS   -> se construyen DENTRO de la ventana: con "Ajustar a la ventana" las espiras por capa
#                     salen de la altura que deja el núcleo (Hc - 2 x distancia mínima al yugo) y de ahí
#                     el N° de capas, el radial y los diámetros. (También se pueden dar las capas o las
#                     espiras por capa a mano: entonces se verifica que entren.)
#   4. DISTANCIAS ELÉCTRICAS (aislamiento mayor) -> con el núcleo y los devanados ya fijos, lo que queda:
#                     distancia real al yugo de cada devanado y distancia real entre fases, comparadas con
#                     los mínimos. Si algo no entra, el programa dice cuántos mm faltan.
#   Luego: peso de cobre, resistencia, pérdidas I²R y Vcc (misma fórmula de la hoja de Excel).
#   BÚSQUEDA POR Vcc (opcional) -> con el Vcc objetivo y las condiciones (densidad de corriente, rango de inducción,
#                     Dn fijo o en un rango, De máximo) da las combinaciones de conductores y el Dn que cumplen,
#                     cada una verificada con el cálculo completo y lista para usarla en el diseño.
#
# Aislamiento MAYOR = entre partes distintas: núcleo-devanado y devanado-devanado (canal interior),
#                     devanado-yugo, tubo enrollado y entre fases.
# Aislamiento MENOR = dentro de un mismo devanado: papel de la platina (entre espiras), papel entre capas
#                     y canales internos de refrigeración.
#
# Devanados con dos tensiones
#   - Las espiras de referencia salen de la MENOR tensión de fase de toda la tabla.
#   - Cada tensión tiene sus espiras = tensión de fase / voltios por espira.
#   - El devanado se construye con las espiras de la tensión que necesita más; la otra es una derivación.
#   - El conductor es uno solo: la tabla muestra la densidad con la corriente de cada tensión.
#   - Resistencia, pérdidas y Vcc se calculan con la primera tensión de cada devanado.
#   - El Devanado I es el principal: lleva la regulación (taps), sobre su primera tensión.
#
# Origen de los datos de la pantalla (cada uno sale de su fuente; lo que no tiene fuente queda VACÍO y se digita):
#   - Diseño de referencia ........... núcleo Dn 259 / De 510 (con B objetivo 1.73 salen 6 espiras de referencia,
#                                      B real 1.729 T); anchos = los óptimos de tabla para Dn 259; factor de
#                                      apilamiento 0.97, tubo enrollado 1 mm y, en cada devanado, tipo, papeles,
#                                      canales internos, canal interior y distancia al yugo (ver VALORES_TABLA)
#   - Supuestos por validar .......... T° de referencia 75 °C (IEC 60076-1), entre fases mínimo 9 mm (el que resulta
#                                      en el diseño de referencia) y 3 transposiciones en el Devanado II (las que
#                                      caben en Hc = 440)
#   - Hoja de núcleo ................. código, Hc, traslape g, factor elipse K = 1 (fijo, ya no se digita),
#                                      plancha 0.27 mm, 7650 kg/m³ y la tabla de anchos óptimos
#   - Hoja de devanado ............... alambres y platinas de stock, reglas de cada tipo de devanado, separación
#                                      entre galletas (20 mm), sección de la platina = espesor x ancho
#   - Hoja de datos de entrada ....... sección de la espira con platina = sección x cantidad x 0.97; potencia,
#                                      tensiones, grupos, BIL, calibre, cantidad y horizontales de cada devanado;
#                                      N° de pasos, % de variación y tap nominal
#   - Especificaciones del cliente ... frecuencia (60 Hz) y reparto de carga (100-0)
#   - Hoja de cálculo de Vcc ......... K = 0.018 y el cuadro de kR por corriente
#   - Curva de pérdidas de la chapa .. tabla de la chapa M4 0.27 mm, regresión cuadrática (polinomio de grado 2) y
#                                      factor de construcción (1 = sin factor); las pérdidas se leen con B real + 0.099
#   - Tus condiciones ................ J máxima 4.7 A/mm² (paso 3) y B entre 1.65 y 1.73 T (paso 2; la B máxima es la
#                                      inducción objetivo del diseño). Son las condiciones del semáforo del diseño.
#   - Sin fuente (se digitan) ........ Vcc objetivo y tolerancia del diseño (paso 1; vacíos = no se verifican) y, en
#                                      la búsqueda, Vcc objetivo, tolerancia, J mínima, Dn y De
#   La BÚSQUEDA POR Vcc va aparte: sus condiciones, Dn y De son propios y no cambian el diseño ni su semáforo;
#   solo «USAR EN EL DISEÑO» pasa la alternativa elegida.
#   Mientras falte uno de esos datos, el programa no calcula y dice cuáles faltan.
#
# Cómo se ubican los conductores en la espira:
#   CANTIDAD     = conductores en paralelo por espira
#   HORIZONTALES = filas de conductores de la espira  -> dirección AXIAL
#   RADIALES     = CANTIDAD / HORIZONTALES (columnas o "verticales") -> dirección RADIAL
import copy
import math
import re
import ipywidgets as widgets
from IPython.display import display, HTML
from datetime import datetime

# =====================================================================
# 1. CONDUCTORES DE STOCK Y REGLAS DE FABRICACIÓN
# =====================================================================
# Alambre esmaltado: calibre -> (sección de cobre mm², diámetro esmaltado mm)
# El diámetro esmaltado ya es la medida final: el alambre NO lleva papel.
ALAMBRES = {
    8: (8.36, 3.44),
    9: (6.63, 3.08),
    10: (5.26, 2.72),
    11: (4.17, 2.45),
    12: (3.30, 2.18),
    13: (2.62, 1.98),
    14: (2.08, 1.75),
    15: (1.65, 1.565),
    16: (1.309, 1.41),
    17: (1.038, 1.25),
    18: (0.823, 1.12),
    19: (0.652, 1.025),
    20: (0.517, 0.905),
    21: (0.410, 0.80),
    22: (0.325, 0.72),
    23: (0.258, 0.655),
    24: (0.204, 0.58),
    25: (0.162, 0.52),
    26: (0.128, 0.45),
    27: (0.102, 0.41),
}

# Platina CALATA: (espesor, ancho) en mm. Es la única que se envuelve con papel.
#   espesor -> dirección RADIAL (espesor de la espira)
#   ancho   -> dirección AXIAL  (ancho de la espira)
PLATINAS = [
    (1.8, 10.0),
    (1.8, 12.0),
    (2.5, 12.0),
    (3.5, 12.0),
    (3.5, 14.0),
    (3.5, 15.5),
]

# Sección de cobre de la platina: espesor x ancho (como la hoja de devanado): 3.5 x 14 -> 49 mm²
def seccion_platina(espesor, ancho):
    return espesor * ancho


# Sección TOTAL de la espira: con platina se multiplica por 0.97 (como la hoja de datos de entrada:
# 12 platinas 3.5 x 14 -> 49 x 12 x 0.97 = 570.36 mm²); con alambre, sección x cantidad.
FACTOR_SECCION_PLATINA = 0.97


def seccion_espira(conductor, seccion, cantidad):
    return seccion * cantidad * (FACTOR_SECCION_PLATINA if conductor == "PLATINA" else 1.0)


#   max_cond : máximo de conductores por espira
#   max_h    : máximo de horizontales
#   h_fijo   : horizontales fijas (None = libre hasta max_h)
#   radiales : radiales permitidas (None = libre)
#   secciones: devanados apilados en el mismo eje (galleta = 2)
#   capas_fijas: capas que siempre lleva (FRANCÉS = 2; HÉLICE = 1, una sola capa; sin la clave = libre)
TIPOS = {
    # 1 radial fijo: 1x1, 2x2, 3x3
    "CONTINUO":      {"max_cond": 3,  "max_h": 3, "h_fijo": None, "radiales": (1,),   "secciones": 1},
    # 2 devanados en el mismo eje, cada uno se comporta como un continuo
    "GALLETA":       {"max_cond": 3,  "max_h": 3, "h_fijo": None, "radiales": (1,),   "secciones": 2},
    # divisor de corriente: 2 o 3 verticales, hasta 6 horizontales
    "FRANCÉS":       {"max_cond": 18, "max_h": 6, "h_fijo": None, "radiales": (2, 3), "secciones": 1, "capas_fijas": 2},
    "HÉLICE SIMPLE": {"max_cond": 24, "max_h": 2, "h_fijo": 2,    "radiales": None,   "secciones": 1, "capas_fijas": 1},
    "HÉLICE DOBLE":  {"max_cond": 48, "max_h": 4, "h_fijo": 4,    "radiales": None,   "secciones": 1, "capas_fijas": 1},
}
SEPARACION_GALLETA = 20.0   # mm axiales entre las 2 galletas
DECIMALES_REDONDEO = 0      # REDONDEO.MAS(x; 0) -> mm enteros
MAX_DEVANADOS = 3           # máximo de devanados radiales (concéntricos) por columna

# Devanados eléctricos de la tabla de DATOS DE ENTRADA (mismas columnas que la hoja de Excel)
CLAVES = ["I", "II", "III"]
NOMBRES = {"I": "Devanado I", "II": "Devanado II", "III": "Devanado III"}
COLORES = {"I": "#c87533", "II": "#8cc08c", "III": "#7fa8d1"}
PRINCIPAL = "I"             # el Devanado I es el principal: lleva la regulación (taps)
GRUPOS = ["D", "Y", "YN"]

# Constantes de cálculo
K_FEM = 4.44                # E = 4.44 · f · N · B · A
FACTOR_ELIPSE = 1           # núcleo circular: factor elipse K = 1 (hoja de núcleo); ya no se digita
T_CHAPA = 0.27              # mm, plancha M4 0.27 mm
RHO_FE = 7650.0             # kg/m³
RHO_CU_20 = 0.017241        # Ω·mm²/m a 20 °C
DENS_CU = 8.9               # kg/dm³
# Vcc como en la hoja de Excel: constante K (con B en kilogauss, Sfe en cm² y medidas en mm)
K_VCC = 0.018
# Cuadro de Rogowski: (corriente de fase desde, kR)
TABLA_ROGOWSKI = [(1, 0.96), (501, 0.98), (631, 1.02), (1001, 1.05), (1501, 1.10), (2501, 1.15)]
FASES = 3
ERROR_RELACION_MAX = 0.5    # % admisible en la relación de transformación
# Error de relación: hasta 0.3 % cumple; de 0.3 a 0.5 % se marca en rojo pero procede; más de 0.5 % no procede
ERROR_RELACION_AVISO = 0.3


def redondeo_mas(x, decimales=DECIMALES_REDONDEO):
    """Igual que REDONDEO.MAS de Excel (valores positivos)."""
    f = 10 ** decimales
    return math.ceil(round(x * f, 6)) / f


# =====================================================================
# 2. NÚCLEO  (misma lógica de la hoja de núcleo)
# =====================================================================
COEFICIENTES_ANCHO = {
    1: [0.707],
    2: [0.85, 0.526],
    3: [0.906, 0.707, 0.424],
    4: [0.934, 0.796, 0.605, 0.356],
    5: [0.95, 0.846, 0.707, 0.534, 0.313],
    6: [0.959, 0.875, 0.768, 0.64, 0.483, 0.281],
    7: [0.967, 0.898, 0.812, 0.707, 0.584, 0.436, 0.255],
    8: [0.972, 0.91, 0.842, 0.755, 0.657, 0.541, 0.417, 0.239],
    9: [0.977, 0.929, 0.867, 0.794, 0.707, 0.608, 0.498, 0.37, 0.214],
    10: [0.979, 0.93, 0.884, 0.823, 0.748, 0.662, 0.578, 0.468, 0.346, 0.204]
}


MSG_DE = "Núcleo: la distancia entre ejes De debe ser mayor que el diámetro Dn (De va de centro a centro de las columnas)."


def validar_nucleo(dn, g, de, hc, k_elipse, anchos):
    errores = []
    if dn <= 0 or de <= 0 or hc <= 0:
        errores.append("Núcleo: Dn, De y Hc deben ser mayores que 0.")
    if not anchos:
        errores.append("Núcleo: ingresa al menos un ancho de escalón.")
    elif dn > 0 and max(anchos) >= dn:
        errores.append("Núcleo: los anchos de escalón deben ser menores que el diámetro Dn.")
    return errores


def calcular_nucleo(dn, g, de, hc, k_elipse, anchos, factor_apilamiento=1.0):
    """Corte y peso del núcleo. Además devuelve la sección para el cálculo de V/espira."""
    escalones = []
    suma_chapas_previas = 0
    espesor_total = 0.0
    peso_total = 0.0
    seccion_bruta = 0.0

    # DETECCIÓN AUTOMÁTICA DE ESCALONES ACTIVOS
    n_real_esc = len(anchos)

    for i, ancho in enumerate(anchos):
        if ancho == 0:
            continue

        # 1. Altura geométrica en la elipse/círculo
        y_geom = dn * k_elipse * math.sqrt(max(1.0 - (ancho / dn) ** 2, 0.0))

        # 2. Acumulado total de chapas (múltiplo de 10)
        chapas_acum_teoricas = int(round((y_geom / T_CHAPA) / 10.0) * 10)

        # 3. Chapas exclusivas del escalón
        chapas_esc = chapas_acum_teoricas - suma_chapas_previas
        if chapas_esc < 0:
            chapas_esc = 0

        # 4. Espesor real del escalón
        esp_esc = round(chapas_esc * T_CHAPA, 2)
        suma_chapas_previas += chapas_esc
        espesor_total += esp_esc

        # --- REGLAS DE CORTE ---
        an = anchos[0] + hc + ancho
        cn = (2.0 * de) + ancho
        e_const = hc + anchos[0]

        # 5. Peso
        area_plancha = (cn * an) - (2.0 * (g ** 2)) - ((cn - 3.0 * ancho) * (an - 2.0 * ancho))
        peso_esc = (area_plancha * esp_esc / 1e9) * RHO_FE
        peso_total += peso_esc

        # 6. Ancho óptimo según la tabla y el número real de escalones
        ancho_optimo = 0.0
        if 1 <= n_real_esc <= 10:
            ancho_optimo = dn * COEFICIENTES_ANCHO[n_real_esc][i]

        seccion_bruta += ancho * esp_esc
        escalones.append({
            "n": i + 1, "ancho": ancho, "ancho_optimo": ancho_optimo, "espesor": esp_esc,
            "chapas": chapas_esc, "A": an, "C": cn, "E": e_const, "peso": peso_esc,
        })

    return {
        "dn": dn, "g": g, "de": de, "hc": hc, "k": k_elipse,
        "escalones": escalones, "peso": peso_total, "espesor_total": espesor_total,
        "seccion_bruta": seccion_bruta,                       # mm²
        "factor_apilamiento": factor_apilamiento,
        "seccion_neta": seccion_bruta * factor_apilamiento,   # mm²
    }


# ---------------------------------------------------------------------
# 2.1 PÉRDIDAS EN EL NÚCLEO (VACÍO)  (regresión de la curva de pérdidas de la chapa)
#   Regresión cuadrática: Pfe = c0 + c1·B + c2·B² (polinomio de grado 2), por
#   mínimos cuadrados sobre la tabla del fabricante, una curva para 50 Hz y otra para 60 Hz.
#   La inducción con que se leen las pérdidas es B = B real + 0.099 T (regla de J. Peralta).
#   Otra frecuencia: Pfe = a·f + b·f² con
#   a = (3600·P50 - 2500·P60) / 30000  y  b = (50·P60 - 60·P50) / 30000.
#   P0 (W) = Pfe (W/kg) x peso del núcleo (kg) x factor de construcción.
# ---------------------------------------------------------------------
MATERIAL_NUCLEO = "chapa M4 de 0.27 mm"
AUMENTO_B_PERDIDAS = 0.099      # T: las pérdidas se leen con B real + 0.099
# (inducción en T, Pfe a 50 Hz en W/kg, Pfe a 60 Hz en W/kg)
TABLA_PERDIDAS = [
    (0.5, 0.10, 0.14), (0.6, 0.15, 0.18), (0.7, 0.18, 0.24), (0.8, 0.23, 0.31), (0.9, 0.29, 0.38),
    (1.0, 0.36, 0.46), (1.1, 0.43, 0.55), (1.2, 0.51, 0.65), (1.3, 0.60, 0.78), (1.4, 0.72, 0.91),
    (1.5, 0.84, 1.10), (1.6, 1.00, 1.30), (1.7, 1.22, 1.58), (1.8, 1.52, 1.96), (1.9, 1.90, 2.50),
]


def minimos_cuadrados(filas, y):
    """Regresión lineal: coeficientes c que minimizan la suma de (filas·c - y)², por QR de Householder.
    (Sumas con lazos explícitos para dar el mismo resultado que la página web.)"""
    a = [list(map(float, f)) for f in filas]
    b = [float(v) for v in y]
    m, n = len(a), len(a[0])
    for j in range(n):
        norma = 0.0
        for i in range(j, m):
            norma += a[i][j] * a[i][j]
        norma = math.sqrt(norma)
        alfa = -norma if a[j][j] > 0 else norma
        v = [0.0] * m
        v[j] = a[j][j] - alfa
        for i in range(j + 1, m):
            v[i] = a[i][j]
        vv = 0.0
        for i in range(j, m):
            vv += v[i] * v[i]
        if vv == 0.0:
            continue
        for k in range(j, n):
            t = 0.0
            for i in range(j, m):
                t += v[i] * a[i][k]
            t = 2.0 * t / vv
            for i in range(j, m):
                a[i][k] -= t * v[i]
        t = 0.0
        for i in range(j, m):
            t += v[i] * b[i]
        t = 2.0 * t / vv
        for i in range(j, m):
            b[i] -= t * v[i]
    c = [0.0] * n
    for j in range(n - 1, -1, -1):
        t = b[j]
        for k in range(j + 1, n):
            t -= a[j][k] * c[k]
        c[j] = t / a[j][j]
    return c


def _ajuste_perdidas(columna):
    filas = [[1.0, b, b * b] for b, _, _ in TABLA_PERDIDAS]
    return minimos_cuadrados(filas, [fila[columna] for fila in TABLA_PERDIDAS])


COEF_PERDIDAS = {50: _ajuste_perdidas(1), 60: _ajuste_perdidas(2)}
B_TABLA_MIN, B_TABLA_MAX = TABLA_PERDIDAS[0][0], TABLA_PERDIDAS[-1][0]


def pfe_curva(f, b):
    """Pfe (W/kg) de la curva ajustada de f Hz (50 o 60) a la inducción b (T)."""
    c = COEF_PERDIDAS[f]
    return c[0] + c[1] * b + c[2] * (b * b)


def perdidas_especificas(b, f):
    """Pfe (W/kg) a la inducción b y la frecuencia f: la curva a 50 o 60 Hz, si no a·f + b·f²."""
    p50, p60 = pfe_curva(50, b), pfe_curva(60, b)
    a = (3600.0 * p50 - 2500.0 * p60) / 30000.0
    bb = (50.0 * p60 - 60.0 * p50) / 30000.0
    pfe = p50 if f == 50 else p60 if f == 60 else a * f + bb * (f * f)
    return {"b": b, "f": f, "p50": p50, "p60": p60, "a": a, "bb": bb, "pfe": pfe}


def calcular_vacio(nuc, elec, w_kg_manual=0.0, factor=1.0):
    """Pérdidas en el núcleo con B = B real + 0.099 y la frecuencia del diseño.
    w_kg_manual > 0 reemplaza a la regresión (por ejemplo, el valor de una prueba)."""
    r = perdidas_especificas(elec["b_real"] + AUMENTO_B_PERDIDAS, elec["frecuencia"])
    r["b_real"] = elec["b_real"]
    manual = w_kg_manual > 0
    r["pfe_regresion"] = r["pfe"]
    if manual:
        r["pfe"] = w_kg_manual
    r.update({
        "manual": manual, "peso": nuc["peso"], "factor": factor, "p0": r["pfe"] * nuc["peso"] * factor,
        "fuera_tabla": not (B_TABLA_MIN - 1e-9 <= r["b"] <= B_TABLA_MAX + 1e-9),
        "fuera_frec": not (50 - 1e-9 <= r["f"] <= 60 + 1e-9),
    })
    return r


# =====================================================================
# 3. CÁLCULO ELÉCTRICO  (a partir de los DATOS DE ENTRADA)
# =====================================================================
def es_estrella(conexion):
    return conexion in ("Y", "YN")


def tension_fase(v_linea, conexion):
    return v_linea / math.sqrt(3) if es_estrella(conexion) else v_linea


def corriente_fase(kva, v_linea, conexion):
    i_linea = kva * 1000.0 / (math.sqrt(3) * v_linea)
    return i_linea if es_estrella(conexion) else i_linea / math.sqrt(3)


def redondear(x):
    """Redondeo al entero más cercano (0.5 hacia arriba), mínimo 1."""
    return max(int(math.floor(x + 0.5)), 1)


def calcular_electrico(specs, frecuencia, tap_nom, variacion, n_pasos, rep_carga,
                       seccion_neta_mm2, b_objetivo, n_ref_manual=0):
    """specs: {clave: {"kva", "volt", "conex", "bil"}} y, si el devanado tiene una segunda tensión,
    además {"volt2", "conex2", "kva2"} (kva2 = 0 -> la misma potencia). Un devanado se usa cuando
    tiene potencia. Devuelve (errores, resultado)."""
    errores = []
    activos = []
    for k in CLAVES:
        s = specs[k]
        if min(s["kva"], s["volt"], s.get("kva2", 0.0), s.get("volt2", 0.0)) < 0:
            errores.append(f"{NOMBRES[k]}: potencias y tensiones no pueden ser negativas.")
        elif s["kva"] > 0 and s["volt"] > 0:
            activos.append(k)
        elif s["kva"] > 0:
            errores.append(f"{NOMBRES[k]}: tiene potencia pero le falta la primera tensión.")
    if PRINCIPAL not in activos:
        errores.append(f"Falta el {NOMBRES[PRINCIPAL]} (principal): ingresa su potencia y su tensión.")
    if len(activos) < 2:
        errores.append("Se necesitan al menos 2 devanados con potencia y tensión.")
    if frecuencia <= 0 or b_objetivo <= 0 or seccion_neta_mm2 <= 0:
        errores.append("Frecuencia, inducción objetivo y sección del núcleo deben ser mayores que 0.")
    if n_pasos < 1 or not (1 <= tap_nom <= n_pasos):
        errores.append(f"Tap: la posición nominal ({tap_nom}) debe estar entre 1 y el N° de pasos ({n_pasos}).")
    if variacion < 0 or (n_pasos >= 1 and variacion * max(n_pasos - tap_nom, 0) >= 100):
        errores.append("Tap: el % de variación no es válido.")
    repartos = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(rep_carga))]
    if not repartos:
        errores.append("Reparto BT: escribe los porcentajes separados por guion, por ejemplo 100-0.")
    if errores:
        return errores, None

    area_m2 = seccion_neta_mm2 / 1e6
    dev = {}
    for k in activos:
        s = specs[k]
        entradas = [(s["volt"], s["conex"], s["kva"])]
        if s.get("volt2", 0.0) > 0:        # segunda tensión del mismo devanado
            entradas.append((s["volt2"], s.get("conex2", s["conex"]),
                             s["kva2"] if s.get("kva2", 0.0) > 0 else s["kva"]))
        tensiones = [{
            "volt": v, "conex": c, "kva": p, "v_fase": tension_fase(v, c),
            "i_linea": p * 1000.0 / (math.sqrt(3) * v), "i_fase": corriente_fase(p, v, c),
        } for v, c, p in entradas]
        t0 = tensiones[0]
        dev[k] = {
            "clave": k, "nombre": NOMBRES[k], "kva": s["kva"], "volt": s["volt"],
            "conex": s["conex"], "bil": s["bil"],
            "v_fase": t0["v_fase"], "i_linea": t0["i_linea"], "i_fase": t0["i_fase"],
            "tensiones": tensiones,
        }

    # Referencia: la menor tensión de fase de toda la tabla (menos espiras -> ahí se redondea)
    ref, t_ref = min(((k, t) for k in activos for t in dev[k]["tensiones"]), key=lambda kt: kt[1]["v_fase"])
    n_teorico = t_ref["v_fase"] / (K_FEM * frecuencia * b_objetivo * area_m2)
    n_ref = int(n_ref_manual) if n_ref_manual and n_ref_manual > 0 else int(redondeo_mas(n_teorico, 0))
    v_esp = t_ref["v_fase"] / n_ref
    b_real = v_esp / (K_FEM * frecuencia * area_m2)

    # Espiras de cada tensión. El devanado se construye con las de la tensión que necesita más.
    for k in activos:
        d = dev[k]
        for t in d["tensiones"]:
            t["n"] = n_ref if t is t_ref else redondear(t["v_fase"] / v_esp)
            t["error"] = (t["n"] * v_esp - t["v_fase"]) / t["v_fase"] * 100.0
        d["n_nom"] = d["tensiones"][0]["n"]
        d["n_max"] = max(t["n"] for t in d["tensiones"])
        d["i_max"] = max(t["i_fase"] for t in d["tensiones"])
        d["error"] = d["tensiones"][0]["error"]

    # Regulación (taps) en el devanado principal, sobre su primera tensión: posición 1 = mayor tensión
    at = dev[PRINCIPAL]
    taps = []
    for p in range(1, n_pasos + 1):
        factor = 1.0 + (tap_nom - p) * variacion / 100.0
        v_l = at["volt"] * factor
        v_f = tension_fase(v_l, at["conex"])
        n_p = at["n_nom"] if p == tap_nom else redondear(v_f / v_esp)
        v_f_real = n_p * v_esp
        taps.append({
            "pos": p, "pct": (factor - 1.0) * 100.0, "v_linea": v_l, "v_fase": v_f, "espiras": n_p,
            "v_linea_real": v_f_real * (math.sqrt(3) if es_estrella(at["conex"]) else 1.0),
            "error": (v_f_real - v_f) / v_f * 100.0,
            "i_fase": corriente_fase(at["kva"], v_l, at["conex"]),
        })
    at["n_max"] = max(at["n_max"], max(t["espiras"] for t in taps))
    at["i_max"] = max(at["i_max"], max(t["i_fase"] for t in taps))

    # Reparto de carga: % de la potencia del principal que toma cada secundario (en el orden II, III)
    secundarios = [k for k in activos if k != PRINCIPAL]
    carga_total = 0.0
    for idx, k in enumerate(secundarios):
        pct = repartos[idx] if idx < len(repartos) else 0.0
        kva_carga = pct / 100.0 * at["kva"]
        dev[k]["reparto"] = pct
        dev[k]["kva_carga"] = kva_carga
        dev[k]["i_carga"] = corriente_fase(kva_carga, dev[k]["volt"], dev[k]["conex"])
        carga_total += kva_carga
    at["reparto"] = sum(dev[k]["reparto"] for k in secundarios)
    at["kva_carga"] = carga_total
    at["i_carga"] = corriente_fase(carga_total, at["volt"], at["conex"])

    return [], {
        "activos": activos, "secundarios": secundarios, "dev": dev, "ref": ref, "ref_volt": t_ref["volt"],
        "n_teorico": n_teorico, "n_ref": n_ref, "n_ref_manual": bool(n_ref_manual and n_ref_manual > 0),
        "v_esp": v_esp, "b_real": b_real, "b_objetivo": b_objetivo, "frecuencia": frecuencia,
        "seccion_neta": seccion_neta_mm2,
        "taps": taps, "tap_nom": tap_nom, "variacion": variacion, "n_pasos": n_pasos,
        "rep_carga": str(rep_carga),
    }


def resumen_entrada(specs, cond):
    """Lo que calcula la tabla de DATOS DE ENTRADA: por devanado, la sección de la espira y, por cada
    tensión, I línea, I fase y densidad. cond: {clave: {"conductor", "medida", "cantidad", "horizontales"}}.
    Un devanado sin potencia queda con corrientes en 0, como en la hoja de Excel."""
    salida = {}
    for k in CLAVES:
        s, c = specs[k], cond[k]
        if c["conductor"] == "PLATINA":
            espesor, ancho = PLATINAS[c["medida"]]
            seccion, calibre, aislante = seccion_platina(espesor, ancho), f"{espesor:g}x{ancho:g}", "PAPEL"
        else:
            seccion, calibre, aislante = ALAMBRES[c["medida"]][0], f"{c['medida']}", "ESMALTE"
        seccion_total = seccion_espira(c["conductor"], seccion, c["cantidad"])
        columnas = []
        for volt, conex, kva in ((s["volt"], s["conex"], s["kva"]),
                                 (s.get("volt2", 0.0), s.get("conex2", s["conex"]),
                                  s["kva2"] if s.get("kva2", 0.0) > 0 else s["kva"])):
            usada = s["kva"] > 0 and kva > 0 and volt > 0
            i_linea = kva * 1000.0 / (math.sqrt(3) * volt) if usada else 0.0
            i_fase = corriente_fase(kva, volt, conex) if usada else 0.0
            columnas.append({"volt": volt, "conex": conex, "kva": kva, "usada": usada,
                             "i_linea": i_linea, "i_fase": i_fase,
                             "densidad": i_fase / seccion_total if seccion_total > 0 else 0.0})
        salida[k] = {
            "activo": s["kva"] > 0 and s["volt"] > 0, "bil": s["bil"], "calibre": calibre,
            "aislante": aislante, "cantidad": c["cantidad"], "horizontales": c["horizontales"],
            "seccion": seccion_total, "columnas": columnas,
        }
    return salida


# =====================================================================
# 4. DEVANADO  (misma lógica de la hoja de devanado)
# =====================================================================
def validar(tipo, cantidad, horizontales, n_espiras, esp_por_capa):
    """Devuelve la lista de reglas de fabricación que no se cumplen (vacía = OK)."""
    r = TIPOS[tipo]
    errores = []
    if cantidad < 1 or horizontales < 1:
        return ["La cantidad de conductores y las horizontales deben ser al menos 1."]
    if cantidad > r["max_cond"]:
        errores.append(f"{tipo}: máximo {r['max_cond']} conductores por espira (ingresaste {cantidad}).")
    if r["h_fijo"] is not None and horizontales != r["h_fijo"]:
        errores.append(f"{tipo}: las horizontales son fijas = {r['h_fijo']}.")
    elif horizontales > r["max_h"]:
        errores.append(f"{tipo}: máximo {r['max_h']} horizontales.")
    if cantidad % horizontales:
        errores.append(f"{cantidad} conductores no se reparten en {horizontales} horizontales "
                       f"(la cantidad debe ser múltiplo de las horizontales).")
    else:
        radiales = cantidad // horizontales
        if r["radiales"] == (1,) and radiales != 1:
            errores.append(f"{tipo}: 1 radial fijo, solo se permite 1x1, 2x2 o 3x3.")
        elif r["radiales"] and radiales not in r["radiales"]:
            permitidas = " o ".join(str(v) for v in r["radiales"])
            errores.append(f"{tipo}: se permiten {permitidas} verticales (radiales); "
                           f"{cantidad} = {horizontales} x {radiales} da {radiales}.")
    if n_espiras < 1 or esp_por_capa < 1:
        errores.append("Las espiras totales y las espiras por capa deben ser al menos 1 "
                       "(si ingresas capas, no pueden ser más que las espiras).")
    elif r.get("capas_fijas"):                 # FRANCÉS: siempre 2 capas · HÉLICE: una sola capa
        capas = int(redondeo_mas(espiras_por_seccion(tipo, n_espiras) / esp_por_capa, 0))
        regla = "es de una sola capa" if r["capas_fijas"] == 1 else f"es de {r['capas_fijas']} capas"
        if capas != r["capas_fijas"]:
            errores.append(f"{tipo}: {regla}; con {n(esp_por_capa)} espiras por capa salen {capas} "
                           f"{'capa' if capas == 1 else 'capas'}.")
    return errores


def espiras_por_seccion(tipo, n_espiras):
    """Espiras de cada sección: N en devanado normal, REDONDEO.MAS(N/2) en galleta."""
    return int(redondeo_mas(n_espiras / TIPOS[tipo]["secciones"], 0))


def espiras_por_bobina(tipo, n_espiras):
    """Galleta: 2 bobinas en el mismo eje. La primera lleva REDONDEO.MAS(N / 2) espiras y la segunda el resto (con N
    impar, una espira menos); las dos se dimensionan con la mayor. None si el tipo no es de 2 bobinas."""
    if tipo not in TIPOS or TIPOS[tipo]["secciones"] < 2 or n_espiras is None:
        return None
    a = espiras_por_seccion(tipo, n_espiras)
    return a, n_espiras - a


def texto_bobinas(b):
    return f"{b[0]} + {b[1]}"


def medidas_conductor(conductor, medida, papel_platina):
    """(espesor calato, ancho calato, papel, sección de cobre, nombre) de 1 conductor."""
    if conductor == "PLATINA":
        esp_cal, anc_cal = PLATINAS[medida]
        # sección rectangular, sin descontar el radio de las esquinas (como la hoja de devanado)
        return esp_cal, anc_cal, papel_platina, seccion_platina(esp_cal, anc_cal), f"Platina {esp_cal:g} x {anc_cal:g} mm"
    seccion, d_esm = ALAMBRES[medida]        # ya esmaltado: no lleva papel
    return d_esm, d_esm, 0.0, seccion, f"Alambre cal. {medida} (Ø {d_esm:g} mm)"


def ajuste_ventana(tipo, conductor, medida, horizontales, papel_platina, n_espiras, transposiciones,
                   hc, yugo_min):
    """Paso 2: el devanado se construye dentro de la ventana del núcleo.
    Altura disponible = Hc - 2 x distancia mínima al yugo (en galleta, menos la separación y entre 2).
    El axial es REDONDEO.MAS((esp. por capa + 1) x ancho por espira) + transposiciones x ancho del
    conductor, así que las espiras por capa que entran son ENTERO(disponible - transp.) / ancho - 1.
    Con eso: capas = REDONDEO.MAS(espiras / esp. por capa máx.). capas = None si no entra ni una."""
    _, anc_cal, papel, _, _ = medidas_conductor(conductor, medida, papel_platina)
    ancho_cond = papel + anc_cal
    ancho_espira = ancho_cond * horizontales
    n_sec = TIPOS[tipo]["secciones"]
    axial_disp = hc - 2.0 * yugo_min
    por_seccion = (axial_disp - (n_sec - 1) * SEPARACION_GALLETA) / n_sec
    util = math.floor(round(por_seccion - transposiciones * ancho_cond, 6))
    epc_lim = util / ancho_espira - 1.0
    n_por_sec = espiras_por_seccion(tipo, n_espiras)
    # FRANCÉS: siempre 2 capas (espiras por capa = N / 2); si no caben en la altura, el al yugo lo muestra (faltan mm)
    fijas = TIPOS[tipo].get("capas_fijas")
    capas = (fijas or int(redondeo_mas(n_por_sec / epc_lim, 0))) if epc_lim >= 1 else None
    return {"hc": hc, "yugo": yugo_min, "axial_disp": axial_disp, "por_seccion": por_seccion, "util": util,
            "epc_lim": epc_lim, "capas": capas, "n_por_sec": n_por_sec, "ancho_espira": ancho_espira,
            "ancho_cond": ancho_cond, "n_sec": n_sec, "capas_fijas": fijas,
            "entra_fijas": epc_lim >= n_por_sec / fijas - 1e-9 if fijas else None}


def calcular_devanado(tipo, conductor, medida, cantidad, horizontales, papel_platina,
                      n_espiras, esp_por_capa, papel_capa, canales, transposiciones,
                      corriente=0.0, capas_in=None, ventana=None):
    """esp_por_capa admite decimales. Si se da capas_in (N° de capas ingresado o ajustado a la ventana),
    las espiras por capa se calculan como espiras / capas_in. ventana = detalle de ajuste_ventana."""
    # --- 1 conductor ---
    esp_cal, anc_cal, papel, seccion, nombre = medidas_conductor(conductor, medida, papel_platina)
    ancho_cond = papel + anc_cal             # axial de 1 conductor
    esp_cond = papel + esp_cal               # radial de 1 conductor

    # --- Espira ---
    radiales = cantidad // horizontales
    ancho_espira = ancho_cond * horizontales     # (papel + ancho calato) x axiales
    espesor_espira = esp_cond * radiales         # (papel + espesor calato) x radiales

    # --- Espiras por sección (galleta: N se reparte entre las 2 galletas) ---
    n_sec = TIPOS[tipo]["secciones"]
    n_por_sec = espiras_por_seccion(tipo, n_espiras)

    # --- Capas y espiras por capa ---
    if capas_in:                                   # se ingresó el N° de capas
        capas = int(capas_in)
        esp_por_capa = n_por_sec / capas
        capas_calc = float(capas)
    else:                                          # se ingresaron espiras por capa
        capas_calc = n_por_sec / esp_por_capa
        capas = int(redondeo_mas(capas_calc, 0))

    # --- Radial ---
    suma_canales = sum(canales)
    radial_bruto = capas * (papel_capa + espesor_espira) + suma_canales
    radial = redondeo_mas(radial_bruto)

    # --- Axial ---
    axial_bruto = (esp_por_capa + 1) * ancho_espira
    axial_redondeado = redondeo_mas(axial_bruto)
    axial_seccion = axial_redondeado + transposiciones * ancho_cond
    axial_total = n_sec * axial_seccion + (n_sec - 1) * SEPARACION_GALLETA

    seccion_total = seccion_espira(conductor, seccion, cantidad)       # platina: x 0.97
    return {
        "tipo": tipo, "conductor": conductor, "medida": medida, "nombre": nombre,
        "papel": papel, "esp_cal": esp_cal, "anc_cal": anc_cal,
        "ancho_cond": ancho_cond, "esp_cond": esp_cond,
        "seccion": seccion, "seccion_total": seccion_total,
        "corriente": corriente,
        "densidad": corriente / seccion_total if corriente > 0 else None,
        "cantidad": cantidad, "horizontales": horizontales, "radiales": radiales,
        "ancho_espira": ancho_espira, "espesor_espira": espesor_espira,
        "n_espiras": n_espiras, "n_por_sec": n_por_sec, "esp_por_capa": esp_por_capa,
        "capas_calc": capas_calc, "capas": capas, "modo_capas": bool(capas_in), "ventana": ventana,
        "espiras_ultima": n_por_sec - (capas - 1) * esp_por_capa,
        "papel_capa": papel_capa, "canales": canales, "suma_canales": suma_canales,
        "radial_bruto": radial_bruto, "radial": radial,
        "transposiciones": transposiciones,
        "axial_bruto": axial_bruto, "axial_redondeado": axial_redondeado,
        "axial_seccion": axial_seccion, "n_sec": n_sec, "axial_total": axial_total,
    }


# =====================================================================
# 5. MONTAJE: DEVANADOS SOBRE EL NÚCLEO
# =====================================================================
def calcular_montaje(nuc, elec, lista, entre_fases, t_ref, tubo=0.0):
    """lista: devanados en orden radial (del núcleo hacia afuera), cada uno con
    {"pos", "clave", "res", "canal", "yugo"}: canal = canal interior (aislamiento mayor hacia el núcleo o
    el devanado anterior), yugo = distancia MÍNIMA al yugo. tubo = espesor del tubo enrollado que envuelve
    todo el conjunto; entre_fases = distancia MÍNIMA entre bobinas de fases vecinas.
    Devuelve diámetros, distancias resultantes (paso 3), pesos, resistencias y pérdidas."""
    rho_t = RHO_CU_20 * (234.5 + t_ref) / (234.5 + 20.0)
    filas = []
    d_prev = nuc["dn"]
    for item in lista:
        res = item["res"]
        e = elec["dev"][item["clave"]]
        d_int = d_prev + 2.0 * item["canal"]
        d_ext = d_int + 2.0 * res["radial"]
        d_med = (d_int + d_ext) / 2.0
        l_espira = math.pi * d_med                                    # mm
        long_fase = e["n_max"] * l_espira / 1000.0                    # m (con todas las espiras)
        peso = FASES * long_fase * res["seccion_total"] * DENS_CU / 1000.0   # kg
        r_fase = rho_t * e["n_nom"] * l_espira / 1000.0 / res["seccion_total"]   # Ω, toma nominal
        altura = res["axial_total"] + 2.0 * item["yugo"]       # altura que necesita con el mínimo al yugo
        al_yugo = (nuc["hc"] - res["axial_total"]) / 2.0      # lo que queda al yugo (devanado centrado)
        filas.append({
            "pos": item["pos"], "clave": item["clave"], "nombre": e["nombre"], "tipo": res["tipo"],
            "canal": item["canal"], "yugo": item["yugo"],
            "d_int": d_int, "d_ext": d_ext, "d_med": d_med,
            "radial": res["radial"], "axial": res["axial_total"],
            "axial_seccion": res["axial_seccion"], "n_sec": res["n_sec"], "seccion": res["seccion_total"],
            "capas": res["capas"], "radiales": res["radiales"], "n_canales": len(res["canales"]), "ventana": bool(res["ventana"]),
            "altura": altura, "margen_hc": nuc["hc"] - altura,
            "al_yugo": al_yugo, "margen_yugo": al_yugo - item["yugo"],
            "l_espira": l_espira, "long_fase": long_fase, "peso": peso, "r_fase": r_fase,
            "i_carga": e["i_carga"], "perdidas": FASES * e["i_carga"] ** 2 * r_fase,
            "j_nom": e["i_fase"] / res["seccion_total"], "j_max": e["i_max"] / res["seccion_total"],
        })
        d_prev = d_ext

    d_dev = d_prev                          # Ø exterior del último devanado
    d_total = d_dev + 2.0 * tubo            # Ø exterior con el tubo enrollado
    de_min = d_total + entre_fases
    return {
        "filas": filas, "t_ref": t_ref, "entre_fases": entre_fases,
        "d_dev": d_dev, "tubo": tubo, "d_total": d_total, "de_min": de_min, "margen_de": nuc["de"] - de_min,
        "entre_fases_real": nuc["de"] - d_total,          # lo que queda entre bobinas de fases vecinas
        "hc_min": max(f["altura"] for f in filas),
        "peso_cu": sum(f["peso"] for f in filas),
        "perdidas": sum(f["perdidas"] for f in filas),
    }


def k_rogowski(corriente):
    """kR del cuadro: el de la última fila cuya corriente 'desde' no supera la corriente de fase."""
    valor = TABLA_ROGOWSKI[0][1]
    for desde, k_r in TABLA_ROGOWSKI:
        if corriente >= desde:
            valor = k_r
    return valor


def calcular_vcc(elec, mont):
    """Vcc entre el devanado principal y cada secundario, con la fórmula de la hoja de Excel:
        Vcc_reactiva = (N·I_fase)·(PI·Dm)·(Lambda + (e1 + e2)/3)·kR·K / (Heq·B·Sfe)
        Vcc_Activa   = Pérdidas / (Potencia·10)        Vcc = RAÍZ(Vcc_reactiva² + Vcc_Activa²)
    N e I_fase son los del secundario; kR sale del cuadro con esa corriente. Se usa la primera tensión
    de cada devanado. Si hay un devanado en medio, su espesor cuenta dentro de Lambda."""
    por_clave = {f["clave"]: f for f in mont["filas"]}
    at_e = elec["dev"][PRINCIPAL]
    s_fe = elec["seccion_neta"] / 100.0             # cm²
    b_kg = elec["b_real"] * 10.0                    # kilogauss
    pares = []
    for k in elec["secundarios"]:
        if k not in por_clave or PRINCIPAL not in por_clave:
            continue
        a_f, s_f = por_clave[PRINCIPAL], por_clave[k]
        dentro, fuera = (a_f, s_f) if a_f["pos"] < s_f["pos"] else (s_f, a_f)
        sec_e = elec["dev"][k]
        s_base = min(at_e["kva"], sec_e["kva"])
        i_sec = corriente_fase(s_base, sec_e["volt"], sec_e["conex"])
        i_at = corriente_fase(s_base, at_e["volt"], at_e["conex"])
        lam = (fuera["d_int"] - dentro["d_ext"]) / 2.0
        d_m = (a_f["d_med"] + s_f["d_med"]) / 2.0
        h_eq = (a_f["axial"] + s_f["axial"]) / 2.0
        k_r = k_rogowski(i_sec)
        reactiva = ((sec_e["n_nom"] * i_sec) * (math.pi * d_m) * (lam + (a_f["radial"] + s_f["radial"]) / 3.0)
                    * k_r * K_VCC / (h_eq * b_kg * s_fe))
        perdidas = FASES * (i_sec ** 2 * s_f["r_fase"] + i_at ** 2 * a_f["r_fase"])
        activa = perdidas / (s_base * 10.0)
        pares.append({
            "par": f"{at_e['nombre']} – {sec_e['nombre']}", "clave": k, "s_base": s_base,
            "n": sec_e["n_nom"], "i": i_sec, "d_m": d_m, "lam": lam,
            "e_pri": a_f["radial"], "e_sec": s_f["radial"], "h_eq": h_eq, "k_r": k_r,
            "b_kg": b_kg, "s_fe": s_fe, "perdidas": perdidas,
            "ux": reactiva, "ur": activa, "uz": math.hypot(reactiva, activa),
        })
    return pares


# =====================================================================
# 5.1 CÁLCULO COMPLETO DESDE UN DICCIONARIO DE DATOS (sin la pantalla)
# =====================================================================
# Mismos pasos que calcular_todo, pero con los datos en un diccionario (como los de la pantalla). Lo usa la
# búsqueda por Vcc para verificar cada alternativa con el cálculo completo.
def _canales(texto):
    """Formato anterior: canales escritos como 4+4."""
    return [v for v in (float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(texto))) if v > 0]


def canales_internos(n_canales, canal_mm):
    """Canales internos de refrigeración (aislamiento menor): N° de canales, todos de canal_mm."""
    n_can = int(n_canales)
    return [float(canal_mm)] * n_can if n_can > 0 and canal_mm > 0 else []


def canales_de(w):
    """N° de canales, medida y lista de canales de un devanado (acepta también el formato anterior "4+4")."""
    if "n_canales" in w:
        if w["n_canales"] is None:              # sin digitar (devanado sin uso)
            return None, w.get("canal_mm"), []
        return w["n_canales"], w["canal_mm"], canales_internos(w["n_canales"], w["canal_mm"])
    lista = _canales(w.get("canales", ""))
    return len(lista), (sum(lista) / len(lista) if lista else 0.0), lista


# Posición radial FIJA: el Devanado I es siempre el externo; hacia el núcleo siguen el II y luego el III.
# Solo cuentan los devanados con potencia; el más interno es la posición 1 (junto al núcleo).
ORDEN_RADIAL = ["III", "II", "I"]          # del núcleo hacia afuera
NOTA_POSICION = ("El Devanado I es siempre el externo; hacia el núcleo siguen el II y luego el III (el más interno va junto al núcleo). La posición radial no se digita: sale de este orden.")


def posiciones_radiales(dev):
    activos = [k for k in ORDEN_RADIAL if (dev[k].get("kva") or 0) > 0]
    return {k: (activos.index(k) + 1 if k in activos else None) for k in CLAVES}


def con_posiciones(d):
    """Copia de los datos con la posición radial de cada devanado según el orden fijo."""
    d = copy.deepcopy(d)
    for k, p in posiciones_radiales(d["dev"]).items():
        d["dev"][k]["pos"] = p
    return d


def texto_posicion(p, n_activos):
    if p is None:
        return "—"
    if p == n_activos:
        return f"{p} · externo"
    return f"{p} · junto al núcleo" if p == 1 else f"{p}"


# Datos que se digitan (no tienen fuente): si alguno está vacío (None) no se calcula
ROTULOS_GENERALES = {"frec": "frecuencia", "rep": "reparto de carga", "pasos": "N° de pasos", "variacion": "% de variación",
                     "tap": "tap nominal", "dn": "diámetro Dn", "de": "distancia entre ejes De", "hc": "altura de ventana Hc",
                     "g": "traslape g", "bobj": "B máxima (objetivo)", "fa": "factor de apilamiento",
                     "fconst": "factor de construcción",
                     "tubo": "tubo enrollado exterior", "fases": "entre fases mínimo", "tref": "T° de referencia",
                     "barrera": "barrera entre bobinas (hawayano o tubo)", "e_barrera": "espesor de la barrera",
                     "tubo_rigido": "tubo rígido: largo extra", "tubo_nucleo": "tubo núcleo–bobina"}
ROTULOS_DEVANADO = {"kva": "potencia", "kva2": "2ª potencia", "volt": "tensión", "volt2": "2ª tensión", "conex": "grupo",
                    "conex2": "2º grupo", "calibre": "calibre", "cant": "cantidad de conductores", "horiz": "horizontales",
                    "pos": "posición radial", "tipo": "tipo de devanado", "papel": "papel de platina",
                    "papel_capa": "papel entre capas", "capas": "N° de capas", "epc": "espiras por capa",
                    "n_canales": "N° de canales internos", "canal_mm": "medida de los canales internos",
                    "transp": "transposiciones", "canal": "canal interior", "yugo": "distancia mínima al yugo",
                    "relleno": "relleno de los extremos", "industrial": "tensión de prueba industrial"}


def _vacio(v):
    return v is None or v == ""


def faltantes(d):
    """Datos sin fuente que todavía no se digitaron. Solo se piden los que el cálculo usa: los de los devanados con
    potencia, el papel solo con platina, la medida de canales solo si hay canales y capas o espiras por capa según
    el ajuste de capas."""
    falta = []
    gen = [ROTULOS_GENERALES[c] for c in ROTULOS_GENERALES if _vacio(d.get(c))]
    if gen:
        falta.append("Datos generales: " + ", ".join(gen) + ".")
    for k in CLAVES:
        w = d["dev"][k]
        if _vacio(w.get("kva")):
            falta.append(f"{NOMBRES[k]}: potencia.")
            continue
        if w["kva"] <= 0:                       # devanado sin potencia: no se usa
            continue
        pedir = _pedir_devanado(w)
        vacios = [ROTULOS_DEVANADO[c] for c in ROTULOS_DEVANADO if c in pedir and _vacio(w.get(c))]
        if vacios:
            falta.append(f"{NOMBRES[k]}: " + ", ".join(vacios) + ".")
    return falta


def _pedir_devanado(w):
    """Datos de un devanado con potencia que el cálculo necesita."""
    pedir = ["kva2", "volt", "volt2", "conex", "conex2", "calibre", "cant", "horiz", "tipo", "papel_capa",
             "n_canales", "transp", "canal", "yugo", "relleno", "industrial"]
    if not _vacio(w.get("calibre")) and w["calibre"][0] == "PLATINA":
        pedir.append("papel")
    if not _vacio(w.get("n_canales")) and w["n_canales"] > 0:
        pedir.append("canal_mm")
    if w.get("modo") == "capas":
        pedir.append("capas")
    elif w.get("modo") == "epc":
        pedir.append("epc")
    return pedir


# Lo mismo, dato por dato y con el paso de la pantalla donde se digita
# (1 datos del cliente, 2 núcleo, 3 devanados, 4 distancias eléctricas)
PASO_GENERAL = {"frec": 1, "rep": 1, "pasos": 1, "variacion": 1, "tap": 1, "dn": 2, "de": 2, "hc": 2, "g": 2,
                "bobj": 2, "fa": 2, "fconst": 2, "tubo": 4, "fases": 4, "tref": 2,
                "barrera": 4, "e_barrera": 4, "tubo_rigido": 4, "tubo_nucleo": 4}
PASO_CLIENTE_DEV = ("kva", "kva2", "volt", "volt2", "conex", "conex2", "bil", "industrial")   # datos del cliente
PASO_DIST_DEV = ("canal", "yugo", "relleno")                  # distancias eléctricas


def paso_dev(c):
    return 1 if c in PASO_CLIENTE_DEV else 4 if c in PASO_DIST_DEV else 3


def faltantes_detalle(d):
    out = []
    for c in ROTULOS_GENERALES:
        if _vacio(d.get(c)):
            out.append({"paso": PASO_GENERAL[c], "k": None, "c": c, "rotulo": ROTULOS_GENERALES[c][:1].upper() + ROTULOS_GENERALES[c][1:]})
    for k in CLAVES:
        w = d["dev"][k]
        if _vacio(w.get("kva")):
            out.append({"paso": 1, "k": k, "c": "kva", "rotulo": f"{NOMBRES[k]} · potencia"})
            continue
        if w["kva"] <= 0:
            continue
        pedir = _pedir_devanado(w)
        for c in ROTULOS_DEVANADO:
            if c in pedir and _vacio(w.get(c)):
                out.append({"paso": paso_dev(c), "k": k, "c": c,
                            "rotulo": f"{NOMBRES[k]} · {ROTULOS_DEVANADO[c]}"})
    return sorted(out, key=lambda x: x["paso"])


def calcular_datos(d):
    d = con_posiciones(d)                       # el Devanado I es siempre el externo
    salida = {"errores": [], "llenado": {}}
    specs, cond, bob = {}, {}, {}
    for k in CLAVES:
        w = d["dev"][k]
        cant, horiz = w["cant"], w["horiz"]
        if w["tipo"] is not None and cant is not None and horiz is not None:   # sin uso: puede no tener tipo
            r = TIPOS[w["tipo"]]
            cant = min(max(cant, 1), r["max_cond"])
            horiz = min(max(horiz, 1), r["max_h"])
            if r["h_fijo"] is not None:
                horiz = r["h_fijo"]
            elif r["radiales"] == (1,):
                horiz = cant
        # con «Ajustar a la ventana» las capas salen del cálculo: hasta calcular, quedan vacías
        ventana_ = w["modo"] == "ventana"
        salida["llenado"][k] = {"cant": cant, "horiz": horiz, "capas": None if ventana_ else w["capas"],
                                "epc": None if ventana_ else w["epc"]}
        specs[k] = {c: w[c] for c in ("kva", "kva2", "volt", "volt2", "conex", "conex2", "bil")}
        cond[k] = {"conductor": w["calibre"][0], "medida": w["calibre"][1], "cantidad": cant, "horizontales": horiz}
    salida.update(specs=specs, cond=cond)
    falta = faltantes(d)
    if falta:                                   # datos sin fuente que todavía no se digitaron
        salida["errores"] = falta
        salida["faltan"] = True
        return salida
    anchos = [a for a in d["anchos"] if a > 0]
    err = validar_nucleo(d["dn"], d["g"], d["de"], d["hc"], FACTOR_ELIPSE, anchos)
    if d["fa"] <= 0 or d["fa"] > 1:
        err.append("Núcleo: el factor de apilamiento debe estar entre 0 y 1.")
    if d["de"] <= d["dn"]:
        err.append(MSG_DE)
    if err:
        salida["errores"] = err
        return salida
    nuc = calcular_nucleo(d["dn"], d["g"], d["de"], d["hc"], FACTOR_ELIPSE, anchos, d["fa"])
    salida["nuc"] = nuc
    err_elec, elec = calcular_electrico(specs, d["frec"], d["tap"], d["variacion"], d["pasos"], d["rep"],
                                        nuc["seccion_neta"], d["bobj"], 0)   # espiras de referencia: siempre de la B objetivo
    salida["elec"] = elec
    for k in CLAVES:
        w, ll = d["dev"][k], salida["llenado"][k]
        e = elec["dev"].get(k) if elec else None
        if e and w["modo"] != "ventana":
            n_sec = espiras_por_seccion(w["tipo"], e["n_max"])
            if w["modo"] == "capas":
                ll["epc"] = redondeo_mas(n_sec / w["capas"], 2)
            elif w["epc"] > 0:
                ll["capas"] = int(redondeo_mas(n_sec / w["epc"], 0))
        n_can, mm_can, canales = canales_de(w)
        papel = 0.0 if w["papel"] is None and w["calibre"][0] == "ALAMBRE" else w["papel"]   # alambre: sin papel
        bob[k] = {"pos": w["pos"], "tipo": w["tipo"], "papel": papel, "papel_capa": w["papel_capa"],
                  "modo": w["modo"], "capas": ll["capas"], "epc": ll["epc"], "canal": w["canal"], "yugo": w["yugo"],
                  "n_canales": n_can, "canal_mm": mm_can, "canales": canales, "transp": w["transp"]}
    salida["bob"] = bob
    err_vac = []
    if d["fconst"] <= 0:
        err_vac.append("Pérdidas en el núcleo: el factor de construcción debe ser mayor que 0.")
    elif elec:
        salida["vacio"] = calcular_vacio(nuc, elec, 0.0, d["fconst"])     # Pfe siempre de la regresión de la tabla
    errores = list(err_elec) + err_vac
    if elec:
        por_pos = {}
        for k in elec["activos"]:
            por_pos.setdefault(bob[k]["pos"], []).append(NOMBRES[k])
        for pos, nombres in sorted(por_pos.items()):
            if len(nombres) > 1:
                errores.append(f"{' y '.join(nombres)} tienen la misma posición radial ({pos}): "
                               f"cada devanado va en una posición distinta.")
    if d["fases"] < 0 or d["tubo"] < 0:
        errores.append("La distancia entre fases y el tubo enrollado no pueden ser negativos.")
    errores += errores_esfuerzos(d, elec)
    lista = []
    if elec:
        for k in sorted(elec["activos"], key=lambda c: bob[c]["pos"]):
            err_dev, res = calcular_bobinado(k, elec["dev"][k], cond, bob, nuc["hc"])
            if err_dev:
                errores += [f"{NOMBRES[k]}: {x}" for x in err_dev]
            else:
                lista.append({"pos": bob[k]["pos"], "clave": k, "res": res, "canal": bob[k]["canal"],
                              "yugo": bob[k]["yugo"]})
    salida["lista"] = lista
    for item in lista:
        if item["res"]["ventana"]:
            salida["llenado"][item["clave"]]["capas"] = item["res"]["capas"]
            salida["llenado"][item["clave"]]["epc"] = redondeo_mas(item["res"]["esp_por_capa"], 2)
    if errores:
        salida["errores"] = errores
        return salida
    salida["mont"] = calcular_montaje(nuc, elec, lista, d["fases"], d["tref"], d["tubo"])
    salida["pares"] = calcular_vcc(elec, salida["mont"])
    salida["esf"] = esfuerzos_dielectricos(salida["mont"], d["dev"], d)
    return salida


# =====================================================================
# 5.2 BÚSQUEDA POR Vcc: COMBINACIONES DE CONDUCTORES Y DIÁMETRO DEL NÚCLEO
# =====================================================================
# Con el mismo cálculo del diseño (núcleo -> devanados ajustados a la ventana -> distancias):
#   - Vcc objetivo ± tolerancia (par Devanado I – primer secundario)
#   - densidad de corriente de cada devanado entre J mín y J máx, con la corriente MAYOR (tensiones y tomas)
#   - inducción real entre B mín y B máx, con espiras enteras
#   - Dn fijo (si se da) o buscado en un rango; Hc fijo; De máximo (0 = se calcula el mínimo que entra)
# Las espiras no dependen de Dn (solo de las espiras de referencia), ni el radial y el axial de cada devanado:
# los devanados candidatos se arman una vez por cada N y luego se combinan para cada Dn.
CONDUCTORES_TODOS = [("ALAMBRE", c) for c in ALAMBRES] + [("PLATINA", i) for i in range(len(PLATINAS))]
ORDENES_BUSQUEDA = {"peso": "Menor peso (cobre + núcleo)", "perdidas": "Menores pérdidas (P0 + I²R)",
                    "vcc": "Vcc más cercano al objetivo", "cobre": "Menor cobre"}


def arreglos_tipo(tipo):
    """(cantidad, horizontales) que permite cada tipo de devanado."""
    r, out = TIPOS[tipo], []
    for h in range(1, r["max_h"] + 1):
        if r["h_fijo"] is not None and h != r["h_fijo"]:
            continue
        for cant in range(h, r["max_cond"] + 1, h):
            if r["radiales"] and cant // h not in r["radiales"]:
                continue
            out.append((cant, h))
    return out


def anchos_para_dn(d, dn):
    """Los anchos del diseño si es el mismo Dn; si no, los óptimos de la tabla con el mismo número de escalones,
    redondeados a 5 mm y siempre decrecientes."""
    usados = [a for a in d["anchos"] if a > 0]
    if abs(dn - d["dn"]) < 1e-9:
        return usados
    n, out = min(max(len(usados), 1), 10), []
    for c in COEFICIENTES_ANCHO[n]:
        a = math.floor(dn * c / 5 + 0.5) * 5
        if a >= dn:
            a -= 5
        if out and a >= out[-1]:
            a = out[-1] - 5
        if a > 0:
            out.append(a)
    return out


ROTULOS_BUSQUEDA = {"vcc": "Vcc objetivo", "tol": "tolerancia", "jmin": "J mínima", "jmax": "J máxima", "bmin": "B mínima",
                    "bmax": "B máxima", "dn_fijo": "Dn fijo", "de_max": "De máximo"}


def validar_busqueda(o):
    vacios = [ROTULOS_BUSQUEDA[c] for c in ROTULOS_BUSQUEDA if _vacio(o.get(c))]
    if not _vacio(o.get("dn_fijo")) and not o["dn_fijo"] > 0:
        vacios += [r for c, r in (("dn_min", "Dn mínimo"), ("dn_max", "Dn máximo"), ("dn_paso", "paso de Dn"))
                   if _vacio(o.get(c))]
    if vacios:
        return ["Búsqueda: digita " + ", ".join(vacios) + "."]
    e = []
    if not (o["vcc"] > 0) or not (o["tol"] > 0):
        e.append("Búsqueda: el Vcc objetivo y su tolerancia deben ser mayores que 0.")
    if not (o["jmin"] >= 0) or not (o["jmax"] > o["jmin"]):
        e.append("Búsqueda: la densidad máxima debe ser mayor que la mínima.")
    if not (o["bmin"] > 0) or not (o["bmax"] > o["bmin"]):
        e.append("Búsqueda: la inducción máxima debe ser mayor que la mínima.")
    if not o["dn_fijo"] > 0 and (not o["dn_min"] > 0 or not o["dn_max"] >= o["dn_min"] or not o["dn_paso"] > 0):
        e.append("Búsqueda: el rango de Dn no es válido (mínimo, máximo y paso mayores que 0).")
    if not o["dn_fijo"] > 0 and o["dn_paso"] > 0 and (o["dn_max"] - o["dn_min"]) / o["dn_paso"] > 400:
        e.append("Búsqueda: el rango de Dn tiene más de 400 valores; usa un paso mayor.")
    if o["de_max"] < 0:
        e.append("Búsqueda: el De máximo no puede ser negativo (0 = se calcula).")
    return e


def candidatos_devanado(k, elec, d, o):
    """Devanados posibles de la clave k: tipo x arreglo x conductor, con la densidad en el rango y dentro de la ventana."""
    w, e, out = d["dev"][k], elec["dev"][k], []
    tipos = o["tipos"].get(k) or [w["tipo"]]
    canales = canales_de(w)[2]
    for tipo in tipos:
        for cant, horiz in arreglos_tipo(tipo):
            for cond_, med in CONDUCTORES_TODOS:
                if cond_ == "PLATINA" and w["papel"] is None:      # sin papel digitado: solo alambres
                    continue
                sec = medidas_conductor(cond_, med, w["papel"])[3]
                s_ = seccion_espira(cond_, sec, cant)
                jmax = e["i_max"] / s_
                if jmax > o["jmax"] + 1e-9 or jmax < o["jmin"] - 1e-9:
                    continue
                v = ajuste_ventana(tipo, cond_, med, horiz, w["papel"], e["n_max"], w["transp"], d["hc"], w["yugo"])
                if v["capas"] is None or (v["capas_fijas"] and not v["entra_fijas"]):   # FRANCÉS en 2 capas, HÉLICE en 1
                    continue
                epc = espiras_por_seccion(tipo, e["n_max"]) / v["capas"]
                if validar(tipo, cant, horiz, e["n_max"], epc):
                    continue
                res = calcular_devanado(tipo, cond_, med, cant, horiz, w["papel"], e["n_max"], epc, w["papel_capa"],
                                        canales, w["transp"], e["i_fase"], capas_in=v["capas"], ventana=v)
                out.append({"clave": k, "tipo": tipo, "conductor": cond_, "medida": med, "cant": cant, "horiz": horiz,
                            "res": res, "s": s_, "jnom": e["i_fase"] / s_, "jmax": jmax, "fijo": False})
    return out


def devanado_fijo(k, elec, d):
    """Devanado que no se optimiza (el III, si se usa): tal como está en la tabla."""
    w, e = d["dev"][k], elec["dev"][k]
    r = TIPOS[w["tipo"]]
    cant = min(max(int(w["cant"]), 1), r["max_cond"])
    horiz = min(max(int(w["horiz"]), 1), r["max_h"])
    if r["h_fijo"] is not None:
        horiz = r["h_fijo"]
    elif r["radiales"] == (1,):
        horiz = cant
    ventana, capas_in = None, (w["capas"] if w["modo"] == "capas" else None)
    if w["modo"] == "ventana":
        ventana = ajuste_ventana(w["tipo"], w["calibre"][0], w["calibre"][1], horiz, w["papel"], e["n_max"],
                                 w["transp"], d["hc"], w["yugo"])
        if ventana["capas"] is None or (ventana["capas_fijas"] and not ventana["entra_fijas"]):
            return None
        capas_in = ventana["capas"]
    epc = espiras_por_seccion(w["tipo"], e["n_max"]) / capas_in if capas_in else w["epc"]
    if validar(w["tipo"], cant, horiz, e["n_max"], epc):
        return None
    res = calcular_devanado(w["tipo"], w["calibre"][0], w["calibre"][1], cant, horiz, w["papel"], e["n_max"], epc,
                            w["papel_capa"], canales_de(w)[2], w["transp"], e["i_fase"], capas_in=capas_in,
                            ventana=ventana)
    s_ = res["seccion_total"]
    return {"clave": k, "tipo": w["tipo"], "conductor": w["calibre"][0], "medida": w["calibre"][1], "cant": cant,
            "horiz": horiz, "res": res, "s": s_, "jnom": e["i_fase"] / s_, "jmax": e["i_max"] / s_, "fijo": True}


def aplicar_alternativa(d, alt, o):
    """Datos del diseño con la alternativa puesta (para verificarla y para cargarla en la pantalla)."""
    n = copy.deepcopy(d)
    n["dn"] = alt["dn"]
    n["anchos"] = (list(alt["anchos"]) + [0] * 10)[:10]
    n["de"] = alt["de"]          # las espiras salen de la B objetivo del diseño, que no se toca: la búsqueda va aparte
    for c in alt["devanados"]:
        if not c["fijo"]:
            n["dev"][c["clave"]].update(tipo=c["tipo"], calibre=(c["conductor"], c["medida"]), cant=c["cant"],
                                        horiz=c["horiz"], modo="ventana")
    return n


def explicar_busqueda(c, o, optimiza, d):
    """Por qué no salen combinaciones (o salen pocas): en qué condición se quedaron."""
    t = []
    if not c["dn"]:
        t.append("Ningún Dn del rango sirve: revisa que los anchos de escalón sean menores que Dn.")
    if abs(o["bmax"] - d["bobj"]) > 1e-9:
        t.append(f"La B máxima de la búsqueda ({o['bmax']:g} T) no es la B objetivo del diseño ({d['bobj']:g} T): el diseño "
                 f"calcula sus espiras con la suya, así que una alternativa puede no reproducirse («Verif.» ✗) y no se puede usar.")
    if c["sin_n"] and len(c["sin_n"]) == c["dn"]:
        s0 = c["sin_n"][0]
        texto = (f"Con Dn {s0['dn']:g} no hay" if c["dn"] == 1 else "En ningún Dn del rango hay")
        texto += f" una cantidad entera de espiras que deje B entre {o['bmin']:g} y {o['bmax']:g} T"
        if c["dn"] == 1:
            texto += f": {s0['n2']} espiras dan {s0['b2']:.3f} T"
            if s0["b1"]:
                texto += f" y {s0['n1']} dan {s0['b1']:.3f} T"
            texto += ". Cambia Dn o el rango de B."
        else:
            texto += "."
        t.append(texto)
    elif c["sin_n"]:
        t.append(f"{len(c['sin_n'])} de los {c['dn']} Dn no tienen espiras enteras con B en el rango y se saltaron.")
    if not c["n"] and c["n_relacion"]:
        t.append("Con las espiras enteras que dejan B en el rango, el error de relación pasa de "
                 f"{ERROR_RELACION_MAX:g} %: " + ", ".join(f"{n_} espiras dan {e_:.2f} %" for n_, e_ in c["n_relacion"][:3])
                 + ". Revisa las tensiones o amplía el rango de B.")
    if not c["n"] and c["n_fijo"]:
        k_ = c["n_fijo"][0][1]
        t.append(f"El {NOMBRES[k_]} (no se optimiza: va como está en la tabla) no entra en la ventana con esas espiras.")
    for k in optimiza:
        if c["n"] and c["candidatos"].get(k) == 0:
            tipos = ", ".join(o["tipos"].get(k) or [d["dev"][k]["tipo"]])
            t.append(f"Ningún conductor del {NOMBRES[k]} ({tipos}) deja la densidad máxima entre {o['jmin']:g} y "
                     f"{o['jmax']:g} A/mm² y entra en la ventana.")
    if c["rechazo_de"] and not c["cumplen"] and c["rechazo_de"] == c["combinaciones"]:
        t.append(f"Ninguna combinación entra en De = {o['de_max']:g} mm con {d['fases']:g} mm entre fases.")
    if c["combinaciones"] and not c["cumplen"] and math.isfinite(c["vcc_min"]):
        t.append(f"El Vcc que se alcanza va de {c['vcc_min']:.2f} a {c['vcc_max']:.2f} %, fuera de {o['vcc']:g} % ± "
                 f"{o['tol']:g} %. Cambia el canal entre devanados, la altura de ventana o los tipos de devanado.")
    return t


def buscar_combinaciones(d, o):
    """d: datos del diseño (ver leer_datos) · o: condiciones de la búsqueda. Devuelve las combinaciones que cumplen,
    ordenadas, con el frente de Pareto (peso activo vs pérdidas) y cada una de las primeras verificada."""
    d = con_posiciones(d)                       # el Devanado I es siempre el externo
    falta = faltantes(d)
    salida = {"errores": ([f"Para buscar, primero digita estos datos. {x}" for x in falta] if falta else validar_busqueda(o)),
              "resultados": [], "avisos": [], "todos": [],
              "cuenta": {"dn": 0, "n": 0, "combinaciones": 0, "cumplen": 0, "candidatos": {}, "rechazo_de": 0,
                         "rechazo_vcc": 0, "vcc_min": math.inf, "vcc_max": -math.inf, "sin_n": [], "n_relacion": [],
                         "n_fijo": []}}
    if salida["errores"]:
        return salida
    cta = salida["cuenta"]
    specs = {k: {c: d["dev"][k][c] for c in ("kva", "kva2", "volt", "volt2", "conex", "conex2", "bil")} for k in CLAVES}
    if o["dn_fijo"] > 0:
        dns = [o["dn_fijo"]]
    else:
        dns, i = [], 0
        while o["dn_min"] + i * o["dn_paso"] <= o["dn_max"] + 1e-9:
            dns.append(math.floor((o["dn_min"] + i * o["dn_paso"]) * 1000 + 0.5) / 1000)
            i += 1
    err, prueba = calcular_electrico(specs, d["frec"], d["tap"], d["variacion"], d["pasos"], d["rep"], 1e5, d["bobj"], 1)
    if err:
        salida["errores"] = err
        return salida
    activos, sec = prueba["activos"], prueba["secundarios"][0]
    optimiza = ["I", sec]
    posiciones = [d["dev"][k]["pos"] for k in activos]
    if len(set(posiciones)) != len(posiciones):
        salida["errores"] = ["Cada devanado debe ir en una posición radial distinta."]
        return salida
    orden = sorted(activos, key=lambda c: d["dev"][c]["pos"])
    vf_ref = min(t["v_fase"] for k in activos for t in prueba["dev"][k]["tensiones"])
    rho_t = RHO_CU_20 * (234.5 + d["tref"]) / (234.5 + 20.0)
    k_term = FASES * DENS_CU / 1e6
    por_n, todos = {}, []
    for dn in dns:
        anchos = anchos_para_dn(d, dn)
        if validar_nucleo(dn, d["g"], 1, d["hc"], FACTOR_ELIPSE, anchos):
            continue
        nuc0 = calcular_nucleo(dn, d["g"], 0, d["hc"], FACTOR_ELIPSE, anchos, d["fa"])
        nuc1 = calcular_nucleo(dn, d["g"], 1, d["hc"], FACTOR_ELIPSE, anchos, d["fa"])
        w0, w1, s_neta = nuc0["peso"], nuc1["peso"] - nuc0["peso"], nuc0["seccion_neta"]
        area = s_neta / 1e6
        cta["dn"] += 1
        # espiras: las mismas del diseño, REDONDEO.MAS con la B máxima (el diseño ya no las da a mano)
        n_lo = max(1, int(redondeo_mas(vf_ref / (K_FEM * d["frec"] * o["bmax"] * area), 0)))
        n_hi = math.floor(vf_ref / (K_FEM * d["frec"] * o["bmin"] * area) + 1e-9)
        if n_hi < n_lo:
            b_de = lambda n_: vf_ref / n_ / (K_FEM * d["frec"] * area)
            cta["sin_n"].append({"dn": dn, "n1": n_hi, "b1": b_de(n_hi) if n_hi >= 1 else None, "n2": n_lo, "b2": b_de(n_lo)})
        for N in ([n_lo] if n_lo <= n_hi else []):        # B de esas espiras dentro del rango
            if N not in por_n:
                errores, elec = calcular_electrico(specs, d["frec"], d["tap"], d["variacion"], d["pasos"], d["rep"],
                                                   s_neta, d["bobj"], N)
                ok, err_max = not errores, None
                if ok:
                    errs = [abs(t["error"]) for t in elec["taps"]] + \
                           [abs(t["error"]) for k in elec["activos"] for t in elec["dev"][k]["tensiones"]]
                    err_max = max(errs)
                    ok = err_max <= ERROR_RELACION_MAX     # de 0.3 a 0.5 % procede (se marca en rojo en los resultados)
                    if not ok:
                        cta["n_relacion"].append((N, err_max))
                ent = {"ok": ok, "elec": elec, "cand": {}, "fijos": {}, "err_max": err_max}
                if ok:
                    for k in optimiza:
                        ent["cand"][k] = candidatos_devanado(k, elec, d, o)
                    for k in activos:
                        if k not in optimiza:
                            ent["fijos"][k] = devanado_fijo(k, elec, d)
                            if not ent["fijos"][k]:
                                ent["ok"] = False
                                cta["n_fijo"].append((N, k))
                    for k in optimiza:
                        cta["candidatos"][k] = max(cta["candidatos"].get(k, 0), len(ent["cand"][k]))
                por_n[N] = ent
            ent = por_n[N]
            if not ent["ok"]:
                continue
            cta["n"] += 1
            elec = ent["elec"]
            v_esp = vf_ref / N
            b = v_esp / (K_FEM * d["frec"] * area)
            pfe = perdidas_especificas(b + AUMENTO_B_PERDIDAS, d["frec"])["pfe"]
            at, se = elec["dev"]["I"], elec["dev"][sec]
            s_base = min(at["kva"], se["kva"])
            i_sec = corriente_fase(s_base, se["volt"], se["conex"])
            i_at = corriente_fase(s_base, at["volt"], at["conex"])
            k_r, b_kg, s_fe = k_rogowski(i_sec), b * 10.0, s_neta / 100.0
            for c1 in ent["cand"]["I"]:
                for c2 in ent["cand"][sec]:
                    cta["combinaciones"] += 1
                    elegido = dict(ent["fijos"])
                    elegido["I"], elegido[sec] = c1, c2
                    d_prev, cu, pcu, geo = dn, 0.0, 0.0, {}
                    for k in orden:
                        c, w = elegido[k], d["dev"][k]
                        d_int = d_prev + 2.0 * w["canal"]
                        d_ext = d_int + 2.0 * c["res"]["radial"]
                        d_med = (d_int + d_ext) / 2.0
                        l_esp = math.pi * d_med
                        e = elec["dev"][k]
                        r_fase = rho_t * e["n_nom"] * l_esp / 1000.0 / c["s"]
                        cu += k_term * e["n_max"] * l_esp * c["s"]
                        pcu += FASES * e["i_carga"] ** 2 * r_fase
                        geo[k] = {"d_int": d_int, "d_ext": d_ext, "d_med": d_med, "r_fase": r_fase,
                                  "radial": c["res"]["radial"], "axial": c["res"]["axial_total"], "pos": w["pos"]}
                        d_prev = d_ext
                    d_total = d_prev + 2.0 * d["tubo"]
                    if o["de_max"] > 0:
                        if d_total + d["fases"] > o["de_max"] + 1e-9:
                            cta["rechazo_de"] += 1
                            continue
                        de = o["de_max"]
                    else:
                        de = math.ceil((d_total + d["fases"]) / 5 - 1e-9) * 5
                    g_a, g_s = geo["I"], geo[sec]
                    dentro, fuera = (g_a, g_s) if g_a["pos"] < g_s["pos"] else (g_s, g_a)
                    lam = (fuera["d_int"] - dentro["d_ext"]) / 2.0
                    d_m = (g_a["d_med"] + g_s["d_med"]) / 2.0
                    h_eq = (g_a["axial"] + g_s["axial"]) / 2.0
                    ux = ((se["n_nom"] * i_sec) * (math.pi * d_m) * (lam + (g_a["radial"] + g_s["radial"]) / 3.0)
                          * k_r * K_VCC / (h_eq * b_kg * s_fe))
                    ur = FASES * (i_sec ** 2 * g_s["r_fase"] + i_at ** 2 * g_a["r_fase"]) / (s_base * 10.0)
                    uz = math.hypot(ux, ur)
                    cta["vcc_min"], cta["vcc_max"] = min(cta["vcc_min"], uz), max(cta["vcc_max"], uz)
                    if abs(uz - o["vcc"]) > o["vcc"] * o["tol"] / 100.0 + 1e-12:
                        cta["rechazo_vcc"] += 1
                        continue
                    nucleo = w0 + w1 * de
                    p0 = pfe * nucleo * d["fconst"]
                    todos.append({"dn": dn, "anchos": anchos, "n": N, "b": b, "de": de, "uz": uz, "ux": ux, "ur": ur,
                                  "cobre": cu, "nucleo": nucleo, "p0": p0, "pcu": pcu, "peso": cu + nucleo,
                                  "perdidas": p0 + pcu, "error": ent["err_max"], "devanados": [elegido[k] for k in orden], "d_total": d_total,
                                  "lam": lam, "pareto": False})
    cta["cumplen"] = len(todos)
    salida["avisos"] = explicar_busqueda(cta, o, optimiza, d) + [
        f"{NOMBRES[k]}: sin papel de platina digitado, solo se probaron alambres." for k in optimiza
        if d["dev"][k]["papel"] is None]
    mejor = math.inf
    for r in sorted(todos, key=lambda r: (r["peso"], r["perdidas"])):
        if r["perdidas"] < mejor - 1e-9:
            r["pareto"], mejor = True, r["perdidas"]
    claves = {"peso": lambda r: (r["peso"], r["perdidas"]), "perdidas": lambda r: (r["perdidas"], r["peso"]),
              "vcc": lambda r: (abs(r["uz"] - o["vcc"]), r["peso"]), "cobre": lambda r: (r["cobre"], r["perdidas"])}
    todos.sort(key=claves.get(o["orden"], claves["peso"]))
    salida["todos"] = todos
    for r in todos[:o["max"]]:
        nd = aplicar_alternativa(d, r, o)
        v = calcular_datos(nd)
        igual = lambda a, b_: abs(a - b_) <= 1e-6 * max(1.0, abs(b_))
        r["verificado"] = (not v["errores"] and bool(v.get("pares")) and igual(v["pares"][0]["uz"], r["uz"])
                           and igual(v["mont"]["peso_cu"], r["cobre"]) and igual(v["nuc"]["peso"], r["nucleo"])
                           and igual(v["vacio"]["p0"], r["p0"]) and igual(v["mont"]["perdidas"], r["pcu"])
                           and entra_en_nucleo(v["mont"]))
        r["datos"] = nd
        salida["resultados"].append(r)
    return salida


# =====================================================================
# 6. REPORTES HTML
# =====================================================================
def n(x):
    """Número sin decimales si es entero, si no con 2 decimales."""
    return f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.2f}"


def miles(x, dec=0):
    return f"{x:,.{dec}f}"


TD = 'style="padding: 3px 5px;"'
TDR = 'style="text-align: right; padding: 3px 5px;"'
CAJA_TITULO = ('style="background-color: #f2f2f2; border-bottom: 1px solid black; padding: 5px; '
               'text-align: center; font-weight: bold;"')


def dato(k, v):
    return f"<tr><td {TD}>{k}</td><td {TDR}>{v}</td></tr>"


def caja(titulo, contenido, flex="1"):
    return (f'<div style="flex: {flex}; border: 1px solid black;">'
            f'<div {CAJA_TITULO}>{titulo}</div>{contenido}</div>')


def tabla_datos(filas):
    return f'<table style="width: 100%; font-size: 12px; border-collapse: collapse;">{filas}</table>'


def tabla(encabezados, filas, total=None):
    """Tabla con borde: primera columna a la izquierda, el resto centrado."""
    ths = "".join(f'<th style="padding: 4px 5px;">{h}</th>' for h in encabezados)

    def fila(celdas, estilo=""):
        tds = "".join(
            f'<td style="padding: 3px 5px; text-align: {"left" if i == 0 else "center"};">{c}</td>'
            for i, c in enumerate(celdas))
        return f"<tr{estilo}>{tds}</tr>"

    cuerpo = "".join(fila(f) for f in filas)
    if total:
        cuerpo += fila(total, ' style="background-color: #f2f2f2; font-weight: bold;"')
    return ('<table border="1" style="border-collapse: collapse; width: 100%; font-size: 12px; '
            'border: 2px solid black;">'
            f'<tr style="background-color: #d9d9d9;">{ths}</tr>{cuerpo}</table>')


def subtitulo(texto):
    return (f'<div style="font-weight: bold; font-size: 13px; margin: 15px 0 5px 0; '
            f'border-bottom: 1px solid black;">{texto}</div>')


def hoja(titulo, linea2, derecha, cuerpo):
    """Marco común de todas las hojas: encabezado + cuerpo + pie de firmas."""
    fecha_hoy = datetime.now().strftime("%d-%b-%y")
    celda = 'style="border: 1px solid black; padding: 5px;"'
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 950px; border: 2px solid black; padding: 15px; margin-bottom: 20px; color: black; background-color: white;">

        <!-- ENCABEZADO -->
        <div style="display: flex; justify-content: space-between; border-bottom: 2px solid black; padding-bottom: 10px; margin-bottom: 15px;">
            <div>
                <h2 style="margin: 0; font-size: 24px; font-weight: bold;">HOJA DE DISEÑO</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px;">FECHA: {fecha_hoy}</p>
            </div>
            <div style="text-align: center;">
                <h3 style="margin: 0; font-size: 18px;">{titulo}</h3>
                <p style="margin: 2px 0 0 0; font-size: 14px; font-weight: bold;">{linea2}</p>
            </div>
            <div style="text-align: right;">{derecha}</div>
        </div>

        {cuerpo}

        <!-- PIE DE FIRMAS -->
        <table style="width: 100%; margin-top: 15px; font-size: 12px; text-align: center; border-collapse: collapse; border: 1px solid black;">
            <tr style="background-color: #f2f2f2;">
                <th {celda}>Elab. por</th><th {celda}>fecha</th><th {celda}>firma</th>
                <th {celda}>Rev. por</th><th {celda}>firma</th>
            </tr>
            <tr>
                <td {celda}>J. Peralta</td><td {celda}>{fecha_hoy}</td><td {celda}></td>
                <td {celda}></td><td {celda}></td>
            </tr>
        </table>
    </div>
    """


def html_errores(errores, titulo="Revisa estos datos antes de calcular:"):
    items = "".join(f"<li>{e}</li>" for e in errores)
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 950px; border: 2px solid #c53030; padding: 12px 15px; margin-bottom: 20px; color: #742a2a; background-color: #fff5f5;">
        <b>{titulo}</b>
        <ul style="margin: 6px 0 0 0;">{items}</ul>
    </div>"""


# ---------------------------------------------------------------------
# 6.1 Hoja resumen: especificaciones, cálculo eléctrico y montaje
# ---------------------------------------------------------------------
def svg_montaje(nuc, mont):
    """Media ventana: columna a la izquierda, devanados y plano medio entre columnas."""
    medio = nuc["de"] / 2.0
    hc = nuc["hc"]
    ancho_max = max(medio, mont["d_total"] / 2.0)
    alto_max = max(hc, mont["hc_min"])
    s = min(330.0 / ancho_max, 280.0 / alto_max)
    yugo = 16
    x0, y0 = 30, 8 + yugo + max((alto_max - hc) / 2.0 * s, 0)
    w_vent, h_vent = medio * s, hc * s
    w_tot = max(ancho_max * s, w_vent)
    gris = 'fill="#bdbdbd" stroke="#555" stroke-width="0.8"'
    p = [
        f'<rect x="{x0}" y="{y0 - yugo:.1f}" width="{w_vent:.1f}" height="{yugo}" {gris}/>',
        f'<rect x="{x0}" y="{y0 + h_vent:.1f}" width="{w_vent:.1f}" height="{yugo}" {gris}/>',
        f'<rect x="{x0}" y="{y0:.1f}" width="{nuc["dn"] / 2.0 * s:.1f}" height="{h_vent:.1f}" {gris}/>',
        f'<line x1="{x0}" y1="{y0 - yugo - 6:.1f}" x2="{x0}" y2="{y0 + h_vent + yugo + 6:.1f}" '
        f'stroke="black" stroke-width="0.8" stroke-dasharray="8 3 2 3"/>',
        f'<line x1="{x0 + w_vent:.1f}" y1="{y0 - yugo - 6:.1f}" x2="{x0 + w_vent:.1f}" '
        f'y2="{y0 + h_vent + yugo + 6:.1f}" stroke="#c53030" stroke-width="0.8" stroke-dasharray="4 3"/>',
    ]
    for f in mont["filas"]:
        x = x0 + f["d_int"] / 2.0 * s
        w = f["radial"] * s
        y_sup = y0 + (hc - f["axial"]) / 2.0 * s
        no_cabe = f["margen_hc"] < 0 or (f["pos"] == mont["filas"][-1]["pos"] and mont["margen_de"] < 0)
        borde = 'stroke="#c53030" stroke-width="1.6"' if no_cabe else 'stroke="#333" stroke-width="0.8"'
        for k in range(f["n_sec"]):
            y = y_sup + k * (f["axial_seccion"] + SEPARACION_GALLETA) * s
            p.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{f["axial_seccion"] * s:.1f}" '
                     f'fill="{COLORES[f["clave"]]}" {borde}/>')
        yc = y0 + h_vent / 2.0
        p.append(f'<text x="{x + w / 2.0:.1f}" y="{yc:.1f}" font-size="10" text-anchor="middle" '
                 f'stroke="white" stroke-width="2.5" paint-order="stroke" '
                 f'transform="rotate(-90 {x + w / 2.0:.1f} {yc:.1f})" dy="3">{f["nombre"]}</text>')
    if mont["tubo"] > 0:
        alto_tubo = max(f["axial"] for f in mont["filas"])
        p.append(f'<rect x="{x0 + mont["d_dev"] / 2.0 * s:.1f}" y="{y0 + (hc - alto_tubo) / 2.0 * s:.1f}" '
                 f'width="{max(mont["tubo"] * s, 1.5):.1f}" height="{alto_tubo * s:.1f}" '
                 f'fill="#6b4f2a" stroke="#3d2c14" stroke-width="0.5"/>')
    yt = y0 + h_vent + yugo + 18
    p.append(f'<text x="{x0}" y="{yt:.1f}" font-size="10">eje columna</text>')
    p.append(f'<text x="{x0 + w_vent:.1f}" y="{yt:.1f}" font-size="10" text-anchor="end" fill="#c53030">'
             f'De/2 = {n(medio)}</text>')
    p.append(f'<text x="{x0 - 8}" y="{y0 + h_vent / 2.0:.1f}" font-size="10" text-anchor="middle" '
             f'transform="rotate(-90 {x0 - 8} {y0 + h_vent / 2.0:.1f})">Hc = {n(hc)}</text>')
    w_svg = x0 + w_tot + 12
    h_svg = yt + 8 + max((alto_max - hc) / 2.0 * s, 0)
    return (f'<svg width="{w_svg:.0f}" height="{h_svg:.0f}" viewBox="0 0 {w_svg:.0f} {h_svg:.0f}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(p)}</svg>')


# ---------------------------------------------------------------------
# 6. Esfuerzos dieléctricos (hoja de esfuerzos): tensión de prueba industrial / distancia
#   Núcleo – bobina más interna: E = prueba industrial / (canal interior + tubo núcleo–bobina) < 1.8 kV/mm (máx. 2)
#   Bobina – bobina, por contorneo: E = prueba industrial (la mayor de las dos) / contorno < 0.8 kV/mm, con
#     lado = canal interior / 2 a cada lado de la barrera · s = tubo rígido / 2 (sobresale por lado) · R = radial de la bobina de afuera
#     d1 = √(lado² + (relleno de adentro + s)²) · d2 = lado + 0.75·R · d3 = √((0.75·R)² + s²) · d4 = relleno de afuera
#     d5 = √((relleno de afuera + s)² + lado²) · contorno HAWAYANO = d1 + barrera + d2 + d3 + d4 · TUBO = d1 + barrera + d5
# ---------------------------------------------------------------------
ESFUERZO_BOB_BOB = 0.8          # kV/mm
ESFUERZO_BOB_NUC = 1.8          # kV/mm
ESFUERZO_BOB_NUC_MAX = 2.0      # kV/mm: de 1.8 a 2 se marca en rojo pero procede
FACTOR_RADIAL_CONTORNO = 0.75   # el contorno recorre 3/4 del radial de la bobina de afuera
BARRERAS = ["HAWAYANO", "TUBO"]


def uno(x):
    """1 decimal con el .5 hacia arriba (igual que en la página web: 26.25 -> 26.3)."""
    return f"{math.floor(x * 10 + 0.5) / 10:.1f}"


def kvmm(E):
    return f"{E:.2f}" if E != math.inf else "∞"      # sin distancia: esfuerzo infinito


def errores_esfuerzos(d, elec):
    err = []
    if min(d["e_barrera"], d["tubo_rigido"], d["tubo_nucleo"]) < 0:
        err.append("Esfuerzos: la barrera, el tubo rígido y el tubo núcleo–bobina no pueden ser negativos.")
    if d["barrera"] not in BARRERAS:
        err.append("Esfuerzos: la barrera entre bobinas es HAWAYANO o TUBO.")
    if elec:
        for k in elec["activos"]:
            if d["dev"][k]["relleno"] < 0 or d["dev"][k]["industrial"] < 0:
                err.append(f"{NOMBRES[k]}: el relleno y la tensión de prueba industrial no pueden ser negativos.")
    return err


def esfuerzos_dielectricos(mont, dev, d):
    """Esfuerzo núcleo – bobina más interna y, por contorneo, entre cada par de bobinas vecinas."""
    out, f = [], mont["filas"]
    if not f:
        return out
    a = f[0]
    ua = dev[a["clave"]]["industrial"]
    dist0 = a["canal"] + d["tubo_nucleo"]
    e0 = ua / dist0 if dist0 > 0 else math.inf
    out.append({"clave": f"nuc-{a['clave']}", "tipo": "bob-nuc", "nombre": f"Núcleo – {a['nombre']}", "tension": ua,
                "distancia": dist0, "esfuerzo": e0, "partes": None, "lineas": [
                    f"Distancia = canal interior del {a['nombre']} + tubo núcleo–bobina = {n(a['canal'])} + "
                    f"{d['tubo_nucleo']:g} = {n(dist0)} mm",
                    f"E = prueba industrial {a['nombre']} / distancia = {ua:g} kV / {n(dist0)} mm = {kvmm(e0)} kV/mm"]})
    for i in range(1, len(f)):
        bi, bo = f[i - 1], f[i]
        wi, wo = dev[bi["clave"]], dev[bo["clave"]]
        lado, s_, R = bo["canal"] / 2, d["tubo_rigido"] / 2, FACTOR_RADIAL_CONTORNO * bo["radial"]
        eb = d["e_barrera"]
        d1, d2, d3 = math.hypot(lado, wi["relleno"] + s_), lado + R, math.hypot(R, s_)
        d4, d5 = wo["relleno"], math.hypot(wo["relleno"] + s_, lado)
        tubo = d["barrera"] == "TUBO"
        total = d1 + eb + d5 if tubo else d1 + eb + d2 + d3 + d4
        U = max(wi["industrial"], wo["industrial"])
        E = U / total if total > 0 else math.inf
        lineas = [
            f"lado = canal interior del {bo['nombre']} / 2 = {n(bo['canal'])} / 2 = {n(lado)} mm · s = tubo rígido / 2 = "
            f"{d['tubo_rigido']:g} / 2 = {s_:g} mm · 0.75·R = 0.75 x {n(bo['radial'])} = {n(R)} mm",
            f"d1 = √(lado² + (relleno {bi['nombre']} + s)²) = √({n(lado)}² + ({wi['relleno']:g} + {s_:g})²) = {uno(d1)} mm"]
        if tubo:
            lineas += [f"d5 = √((relleno {bo['nombre']} + s)² + lado²) = √(({wo['relleno']:g} + {s_:g})² + {n(lado)}²) = {uno(d5)} mm",
                       f"Contorno (TUBO) = d1 + tubo + d5 = {uno(d1)} + {eb:g} + {uno(d5)} = {uno(total)} mm"]
        else:
            lineas += [f"d2 = lado + 0.75·R = {n(lado)} + {n(R)} = {uno(d2)} mm · d3 = √((0.75·R)² + s²) = √({n(R)}² + {s_:g}²) = "
                       f"{uno(d3)} mm · d4 = relleno {bo['nombre']} = {d4:g} mm",
                       f"Contorno (HAWAYANO) = d1 + hawayano + d2 + d3 + d4 = {uno(d1)} + {eb:g} + {uno(d2)} + {uno(d3)} + {uno(d4)} = "
                       f"{uno(total)} mm"]
        lineas.append(f"E = prueba industrial (la mayor: {U:g} kV) / contorno = {U:g} / {uno(total)} = {kvmm(E)} kV/mm")
        out.append({"clave": f"bob-{bi['clave']}-{bo['clave']}", "tipo": "bob-bob", "nombre": f"{bi['nombre']} – {bo['nombre']}",
                    "tension": U, "distancia": total, "esfuerzo": E,
                    "partes": {"d1": d1, "e": eb, "d2": d2, "d3": d3, "d4": d4, "d5": d5}, "lineas": lineas})
    return out


def limite_esfuerzo(x):
    """Bobina–bobina hasta 0.8 kV/mm; núcleo–bobina hasta 1.8 kV/mm y de 1.8 a 2 en rojo pero procede."""
    E = x["esfuerzo"]
    base = {"clave": f"esf-{x['clave']}", "paso": 4, "nombre": f"Esfuerzo {x['nombre']}",
            "valor": f"{E:.2f} kV/mm" if E != math.inf else "sin distancia", "formula": "; ".join(x["lineas"])}
    if x["tipo"] == "bob-bob":
        u = E / ESFUERZO_BOB_BOB
        return {**base, "limite": f"máx. {ESFUERZO_BOB_BOB:g} kV/mm", "uso": u,
                "estado": "no" if u > 1 + 1e-9 else "cerca" if u >= 0.9 - 1e-12 else "ok", "nota": ""}
    u = E / ESFUERZO_BOB_NUC
    est = ("no" if E > ESFUERZO_BOB_NUC_MAX + 1e-9 else "procede" if E > ESFUERZO_BOB_NUC + 1e-9
           else "cerca" if u >= 0.9 - 1e-12 else "ok")
    return {**base, "limite": f"{ESFUERZO_BOB_NUC:g} kV/mm (máx. {ESFUERZO_BOB_NUC_MAX:g})", "uso": u, "estado": est,
            "nota": (f"de {ESFUERZO_BOB_NUC:g} a {ESFUERZO_BOB_NUC_MAX:g} kV/mm, procede" if est == "procede"
                     else f"pasa de {ESFUERZO_BOB_NUC_MAX:g} kV/mm" if est == "no" else "")}


def limites_diseno(nuc, elec, mont, pares, cond=None, esf=None):
    """Límites del diseño con su % de uso (uso = exigido / disponible; más de 100 % no cumple, desde 90 % está cerca).
    cond: tus condiciones {jmax, bmin, bmax, vcc, tol} (las que falten no se verifican)."""
    cond = cond or {}
    L = []

    def estado(uso):
        return "no" if uso > 1 + 1e-9 else "cerca" if uso >= 0.9 - 1e-12 else "ok"

    def uso_min(minimo, real):
        return 0.0 if minimo <= 0 else minimo / real if real > 0 else math.inf

    u = uso_min(mont["entre_fases"], mont["entre_fases_real"])
    L.append({"clave": "fases", "paso": 4, "nombre": "Entre fases", "valor": f"{n(mont['entre_fases_real'])} mm",
              "limite": f"mín. {n(mont['entre_fases'])} mm", "uso": u, "estado": estado(u),
              "nota": f"faltan {n(mont['entre_fases'] - mont['entre_fases_real'])} mm" if estado(u) == "no" else "",
              "formula": f"De − Ø exterior con tubo = {n(nuc['de'])} − {n(mont['d_total'])} = {n(mont['entre_fases_real'])} mm; "
                         f"uso = mínimo / real = {n(mont['entre_fases'])} / {n(mont['entre_fases_real'])}"})
    for f in mont["filas"]:
        u = uso_min(f["yugo"], f["al_yugo"])
        # con «Ajustar a la ventana» el devanado llena la altura hasta el mínimo: estar cerca es lo buscado, no un aviso
        ajustado = f["ventana"] and u <= 1 + 1e-9
        est = "ok" if ajustado else estado(u)
        L.append({"clave": f"yugo-{f['clave']}", "paso": 4, "nombre": f"Al yugo · {f['nombre']}", "valor": f"{n(f['al_yugo'])} mm",
                  "limite": f"mín. {n(f['yugo'])} mm", "uso": u, "estado": est,
                  "nota": (f"faltan {n(f['yugo'] - f['al_yugo'])} mm por lado" if est == "no"
                           else "ajustado a la ventana" if ajustado else ""), "ajustado": ajustado,
                  "formula": f"(Hc − axial) / 2 = ({n(nuc['hc'])} − {n(f['axial'])}) / 2 = {n(f['al_yugo'])} mm; "
                             f"uso = mínimo / real = {n(f['yugo'])} / {n(f['al_yugo'])}"})
    # canales internos: van entre conductores vecinos en la dirección radial, dentro de la espira (entre sus conductores
    # radiales) y, si el devanado tiene varias capas, también entre capas: caben radiales x capas − 1
    for f in mont["filas"]:
        if f["n_canales"] > 0:
            huecos = f["radiales"] * f["capas"]
            caben = max(huecos - 1, 0)
            u_c = f["n_canales"] / caben if caben > 0 else math.inf
            est = "no" if f["n_canales"] > caben else "ok"
            capa_t = "capa" if f["capas"] == 1 else "capas"
            L.append({"clave": f"canales-{f['clave']}", "paso": 3, "nombre": f"Canales internos · {f['nombre']}",
                      "valor": f"{f['n_canales']} entre {huecos} conductores radiales",
                      "limite": f"máx. {caben} (radiales x capas − 1)", "uso": u_c,
                      "estado": est, "nota": f"caben {caben}" if est == "no" else "",
                      "formula": f"los canales van entre conductores vecinos en la dirección radial (dentro de la espira y entre "
                                 f"capas): {f['radiales']} {'radial' if f['radiales'] == 1 else 'radiales'} x {f['capas']} {capa_t} − 1 = "
                                 f"{caben} {'espacio' if caben == 1 else 'espacios'}; uso = {f['n_canales']} / {caben}"})
    for x in esf or []:
        L.append(limite_esfuerzo(x))
    if not _vacio(cond.get("jmax")) and cond["jmax"] > 0:
        for f in mont["filas"]:
            e = elec["dev"][f["clave"]]
            sec = e["i_max"] / f["j_max"]
            u = f["j_max"] / cond["jmax"]
            L.append({"clave": f"j-{f['clave']}", "paso": 3, "nombre": f"Densidad · {f['nombre']}", "valor": f"{f['j_max']:.2f} A/mm²",
                      "limite": f"máx. {cond['jmax']:g} A/mm²", "uso": u, "estado": estado(u),
                      "formula": f"J = I máxima / sección = {e['i_max']:.2f} / {sec:.2f} = {f['j_max']:.2f} A/mm²; "
                                 f"uso = {f['j_max']:.2f} / {cond['jmax']:g}"})
    if not _vacio(cond.get("bmax")) and cond["bmax"] > 0:
        b = elec["b_real"]
        bajo = not _vacio(cond.get("bmin")) and b < cond["bmin"] - 1e-9
        u = b / cond["bmax"]
        limite = f"máx. {cond['bmax']:g} T" if _vacio(cond.get("bmin")) else f"{cond['bmin']:g} a {cond['bmax']:g} T"
        L.append({"clave": "b", "paso": 2, "nombre": "Inducción B", "valor": f"{b:.3f} T", "limite": limite, "uso": u,
                  "estado": "no" if bajo else estado(u), "nota": f"bajo el mínimo de {cond['bmin']:g} T" if bajo else "",
                  "formula": f"B = V/espira / (4.44 · f · sección neta) = {elec['v_esp']:.3f} / (4.44 · {elec['frecuencia']:g} · "
                             f"{elec['seccion_neta'] / 1e6:.5f}) = {b:.3f} T; uso = {b:.3f} / {cond['bmax']:g}"})
    errs = [abs(t["error"]) for t in elec["taps"]] + [abs(t["error"]) for k in elec["activos"] for t in elec["dev"][k]["tensiones"]]
    mx = max(errs)
    u = mx / ERROR_RELACION_MAX
    er, A, M = estado_error(mx), f"{ERROR_RELACION_AVISO:g}", f"{ERROR_RELACION_MAX:g}"
    L.append({"clave": "relacion", "paso": 3, "nombre": "Error de relación", "valor": f"{mx:.2f} %", "limite": f"máx. {M} % · rojo desde {A} %",
              "uso": u, "estado": er,
              "nota": f"de {A} a {M} %, procede" if er == "procede" else f"pasa de {M} %, no procede" if er == "no" else "",
              "formula": f"el mayor error entre tensiones y tomas = {mx:.2f} %; uso = {mx:.2f} / {M}. Hasta {A} % cumple; de {A} a "
                         f"{M} % se marca en rojo pero procede; más de {M} % no procede"})
    if not _vacio(cond.get("vcc")) and not _vacio(cond.get("tol")) and cond["vcc"] > 0 and cond["tol"] > 0:
        for p in pares:
            tol_abs = cond["vcc"] * cond["tol"] / 100.0
            u = abs(p["uz"] - cond["vcc"]) / tol_abs
            L.append({"clave": f"vcc-{p['clave']}", "paso": 5, "nombre": f"Vcc · {p['par']}", "valor": f"{p['uz']:.2f} %",
                      "limite": f"{cond['vcc']:g} ± {cond['tol']:g} %", "uso": u, "estado": estado(u),
                      "formula": f"|Vcc − objetivo| / tolerancia = |{p['uz']:.2f} − {cond['vcc']:g}| / ({cond['vcc']:g} x "
                                 f"{cond['tol']:g} %) = {abs(p['uz'] - cond['vcc']):.2f} / {tol_abs:.3f}"})
    return L


def limite_gobernante(L):
    """El límite que gobierna: el que no cumple o, si todos cumplen, el de mayor uso."""
    if not L:
        return None
    malos = [x for x in L if x["estado"] == "no"]
    grupo = malos or [x for x in L if not x.get("ajustado")] or L
    mejor = grupo[0]
    for x in grupo[1:]:
        if x["uso"] > mejor["uso"]:
            mejor = x
    return mejor


def pct_texto(uso):
    """% de uso como texto, igual que en la página web: hasta 100 % se trunca y desde ahí se sube
    (89.7 % se lee 89 % y cumple; 100.4 % se lee 101 % y no cumple)."""
    if uso == math.inf or uso > 9.99:
        return "> 999 %"
    return f"{math.floor(uso * 100 + 1e-9) if uso <= 1 else math.ceil(uso * 100 - 1e-9)} %"


def desc_limite(x):
    return f"{x['nombre']}: {x['nota']}" if x.get("nota") else f"{x['nombre']} · {pct_texto(x['uso'])}"


PASOS = [(1, "Datos del cliente"), (2, "Núcleo"), (3, "Devanados"), (4, "Distancias"), (5, "Resultados")]
ULTIMO_PASO = len(PASOS)        # el de resultados
PESO_ESTADO = {"ok": 0, "cerca": 1, "procede": 2, "no": 3}


def estado_pasos(det, errores, L, nuc_ok):
    """Estado de cada paso para la barra de pasos: ok · cerca · falta · no · pend, con un texto corto.
    det = faltantes_detalle(d); errores = los que impiden calcular; L = limites_diseno (None si no se calculó);
    nuc_ok = el núcleo se pudo calcular."""
    def peor(lista):
        m = lista[0]
        for b in lista[1:]:
            if PESO_ESTADO[b["estado"]] > PESO_ESTADO[m["estado"]] or (b["estado"] == m["estado"] and b["uso"] > m["uso"]):
                m = b
        return m

    out = []
    for p, nombre in PASOS:
        falta = sum(1 for x in det if x["paso"] == p)
        if p < ULTIMO_PASO and falta:
            estado, texto = "falta", f"Faltan {falta} {'dato' if falta == 1 else 'datos'}"
        elif p == ULTIMO_PASO and det:
            estado, texto = "pend", (f"Faltan {len(det)} {'dato' if len(det) == 1 else 'datos'} en los pasos 1 a "
                                     f"{ULTIMO_PASO - 1}")
        elif L is None:
            # sin núcleo, lo que hay que revisar está en el núcleo; con núcleo, en los devanados
            aqui = errores and ((p == 2 and not nuc_ok) or (p == 3 and nuc_ok))
            if aqui:
                estado, texto = "no", f"Revisar {len(errores)} {'dato' if len(errores) == 1 else 'datos'}"
            elif p == ULTIMO_PASO or (p == 4 and errores) or (p == 3 and not nuc_ok):
                estado, texto = "pend", "Se calcula al completar lo anterior"
            else:
                estado, texto = "ok", "Completo"
        else:
            mios = L if p == ULTIMO_PASO else [x for x in L if x["paso"] == p]
            if not mios:
                estado, texto = "ok", "Completo"
            else:
                w = limite_gobernante(L) if p == ULTIMO_PASO else peor(mios)
                hay = next((e for e in ("no", "procede", "cerca") if any(x["estado"] == e for x in mios)), "ok")
                estado = hay
                texto = (f"Gobierna: {desc_limite(w)}" if p == ULTIMO_PASO else f"Cumple · máx. {pct_texto(w['uso'])}" if hay == "ok"
                         else desc_limite(w))
        out.append({"paso": p, "nombre": nombre, "estado": estado, "texto": texto})
    return out


def explicaciones_resultados(nuc, elec, mont, pares, vac):
    """Fórmula con los valores de cada resultado principal y de dónde sale (se ve al abrir el resultado)."""
    X = []
    for p in pares:
        X.append({"clave": f"vcc-{p['clave']}", "nombre": f"Vcc {PRINCIPAL}–{p['clave']}", "valor": f"{p['uz']:.2f} %", "lineas": [
            f"Vcc_reactiva = (N·I)·(π·Dm)·(λ + (e1 + e2)/3)·kR·K / (Heq·B·Sfe) = ({p['n']}·{p['i']:.2f})·(π·{p['d_m']:.1f})·"
            f"({n(p['lam'])} + ({n(p['e_pri'])} + {n(p['e_sec'])})/3)·{p['k_r']:g}·{K_VCC:g} / ({n(p['h_eq'])}·{p['b_kg']:.3f}·"
            f"{p['s_fe']:.2f}) = {p['ux']:.4f} %",
            f"Vcc_activa = Pcu / (S·10) = {p['perdidas']:.1f} / ({p['s_base']:g}·10) = {p['ur']:.4f} %",
            f"Vcc = √(Vcc_reactiva² + Vcc_activa²) = √({p['ux']:.4f}² + {p['ur']:.4f}²) = {p['uz']:.4f} %"],
            "fuente": f"Cálculo de Vcc · K = {K_VCC:g} con B en kG, Sfe en cm² y medidas en mm · kR del cuadro de Rogowski "
                      f"con I = {p['i']:.1f} A"})
    area = elec["seccion_neta"] / 1e6
    v_ref = elec["v_esp"] * elec["n_ref"]
    ref = elec["dev"][elec["ref"]]
    X.append({"clave": "b", "nombre": "B real", "valor": f"{elec['b_real']:.3f} T", "lineas": [
        f"B = (V/espira) / (4.44 · f · Sn) = {elec['v_esp']:.4f} / (4.44 · {elec['frecuencia']:g} · {area:.6f} m²) = "
        f"{elec['b_real']:.4f} T"],
        "fuente": f"Ley de Faraday E = 4.44·f·N·B·A · Sn = sección neta del núcleo ({nuc['seccion_neta'] / 100:.1f} cm²)"})
    lineas_v = [f"V/espira = V fase de referencia / N de referencia = {v_ref:.2f} / {elec['n_ref']} = {elec['v_esp']:.4f} V"]
    lineas_v.append(f"N de referencia = {elec['n_ref']} (ingresadas a mano)" if elec["n_ref_manual"] else
                    f"N de referencia = REDONDEO.MAS(V fase / (4.44 · f · B objetivo · Sn)) = REDONDEO.MAS({v_ref:.2f} / "
                    f"(4.44 · {elec['frecuencia']:g} · {elec['b_objetivo']:g} · {area:.6f})) = "
                    f"REDONDEO.MAS({elec['n_teorico']:.2f}) = {elec['n_ref']}")
    X.append({"clave": "vesp", "nombre": "V / espira", "valor": f"{elec['v_esp']:.3f} V", "lineas": lineas_v,
              "fuente": f"la menor tensión de fase del diseño: {ref['nombre']}, {elec['ref_volt']:g} V de línea"})
    lineas_cu = [f"{f['nombre']}: {FASES} · ({elec['dev'][f['clave']]['n_max']} esp. · {f['l_espira']:.1f} mm / 1000) · "
                 f"{f['seccion']:.2f} mm² · {DENS_CU:g} / 1000 = {f['peso']:.1f} kg" for f in mont["filas"]]
    lineas_cu.append(f"Total = {' + '.join(format(f['peso'], '.1f') for f in mont['filas'])} = "
                     f"{mont['peso_cu']:.1f} kg")
    X.append({"clave": "cobre", "nombre": f"Cobre {FASES} fases", "valor": f"{mont['peso_cu']:.1f} kg", "lineas": lineas_cu,
              "fuente": f"fases · largo del conductor por fase (espiras x espira media π·Dm) · sección por espira · "
                        f"densidad del cobre {DENS_CU:g} kg/dm³"})
    X.append({"clave": "nucleo", "nombre": "Núcleo", "valor": f"{nuc['peso']:.0f} kg", "lineas": [
        f"Peso = Σ escalones = {' + '.join(format(e['peso'], '.1f') for e in nuc['escalones'])} = "
        f"{nuc['peso']:.1f} kg"],
        "fuente": f"hoja de corte de núcleo · área de cada escalón x espesor x {RHO_FE:g} kg/m³ · plancha de {T_CHAPA:g} mm"})
    X.append({"clave": "p0", "nombre": "Pérdidas en vacío", "valor": f"{miles(vac['p0'])} W", "lineas": [
        f"B para pérdidas = B real + {AUMENTO_B_PERDIDAS:g} = {vac['b_real']:.4f} + {AUMENTO_B_PERDIDAS:g} = {vac['b']:.4f} T",
        f"Pfe = {vac['pfe']:.4f} W/kg (a mano)" if vac["manual"] else
        f"Pfe = c0 + c1·B + c2·B² ({vac['f']:g} Hz) con B = {vac['b']:.4f} T = {vac['pfe']:.4f} W/kg",
        f"P0 = Pfe x peso x factor = {vac['pfe']:.4f} x {vac['peso']:.1f} x {vac['factor']:g} = {vac['p0']:.1f} W"],
        "fuente": f"Curva de pérdidas de la chapa · regresión cuadrática de la tabla {MATERIAL_NUCLEO}"})
    rho = RHO_CU_20 * (234.5 + mont["t_ref"]) / (234.5 + 20)
    lineas_r = [f"ρ a {mont['t_ref']:g} °C = {RHO_CU_20:g} · (234.5 + {mont['t_ref']:g}) / (234.5 + 20) = {rho:.6f} Ω·mm²/m"]
    for f in mont["filas"]:
        lineas_r.append(f"{f['nombre']}: {FASES} · I² · R = {FASES} · {f['i_carga']:.2f}² · {f['r_fase'] * 1000:.3f} mΩ = "
                        f"{f['perdidas']:.1f} W (R = ρ · {elec['dev'][f['clave']]['n_nom']} esp. · {f['l_espira']:.1f} mm / 1000 / "
                        f"{f['seccion']:.2f} mm²)")
    lineas_r.append(f"Total = {' + '.join(format(f['perdidas'], '.1f') for f in mont['filas'])} = {mont['perdidas']:.1f} W")
    X.append({"clave": "pcu", "nombre": "Pérdidas I²R carga", "valor": f"{miles(mont['perdidas'])} W", "lineas": lineas_r,
              "fuente": f"corriente continua con el reparto de carga {elec['rep_carga']}; sin pérdidas adicionales"})
    return X


def estado_error(e):
    """ok (hasta 0.3 %) · procede (de 0.3 a 0.5 %: en rojo pero procede) · no (más de 0.5 %: no procede)."""
    a = abs(e)
    return "no" if a > ERROR_RELACION_MAX else "procede" if a > ERROR_RELACION_AVISO else "ok"


TEXTO_ERROR = {"ok": "cumple", "procede": "en rojo, procede", "no": "no procede"}


def signo_texto(x):
    return ("+" if x >= 0 else "-") + f"{abs(x):.2f}"


def errores_relacion(elec):
    """Punto de verificación del error de relación: cada tensión de cada devanado y cada toma de la regulación."""
    out = []
    for k in elec["activos"]:
        for j, t in enumerate(elec["dev"][k]["tensiones"]):
            out.append({"quien": f"{elec['dev'][k]['nombre']} · {'2ª' if j else '1ª'} tensión {miles(t['volt'])} V",
                        "espiras": t["n"], "error": t["error"], "estado": estado_error(t["error"])})
    for t in elec["taps"]:
        out.append({"quien": f"Toma {t['pos']}{' (nominal)' if t['pos'] == elec['tap_nom'] else ''} · "
                             f"{signo_texto(t['pct'])} % · {miles(t['v_linea'])} V",
                    "espiras": t["espiras"], "error": t["error"], "estado": estado_error(t["error"])})
    return out


def verificaciones(nuc, elec, mont):
    """Lista de (cumple, texto). Las de altura y entre fases dicen si el diseño entra en el núcleo."""
    v = []
    b = elec["b_real"]
    v.append((b <= elec["b_objetivo"] + 1e-9,
              f"Inducción real {b:.3f} T frente al objetivo de {elec['b_objetivo']:g} T."))
    errores_rel = [abs(t["error"]) for t in elec["taps"]] + \
                  [abs(t["error"]) for k in elec["activos"] for t in elec["dev"][k]["tensiones"]]
    er = estado_error(max(errores_rel))
    v.append((True if er == "ok" else "procede" if er == "procede" else False,
              f"Error máximo de relación {max(errores_rel):.2f} % (admisible {ERROR_RELACION_MAX:g} %; en rojo desde "
              f"{ERROR_RELACION_AVISO:g} %){'' if er == 'ok' else ': ' + TEXTO_ERROR[er]}."))
    for f in mont["filas"]:
        if f["margen_yugo"] >= 0:
            txt = f"sobran {n(f['margen_yugo'])} mm"
        else:
            txt = f"<b>faltan {n(-f['margen_yugo'])} mm por lado</b>"
        v.append((f["margen_yugo"] >= 0,
                  f"Altura {f['nombre']}: axial {n(f['axial'])} mm en ventana Hc = {n(nuc['hc'])} mm; al yugo quedan "
                  f"({n(nuc['hc'])} − {n(f['axial'])}) / 2 = {n(f['al_yugo'])} mm (mínimo {n(f['yugo'])}: {txt})."))
    if mont["margen_de"] >= 0:
        txt = f"sobran {n(mont['margen_de'])} mm"
    else:
        txt = f"<b>faltan {n(-mont['margen_de'])} mm</b>"
    v.append((mont["margen_de"] >= 0,
              f"Entre fases: De {n(nuc['de'])} − Ø exterior con tubo {n(mont['d_total'])} "
              f"(Ø último devanado {n(mont['d_dev'])} + 2 x {n(mont['tubo'])}) = {n(mont['entre_fases_real'])} mm "
              f"entre bobinas vecinas (mínimo {n(mont['entre_fases'])}: {txt})."))
    return v


def entra_en_nucleo(mont):
    return all(f["margen_yugo"] >= 0 for f in mont["filas"]) and mont["margen_de"] >= 0


def html_no_entra(nuc, mont):
    """Aviso rojo cuando los devanados no entran en el núcleo (el núcleo es el que limita)."""
    faltas = []
    for f in mont["filas"]:
        if f["margen_yugo"] < 0:
            faltas.append(f"{f['nombre']}: axial {n(f['axial'])} mm en Hc = {n(nuc['hc'])} mm deja "
                          f"{n(f['al_yugo'])} mm al yugo y el mínimo es {n(f['yugo'])} mm "
                          f"(faltan {n(-f['margen_yugo'])} mm por lado).")
    if mont["margen_de"] < 0:
        faltas.append(f"Entre fases: De {n(nuc['de'])} − Ø exterior con tubo {n(mont['d_total'])} = "
                      f"{n(mont['entre_fases_real'])} mm y el mínimo es {n(mont['entre_fases'])} mm "
                      f"(faltan {n(-mont['margen_de'])} mm): las bobinas de fases vecinas quedan muy juntas.")
    if not faltas:
        return ""
    return html_errores(faltas, "Los devanados no entran en el núcleo. Achica el devanado (conductor, capas, "
                                "canales o «Ajustar a la ventana») o cambia el núcleo:")


# ---------------------------------------------------------------------
# 6.1b Verificación del diseño: límites con su % de uso (semáforo) y fórmula de cada resultado
# Color solo para lo anormal: rojo + ✘ = no cumple, ámbar + ⚠ = cerca del límite o falta un dato; lo normal en gris.
# ---------------------------------------------------------------------
C_NO, C_NO_FONDO = "#b42318", "#fdecea"
C_CERCA, C_CERCA_FONDO = "#9a5b00", "#fff4dc"
ICONO = {"ok": "&#10004;", "cerca": "&#9888;", "falta": "&#9888;", "procede": "!", "no": "&#10008;", "pend": "&#9675;"}
TEXTO_ESTADO = {"ok": "cumple", "cerca": "cerca del límite", "procede": "en rojo", "no": "no cumple"}
COLOR_ESTADO = {"ok": "#333333", "cerca": C_CERCA, "falta": C_CERCA, "procede": C_NO, "no": C_NO, "pend": "#6b7680"}


def texto_error(e, corto=False):
    """Error de relación en una celda: normal hasta 0.3 %; en rojo de 0.3 a 0.5 % (procede) y más de 0.5 % (no procede)."""
    er = estado_error(e)
    if er == "ok":
        return f"{e:+.2f}%"
    return (f'<span style="color: {C_NO}; font-weight: bold;">{"&#10008;" if er == "no" else "!"} {e:+.2f}%'
            f'{"" if corto else " · " + TEXTO_ERROR[er]}</span>')


def html_errores_relacion(elec):
    """Punto de verificación del error de relación: cada tensión y cada toma, con su estado."""
    filas = [[x["quien"], x["espiras"], texto_error(x["error"], corto=True),
              f'<span style="color: {COLOR_ESTADO[x["estado"]]}; font-weight: bold;">{ICONO[x["estado"]]} '
              f'{TEXTO_ERROR[x["estado"]]}</span>'] for x in errores_relacion(elec)]
    return (tabla(["Tensión / toma", "Espiras", "Error", "Estado"], filas)
            + f'<div style="font-size: 11px; margin-top: 4px;">Hasta {ERROR_RELACION_AVISO:g} % cumple · de '
              f'{ERROR_RELACION_AVISO:g} a {ERROR_RELACION_MAX:g} % se marca en rojo pero <b>procede</b> · más de '
              f'{ERROR_RELACION_MAX:g} % <b>no procede</b>.</div>')


def condiciones_diseno(d):
    """Condiciones del semáforo: las del propio diseño, no las de la búsqueda. Vcc objetivo y tolerancia (paso 1),
    B mínima y B máxima = objetivo (paso 2), J máxima (paso 3). Las vacías no se verifican."""
    return {"jmax": d.get("j_max"), "bmin": d.get("b_min"), "bmax": d.get("bobj"), "vcc": d.get("vcc_obj"),
            "tol": d.get("vcc_tol")}


def condiciones_faltantes(cond):
    sin = []
    if _vacio(cond.get("vcc")) or _vacio(cond.get("tol")):
        sin.append("Vcc objetivo y tolerancia (paso 1)")
    if _vacio(cond.get("bmax")):
        sin.append("B máxima (paso 2)")
    if _vacio(cond.get("jmax")):
        sin.append("J máxima (paso 3)")
    return sin


def html_verificacion(L, X, cond):
    """Semáforo de límites (% de uso, la raya es el 100 %) y resultados principales con su fórmula."""
    g = limite_gobernante(L)
    orden = sorted(L, key=lambda x: (-PESO_ESTADO[x["estado"]], -x["uso"]))
    filas = ""
    for x in orden:
        e = x["estado"]
        ancho = min(x["uso"] if x["uso"] != math.inf else 1.2, 1.2) / 1.2 * 100
        barra_color = {"ok": "#8a96a2", "cerca": C_CERCA, "procede": C_NO, "no": C_NO}[e]
        fondo = C_NO_FONDO if e in ("no", "procede") else "white"
        nota = f" · {x['nota']}" if x.get("nota") else ""
        filas += (
            f'<tr style="background-color: {fondo};">'
            f'<td style="padding: 4px 6px; text-align: center; color: {COLOR_ESTADO[e]}; font-weight: bold;">{ICONO[e]}</td>'
            f'<td style="padding: 4px 6px;"><details><summary style="cursor: pointer;"><b>{x["nombre"]}</b> '
            f'<span style="color: {COLOR_ESTADO[e]};">· {TEXTO_ESTADO[e]}{nota}</span></summary>'
            f'<div style="font-family: Consolas, monospace; font-size: 11px; margin: 4px 0 2px 0;">{x["formula"]}</div></details></td>'
            f'<td style="padding: 4px 6px; width: 170px;"><div style="position: relative; height: 10px; border: 1px solid #8a96a2; '
            f'background: white;"><div style="position: absolute; left: 0; top: 0; bottom: 0; width: {ancho:.1f}%; '
            f'background: {barra_color};"></div><div style="position: absolute; top: -3px; bottom: -3px; left: 83.3%; width: 2px; '
            f'background: black;"></div></div></td>'
            f'<td style="padding: 4px 6px; text-align: right; font-weight: bold; color: {COLOR_ESTADO[e]}; white-space: nowrap;">'
            f'{pct_texto(x["uso"])}</td>'
            f'<td style="padding: 4px 6px; white-space: nowrap;">{x["valor"]} · {x["limite"]}</td></tr>')
    sin = condiciones_faltantes(cond)
    nota_sin = (f'<div style="font-size: 11px; margin-top: 4px;">Sin {", ".join(sin)}: no se verifica'
                f'{"n" if len(sin) > 1 else ""}.</div>' if sin else "")
    cajas = ""
    for x in X:
        lineas = "".join(f'<div style="margin: 2px 0;">{t}</div>' for t in x["lineas"])
        cajas += (f'<details style="border: 1px solid #b7c0c8; padding: 5px 8px; background: white;">'
                  f'<summary style="cursor: pointer;"><span style="font-size: 11px; color: #555;">{x["nombre"].upper()}</span> '
                  f'<b style="font-size: 15px;">{x["valor"]}</b></summary>'
                  f'<div style="font-family: Consolas, monospace; font-size: 11px; margin-top: 4px;">{lineas}</div>'
                  f'<div style="font-size: 11px; color: #555; margin-top: 4px;">Fuente: {x["fuente"]}</div></details>')
    e = g["estado"]
    return f"""
    <div style="font-family: Arial, sans-serif; max-width: 950px; border: 2px solid black; padding: 12px 15px; margin-bottom: 20px; color: black; background-color: white; font-size: 12px;">
        <div style="font-weight: bold; font-size: 14px; border-bottom: 1px solid black; padding-bottom: 4px; margin-bottom: 8px;">
            VERIFICACIÓN DEL DISEÑO · % DE USO DE CADA LÍMITE</div>
        <div style="font-size: 13px; margin-bottom: 6px;"><b style="color: {COLOR_ESTADO[e]};">{ICONO[e]}</b> Gobierna:
            <b>{desc_limite(g)}</b> ({TEXTO_ESTADO[e]}).</div>
        <table style="border-collapse: collapse; width: 100%; border: 1px solid #b7c0c8; font-size: 12px;">{filas}</table>
        <div style="font-size: 11px; margin-top: 4px;">Uso = lo exigido / lo disponible. &#10008; más de 100 % no cumple ·
            &#9888; desde 90 % está cerca · ! error de relación de {ERROR_RELACION_AVISO:g} a {ERROR_RELACION_MAX:g} %: en rojo, procede ·
            la raya marca el 100 %. Abre una fila para ver su fórmula.</div>
        {nota_sin}
        <div style="font-weight: bold; font-size: 13px; margin: 12px 0 5px 0;">RESULTADOS PRINCIPALES · abre cada uno para ver su fórmula con los valores</div>
        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(210px, 1fr)); gap: 6px; align-items: start;">{cajas}</div>
    </div>"""


def html_pasos(pasos, det):
    """Barra de pasos con su estado (ícono y texto, color solo si falta algo o no cumple) y los datos que faltan."""
    cajas = ""
    for p in pasos:
        e = p["estado"]
        borde = {"ok": "#6b7680", "pend": "#b7c0c8"}.get(e, COLOR_ESTADO[e])
        cajas += (f'<div style="flex: 1 1 200px; border: 1px solid #b7c0c8; border-left: 5px solid {borde}; padding: 5px 9px; '
                  f'background: white;"><div style="font-weight: bold; font-size: 13px;">{p["paso"]} · {p["nombre"].upper()}</div>'
                  f'<div style="font-size: 12px; color: {COLOR_ESTADO[e]};{" font-weight: bold;" if e not in ("ok", "pend") else ""}">'
                  f'{ICONO[e]} {p["texto"]}</div></div>')
    faltan = ""
    if det:
        grupos = ""
        for paso, nombre in PASOS[:ULTIMO_PASO - 1]:
            xs = [x for x in det if x["paso"] == paso]
            if xs:
                chips = "".join(f'<span style="display: inline-block; border: 1px solid {C_CERCA}; background: {C_CERCA_FONDO}; '
                                f'border-radius: 10px; padding: 1px 8px; margin: 2px 3px 2px 0;">{x["rotulo"]}</span>' for x in xs)
                grupos += f'<div style="margin-top: 3px;"><b>{paso} · {nombre}:</b> {chips}</div>'
        faltan = (f'<div style="margin-top: 6px; padding: 6px 9px; border-left: 4px solid {C_CERCA}; background: white; font-size: 12px;">'
                  f'<b style="color: {C_CERCA};">&#9888; Faltan {len(det)} {"dato" if len(det) == 1 else "datos"} sin fuente</b>: '
                  f'digítalos para calcular (sus celdas están en ámbar).{grupos}</div>')
    return (f'<div style="font-family: Arial, sans-serif; max-width: 1000px; margin: 0 0 8px 0;">'
            f'<div style="display: flex; flex-wrap: wrap; gap: 6px;">{cajas}</div>{faltan}</div>')


# Colores de la tabla de DATOS DE ENTRADA (los de la hoja de Excel)
C_TITULO = "#ed7d31"        # encabezados
C_DATO = "#41b6e6"          # celdas que se ingresan
C_CALC = "#a6a6a6"          # celdas calculadas
C_DENS = "#5fbf7f"          # densidad


def texto_canales(canales):
    """Canales internos como N° x medida (o 0 si no hay)."""
    if not canales:
        return "0"
    if len(set(canales)) == 1:
        return f"{len(canales)} x {canales[0]:g}"
    return " + ".join(f"{c:g}" for c in canales)


def html_tabla_entrada(entrada, bobinado=None):
    """La tabla de DATOS DE ENTRADA tal como queda llena. entrada = resumen_entrada(specs, cond).
    bobinado: {clave: {"pos", "tipo", "papel", "papel_capa", "capas", "epc", "espiras", "canal", "yugo",
    "n_canales", "canal_mm", "transp"}} con textos ya formateados (None = solo la parte eléctrica)."""
    borde = "border: 1px solid black; padding: 3px 6px; text-align: center;"

    def celda(texto, fondo="white", span=1, extra="font-weight: bold;"):
        return f'<td colspan="{span}" style="{borde} background-color: {fondo}; {extra}">{texto}</td>'

    def rotulo(texto, filas=1):
        return (f'<td rowspan="{filas}" style="{borde} text-align: left; font-weight: bold; '
                f'white-space: nowrap;">{texto}</td>')

    def par(k, campo, fondo, formato):
        return "".join(celda(formato(col[campo]) if col["volt"] > 0 else "—", fondo)
                       for col in entrada[k]["columnas"])

    filas = [rotulo("") + "".join(celda(NOMBRES[k].upper(), C_TITULO, 2) for k in CLAVES)]
    potencia = ""
    for k in CLAVES:
        c1, c2 = entrada[k]["columnas"]
        if c2["volt"] > 0 and abs(c2["kva"] - c1["kva"]) > 1e-9:
            potencia += celda(f"{c1['kva']:g}", C_DATO) + celda(f"{c2['kva']:g}", C_DATO)
        else:
            potencia += celda(f"{c1['kva']:g}" if c1["kva"] > 0 else "", C_DATO, 2)
    filas.append(rotulo("POTENCIA (kVA)") + potencia)
    filas.append(rotulo("TENSION (V)") + "".join(par(k, "volt", C_DATO, lambda v: f"{v:g}") for k in CLAVES))
    filas.append(rotulo("GRUPO") + "".join(par(k, "conex", C_DATO, str) for k in CLAVES))
    filas.append(rotulo("BIL (kV)") + "".join(celda(f"{entrada[k]['bil']:g}", C_DATO, 2) for k in CLAVES))
    filas.append(rotulo("CALIBRE CONDUCTOR") + "".join(
        celda(entrada[k]["calibre"], C_DATO) + celda(entrada[k]["aislante"], extra="font-weight: bold; font-style: italic;")
        for k in CLAVES))
    filas.append(rotulo("ARREGLO DE") + "".join(celda("CANTIDAD") + celda("HORIZONTAL") for k in CLAVES))
    filas.append(rotulo("CONDUCTORES") + "".join(
        celda(entrada[k]["cantidad"], C_DATO) + celda(entrada[k]["horizontales"], C_DATO) for k in CLAVES))
    filas.append(rotulo("Ilinea_nominal (A)") + "".join(
        "".join(celda(f"{col['i_linea']:.2f}", C_CALC, extra="") for col in entrada[k]["columnas"]) for k in CLAVES))
    filas.append(rotulo("Ifase_nominal (A)") + "".join(
        "".join(celda(f"{col['i_fase']:.2f}", C_CALC, extra="") for col in entrada[k]["columnas"]) for k in CLAVES))
    filas.append(rotulo("SECCION (mm²)") + "".join(
        celda(f"{entrada[k]['seccion']:.2f}", C_CALC, 2, "") for k in CLAVES))
    filas.append(rotulo("DENSIDAD (A/mm²)") + "".join(
        "".join(celda(f"{col['densidad']:.4f}", C_DENS, extra="") for col in entrada[k]["columnas"]) for k in CLAVES))
    if bobinado:
        def uno(campo, fondo=C_DATO, extra="font-weight: bold;"):
            return "".join(celda(bobinado[k][campo], fondo, 2, extra) for k in CLAVES)

        def dos(titulo, sub1, campo1, sub2, campo2):
            filas.append(rotulo(titulo, 2) + "".join(celda(sub1) + celda(sub2) for k in CLAVES))
            filas.append("".join(celda(bobinado[k][campo1], C_DATO) + celda(bobinado[k][campo2], C_DATO)
                                 for k in CLAVES))

        filas.append(rotulo("POSICION RADIAL") + uno("pos"))
        filas.append(rotulo("TIPO DE DEVANADO") + uno("tipo"))
        dos("AISL. MENOR: PAPEL (mm)", "PLATINA", "papel", "ENTRE CAPAS", "papel_capa")
        filas.append(rotulo("AJUSTE DE CAPAS") + uno("modo"))
        dos("BOBINADO", "N° CAPAS", "capas", "ESP. X CAPA", "epc")
        filas.append(rotulo("ESPIRAS") + uno("espiras", C_CALC, ""))
        dos("AISL. MENOR: CANALES INT.", "N° CANALES", "n_canales", "MEDIDA (mm)", "canal_mm")
        filas.append(rotulo("TRANSPOSICIONES") + uno("transp"))
        dos("AISL. MAYOR (mm)", "CANAL INT.", "canal", "AL YUGO MÍN.", "yugo")
    return ('<table style="border-collapse: collapse; width: 100%; font-size: 12px; border: 2px solid black;">'
            + "".join(f"<tr>{f}</tr>" for f in filas) + "</table>")


TEXTO_MODO = {"ventana": "AJUSTADAS A LA VENTANA", "capas": "INGRESADAS", "epc": "SALEN DE ESP. X CAPA"}


def ecuacion_perdidas(f):
    c = COEF_PERDIDAS[f]
    return (f"Pfe = {c[0]:.5f} {c[1]:+.5f}·B {c[2]:+.5f}·B²").replace("+", "+ ").replace(" -", " − ")


def html_vacio(vac):
    """Desarrollo de las pérdidas en el núcleo (vacío)."""
    b, f = vac["b"], vac["f"]
    filas = [
        ["Inducción real", "V/espira / (4.44 · f · sección neta)", f"{vac['b_real']:.4f} T"],
        ["Inducción para pérdidas B", f"B real + {AUMENTO_B_PERDIDAS:g} = {vac['b_real']:.4f} + {AUMENTO_B_PERDIDAS:g}",
         f"{b:.4f} T"],
        ["Frecuencia", "dato", f"{f:g} Hz"],
        ["Curva de 50 Hz", f"c0 + c1·B + c2·B² con B = {b:.4f}", f"{vac['p50']:.4f} W/kg"],
        ["Curva de 60 Hz", f"c0 + c1·B + c2·B² con B = {b:.4f}", f"{vac['p60']:.4f} W/kg"],
    ]
    if f not in (50, 60):
        filas += [
            ["a (histéresis)", f"(3600·P50 − 2500·P60) / 30000 = (3600 x {vac['p50']:.4f} − 2500 x {vac['p60']:.4f}) / 30000",
             f"{vac['a']:.7f}"],
            ["b (parásitas)", f"(50·P60 − 60·P50) / 30000 = (50 x {vac['p60']:.4f} − 60 x {vac['p50']:.4f}) / 30000",
             f"{vac['bb']:.7f}"],
        ]
        origen = f"a·f + b·f² = {vac['a']:.7f} x {f:g} + {vac['bb']:.7f} x {f:g}²"
    else:
        origen = f"curva de {f:g} Hz"
    if vac["manual"]:
        filas.append(["<b>Pfe</b>", f"dato a mano (la regresión da {vac['pfe_regresion']:.4f} con {origen})",
                      f"<b>{vac['pfe']:.4f} W/kg</b>"])
    else:
        filas.append(["<b>Pfe</b>", origen, f"<b>{vac['pfe']:.4f} W/kg</b>"])
    filas += [
        ["Peso del núcleo", "hoja de corte de núcleo", f"{vac['peso']:.1f} kg"],
        ["Factor de construcción", "dato", f"{vac['factor']:g}"],
        ["<b>P0</b>", f"Pfe x peso x factor = {vac['pfe']:.4f} x {vac['peso']:.1f} x {vac['factor']:g}",
         f"<b>{vac['p0']:,.0f} W</b>"],
    ]
    avisos = []
    if vac["fuera_tabla"]:
        avisos.append(f"La inducción {b:.3f} T está fuera de la tabla ({B_TABLA_MIN:g} a {B_TABLA_MAX:g} T): Pfe es una "
                      f"extrapolación de la regresión.")
    if vac["fuera_frec"]:
        avisos.append(f"La frecuencia {f:g} Hz está fuera de 50–60 Hz: Pfe = a·f + b·f² se extrapola.")
    aviso = "".join(f'<div style="color: #b7791f; font-size: 11px;"><b>Ojo:</b> {a}</div>' for a in avisos)
    return (tabla(["Concepto", "Fórmula", "Valor"], filas) + aviso
            + f'<div style="font-size: 11px; margin-top: 4px; line-height: 1.6;">Regresión cuadrática por mínimos '
              f'cuadrados sobre la tabla {MATERIAL_NUCLEO} ({len(TABLA_PERDIDAS)} puntos, {B_TABLA_MIN:g} a {B_TABLA_MAX:g} T), '
              f'el polinomio de grado 2:<br>50 Hz: <span style="font-family: Consolas, monospace;">'
              f'{ecuacion_perdidas(50)}</span> &nbsp;·&nbsp; 60 Hz: <span style="font-family: Consolas, monospace;">'
              f'{ecuacion_perdidas(60)}</span></div>')


def svg_contorno(x, d, rel_in, rel_out, canal, radial):
    """Dibujo (sin escala) del contorno entre dos bobinas vecinas, en el extremo de arriba: d1, barrera, d2, d3, d4 (HAWAYANO)
    o d1, tubo, d5 (TUBO)."""
    lado, s_, R, e_ = canal / 2, d["tubo_rigido"] / 2, FACTOR_RADIAL_CONTORNO * radial, d["e_barrera"]
    k = 300 / max(30 + 2 * lado + e_ + radial, 1)                 # mm -> px (ancho fijo)
    alto_cu = 60
    y0 = 40 + max(rel_in, rel_out, 1) * k + s_ * k                 # cara de arriba del cobre
    xb = 20                                                        # bobina de adentro: 30 mm dibujados
    xb1, xa = xb + 30 * k + lado * k, xb + 30 * k + lado * k + e_ * k + lado * k
    yt = y0 - (max(rel_in, rel_out) + s_) * k                      # tope de la barrera
    def r(x0, y_, w, h, c, borde="black"):
        return f'<rect x="{x0:.1f}" y="{y_:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{c}" stroke="{borde}" stroke-width="0.8"/>'
    p = [r(xb, y0, 30 * k, alto_cu, "#f2b183"), r(xb, y0 - rel_in * k, 30 * k, rel_in * k, "#2e74b5"),
         r(xa, y0, radial * k, alto_cu, "#f2b183"), r(xa, y0 - rel_out * k, radial * k, rel_out * k, "#2e74b5"),
         r(xb1, yt, max(e_ * k, 2), y0 + alto_cu - yt, "#fde9c4", "#b38f4d")]
    if x["partes"] and d["barrera"] == "HAWAYANO":
        pts = [(xb + 30 * k, y0), (xb1, yt), (xb1 + max(e_ * k, 2), yt), (xa + R * k, yt), (xa, y0 - rel_out * k), (xa, y0)]
        p.append(f'<path d="M{xb1 + max(e_ * k, 2):.1f} {yt:.1f} L{xa + radial * k + 4:.1f} {yt:.1f} L{xa + radial * k + 4:.1f} {yt + 6:.1f}" '
                 f'fill="none" stroke="#4472c4" stroke-width="3"/>')
        nombres = ["d1", "", "d2", "d3", "d4"]
    else:
        pts = [(xb + 30 * k, y0), (xb1, yt), (xb1 + max(e_ * k, 2), yt), (xa, y0)]
        nombres = ["d1", "", "d5"]
    p.append('<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
             + '" fill="none" stroke="#c00000" stroke-width="1.6" stroke-dasharray="4 2"/>')
    desplaza = {"d1": (-18, 4), "d2": (-6, -6), "d3": (-6, 16), "d4": (4, 4), "d5": (6, 4)}    # rótulos fuera de las líneas
    for (a1, b1), (a2, b2), t in zip(pts, pts[1:], nombres):
        if t:
            p.append(f'<text x="{(a1 + a2) / 2 + desplaza[t][0]:.1f}" y="{(b1 + b2) / 2 + desplaza[t][1]:.1f}" font-size="11" '
                     f'font-weight="bold" fill="#c00000">{t}</text>')
    W, H = xa + radial * k + 30, y0 + alto_cu + 8
    return (f'<svg width="{W:.0f}" height="{H:.0f}" viewBox="0 0 {W:.0f} {H:.0f}" style="font-family: Arial;">' + "".join(p)
            + f'<text x="{xb:.1f}" y="{y0 + alto_cu - 4:.1f}" font-size="10">adentro</text>'
            + f'<text x="{xa:.1f}" y="{y0 + alto_cu - 4:.1f}" font-size="10">afuera</text></svg>')


def html_esfuerzos(esf, mont, d):
    """Hoja de esfuerzos: contorneo entre bobinas y núcleo – bobina, con su estado."""
    if not esf:
        return ""
    por = {f["clave"]: f for f in mont["filas"]}
    filas, dibujos = [], ""
    for x in esf:
        L = limite_esfuerzo(x)
        e = L["estado"]
        est = f'<span style="color: {COLOR_ESTADO[e]}; font-weight: bold;">{ICONO[e]} {TEXTO_ESTADO[e]}</span>'
        val = f'<b style="color: {C_NO if e in ("no", "procede") else "black"};">{kvmm(x["esfuerzo"])}</b>'
        if x["tipo"] == "bob-bob":
            q = x["partes"]
            tubo = d["barrera"] == "TUBO"
            filas.append([f"<b>{x['nombre']}</b><br><small>contorneo · {d['barrera']}</small>", val, L["limite"], est,
                          f"{x['tension']:g}", f"<b>{uno(x['distancia'])}</b>", uno(q["d1"]), f"{q['e']:g}",
                          "—" if tubo else uno(q["d2"]), "—" if tubo else uno(q["d3"]), "—" if tubo else uno(q["d4"]),
                          uno(q["d5"]) if tubo else "—"])
            ci, co = x["clave"].split("-")[1:]
            dibujos += (f'<div style="border: 1px solid #b7c0c8; padding: 6px; text-align: center;"><div style="font-size: 11px; '
                        f'font-weight: bold;">{x["nombre"]}</div>'
                        + svg_contorno(x, d, d["dev"][ci]["relleno"], d["dev"][co]["relleno"], por[co]["canal"], por[co]["radial"])
                        + "</div>")
        else:
            filas.append([f"<b>{x['nombre']}</b><br><small>núcleo – bobina</small>", val, L["limite"], est, f"{x['tension']:g}",
                          f"<b>{n(x['distancia'])}</b>", "—", "—", "—", "—", "—", "—"])
    detalle = "".join(f'<div style="margin: 2px 0;"><b>{x["nombre"]}:</b> ' + " · ".join(x["lineas"]) + "</div>" for x in esf)
    return (tabla(["Par", "E (kV/mm)", "Límite", "Estado", "Prueba (kV)", "Distancia (mm)", "d1", "Barrera", "d2", "d3", "d4",
                   "d5"], filas)
            + f'<div style="display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px;">{dibujos}</div>'
            + f'<div style="font-size: 11px; margin-top: 6px; line-height: 1.5;">{detalle}E = tensión de prueba industrial / '
              f'distancia. Entre bobinas se usa la mayor de las dos pruebas y el contorno por encima de la barrera; '
              f'núcleo – bobina: canal interior + tubo. Límites de la hoja de esfuerzos: bobina–bobina {ESFUERZO_BOB_BOB:g} kV/mm; '
              f'núcleo–bobina {ESFUERZO_BOB_NUC:g} kV/mm y de {ESFUERZO_BOB_NUC:g} a {ESFUERZO_BOB_NUC_MAX:g} en rojo pero procede.</div>')


def html_resumen(codigo, specs, cond, bob, nuc, elec, mont, pares, lista, vac, esf=None, datos=None):
    """bob: cómo se bobina cada devanado, tal como está en la tabla (ver leer_bobinado).
    vac: pérdidas en el núcleo (ver calcular_vacio)."""
    dev = elec["dev"]
    at = dev[PRINCIPAL]

    # --- DATOS DE ENTRADA (la misma tabla de la hoja Excel) ---
    generales = (f"Frecuencia <b>{elec['frecuencia']:g} Hz</b> &nbsp;·&nbsp; Reparto BT <b>{elec['rep_carga']}</b>"
                 f" &nbsp;·&nbsp; N° pasos <b>{elec['n_pasos']}</b> &nbsp;·&nbsp; "
                 f"% Variación <b>{elec['variacion']:g}</b> &nbsp;·&nbsp; Tap nominal <b>{elec['tap_nom']}</b>")
    res_tabla = {item["clave"]: item["res"] for item in lista}
    bobinado = {}
    for k in CLAVES:
        b, r = bob[k], res_tabla.get(k)
        if r is None:                       # devanado sin potencia: no se usa
            bobinado[k] = {c: "—" for c in ("pos", "tipo", "papel", "papel_capa", "modo", "capas", "epc",
                                            "espiras", "canal", "yugo", "n_canales", "canal_mm", "transp")}
            continue
        bobinado[k] = {
            "pos": b["pos"], "tipo": r["tipo"], "papel": f"{r['papel']:g}" if r["conductor"] == "PLATINA" else "—",
            "papel_capa": f"{r['papel_capa']:g}", "modo": TEXTO_MODO[b["modo"]], "capas": r["capas"],
            "epc": n(r["esp_por_capa"]), "espiras": r["n_espiras"], "canal": f"{b['canal']:g}", "yugo": f"{b['yugo']:g}",
            "n_canales": b["n_canales"], "canal_mm": "—" if b["canal_mm"] is None else f"{b['canal_mm']:g}",
            "transp": r["transposiciones"],
        }
    bloque_spec = (html_tabla_entrada(resumen_entrada(specs, cond), bobinado)
                   + f'<div style="font-size: 12px; margin-top: 6px;">{generales}</div>')

    # --- 2. NÚCLEO: fija el espacio ---
    ref = dev[elec["ref"]]
    ref_txt = f"{ref['nombre']}, {elec['ref_volt']:g} V"
    origen = "ingresadas" if elec["n_ref_manual"] else f"REDONDEO.MAS({elec['n_teorico']:.2f})"
    filas_flujo = (
        dato("Sección bruta del núcleo", f"{nuc['seccion_bruta'] / 100:.1f} cm²")
        + dato("Factor de apilamiento", f"{nuc['factor_apilamiento']:g}")
        + dato("Sección neta", f"<b>{nuc['seccion_neta'] / 100:.1f} cm²</b>")
        + dato("Inducción objetivo", f"{elec['b_objetivo']:g} T")
        + dato(f"Espiras de referencia ({ref_txt})", f"{elec['n_ref']} ({origen})")
        + dato("Voltios por espira", f"<b>{elec['v_esp']:.3f} V</b>")
        + dato("Inducción real", f"<b>{elec['b_real']:.3f} T</b>")
        + dato("Peso del núcleo", f"{nuc['peso']:.0f} kg")
        + dato(f"Pérdidas específicas Pfe ({MATERIAL_NUCLEO}{', a mano' if vac['manual'] else ''})",
               f"{vac['pfe']:.4f} W/kg")
        + dato("Pérdidas en el núcleo (vacío) P0", f"<b>{vac['p0']:,.0f} W</b>")
    )
    filas_lim = (
        dato("Diámetro del núcleo (Dn)", f"{n(nuc['dn'])} mm")
        + dato("Altura de ventana (Hc): limita la altura", f"<b>{n(nuc['hc'])} mm</b>")
        + dato("Altura que piden los devanados (con el mínimo al yugo)", f"{n(mont['hc_min'])} mm")
        + dato("Distancia entre ejes (De): limita el diámetro", f"<b>{n(nuc['de'])} mm</b>")
        + dato("Ø exterior con tubo", f"{n(mont['d_total'])} mm")
        + dato("De que piden los devanados (con el mínimo entre fases)", f"{n(mont['de_min'])} mm")
    )

    # --- CÁLCULO ELÉCTRICO: una fila por cada tensión ---
    por_clave = {f["clave"]: f for f in mont["filas"]}
    filas_elec = []
    for k in elec["activos"]:
        d, r, m = dev[k], res_tabla[k], por_clave[k]
        for j, tn in enumerate(d["tensiones"]):
            espiras = f"{tn['n']}"
            if j == 0 and k == PRINCIPAL and elec["n_pasos"] > 1:
                espiras += f" (tomas {min(t['espiras'] for t in elec['taps'])}–{max(t['espiras'] for t in elec['taps'])})"
            primera = j == 0
            filas_elec.append([
                f"<b>{d['nombre']}</b>" if primera else "&nbsp;&nbsp;2ª tensión", m["pos"] if primera else "",
                tn["conex"], miles(tn["volt"]), miles(tn["v_fase"], 1),
                f"{tn['i_linea']:.1f}", f"{tn['i_fase']:.1f}", espiras, texto_error(tn["error"]),
                r["tipo"].title() if primera else "",
                f"{r['cantidad']} x {r['nombre'].replace(' mm', '')}" if primera else "",
                f"{r['seccion_total']:.2f}" if primera else "",
                f"{tn['i_fase'] / r['seccion_total']:.2f}",
            ])
    bloque_elec = tabla(["Dev.", "Pos.", "Grupo", "V línea", "V fase", "I línea (A)", "I fase (A)",
                         "Espiras", "Error rel.", "Tipo", "Conductor", "mm²", "J (A/mm²)"], filas_elec)

    # --- REGULACIÓN ---
    filas_tap = []
    for t in elec["taps"]:
        marca = " (nominal)" if t["pos"] == elec["tap_nom"] else ""
        filas_tap.append([f"{t['pos']}{marca}", f"{t['pct']:+.2f}%", miles(t["v_linea"]),
                          t["espiras"], miles(t["v_linea_real"]), texto_error(t["error"])])
    bloque_tap = tabla(["Posición", "Variación", "V línea", "Espiras", "V línea real", "Error"], filas_tap)

    # --- 3. DEVANADOS DENTRO DE LA VENTANA ---
    filas_mont = []
    for f in mont["filas"]:
        r = res_tabla[f["clave"]]
        filas_mont.append([
            f"{f['pos']} · <b>{f['nombre']}</b>", r["tipo"].title(), TEXTO_MODO[bob[f["clave"]]["modo"]].capitalize(),
            r["capas"], n(r["esp_por_capa"]), n(f["canal"]), n(f["d_int"]), n(f["radial"]), n(f["d_ext"]),
            n(f["d_med"]), n(f["axial"]),
        ])
    bloque_mont = tabla(["Pos. · Dev.", "Tipo", "Ajuste de capas", "N° capas", "Esp. x capa", "Canal int.", "Ø int.",
                         "Radial", "Ø ext.", "Ø medio", "Axial"], filas_mont)

    # --- 4. DISTANCIAS ELÉCTRICAS (aislamiento mayor): lo que queda con el núcleo y los devanados fijos ---
    def margen(x):
        if x >= 0:
            return f'<b>+{n(x)}</b>'
        return f'<span style="color: #b42318;"><b>&#10008; −{n(-x)} (faltan)</b></span>'

    filas_dist = []
    anterior = "Núcleo"
    for f in mont["filas"]:
        filas_dist.append([f"{anterior} → {f['nombre']} (canal interior)", "radial", "—", n(f["canal"]), "ingresado"])
        anterior = f["nombre"]
    for f in mont["filas"]:
        filas_dist.append([f"{f['nombre']} → yugo (arriba y abajo)", "axial", n(f["yugo"]), n(f["al_yugo"]),
                           margen(f["margen_yugo"])])
    filas_dist.append(["Tubo enrollado exterior", "radial", "—", n(mont["tubo"]), "ingresado"])
    filas_dist.append(["Entre fases (bobina con bobina)", "radial", n(mont["entre_fases"]),
                       n(mont["entre_fases_real"]), margen(mont["margen_de"])])
    bloque_dist = tabla(["Aislamiento mayor", "Dirección", "Mínimo", "Resultante", "Margen"], filas_dist)
    if mont["margen_de"] > 0:
        nota_dist = (f"Sobran {n(mont['margen_de'])} mm entre fases: se pueden repartir en los canales radiales "
                     f"(1 mm más de canal suma 2 mm al diámetro, o sea hasta {n(mont['margen_de'] / 2)} mm de canal en total).")
    else:
        nota_dist = "No sobra espacio entre fases: no se puede agrandar ningún canal radial sin cambiar el núcleo."

    # --- VERIFICACIONES ---
    items = ""
    for cumple, texto in verificaciones(nuc, elec, mont):
        color, signo = (("#b42318", "!") if cumple == "procede" else ("#333333", "&#10004;") if cumple
                        else ("#b42318", "&#10008;"))
        items += (f'<div style="color: {color}; padding: 2px 0;"><b>{signo}</b> {texto}</div>')

    # --- PESOS, RESISTENCIA Y PÉRDIDAS ---
    filas_cu = []
    for f in mont["filas"]:
        filas_cu.append([
            f"<b>{f['nombre']}</b>", f"{f['l_espira']:.0f}", f"{f['long_fase']:.1f}", f"{f['peso']:.1f}",
            f"{f['r_fase']:.5g}", f"{dev[f['clave']]['reparto']:g}%", f"{f['i_carga']:.1f}",
            miles(f["perdidas"]),
        ])
    bloque_cu = tabla(
        ["Dev.", "Espira media (mm)", "Conductor por fase (m)", f"Cobre {FASES} fases (kg)",
         f"R fase a {mont['t_ref']:g} °C (Ω)", "Carga", "I fase (A)", "I²R (W)"],
        filas_cu,
        total=["TOTAL", "", "", f"{mont['peso_cu']:.1f}", "", "", "", miles(mont["perdidas"])])
    filas_ucc = [[p["par"], miles(p["s_base"]), p["n"], f"{p['i']:.1f}", f"{p['d_m']:.1f}", n(p["lam"]),
                  f"{n(p['e_pri'])} / {n(p['e_sec'])}", n(p["h_eq"]), f"{p['k_r']:g}", f"{p['b_kg']:.2f}",
                  f"{p['s_fe']:.1f}", miles(p["perdidas"]),
                  f"{p['ux']:.2f}%", f"{p['ur']:.2f}%", f"<b>{p['uz']:.2f}%</b>"] for p in pares]
    bloque_ucc = tabla(["Par", "Potencia (kVA)", "N", "I_fase (A)", "Dm", "Lambda", "e (mm)", "Heq", "kR",
                        "B (kG)", "Sfe (cm²)", "Pérdidas (W)", "Vcc_reactiva", "Vcc_Activa", "Vcc"], filas_ucc)
    nota_ucc = (f"Vcc_reactiva = (N·I_fase)·(π·Dm)·(Lambda + (e1 + e2)/3)·kR·K / (Heq·B·Sfe), con K = {K_VCC:g}"
                " &nbsp;·&nbsp; Vcc_Activa = Pérdidas / (Potencia·10) &nbsp;·&nbsp; "
                "Vcc = &radic;(Vcc_reactiva² + Vcc_Activa²). N e I_fase son los del secundario, con la primera "
                "tensión de cada devanado; kR sale del cuadro de Rogowski con esa corriente.")

    cuerpo = f"""
        {subtitulo("1. DATOS DEL CLIENTE Y DATOS DE ENTRADA")}
        {bloque_spec}

        {subtitulo("2. NÚCLEO: FIJA EL ESPACIO (Hc limita la altura de las bobinas y De su diámetro)")}
        <div style="display: flex; gap: 15px;">
            {caja("NÚCLEO Y FLUJO", tabla_datos(filas_flujo))}
            {caja("LÍMITES DEL NÚCLEO", tabla_datos(filas_lim))}
        </div>
        <div style="font-weight: bold; font-size: 13px; margin: 12px 0 5px 0;">PÉRDIDAS EN EL NÚCLEO (VACÍO) · {MATERIAL_NUCLEO}</div>
        {html_vacio(vac)}

        {subtitulo("CÁLCULO ELÉCTRICO")}
        {bloque_elec}
        <div style="font-weight: bold; font-size: 13px; margin: 10px 0 5px 0;">REGULACIÓN EN EL {at['nombre'].upper()} (posición 1 = mayor tensión)</div>
        {bloque_tap}
        <div style="font-weight: bold; font-size: 13px; margin: 10px 0 5px 0;">VERIFICACIÓN DEL ERROR DE RELACIÓN (máx. {ERROR_RELACION_MAX:g} %; en rojo desde {ERROR_RELACION_AVISO:g} %, pero procede)</div>
        {html_errores_relacion(elec)}

        {subtitulo("3. DEVANADOS DENTRO DE LA VENTANA (mm, del núcleo hacia afuera)")}
        {bloque_mont}

        {subtitulo("4. DISTANCIAS ELÉCTRICAS: AISLAMIENTO MAYOR (lo que queda con el núcleo y los devanados ya fijos, en mm)")}
        <div style="display: flex; gap: 15px; align-items: flex-start;">
            <div style="flex: 1.4;">{bloque_dist}<div style="font-size: 11px; margin-top: 4px;">{nota_dist}</div></div>
            {caja("VENTANA (media sección)", f'<div style="text-align: center; padding: 6px;">{svg_montaje(nuc, mont)}</div>', "1")}
        </div>
        {subtitulo("ESFUERZOS DIELÉCTRICOS (hoja de esfuerzos: prueba industrial / distancia)") + html_esfuerzos(esf, mont, datos) if esf else ""}

        {subtitulo("VERIFICACIONES")}
        <div style="font-size: 12px;">{items}</div>

        {subtitulo("COBRE, RESISTENCIA Y PÉRDIDAS EN CARGA")}
        {bloque_cu}
        <div style="font-size: 11px; margin: 4px 0 10px 0;">Pérdidas I²R en corriente continua con el reparto de carga {elec['rep_carga']}; no incluyen pérdidas adicionales.</div>
        {subtitulo("TENSIÓN DE CORTOCIRCUITO (Vcc)")}
        {bloque_ucc}
        <div style="font-size: 11px; margin-top: 4px;">{nota_ucc}</div>
    """
    potencia = f"{miles(at['kva'])} kVA"
    tensiones = " / ".join("–".join(miles(tn["volt"]) for tn in dev[k]["tensiones"])
                           for k in elec["activos"]) + " V"
    derecha = (f'<p style="margin: 0; font-size: 14px; font-weight: bold;">{potencia}</p>'
               f'<p style="margin: 2px 0 0 0; font-size: 12px;">{tensiones}<br>{elec["frecuencia"]:g} Hz</p>')
    return hoja("DISEÑO DE TRANSFORMADOR:", f"{codigo}<br>HOJA DE CÁLCULO", derecha, cuerpo)


# ---------------------------------------------------------------------
# 6.2 Hoja de corte de núcleo
# ---------------------------------------------------------------------
def html_nucleo(nuc, codigo):
    filas_seccion = "".join(
        f"<tr><td>{e['n']}</td><td><b>{e['ancho']}</b></td>"
        f"<td style='color: #2b6cb0;'>{e['ancho_optimo']:.1f}</td><td>{e['espesor']:.2f}</td></tr>"
        for e in nuc["escalones"])
    filas_corte = "".join(
        f"<tr><td>{e['n']}</td><td>{e['espesor']:.2f}</td>"
        f"<td>{e['chapas'] * 2}</td><td>{e['A']:.0f}</td><td>{e['ancho']:.0f}</td>"
        f"<td>{e['chapas'] * 2}</td><td>{e['C']:.0f}</td><td>{e['ancho']:.0f}</td>"
        f"<td>{e['chapas']}</td><td>{e['E']:.0f}</td><td>{e['ancho']:.0f}</td>"
        f"<td><b>{e['peso']:.1f}</b></td></tr>"
        for e in nuc["escalones"])
    filas_datos = (
        dato("Dist. Entre Ejes de Columna (De)", f"{nuc['de']} mm")
        + dato("Altura de Ventana (Hc)", f"{nuc['hc']} mm")
        + dato("Diametro de Nucleo (Dn)", f"{nuc['dn']} mm")
        + dato("Traslape (g)", f"{nuc['g']} mm")
        + dato("Numero de Escalones (Ne)", f"{len(nuc['escalones'])}")
        + dato("Espesor de Plancha", f"{T_CHAPA} mm")
        + dato("Sección neta", f"{nuc['seccion_neta'] / 100:.1f} cm²")
    )
    seccion = f"""
        <table style="width: 100%; font-size: 12px; text-align: center; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #ccc;">
                <th>Escalon</th><th>Ancho Real</th>
                <th style="color: #2b6cb0;">Ancho Ópt. (Tabla)</th><th>Espesor</th>
            </tr>
            {filas_seccion}
            <tr style="border-top: 1px solid black; font-weight: bold;">
                <td colspan="3" style="text-align: right; padding-right: 10px;">ESPESOR TOTAL</td>
                <td>{nuc['espesor_total']:.2f} mm</td>
            </tr>
        </table>"""
    cuerpo = f"""
        <div style="display: flex; gap: 20px; margin-bottom: 15px;">
            {caja("DATOS", tabla_datos(filas_datos))}
            {caja("SECCIÓN", seccion)}
        </div>

        <table border="1" style="border-collapse: collapse; text-align: center; width: 100%; font-size: 12px; border: 2px solid black;">
            <tr style="background-color: #d9d9d9;">
                <th rowspan="2" style="padding: 5px;">ESC.</th>
                <th rowspan="2">Espesor</th>
                <th colspan="3">Columna Lateral</th>
                <th colspan="3">Yugo</th>
                <th colspan="3">Columna Central</th>
                <th rowspan="2">PESO</th>
            </tr>
            <tr style="background-color: #d9d9d9;">
                <th>Cant.</th><th>A</th><th>B</th>
                <th>Cant.</th><th>C</th><th>D</th>
                <th>Cant.</th><th>E</th><th>F</th>
            </tr>
            {filas_corte}
            <tr style="background-color: #f2f2f2; font-size: 14px;">
                <td colspan="11" style="text-align: right; font-weight: bold; padding: 5px 10px;">PESO TOTAL</td>
                <td style="font-weight: bold;">{nuc['peso']:.0f} kg</td>
            </tr>
        </table>
    """
    derecha = '<p style="margin: 0; font-size: 14px; font-weight: bold;">Plancha M4 0.27 mm</p>'
    return hoja("CORTE DE NUCLEO:", f"{codigo}<br>STEP LAP CORE", derecha, cuerpo)


# ---------------------------------------------------------------------
# 6.3 Hoja de cada devanado
# ---------------------------------------------------------------------
def svg_espira(res):
    """Corte de una espira: horizontales (axial, vertical) x radiales (horizontal)."""
    H, R = res["horizontales"], res["radiales"]
    a, e = res["ancho_cond"], res["esp_cond"]
    s = min(220.0 / (R * e), 150.0 / (H * a), 40.0)     # px por mm
    x0, y0 = 34, 14
    W, A = R * e * s, H * a * s
    figs = []
    for i in range(H):
        for j in range(R):
            x, y = x0 + j * e * s, y0 + i * a * s
            if res["conductor"] == "PLATINA":
                p = res["papel"] / 2 * s
                figs.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{e*s:.1f}" height="{a*s:.1f}" '
                            f'fill="#efe4c8" stroke="#8a7a5a" stroke-width="0.6"/>')
                figs.append(f'<rect x="{x+p:.1f}" y="{y+p:.1f}" width="{max(e*s-2*p, 0.5):.1f}" '
                            f'height="{max(a*s-2*p, 0.5):.1f}" fill="#c87533"/>')
            else:
                r = e * s / 2
                figs.append(f'<circle cx="{x+r:.1f}" cy="{y+r:.1f}" r="{max(r-0.6, 0.5):.1f}" '
                            f'fill="#c87533" stroke="#6b3410" stroke-width="1"/>')
    yc = y0 + A + 10          # cota radial (abajo)
    xc = x0 - 12              # cota axial (izquierda)
    ln = 'stroke="black" stroke-width="0.8"'
    cotas = (
        f'<line x1="{x0}" y1="{yc:.1f}" x2="{x0+W:.1f}" y2="{yc:.1f}" {ln}/>'
        f'<line x1="{x0}" y1="{yc-4:.1f}" x2="{x0}" y2="{yc+4:.1f}" {ln}/>'
        f'<line x1="{x0+W:.1f}" y1="{yc-4:.1f}" x2="{x0+W:.1f}" y2="{yc+4:.1f}" {ln}/>'
        f'<text x="{x0+W/2:.1f}" y="{yc+14:.1f}" font-size="11" text-anchor="middle">'
        f'{res["espesor_espira"]:.2f}</text>'
        f'<line x1="{xc}" y1="{y0}" x2="{xc}" y2="{y0+A:.1f}" {ln}/>'
        f'<line x1="{xc-4}" y1="{y0}" x2="{xc+4}" y2="{y0}" {ln}/>'
        f'<line x1="{xc-4}" y1="{y0+A:.1f}" x2="{xc+4}" y2="{y0+A:.1f}" {ln}/>'
        f'<text x="{xc-5}" y="{y0+A/2:.1f}" font-size="11" text-anchor="middle" '
        f'transform="rotate(-90 {xc-5} {y0+A/2:.1f})">{res["ancho_espira"]:.2f}</text>'
    )
    w_svg, h_svg = x0 + W + 8, yc + 20
    return (f'<svg width="{w_svg:.0f}" height="{h_svg:.0f}" viewBox="0 0 {w_svg:.0f} {h_svg:.0f}" '
            f'xmlns="http://www.w3.org/2000/svg">{"".join(figs)}{cotas}</svg>')


def html_devanado(res, codigo, e, m):
    """res: cálculo del devanado · e: datos eléctricos · m: fila de montaje."""
    platina = res["conductor"] == "PLATINA"
    galleta = res["n_sec"] > 1
    H, R = res["horizontales"], res["radiales"]
    canales_txt = texto_canales(res["canales"])

    def paso(concepto, formula, valor, fuerte=False):
        estilo = ' style="background-color: #f2f2f2; font-weight: bold;"' if fuerte else ""
        return (f"<tr{estilo}><td style='padding: 4px 6px; text-align: left;'>{concepto}</td>"
                f"<td style='padding: 4px 6px; text-align: left; font-family: Consolas, monospace; font-size: 11px;'>{formula}</td>"
                f"<td style='padding: 4px 6px; text-align: right; white-space: nowrap;'><b>{valor}</b></td></tr>")

    # --- DATOS ---
    v = res["ventana"]
    modo = "ventana" if v else ("capas" if res["modo_capas"] else "epc")
    con_taps = e["n_max"] != e["n_nom"]
    espiras_txt = f"{res['n_espiras']} (las máximas; nominal {e['n_nom']})" if con_taps else f"{res['n_espiras']}"
    segunda = ""
    for tn in e["tensiones"][1:]:
        segunda += dato("2ª tensión: línea · grupo · espiras",
                        f"{miles(tn['volt'])} V · {tn['conex']} · {tn['n']} espiras")
    filas_datos = (
        dato("Devanado · posición radial", f"<b>{e['nombre']}</b> · {m['pos']}")
        + dato("Tensión de fase · grupo", f"{miles(e['v_fase'], 1)} V · {e['conex']}")
        + segunda
        + dato("Tipo de devanado", f"<b>{res['tipo']}</b>")
        + dato("Disposición (cant. = horiz. x rad.)", f"{res['cantidad']} = {H} x {R}")
        + dato("Espiras totales (N)", espiras_txt)
        + (dato("Espiras por galleta", f"{texto_bobinas(espiras_por_bobina(res['tipo'], res['n_espiras']))} = {res['n_espiras']}"
                + (f" (nominal {texto_bobinas(espiras_por_bobina(res['tipo'], e['n_nom']))} = {e['n_nom']})" if con_taps else "")
                + f" · se dimensiona con {res['n_por_sec']}") if galleta else "")
        + (dato("Altura disponible en la ventana", f"{n(v['axial_disp'])} mm (Hc {n(v['hc'])} − 2 x {n(v['yugo'])})")
           if v else "")
        + dato("Espiras por capa" + (" (calculadas)" if res["modo_capas"] else ""), n(res["esp_por_capa"]))
        + dato("Capas" + {"ventana": " (ajustadas a la ventana)", "capas": " (ingresadas)", "epc": ""}[modo],
               f"{res['capas']} (última: {n(res['espiras_ultima'])} esp.)")
        + dato("Papel entre capas (aisl. menor)", f"{res['papel_capa']:g} mm")
        + dato("Canales internos: N° x medida (aisl. menor)", f"{canales_txt} mm" if res["canales"] else "sin canales")
        + dato("Transposiciones", f"{res['transposiciones']}")
        + dato("Canal interior (aisl. mayor)", f"{n(m['canal'])} mm")
        + dato("Al yugo: resultante / mínimo (aisl. mayor)", f"<b>{n(m['al_yugo'])}</b> / {n(m['yugo'])} mm")
    )

    # --- CONDUCTOR ---
    if platina:
        filas_cond = (dato("Platina calata (esp. x ancho)", f"{res['esp_cal']:g} x {res['anc_cal']:g} mm")
                      + dato("Papel que la envuelve (aisl. menor)", f"{res['papel']:g} mm"))
    else:
        filas_cond = (dato("Alambre esmaltado", f"Cal. {res['medida']}")
                      + dato("Ø esmaltado (sin papel)", f"{res['ancho_cond']:g} mm"))
    filas_cond += (
        dato("1 conductor: radial x axial", f"{res['esp_cond']:.2f} x {res['ancho_cond']:.2f} mm")
        + dato("Sección por conductor", f"{res['seccion']:.3f} mm²")
        + dato(f"Sección por espira (x{res['cantidad']}" + (f" x {FACTOR_SECCION_PLATINA:g}" if platina else "") + ")",
               f"<b>{res['seccion_total']:.2f} mm²</b>")
        + dato("Corriente de fase nominal", f"{e['i_fase']:.1f} A")
        + dato("Densidad de corriente", f"<b>{m['j_nom']:.2f} A/mm²</b>")
    )
    if abs(e["i_max"] - e["i_fase"]) > 1e-9:
        filas_cond += (dato("Corriente máxima (entre tensiones y tomas)", f"{e['i_max']:.1f} A")
                       + dato("Densidad máxima", f"{m['j_max']:.2f} A/mm²"))
    filas_cond += (dato("Espira media", f"{m['l_espira']:.0f} mm")
                   + dato(f"Peso de cobre ({FASES} fases)", f"{m['peso']:.1f} kg"))

    # --- DESARROLLO DEL CÁLCULO ---
    if platina:
        f_anc = f"papel + ancho calato = {res['papel']:g} + {res['anc_cal']:g}"
        f_esp = f"papel + espesor calato = {res['papel']:g} + {res['esp_cal']:g}"
    else:
        f_anc = f_esp = "Ø esmaltado (el alambre no lleva papel)"
    t = res["transposiciones"]
    n_capas_txt = "espiras por galleta" if galleta else "N"
    pasos = [] if not galleta else [
        paso("Espiras por galleta", f"REDONDEO.MAS(N / 2) = REDONDEO.MAS({res['n_espiras']} / 2)",
             f"{res['n_por_sec']}"),
    ]
    epc = n(res["esp_por_capa"])
    if v:
        pasos_capas = [
            paso("Altura disponible", f"Hc − 2 x al yugo mín. = {n(v['hc'])} − 2 x {n(v['yugo'])}",
                 f"{n(v['axial_disp'])} mm"),
        ]
        disp = "disponible"
        if galleta:
            pasos_capas.append(paso("Altura por galleta",
                                    f"(disponible − separación) / 2 = ({n(v['axial_disp'])} − {SEPARACION_GALLETA:g}) / 2",
                                    f"{n(v['por_seccion'])} mm"))
            disp = "por galleta"
        pasos_capas += [
            paso("Espiras por capa que entran",
                 f"ENTERO({disp} − transp. x ancho cond.) / ancho por espira − 1 = "
                 f"ENTERO({n(v['por_seccion'])} − {t} x {res['ancho_cond']:.2f}) / {res['ancho_espira']:.2f} − 1 "
                 f"= {v['util']} / {res['ancho_espira']:.2f} − 1", f"{v['epc_lim']:.2f}"),
            paso("Capas",
                 (f"{res['tipo']}: " + ("una sola capa" if v["capas_fijas"] == 1 else f"siempre {v['capas_fijas']} capas")
                  + ("" if v["entra_fijas"] else f" · <b style='color: #b42318;'>no caben: entran {v['epc_lim']:.2f} espiras por "
                                                 f"capa y se necesitan {n(res['n_por_sec'] / v['capas_fijas'])}</b>"))
                 if v["capas_fijas"] else
                 f"REDONDEO.MAS({n_capas_txt} / esp. por capa que entran) = REDONDEO.MAS({res['n_por_sec']} / "
                 f"{v['epc_lim']:.2f} = {res['n_por_sec'] / v['epc_lim']:.2f})", f"{res['capas']}"),
            paso("Espiras por capa",
                 f"{n_capas_txt} / capas = {res['n_por_sec']} / {res['capas']}", epc),
        ]
    elif res["modo_capas"]:
        pasos_capas = [
            paso("Capas", "dato ingresado", f"{res['capas']}"),
            paso("Espiras por capa",
                 f"{n_capas_txt} / capas = {res['n_por_sec']} / {res['capas']}", epc),
        ]
    else:
        pasos_capas = [
            paso("Capas",
                 f"REDONDEO.MAS({n_capas_txt} / esp. por capa) = REDONDEO.MAS({res['n_por_sec']} / {epc} "
                 f"= {res['capas_calc']:.2f})",
                 f"{res['capas']}"),
        ]
    pasos += [
        paso("Ancho de 1 conductor (axial)", f_anc, f"{res['ancho_cond']:.2f} mm"),
        paso("Espesor de 1 conductor (radial)", f_esp, f"{res['esp_cond']:.2f} mm"),
        paso("Radiales (verticales)", f"cantidad / horizontales = {res['cantidad']} / {H}", f"{R}"),
        paso("ANCHO POR ESPIRA",
             f"(papel + ancho calato) x horizontales = {res['ancho_cond']:.2f} x {H}",
             f"{res['ancho_espira']:.2f} mm"),
        paso("ESPESOR POR ESPIRA",
             f"(papel + espesor calato) x radiales = {res['esp_cond']:.2f} x {R}",
             f"{res['espesor_espira']:.2f} mm"),
    ] + pasos_capas + [
        paso("Suma de canales", f"N° de canales x medida = {canales_txt}" if res["canales"] else "sin canales internos",
             f"{res['suma_canales']:.2f} mm"),
        paso("RADIAL",
             f"REDONDEO.MAS({res['capas']} x ({res['papel_capa']:g} + {res['espesor_espira']:.2f}) "
             f"+ {res['suma_canales']:.2f}) = REDONDEO.MAS({res['radial_bruto']:.2f})",
             f"{n(res['radial'])} mm", True),
        paso("AXIAL" + (" (1 galleta)" if galleta else ""),
             f"REDONDEO.MAS(({epc} + 1) x {res['ancho_espira']:.2f} = {res['axial_bruto']:.2f}) "
             f"+ {t} x {res['ancho_cond']:.2f}",
             f"{n(res['axial_seccion'])} mm", True),
    ]
    if galleta:
        pasos.append(paso("AXIAL TOTAL",
                          f"2 galletas x {n(res['axial_seccion'])} + separación {SEPARACION_GALLETA:g}",
                          f"{n(res['axial_total'])} mm", True))
    pasos += [
        paso("Ø INTERIOR", f"Ø anterior + 2 x canal = {n(m['d_int'] - 2 * m['canal'])} + 2 x {n(m['canal'])}",
             f"{n(m['d_int'])} mm"),
        paso("Ø EXTERIOR", f"Ø interior + 2 x radial = {n(m['d_int'])} + 2 x {n(res['radial'])}",
             f"{n(m['d_ext'])} mm"),
    ]

    nota_galleta = (f"<div style='font-size: 11px; margin-top: 4px;'>2 galletas iguales, "
                    f"separadas {SEPARACION_GALLETA:g} mm axialmente</div>") if galleta else ""
    detalle_axial = (f"<div style='font-size: 11px;'>2 x {n(res['axial_seccion'])} + "
                     f"{SEPARACION_GALLETA:g} mm</div>") if galleta else ""
    espira = f"""
        <div style="text-align: center; padding: 8px 5px 5px 5px;">
            {svg_espira(res)}
            <div style="font-size: 11px; margin-top: 4px;">&#8597; axial: {H} horizontales &nbsp;·&nbsp; &#8596; radial: {R} radiales</div>
            <div style="font-size: 12px; margin-top: 4px;">Ancho <b>{res['ancho_espira']:.2f}</b> mm &nbsp;·&nbsp; Espesor <b>{res['espesor_espira']:.2f}</b> mm</div>
            {nota_galleta}
        </div>"""
    resultado = 'style="flex: 1; border: 2px solid black; text-align: center; padding: 8px;"'
    cuerpo = f"""
        <div style="display: flex; gap: 15px; margin-bottom: 15px;">
            {caja("DATOS", tabla_datos(filas_datos))}
            {caja("ESPIRA", espira)}
            {caja("CONDUCTOR", tabla_datos(filas_cond))}
        </div>

        <table border="1" style="border-collapse: collapse; width: 100%; font-size: 12px; border: 2px solid black;">
            <tr style="background-color: #d9d9d9;">
                <th style="padding: 5px;">Concepto</th><th>Fórmula</th><th>Valor</th>
            </tr>
            {"".join(pasos)}
        </table>

        <div style="display: flex; gap: 15px; margin-top: 15px;">
            <div {resultado}>
                <div style="font-size: 12px; font-weight: bold;">AL YUGO (mín. {n(m['yugo'])})</div>
                <div style="font-size: 26px; font-weight: bold; color: {'black' if m['margen_yugo'] >= 0 else '#c53030'};">{n(m['al_yugo'])} mm</div>
            </div>
            <div {resultado}>
                <div style="font-size: 12px; font-weight: bold;">DIMENSIÓN RADIAL</div>
                <div style="font-size: 26px; font-weight: bold;">{n(res['radial'])} mm</div>
            </div>
            <div {resultado}>
                <div style="font-size: 12px; font-weight: bold;">DIMENSIÓN AXIAL{' TOTAL' if galleta else ''}</div>
                <div style="font-size: 26px; font-weight: bold;">{n(res['axial_total'])} mm</div>
                {detalle_axial}
            </div>
            <div {resultado}>
                <div style="font-size: 12px; font-weight: bold;">Ø INTERIOR / Ø EXTERIOR</div>
                <div style="font-size: 26px; font-weight: bold;">{n(m['d_int'])} / {n(m['d_ext'])} mm</div>
            </div>
        </div>
    """
    derecha = (f'<p style="margin: 0; font-size: 14px; font-weight: bold;">{res["nombre"]}</p>'
               f'<p style="margin: 2px 0 0 0; font-size: 12px;">{res["cantidad"]} en paralelo ({H} x {R})</p>')
    return hoja(f"DISEÑO DE DEVANADO {e['nombre']}:", f"{codigo}<br>{res['tipo']}", derecha, cuerpo)


# =====================================================================
# 7. INTERFAZ GRÁFICA CON IPYWIDGETS: TODOS LOS DATOS EN UNA SOLA PANTALLA, EN EL ORDEN DEL DISEÑO
#    1 · NÚCLEO  ->  2 · DEVANADOS  ->  3 · DISTANCIAS ELÉCTRICAS (aislamiento mayor)
# =====================================================================
# Conductores de stock en un solo desplegable: el alambre va esmaltado y la platina con papel
OPCIONES_CALIBRE = ([(f"{c}", ("ALAMBRE", c)) for c in ALAMBRES]
                    + [(f"{e:g}x{a:g}", ("PLATINA", i)) for i, (e, a) in enumerate(PLATINAS)])
# Ajustar a la ventana: las capas salen de la altura que deja el núcleo (Hc - 2 x mínimo al yugo)
OPCIONES_MODO = [("Ajustar a la ventana", "ventana"), ("N° de capas", "capas"), ("Espiras por capa", "epc")]
# Valores iniciales: SOLO los que tienen fuente. Especificación y conductor: hoja de datos de entrada.
# Lo de bobinado (posición, tipo, papeles, canales, transposiciones, canal interior y al yugo) no tiene fuente:
# queda vacío (None) y se digita. El ajuste de capas es «Ajustar a la ventana» (primero el núcleo, luego los devanados).
#   kva2 = 0 -> la misma potencia · volt2 = 0 -> el devanado tiene una sola tensión
#   pos = posición radial: FIJA, el Devanado I es siempre el externo (no se digita)
#   aislamiento MAYOR: canal = canal interior (hacia el núcleo o el devanado anterior) · yugo = mínimo al yugo
#   aislamiento MENOR: papel de platina, papel entre capas y canales internos (N° de canales y medida de cada uno): los
#   canales van dentro de la espira, entre conductores (y entre capas si hay varias); caben radiales x capas − 1
#   transp = transposiciones: cruces de los conductores en paralelo; la completa es cantidad − 1 (12 platinas -> 11, como
#   el diseño de referencia) y cada una suma el ancho de un conductor a la altura del devanado
_SIN_FUENTE = dict(pos=None, tipo=None, papel=None, papel_capa=None, modo="ventana", capas=None, epc=None, canal=None,
                   yugo=None, n_canales=None, canal_mm=None, transp=None)
# Esfuerzos dieléctricos (hoja de esfuerzos): relleno de los extremos 15 mm en BT y AT; prueba industrial 70 kV en AT
# (Devanado I) y 3 kV en BT (Devanado II). El Devanado III no tiene fuente: se digita si se usa.
# Los datos de bobinado y distancias de los Devanados I y II salen del diseño de referencia.
VALORES_TABLA = {
    "I": dict(kva=1000.0, kva2=0.0, volt=22900.0, volt2=10000.0, conex="D", conex2="Y", bil=75.0,
              calibre=("ALAMBRE", 9), cant=2, horiz=2, pos=None,
              tipo="CONTINUO",            # diseño de referencia · AT = C. CONT. (1 bobina axial, 1 radial)
              papel=None, papel_capa=1.0,  # diseño de referencia
              modo="ventana", capas=None, epc=None,
              n_canales=2, canal_mm=3.0,   # diseño de referencia
              transp=0,
              canal=10.0,                  # diseño de referencia = 4+2+4 (canal + hawayano + canal)
              yugo=20.0,                   # diseño de referencia = 40 entre los dos extremos
              relleno=15.0, industrial=70.0),
    "II": dict(kva=1000.0, kva2=0.0, volt=460.0, volt2=230.0, conex="Y", conex2="Y", bil=20.0,
               calibre=("PLATINA", 4), cant=12, horiz=2, pos=None,
               tipo="HÉLICE SIMPLE",       # diseño de referencia · BT = HELICE (1 capa, ≥2 radiales, PT axial par)
               papel=0.4, papel_capa=0.0,  # diseño de referencia
               modo="ventana", capas=None, epc=None,
               n_canales=3, canal_mm=3.0,  # diseño de referencia: 3 canales dentro de la espira, entre los conductores radiales
               transp=3,                   # máximo que cabe en Hc = 440 (el diseño de referencia usa 11 con 8 espiras; aquí hay 12)
               canal=8.0,                  # diseño de referencia = 3+2+3 (canal + tubo rígido + canal adicional)
               yugo=10.0,                  # diseño de referencia = 20 entre los dos extremos
               relleno=15.0, industrial=3.0),
    "III": dict(kva=0.0, kva2=0.0, volt=220.0, volt2=20.0, conex="Y", conex2="D", bil=20.0,
                calibre=("PLATINA", 0), cant=4, horiz=2, **_SIN_FUENTE, relleno=None, industrial=None),
}
ANCHO_ROTULO, ANCHO_CELDA, ALTO_CELDA = 150, 88, 28


def _ocupa(columnas=1, filas=1):
    """Posición de una celda que ocupa varias columnas o filas. Se da con grid_area y no con
    grid_column, porque ipywidgets borra grid_column al aplicar un grid_area vacío."""
    return f"auto / auto / span {filas} / span {columnas}"


def _capa(span=1, filas=1):
    alto = ALTO_CELDA * filas + 2 * (filas - 1)
    capa = widgets.Layout(width='auto', height=f'{alto}px', margin='0')
    if span > 1 or filas > 1:
        capa.grid_area = _ocupa(span, filas)
    return capa


def _html_celda(texto, fondo="white", negrita=True, cursiva=False, alinear="center", filas=1, chica=False):
    alto = ALTO_CELDA * filas + 2 * (filas - 1) - 2
    estilo = (f"background-color: {fondo}; border: 1px solid black; display: flex; align-items: center; "
              f"justify-content: {'flex-start' if alinear == 'left' else 'center'}; text-align: {alinear}; "
              f"font-size: {11 if chica else 12}px; line-height: 1.25; height: {alto}px; padding: 0 5px; "
              f"color: black; white-space: nowrap; overflow: hidden; "
              f"font-weight: {'bold' if negrita else 'normal'}; font-style: {'italic' if cursiva else 'normal'};")
    return f'<div style="{estilo}">{texto}</div>'


def _celda(texto="", fondo="white", span=1, filas=1, **kw):
    w = widgets.HTML(_html_celda(texto, fondo, filas=filas, **kw), layout=_capa(span, filas))
    w.add_class("dc-celda")
    return w


def _dato(w, span=1):
    """Celda que se ingresa (azul, como en la hoja)."""
    w.layout = _capa(span)
    w.add_class("dc-dato")
    return w


def _entrada(valor=None, entero=False):
    """Celda numérica que puede quedar vacía (dato sin fuente: se digita). Vacía = None."""
    w = widgets.Text(value="" if valor is None else f"{valor:g}", placeholder="digitar", continuous_update=False)
    w._num = "int" if entero else "float"
    return w


def _leer(w):
    """Valor de una celda: número o None si está vacía (celdas de _entrada); el valor tal cual en las demás."""
    if not hasattr(w, "_num"):
        return w.value
    t = str(w.value).strip().replace(",", ".")
    if t == "":
        return None
    try:
        v = float(t)
    except ValueError:
        return None
    return int(v) if w._num == "int" else v


def _poner(w, v):
    """Escribe un valor en una celda (vacía si v es None)."""
    if hasattr(w, "_num"):
        w.value = "" if v is None else (f"{v:g}" if isinstance(v, float) else f"{v}")
    else:
        w.value = v


def _separador(columnas):
    return widgets.HTML("", layout=widgets.Layout(grid_area=_ocupa(columnas), height="6px", margin="0"))


# ---------------------------------------------------------------------
# 7.1 TABLA DE DEVANADOS: especificaciones, conductor y bobinado de cada devanado
# ---------------------------------------------------------------------
w_tab = {}
for _k in CLAVES:
    _v = VALORES_TABLA[_k]
    w_tab[_k] = {
        # --- especificaciones ---
        "kva": _dato(widgets.FloatText(value=_v["kva"])), "kva2": _dato(widgets.FloatText(value=_v["kva2"])),
        "volt": _dato(widgets.FloatText(value=_v["volt"])), "volt2": _dato(widgets.FloatText(value=_v["volt2"])),
        "conex": _dato(widgets.Dropdown(options=GRUPOS, value=_v["conex"])),
        "conex2": _dato(widgets.Dropdown(options=GRUPOS, value=_v["conex2"])),
        "bil": _dato(widgets.FloatText(value=_v["bil"]), span=2),
        # --- conductor ---
        "calibre": _dato(widgets.Dropdown(options=OPCIONES_CALIBRE, value=_v["calibre"])),
        "cant": _dato(widgets.BoundedIntText(value=_v["cant"], min=1, max=48)),
        "horiz": _dato(widgets.BoundedIntText(value=_v["horiz"], min=1, max=6)),
        # --- bobinado ---
        # posición radial fija (no se digita): el Devanado I es siempre el externo
        "pos": _celda(fondo=C_CALC, negrita=False, span=2),
        # tipo sin fuente: empieza vacío y se elige
        "tipo": _dato(widgets.Dropdown(options=list(TIPOS), value=_v["tipo"]), span=2),
        # Papel de la platina: aumento TOTAL sobre cada medida (ej. 0.4 = 0.2 por cada cara)
        "papel": _dato(_entrada(_v["papel"])),
        "papel_capa": _dato(_entrada(_v["papel_capa"])),
        # Ajustar a la ventana: capas y espiras por capa salen del núcleo y quedan bloqueadas.
        # Si no, se ingresa UNO de los dos (capas o espiras por capa); el otro se calcula solo
        "modo": _dato(widgets.Dropdown(options=OPCIONES_MODO, value=_v["modo"]), span=2),
        "capas": _dato(_entrada(_v["capas"], entero=True)),
        "epc": _dato(_entrada(_v["epc"])),
        # --- aislamiento mayor (van en la tabla 3 · DISTANCIAS ELÉCTRICAS) ---
        "canal": _dato(_entrada(_v["canal"])), "yugo": _dato(_entrada(_v["yugo"])),
        # esfuerzos dieléctricos: relleno de los extremos (mm) y tensión de prueba industrial (kV)
        "relleno": _dato(_entrada(_v["relleno"])), "industrial": _dato(_entrada(_v["industrial"]), span=2),
        # canales internos de refrigeración (aislamiento menor): cuántos y cuánto mide cada uno
        "n_canales": _dato(_entrada(_v["n_canales"], entero=True)),
        "canal_mm": _dato(_entrada(_v["canal_mm"])),
        "transp": _dato(_entrada(_v["transp"], entero=True), span=2),
        # --- celdas calculadas (se llenan en pintar_tabla) ---
        "aislante": _celda(cursiva=True),
        "il1": _celda(fondo=C_CALC, negrita=False), "il2": _celda(fondo=C_CALC, negrita=False),
        "if1": _celda(fondo=C_CALC, negrita=False), "if2": _celda(fondo=C_CALC, negrita=False),
        "seccion": _celda(fondo=C_CALC, negrita=False, span=2),
        "j1": _celda(fondo=C_CALC, negrita=False), "j2": _celda(fondo=C_CALC, negrita=False),
        "espiras": _celda(fondo=C_CALC, negrita=False, span=2),
        "al_yugo": _celda(fondo=C_CALC, negrita=False),          # distancia al yugo que resulta
    }
# Campos que se ingresan (todos disparan el recálculo)
CAMPOS_TABLA = ("kva", "kva2", "volt", "volt2", "conex", "conex2", "bil", "calibre", "cant", "horiz",
                "tipo", "papel", "papel_capa", "modo", "capas", "epc", "canal", "yugo", "n_canales", "canal_mm",
                "transp", "relleno", "industrial")


def _fila(rotulo, *campos):
    """Una fila de la tabla: el rótulo y, por cada devanado, las celdas de esos campos."""
    return [_celda(rotulo, alinear="left")] + [w_tab[k][c] for k in CLAVES for c in campos]


def _fila_doble(rotulo, sub1, campo1, sub2, campo2):
    """Dos filas: el rótulo (ocupa las dos), los dos subtítulos de cada devanado y, debajo, sus celdas."""
    return ([_celda(rotulo, alinear="left", filas=2)]
            + [_celda(x, chica=True) for k in CLAVES for x in (sub1, sub2)]
            + [w_tab[k][c] for k in CLAVES for c in (campo1, campo2)])


_rot_modo = _celda("AJUSTE DE CAPAS", alinear="left")       # fila avanzada: se ve con la casilla o si se usa
# 1 · DATOS DEL CLIENTE: especificación de cada devanado y sus corrientes
_celdas_cliente = (
    [_celda()] + [_celda(NOMBRES[k].upper(), C_TITULO, span=2) for k in CLAVES]
    + _fila("POTENCIA (kVA)", "kva", "kva2")
    + _fila("TENSION (V)", "volt", "volt2")
    + _fila("GRUPO", "conex", "conex2")
    + _fila("BIL (kV)", "bil")
    + _fila("PRUEBA INDUSTRIAL (kV)", "industrial")
    + [_separador(7)]
    + _fila("Ilinea_nominal (A)", "il1", "il2")
    + _fila("Ifase_nominal (A)", "if1", "if2")
)
tabla_cliente = widgets.GridBox(_celdas_cliente, layout=widgets.Layout(
    grid_template_columns=f"{ANCHO_ROTULO}px repeat(6, {ANCHO_CELDA}px)", grid_gap="2px",
    min_width=f"{ANCHO_ROTULO + 6 * ANCHO_CELDA + 12}px", margin="0 30px 10px 0"))

# 3 · DEVANADOS: conductor y bobinado de cada devanado
_celdas_tabla = (
    [_celda()] + [_celda(NOMBRES[k].upper(), C_TITULO, span=2) for k in CLAVES]
    + _fila("CALIBRE CONDUCTOR", "calibre", "aislante")
    + _fila_doble("ARREGLO DE<br>CONDUCTORES", "CANTIDAD", "cant", "HORIZONTAL", "horiz")
    + _fila("SECCION (mm²)", "seccion")
    + _fila("DENSIDAD (A/mm²)", "j1", "j2")
    + [_separador(7)]
    + _fila("POSICIÓN RADIAL (FIJA)", "pos")
    + _fila("TIPO DE DEVANADO", "tipo")
    + _fila_doble("PAPEL (mm)<br>AISL. MENOR", "PLATINA", "papel", "ENTRE CAPAS", "papel_capa")
    + [_rot_modo] + [w_tab[k]["modo"] for k in CLAVES]
    + _fila_doble("BOBINADO", "N° CAPAS", "capas", "ESP. X CAPA", "epc")
    + _fila("ESPIRAS", "espiras")
    + _fila_doble("CANALES INTERNOS<br>AISL. MENOR", "N° CANALES", "n_canales", "MEDIDA (mm)", "canal_mm")
    + _fila("TRANSPOSICIONES", "transp")
)
tabla_entrada = widgets.GridBox(_celdas_tabla, layout=widgets.Layout(
    grid_template_columns=f"{ANCHO_ROTULO}px repeat(6, {ANCHO_CELDA}px)", grid_gap="2px",
    # ancho mínimo = el de la tabla completa: en una salida angosta aparece la barra de desplazamiento
    min_width=f"{ANCHO_ROTULO + 6 * ANCHO_CELDA + 12}px", margin="0 30px 10px 0"))


# ---------------------------------------------------------------------
# 7.2 REPARTO, REGULACIÓN, GENERALES Y NÚCLEO (mismo formato de celdas)
# ---------------------------------------------------------------------
def _tabla_pares(titulo, filas, ancho_rotulo=200, ancho_valor=ANCHO_CELDA):
    """Tabla de dos columnas: rótulo y celda de ingreso."""
    celdas = [_celda(titulo, C_TITULO, span=2)]
    for rotulo, w in filas:
        celdas += [_celda(rotulo, alinear="left"), _dato(w)]
    return widgets.GridBox(celdas, layout=widgets.Layout(
        grid_template_columns=f"{ancho_rotulo}px {ancho_valor}px", grid_gap="2px", margin="0 30px 10px 0",
        align_content="flex-start"))


w_rep = _dato(widgets.Text(value='100-0', continuous_update=False), span=3)
w_pasos = _dato(widgets.BoundedIntText(value=5, min=1, max=99))
w_var = _dato(widgets.FloatText(value=2.5))
w_tap = _dato(widgets.BoundedIntText(value=3, min=1, max=99))
tabla_tap = widgets.GridBox(
    [_celda("REPARTO BT", C_TITULO, span=3), w_rep, _separador(3),
     _celda("N° PASOS"), _celda("%VARIACION"), _celda("TAP NOMINAL"), w_pasos, w_var, w_tap],
    layout=widgets.Layout(grid_template_columns="repeat(3, 100px)", grid_gap="2px",
                          margin="0 0 10px 0", align_content="flex-start"))

w_codigo = widgets.Text(value='TR-1000-22.9', continuous_update=False)
w_frec = widgets.FloatText(value=60.0)
tabla_generales = _tabla_pares("GENERALES", [("CODIGO", w_codigo), ("FRECUENCIA (Hz)", w_frec)],
                               ancho_rotulo=150, ancho_valor=150)
# Especificación del cliente que verifica el semáforo (sin fuente: se digita; vacía = no se verifica)
w_vcc_obj = _entrada()
w_vcc_tol = _entrada()
tabla_especificacion = _tabla_pares("ESPECIFICACIÓN (SEMÁFORO)", [("Vcc OBJETIVO (%)", w_vcc_obj),
                                                                   ("TOLERANCIA (± % DEL Vcc)", w_vcc_tol)], ancho_rotulo=180)

# Núcleo del diseño de referencia (TR-1000-22.9): el núcleo manda; los devanados se ajustan a él
w_dn = widgets.FloatText(value=259.0)      # diseño de referencia
w_de = widgets.FloatText(value=510.0)
w_hc = widgets.FloatText(value=440.0)
w_g = widgets.FloatText(value=5.0)
tabla_nucleo = _tabla_pares("NUCLEO", [
    ("DIAMETRO Dn (mm)", w_dn), ("DIST. ENTRE EJES De (mm)", w_de), ("ALTURA DE VENTANA Hc (mm)", w_hc),
    ("TRASLAPE g (mm)", w_g)])

# B máxima de tus condiciones (1.65 a 1.73 T): es la inducción objetivo del diseño (la búsqueda tiene la suya)
w_bobj = widgets.FloatText(value=1.73)
w_b_min = _entrada(1.65)   # tus condiciones: B mínima del semáforo
w_fa = _entrada(0.97)      # diseño de referencia (factor de apilamiento)
# Las espiras de la menor tensión salen siempre de la B objetivo (con 1.73 T: 6 espiras, B real 1,729 T) y las
# pérdidas en el núcleo, de la regresión de la tabla M4 0.27 mm: ya no se dan a mano. Factor de construcción:
w_fconst = widgets.FloatText(value=1.0)
# Tubo enrollado que envuelve todo el conjunto: espesor que se suma por fuera del último devanado
w_tubo = _entrada(1.0)     # diseño de referencia
w_fases = _entrada(9.0)    # diseño de referencia (el entre fases que resulta en él); supuesto como mínimo
w_tref = _entrada(75.0)    # supuesto: IEC 60076-1, 75 °C para cobre en aceite (el diseño de referencia equivale a ~83 °C)
tabla_flujo = _tabla_pares("FLUJO", [
    ("B MÁXIMA = OBJETIVO (T)", w_bobj), ("B MÍNIMA (T)", w_b_min), ("FACTOR DE APILAMIENTO", w_fa),
    ("T° DE REFERENCIA (°C)", w_tref)])

w_pfe = _celda(fondo=C_CALC, negrita=False)
w_p0 = _celda(fondo=C_CALC, negrita=False)
tabla_vacio = widgets.GridBox(
    [_celda("PÉRDIDAS EN EL NÚCLEO (VACÍO)", C_TITULO, span=2),
     _celda("MATERIAL", alinear="left"), _celda("M4 0.27", chica=True),
     _celda("FACTOR DE CONSTRUCCIÓN", alinear="left"), _dato(w_fconst),
     _celda("Pfe CON B REAL + 0.099 (W/kg)", alinear="left"), w_pfe,
     _celda("P0 = Pfe x PESO x FACTOR (W)", alinear="left"), w_p0],
    layout=widgets.Layout(grid_template_columns=f"220px {ANCHO_CELDA}px", grid_gap="2px", margin="0 30px 10px 0",
                          align_content="flex-start"))


# Opción avanzada (plegada, paso 3): la fila «AJUSTE DE CAPAS»
w_ver_ajuste = widgets.Checkbox(value=False, indent=False, layout=widgets.Layout(width="auto"),
                                description="Mostrar la fila «AJUSTE DE CAPAS» (capas o espiras por capa a mano)")
caja_avanzadas = widgets.Accordion(children=[widgets.VBox([w_ver_ajuste])], selected_index=None,
                                   layout=widgets.Layout(max_width="1000px", margin="0 0 10px 0"))
caja_avanzadas.set_title(0, "Opciones avanzadas · ajuste de capas a mano")


def pintar_vacio(vac):
    """Pfe y P0 en la tabla del paso 2 (núcleo)."""
    if vac is None:
        w_pfe.value = _html_celda("—", C_CALC, negrita=False)
        w_p0.value = _html_celda("—", C_CALC, negrita=False)
        return
    w_pfe.value = _html_celda(f"{vac['pfe']:.4f}", C_CALC, negrita=False)
    w_p0.value = _html_celda(f"{vac['p0']:,.0f}", C_CALC, negrita=True)

# 3 · DISTANCIAS ELÉCTRICAS (aislamiento mayor): mínimos que se ingresan y lo que resulta
_ANCHO_DEV = 2 * ANCHO_CELDA + 2
# Esfuerzos dieléctricos (hoja de esfuerzos): barrera HAWAYANO de 2 mm, tubo rígido +10 (sobresale 5 por lado) y sin
# tubo entre núcleo y bobina
w_barrera = widgets.Dropdown(options=BARRERAS, value="HAWAYANO")
w_e_barrera = _entrada(2.0)
w_tubo_rigido = _entrada(10.0)
w_tubo_nucleo = _entrada(0.0)
w_fases_real = _celda(fondo=C_CALC, negrita=False)
tabla_distancias = widgets.GridBox(
    [_celda("AISLAMIENTO MAYOR (mm)", C_TITULO)] + [_celda(NOMBRES[k].upper(), C_TITULO) for k in CLAVES]
    + [_celda("CANAL INTERIOR*", alinear="left")] + [w_tab[k]["canal"] for k in CLAVES]
    + [_celda("AL YUGO MÍNIMO", alinear="left")] + [w_tab[k]["yugo"] for k in CLAVES]
    + [_celda("AL YUGO RESULTANTE", alinear="left")] + [w_tab[k]["al_yugo"] for k in CLAVES]
    + [_celda("RELLENO EXTREMOS (mm)", alinear="left")] + [w_tab[k]["relleno"] for k in CLAVES]
    + [_separador(4)]
    + [_celda("TUBO ENROLLADO EXT.", alinear="left"), _dato(w_tubo), _separador(2)]
    + [_celda("ENTRE FASES MÍNIMO", alinear="left"), _dato(w_fases), _separador(2)]
    + [_celda("ENTRE FASES RESULTANTE", alinear="left"), w_fases_real, _separador(2)]
    + [_separador(4)]
    + [_celda("BARRERA ENTRE BOBINAS", alinear="left"), _dato(w_barrera), _separador(2)]
    + [_celda("ESPESOR BARRERA (mm)", alinear="left"), _dato(w_e_barrera), _separador(2)]
    + [_celda("TUBO RÍGIDO + (mm)", alinear="left"), _dato(w_tubo_rigido), _separador(2)]
    + [_celda("TUBO NÚCLEO–BOBINA (mm)", alinear="left"), _dato(w_tubo_nucleo), _separador(2)],
    layout=widgets.Layout(grid_template_columns=f"{ANCHO_ROTULO + 34}px repeat(3, {_ANCHO_DEV}px)",
                          grid_gap="2px", min_width=f"{ANCHO_ROTULO + 34 + 3 * _ANCHO_DEV + 8}px",
                          margin="0 30px 10px 0", align_content="flex-start"))

valores_anchos = [250, 235, 220, 195, 170, 140, 110, 60, 0, 0]   # ancho óptimo de tabla para Dn 259, 8 escalones, a 5 mm
w_anchos = [_dato(widgets.FloatText(value=val)) for val in valores_anchos]
tabla_anchos = widgets.GridBox(
    [_celda("ANCHOS DE ESCALON (mm) · 0 = no se usa", C_TITULO, span=5)]
    + [_celda(f"ESC. {i + 1}", chica=True) for i in range(5)] + w_anchos[:5]
    + [_celda(f"ESC. {i + 1}", chica=True) for i in range(5, 10)] + w_anchos[5:],
    layout=widgets.Layout(grid_template_columns=f"repeat(5, {ANCHO_CELDA}px)", grid_gap="2px",
                          margin="0 0 10px 0", align_content="flex-start"))

# Las celdas que se ingresan van en azul, como en la hoja
ESTILO_TABLA = widgets.HTML(f"""<style>
.dc-dato input, .dc-dato select {{ background-color: {C_DATO} !important; color: black !important;
    font-weight: bold; text-align: center; text-align-last: center; border: 1px solid black !important;
    height: {ALTO_CELDA}px !important; }}
.dc-dato input:disabled, .dc-dato select:disabled {{ opacity: 0.6; }}
.dc-dato.dc-falta input, .dc-dato.dc-falta select {{ background-color: {C_CERCA_FONDO} !important;
    border: 2px solid {C_CERCA} !important; }}
.dc-dato.dc-falta input::placeholder {{ color: {C_CERCA}; font-style: italic; }}
.dc-celda, .dc-celda .widget-html-content {{ width: 100%; }}
</style>""")


# ---------------------------------------------------------------------
# 7.3 Lectura de la tabla
# ---------------------------------------------------------------------
def leer_specs():
    return {k: {c: _leer(w[c]) for c in ("kva", "kva2", "volt", "volt2", "conex", "conex2", "bil")}
            for k, w in w_tab.items()}


def leer_conductores():
    """Conductor y arreglo de cada devanado, tal como están en la tabla."""
    return {k: {"conductor": w["calibre"].value[0], "medida": w["calibre"].value[1],
                "cantidad": w["cant"].value, "horizontales": w["horiz"].value} for k, w in w_tab.items()}


def leer_bobinado():
    """Cómo se bobina cada devanado, tal como está en la tabla."""
    bob = {}
    pos = posiciones_radiales({k: {"kva": _leer(w["kva"])} for k, w in w_tab.items()})
    for k, w in w_tab.items():
        b = {c: _leer(w[c]) for c in ("tipo", "papel", "papel_capa", "modo", "capas", "epc", "canal", "yugo",
                                      "n_canales", "canal_mm", "transp")}
        b["pos"] = pos[k]                       # fija: el Devanado I es siempre el externo
        b["canales"] = canales_de(b)[2] if b["n_canales"] is not None else []
        if w["calibre"].value[0] == "ALAMBRE" and b["papel"] is None:
            b["papel"] = 0.0                    # el alambre va esmaltado: no lleva papel
        bob[k] = b
    return bob


def pintar_posiciones():
    """Posición radial fija de cada devanado (no se digita)."""
    pos = posiciones_radiales({k: {"kva": _leer(w["kva"])} for k, w in w_tab.items()})
    n_act = sum(1 for p in pos.values() if p)
    for k in CLAVES:
        w_tab[k]["pos"].value = _html_celda(texto_posicion(pos[k], n_act), C_CALC, negrita=False)


def pintar_tabla(specs, cond):
    """Llena las celdas calculadas de la parte eléctrica: aislante, corrientes, sección y densidad."""
    entrada = resumen_entrada(specs, cond)
    for k in CLAVES:
        d, w = entrada[k], w_tab[k]
        w["aislante"].value = _html_celda(d["aislante"], cursiva=True)
        for j, col in enumerate(d["columnas"], start=1):
            w[f"il{j}"].value = _html_celda(f"{col['i_linea']:.2f}", C_CALC, negrita=False)
            w[f"if{j}"].value = _html_celda(f"{col['i_fase']:.2f}", C_CALC, negrita=False)
            w[f"j{j}"].value = _html_celda(f"{col['densidad']:.4f}", C_CALC, negrita=False)
        w["seccion"].value = _html_celda(f"{d['seccion']:.2f}", C_CALC, negrita=False)


def ajustar_tabla():
    """Aplica a la tabla las reglas del tipo de devanado (máximo de conductores y horizontales: fijas en
    las hélices, iguales a la cantidad en continuo y galleta) y bloquea las celdas que no corresponden."""
    for k in CLAVES:
        w = w_tab[k]
        w["papel"].disabled = w["calibre"].value[0] == "ALAMBRE"    # el alambre va esmaltado, sin papel
        w["epc"].disabled = w["modo"].value in ('capas', 'ventana')
        w["capas"].disabled = w["modo"].value in ('epc', 'ventana')
        for c in ("epc", "capas"):              # celda calculada: sin «digitar»
            w[c].placeholder = "—" if w[c].disabled else "digitar"
        if w["tipo"].value is None:                # tipo todavía sin elegir: sin reglas
            w["horiz"].disabled = False
            continue
        r = TIPOS[w["tipo"].value]
        if w["cant"].max != r["max_cond"]:
            w["cant"].max = r["max_cond"]
        if w["horiz"].max != r["max_h"]:
            w["horiz"].max = r["max_h"]
        fijo = False
        if r["h_fijo"] is not None:                # hélices: horizontales fijas
            w["horiz"].value, fijo = r["h_fijo"], True
        elif r["radiales"] == (1,):                # continuo / galleta: horizontales = cantidad
            w["horiz"].value, fijo = w["cant"].value, True
        w["horiz"].disabled = fijo


def pintar_espiras(elec):
    """Con el cálculo eléctrico: muestra las espiras de cada devanado y llena solo el dato de bobinado
    que no se ingresa (espiras por capa o N° de capas). Con «Ajustar a la ventana» los dos se llenan
    después, en pintar_ventana, porque salen del núcleo y del conductor."""
    for k in CLAVES:
        w = w_tab[k]
        e = elec["dev"].get(k) if elec else None
        if e is None:
            w["espiras"].value = _html_celda("—", C_CALC, negrita=False)
            continue
        texto = f"{e['n_max']}" if e["n_max"] == e["n_nom"] else f"{e['n_max']} (nominal {e['n_nom']})"
        bob = espiras_por_bobina(w["tipo"].value, e["n_max"])
        if bob:      # galleta: también las espiras de cada una de sus 2 bobinas, en una segunda línea
            alto = ALTO_CELDA - 2
            w["espiras"].value = (f'<div style="background-color: {C_CALC}; border: 1px solid black; height: {alto}px; '
                                  f'display: flex; flex-direction: column; justify-content: center; align-items: center; '
                                  f'font-size: 10.5px; line-height: 1.2; color: black; white-space: nowrap; overflow: hidden;">'
                                  f'<span>{texto}</span><span>por bobina: {texto_bobinas(bob)}</span></div>')
        else:
            w["espiras"].value = _html_celda(texto, C_CALC, negrita=False)
        if w["modo"].value == 'ventana' or w["tipo"].value is None:
            continue
        n_sec = espiras_por_seccion(w["tipo"].value, e["n_max"])
        capas, epc = _leer(w["capas"]), _leer(w["epc"])
        if w["modo"].value == 'capas' and capas:
            # se muestra redondeado hacia arriba a 2 decimales (el cálculo usa N / capas exacto)
            _poner(w["epc"], redondeo_mas(n_sec / capas, 2))
        elif w["modo"].value == 'epc' and epc and epc > 0:
            _poner(w["capas"], int(redondeo_mas(n_sec / epc, 0)))


def pintar_ventana(lista):
    """Con «Ajustar a la ventana»: muestra las capas y las espiras por capa que salieron del núcleo. Si un devanado
    no se pudo calcular, sus celdas quedan vacías (nunca con los números de un cálculo anterior)."""
    hechos = {item["clave"] for item in lista}
    for k in CLAVES:
        if w_tab[k]["modo"].value == "ventana" and k not in hechos:
            _poner(w_tab[k]["capas"], None)
            _poner(w_tab[k]["epc"], None)
    for item in lista:
        w, res = w_tab[item["clave"]], item["res"]
        if res["ventana"]:
            _poner(w["capas"], res["capas"])
            _poner(w["epc"], redondeo_mas(res["esp_por_capa"], 2))


def pintar_distancias(mont):
    """Paso 3: distancia al yugo y entre fases que resultan (gris si cumplen el mínimo; rojo con ✘ si no)."""
    rojo = "#f4a6a6"
    por_clave = {f["clave"]: f for f in mont["filas"]} if mont else {}
    for k in CLAVES:
        f = por_clave.get(k)
        if f is None:
            texto, fondo = "—", C_CALC
        elif f["margen_yugo"] >= 0:
            texto, fondo = n(f["al_yugo"]), C_CALC
        else:
            texto, fondo = f"&#10008; {n(f['al_yugo'])}", rojo
        w_tab[k]["al_yugo"].value = _html_celda(texto, fondo, negrita=f is not None and f["margen_yugo"] < 0)
    if mont:
        ok = mont["margen_de"] >= 0
        w_fases_real.value = _html_celda(n(mont["entre_fases_real"]) if ok else f"&#10008; {n(mont['entre_fases_real'])}",
                                         C_CALC if ok else rojo, negrita=not ok)
    else:
        w_fases_real.value = _html_celda("—", C_CALC, negrita=False)


def calcular_bobinado(k, e, cond, bob, hc):
    """Devuelve (errores, res) del devanado k con las espiras y la corriente del cálculo eléctrico.
    hc = altura de ventana del núcleo (para «Ajustar a la ventana»)."""
    c, b = cond[k], bob[k]
    n_esp = e["n_max"]
    ventana = None
    if b["modo"] == 'ventana':
        ventana = ajuste_ventana(b["tipo"], c["conductor"], c["medida"], c["horizontales"], b["papel"], n_esp,
                                 b["transp"], hc, b["yugo"])
        if ventana["capas"] is None:
            tr = (f"; las {b['transp']} transposiciones ocupan {b['transp']} x {ventana['ancho_cond']:.2f} = "
                  f"{b['transp'] * ventana['ancho_cond']:.1f} mm" if b["transp"] > 0 else "")
            return [f"no entra en la ventana: Hc {n(hc)} − 2 x {n(b['yugo'])} al yugo deja "
                    f"{n(ventana['axial_disp'])} mm{tr} y con espiras de {ventana['ancho_espira']:.2f} mm de ancho no "
                    f"cabe ni una espira por capa."], None
        capas_in = ventana["capas"]
    else:
        capas_in = b["capas"] if b["modo"] == 'capas' else None
    epc = espiras_por_seccion(b["tipo"], n_esp) / capas_in if capas_in else b["epc"]
    errores = validar(b["tipo"], c["cantidad"], c["horizontales"], n_esp, epc)
    if min(b["canal"], b["yugo"], b["papel"], b["papel_capa"]) < 0:
        errores.append("Papeles, canal interior y distancia al yugo no pueden ser negativos.")
    if b["n_canales"] < 0 or (b["n_canales"] > 0 and b["canal_mm"] <= 0):
        errores.append("Canales internos: con 1 o más canales, la medida de cada canal debe ser mayor que 0 mm.")
    if errores:
        return errores, None
    res = calcular_devanado(
        b["tipo"], c["conductor"], c["medida"], c["cantidad"], c["horizontales"], b["papel"], n_esp, epc,
        b["papel_capa"], b["canales"], b["transp"], e["i_fase"], capas_in=capas_in, ventana=ventana)
    return [], res


out = widgets.Output()
_estado = {"bloqueo": False}
_ultimo = {"det": [], "errores": [], "nuc_ok": False, "calc": None}     # para la barra de pasos y el semáforo


# ---------------------------------------------------------------------
# 7.4 Cálculo completo y dibujo
# ---------------------------------------------------------------------
def calcular_todo():
    """Lee la interfaz y devuelve la lista de bloques HTML a mostrar."""
    codigo = w_codigo.value
    ajustar_tabla()
    pintar_posiciones()
    d = leer_datos()
    specs = leer_specs()
    cond = leer_conductores()
    bloques = []
    _ultimo.update(det=faltantes_detalle(d), errores=[], nuc_ok=False, calc=None)
    falta = faltantes(d)
    if falta:                                   # datos sin fuente que todavía no se digitaron
        if all(v is not None for k in CLAVES for v in specs[k].values()):
            pintar_tabla(specs, cond)           # corrientes y densidades sí tienen todos sus datos
        pintar_espiras(None)
        pintar_ventana([])
        pintar_distancias(None)
        pintar_vacio(None)
        return [html_errores(falta, "Faltan estos datos (no tienen fuente, se digitan):")]
    pintar_tabla(specs, cond)

    # 1. Núcleo
    anchos = [w.value for w in w_anchos if w.value > 0]
    err_nuc = validar_nucleo(w_dn.value, w_g.value, w_de.value, w_hc.value, FACTOR_ELIPSE, anchos)
    if d["fa"] <= 0 or d["fa"] > 1:
        err_nuc.append("Núcleo: el factor de apilamiento debe estar entre 0 y 1.")
    if w_de.value <= w_dn.value:
        err_nuc.append(MSG_DE)
    if err_nuc:
        _ultimo["errores"] = err_nuc
        pintar_espiras(None)
        pintar_ventana([])
        pintar_distancias(None)
        pintar_vacio(None)
        return [html_errores(err_nuc)]
    nuc = calcular_nucleo(w_dn.value, w_g.value, w_de.value, w_hc.value, FACTOR_ELIPSE, anchos, d["fa"])
    _ultimo["nuc_ok"] = True

    # Cálculo eléctrico: espiras de cada devanado
    err_elec, elec = calcular_electrico(
        specs, w_frec.value, w_tap.value, w_var.value, w_pasos.value, w_rep.value,
        nuc["seccion_neta"], w_bobj.value, 0)
    pintar_espiras(elec)
    bob = leer_bobinado()       # después de pintar_espiras: ya tiene el dato de bobinado que se llena solo

    # Pérdidas en el núcleo con la inducción real
    vac = None
    if w_fconst.value <= 0:
        err_elec = list(err_elec) + ["Pérdidas en el núcleo: el factor de construcción debe ser mayor que 0."]
    elif elec:
        vac = calcular_vacio(nuc, elec, 0.0, w_fconst.value)
    pintar_vacio(vac)

    # Posición radial de cada devanado
    errores = list(err_elec)
    if elec:
        por_pos = {}
        for k in elec["activos"]:
            por_pos.setdefault(bob[k]["pos"], []).append(NOMBRES[k])
        for pos, nombres in sorted(por_pos.items()):
            if len(nombres) > 1:
                errores.append(f"{' y '.join(nombres)} tienen la misma posición radial ({pos}): "
                               f"cada devanado va en una posición distinta.")
    if d["fases"] < 0 or d["tubo"] < 0:
        errores.append("La distancia entre fases y el tubo enrollado no pueden ser negativos.")
    errores += errores_esfuerzos(d, elec)

    # 2. Devanados dentro de la ventana, del núcleo hacia afuera
    lista = []
    if elec:
        for k in sorted(elec["activos"], key=lambda c: bob[c]["pos"]):
            err_dev, res = calcular_bobinado(k, elec["dev"][k], cond, bob, nuc["hc"])
            if err_dev:
                errores += [f"{NOMBRES[k]}: {x}" for x in err_dev]
            else:
                lista.append({"pos": bob[k]["pos"], "clave": k, "res": res,
                              "canal": bob[k]["canal"], "yugo": bob[k]["yugo"]})

    pintar_ventana(lista)
    if errores:
        _ultimo["errores"] = errores
        pintar_distancias(None)
        return [html_errores(errores), html_nucleo(nuc, codigo)]

    # 3. Distancias eléctricas que quedan, peso, pérdidas, Vcc y hojas
    mont = calcular_montaje(nuc, elec, lista, d["fases"], d["tref"], d["tubo"])
    pintar_distancias(mont)
    pares = calcular_vcc(elec, mont)
    esf = esfuerzos_dielectricos(mont, d["dev"], d)
    _ultimo["calc"] = {"nuc": nuc, "elec": elec, "mont": mont, "pares": pares, "vac": vac, "esf": esf}
    cond_ = condiciones_ui()
    bloques.append(html_no_entra(nuc, mont))
    bloques.append(html_verificacion(limites_diseno(nuc, elec, mont, pares, cond_, esf),
                                     explicaciones_resultados(nuc, elec, mont, pares, vac), cond_))
    bloques.append(html_resumen(codigo, specs, cond, bob, nuc, elec, mont, pares, lista, vac, esf=esf, datos=d))
    bloques.append(html_nucleo(nuc, codigo))
    por_clave = {f["clave"]: f for f in mont["filas"]}
    for item in lista:
        bloques.append(html_devanado(item["res"], codigo, elec["dev"][item["clave"]], por_clave[item["clave"]]))
    return bloques


def actualizar_ui(*args):
    if _estado["bloqueo"]:
        return
    _estado["bloqueo"] = True
    try:
        bloques = calcular_todo()
    except Exception as ex:      # dato fuera de rango que no se previó: se avisa en vez de romper la hoja
        bloques = [html_errores([f"{type(ex).__name__}: {ex}"], "No se pudo calcular con estos datos:")]
        _ultimo.update(errores=[f"{type(ex).__name__}: {ex}"], calc=None)
    finally:
        _estado["bloqueo"] = False
    pintar_pasos()
    pintar_faltantes(_ultimo["det"])
    _ver_ajuste()

    with out:
        out.clear_output(wait=True)
        display(HTML("".join(bloques)))


# J máxima del diseño (tus condiciones): condición del semáforo en el paso 3
w_j_max = _entrada(4.7)
tabla_cond_dev = _tabla_pares("CONDICIÓN DEL CONDUCTOR", [("J MÁXIMA (A/mm²)", w_j_max)], ancho_rotulo=160)


def condiciones_ui():
    """Condiciones del semáforo: las del propio diseño (pasos 1, 2 y 3), no las de la búsqueda."""
    return condiciones_diseno(leer_datos())


w_barra_pasos = widgets.HTML()


def pintar_pasos():
    """Barra de pasos con su estado y la lista de datos que faltan."""
    u = _ultimo
    c = u["calc"]
    L = limites_diseno(c["nuc"], c["elec"], c["mont"], c["pares"], condiciones_ui(), c["esf"]) if c else None
    w_barra_pasos.value = html_pasos(estado_pasos(u["det"], u["errores"], L, u["nuc_ok"]), u["det"])


_CAMPOS_GENERALES = {"frec": w_frec, "rep": w_rep, "pasos": w_pasos, "variacion": w_var, "tap": w_tap, "dn": w_dn,
                     "de": w_de, "hc": w_hc, "g": w_g, "bobj": w_bobj, "fa": w_fa,
                     "vcc_obj": w_vcc_obj, "vcc_tol": w_vcc_tol, "b_min": w_b_min, "j_max": w_j_max,
                     "fconst": w_fconst, "tubo": w_tubo, "fases": w_fases, "tref": w_tref, "barrera": w_barrera,
                     "e_barrera": w_e_barrera, "tubo_rigido": w_tubo_rigido, "tubo_nucleo": w_tubo_nucleo}


def pintar_faltantes(det):
    """Celdas de los datos que faltan en ámbar (clase dc-falta); las demás, normales."""
    faltan = {(x["k"], x["c"]) for x in det}
    celdas = [((None, c), w) for c, w in _CAMPOS_GENERALES.items()]
    celdas += [((k, c), w_tab[k][c]) for k in CLAVES for c in CAMPOS_TABLA]
    for clave, w in celdas:
        marcada = "dc-falta" in w._dom_classes
        if clave in faltan and not marcada:
            w.add_class("dc-falta")
        elif clave not in faltan and marcada:
            w.remove_class("dc-falta")


def _ver_ajuste(*_):
    """La fila «AJUSTE DE CAPAS» se ve con la casilla o si algún devanado no usa «Ajustar a la ventana»."""
    if any(w_tab[k]["modo"].value != "ventana" for k in CLAVES) and not w_ver_ajuste.value:
        w_ver_ajuste.value = True                      # en uso: queda a la vista (vuelve a llamar a esta función)
        return
    disp = None if w_ver_ajuste.value else "none"
    for w in [_rot_modo] + [w_tab[k]["modo"] for k in CLAVES]:
        if w.layout.display != disp:
            w.layout.display = disp


w_ver_ajuste.observe(_ver_ajuste, "value")


# ---------------------------------------------------------------------
# 7.5 BÚSQUEDA POR Vcc: combinaciones de conductores y Dn (se corre con el botón)
# ---------------------------------------------------------------------
def leer_datos():
    """Todos los datos de la pantalla en un diccionario (el que usan calcular_datos y la búsqueda)."""
    return {"codigo": w_codigo.value, "frec": w_frec.value, "rep": w_rep.value, "pasos": w_pasos.value,
            "variacion": w_var.value, "tap": w_tap.value, "dn": w_dn.value, "de": w_de.value, "hc": w_hc.value,
            "g": w_g.value, "bobj": w_bobj.value, "fa": _leer(w_fa),
            "fconst": w_fconst.value, "tubo": _leer(w_tubo), "fases": _leer(w_fases),
            "tref": _leer(w_tref), "barrera": w_barrera.value, "e_barrera": _leer(w_e_barrera),
            "tubo_rigido": _leer(w_tubo_rigido), "tubo_nucleo": _leer(w_tubo_nucleo), "anchos": [w.value for w in w_anchos],
            "vcc_obj": _leer(w_vcc_obj), "vcc_tol": _leer(w_vcc_tol), "b_min": _leer(w_b_min), "j_max": _leer(w_j_max),
            "dev": {k: {c: _leer(w[c]) for c in CAMPOS_TABLA} for k, w in w_tab.items()}}


def poner_datos(nd):
    """Carga en la pantalla una alternativa de la búsqueda: Dn, anchos, De y, por devanado,
    tipo, conductor, cantidad, horizontales y «Ajustar a la ventana». Las condiciones del diseño no cambian."""
    _estado["bloqueo"] = True
    try:
        w_dn.value = nd["dn"]
        for w, a in zip(w_anchos, nd["anchos"]):
            w.value = a
        w_de.value = nd["de"]
        for k in CLAVES:
            t, v = w_tab[k], nd["dev"][k]
            t["tipo"].value, t["calibre"].value, t["modo"].value = v["tipo"], tuple(v["calibre"]), v["modo"]
            ajustar_tabla()                       # límites de cantidad y horizontales del tipo nuevo
            t["cant"].value, t["horiz"].value = v["cant"], v["horiz"]
    finally:
        _estado["bloqueo"] = False
    actualizar_ui()


# Condiciones: J máxima y rango de B son las tuyas; Vcc, tolerancia y J mínima no tienen fuente (se digitan).
# La búsqueda va aparte del diseño: sus condiciones, Dn fijo (o el rango) y De máximo son propios.
wb = {
    "vcc": _entrada(), "tol": _entrada(),
    "jmin": _entrada(), "jmax": widgets.FloatText(value=4.7),
    "bmin": widgets.FloatText(value=1.65), "bmax": widgets.FloatText(value=1.73),
    "dn_fijo": _entrada(), "dn_min": _entrada(),
    "dn_max": _entrada(), "dn_paso": _entrada(),
    "de_max": _entrada(), "max": widgets.BoundedIntText(value=40, min=1, max=500),
}
# Tipos que se prueban en cada devanado (nada marcado = el tipo que tiene en la tabla)
wb_tipos = {k: widgets.SelectMultiple(options=list(TIPOS), value=(), rows=5, layout=widgets.Layout(width="200px"))
            for k in ("I", "II")}
wb_orden = widgets.Dropdown(options=[(v, k) for k, v in ORDENES_BUSQUEDA.items()], value="peso",
                            layout=widgets.Layout(width="270px"))
b_buscar = widgets.Button(description="BUSCAR COMBINACIONES", button_style="primary", layout=widgets.Layout(width="270px"))
wb_alt = widgets.Dropdown(options=[], layout=widgets.Layout(width="520px"))
b_usar = widgets.Button(description="USAR EN EL DISEÑO", button_style="success", disabled=True,
                        layout=widgets.Layout(width="200px"))
out_busqueda = widgets.Output()
_busqueda = {"res": None, "o": None}

tabla_condiciones = _tabla_pares("CONDICIONES", [
    ("VCC OBJETIVO (%)", wb["vcc"]), ("TOLERANCIA (± % DEL Vcc)", wb["tol"]), ("J MÍNIMA (A/mm²)", wb["jmin"]),
    ("J MÁXIMA (A/mm²)", wb["jmax"]), ("B MÍNIMA (T)", wb["bmin"]), ("B MÁXIMA (T)", wb["bmax"])])
tabla_dn_busqueda = _tabla_pares("NÚCLEO A BUSCAR", [
    ("Dn FIJO (0 = buscar)", wb["dn_fijo"]), ("Dn MÍNIMO (mm)", wb["dn_min"]), ("Dn MÁXIMO (mm)", wb["dn_max"]),
    ("PASO DE Dn (mm)", wb["dn_paso"]), ("De MÁXIMO (0 = libre)", wb["de_max"]), ("RESULTADOS A MOSTRAR", wb["max"])])
caja_tipos = widgets.VBox([
    widgets.HTML(_html_celda("TIPOS QUE SE PRUEBAN (nada = el de la tabla)", C_TITULO)),
    widgets.HBox([widgets.VBox([widgets.HTML("<b style='font-size: 12px;'>DEVANADO I</b>"), wb_tipos["I"]]),
                  widgets.VBox([widgets.HTML("<b style='font-size: 12px;'>SECUNDARIO</b>"), wb_tipos["II"]])]),
    widgets.HTML("<b style='font-size: 12px;'>ORDENAR POR</b>"), wb_orden, b_buscar,
], layout=widgets.Layout(margin="0 30px 10px 0", width="430px"))


def leer_busqueda():
    o = {k: _leer(w) for k, w in wb.items()}
    tipos_sec = list(wb_tipos["II"].value)
    o.update(tipos={"I": list(wb_tipos["I"].value), "II": tipos_sec, "III": tipos_sec},
             orden=wb_orden.value, max=int(o["max"]))
    return o


def _texto_devanado(c):
    cond_ = f"cal. {c['medida']}" if c["conductor"] == "ALAMBRE" else "{:g}x{:g}".format(*PLATINAS[c["medida"]])
    return (f"<b>{c['tipo'].title()}</b> · {cond_} · {c['cant']} ({c['horiz']}x{c['cant'] // c['horiz']}) · "
            f"{c['res']['capas']} capas · J {c['jmax']:.2f}" + (" · <i>de la tabla</i>" if c["fijo"] else ""))


def html_busqueda(r, o):
    if r["errores"]:
        return html_errores(r["errores"], "Revisa estos datos antes de buscar:")
    c = r["cuenta"]
    rango = f"Dn {o['dn_fijo']:g} mm" if o["dn_fijo"] > 0 else f"Dn {o['dn_min']:g} a {o['dn_max']:g} mm cada {o['dn_paso']:g}"
    resumen = (f"<b>{c['cumplen']:,}</b> combinaciones cumplen de <b>{c['combinaciones']:,}</b> evaluadas · {rango} · "
               f"B {o['bmin']:g}–{o['bmax']:g} T · J {o['jmin']:g}–{o['jmax']:g} A/mm² · Vcc {o['vcc']:g} % ± {o['tol']:g} %"
               + (f" · De ≤ {o['de_max']:g} mm" if o["de_max"] > 0 else " · De mínimo que entra"))
    avisos = "".join(f"<li>{a}</li>" for a in r["avisos"])
    if not r["resultados"]:
        return html_errores(r["avisos"] or ["No hay combinaciones con estas condiciones."],
                            f"Ninguna combinación cumple ({c['combinaciones']:,} evaluadas):")
    filas = []
    for i, a in enumerate(r["resultados"], start=1):
        dev = {x["clave"]: x for x in a["devanados"]}
        sec_ = next(k for k in dev if k != "I" and not dev[k]["fijo"])
        filas.append([
            f"<b>{i}</b>", f"{a['dn']:g}", a["n"], f"{a['b']:.3f}", f"{a['de']:g}", f"<b>{a['uz']:.2f}</b>",
            (f"{a['error']:.2f}" if estado_error(a["error"]) == "ok"       # en la búsqueda solo quedan hasta 0.5 %
             else f'<b style="color: {C_NO};">! {a["error"]:.2f} · procede</b>'),
            _texto_devanado(dev["I"]), _texto_devanado(dev[sec_]),
            f"{a['cobre']:.0f}", f"{a['nucleo']:.0f}", f"{a['p0']:,.0f}", f"{a['pcu']:,.0f}",
            f"<b>{a['peso']:.0f}</b>", f"<b>{a['perdidas']:,.0f}</b>",
            "&#10004;" if a["pareto"] else "", "&#10004;" if a["verificado"] else "<b style='color: #c53030;'>&#10008;</b>",
        ])
    tabla_res = tabla(["#", "Dn (mm)", "N ref.", "B (T)", "De (mm)", "Vcc (%)", "Error rel. máx. (%)", "Devanado I", "Secundario",
                       "Cobre (kg)", "Núcleo (kg)", "P0 (W)", "I²R (W)", "Peso total (kg)", "Pérdidas totales (W)",
                       "Pareto", "Verif."], filas)
    cuerpo = f"""
        <div style="font-size: 12px; margin-bottom: 6px;">{resumen}. Se muestran las {len(r['resultados'])} primeras por
        <b>{ORDENES_BUSQUEDA[o['orden']].lower()}</b>.</div>
        {f'<ul style="font-size: 12px; margin: 0 0 8px 0; color: #5f370e;">{avisos}</ul>' if avisos else ''}
        {tabla_res}
        <div style="font-size: 11px; margin-top: 6px; line-height: 1.5;">J = densidad con la corriente mayor (entre
        tensiones y tomas). Pareto = no hay otra combinación más liviana y con menos pérdidas a la vez. Verif. = la
        alternativa cargada en el diseño completo da los mismos números. Todas usan «Ajustar a la ventana» con la Hc,
        los papeles, canales y distancias de la pantalla; los anchos de escalón son los óptimos de la tabla para cada
        Dn (los del diseño si Dn no cambia). El kR es el del cuadro por corriente.</div>"""
    derecha = f'<p style="margin: 0; font-size: 14px; font-weight: bold;">Vcc {o["vcc"]:g} % ± {o["tol"]:g} %</p>'
    return hoja("BÚSQUEDA POR Vcc:", f"{w_codigo.value}<br>CONDUCTORES Y DIÁMETRO DEL NÚCLEO", derecha, cuerpo)


def al_buscar(_=None):
    o, d = leer_busqueda(), leer_datos()
    with out_busqueda:
        out_busqueda.clear_output(wait=True)
        display(HTML("<div style='font-size: 12px;'><i>Buscando combinaciones…</i></div>"))
    try:
        r = buscar_combinaciones(d, o)
    except Exception as ex:      # dato que no se previó: se avisa en vez de romper la pantalla
        r = {"errores": [f"{type(ex).__name__}: {ex}"], "resultados": [], "avisos": [], "cuenta": {}}
    _busqueda.update(res=r, o=o)
    wb_alt.options = [(f"{i + 1}: Dn {a['dn']:g} · Vcc {a['uz']:.2f} % · {a['peso']:.0f} kg · {a['perdidas']:,.0f} W", i)
                      for i, a in enumerate(r["resultados"])]
    wb_alt.value = 0 if r["resultados"] else None
    b_usar.disabled = not r["resultados"]
    with out_busqueda:
        out_busqueda.clear_output(wait=True)
        display(HTML(html_busqueda(r, o)))


def al_usar(_=None):
    r = _busqueda["res"]
    if not r or wb_alt.value is None:
        return
    poner_datos(r["resultados"][wb_alt.value]["datos"])


b_buscar.on_click(al_buscar)
b_usar.on_click(al_usar)
panel_busqueda = widgets.VBox([
    widgets.HTML(f"<div style='font-weight: bold; font-size: 14px; margin: 10px 0 6px 0; padding-bottom: 3px; "
                 f"border-bottom: 2px solid {C_TITULO}; max-width: 1000px;'>BÚSQUEDA POR Vcc (opcional) — combinaciones de "
                 f"conductores y diámetro del núcleo con densidad y rango de inducción</div>"),
    widgets.Box([tabla_condiciones, tabla_dn_busqueda, caja_tipos],
                layout=widgets.Layout(display='flex', flex_flow='row wrap', overflow='auto', align_items='flex-start')),
    widgets.HBox([widgets.HTML("<b style='font-size: 12px; line-height: 32px;'>ALTERNATIVA&nbsp;</b>"), wb_alt, b_usar]),
    out_busqueda,
], layout=widgets.Layout(margin='0 0 20px 0'))


# Observers
_todos = [w_codigo, w_frec, w_rep, w_tap, w_var, w_pasos,
          w_dn, w_de, w_hc, w_g, w_bobj, w_fa, w_fconst, w_tubo, w_fases, w_tref,
          w_vcc_obj, w_vcc_tol, w_b_min, w_j_max,
          w_barrera, w_e_barrera, w_tubo_rigido, w_tubo_nucleo] + w_anchos
for _w in w_tab.values():
    _todos += [_w[c] for c in CAMPOS_TABLA]
for _w in _todos:
    _w.observe(actualizar_ui, 'value')

# Una sola pantalla, en el orden del diseño: si no hay ancho, las tablas de la derecha bajan solas
_flex = dict(display='flex', flex_flow='row wrap', overflow='auto', align_items='flex-start')


def _paso(texto):
    return widgets.HTML(f"<div style='font-weight: bold; font-size: 14px; margin: 10px 0 6px 0; padding-bottom: 3px; "
                        f"border-bottom: 2px solid {C_TITULO}; max-width: 1000px;'>{texto}</div>")


interfaz = widgets.VBox([
    ESTILO_TABLA,
    w_barra_pasos,
    _paso("1 · DATOS DEL CLIENTE — potencia, tensiones, grupos, BIL, prueba industrial, frecuencia y regulación"),
    widgets.Box([tabla_cliente, tabla_generales, tabla_tap, tabla_especificacion], layout=widgets.Layout(**_flex)),
    _paso("2 · NÚCLEO — fija el espacio: Hc limita la altura de las bobinas y De su diámetro"),
    widgets.Box([tabla_nucleo, tabla_anchos, tabla_flujo, tabla_vacio], layout=widgets.Layout(**_flex)),
    _paso("3 · DEVANADOS — se construyen dentro de la ventana del núcleo"),
    widgets.HTML(f"<div style='font-size: 12px; margin: 0 0 6px 0; padding: 4px 8px; max-width: 1000px; "
                 f"border-left: 4px solid #e7a83d; background: #fff8e6;'><b>Nota:</b> {NOTA_POSICION}</div>"),
    widgets.Box([tabla_entrada, tabla_cond_dev], layout=widgets.Layout(**_flex)),
    caja_avanzadas,
    _paso("4 · DISTANCIAS ELÉCTRICAS — aislamiento mayor: lo que queda con el núcleo y los devanados ya fijos"),
    widgets.HTML("<div style='font-size: 12px; margin: 0 0 6px 0; max-width: 1000px;'>* Canal interior = separación "
                 "hacia el devanado de adentro (el más interno, hacia el núcleo).</div>"),
    widgets.Box([tabla_distancias], layout=widgets.Layout(**_flex)),
    widgets.HTML(
        "<div style='font-size: 12px; margin: 4px 0; max-width: 1000px;'>Azul = dato que se ingresa · gris = "
        "calculado o cumple · <b>ámbar = falta digitarlo</b> · <b>rojo con &#10008; = no cumple</b> (el color solo marca lo "
        "que hay que atender). <b>Origen</b>: núcleo = hoja de núcleo; potencia, "
        "tensiones, grupos, BIL, conductor y arreglo, pasos, % variación y tap = hoja de datos de entrada; frecuencia y "
        "reparto = especificaciones del cliente; factor de construcción = curva de pérdidas de la chapa; B máxima, B mínima y J máxima = "
        "tus condiciones; datos de bobinado, distancias, factor de apilamiento y tubo = diseño de referencia; "
        "T° de referencia y entre fases mínimo = supuestos por validar; Vcc objetivo y tolerancia = sin fuente. "
        "La búsqueda por Vcc va aparte: no cambia el diseño ni su semáforo. "
        "<b>Las celdas vacías no tienen fuente y se digitan</b>: hasta entonces no se "
        "calcula. Cada devanado tiene dos columnas: primera y segunda tensión. "
        "<b>2ª tensión en 0</b> = una sola tensión · <b>2ª potencia en 0</b> = la misma potencia · <b>devanado sin "
        "potencia</b> = no se usa. <b>Posición radial fija</b>: el Devanado I es siempre el externo; hacia el núcleo "
        "siguen el II y el III. <b>Ajustar a la ventana</b>: las "
        "espiras por capa salen de Hc − 2 x al yugo mínimo, y de ahí las capas. <b>Aislamiento menor</b> (dentro del "
        "devanado): papel de platina, papel entre capas y canales internos de refrigeración, que van <b>dentro de la "
        "espira, entre conductores</b> (en varias capas, también entre capas; caben radiales x capas − 1): el <b>N° de canales</b> y la <b>medida</b> de "
        "cada uno en mm (0 canales = sin canales). <b>Transposiciones</b>: cuántas veces se cruzan los conductores en "
        "paralelo para que todos ocupen todas las posiciones; la completa es cantidad − 1 (12 platinas → 11, como el "
        "diseño de referencia) y cada una suma el ancho de un conductor a la altura. <b>FRANCÉS</b>: siempre 2 capas (2 o 3 verticales), con la mitad de las "
        "espiras en cada una. <b>HÉLICE</b> simple o doble: una sola capa, con todas sus espiras. Si no caben en la altura, "
        "el al yugo muestra cuánto falta. "
        "<b>Aislamiento mayor</b> (entre partes): canal interior hacia el núcleo o el devanado anterior, "
        "distancia al yugo, tubo enrollado y distancia entre fases. <b>Esfuerzos dieléctricos</b> (hoja de esfuerzos): con el "
        "relleno de los extremos y la prueba industrial de cada devanado, la barrera entre bobinas (HAWAYANO o TUBO), el "
        "tubo rígido y el tubo núcleo–bobina: bobina–bobina por contorneo &lt; 0.8 kV/mm; núcleo–bobina &lt; 1.8 kV/mm "
        "(de 1.8 a 2 en rojo pero procede). La regulación va en el Devanado I.</div>"),
], layout=widgets.Layout(margin='0 0 20px 0'))

display(interfaz, panel_busqueda, out)
actualizar_ui()
