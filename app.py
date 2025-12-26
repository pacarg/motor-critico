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
    page_title="Motor Crítico | Forense", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# ==========================================
# 2. ESTILO VISUAL "HIGH CONTRAST TECH"
# ==========================================
# Hemos ajustado los colores para máxima legibilidad (Blanco sobre Azul Noche)

st.markdown("""
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* --- PALETA DE COLORES --- */
    :root {
        --fondo-principal: #0f172a;      /* Azul noche muy oscuro (Slate 900) */
        --fondo-secundario: #1e293b;     /* Azul grisáceo (Slate 800) */
        --texto-principal: #f8fafc;      /* Blanco casi puro */
        --texto-secundario: #94a3b8;     /* Gris claro para subtítulos */
        --acento-primario: #38bdf8;      /* Azul cielo brillante (Cyan) */
        --borde: #334155;                /* Borde sutil */
    }

    /* FONDO GENERAL */
    .stApp {
        background-color: var(--fondo-principal);
        color: var(--texto-principal);
        font-family: 'Inter', sans-serif;
    }

    /* BARRA LATERAL */
    section[data-testid="stSidebar"] {
        background-color: #020617; /* Casi negro */
        border-right: 1px solid var(--borde);
    }
    
    /* TÍTULOS */
    h1, h2, h3 {
        color: #ffffff !important;
        font-weight: 700;
    }
    
    p, li, label {
        color: #e2e8f0 !important; /* Texto muy legible */
        font-size: 1rem;
    }

    /* INPUTS DE TEXTO (ÁREA DE ESCRITURA) */
    .stTextArea textarea {
        background-color: var(--fondo-secundario);
        color: #ffffff;
        border: 1px solid var(--borde);
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px; /* Letra un poco más grande */
    }
    .stTextArea textarea:focus {
        border-color: var(--acento-primario);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }

    /* BOTÓN EJECUTAR (MÁS BRILLANTE) */
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7); /* Azul brillante */
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: bold;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        transition: all 0.3s ease;
        width: 100%;
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8, #0ea5e9);
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        transform: translateY(-2px);
    }

    /* MÉTRICAS (Números grandes) */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: var(--acento-primario) !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: var(--texto-secundario) !important;
    }
    
    /* CAJAS DE ALERTA PERSONALIZADAS */
    .info-box {
        background-color: rgba(14, 165, 233, 0.1);
        border-left: 4px solid var(--acento-primario);
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        color: var(--texto-principal);
    }
    
    /* EXPANDER (ACORDEÓN) */
    .streamlit-expanderHeader {
        background-color: var(--fondo-secundario);
        color: var(--texto-principal) !important;
        border-radius: 4px;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

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
    archivos_leidos = []
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        return "ADVERTENCIA: Carpeta 'datos' creada (vacía).", []

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
# 5. CONFIGURACIÓN DEL MODELO IA
# ==========================================

MODEL_NAME = "models/gemini-flash-latest"

PROMPT_BASE = """
Eres el "Motor de Desarticulación Lógica".
Tu tarea es analizar argumentos sobre IA basándote exclusivamente en la documentacion provista.
Debes responder SIEMPRE con este esquema JSON exacto (sin markdown extra):
{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Nivel_Alarmismo": (Número entero 0-100),
  "Punto_de_Dolor": "Texto breve identificando la emoción subyacente...",
  "Riesgo_Real": "Texto breve explicando el problema técnico real...",
  "Desarticulacion": "Texto breve con el argumento lógico y filosófico...",
  "Cita": "Cita textual breve extraída de los documentos...",
  "Autor_Cita": "Nombre del archivo fuente de donde salió la cita"
}
"""

SYSTEM_INSTRUCTION = f"""
{PROMPT_BASE}

LISTA DE FUENTES:
{LISTA_ARCHIVOS}

CONTEXTO DOCUMENTAL COMPLETO:
{BIBLIOTECA_CONOCIMIENTO}
"""

generation_config = {
    "temperature": 0.5,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json",
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 6. INTERFAZ VISUAL (FRONTEND CORREGIDO)
# ==========================================

# --- BARRA LATERAL ---
with st.sidebar:
    
    # 1. RECUPERACIÓN DEL LOGO
    # Buscamos logo.png. Si no está, mostramos un emoji grande.
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("# 🛡️") # Placeholder si no encuentra la imagen
    
    st.markdown("### 🎛️ Panel de Control")
    
    # Widget LED de Estado (Mejorado visualmente)
    num_fuentes = len(LISTA_ARCHIVOS)
    color_led = "#4ade80" if num_fuentes > 0 else "#f87171" # Verde o Rojo pastel
    texto_estado = "SISTEMA ONLINE" if num_fuentes > 0 else "OFFLINE"
    
    st.markdown(f"""
    <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #33415