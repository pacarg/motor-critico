import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf
import time

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA
# ==========================================

st.set_page_config(
    page_title="Análisis Crítico | Forense", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ESTILO VISUAL (MEJORADO CON ALTO CONTRASTE)
# ==========================================

estilo_css = """
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* --- PALETA DE COLORES --- */
    :root {
        --fondo-sidebar: #020617;      /* Negro azulado profundo */
        --fondo-body: #1e293b;         /* Azul grisáceo técnico */
        --fondo-input: #f8fafc;        /* Blanco casi puro */
        --texto-input: #0f172a;        /* Texto oscuro */
        --borde-input: #94a3b8;        /* Borde gris */
        --acento: #38bdf8;             /* Cyan brillante */
        --texto-general: #f1f5f9;      /* Blanco suave */
    }

    .stApp {
        background-color: var(--fondo-body);
        color: var(--texto-general);
        font-family: 'Inter', sans-serif;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--fondo-sidebar);
        border-right: 1px solid #334155;
    }
    
    h1, h2, h3 { color: #ffffff !important; font-weight: 700; }
    p, li, label, .stMarkdown { color: #e2e8f0; }

    /* INPUTS Y CAJAS DE TEXTO */
    .stTextArea textarea {
        background-color: var(--fondo-input) !important;
        color: var(--texto-input) !important;
        border: 2px solid var(--borde-input);
        border-radius: 6px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        caret-color: #ef4444;
    }
    .stTextArea textarea:focus {
        border-color: var(--acento);
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    }
    .stTextArea label {
        color: #cbd5e1 !important;
        font-weight: 600;
    }
    
    /* SELECTBOX */
    div[data-baseweb="select"] > div {
        background-color: var(--fondo-input) !important;
        color: var(--texto-input) !important;
        border: 1px solid var(--borde-input);
    }
    div[data-baseweb="select"] span {
        color: var(--texto-input) !important; 
    }

    /* BOTÓN EJECUTAR */
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: bold;
        text-transform: uppercase;
        width: 100%;
        border-radius: 6px;
        border: 1px solid #7dd3fc;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8, #0ea5e9);
        transform: translateY(-2px);
    }

    /* MÉTRICAS */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: var(--acento) !important;
        text-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    /* --- NUEVO ESTILO PARA EXPANDER (EVIDENCIA) --- */
    .streamlit-expanderHeader {
        background-color: #1e293b !important; 
        color: var(--acento) !important;       /* Título en Cyan */
        border: 2px solid var(--acento) !important; /* Borde Cyan para resaltar */
        border-radius: 8px;
        font-weight: 700;
        font-size: 1.1rem !important;
    }
    /* El contenido interior del expander */
    div[data-testid="stExpanderDetails"] {
        background-color: #020617; /* Fondo más oscuro para contraste interno */
        border: 2px solid var(--acento);
        border-top: none;
        border-bottom-left-radius: 8px;
        border-bottom-right-radius: 8px;
        padding: 20px;
    }
    
    /* CITA TEXTUAL MEJORADA */
    blockquote {
        border-left: 5px solid var(--acento);
        padding-left: 20px;
        margin-left: 0;
        background-color: rgba(56, 189, 248, 0.15); /* Un poco más brillante */
        padding: 15px;
        border-radius: 4px;
        font-style: italic;
        color: #ffffff !important; /* Texto BLANCO PURO para máxima lectura */
        font-size: 1.1rem;
    }

    .info-box {
        background-color: rgba(15, 23, 42, 0.8);
        border-left: 4px solid var(--acento);
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        border: 1px solid #334155;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# ==========================================
# 3. CONEXIÓN Y SEGURIDAD
# ==========================================

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR CRÍTICO: No se detectó la API KEY en los Secrets.")
    st.stop()

# ==========================================
# 4. CEREBRO (LECTURA DE PDFs)
# ==========================================

@st.cache_resource
def cargar_biblioteca_desde_pdfs(carpeta="datos"):
    texto_total = ""