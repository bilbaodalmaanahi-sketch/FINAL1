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
# CARGAR ARCHIVO
# ============================================================

archivo = st.file_uploader(
    "Seleccionar archivo BIN",
    type=["bin"]
)


# ============================================================
# KILOMETRAJE / VALOR EXACTO A BUSCAR
# ============================================================

ingrekk = st.number_input(
    "Kilometraje / valor exacto a buscar",
    min_value=0,
    value=None,
    placeholder="Ingrese el kilometraje",
    step=1
)


# ============================================================
# BÚSQUEDA INDEPENDIENTE EN METROS
# ============================================================

busqueda_metros_input = st.number_input(
    "Valor independiente a buscar en metros",
    min_value=0,
    value=None,
    placeholder="Ingrese el valor en metros",
    step=1
)


# ============================================================
# NUEVO KILOMETRAJE FIJO
# ============================================================

nuevo_km_input = st.number_input(
    "Nuevo kilometraje fijo",
    min_value=0,
    value=None,
    placeholder="Ingrese el nuevo kilometraje",
    step=1
)


# ============================================================
# MARGEN DE BÚSQUEDA EN METROS
# ============================================================

MARGEN_BUSQUEDA_METROS = 1_100_000

st.number_input(
    "Margen de búsqueda en metros",
    min_value=0,
    value=MARGEN_BUSQUEDA_METROS,
    step=100_000,
    disabled=True
)


# ============================================================
# TRES UMBRALES INDEPENDIENTES
# ============================================================

# 1) Umbral para búsqueda/modificación de KM
UMBRAL_KM = 100

# 2) Umbral para búsqueda/modificación de METROS INDEPENDIENTES
UMBRAL_METROS_INDEPENDIENTES = 100

# 3) Umbral para búsqueda/modificación de METROS
#    EQUIVALENTES AL KM
#
#    CORREGIDO: el valor original (100_000_000 m = 100.000 km)
#    era tan amplio que prácticamente cualquier valor del
#    rango de búsqueda (que ya está acotado por
#    MARGEN_BUSQUEDA_METROS) terminaba calificando como
#    "modificable", incluyendo datos que no son el odómetro.
#    Se deja como campo editable con un valor por defecto
#    razonable (equivalente al umbral de metros independientes).
UMBRAL_METROS_EQUIVALENTES = st.number_input(
    "Umbral de modificación para metros equivalentes al KM",
    min_value=1,
    value=100,
    step=10
)


st.info(
    f"Umbral KM: modificación si distancia absoluta < "
    f"**{UMBRAL_KM:,} km** | "
    f"Umbral metros independientes: modificación si distancia absoluta < "
    f"**{UMBRAL_METROS_INDEPENDIENTES:,} m** | "
    f"Umbral metros equivalentes: modificación si distancia absoluta < "
    f"**{UMBRAL_METROS_EQUIVALENTES:,} m**"
)


# ============================================================
# BOTÓN
# ============================================================

buscar = st.button(
    "🔎 Buscar y preparar modificación",
    type="primary"
)


