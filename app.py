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
# 2. ESTILO VISUAL (CONTRASTE OPTIMIZADO)
# ==========================================

estilo_css = """
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* --- PALETA DE COLORES INTELIGENTE --- */
    :root {
        /* 1. BARRA LATERAL (Oscura - Panel de Control) */
        --fondo-sidebar: #020617;      /* Casi negro */
        
        /* 2. CUERPO PRINCIPAL (Tecnológico Intermedio - Gunmetal) */
        --fondo-body: #1e293b;         /* Slate 800: Un azul grisáceo profesional */
        
        /* 3. INPUTS Y CAJAS (Claros - Alto Contraste) */
        --fondo-input: #f1f5f9;        /* Slate 100: Gris platino muy claro */
        --texto-input: #0f172a;        /* Slate 900: Texto oscuro para leer bien */
        
        /* 4. ACENTOS */
        --acento: #38bdf8;             /* Cyan brillante */
        --texto-general: #f8fafc;      /* Blanco para el fondo oscuro */
    }

    /* APLICACIÓN GLOBAL */
    .stApp {
        background-color: var(--fondo-body);
        color: var(--texto-general);
        font-family: 'Inter', sans-serif;
    }

    /* BARRA LATERAL */
    section[data-testid="stSidebar"] {
        background-color: var(--fondo-sidebar);
        border-right: 1px solid #334155;
    }
    
    /* TÍTULOS */
    h1, h2, h3 { color: #ffffff !important; font-weight: 700; }
    p, li, label { color: #e2e8f0 !important; }

    /* --- EL CAMBIO CLAVE: INPUTS CLAROS --- */
    .stTextArea textarea {
        background-color: var(--fondo-input) !important;
        color: var(--texto-input) !important; /* Texto oscuro sobre fondo claro */
        border: 2px solid #94a3b8;
        border-radius: 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 16px;
        caret-color: #ef4444; /* CURSOR ROJO PARA QUE SE VEA BIEN */
    }
    .stTextArea textarea:focus {
        border-color: var(--acento);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
    }
    /* El título pequeñito encima del input */
    .stTextArea label {
        color: #94a3b8 !important;
        font-weight: bold;
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
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8, #0ea5e9);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(14, 165, 233, 0.5);
    }

    /* MÉTRICAS (Números grandes) */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: var(--acento) !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    
    /* CAJAS DE INFORMACIÓN (Avisos, Alertas) */
    div[data-testid="stAlert"] {
        background-color: #0f172a; /* Fondo oscuro para las alertas */
        color: #e2e8f0;
        border: 1px solid #334155;
    }
    
    /* Custom Info Box */
    .info-box {
        background-color: rgba(15, 23, 42, 0.6);
        border-left: 4px solid var(--acento);
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
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
    archivos_leidos = []
    
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        return "ADVERTENCIA: Carpeta 'datos' vacía.", []

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
# 6. INTERFAZ VISUAL
# ==========================================

with st.sidebar:
    # 1. LOGO
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("# 🛡️") 
    
    st.markdown("### 🎛️ Panel de Control")
    
    # 2. WIDGET LED
    num_fuentes = len(LISTA_ARCHIVOS)
    color_led = "#4ade80" if num_fuentes > 0 else "#f87171"
    texto_estado = "SISTEMA ONLINE" if num_fuentes > 0 else "OFFLINE"
    
    # HTML seguro
    html_widget = f"""
    <div style='background-color: #020617; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <span style='color: #94a3b8; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;'>ESTADO DE RED</span>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='width: 10px; height: 10px; background-color: {color_led}; border-radius: 50%; box-shadow: 0 0 10px {color_led};'></div>
            </div>
        </div>
        <div style='margin-top: 8px;'>
            <span style='color: #f8fafc; font-weight: bold; font-family: monospace; font-size: 0.9rem;'>{texto_estado}</span>
        </div>
        <div style='margin-top: 5px; font-size: 0.8rem; color: #94a3b8;'>
            🔗 Conectado a {num_fuentes} fuentes de conocimiento.
        </div>
    </div>
    """
    st.markdown(html_widget, unsafe_allow_html=True)

    modo = st.radio("Modo de Operación:", ["✍️ Escribir crítica", "📂 Casos Estratégicos"])
    
    st.markdown("---")
    st.info("ℹ️ El **Nivel de Alarmismo** mide la distancia semántica entre la narrativa emocional y la realidad técnica.")

# --- CUERPO PRINCIPAL ---

col_h1, col_h2 = st.columns([1,