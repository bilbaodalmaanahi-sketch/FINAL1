
import streamlit as st
import struct
import pandas as pd
import random


import streamlit as st

import streamlit as st

st.set_page_config(
    page_title="Mis aplicaciones",
    page_icon="🧰",
    layout="wide"
)

pagina = st.navigation([
    st.Page(
        "pages/mon1.py",
        title="Monky BIN Analyzer",
        icon="🐒"
    ),
    st.Page(
        "pages/app1.py",
        title="Analizador y reparador de CRC16/XMODEM para archivos BIN-BMW",
        icon="🐒"
    ),
    
    st.Page(
        "pages/Buscador.py",
        title="Monky BIN Analyzer-Buscador",
        icon="🐒"
    ),
    
    
    st.Page(
        "pages/fiat.py",
        title="Monky BIN Analyzer-Renault",
        icon="🐒"
    ),
    st.Page(
        "pages/rena.py",
        title="Monky BIN Analyzer-fiat",
        icon="🐒"
    )
])

pagina.run()
