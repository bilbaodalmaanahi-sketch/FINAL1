import streamlit as st

st.title("🐒 Monky Tools")
st.subheader("Plataforma de análisis y reparación de archivos BIN")

st.write(
    "Bienvenido a Monky Tools. Seleccioná una herramienta "
    "del menú lateral para comenzar."
)

st.divider()

st.subheader("Herramientas disponibles")

st.markdown("""
- 🐒 Monky BIN Analyzer
- 🔧 Analizador y reparador CRC16/XMODEM
- 🔎 Buscador BIN
- 🚗 Herramientas Renault
- 🚘 Herramientas Fiat
""")
