import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf

# Configuración básica
st.set_page_config(page_title="Motor Crítico", layout="wide", page_icon="🛡️")

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

# Lectura de PDFs
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
        except:
            pass 
    return texto_total, archivos_leidos

BIBLIOTECA_CONOCIMIENTO, LISTA_ARCHIVOS = cargar_biblioteca_desde_pdfs()

# --- CONFIGURACIÓN GANADORA ---
# Usamos el nombre que sabemos que funciona en tu servidor:
MODEL_NAME = "models/gemini-flash-latest"

SYSTEM_INSTRUCTION = f"""
Eres el "Motor de Desarticulación Lógica". 
Tu tarea es analizar argumentos sobre IA basándote en estos documentos: {LISTA_ARCHIVOS}.

Debes responder SIEMPRE con este esquema JSON exacto (sin markdown extra):
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

generation_config = {
    "temperature": 0.5,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json", # Forzamos respuesta limpia
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

# Interfaz
with st.sidebar:
    st.title("🎛️ Panel de Control")
    if len(LISTA_ARCHIVOS) > 0:
        st.success(f"✅ **Sistema Online**\nConectado a {len(LISTA_ARCHIVOS)} fuentes.")
    else:
        st.error("⚠️ Sin documentos.")
    st.markdown("---")
    modo = st.radio("Modo:", ["✍️ Escribir crítica", "📂 Casos predefinidos"])

st.title("🛡️ Motor Crítico")

if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Argumento a analizar:", height=100)
else:
    # RECUPERAMOS LA LISTA ESTRATÉGICA COMPLETA
    input_usuario = st.selectbox("Selecciona un caso típico para analizar:", [
        "La IA es una caja negra que tomará decisiones de vida o muerte sin que sepamos por qué.",
        "La IA roba el alma de los artistas al copiar sus estilos y anula la creatividad humana.",
        "Los robots nos quitarán el trabajo y viviremos en la miseria absoluta.",
        "Siento que las aplicaciones me escuchan y vigilan para manipular lo que compro y pienso.",
        "Si un coche autónomo atropella a alguien por error, la culpa es del algoritmo, no de las personas.",
        "Nos estamos convirtiendo en simples datos para alimentar a la máquina y perdiendo nuestra esencia biológica."
    ])
if st.button("🔍 EJECUTAR ANÁLISIS", type="primary"):
    if not input_usuario:
        st.warning("El campo está vacío.")
    else:
        with st.spinner('Procesando...'):
            try:
                response = model.generate_content(input_usuario)
                
                # Limpieza extra por seguridad
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)
                
                # Visualización
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                st.markdown("### 📊 Diagnóstico")
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Alarmismo", f"{alarmismo}%")
                with c2:
                    st.progress(alarmismo / 100)
                    st.caption(f"Perfil: {data.get('Clasificacion')}")

                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                col1.error(f"**Dolor:**\n{data.get('Punto_de_Dolor')}")
                col2.warning(f"**Riesgo:**\n{data.get('Riesgo_Real')}")
                col3.success(f"**Lógica:**\n{data.get('Desarticulacion')}")

                with st.expander("📚 EVIDENCIA", expanded=True):
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente: {data.get('Autor_Cita')}")

            except Exception as e:
                st.error("Error analizando.")
                st.write(e)
                if 'response' in locals(): st.write("Respuesta cruda:", response.text)