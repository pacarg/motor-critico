import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf
import time

# ==========================================
# 0. DICCIONARIO DE TRADUCCIONES (i18n) + PROMPTS
# ==========================================

TRADUCCIONES = {
    "ES": {
        "titulo_app": "Análisis Crítico",
        "intro": """
        Este sistema emplea Inteligencia Artificial para examinar tus afirmaciones sobre tecnología. 
        Procesa los argumentos para aportar contexto técnico y contrastar las ideas con una base de conocimiento especializada.
        """,
        "aviso_legal": "⚠️ **Aviso importante:** Esta herramienta no es un oráculo de verdad absoluta, sino un **asistente para la reflexión**.",
        "input_label_escribir": "Introduce el argumento a analizar:",
        "input_placeholder": "Escribe aquí el argumento...",
        "input_label_select": "Selecciona un caso típico para analizar:",
        "boton_ejecutar": "🚀 EJECUTAR ANÁLISIS",
        "alerta_vacio": "⚠️ Protocolo detenido. El campo de argumento está vacío.",
        "loading_1": "🔄 Inicializando protocolos forenses...",
        "loading_2": "📂 Consultando documentos internos...",
        "loading_3": "🧠 Procesando análisis semántico...",
        "reporte_titulo": "📊 Reporte de Análisis",
        "nivel_alarmismo": "Nivel de Alarmismo",
        "clasificacion": "Clasificación",
        "perfil": "Perfil",
        "punto_dolor": "Punto de Dolor Detectado:",
        "riesgo_real": "Riesgo Técnico Real:",
        "desarticulacion": "Desarticulación Lógica:",
        "evidencia_titulo": "📚 VER EVIDENCIA DOCUMENTAL Y FUENTE",
        "cita_titulo": "Cita textual hallada:",
        "fuente_no_disponible": "FUENTE NO DISPONIBLE",
        "fuente_identificada": "DOCUMENTO FUENTE IDENTIFICADO",
        "fuera_tema_titulo": "🔕 TEMA NO DETECTADO",
        "fuera_tema_desc": "El Motor Crítico ha detectado que este argumento no está relacionado con tecnología o IA.",
        "casos_ejemplo": [
            "La IA es una caja negra que tomará decisiones de vida o muerte sin que sepamos por qué.",
            "La IA roba el alma de los artistas al copiar sus estilos y anula la creatividad humana.",
            "Los robots nos quitarán el trabajo y viviremos en la miseria absoluta.",
            "Siento que las aplicaciones me escuchan y vigilan para manipular lo que compro y pienso.",
            "Si un coche autónomo atropella a alguien por error, la culpa es del algoritmo, no de las personas."
        ],
        "modo_op_1": "✍️ Escribir crítica",
        "modo_op_2": "📂 Casos Estratégicos",
        "info_sidebar": "ℹ️ El **Nivel de Alarmismo** mide la distancia semántica entre la narrativa emocional y la realidad técnica.",
        
        # PROMPT EN ESPAÑOL
        "system_prompt": """
        Eres el "Motor de Desarticulación Lógica".
        
        TU PRIMERA MISIÓN ES UN FILTRO DE RELEVANCIA:
        Analiza si el input del usuario está relacionado con tecnología, inteligencia artificial, sociedad digital, futuro del trabajo o ética tecnológica.
        1. SI NO TIENE RELACIÓN:
           - Debes devolver el JSON con "Clasificacion": "FUERA DE TEMA".
           - En "Desarticulacion" explica brevemente en ESPAÑOL que solo analizas temas tecnológicos.
           - Pon el resto de campos en "N/A" o 0.

        2. SI TIENE RELACIÓN:
           - Procede con el análisis forense estándar basándote exclusivamente en la documentación provista.
           - RESPONDE SIEMPRE EN ESPAÑOL.

        Debes responder SIEMPRE con este esquema JSON exacto (sin markdown extra):
        {
          "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural) o FUERA DE TEMA",
          "Nivel_Alarmismo": (Número entero 0-100),
          "Punto_de_Dolor": "Texto breve identificando la emoción subyacente...",
          "Riesgo_Real": "Texto breve explicando el problema técnico real...",
          "Desarticulacion": "Texto breve con el argumento lógico y filosófico...",
          "Cita": "Cita textual breve extraída de los documentos...",
          "Autor_Cita": "Nombre EXACTO del archivo PDF del que extrajiste la cita. Si no hay cita, pon 'N/A'."
        }
        """
    },
    "EN": {
        "titulo_app": "Critical Analysis",
        "intro": """
        This system uses Artificial Intelligence to examine your claims about technology.
        It processes arguments to provide technical context and contrast ideas against a specialized knowledge base.
        """,
        "aviso_legal": "⚠️ **Important Notice:** This tool is not an oracle of absolute truth, but an **assistant for reflection**.",
        "input_label_escribir": "Enter the argument to analyze:",
        "input_placeholder": "Type your argument here...",
        "input_label_select": "Select a typical case to analyze:",
        "boton_ejecutar": "🚀 RUN ANALYSIS",
        "alerta_vacio": "⚠️ Protocol stopped. The argument field is empty.",
        "loading_1": "🔄 Initializing forensic protocols...",
        "loading_2": "📂 Consulting internal documents...",
        "loading_3": "🧠 Processing semantic analysis...",
        "reporte_titulo": "📊 Analysis Report",
        "nivel_alarmismo": "Alarmism Level",
        "clasificacion": "Classification",
        "perfil": "Profile",
        "punto_dolor": "Detected Pain Point:",
        "riesgo_real": "Real Technical Risk:",
        "desarticulacion": "Logical Deconstruction:",
        "evidencia_titulo": "📚 VIEW DOCUMENTARY EVIDENCE AND SOURCE",
        "cita_titulo": "Textual citation found:",
        "fuente_no_disponible": "SOURCE NOT AVAILABLE",
        "fuente_identificada": "SOURCE DOCUMENT IDENTIFIED",
        "fuera_tema_titulo": "🔕 TOPIC NOT DETECTED",
        "fuera_tema_desc": "The Critical Engine has detected that this argument is unrelated to technology or AI.",
        "casos_ejemplo": [
            "AI is a black box that will make life-or-death decisions without us knowing why.",
            "AI steals the soul of artists by copying their styles and nullifies human creativity.",
            "Robots will take our jobs and we will live in absolute poverty.",
            "I feel like apps listen to me and watch me to manipulate what I buy and think.",
            "If an autonomous car hits someone by mistake, the algorithm is to blame, not the people."
        ],
        "modo_op_1": "✍️ Write Critique",
        "modo_op_2": "📂 Strategic Cases",
        "info_sidebar": "ℹ️ The **Alarmism Level** measures the semantic distance between the emotional narrative and technical reality.",
        
        # PROMPT EN INGLÉS (CLAVE PARA QUE LA RESPUESTA SEA PURA EN INGLÉS)
        "system_prompt": """
        You are the "Logical Deconstruction Engine".
        
        YOUR FIRST MISSION IS A RELEVANCE FILTER:
        Analyze if the user input is related to technology, artificial intelligence, digital society, future of work, or tech ethics.
        1. IF IT IS NOT RELATED:
           - You must return the JSON with "Clasificacion": "FUERA DE TEMA".
           - In "Desarticulacion" briefly explain in ENGLISH that you only analyze technological topics.
           - Set other fields to "N/A" or 0.

        2. IF IT IS RELATED:
           - Proceed with the standard forensic analysis based exclusively on the provided documentation.
           - RESPOND ALWAYS IN ENGLISH.

        You must ALWAYS respond with this exact JSON schema (no extra markdown):
        {
          "Clasificacion": "GROUP A (Technical) or GROUP B (Cultural) or FUERA DE TEMA",
          "Nivel_Alarmismo": (Integer 0-100),
          "Punto_de_Dolor": "Brief text identifying the underlying emotion...",
          "Riesgo_Real": "Brief text explaining the real technical problem...",
          "Desarticulacion": "Brief text with the logical and philosophical argument...",
          "Cita": "Brief textual citation extracted from the documents...",
          "Autor_Cita": "EXACT Name of the PDF file from which you extracted the citation. If no citation, put 'N/A'."
        }
        """
    }
}

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
# 1.5 SISTEMA DE SEGURIDAD
# ==========================================

