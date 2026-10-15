import streamlit as st
import struct
import pandas as pd
import random


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title="Monky BIN Analyzer",
    page_icon="🐒",
    layout="wide"
)


# ============================================================
# ESTILO UNDERGROUND
# ============================================================

st.markdown("""
<style>
.stApp {
    background-color: #080808;
    color: #00ff66;
}
html, body, [class*="css"] {
    font-family: "Courier New", monospace;
}
h1 {
    color: #00ff66 !important;
    font-family: "Courier New", monospace !important;
    font-weight: bold;
    letter-spacing: 3px;
    text-transform: uppercase;
}
h2, h3 {
    color: #00ff66 !important;
    font-family: "Courier New", monospace !important;
}
p {
    color: #b0ffcc;
}
input {
    background-color: #111111 !important;
    color: #00ff66 !important;
    border: 1px solid #00ff66 !important;
    font-family: "Courier New", monospace !important;
}
.stButton > button {
    background-color: #001a0a;
    color: #00ff66;
    border: 1px solid #00ff66;
    border-radius: 0px;
    font-family: "Courier New", monospace;
    font-weight: bold;
    letter-spacing: 2px;
}
.stButton > button:hover {
    background-color: #00ff66;
    color: #000000;
}
[data-testid="stMetric"] {
    background-color: #0d0d0d;
    border: 1px solid #00ff66;
    padding: 15px;
}
[data-testid="stMetricLabel"] {
    color: #00ff66 !important;
}
[data-testid="stMetricValue"] {
    color: #ffffff !important;
}
[data-testid="stDataFrame"] {
    border: 1px solid #00ff66;
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# TÍTULO
# ============================================================

st.title("🐒 🌿💨 MONKY BIN ANALYZER")

st.write(
    "Busca un valor exacto en kilómetros, un valor independiente "
    "en metros y además analiza los metros equivalentes al "
    "kilometraje buscado."
)

st.caption("Concept by Ariel Calacaterra | Developed by DAB")


# ============================================================
# CONSTANTES DE LA APP ORIGINAL
# ============================================================

MARGEN_BUSQUEDA_METROS = 1_000_000
UMBRAL_KM = 100
UMBRAL_METROS_INDEPENDIENTES = 100
UMBRAL_METROS_EQUIVALENTES = 100_000


# ============================================================
# ============================================================
# MÓDULO CS1 / CS2 — INTEGRADO DEL SEGUNDO PROGRAMA
# ============================================================
# ============================================================

BLOCK_LEN = 0x80

CS1_OFF = 0x02
CS1_DATA_START = 0x04
CS1_DATA_LEN = 0x7C

CS2_OFF = 0x7C
CS2_SEED_OFF = 0x78
CS2_DATA_START = 0x08
CS2_DATA_END = 0x78

POLY = 0xEDB88320


def tricore_crc32(seed: int, words) -> int:
    """
    Algoritmo TriCore exactamente como en el segundo programa.
    """
    crc = seed & 0xFFFFFFFF

    for w in words:
        tmp2 = crc & POLY
        tmp1 = 0

        for i in range(32):
            tmp1 ^= (tmp2 >> i) & 1

        crc = (
            w ^ ((crc << 1) | tmp1)
        ) & 0xFFFFFFFF

    return crc


def words_le(data: bytes):
    n = len(data) // 4

    return struct.unpack(
        f"<{n}L",
        data[:n * 4]
    )


def calc_cs1(buf, bstart: int) -> int:
    seed = (
        buf[bstart]
        | (buf[bstart + 1] << 8)
    )

    chunk = bytes(
        buf[
            bstart + CS1_DATA_START:
            bstart + CS1_DATA_START + CS1_DATA_LEN
        ]
    )

    return tricore_crc32(
        seed,
        words_le(chunk)
    ) & 0xFFFF


def calc_cs2(buf, bstart: int) -> int:
    seed = struct.unpack_from(
        "<I",
        bytes(buf),
        bstart + CS2_SEED_OFF
    )[0]

    chunk = bytes(
        buf[
            bstart + CS2_DATA_START:
            bstart + CS2_DATA_END
        ]
    )

    return tricore_crc32(
        seed,
        words_le(chunk)
    )


def cs2_no_aplica(stored: int) -> bool:
    return (
        stored == 0x00000000
        or stored == 0xFFFFFFFF
    )


def is_blank(chunk) -> bool:
    return (
        all(b == 0 for b in chunk)
        or
        all(b == 0xFF for b in chunk)
    )


def _banco_activo(data) -> int:
    """
    Detección del banco activo del segundo programa.
    """
    mitad = len(data) // 2

    if not is_blank(
        data[
            0x90:
            min(mitad, 0x8000)
        ]
    ):
        return 0

    return mitad


def _candidatos_layout(data):
    """
    Configuraciones conocidas del segundo programa.
    """
    n = len(data)
    mitad = n // 2

    candidatos = [
        (
            "grid desde 0x00, archivo completo",
            0x00,
            n
        ),
        (
            "grid desde 0x80, archivo completo",
            0x80,
            n
        ),
    ]

    # Variante doble banco EDC17C54.
    if data[0:4] == bytes.fromhex("feca02a5"):

        b = _banco_activo(data)

        candidatos.append(
            (
                f"doble banco, banco activo {hex(b)}, grid +0x80",
                b + 0x80,
                b + mitad
            )
        )

    return candidatos


def detectar_layout(data):
    """
    Autodetección exactamente basada en el mejor porcentaje de CS1.
    """
    mejor = None

    for nombre, ini, fin in _candidatos_layout(data):

        total = 0
        correctos = 0

        for b in range(
            ini,
            min(fin, len(data)),
            BLOCK_LEN
        ):

            if b + BLOCK_LEN > len(data):
                break

            if is_blank(
                data[b:b + BLOCK_LEN]
            ):
                continue

            total += 1

            cs1_calc = calc_cs1(
                data,
                b
            )

            cs1_stored = (
                data[b + 2]
                | (data[b + 3] << 8)
            )

            if cs1_calc == cs1_stored:
                correctos += 1

        ratio = (
            correctos / total
            if total
            else 0
        )

        if (
            mejor is None
            or ratio > mejor[0]
        ):
            mejor = (
                ratio,
                nombre,
                ini,
                fin,
                total,
                correctos
            )

    return mejor


def iter_blocks(data, ini, fin):
    for b in range(
        ini,
        min(fin, len(data)),
        BLOCK_LEN
    ):

        if b + BLOCK_LEN > len(data):
            break

        if is_blank(
            data[b:b + BLOCK_LEN]
        ):
            continue

        yield b


# ============================================================
# VERIFICACIÓN CS1 / CS2
# ============================================================

def verificar_checksum_bytes(data):
    """
    Devuelve:
        layout
        dataframe por bloque
        resumen
    """

    ratio, nombre, ini, fin, _, _ = (
        detectar_layout(data)
    )

    filas = []

    for b in iter_blocks(
        data,
        ini,
        fin
    ):

        block_id = (
            data[b]
            | (data[b + 1] << 8)
        )

        cs1_calc = calc_cs1(
            data,
            b
        )

        cs1_stored = (
            data[b + CS1_OFF]
            | (data[b + CS1_OFF + 1] << 8)
        )

        cs1_ok = (
            cs1_calc == cs1_stored
        )

        cs2_calc = calc_cs2(
            data,
            b
        )

        cs2_stored = struct.unpack_from(
            "<I",
            bytes(data),
            b + CS2_OFF
        )[0]

        cs2_ok = (
            cs2_calc == cs2_stored
        )

        cs2_na = cs2_no_aplica(
            cs2_stored
        )

        # El segundo programa distingue CS2 "no aplica".
        # Para el estado global no se considera error.
        global_ok = (
            cs1_ok
            and
            (cs2_ok or cs2_na)
        )

        filas.append({

            "Bloque":
                b // BLOCK_LEN,

            "Offset":
                b,

            "Offset HEX":
                f"0x{b:04X}",

            "Block ID":
                block_id,

            "CS1 calculado":
                cs1_calc,

            "CS1 almacenado":
                cs1_stored,

            "CS1 OK":
                cs1_ok,

            "CS2 calculado":
                cs2_calc,

            "CS2 almacenado":
                cs2_stored,

            "CS2 OK":
                cs2_ok,

            "CS2 no aplica":
                cs2_na,

            "OK":
                global_ok
        })

    df = pd.DataFrame(
        filas
    )

    if df.empty:

        resumen = {
            "bloques": 0,
            "cs1_ok": 0,
            "cs2_ok": 0,
            "cs2_na": 0,
            "cs2_bad": 0,
            "global_ok": 0
        }

    else:

        total = len(df)

        cs1_ok = int(
            df["CS1 OK"].sum()
        )

        cs2_ok = int(
            df["CS2 OK"].sum()
        )

        cs2_na = int(
            df["CS2 no aplica"].sum()
        )

        cs2_bad = int(
            (
                ~df["CS2 OK"]
                &
                ~df["CS2 no aplica"]
            ).sum()
        )

        global_ok = int(
            df["OK"].sum()
        )

        resumen = {
            "bloques": total,
            "cs1_ok": cs1_ok,
            "cs2_ok": cs2_ok,
            "cs2_na": cs2_na,
            "cs2_bad": cs2_bad,
            "global_ok": global_ok
        }

    return {
        "layout": nombre,
        "ratio_cs1": ratio,
        "inicio": ini,
        "fin": fin,
        "df": df,
        "resumen": resumen
    }


# ============================================================
# REPARACIÓN CON ORIGINAL COMO REFERENCIA
# ============================================================

def reparar_ref_bytes(
    datos_originales,
    datos_modificados
):
    """
    MODO RECOMENDADO DEL SEGUNDO PROGRAMA.

    Usa el BIN original como referencia.

    - Si el CS2 original es genuino, se recalcula en el modificado.
    - Si el CS2 original no coincide, se considera campo de datos
      y NO se toca.
    - CS2 se procesa antes que CS1.
    - Luego se recalcula CS1.
    """

    ori = bytearray(
        datos_originales
    )

    mod = bytearray(
        datos_modificados
    )

    if len(ori) != len(mod):
        raise ValueError(
            "Los archivos tienen tamaños distintos."
        )

    (
        ratio,
        nombre,
        ini,
        fin,
        _,
        _
    ) = detectar_layout(
        ori
    )

    tocados = []

    cs1_fixed = 0
    cs2_fixed = 0
    cs2_protegidos = 0

    for b in iter_blocks(
        mod,
        ini,
        fin
    ):

        # ----------------------------------------------------
        # El ORIGINAL determina si el campo CS2 es realmente
        # checksum o es otro dato.
        # ----------------------------------------------------

        c2_ori_stored = struct.unpack_from(
            "<I",
            bytes(ori),
            b + CS2_OFF
        )[0]

        cs2_es_genuino = (
            calc_cs2(ori, b)
            == c2_ori_stored
        )

        algo_cambio = False

        # ----------------------------------------------------
        # CS2 PRIMERO
        # ----------------------------------------------------

        if cs2_es_genuino:

            c2 = calc_cs2(
                mod,
                b
            )

            c2s = struct.unpack_from(
                "<I",
                bytes(mod),
                b + CS2_OFF
            )[0]

            if c2 != c2s:

                struct.pack_into(
                    "<I",
                    mod,
                    b + CS2_OFF,
                    c2
                )

                cs2_fixed += 1
                algo_cambio = True

        else:

            c2s = struct.unpack_from(
                "<I",
                bytes(mod),
                b + CS2_OFF
            )[0]

            if calc_cs2(
                mod,
                b
            ) != c2s:

                cs2_protegidos += 1

        # ----------------------------------------------------
        # CS1 DESPUÉS
        # ----------------------------------------------------

        c1 = calc_cs1(
            mod,
            b
        )

        c1s = (
            mod[b + CS1_OFF]
            |
            (mod[b + CS1_OFF + 1] << 8)
        )

        if c1 != c1s:

            mod[
                b + CS1_OFF:
                b + CS1_OFF + 2
            ] = int(c1).to_bytes(
                2,
                "little"
            )

            cs1_fixed += 1
            algo_cambio = True

        if algo_cambio:

            tocados.append(
                b
            )

    return (
        bytes(mod),
        {
            "layout": nombre,
            "ratio_cs1": ratio,
            "cs1_fixed": cs1_fixed,
            "cs2_fixed": cs2_fixed,
            "cs2_protegidos": cs2_protegidos,
            "bloques_tocados": tocados
        }
    )


# ============================================================
# DIFF ORIGINAL / MODIFICADO
# ============================================================

def diff_bytes(
    datos_originales,
    datos_modificados
):
    a = bytes(datos_originales)
    b = bytes(datos_modificados)

    if len(a) != len(b):

        return {
            "mismo_tamano": False,
            "total_diferencias": None,
            "rangos": [],
            "df": pd.DataFrame()
        }

    diferencias = [
        i
        for i in range(len(a))
        if a[i] != b[i]
    ]

    if not diferencias:

        return {
            "mismo_tamano": True,
            "total_diferencias": 0,
            "rangos": [],
            "df": pd.DataFrame()
        }

    rangos = []

    inicio = anterior = diferencias[0]

    for i in diferencias[1:]:

        if i == anterior + 1:

            anterior = i

        else:

            rangos.append(
                (inicio, anterior)
            )

            inicio = anterior = i

    rangos.append(
        (inicio, anterior)
    )

    filas = []

    for r0, r1 in rangos:

        filas.append({

            "Inicio":
                r0,

            "Inicio HEX":
                f"0x{r0:04X}",

            "Fin":
                r1,

            "Fin HEX":
                f"0x{r1:04X}",

            "Bytes modificados":
                r1 - r0 + 1,

            "Bytes originales":
                a[r0:r1 + 1].hex(
                    " "
                ).upper(),

            "Bytes modificados BIN":
                b[r0:r1 + 1].hex(
                    " "
                ).upper()
        })

    return {
        "mismo_tamano": True,
        "total_diferencias":
            len(diferencias),
        "rangos":
            rangos,
        "df":
            pd.DataFrame(filas)
    }


# ============================================================
# INTERFAZ
# ============================================================

archivo = st.file_uploader(
    "Seleccionar archivo BIN",
    type=["bin"]
)


ingrekk = st.number_input(
    "Kilometraje / valor exacto a buscar",
    min_value=0,
    value=None,
    placeholder="Ingrese el kilometraje",
    step=1
)


busqueda_metros_input = st.number_input(
    "Valor independiente a buscar en metros",
    min_value=0,
    value=None,
    placeholder="Ingrese el valor en metros",
    step=1
)


nuevo_km_input = st.number_input(
    "Nuevo kilometraje fijo",
    min_value=0,
    value=None,
    placeholder="Ingrese el nuevo kilometraje",
    step=1
)


st.number_input(
    "Margen de búsqueda en metros",
    min_value=0,
    value=MARGEN_BUSQUEDA_METROS,
    step=100_000,
    disabled=True
)


st.info(
    f"Umbral KM: modificación si distancia absoluta < "
    f"**{UMBRAL_KM:,} km** | "
    f"Umbral metros independientes: modificación si distancia absoluta < "
    f"**{UMBRAL_METROS_INDEPENDIENTES:,} m** | "
    f"Umbral metros equivalentes: modificación si distancia absoluta < "
    f"**{UMBRAL_METROS_EQUIVALENTES:,} m**"
)


buscar = st.button(
    "🔎 Buscar, modificar y reparar checksums",
    type="primary"
)


# ============================================================
# PROCESAMIENTO PRINCIPAL
# ============================================================

if buscar:

    # ========================================================
    # VALIDACIONES
    # ========================================================

    if archivo is None:

        st.warning(
            "Primero debes cargar un archivo BIN."
        )

    elif ingrekk is None:

        st.warning(
            "Ingrese el kilometraje / valor exacto a buscar."
        )

    elif busqueda_metros_input is None:

        st.warning(
            "Ingrese el valor independiente a buscar en metros."
        )

    elif nuevo_km_input is None:

        st.warning(
            "Ingrese el nuevo kilometraje fijo."
        )

    else:

        # ====================================================
        # LEER BIN
        # ====================================================

        datos_originales = archivo.read()

        datos_modificados = bytearray(
            datos_originales
        )

        tamaño = len(
            datos_originales
        )

        objetivo = int(
            ingrekk
        )

        objetivo_metros_independiente = int(
            busqueda_metros_input
        )

        nuevo_km = int(
            nuevo_km_input
        )


        # ====================================================
        # RANGOS ORIGINALES
        # ====================================================

        rango_inicio = (
            objetivo // 1000
        ) * 1000

        rango_fin = (
            rango_inicio + 999
        )

        objetivo_metros = (
            objetivo * 1000
        )

        limite_inicio = (
            objetivo_metros
            - MARGEN_BUSQUEDA_METROS
        )

        limite_fin = (
            objetivo_metros
            + MARGEN_BUSQUEDA_METROS
        )

        rango_metros_inicio = (
            objetivo_metros_independiente // 1000
        ) * 1000

        rango_metros_fin = (
            rango_metros_inicio + 999
        )


        # ====================================================
        # INFORMACIÓN DEL ARCHIVO
        # ====================================================

        st.success(
            f"Archivo cargado correctamente: {archivo.name}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Tamaño BIN",
            f"{tamaño:,} bytes"
        )

        col2.metric(
            "KM buscado",
            f"{objetivo:,}"
        )

        col3.metric(
            "Metros independientes",
            f"{objetivo_metros_independiente:,}"
        )

        col4.metric(
            "KM → metros",
            f"{objetivo_metros:,}"
        )


        # ====================================================
        # LISTAS DE RESULTADOS
        # ====================================================

        resultados_barrido = []
        resultados_metros_independientes = []
        resultados_metros = []

        direcciones_km = []
        direcciones_metros_independientes = []
        direcciones_metros_modificar = []

        direcciones_usadas = set()


        # ====================================================
        # BARRIDO COMPLETO ORIGINAL
        #
        # SE MANTIENE LA LÓGICA ORIGINAL.
        # ====================================================

        for direccion in range(
            0,
            tamaño - 3
        ):

            valor = struct.unpack_from(
                "<I",
                datos_originales,
                direccion
            )[0]

            bytes_valor = (
                datos_originales[
                    direccion:
                    direccion + 4
                ]
            )


            # =================================================
            # 1. KM
            # =================================================

            if (
                rango_inicio
                <= valor
                <= rango_fin
            ):

                diferencia = (
                    valor
                    - objetivo
                )

                distancia_absoluta = abs(
                    diferencia
                )

                if valor == objetivo:

                    tipo_coincidencia = "🔴 EXACTO"

                elif (
                    distancia_absoluta
                    < UMBRAL_KM
                ):

                    tipo_coincidencia = (
                        f"🟡 CERCANO < "
                        f"{UMBRAL_KM} KM"
                    )

                else:

                    tipo_coincidencia = ""

                resultados_barrido.append({

                    "Dirección":
                        f"0x{direccion:04X}",

                    "Valor":
                        valor,

                    "Diferencia desde exacto":
                        diferencia,

                    "Distancia absoluta":
                        distancia_absoluta,

                    "Coincidencia":
                        tipo_coincidencia,

                    "HEX":
                        f"0x{valor:08X}",

                    "Bytes":
                        bytes_valor.hex(
                            " "
                        ).upper()
                })

                if (
                    distancia_absoluta
                    < UMBRAL_KM
                    and direccion
                    not in direcciones_usadas
                ):

                    direcciones_km.append(
                        direccion
                    )

                    direcciones_usadas.add(
                        direccion
                    )


            # =================================================
            # 2. METROS INDEPENDIENTES
            # =================================================

            if (
                rango_metros_inicio
                <= valor
                <= rango_metros_fin
            ):

                diferencia_metros_ind = (
                    valor
                    - objetivo_metros_independiente
                )

                distancia_metros_ind = abs(
                    diferencia_metros_ind
                )

                if (
                    valor
                    == objetivo_metros_independiente
                ):

                    tipo_coincidencia_metros = (
                        "🔴 EXACTO"
                    )

                elif (
                    distancia_metros_ind
                    < UMBRAL_METROS_INDEPENDIENTES
                ):

                    tipo_coincidencia_metros = (
                        f"🟡 CERCANO < "
                        f"{UMBRAL_METROS_INDEPENDIENTES:,} m"
                    )

                else:

                    tipo_coincidencia_metros = ""

                cumple_umbral_independiente = (
                    distancia_metros_ind
                    < UMBRAL_METROS_INDEPENDIENTES
                )

                direccion_ya_usada = (
                    direccion
                    in direcciones_usadas
                )

                if cumple_umbral_independiente:

                    if direccion_ya_usada:

                        modifica_ind = (
                            "NO - YA RESERVADA"
                        )

                    else:

                        modifica_ind = "SÍ"

                else:

                    modifica_ind = "NO"

                resultados_metros_independientes.append({

                    "Dirección":
                        f"0x{direccion:04X}",

                    "Valor":
                        valor,

                    "Kilómetros":
                        round(
                            valor / 1000,
                            3
                        ),

                    "Metros":
                        valor,

                    "Diferencia (m)":
                        diferencia_metros_ind,

                    "Distancia absoluta":
                        distancia_metros_ind,

                    "Coincidencia":
                        tipo_coincidencia_metros,

                    "Modifica":
                        modifica_ind,

                    "HEX":
                        f"0x{valor:08X}",

                    "Bytes":
                        bytes_valor.hex(
                            " "
                        ).upper()
                })

                if (
                    cumple_umbral_independiente
                    and not direccion_ya_usada
                ):

                    direcciones_metros_independientes.append(
                        direccion
                    )

                    direcciones_usadas.add(
                        direccion
                    )


            # =================================================
            # 3. METROS EQUIVALENTES AL KM
            # =================================================

            if (
                limite_inicio
                <= valor
                <= limite_fin
            ):

                diferencia = (
                    valor
                    - objetivo_metros
                )

                distancia_absoluta = abs(
                    diferencia
                )

                cumple_umbral_equivalente = (
                    distancia_absoluta
                    < UMBRAL_METROS_EQUIVALENTES
                )

                direccion_ya_usada = (
                    direccion
                    in direcciones_usadas
                )

                if cumple_umbral_equivalente:

                    if direccion_ya_usada:

                        modifica_equivalente = (
                            "NO - YA RESERVADA"
                        )

                    else:

                        modifica_equivalente = "SÍ"

                else:

                    modifica_equivalente = "NO"

                resultados_metros.append({

                    "Dirección":
                        f"0x{direccion:04X}",

                    "Valor":
                        valor,

                    "Kilómetros":
                        round(
                            valor / 1000,
                            3
                        ),

                    "Metros":
                        valor,

                    "Diferencia (m)":
                        diferencia,

                    "Distancia absoluta":
                        distancia_absoluta,

                    "Modifica":
                        modifica_equivalente,

                    "HEX":
                        f"0x{valor:08X}",

                    "Bytes":
                        bytes_valor.hex(
                            " "
                        ).upper()
                })

                if (
                    cumple_umbral_equivalente
                    and not direccion_ya_usada
                ):

                    direcciones_metros_modificar.append(
                        direccion
                    )

                    direcciones_usadas.add(
                        direccion
                    )


        # ====================================================
        # DATAFRAMES
        # ====================================================

        resultado_barrido = pd.DataFrame(
            resultados_barrido
        )

        resultado_metros_independientes = pd.DataFrame(
            resultados_metros_independientes
        )

        resultado_metros = pd.DataFrame(
            resultados_metros
        )


        # ====================================================
        # RESULTADOS KM
        # ====================================================

        st.subheader(
            "🔎 Barrido de las tres últimas cifras — KM"
        )

        st.write(
            f"Se buscaron todos los valores desde "
            f"**{rango_inicio:,}** hasta "
            f"**{rango_fin:,}**."
        )

        st.info(
            f"Se modificarán los valores cuya distancia "
            f"absoluta respecto de **{objetivo:,} km** sea "
            f"**menor a {UMBRAL_KM:,} km**."
        )

        if resultado_barrido.empty:

            st.warning(
                f"No se encontraron valores entre "
                f"{rango_inicio:,} y "
                f"{rango_fin:,}."
            )

        else:

            resultado_barrido = (
                resultado_barrido
                .sort_values(
                    [
                        "Valor",
                        "Dirección"
                    ]
                )
                .reset_index(
                    drop=True
                )
            )

            st.success(
                f"Se encontraron "
                f"{len(resultado_barrido)} "
                f"coincidencias."
            )

            st.dataframe(
                resultado_barrido,
                use_container_width=True,
                hide_index=True
            )

            exactos = resultado_barrido[
                resultado_barrido[
                    "Valor"
                ] == objetivo
            ]

            st.subheader(
                f"Valor exacto: {objetivo:,}"
            )

            if exactos.empty:

                st.warning(
                    f"No se encontró el valor exacto "
                    f"{objetivo:,}."
                )

            else:

                st.success(
                    f"Se encontraron "
                    f"{len(exactos)} "
                    f"apariciones exactas."
                )

                st.dataframe(
                    exactos,
                    use_container_width=True,
                    hide_index=True
                )

            cercanos = resultado_barrido[
                resultado_barrido[
                    "Distancia absoluta"
                ] < UMBRAL_KM
            ]

            st.subheader(
                f"Valores KM que cumplen < "
                f"{UMBRAL_KM:,} km"
            )

            if cercanos.empty:

                st.warning(
                    "No hay valores KM dentro del "
                    "umbral de modificación."
                )

            else:

                st.success(
                    f"Se modificarán "
                    f"{len(cercanos)} "
                    f"apariciones KM."
                )

                st.dataframe(
                    cercanos,
                    use_container_width=True,
                    hide_index=True
                )

            st.subheader(
                "Resumen del barrido KM"
            )

            resumen = (
                resultado_barrido[
                    "Valor"
                ]
                .value_counts()
                .sort_index()
                .reset_index()
            )

            resumen.columns = [
                "Valor",
                "Cantidad de apariciones"
            ]

            st.dataframe(
                resumen,
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # METROS INDEPENDIENTES
        # ====================================================

        st.subheader(
            "📏 Barrido independiente de las tres últimas cifras — METROS"
        )

        st.write(
            f"Valor independiente buscado: "
            f"**{objetivo_metros_independiente:,} metros**"
        )

        st.write(
            f"Rango de las tres últimas cifras: "
            f"**{rango_metros_inicio:,} → "
            f"{rango_metros_fin:,} metros**"
        )

        st.info(
            f"Umbral de modificación independiente: "
            f"**< {UMBRAL_METROS_INDEPENDIENTES:,} m**"
        )

        st.info(
            f"Este valor es independiente del kilometraje "
            f"**{objetivo:,} km**."
        )

        if resultado_metros_independientes.empty:

            st.warning(
                f"No se encontraron valores entre "
                f"{rango_metros_inicio:,} y "
                f"{rango_metros_fin:,} metros."
            )

        else:

            resultado_metros_independientes = (
                resultado_metros_independientes
                .sort_values(
                    [
                        "Valor",
                        "Dirección"
                    ]
                )
                .reset_index(
                    drop=True
                )
            )

            st.success(
                f"Se encontraron "
                f"{len(resultado_metros_independientes)} "
                f"coincidencias."
            )

            st.dataframe(
                resultado_metros_independientes,
                use_container_width=True,
                hide_index=True
            )

            exactos_metros_ind = (
                resultado_metros_independientes[
                    resultado_metros_independientes[
                        "Valor"
                    ]
                    == objetivo_metros_independiente
                ]
            )

            st.subheader(
                f"Valor exacto en metros: "
                f"{objetivo_metros_independiente:,}"
            )

            if exactos_metros_ind.empty:

                st.warning(
                    f"No se encontró el valor exacto "
                    f"{objetivo_metros_independiente:,} m."
                )

            else:

                st.success(
                    f"Se encontraron "
                    f"{len(exactos_metros_ind)} "
                    f"apariciones exactas."
                )

                st.dataframe(
                    exactos_metros_ind,
                    use_container_width=True,
                    hide_index=True
                )

            cercanos_metros_ind = (
                resultado_metros_independientes[
                    resultado_metros_independientes[
                        "Distancia absoluta"
                    ]
                    < UMBRAL_METROS_INDEPENDIENTES
                ]
            )

            st.subheader(
                f"Valores metros independientes que cumplen "
                f"< {UMBRAL_METROS_INDEPENDIENTES:,} m"
            )

            if cercanos_metros_ind.empty:

                st.warning(
                    "No hay valores dentro del "
                    "umbral de modificación."
                )

            else:

                st.success(
                    f"Se encontraron "
                    f"{len(cercanos_metros_ind)} "
                    f"valores dentro del umbral."
                )

                st.dataframe(
                    cercanos_metros_ind,
                    use_container_width=True,
                    hide_index=True
                )


        # ====================================================
        # METROS EQUIVALENTES
        # ====================================================

        st.subheader(
            "📐 Análisis de metros equivalentes al KM buscado"
        )

        st.write(
            f"Kilometraje buscado: "
            f"**{objetivo:,} km**"
        )

        st.write(
            f"Equivalente: "
            f"**{objetivo_metros:,} metros**"
        )

        st.write(
            f"Margen de búsqueda: "
            f"**±{MARGEN_BUSQUEDA_METROS:,} metros**"
        )

        st.write(
            f"Rango de búsqueda: "
            f"**{limite_inicio:,} → "
            f"{limite_fin:,} metros**"
        )

        st.write(
            f"Umbral de modificación: "
            f"**< {UMBRAL_METROS_EQUIVALENTES:,} metros**"
        )

        if resultado_metros.empty:

            st.warning(
                "No se encontraron valores dentro "
                "del margen de búsqueda."
            )

        else:

            resultado_metros = (
                resultado_metros
                .sort_values(
                    "Distancia absoluta"
                )
                .reset_index(
                    drop=True
                )
            )

            st.success(
                f"Se encontraron "
                f"{len(resultado_metros)} "
                f"coincidencias dentro del margen."
            )

            st.dataframe(
                resultado_metros,
                use_container_width=True,
                hide_index=True
            )

            metros_a_modificar = (
                resultado_metros[
                    resultado_metros[
                        "Modifica"
                    ] == "SÍ"
                ]
            )

            st.subheader(
                f"Valores en metros equivalentes al KM que "
                f"cumplen < {UMBRAL_METROS_EQUIVALENTES:,} m"
            )

            if metros_a_modificar.empty:

                st.warning(
                    "No hay valores en metros dentro "
                    "del umbral de modificación."
                )

            else:

                st.success(
                    f"Se modificarán "
                    f"{len(metros_a_modificar)} "
                    f"apariciones en metros."
                )

                st.dataframe(
                    metros_a_modificar,
                    use_container_width=True,
                    hide_index=True
                )

            cercano = (
                resultado_metros.iloc[0]
            )

            st.info(
                f"Más cercano al equivalente: "
                f"{cercano['Metros']:,} metros | "
                f"{cercano['Kilómetros']} km | "
                f"Diferencia: "
                f"{cercano['Diferencia (m)']:+,} m | "
                f"Distancia absoluta: "
                f"{cercano['Distancia absoluta']:,} m | "
                f"Dirección: "
                f"{cercano['Dirección']}"
            )


        # ====================================================
        # RESUMEN MODIFICACIONES
        # ====================================================

        st.subheader(
            "🛠️ Modificación de valores"
        )

        cantidad_km = len(
            direcciones_km
        )

        cantidad_metros_independientes = len(
            direcciones_metros_independientes
        )

        cantidad_metros_equivalentes = len(
            direcciones_metros_modificar
        )

        total_modificaciones = len(
            direcciones_usadas
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "KM a modificar",
            cantidad_km
        )

        col2.metric(
            "Metros independientes",
            cantidad_metros_independientes
        )

        col3.metric(
            "Metros equivalentes",
            cantidad_metros_equivalentes
        )

        col4.metric(
            "TOTAL ÚNICO",
            total_modificaciones
        )


        # ====================================================
        # CONTROL SOLAPAMIENTO
        # ====================================================

        interseccion_km_ind = (
            set(direcciones_km)
            &
            set(direcciones_metros_independientes)
        )

        interseccion_km_equiv = (
            set(direcciones_km)
            &
            set(direcciones_metros_modificar)
        )

        interseccion_ind_equiv = (
            set(direcciones_metros_independientes)
            &
            set(direcciones_metros_modificar)
        )

        total_intersecciones = (
            len(interseccion_km_ind)
            +
            len(interseccion_km_equiv)
            +
            len(interseccion_ind_equiv)
        )

        if total_intersecciones == 0:

            st.success(
                "🔒 CONTROL DE SOLAPAMIENTO: "
                "No existen direcciones repetidas. "
                "Cada dirección será modificada una sola vez."
            )

        else:

            st.error(
                f"⚠️ Se detectaron "
                f"{total_intersecciones} "
                f"solapamientos."
            )


        # ====================================================
        # REALIZAR MODIFICACIONES
        # ====================================================

        modificaciones = []

        sufijos_independientes = []
        sufijos = []


        # ----------------------------------------------------
        # KM
        # ----------------------------------------------------

        for direccion in direcciones_km:

            valor_anterior = struct.unpack_from(
                "<I",
                datos_originales,
                direccion
            )[0]

            diferencia = (
                valor_anterior
                - objetivo
            )

            distancia_absoluta = abs(
                diferencia
            )

            if valor_anterior == objetivo:

                tipo_modificacion = "KM exacto"

            elif valor_anterior < objetivo:

                tipo_modificacion = (
                    f"KM cercano por debajo "
                    f"(< {UMBRAL_KM} km)"
                )

            else:

                tipo_modificacion = (
                    f"KM cercano por encima "
                    f"(< {UMBRAL_KM} km)"
                )

            nuevo_valor = nuevo_km

            nuevos_bytes = struct.pack(
                "<I",
                nuevo_valor
            )

            datos_modificados[
                direccion:
                direccion + 4
            ] = nuevos_bytes

            modificaciones.append({

                "Tipo":
                    tipo_modificacion,

                "Dirección":
                    f"0x{direccion:04X}",

                "Valor anterior":
                    valor_anterior,

                "Diferencia":
                    diferencia,

                "Distancia absoluta":
                    distancia_absoluta,

                "Nuevo valor":
                    nuevo_valor,

                "Kilómetros":
                    nuevo_valor,

                "Últimas 3 cifras":
                    "",

                "HEX anterior":
                    f"0x{valor_anterior:08X}",

                "HEX nuevo":
                    f"0x{nuevo_valor:08X}",

                "Bytes anteriores":
                    datos_originales[
                        direccion:
                        direccion + 4
                    ].hex(
                        " "
                    ).upper(),

                "Bytes nuevos":
                    nuevos_bytes.hex(
                        " "
                    ).upper()
            })


        # ----------------------------------------------------
        # SUFIJOS METROS INDEPENDIENTES
        # ----------------------------------------------------

        cantidad_ind = len(
            direcciones_metros_independientes
        )

        if cantidad_ind <= 1000:

            sufijos_independientes = random.sample(
                range(1000),
                cantidad_ind
            )

        else:

            sufijos_independientes = [
                random.randint(
                    0,
                    999
                )
                for _ in range(
                    cantidad_ind
                )
            ]


        # ----------------------------------------------------
        # METROS INDEPENDIENTES
        # ----------------------------------------------------

        for direccion, sufijo in zip(
            direcciones_metros_independientes,
            sufijos_independientes
        ):

            valor_anterior = struct.unpack_from(
                "<I",
                datos_originales,
                direccion
            )[0]

            diferencia = (
                valor_anterior
                - objetivo_metros_independiente
            )

            distancia_absoluta = abs(
                diferencia
            )

            nuevo_valor = (
                nuevo_km * 1000
            ) + sufijo

            nuevos_bytes = struct.pack(
                "<I",
                nuevo_valor
            )

            datos_modificados[
                direccion:
                direccion + 4
            ] = nuevos_bytes

            modificaciones.append({

                "Tipo":
                    "Metros independientes",

                "Dirección":
                    f"0x{direccion:04X}",

                "Valor anterior":
                    valor_anterior,

                "Diferencia":
                    diferencia,

                "Distancia absoluta":
                    distancia_absoluta,

                "Nuevo valor":
                    nuevo_valor,

                "Kilómetros":
                    round(
                        nuevo_valor / 1000,
                        3
                    ),

                "Últimas 3 cifras":
                    f"{sufijo:03d}",

                "HEX anterior":
                    f"0x{valor_anterior:08X}",

                "HEX nuevo":
                    f"0x{nuevo_valor:08X}",

                "Bytes anteriores":
                    datos_originales[
                        direccion:
                        direccion + 4
                    ].hex(
                        " "
                    ).upper(),

                "Bytes nuevos":
                    nuevos_bytes.hex(
                        " "
                    ).upper()
            })


        # ----------------------------------------------------
        # SUFIJOS METROS EQUIVALENTES
        # ----------------------------------------------------

        cantidad = len(
            direcciones_metros_modificar
        )

        if cantidad <= 1000:

            sufijos = random.sample(
                range(1000),
                cantidad
            )

        else:

            sufijos = [
                random.randint(
                    0,
                    999
                )
                for _ in range(
                    cantidad
                )
            ]


        # ----------------------------------------------------
        # METROS EQUIVALENTES
        # ----------------------------------------------------

        for direccion, sufijo in zip(
            direcciones_metros_modificar,
            sufijos
        ):

            valor_anterior = struct.unpack_from(
                "<I",
                datos_originales,
                direccion
            )[0]

            diferencia = (
                valor_anterior
                - objetivo_metros
            )

            distancia_absoluta = abs(
                diferencia
            )

            nuevo_valor = (
                nuevo_km * 1000
            ) + sufijo

            nuevos_bytes = struct.pack(
                "<I",
                nuevo_valor
            )

            datos_modificados[
                direccion:
                direccion + 4
            ] = nuevos_bytes

            modificaciones.append({

                "Tipo":
                    "Metros equivalentes al KM",

                "Dirección":
                    f"0x{direccion:04X}",

                "Valor anterior":
                    valor_anterior,

                "Diferencia":
                    diferencia,

                "Distancia absoluta":
                    distancia_absoluta,

                "Nuevo valor":
                    nuevo_valor,

                "Kilómetros":
                    round(
                        nuevo_valor / 1000,
                        3
                    ),

                "Últimas 3 cifras":
                    f"{sufijo:03d}",

                "HEX anterior":
                    f"0x{valor_anterior:08X}",

                "HEX nuevo":
                    f"0x{nuevo_valor:08X}",

                "Bytes anteriores":
                    datos_originales[
                        direccion:
                        direccion + 4
                    ].hex(
                        " "
                    ).upper(),

                "Bytes nuevos":
                    nuevos_bytes.hex(
                        " "
                    ).upper()
            })


        # ====================================================
        # DATAFRAME MODIFICACIONES
        # ====================================================

        resultado_modificaciones = pd.DataFrame(
            modificaciones
        )


        # ====================================================
        # MOSTRAR MODIFICACIONES
        # ====================================================

        st.subheader(
            "📋 Registro de modificaciones"
        )

        st.success(
            f"Se realizaron "
            f"{len(modificaciones)} "
            f"modificaciones sobre "
            f"{len(set(resultado_modificaciones['Dirección'])) if not resultado_modificaciones.empty else 0} "
            f"direcciones únicas."
        )

        if not resultado_modificaciones.empty:

            direcciones_registro = (
                resultado_modificaciones[
                    "Dirección"
                ].tolist()
            )

            if (
                len(direcciones_registro)
                ==
                len(set(direcciones_registro))
            ):

                st.success(
                    "🔒 CONFIRMADO: ninguna dirección "
                    "fue modificada dos veces."
                )

            else:

                st.error(
                    "⚠️ ERROR: existen direcciones "
                    "duplicadas en el registro."
                )

            st.dataframe(
                resultado_modificaciones,
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # VERIFICAR REEMPLAZOS ANTES DEL CHECKSUM
        # ====================================================

        st.subheader(
            "✓ Verificación de reemplazos"
        )

        errores = 0

        for direccion in direcciones_km:

            valor_verificado = struct.unpack_from(
                "<I",
                datos_modificados,
                direccion
            )[0]

            if valor_verificado != nuevo_km:

                errores += 1

        for direccion, sufijo in zip(
            direcciones_metros_independientes,
            sufijos_independientes
        ):

            valor_esperado = (
                nuevo_km * 1000
            ) + sufijo

            valor_verificado = struct.unpack_from(
                "<I",
                datos_modificados,
                direccion
            )[0]

            if valor_verificado != valor_esperado:

                errores += 1

        for direccion, sufijo in zip(
            direcciones_metros_modificar,
            sufijos
        ):

            valor_esperado = (
                nuevo_km * 1000
            ) + sufijo

            valor_verificado = struct.unpack_from(
                "<I",
                datos_modificados,
                direccion
            )[0]

            if valor_verificado != valor_esperado:

                errores += 1

        if errores == 0:

            st.success(
                "✓ Todos los reemplazos fueron "
                "verificados correctamente."
            )

        else:

            st.error(
                f"Se detectaron "
                f"{errores} errores "
                f"durante la verificación."
            )


        # ====================================================
        # DIFF ORIGINAL VS MODIFICADO
        # ====================================================

        st.subheader(
            "🔬 Diff BIN — antes de reparar checksum"
        )

        resultado_diff = diff_bytes(
            datos_originales,
            datos_modificados
        )

        if not resultado_diff["mismo_tamano"]:

            st.error(
                "Los archivos tienen tamaños diferentes."
            )

        elif resultado_diff["total_diferencias"] == 0:

            st.info(
                "Los archivos son idénticos."
            )

        else:

            st.info(
                f"Bytes distintos: "
                f"**{resultado_diff['total_diferencias']}** | "
                f"Rangos contiguos: "
                f"**{len(resultado_diff['rangos'])}**"
            )

            st.dataframe(
                resultado_diff["df"],
                use_container_width=True,
                hide_index=True
            )


        # ====================================================
        # CHECKSUM ORIGINAL
        # ====================================================

        st.subheader(
            "🔐 Checksum — BIN original"
        )

        try:

            verif_original = verificar_checksum_bytes(
                datos_originales
            )

            resumen_ori = (
                verif_original["resumen"]
            )

            col1, col2, col3, col4, col5 = st.columns(5)

            col1.metric(
                "Bloques",
                resumen_ori["bloques"]
            )

            col2.metric(
                "CS1 OK",
                f"{resumen_ori['cs1_ok']}/{resumen_ori['bloques']}"
            )

            col3.metric(
                "CS2 OK",
                resumen_ori["cs2_ok"]
            )

            col4.metric(
                "CS2 no aplica",
                resumen_ori["cs2_na"]
            )

            col5.metric(
                "CS2 inválidos",
                resumen_ori["cs2_bad"]
            )

            st.caption(
                f"Layout detectado: "
                f"{verif_original['layout']} | "
                f"CS1 score: "
                f"{verif_original['ratio_cs1'] * 100:.2f}%"
            )

        except Exception as e:

            verif_original = None

            st.warning(
                f"No fue posible detectar un layout CS1/CS2 "
                f"válido para este BIN: {e}"
            )


        # ====================================================
        # REPARACIÓN CS1 / CS2 CON REFERENCIA
        # ====================================================

        st.subheader(
            "🧮 Reparación automática CS1 / CS2"
        )

        st.info(
            "Se utiliza el BIN ORIGINAL como referencia. "
            "CS2 se corrige únicamente cuando el CS2 del original "
            "es genuino. Después se recalcula CS1."
        )

        try:

            datos_finales, info_reparacion = (
                reparar_ref_bytes(
                    datos_originales,
                    datos_modificados
                )
            )

            st.success(
                "✓ Reparación de checksum completada."
            )

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "CS1 recalculados",
                info_reparacion["cs1_fixed"]
            )

            col2.metric(
                "CS2 recalculados",
                info_reparacion["cs2_fixed"]
            )

            col3.metric(
                "CS2 protegidos",
                info_reparacion["cs2_protegidos"]
            )

            col4.metric(
                "Bloques tocados",
                len(
                    info_reparacion["bloques_tocados"]
                )
            )

            st.caption(
                f"Layout detectado: "
                f"{info_reparacion['layout']} | "
                f"CS1 score original: "
                f"{info_reparacion['ratio_cs1'] * 100:.2f}%"
            )

        except Exception as e:

            datos_finales = bytes(
                datos_modificados
            )

            st.error(
                f"Error durante la reparación de checksum: {e}"
            )


        # ====================================================
        # DIFF FINAL
        # ====================================================

        st.subheader(
            "🔬 Diff BIN — original vs BIN final"
        )

        diff_final = diff_bytes(
            datos_originales,
            datos_finales
        )

        if (
            diff_final["mismo_tamano"]
            and diff_final["total_diferencias"] is not None
        ):

            st.info(
                f"Bytes distintos respecto del original: "
                f"**{diff_final['total_diferencias']}** | "
                f"Rangos contiguos: "
                f"**{len(diff_final['rangos'])}**"
            )

            if not diff_final["df"].empty:

                st.dataframe(
                    diff_final["df"],
                    use_container_width=True,
                    hide_index=True
                )


        # ====================================================
        # VERIFICACIÓN FINAL
        # ====================================================

        st.subheader(
            "✅ Verificación final CS1 / CS2"
        )

        try:

            verif_final = verificar_checksum_bytes(
                datos_finales
            )

            resumen_final = (
                verif_final["resumen"]
            )

            col1, col2, col3, col4, col5, col6 = st.columns(6)

            col1.metric(
                "Bloques",
                resumen_final["bloques"]
            )

            col2.metric(
                "CS1 OK",
                f"{resumen_final['cs1_ok']}/{resumen_final['bloques']}"
            )

            col3.metric(
                "CS2 OK",
                resumen_final["cs2_ok"]
            )

            col4.metric(
                "CS2 no aplica",
                resumen_final["cs2_na"]
            )

            col5.metric(
                "CS2 inválidos",
                resumen_final["cs2_bad"]
            )

            col6.metric(
                "GLOBAL OK",
                f"{resumen_final['global_ok']}/{resumen_final['bloques']}"
            )

            st.caption(
                f"Layout final: "
                f"{verif_final['layout']} | "
                f"CS1 score final: "
                f"{verif_final['ratio_cs1'] * 100:.2f}%"
            )

            # -----------------------------------------------
            # MOSTRAR SOLO ERRORES
            # -----------------------------------------------

            df_final = verif_final["df"]

            if not df_final.empty:

                errores_finales = df_final[
                    ~df_final["OK"]
                ]

                if errores_finales.empty:

                    st.success(
                        "🎯 BIN FINAL: todos los bloques "
                        "analizados están correctos."
                    )

                else:

                    st.warning(
                        f"Quedan "
                        f"{len(errores_finales)} "
                        f"bloques con estado no OK."
                    )

                    st.dataframe(
                        errores_finales,
                        use_container_width=True,
                        hide_index=True
                    )

        except Exception as e:

            st.error(
                f"Error en la verificación final: {e}"
            )


        # ====================================================
        # DESCARGA BIN FINAL
        # ====================================================

        nombre_original = archivo.name

        if nombre_original.lower().endswith(
            ".bin"
        ):

            nombre_salida = (
                nombre_original[:-4]
                + "_MODIFICADO_CHECKSUM_OK.bin"
            )

        else:

            nombre_salida = (
                nombre_original
                + "_MODIFICADO_CHECKSUM_OK.bin"
            )

        st.subheader(
            "⬇️ Descargar BIN final"
        )

        st.download_button(
            label="⬇️ Descargar BIN MODIFICADO + CHECKSUM",
            data=datos_finales,
            file_name=nombre_salida,
            mime="application/octet-stream",
            type="primary"
        )


        # ====================================================
        # DESCARGA DEL REGISTRO CSV
        # ====================================================

        if not resultado_modificaciones.empty:

            csv_modificaciones = (
                resultado_modificaciones
                .to_csv(
                    index=False
                )
                .encode("utf-8")
            )

            st.download_button(
                label="⬇️ Descargar registro de modificaciones CSV",
                data=csv_modificaciones,
                file_name="registro_modificaciones.csv",
                mime="text/csv"
            )
