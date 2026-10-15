
import streamlit as st

st.set_page_config(
    page_title="Monky Tools",
    page_icon="🐒",
    layout="wide"
)

inicio = st.Page(
    "inicio.py",
    title="Inicio",
    icon="🏠",
    default=True
)

monky = st.Page(
    "pages/mon1.py",
    title="Monky BIN Analyzer",
    icon="🐒"
)

crc16 = st.Page(
    "pages/app1.py",
    title="Analizador y reparador CRC16/XMODEM",
    icon="🔧"
)

buscador = st.Page(
    "pages/Buscador.py",
    title="Monky BIN Analyzer - Buscador",
    icon="🔎"
)

renault = st.Page(
    "pages/rena.py",
    title="Monky BIN Analyzer - Renault",
    icon="🚗"
)

fiat = st.Page(
    "pages/fiat.py",
    title="Monky BIN Analyzer - Fiat",
    icon="🚘"
)

pagina = st.navigation([
    inicio,
    monky,
    crc16,
    buscador,
    renault,
    fiat
])

pagina.run()
