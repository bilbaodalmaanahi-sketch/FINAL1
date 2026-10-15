import streamlit as st
from pathlib import Path
import struct
import pandas as pd
import random


# ============================================================
# CONFIGURACIÓN
# ============================================================

st.set_page_config(
    page_title=" 🐒 Monky-I BIN Analyzer",
    page_icon="",
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

st.title("🐒 I-MONKY EEPROM LAB")

st.markdown(
    "### ECU / EEPROM Binary Memory Analyzer-Fiat"
)

st.caption("Concept by Ariel Calacaterra")

st.write(
    "Busca un valor exacto, realiza un barrido de las "
    "tres últimas cifras y busca equivalentes en metros "
    "dentro de todo el archivo BIN."
)



# ============================================================
# ARCHIVO BIN
# ============================================================

archivo_cargado = st.file_uploader(
    "Seleccionar archivo BIN",
    type=["bin"]
)


if archivo_cargado is None:

    st.info("Seleccione un archivo BIN para comenzar.")

    st.stop()


# ============================================================
# LEER ARCHIVO BIN
# ============================================================

datos = archivo_cargado.read()

st.success(
    f"Archivo cargado: {archivo_cargado.name} | "
    f"Tamaño: {len(datos):,} bytes"
)


# ============================================================
# VALORES
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    valor_buscado = st.number_input(
        "Valor KM a buscar",
        min_value=0,
        value=185971,
        step=1
    )

with col2:
    nuevov = st.number_input(
        "Nuevo valor KM",
        min_value=0,
        value=123,
        step=1
    )

with col3:
    margen_metros = st.number_input(
        "Margen de búsqueda en metros",
        min_value=0,
        value=1_000_000,
        step=1
    )
# ============================================================

margen_metros = 1_000_000

# ============================================================
# EQUIVALENTE ORIGINAL EN METROS
# ============================================================

valor_metros_objetivo = valor_buscado * 1000


limite_metros_inicio = (
    valor_metros_objetivo - margen_metros
)


limite_metros_fin = (
    valor_metros_objetivo + margen_metros
)


# ============================================================
# BOTÓN ANALIZAR
# ============================================================

analizar = st.button(
    "ANALIZAR BIN",
    type="primary",
    use_container_width=True,
    key="btn_analizar"
)


if analizar:

    # ========================================================
    # DATAFRAME BIG + LITTLE
    # ========================================================

    registros = []

    for direccion in range(0, len(datos) - 3, 4):

        bloque = datos[direccion:direccion + 4]


        # ====================================================
        # BIG-ENDIAN
        # ====================================================

        decimal_big = int.from_bytes(
            bloque,
            byteorder="big",
            signed=False
        )

        hex_big = f"{decimal_big:08X}"


        # ====================================================
        # LITTLE-ENDIAN
        # ====================================================

        decimal_little = int.from_bytes(
            bloque,
            byteorder="little",
            signed=False
        )

        hex_little = f"{decimal_little:08X}"


        # ====================================================
        # DATAFRAME
        # ====================================================

        registros.append({

            "Direccion":
                f"0x{direccion:04X}",

            "Direccion_decimal":
                direccion,

            "Bytes_BIN":
                bloque.hex(" ").upper(),

            "HEX_BIG":
                hex_big,

            "Decimal_BIG":
                decimal_big,

            "HEX_LITTLE":
                hex_little,

            "Decimal_LITTLE":
                decimal_little
        })


    df = pd.DataFrame(registros)


    # ========================================================
    # MOSTRAR DATAFRAME
    # ========================================================

    st.subheader("BIG-ENDIAN VS LITTLE-ENDIAN")

    st.dataframe(
        df,
        use_container_width=True,
        height=500
    )


    # ========================================================
    # BUSCAR VALOR EN BIG O LITTLE
    # ========================================================

    resultado = df[
        (df["Decimal_BIG"] == valor_buscado) |
        (df["Decimal_LITTLE"] == valor_buscado)
    ].copy()


    # ========================================================
    # MOSTRAR COINCIDENCIAS
    # ========================================================

    st.subheader(
        f"COINCIDENCIAS DE {valor_buscado:,} KM"
    )


    if not resultado.empty:

        st.success(
            f"Se encontraron {len(resultado)} coincidencia(s)."
        )

        st.dataframe(
            resultado[[
                "Direccion_decimal",
                "Direccion",
                "Bytes_BIN",
                "HEX_BIG",
                "Decimal_BIG",
                "HEX_LITTLE",
                "Decimal_LITTLE"
            ]],
            use_container_width=True
        )

    else:

        st.warning(
            f"No se encontró el valor {valor_buscado:,}."
        )


    st.write(
        f"**Coincidencias encontradas:** {len(resultado)}"
    )


    # ========================================================
    # CREAR DATAFRAME DE METROS
    # ========================================================

    filas_metros = []


    for direccion in range(0, len(datos) - 3, 4):

        bloque = datos[direccion:direccion + 4]


        # ====================================================
        # INTERPRETACIÓN BIG
        # ====================================================

        valor_big = int.from_bytes(
            bloque,
            byteorder="big",
            signed=False
        )


        # ====================================================
        # INTERPRETACIÓN LITTLE
        # ====================================================

        valor_little = int.from_bytes(
            bloque,
            byteorder="little",
            signed=False
        )


        # ====================================================
        # BUSCAR METROS EN BIG
        # ====================================================

        if (
            limite_metros_inicio
            <= valor_big
            <= limite_metros_fin
        ):

            filas_metros.append({

                "Direccion_decimal":
                    direccion,

                "Direccion":
                    f"0x{direccion:04X}",

                "Endian":
                    "BIG",

                "Metros":
                    valor_big,

                "HEX":
                    f"{valor_big:08X}",

                "Bytes_BIN":
                    bloque.hex(" ").upper()
            })


        # ====================================================
        # BUSCAR METROS EN LITTLE
        # ====================================================

        if (
            limite_metros_inicio
            <= valor_little
            <= limite_metros_fin
        ):

            if valor_little != valor_big:

                filas_metros.append({

                    "Direccion_decimal":
                        direccion,

                    "Direccion":
                        f"0x{direccion:04X}",

                    "Endian":
                        "LITTLE",

                    "Metros":
                        valor_little,

                    "HEX":
                        f"{valor_little:08X}",

                    "Bytes_BIN":
                        bloque.hex(" ").upper()
                })


    # ========================================================
    # DATAFRAME METROS
    # ========================================================

    df_metros = pd.DataFrame(
        filas_metros
    )


    # ========================================================
    # MOSTRAR DATAFRAME METROS
    # ========================================================

    st.subheader(
        "DATAFRAME DE VALORES EN METROS"
    )


    st.write(
        f"**Valor buscado:** {valor_buscado:,} KM"
    )

    st.write(
        f"**Equivalente metros:** "
        f"{valor_metros_objetivo:,}"
    )

    st.write(
        f"**Margen:** ±{margen_metros:,}"
    )

    st.write(
        f"**Rango:** "
        f"{limite_metros_inicio:,} → "
        f"{limite_metros_fin:,}"
    )

    st.write(
        f"**Coincidencias:** {len(df_metros)}"
    )


    if not df_metros.empty:

        st.dataframe(
            df_metros,
            use_container_width=True
        )

    else:

        st.warning(
            "No se encontraron valores en el rango."
        )


    # ========================================================
    # GUARDAR DATOS EN SESSION STATE
    # ========================================================

    st.session_state["datos"] = datos
    st.session_state["df"] = df
    st.session_state["resultado"] = resultado
    st.session_state["df_metros"] = df_metros
    st.session_state["valor_buscado"] = valor_buscado
    st.session_state["nuevov"] = nuevov


# ============================================================
# GENERAR BIN MODIFICADO
# ============================================================

if (
    "resultado" in st.session_state
    and "df" in st.session_state
    and "df_metros" in st.session_state
):

    st.divider()

    st.subheader("GENERAR BIN MODIFICADO")


    generar_bin = st.button(
        "GENERAR BIN MODIFICADO",
        type="primary",
        use_container_width=True,
        key="btn_generar_bin"
    )


    if generar_bin:

        datos = st.session_state["datos"]

        df = st.session_state["df"]

        resultado = st.session_state["resultado"]

        df_metros = st.session_state["df_metros"]

        valor_buscado = st.session_state["valor_buscado"]

        nuevov = st.session_state["nuevov"]


        # ====================================================
        # COPIA MODIFICABLE
        # ====================================================

        datos_modificados = bytearray(datos)


        # ====================================================
        # CAMBIAR LOS VALORES DE KM
        # ====================================================

        modificaciones_km = []


        for _, fila in resultado.iterrows():

            direccion = int(
                fila["Direccion_decimal"]
            )


            # ------------------------------------------------
            # Determinar dónde estaba el valor
            # ------------------------------------------------

            fila_original = df[
                df["Direccion_decimal"] == direccion
            ].iloc[0]


            if fila_original["Decimal_BIG"] == valor_buscado:

                # BIG-ENDIAN

                datos_modificados[
                    direccion:direccion + 4
                ] = int(nuevov).to_bytes(
                    4,
                    byteorder="big",
                    signed=False
                )


                modificaciones_km.append({
                    "Direccion": f"0x{direccion:04X}",
                    "Endian": "BIG",
                    "Original": valor_buscado,
                    "Nuevo": nuevov
                })


            elif fila_original["Decimal_LITTLE"] == valor_buscado:

                # LITTLE-ENDIAN

                datos_modificados[
                    direccion:direccion + 4
                ] = int(nuevov).to_bytes(
                    4,
                    byteorder="little",
                    signed=False
                )


                modificaciones_km.append({
                    "Direccion": f"0x{direccion:04X}",
                    "Endian": "LITTLE",
                    "Original": valor_buscado,
                    "Nuevo": nuevov
                })


        # ====================================================
        # GENERAR NUEVOS VALORES DE METROS
        # ====================================================

        if not df_metros.empty:

            df_metros = df_metros.copy()

            df_metros["Metros_Nuevo"] = df_metros[
                "Metros"
            ].apply(
                lambda x:
                    nuevov * 1000
                    + random.randint(0, 999)
            )


        # ====================================================
        # MOSTRAR NUEVOS VALORES
        # ====================================================

        st.subheader(
            "NUEVOS VALORES EN METROS"
        )


        if not df_metros.empty:

            st.dataframe(
                df_metros[[
                    "Direccion_decimal",
                    "Direccion",
                    "Endian",
                    "Metros",
                    "Metros_Nuevo",
                    "HEX",
                    "Bytes_BIN"
                ]],
                use_container_width=True
            )


        # ====================================================
        # ESCRIBIR NUEVOS VALORES DE METROS
        # ====================================================

        for _, fila in df_metros.iterrows():

            direccion = int(
                fila["Direccion_decimal"]
            )

            nuevo_metros = int(
                fila["Metros_Nuevo"]
            )

            endian = fila["Endian"]


            # ------------------------------------------------
            # BIG-ENDIAN
            # ------------------------------------------------

            if endian == "BIG":

                datos_modificados[
                    direccion:direccion + 4
                ] = nuevo_metros.to_bytes(
                    4,
                    byteorder="big",
                    signed=False
                )


            # ------------------------------------------------
            # LITTLE-ENDIAN
            # ------------------------------------------------

            elif endian == "LITTLE":

                datos_modificados[
                    direccion:direccion + 4
                ] = nuevo_metros.to_bytes(
                    4,
                    byteorder="little",
                    signed=False
                )


        # ====================================================
        # NOMBRE ARCHIVO SALIDA
        # ====================================================

        nombre_original = Path(
            archivo_cargado.name
        )

        archivo_salida = (
            nombre_original.stem
            + f"-MOD-{nuevov}KM.bin"
        )


        # ====================================================
        # MOSTRAR RESULTADO
        # ====================================================

        st.success(
            "BIN modificado generado correctamente."
        )


        col1, col2, col3 = st.columns(3)


        with col1:

            st.metric(
                "KM modificados",
                len(resultado)
            )


        with col2:

            st.metric(
                "Metros modificados",
                len(df_metros)
            )


        with col3:

            st.metric(
                "Total posiciones",
                len(resultado) + len(df_metros)
            )


        # ====================================================
        # TABLA DE MODIFICACIONES KM
        # ====================================================

        if modificaciones_km:

            st.subheader(
                "MODIFICACIONES DE KM"
            )

            st.dataframe(
                pd.DataFrame(modificaciones_km),
                use_container_width=True
            )


        # ====================================================
        # DESCARGAR BIN
        # ====================================================

        st.download_button(
            label="DESCARGAR BIN MODIFICADO",
            data=bytes(datos_modificados),
            file_name=archivo_salida,
            mime="application/octet-stream",
            use_container_width=True,
            key="download_bin"
        )