# ============================================================
# PROCESAMIENTO
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
        # RANGO DE LAS 3 ÚLTIMAS CIFRAS - KM
        # ====================================================

        rango_inicio = (
            objetivo // 1000
        ) * 1000

        rango_fin = (
            rango_inicio + 999
        )


        # ====================================================
        # OBJETIVO EN METROS EQUIVALENTE AL KM
        # ====================================================

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


        # ====================================================
        # RANGO DE LAS 3 ÚLTIMAS CIFRAS -
        # METROS INDEPENDIENTE
        # ====================================================

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


        # ====================================================
        # DIRECCIONES PARA MODIFICACIÓN
        # ====================================================

        direcciones_km = []

        direcciones_metros_independientes = []

        direcciones_metros_modificar = []


        # ====================================================
        # CONTROL DE DIRECCIONES YA UTILIZADAS
        #
        # IMPORTANTE:
        #
        # Una dirección solamente puede modificarse UNA VEZ.
        #
        # PRIORIDAD:
        #
        # 1. KM
        # 2. METROS INDEPENDIENTES
        # 3. METROS EQUIVALENTES AL KM
        # ====================================================

        direcciones_usadas = set()


        # ====================================================
        # BARRIDO COMPLETO DEL BIN
        #
        # CORREGIDO: el barrido original avanzaba de a 1 byte
        # ("range(0, tamaño - 3)"), lo que arma un entero de
        # 32 bits mezclando bytes de DOS campos vecinos en
        # cada posición no alineada. Todos los campos reales
        # de estas EEPROM (odómetro incluido) están alineados
        # a 4 bytes, así que ese barrido byte-a-byte generaba
        # "valores" que no corresponden a ningún dato real y
        # que, por pura coincidencia numérica, a veces caían
        # dentro del rango buscado -> de ahí los cambios en
        # direcciones con "dato desconocido".
        #
        # Ahora se avanza de a 4 bytes (alineado), que es la
        # única alineación válida para estos campos.
        # ====================================================

        PASO_ALINEACION = 4

        for direccion in range(
            0,
            tamaño - 3,
            PASO_ALINEACION
        ):

            valor = struct.unpack_from(
                "<I",
                datos_originales,
                direccion
            )[0]


            bytes_valor = (
                datos_originales[
                    direccion:direccion + 4
                ]
            )


            # =================================================
            # 1. BÚSQUEDA DEL RANGO DE KM
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

                elif distancia_absoluta < UMBRAL_KM:

                    tipo_coincidencia = (
                        f"🟡 CERCANO < {UMBRAL_KM} KM"
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


                # ---------------------------------------------
                # GUARDAR KM PARA MODIFICAR
                #
                # PRIORIDAD 1
                # ---------------------------------------------

                if (
                    distancia_absoluta < UMBRAL_KM
                    and direccion not in direcciones_usadas
                ):

                    direcciones_km.append(
                        direccion
                    )

                    direcciones_usadas.add(
                        direccion
                    )


            # =================================================
            # 2. BÚSQUEDA INDEPENDIENTE EN METROS
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


                # ---------------------------------------------
                # DETERMINAR SI REALMENTE SE VA A MODIFICAR
                # ---------------------------------------------

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

                        modifica_ind = "NO - YA RESERVADA"

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


                # ---------------------------------------------
                # GUARDAR SOLO SI:
                #
                # 1. CUMPLE UMBRAL
                # 2. LA DIRECCIÓN NO FUE USADA POR KM
                # ---------------------------------------------

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
            # 3. BÚSQUEDA POR METROS EQUIVALENTES AL KM
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


                # ---------------------------------------------
                # DETERMINAR SI CUMPLE UMBRAL
                # ---------------------------------------------

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


                # ---------------------------------------------
                # GUARDAR PARA MODIFICAR
                #
                # SOLO SI:
                #
                # 1. CUMPLE UMBRAL
                # 2. NO FUE USADA POR KM
                # 3. NO FUE USADA POR METROS INDEPENDIENTES
                # ---------------------------------------------

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
        # DATAFRAME BARRIDO KM
        # ====================================================

        resultado_barrido = pd.DataFrame(
            resultados_barrido
        )


        # ====================================================
        # DATAFRAME METROS INDEPENDIENTES
        # ====================================================

        resultado_metros_independientes = pd.DataFrame(
            resultados_metros_independientes
        )


        # ====================================================
        # DATAFRAME METROS EQUIVALENTES
        # ====================================================

        resultado_metros = pd.DataFrame(
            resultados_metros
        )


        # ====================================================
        # RESULTADOS DEL BARRIDO KM
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


            # =================================================
            # VALORES EXACTOS
            # =================================================

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


            # =================================================
            # VALORES QUE SERÁN MODIFICADOS
            # =================================================

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


            # =================================================
            # RESUMEN
            # =================================================

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
        # BÚSQUEDA INDEPENDIENTE EN METROS
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


            # =================================================
            # EXACTO METROS INDEPENDIENTE
            # =================================================

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


            # =================================================
            # CERCANOS METROS INDEPENDIENTES
            # =================================================

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
        # RESULTADOS METROS EQUIVALENTES AL KM
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


            # =================================================
            # VALORES DE METROS QUE SE MODIFICARÁN
            # =================================================

            metros_a_modificar = resultado_metros[
                resultado_metros[
                    "Modifica"
                ] == "SÍ"
            ]


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


            # =================================================
            # VALOR MÁS CERCANO
            # =================================================

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
        # MODIFICACIÓN
        # ====================================================

        st.subheader(
            "🛠️ Modificación de valores"
        )


        st.write(
            f"Valor original exacto KM: "
            f"**{objetivo:,} km**"
        )


        st.write(
            f"Valor independiente en metros: "
            f"**{objetivo_metros_independiente:,} m**"
        )


        st.write(
            f"Nuevo kilometraje: "
            f"**{nuevo_km:,} km**"
        )


        st.write(
            f"Nuevo valor base en metros: "
            f"**{nuevo_km * 1000:,} m**"
        )


        st.write(
            f"Umbral KM: "
            f"**< {UMBRAL_KM:,} km**"
        )


        st.write(
            f"Umbral metros independientes: "
            f"**< {UMBRAL_METROS_INDEPENDIENTES:,} m**"
        )


        st.write(
            f"Umbral metros equivalentes: "
            f"**< {UMBRAL_METROS_EQUIVALENTES:,} m**"
        )


        # ====================================================
        # CANTIDADES
        # ====================================================

        cantidad_km = len(
            direcciones_km
        )


        cantidad_metros_independientes = len(
            direcciones_metros_independientes
        )


        cantidad_metros_equivalentes = len(
            direcciones_metros_modificar
        )


        # ====================================================
        # TOTAL DE DIRECCIONES ÚNICAS
        # ====================================================

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
        # VERIFICACIÓN DE NO SOLAPAMIENTO
        # ====================================================

        interseccion_km_ind = (
            set(direcciones_km)
            & set(direcciones_metros_independientes)
        )


        interseccion_km_equiv = (
            set(direcciones_km)
            & set(direcciones_metros_modificar)
        )


        interseccion_ind_equiv = (
            set(direcciones_metros_independientes)
            & set(direcciones_metros_modificar)
        )


        total_intersecciones = (
            len(interseccion_km_ind)
            + len(interseccion_km_equiv)
            + len(interseccion_ind_equiv)
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

        if total_modificaciones == 0:

            st.warning(
                "No se encontraron valores "
                "para modificar."
            )


        else:

            modificaciones = []


            # =================================================
            # MODIFICAR VALORES KM
            # =================================================

            for direccion in direcciones_km:

                valor_anterior = (
                    struct.unpack_from(
                        "<I",
                        datos_originales,
                        direccion
                    )[0]
                )


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


            # =================================================
            # GENERAR SUFIJOS METROS INDEPENDIENTES
            # =================================================

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


            # =================================================
            # MODIFICAR METROS INDEPENDIENTES
            # =================================================

            for direccion, sufijo in zip(
                direcciones_metros_independientes,
                sufijos_independientes
            ):

                valor_anterior = (
                    struct.unpack_from(
                        "<I",
                        datos_originales,
                        direccion
                    )[0]
                )


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


            # =================================================
            # GENERAR SUFIJOS METROS EQUIVALENTES
            # =================================================

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


            # =================================================
            # MODIFICAR METROS EQUIVALENTES AL KM
            # =================================================

            for direccion, sufijo in zip(
                direcciones_metros_modificar,
                sufijos
            ):

                valor_anterior = (
                    struct.unpack_from(
                        "<I",
                        datos_originales,
                        direccion
                    )[0]
                )


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


            # =================================================
            # DATAFRAME DE MODIFICACIONES
            # =================================================

            resultado_modificaciones = pd.DataFrame(
                modificaciones
            )


            # =================================================
            # SEGURIDAD EXTRA:
            # VERIFICAR DIRECCIONES ÚNICAS EN EL REGISTRO
            # =================================================

            direcciones_registro = (
                resultado_modificaciones[
                    "Dirección"
                ].tolist()
            )


            cantidad_direcciones_registro = (
                len(direcciones_registro)
            )


            cantidad_direcciones_unicas_registro = (
                len(set(direcciones_registro))
            )


            # =================================================
            # MOSTRAR MODIFICACIONES
            # =================================================

            st.subheader(
                "📋 Registro de modificaciones"
            )


            st.success(
                f"Se realizaron "
                f"{len(modificaciones)} "
                f"modificaciones sobre "
                f"{cantidad_direcciones_unicas_registro} "
                f"direcciones únicas."
            )


            if (
                cantidad_direcciones_registro
                == cantidad_direcciones_unicas_registro
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


            # =================================================
            # VERIFICACIÓN
            # =================================================

            st.subheader(
                "✓ Verificación"
            )


            errores = 0


            # =================================================
            # VERIFICAR KM
            # =================================================

            for direccion in direcciones_km:

                valor_verificado = (
                    struct.unpack_from(
                        "<I",
                        datos_modificados,
                        direccion
                    )[0]
                )


                if (
                    valor_verificado
                    != nuevo_km
                ):

                    errores += 1


            # =================================================
            # VERIFICAR METROS INDEPENDIENTES
            # =================================================

            for direccion, sufijo in zip(
                direcciones_metros_independientes,
                sufijos_independientes
            ):

                valor_esperado = (
                    nuevo_km * 1000
                ) + sufijo


                valor_verificado = (
                    struct.unpack_from(
                        "<I",
                        datos_modificados,
                        direccion
                    )[0]
                )


                if (
                    valor_verificado
                    != valor_esperado
                ):

                    errores += 1


            # =================================================
            # VERIFICAR METROS EQUIVALENTES
            # =================================================

            for direccion, sufijo in zip(
                direcciones_metros_modificar,
                sufijos
            ):

                valor_esperado = (
                    nuevo_km * 1000
                ) + sufijo


                valor_verificado = (
                    struct.unpack_from(
                        "<I",
                        datos_modificados,
                        direccion
                    )[0]
                )


                if (
                    valor_verificado
                    != valor_esperado
                ):

                    errores += 1


            # =================================================
            # RESULTADO DE VERIFICACIÓN
            # =================================================

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


            # =================================================
            # NOMBRE DEL ARCHIVO
            # =================================================

            nombre_original = (
                archivo.name
            )


            if nombre_original.lower().endswith(
                ".bin"
            ):

                nombre_salida = (
                    nombre_original[:-4]
                    + "_MODIFICADO.bin"
                )

            else:

                nombre_salida = (
                    nombre_original
                    + "_MODIFICADO.bin"
                )


            # =================================================
            # DESCARGAR BIN MODIFICADO
            # =================================================

            st.subheader(
                "⬇️ Descargar BIN modificado"
            )


            st.download_button(
                label="⬇️ Descargar BIN MODIFICADO",
                data=bytes(
                    datos_modificados
                ),
                file_name=nombre_salida,
                mime="application/octet-stream",
                type="primary"
            )


            # =================================================
            # DESCARGAR CSV
            # =================================================

            csv_modificaciones = (
                resultado_modificaciones
                .to_csv(
                    index=False
                )
                .encode("utf-8")
            )


            st.download_button(
                label="⬇️ Descargar registro de modificaciones",
                data=csv_modificaciones,
                file_name="registro_modificaciones.csv",
                mime="text/csv"
            )
