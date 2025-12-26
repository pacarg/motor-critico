import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf

# ==========================================
# 1. CONFIGURACIÓN Y SECRETOS
# ==========================================

st.set_page_config(
    page_title="Motor Crítico v2.0", 
    layout="wide", 
    page_icon="🛡️"
)

# Estilos CSS para hacer el número del termómetro más grande
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Gestión segura de la API Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR CRÍTICO: No se detectó la API KEY en los Secrets de Streamlit.")
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

# --- PROMPT DEL SISTEMA (CON SOLICITUD DE MÉTRICA NUMÉRICA) ---
SYSTEM_INSTRUCTION = f"""
ROL: Eres el "Motor de Desarticulación Lógica". 
TU BASE DE DATOS: {LISTA_ARCHIVOS}.

TAREA: Analiza el argumento del usuario.

FORMATO JSON OBLIGATORIO:
{{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Nivel_Alarmismo": (Un número entero del 0 al 100 que indique cuánto miedo irracional o exageración contiene el texto),
  "Punto_de_Dolor": "Identifica la emoción legítima...",
  "Riesgo_Real": "Identifica el problema técnico real...",
  "Desarticulacion": "Argumento lógico que desmonta la falacia...",
  "Cita": "Cita textual breve extraída de los documentos...",
  "Autor_Cita": "Nombre del documento fuente"
}}

CONTEXTO (TUS DOCUMENTOS):
{BIBLIOTECA_CONOCIMIENTO}
"""

model = genai.GenerativeModel(
    model_name="gemini-pro",
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 3. INTERFAZ VISUAL
# ==========================================

# --- BARRA LATERAL ---
with st.sidebar:
    st.title("🎛️ Panel de Control")
    
    if len(LISTA_ARCHIVOS) > 0:
        st.success(f"✅ **Sistema Online**\nConectado a {len(LISTA_ARCHIVOS)} fuentes internas.")
    else:
        st.error("⚠️ Sin documentos.")
    
    st.markdown("---")
    modo = st.radio("Modo:", ["✍️ Escribir crítica", "📂 Casos predefinidos"])
    
    st.markdown("---")
    st.caption("ℹ️ El **Nivel de Alarmismo** mide la distancia entre la narrativa emocional y la realidad técnica.")

# --- CUERPO PRINCIPAL ---
st.title("🛡️ Motor Crítico")
st.caption("Herramienta forense de análisis de narrativas tecnológicas")

if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Introduce el argumento a analizar:", height=100)
else:
    input_usuario = st.selectbox("Selecciona caso:", [
        "La IA cobrará conciencia y nos aniquilará a todos.",
        "La IA es una caja negra opaca y peligrosa.",
        "Los artistas morirán de hambre por culpa de la IA generativa.",
        "Mis datos privados son vendidos para controlarme mentalmente.",
        "Si un coche autónomo mata a alguien, nadie es responsable."
    ])

# --- BOTÓN DE ANÁLISIS ---
if st.button("🔍 EJECUTAR ANÁLISIS", type="primary"):
    if not input_usuario:
        st.warning("El campo está vacío.")
    else:
        with st.spinner('Midiendo niveles de pánico y consultando biblioteca...'):
            try:
                # Llamada a la IA
                response = model.generate_content(input_usuario)
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)

                # Recuperamos el valor numérico (si falla, pone 0)
                alarmismo = data.get('Nivel_Alarmismo', 0)

                # --- SECCIÓN 1: EL TERMÓMETRO VISUAL ---
                st.markdown("### 📊 Diagnóstico de Intensidad")
                
                # Definimos colores y textos según el nivel
                if alarmismo < 30:
                    estado = "🟢 BAJO (Argumento Racional)"
                elif alarmismo < 70:
                    estado = "🟡 MEDIO (Preocupación Legítima)"
                else:
                    estado = "🔴 CRÍTICO (Pánico/Falacia)"

                c1, c2 = st.columns([1, 3])
                
                with c1:
                    st.metric("Nivel de Alarmismo", f"{alarmismo}%")
                
                with c2:
                    st.write(f"**Clasificación:** {estado}")
                    st.progress(alarmismo / 100)
                    st.caption(f"Perfil detectado: {data.get('Clasificacion')}")

                st.markdown("---")

                # --- SECCIÓN 2: LAS TARJETAS ---
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

                # --- SECCIÓN 3: EVIDENCIA ---
                st.markdown("###")
                with st.expander("📚 VER EVIDENCIA DOCUMENTAL", expanded=True):
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente: **{data.get('Autor_Cita')}**")

            except Exception as e:
                st.error("Hubo un error interpretando la respuesta. Inténtalo de nuevo.")
                st.write(e)