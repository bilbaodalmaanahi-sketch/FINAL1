
import streamlit as st
import struct
import pandas as pd
import random


import streamlit as st

st.set_page_config(
    page_title="Mis aplicaciones",
    page_icon="🧰",
    layout="wide"
)

pagina = st.navigation([
    st.Page(
        "moni1.py",
        title="Monky BIN Analyzer",
        icon="🐒"
    ),
    st.Page(
        "app1.py",
        title="Segunda aplicación",
        icon="📊"
    )
])

pagina.run()