def check_password():
    if "password_correct" not in st.session_state:
        token_input = st.text_input("🎟️ Token / Access Code:", type="password", key="token_input")
        st.caption("🔒 Access restricted / Acceso restringido.")
        if st.button("Enter / Entrar"):
            verify_token(token_input)
        return False
    return st.session_state["password_correct"]

def verify_token(token_ingresado):
    try:
        raw_tokens = st.secrets["TOKENS_VALIDOS"]
    except:
        st.error("⚠️ Config Error: 'TOKENS_VALIDOS' not found in Secrets.")
        return
    lista_tokens = [t.strip() for t in raw_tokens.split(",")]
    if token_ingresado.strip() in lista_tokens:
        st.session_state["password_correct"] = True
        st.success("✅ OK")
        time.sleep(0.5) 
        st.rerun()    
    else:
        st.session_state["password_correct"] = False
        st.error("⛔ Invalid Token")

if not check_password():
    st.stop()

# ==========================================
# 2. ESTILO VISUAL
# ==========================================

estilo_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@400;600&display=swap');
    :root {
        --fondo-sidebar: #020617; --fondo-body: #1e293b; --fondo-input: #f8fafc;
        --texto-input: #0f172a; --borde-input: #94a3b8; --acento: #38bdf8; --texto-general: #f1f5f9;
    }
    .stApp { background-color: var(--fondo-body); color: var(--texto-general); font-family: 'Inter', sans-serif; }
    section[data-testid="stSidebar"] { background-color: var(--fondo-sidebar); border-right: 1px solid #334155; }
    h1, h2, h3 { color: #ffffff !important; font-weight: 700; }
    p, li, label, .stMarkdown { color: #e2e8f0; }
    .stTextArea textarea { background-color: var(--fondo-input) !important; color: var(--texto-input) !important; border: 2px solid var(--borde-input); border-radius: 6px; font-family: 'JetBrains Mono', monospace; font-size: 16px; caret-color: #ef4444; }
    .stTextArea textarea:focus { border-color: var(--acento); box-shadow: 0 0 10px rgba(56, 189, 248, 0.5); }
    .stTextArea label { color: #cbd5e1 !important; font-weight: 600; }
    div[data-baseweb="select"] > div { background-color: var(--fondo-input) !important; color: var(--texto-input) !important; border: 1px solid var(--borde-input); }
    div[data-baseweb="select"] span { color: var(--texto-input) !important; }
    div.stButton > button { background: linear-gradient(135deg, #0ea5e9, #0284c7); color: white; border: none; padding: 0.6rem 1rem; font-family: 'Inter', sans-serif; font-weight: bold; text-transform: uppercase; width: 100%; border-radius: 6px; border: 1px solid #7dd3fc; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3); }
    div.stButton > button:hover { background: linear-gradient(135deg, #38bdf8, #0ea5e9); transform: translateY(-2px); }
    div[data-testid="stMetricValue"] { font-size: 2rem !important; font-family: 'JetBrains Mono', monospace; color: var(--acento) !important; text-shadow: 0 0 15px rgba(56, 189, 248, 0.4); }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    div[data-testid="stExpander"] details { border-color: var(--acento) !important; border-radius: 8px; background-color: transparent !important; }
    div[data-testid="stExpander"] details > summary { background-color: #020617 !important; border: 1px solid #38bdf8 !important; color: #38bdf8 !important; border-radius: 8px; }
    div[data-testid="stExpander"] details > summary p { color: #38bdf8 !important; font-weight: 700 !important; font-size: 1.1rem !important; }
    div[data-testid="stExpander"] details > summary svg { fill: #38bdf8 !important; color: #38bdf8 !important; }
    div[data-testid="stExpander"] details > summary:hover { background-color: #1e293b !important; border-color: #ffffff !important; }
    div[data-testid="stExpander"] details > summary:hover p { color: #ffffff !important; }
    div[data-testid="stExpander"] details > summary:hover svg { fill: #ffffff !important; color: #ffffff !important; }
    div[data-testid="stExpanderDetails"] { background-color: #0f172a !important; border: 1px solid #334155; border-top: none; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px; padding: 20px; }
    blockquote { border-left: 5px solid var(--acento); padding-left: 20px; margin-left: 0; background-color: rgba(56, 189, 248, 0.1); padding: 15px; border-radius: 4px; font-style: italic; color: #ffffff !important; font-size: 1.1rem; }
    .info-box { background-color: rgba(15, 23, 42, 0.8); border-left: 4px solid var(--acento); padding: 15px; border-radius: 4px; margin-bottom: 20px; border: 1px solid #334155; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
</style>
"""
st.markdown(estilo_css, unsafe_allow_html=True)

# ==========================================
# 3. CONEXIÓN Y SEGURIDAD API
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
# 5. LÓGICA DE IDIOMA E INTERFAZ
# ==========================================

with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", use_column_width=True)
        st.markdown("<br>", unsafe_allow_html=True)
    else:
        st.markdown("# 🛡️")
    
    # --- SELECTOR DE IDIOMA ---
    idioma_seleccionado = st.radio("Language / Idioma:", ["Español", "English"])
    LANG_CODE = "ES" if idioma_seleccionado == "Español" else "EN"
    TXT = TRADUCCIONES[LANG_CODE] 

    st.markdown("### 🎛️ Panel de Control")
    
    # WIDGET LED 
    num_fuentes = len(LISTA_ARCHIVOS)
    color_led = "#4ade80" if num_fuentes > 0 else "#f87171"
    texto_estado = "ONLINE" if num_fuentes > 0 else "OFFLINE"
    
    html_widget = f"""
    <div style='background-color: #020617; padding: 15px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 20px;'>
        <div style='display: flex; align-items: center; justify-content: space-between;'>
            <span style='color: #94a3b8; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;'>STATUS</span>
            <div style='display: flex; align-items: center; gap: 8px;'>
                <div style='width: 10px; height: 10px; background-color: {color_led}; border-radius: 50%; box-shadow: 0 0 10px {color_led};'></div>
            </div>
        </div>
        <div style='margin-top: 8px;'>
            <span style='color: #f8fafc; font-weight: bold; font-family: monospace; font-size: 0.9rem;'>{texto_estado}</span>
        </div>
        <div style='margin-top: 5px; font-size: 0.8rem; color: #94a3b8;'>
            🔗 {num_fuentes} Sources / Fuentes.
        </div>
    </div>
    """
    st.markdown(html_widget, unsafe_allow_html=True)

    modo = st.radio("Modo:", [TXT["modo_op_1"], TXT["modo_op_2"]])
    st.markdown("---")
    st.info(TXT["info_sidebar"])
    
    # FAQ DESCARGABLE
    texto_faq = """
    (AQUÍ PEGARÍAS EL TEXTO DEL FAQ QUE TE PASÉ ANTES SI QUIERES, O DÉJALO VACÍO)
    """
    # st.download_button(label="📄 FAQ", data=texto_faq, file_name="FAQ.txt")

# ==========================================
# 6. CONFIGURACIÓN DEL MODELO IA (PROMPT DINÁMICO)
# ==========================================

MODEL_NAME = "models/gemini-2.0-flash"

# AQUÍ ESTÁ EL CAMBIO CLAVE:
# Cargamos el Prompt ENTERO desde el diccionario, según el idioma.
SYSTEM_INSTRUCTION = f"""
{TXT['system_prompt']}

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
# 7. CUERPO PRINCIPAL (INTERFACE)
# ==========================================

col_h1, col_h2 = st.columns([1, 10])
with col_h2:
    st.title(TXT["titulo_app"])

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(TXT["intro"])

# Aviso importante
html_aviso = f"""
<div class="info-box">
    {TXT['aviso_legal']}
</div>
"""
st.markdown(html_aviso, unsafe_allow_html=True)

st.markdown("---")

# INPUT USUARIO
if modo == TXT["modo_op_1"]:
    input_usuario = st.text_area(TXT["input_label_escribir"], height=150, placeholder=TXT["input_placeholder"])
else:
    input_usuario = st.selectbox(TXT["input_label_select"], TXT["casos_ejemplo"])

st.markdown("<br>", unsafe_allow_html=True)

col_btn, col_rest = st.columns([1, 2])
with col_btn:
    ejecutar = st.button(TXT["boton_ejecutar"])

if ejecutar:
    if not input_usuario:
        st.warning(TXT["alerta_vacio"])
    else:
        # VISUALIZACIÓN AUTOMÁTICA
        loader_placeholder = st.empty()
        
        with loader_placeholder.container():
            st.info(TXT["loading_1"])
            time.sleep(0.3)
            st.write(TXT["loading_2"])
            time.sleep(0.3)
            st.write(TXT["loading_3"])
            
        try:
            # 1. LLAMADA A LA IA
            response = model.generate_content(input_usuario)
            
            # 2. LIMPIEZA
            texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
            data = json.loads(texto_limpio)
            
            clasificacion = data.get('Clasificacion', 'N/A')
            alarmismo = data.get('Nivel_Alarmismo', 0)
            
            loader_placeholder.empty()
            st.divider()

            # --- LÓGICA DE REPORTE ---
            if clasificacion == "FUERA DE TEMA":
                st.warning(f"🔕 **{TXT['fuera_tema_titulo']}**")
                st.info(f"{TXT['fuera_tema_desc']}\n\n**IA:** {data.get('Desarticulacion')}")
                
            else:
                st.markdown(f"### {TXT['reporte_titulo']}")
                
                if alarmismo < 30:
                    estado_texto = "LOW/BAJO"
                elif alarmismo < 70:
                    estado_texto = "MED/MEDIO"
                else:
                    estado_texto = "CRITICAL/CRÍTICO"

                col_met1, col_met2, col_met3 = st.columns(3)
                col_met1.metric(TXT["nivel_alarmismo"], f"{alarmismo}%")
                col_met2.metric(TXT["clasificacion"], estado_texto)
                col_met3.metric(TXT["perfil"], clasificacion)

                st.markdown("<br>", unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**😫 {TXT['punto_dolor']}**\n\n{data.get('Punto_de_Dolor')}")
                    st.warning(f"**⚠️ {TXT['riesgo_real']}**\n\n{data.get('Riesgo_Real')}")
                with c2:
                    st.success(f"**🧠 {TXT['desarticulacion']}**\n\n{data.get('Desarticulacion')}")

                st.markdown("<br>", unsafe_allow_html=True)
                
                # --- EVIDENCIA ---
                with st.expander(TXT["evidencia_titulo"], expanded=True):
                    st.markdown(f"#### {TXT['cita_titulo']}")
                    st.markdown(f"<blockquote>{data.get('Cita')}</blockquote>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    autor_cita = data.get('Autor_Cita', 'Desconocido')
                    if autor_cita == "N/A" or autor_cita == "Desconocido":
                        color_borde = "#94a3b8"
                        icono_fuente = "🚫"
                        titulo_fuente = TXT["fuente_no_disponible"]
                    else:
                        color_borde = "#38bdf8"
                        icono_fuente = "📂"
                        titulo_fuente = TXT["fuente_identificada"]

                    st.markdown(f"""
                    <div style='background-color: #020617; padding: 20px; border-radius: 10px; border: 2px solid {color_borde}; display: flex; align-items: center; gap: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);'>
                        <div style='font-size: 3rem; background: rgba(255,255,255,0.05); padding: 10px; border-radius: 50%; width: 80px; height: 80px; display: flex; align-items: center; justify-content: center;'>
                            {icono_fuente}
                        </div>
                        <div>
                            <div style='color: {color_borde}; font-size: 0.8rem; font-weight: 800; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 5px;'>{titulo_fuente}</div>
                            <div style='color: #ffffff; font-size: 1.3rem; font-weight: 700; font-family: monospace; word-break: break-all;'>{autor_cita}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            loader_placeholder.empty()
            st.error("Error técnico / Technical Error.")
            if "429" in str(e):
                 st.error("⏳ Server busy / Servidor ocupado (429).")
            else:
                 st.code(e)