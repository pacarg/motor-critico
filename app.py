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
# 2. ESTILO VISUAL (CSS BLINDADO)
# ==========================================

# Definimos el CSS en una variable separada para evitar errores de sintaxis
estilo_css = """
<style>
    /* IMPORTAR FUENTES */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');

    /* --- PALETA DE COLORES --- */
    :root {
        --fondo-principal: #0f172a;      /* Azul noche muy oscuro */
        --fondo-secundario: #1e293b;     /* Azul grisáceo */
        --texto-principal: #f8fafc;      /* Blanco casi puro */
        --texto-secundario: #94a3b8;     /* Gris claro */
        --acento-primario: #38bdf8;      /* Azul cielo brillante */
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
        background-color: #020617;
        border-right: 1px solid var(--borde);
    }
    
    /* TÍTULOS Y TEXTOS */
    h1, h2, h3 { color: #ffffff !important; font-weight: 700; }
    p, li, label { color: #e2e8f0 !important; font-size: 1rem; }

    /* INPUTS DE TEXTO */
    .stTextArea textarea {
        background-color: var(--fondo-secundario);
        color: #ffffff;
        border: 1px solid var(--borde);
        font-family: 'JetBrains Mono', monospace;
        font-size: 15px;
    }
    .stTextArea textarea:focus {
        border-color: var(--acento-primario);
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
    }

    /* BOTÓN EJECUTAR */
    div.stButton > button {
        background: linear-gradient(135deg, #0ea5e9, #0284c7);
        color: white;
        border: none;
        padding: 0.6rem 1rem;
        font-family: 'Inter', sans-serif;
        font-weight: bold;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        width: 100%;
        border-radius: 6px;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #38bdf8, #0ea5e9);
        box-shadow: 0 4px 15px rgba(14, 165, 233, 0.4);
        transform: translateY(-2px);
    }

    /* MÉTRICAS */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: var(--acento-primario) !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.3);
    }
    div[data-testid="stMetricLabel"] { color: var(--texto-secundario) !important; }
    
    /* CAJAS DE ALERTA */
    .info-box {
        background-color: rgba(14, 165, 233, 0.1);
        border-left: 4px solid var(--acento-primario);
        padding: 15px;
        border-radius: 4px;
        margin-bottom: 20px;
        color: var(--texto-principal);
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

# Usamos f-string simple aquí, separada del resto para evitar confusión
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
# 6. INTERFAZ VISUAL (ESTRUCTURA SEGURA)
# ==========================================

with st.sidebar:
    
    # 1. LOGO
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("# 🛡️") 
    
    st.markdown("### 🎛️ Panel de Control")
    
    # 2. WIDGET LED (Definido en variable primero)
    num_fuentes = len(LISTA_ARCHIVOS)
    color_led = "#4ade80" if num_fuentes > 0 else "#f87171"
    texto_estado = "SISTEMA ONLINE" if num_fuentes > 0 else "OFFLINE"
    
    html_widget = f"""
    <div style='background-color: #1e293b; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;'>
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

col_h1, col_h2 = st.columns([1, 10])
with col_h2:
    st.title("Motor Crítico")
    st.markdown("**Herramienta forense de análisis de narrativas tecnológicas**")

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
Este sistema emplea Inteligencia Artificial para **desarticular narrativas** sobre tecnología. 
Analiza argumentos para detectar sesgos y contrastar el discurso popular contra una base de conocimiento crítica.
""")

# Aviso importante definido como variable primero
html_aviso = """
<div class="info-box">
    <strong>⚠️ Aviso importante:</strong> Esta herramienta no pretende ser un oráculo de verdad absoluta ni sustituir el juicio ético humano. 
    No es un validador automático de hechos (<i>fact-checker</i>), sino un <strong>asistente para la reflexión</strong>.
</div>
"""
st.markdown(html_aviso, unsafe_allow_html=True)

st.markdown("---")

if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Introduce el argumento a analizar:", height=150, placeholder="Escribe aquí el argumento...")
else:
    input_usuario = st.selectbox("Selecciona un caso típico para analizar:", [
        "La IA es una caja negra que tomará decisiones de vida o muerte sin que sepamos por qué.",
        "La IA roba el alma de los artistas al copiar sus estilos y anula la creatividad humana.",
        "Los robots nos quitarán el trabajo y viviremos en la miseria absoluta.",
        "Siento que las aplicaciones me escuchan y vigilan para manipular lo que compro y pienso.",
        "Si un coche autónomo atropella a alguien por error, la culpa es del algoritmo, no de las personas.",
        "Nos estamos convirtiendo en simples datos para alimentar a la máquina y perdiendo nuestra esencia biológica."
    ])

st.markdown("<br>", unsafe_allow_html=True)

col_btn, col_rest = st.columns([1, 2])
with col_btn:
    ejecutar = st.button("🚀 EJECUTAR ANÁLISIS")

if ejecutar:
    if not input_usuario:
        st.warning("⚠️ Protocolo detenido. El campo de argumento está vacío.")
    else:
        with st.status("🔄 Procesando análisis forense...", expanded=True) as status:
            time.sleep(0.5)
            st.write(f"📂 Consultando {len(LISTA_ARCHIVOS)} documentos internos...")
            time.sleep(0.5)
            st.write("🧠 Detectando sesgos cognitivos...")
            
            try:
                # 1. LLAMADA A LA IA
                response = model.generate_content(input_usuario)
                
                # 2. LIMPIEZA
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)
                
                # 3. MÉTRICAS
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                status.update(label="✅ Análisis Completado", state="complete", expanded=False)

                st.divider()

                # --- REPORTE ---
                st.markdown("### 📊 Reporte de Análisis")
                
                if alarmismo < 30:
                    estado_texto = "BAJO (Racional)"
                elif alarmismo < 70:
                    estado_texto = "MEDIO (Preocupante)"
                else:
                    estado_texto = "CRÍTICO (Pánico)"

                col_met1, col_met2, col_met3 = st.columns(3)
                col_met1.metric("Nivel de Alarmismo", f"{alarmismo}%", delta="Intensidad")
                col_met2.metric("Clasificación", "Detectada", delta=estado_texto)
                col_met3.metric("Perfil", data.get('Clasificacion', 'N/A'))

                st.markdown("<br>", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**😫 Punto de Dolor Detectado:**\n\n{data.get('Punto_de_Dolor')}")
                    st.warning(f"**⚠️ Riesgo Técnico Real:**\n\n{data.get('Riesgo_Real')}")
                with c2:
                    st.success(f"**🧠 Desarticulación Lógica:**\n\n{data.get('Desarticulacion')}")

                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📚 VER EVIDENCIA DOCUMENTAL (FUENTE ORIGINAL)", expanded=True):
                    # Usamos st.write para evitar errores de sintaxis en strings complejos
                    st.markdown("**Cita textual hallada:**")
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente: **{data.get('Autor_Cita')}**")

            except Exception as e:
                status.update(label="❌ Error en el análisis", state="error")
                st.error("Error técnico durante el procesamiento.")
                st.code(e)