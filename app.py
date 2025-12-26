import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Motor Crítico", 
    layout="wide", 
    page_icon="🛡️"
)

# Estilos CSS
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# API KEY
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR: No se detectó la API KEY en los Secrets.")
    st.stop()

# ==========================================
# 2. CEREBRO (LECTURA DE PDFs)
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

# --- CONFIGURACIÓN DEL MODELO ---
# Usamos el nombre OFICIAL y ESTÁNDAR para evitar errores de "Not Found"
MODEL_NAME = "gemini-1.5-flash"

SYSTEM_INSTRUCTION = f"""
Eres el "Motor de Desarticulación Lógica". 
Tu tarea es analizar argumentos sobre IA basándote en estos documentos: {LISTA_ARCHIVOS}.

Debes responder SIEMPRE con este esquema JSON exacto:
{{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Nivel_Alarmismo": (Número entero 0-100),
  "Punto_de_Dolor": "Texto breve...",
  "Riesgo_Real": "Texto breve...",
  "Desarticulacion": "Texto breve...",
  "Cita": "Cita textual breve...",
  "Autor_Cita": "Nombre del archivo fuente"
}}

CONTEXTO DOCUMENTAL:
{BIBLIOTECA_CONOCIMIENTO}
"""

# Configuración técnica para forzar JSON y reducir bloqueos
generation_config = {
    "temperature": 0.5,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json", # <--- ESTO SOLUCIONA EL ERROR JSON PARA SIEMPRE
}

# Configuramos seguridad para que no bloquee palabras como "muerte" o "aniquilar" en contextos académicos
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    safety_settings=safety_settings,
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 3. INTERFAZ VISUAL
# ==========================================

with st.sidebar:
    st.title("🎛️ Panel de Control")
    if len(LISTA_ARCHIVOS) > 0:
        st.success(f"✅ **Sistema Online**\nConectado a {len(LISTA_ARCHIVOS)} fuentes.")
    else:
        st.error("⚠️ Sin documentos.")
    st.markdown("---")
    modo = st.radio("Modo:", ["✍️ Escribir crítica", "📂 Casos predefinidos"])
    st.markdown("---")
    st.caption("v2.1 - JSON Mode Enabled")

st.title("🛡️ Motor Crítico")
st.caption("Herramienta forense de análisis de narrativas tecnológicas")

if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Argumento a analizar:", height=100)
else:
    input_usuario = st.selectbox("Selecciona caso:", [
        "La IA cobrará conciencia y nos aniquilará a todos.",
        "La IA es una caja negra opaca y peligrosa.",
        "Los artistas morirán de hambre por culpa de la IA generativa.",
        "Mis datos privados son vendidos para controlarme mentalmente."
    ])

if st.button("🔍 EJECUTAR ANÁLISIS", type="primary"):
    if not input_usuario:
        st.warning("El campo está vacío.")
    else:
        with st.spinner('Procesando...'):
            try:
                response = model.generate_content(input_usuario)
                
                # Al forzar JSON, la respuesta ya viene limpia
                data = json.loads(response.text)
                
                # --- VISUALIZACIÓN ---
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                st.markdown("### 📊 Diagnóstico")
                
                if alarmismo < 30:
                    estado = "🟢 BAJO"
                elif alarmismo < 70:
                    estado = "🟡 MEDIO"
                else:
                    estado = "🔴 CRÍTICO"

                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Alarmismo", f"{alarmismo}%")
                with c2:
                    st.write(f"**Nivel:** {estado}")
                    st.progress(alarmismo / 100)
                    st.caption(f"Perfil: {data.get('Clasificacion')}")

                st.markdown("---")
                
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    st.error("😫 **Punto de Dolor**")
                    st.write(data.get('Punto_de_Dolor'))
                with col_b:
                    st.warning("⚠️ **Riesgo Real**")
                    st.write(data.get('Riesgo_Real'))
                with col_c:
                    st.success("🧠 **Desarticulación**")
                    st.write(data.get('Desarticulacion'))

                st.markdown("###")
                with st.expander("📚 EVIDENCIA DOCUMENTAL", expanded=True):
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente: **{data.get('Autor_Cita')}**")

            except Exception as e:
                st.error("Error en el análisis.")
                # Mostramos el error técnico para depurar si hace falta
                st.write(f"Detalle: {e}")
                # Si hay respuesta pero falló el JSON, la mostramos (debugging)
                if 'response' in locals():
                    st.write("Respuesta cruda recibida:", response.text)