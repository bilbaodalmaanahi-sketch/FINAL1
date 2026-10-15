
import streamlit as st

st.set_page_config(
    page_title="🐒 MONKY TOOLS | BIN LAB",
    page_icon="🐒",
    layout="wide"
)

# =========================
# ESTILO VISUAL
# =========================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@400;500;600;700&display=swap');

.stApp {
    background:
        radial-gradient(ellipse at 15% 10%, #251044 0%, transparent 38%),
        radial-gradient(ellipse at 90% 65%, #073a32 0%, transparent 35%),
        #080910;
    color: #eeeeff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    max-width: 1250px;
}

#MainMenu, footer {
    visibility: hidden;
}

/* Hero */
.hero {
    position: relative;
    overflow: hidden;
    padding: 48px 35px;
    border: 1px solid #6639a8;
    border-radius: 25px;
    background: linear-gradient(125deg,
        rgba(37, 17, 66, .96),
        rgba(10, 15, 29, .97) 58%,
        rgba(0, 72, 58, .75));
    box-shadow: 0 0 35px rgba(141, 69, 255, .13),
                inset 0 0 35px rgba(141, 69, 255, .05);
}

.eyebrow {
    font-family: 'Orbitron', sans-serif;
    font-size: 11px;
    letter-spacing: 4px;
    color: #42ffd2;
    margin-bottom: 18px;
}

.hero-title {
    font-family: 'Orbitron', sans-serif;
    font-weight: 900;
    font-size: clamp(34px, 5.5vw, 65px);
    line-height: 1.15;
    letter-spacing: -2px;
    margin: 0;
    color: #ffffff;
}

.hero-title span {
    color: #c18aff;
    text-shadow: 0 0 22px rgba(181, 112, 255, .5);
}

.hero-subtitle {
    font-family: 'Rajdhani', sans-serif;
    font-size: 21px;
    color: #c7c6df;
    margin-top: 20px;
    max-width: 690px;
    line-height: 1.4;
}

.hero-tag {
    display: inline-block;
    margin-top: 24px;
    padding: 8px 13px;
    border: 1px solid #42ffd2;
    border-radius: 6px;
    color: #42ffd2;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 2px;
}

/* Secciones */
.section-label {
    font-family: 'Orbitron', sans-serif;
    font-size: 12px;
    color: #b78aff;
    letter-spacing: 3px;
    margin: 36px 0 16px;
}

.section-heading {
    font-family: 'Orbitron', sans-serif;
    font-size: 23px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 7px;
}

.section-description {
    font-family: 'Rajdhani', sans-serif;
    font-size: 18px;
    color: #9999b8;
    margin-bottom: 22px;
}

/* Tarjetas */
.tool-card {
    background: linear-gradient(145deg,
        rgba(28, 27, 48, .96),
        rgba(13, 16, 27, .98));
    border: 1px solid #34304d;
    border-radius: 17px;
    padding: 23px;
    min-height: 205px;
    margin-bottom: 13px;
    transition: all .25s ease;
}

.tool-card:hover {
    border-color: #a66cff;
    box-shadow: 0 0 22px rgba(166, 108, 255, .15);
    transform: translateY(-3px);
}

.tool-icon {
    font-size: 34px;
    margin-bottom: 15px;
}

.tool-title {
    font-family: 'Orbitron', sans-serif;
    font-size: 14px;
    font-weight: 700;
    color: #f4efff;
    margin-bottom: 11px;
}

.tool-description {
    font-family: 'Rajdhani', sans-serif;
    font-size: 17px;
    line-height: 1.35;
    color: #aaaac4;
}

.tool-number {
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    color: #42ffd2;
    letter-spacing: 2px;
    margin-bottom: 13px;
}

.stButton > button {
    width: 100%;
    min-height: 43px;
    background: linear-gradient(90deg, #7d35d6, #5426a5);
    color: white;
    border: 1px solid #b68aff;
    border-radius: 9px;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 1px;
    transition: all .2s ease;
}

.stButton > button:hover {
    background: linear-gradient(90deg, #9a50f4, #6538c4);
    border-color: #42ffd2;
    color: white;
    box-shadow: 0 0 18px rgba(151, 83, 255, .35);
}

/* Pie */
.footer {
    text-align: center;
    margin-top: 45px;
    padding: 24px 10px;
    border-top: 1px solid #29243c;
    font-family: 'Orbitron', sans-serif;
    font-size: 10px;
    letter-spacing: 2px;
    color: #77748f;
}

.footer span {
    color: #42ffd2;
}
</style>
""", unsafe_allow_html=True)


# =========================
# PORTADA
# =========================
st.markdown("""
<div class="hero">
    <div class="eyebrow">◈ DIGITAL FORENSICS · ENGINEERING LAB</div>
    <h1 class="hero-title">MONKY<br><span>TOOLS_</span></h1>
    <div class="hero-subtitle">
        Entrá al laboratorio. Explorá archivos BIN, analizá datos,
        detectá errores y llevá tus herramientas al siguiente nivel.
    </div>
    <div class="hero-tag">SYSTEM ONLINE // SELECT YOUR TOOL</div>
</div>
""", unsafe_allow_html=True)


# =========================
# HERRAMIENTAS
# =========================
st.markdown("""
<div class="section-label">/// 01 — TOOLKIT</div>
<div class="section-heading">Elegí tu próximo movimiento.</div>
<div class="section-description">
    Cinco herramientas. Un solo centro de operaciones.
</div>
""", unsafe_allow_html=True)


def tool_card(number, icon, title, description, button_label, page):
    with st.container():
        st.markdown(f"""
        <div class="tool-card">
            <div class="tool-number">{number} // MODULE</div>
            <div class="tool-icon">{icon}</div>
            <div class="tool-title">{title}</div>
            <div class="tool-description">{description}</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(button_label, key=f"btn_{number}",
                     use_container_width=True):
            st.switch_page(page)


col1, col2 = st.columns(2, gap="large")

with col1:
    tool_card(
        "01", "🐒", "MONKY BIN ANALYZER",
        "Tu centro de análisis para explorar y trabajar con archivos BIN.",
        "↗ INICIAR ANALIZADOR",
        "pages/mon1.py"
    )

    tool_card(
        "03", "🐒", "BIN SEARCH ENGINE",
        "Buscá información y explorá los datos de tus archivos.",
        "↗ ABRIR BUSCADOR",
        "pages/Buscador.py"
    )

    tool_card(
        "05", "🐒","FIAT MODULE",
        "Herramientas específicas para trabajar con archivos Fiat.",
        "↗ ABRIR MÓDULO FIAT",
        "pages/fiat.py"
    )

with col2:
    tool_card(
        "02","🐒","CRC16 / XMODEM",
        "Analizá y repará CRC16/XMODEM para archivos BIN-BMW.",
        "↗ INICIAR CRC LAB",
        "pages/app1.py"
    )

    tool_card(
        "04", "🐒","RENAULT MODULE",
        "Accedé al módulo de análisis orientado a archivos Renault.",
        "↗ ABRIR MÓDULO RENAULT",
        "pages/rena.py"
    )


# =========================
# PIE DE PAGINA
# =========================
st.markdown("""
<div class="footer">
    MONKY TOOLS <span>///</span> BUILT FOR THE CURIOUS
    <br><br>
    BIN LAB · DIGITAL WORKSPACE · VERSION 1.0
</div>
""", unsafe_allow_html=True)
