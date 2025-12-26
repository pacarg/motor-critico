import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf
import time

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILO TECH
# ==========================================

st.set_page_config(
    page_title="Motor Crítico | Forense", 
    layout="wide", 
    page_icon="🛡️",
    initial_sidebar_state="expanded"
)

# --- INYECCIÓN DE CSS ESTILO "FORENSE/CYBER" ---
st.markdown("""
<style>
    /* IMPORTAR FUENTES TÉCNICAS */
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

    /* BOTÓN EJECUTAR */
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
        border: 1px solid #1f6feb;
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #3b8df5, #2659a3);
        box-shadow: 0 0 15px rgba(31, 111, 235, 0.5);
        transform: translateY(-2px);
    }

    /* MÉTRICAS Y TEXTOS */
    div[data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-family: 'JetBrains Mono', monospace;
        color: #58a6ff !important;
    }
    
    /* AVISO IMPORTANTE */
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
# 2. CONEXIÓN Y SEGURIDAD
# ==========================================

try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR CRÍTICO: No se detectó la API KEY en los Secrets.")
    st.stop()

# ==========================================
# 3. CEREBRO (LECTURA DE PDFs)
# ==========================================

@st.cache_resource
def cargar_biblioteca_desde_pdfs(carpeta="datos"):
    texto_total = ""
    archivos_leidos = []
    
    # Crear carpeta si no existe para evitar error
    if not os.path.exists(carpeta):
        os.makedirs(carpeta)
        return "ADVERTENCIA: Carpeta 'datos' creada (está vacía).", []

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
# 4. CONFIGURACIÓN DEL MODELO IA (CORREGIDO)
# ==========================================

MODEL_NAME = "models/gemini-flash-latest"

# 1. Definimos la instrucción base SIN usar f-string (para evitar conflicto con las llaves {})
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

# 2. Ahora sí usamos f-string para inyectar los datos variables
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
# 5. INTERFAZ VISUAL (FRONTEND TECH)
# ==========================================

# --- BARRA LATERAL ---
with st.sidebar:
    st.markdown("## 🛡️ Guía Tecnológico")
    st.caption("Herramienta Forense v2.0")
    st.markdown("---")
    
    st.markdown("### 🎛️ Panel de Control")
    
    # Widget LED de Estado
    num_fuentes = len(LISTA_ARCHIVOS)
    color_led = "#3fb950" if num_fuentes > 0 else "#da3633"
    texto_estado = "ONLINE" if num_fuentes > 0 else "OFFLINE"
    
    st.markdown(f"""
    <div style='background-color: #0d1117; padding: 15px; border-radius: 6px; border: 1px solid #30363d; margin-bottom: 20px;'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <span style='color: #8b949e; font-size: 0.8rem; font-family: monospace;'>ESTADO</span>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='width: 8px; height: 8px; background-color: {color_led}; border-radius: 50%; box-shadow: 0 0 8px {color_led};'></div>
                <span style='color: {color_led}; font-weight: bold; font-family: monospace; font-size: 0.8rem;'>{texto_estado}</span>
            </div>
        </div>
        <div style='margin-top: 10px; border-top: 1px solid #21262d; padding-top: 8px;'>
            <span style='color: #e6edf3; font-size: 0.8rem; font-weight: 600;'>Conexión:</span><br>
            <span style='color: #8b949e; font-size: 0.75rem; font-family: monospace;'>{num_fuentes} Nodos Documentales</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    modo = st.radio("Modo de Operación:", ["✍️ Escribir crítica", "📂 Casos Estratégicos"])
    
    st.markdown("---")
    st.info("ℹ️ El **Nivel de Alarmismo** mide la distancia semántica entre la narrativa emocional y la realidad técnica.")

# --- CUERPO PRINCIPAL ---
col_h1, col_h2 = st.columns([1, 10])
with col_h1:
    st.markdown("# 🛡️")
with col_h2:
    st.markdown("# Motor Crítico")
    st.markdown("<div style='margin-top: -15px; color: #8b949e;'>Herramienta forense de análisis de narrativas tecnológicas</div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

st.markdown("""
Este sistema emplea Inteligencia Artificial para **desarticular narrativas** sobre tecnología. 
Analiza argumentos para detectar sesgos y contrastar el discurso popular contra una base de conocimiento crítica.
""")

st.markdown("""
<div class="info-box">
    <strong>⚠️ Aviso importante:</strong> Esta herramienta no pretende ser un oráculo de verdad absoluta ni sustituir el juicio ético humano. 
    No es un validador automático de hechos (<i>fact-checker</i>), sino un <strong>asistente para la reflexión</strong>.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Lógica de Entrada
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

# Botón de Ejecución
col_btn, col_rest = st.columns([1, 2])
with col_btn:
    ejecutar = st.button("🔴 EJECUTAR ANÁLISIS FORENSE")

if ejecutar:
    if not input_usuario:
        st.warning("⚠️ Protocolo detenido. El campo de argumento está vacío.")
    else:
        # Animación de carga High-Tech
        with st.status("🔄 Inicializando protocolos forenses...", expanded=True) as status:
            time.sleep(0.5)
            st.write(f"📂 Accediendo a {len(LISTA_ARCHIVOS)} fuentes internas...")
            time.sleep(0.5)
            st.write("🧠 Vectorizando argumento del usuario...")
            
            try:
                # 1. LLAMADA A LA IA
                response = model.generate_content(input_usuario)
                
                # 2. LIMPIEZA Y PARSEO
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)
                
                # 3. EXTRACCIÓN DE MÉTRICAS
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                status.update(label="✅ Análisis Completado", state="complete", expanded=False)

                # --- REPORTE DE RESULTADOS ---
                st.markdown("### 📊 Reporte de Análisis")
                
                if alarmismo < 30:
                    estado_texto = "BAJO (Racional)"
                    delta_color = "normal" 
                elif alarmismo < 70:
                    estado_texto = "MEDIO (Preocupante)"
                    delta_color = "off"
                else:
                    estado_texto = "CRÍTICO (Pánico/Falacia)"
                    delta_color = "inverse"

                # Tarjetas de Métricas
                col_met1, col_met2, col_met3 = st.columns(3)
                col_met1.metric("Nivel de Alarmismo", f"{alarmismo}%", delta="Intensidad")
                col_met2.metric("Clasificación", "Detectada", delta=estado_texto)
                col_met3.metric("Perfil", data.get('Clasificacion', 'N/A'))

                st.markdown("---")

                # Grid de Detalles
                c1, c2, c3 = st.columns(3)
                
                with c1:
                    st.markdown("#### 😫 Punto de Dolor")
                    st.info(data.get('Punto_de_Dolor'))
                
                with c2:
                    st.markdown("#### ⚠️ Riesgo Real")
                    st.warning(data.get('Riesgo_Real'))
                    
                with c3:
                    st.markdown("#### 🧠 Desarticulación")
                    st.success(data.get('Desarticulacion'))

                # Evidencia Documental
                st.markdown("<br>", unsafe_allow_html=True)
                with st.expander("📂 VER EVIDENCIA DOCUMENTAL (FUENTE INTERNA)", expanded=True):
                    st.markdown(f"> *\"{data.get('Cita')}\"*")
                    st.caption(f"📍 Identificado en archivo: **{data.get('Autor_Cita')}**")

            except Exception as e:
                status.update(label="❌ Error en el análisis", state="error")
                st.error("Error técnico durante el procesamiento.")
                st.code(e)
                # Debugging (opcional)
                if 'response' in locals():
                    with st.expander("Ver respuesta cruda (Debug)"):
                        st.write(response.text)