import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf
import time  # Necesario para las animaciones de carga

# ==========================================
# 1. CONFIGURACIÓN BÁSICA Y ESTÉTICA (NUEVO DISEÑO)
# ==========================================

st.set_page_config(
    page_title="Motor Crítico | Forense", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS ESTILO "TECH PRO" ---
st.markdown("""
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* FONDO Y TEXTO GENERAL */
    .stApp {
        background-color: #0E1117;
        color: #Cdd6f4;
        font-family: 'Inter', sans-serif;
    }

    /* BARRA LATERAL */
    section[data-testid="stSidebar"] {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }

    /* INPUTS DE TEXTO */
    .stTextArea textarea {
        background-color: #0d1117;
        color: #e6edf3;
        border: 1px solid #30363d;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextArea textarea:focus {
        border-color: #58a6ff;
        box-shadow: 0 0 10px rgba(88, 166, 255, 0.2);
    }

    /* BOTÓN EJECUTAR (CYBERPUNK) */
    div.stButton > button {
        background: linear-gradient(90deg, #1f6feb, #1c4587);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: bold;
        letter-spacing: 1px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #3b8df5, #2659a3);
        box-shadow: 0 0 15px rgba(31, 111, 235, 0.5);
        transform: translateY(-2px);
    }

    /* CAJAS DE ALERTA Y MÉTRICAS */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: #58a6ff !important;
    }
    
    /* AVISO IMPORTANTE PERSONALIZADO */
    .info-box {
        background-color: rgba(56, 139, 253, 0.1);
        border-left: 3px solid #388bfd;
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        font-size: 0.9rem;
        color: #c9d1d9;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. CONEXIÓN Y SEGURIDAD (INTACTO)
# ==========================================

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR CRÍTICO: No se detectó la API KEY en los Secrets.")
    st.stop()

# ==========================================
# 3. CEREBRO (LECTURA DE PDFs) (INTACTO)
# ==========================================

@st.cache_resource
def cargar_biblioteca_desde_pdfs(carpeta="datos"):
    texto_total = ""
    archivos_leidos = []
    
    if not os.path.exists(carpeta):
        return "ADVERTENCIA: Carpeta 'datos' no encontrada.", []

    archivos = [f for f in os.listdir(carpeta) if f.endswith('.pdf')]
    
    for archivo in archivos:
        try:
            ruta_pdf = os.path.join(carpeta, archivo)
            reader = pypdf.PdfReader(ruta_pdf)
            for page in reader.pages:
                texto_total += page.extract_text() + "\n"
            
            texto_total += f"\n--- FIN DOCUMENTO: {archivo} ---\n"
            archivos_leidos.append(archivo)
        except Exception as e:
            pass 

    return texto_total, archivos_leidos

BIBLIOTECA_CONOCIMIENTO, LISTA_ARCHIVOS = cargar_biblioteca_desde_pdfs()

# ==========================================
# 4. CONFIGURACIÓN DEL MODELO IA (INTACTO)
# ==========================================

MODEL_NAME = "models/gemini-flash-latest"

SYSTEM_INSTRUCTION = f"""
Eres el "Motor de Desarticulación Lógica".
Tu tarea es analizar argumentos sobre IA basándote en estos documentos: {LISTA_ARCHIVOS}.
Debes responder SIEMPRE con este esquema JSON exacto (sin markdown extra):
{{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Nivel_Alarmismo": (Número entero 0-100),
  "Punto_de_Dolor": "Texto breve identificando la emoción...",
  "Riesgo_Real": "Texto breve explicando el problema técnico real...",
  "Desarticulacion": "Texto breve con el argumento lógico...",
  "Cita": "Cita textual breve de los documentos...",
  "Autor_Cita": "Nombre del archivo fuente"
}}