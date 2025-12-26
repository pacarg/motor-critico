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

# Gestión segura de la API Key
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=API_KEY)
except:
    st.error("⚠️ ERROR CRÍTICO: No se detectó la API KEY en los Secrets.")
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
            pass # Ignoramos errores puntuales de lectura

    return texto_total, archivos_leidos

BIBLIOTECA_CONOCIMIENTO, LISTA_ARCHIVOS = cargar_biblioteca_desde_pdfs()

# --- PROMPT DEL SISTEMA MEJORADO (CON MÉTRICAS) ---
SYSTEM_INSTRUCTION = f"""
ROL: Eres el "Motor de Desarticulación Lógica". 
TU BASE DE DATOS: {LISTA_ARCHIVOS}.

TAREA: Analiza el argumento del usuario.
Si la respuesta está en los documentos, úsala. Si no, usa tu criterio ético/técnico.

FORMATO JSON OBLIGATORIO:
{{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Nivel_Alarmismo": (Un número entero del 0 al 100 que indique cuánto miedo irracional contiene),
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
    model_name="models/gemini-1.5-flash",
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 3. INTERFAZ VISUAL (DASHBOARD)
# ==========================================

# Estilos CSS para las métricas
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)

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
    st.info("💡 **Tip:** El 'Nivel de Alarmismo' es calculado por la IA basándose en el lenguaje emocional del texto.")

# --- CUERPO PRINCIPAL ---
st.title("🛡️ Motor Crítico de IA")
st.caption("Herramienta forense para desarticular narrativas tecnológicas.")

if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Introduce el argumento a analizar:", height=100)
else:
    input_usuario = st.selectbox("Selecciona caso:", [
        "La IA cobrará conciencia y nos aniquilará a todos.",
        "La IA es una caja negra opaca y peligrosa.",
        "Los artistas morirán de hambre por culpa de la IA generativa.",
        "Mis datos privados son vendidos para controlarme mentalmente."
    ])

# --- BOTÓN DE ANÁLISIS ---
if st.button("🔍 EJECUTAR ANÁLISIS FORENSE", type="primary"):
    if not input_usuario:
        st.warning("El campo está vacío.")
    else:
        with st.spinner('Procesando lógica... Consultando biblioteca...'):
            try:
                response = model.generate_content(input_usuario)
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)

                # --- SECCIÓN 1: EL TERMÓMETRO ---
                st.markdown("### 📊 Diagnóstico de Intensidad")
                c1, c2 = st.columns([1, 3])
                
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                with c1:
                    st.metric("Nivel de Alarmismo", f"{alarmismo}%")
                
                with c2:
                    # Barra de progreso con color dinámico
                    if alarmismo < 30:
                        color_barra = "🟢 Riesgo Bajo"
                        st.progress(alarmismo / 100)
                    elif alarmismo < 70:
                        color_barra = "🟡 Riesgo Medio"
                        st.progress(alarmismo / 100)
                    else:
                        color_barra = "🔴 Riesgo Crítico (Pánico)"
                        st.progress(alarmismo / 100)
                    st.caption(f"Clasificación: **{color_barra}** | Perfil: **{data.get('Clasificacion')}**")

                st.markdown("---")

                # --- SECCIÓN 2: LAS TARJETAS ---
                col_a, col_b, col_c = st.columns(3)
                
                with col_a:
                    st.error("😫 **Punto de Dolor**")
                    st.write(data.get('Punto_de_Dolor'))
                
                with col_b:
                    st.warning("⚠️ **Riesgo Real (Técnico)**")
                    st.write(data.get('Riesgo_Real'))
                    
                with col_c:
                    st.success("🧠 **Desarticulación Lógica**")
                    st.write(data.get('Desarticulacion'))

                # --- SECCIÓN 3: EVIDENCIA ---
                st.markdown("###")
                with st.expander("📚 VER EVIDENCIA DOCUMENTAL", expanded=True):
                    st.markdown(f"> *\"{data.get('Cita')}\"*")
                    st.caption(f"📍 Fuente detectada: **{data.get('Autor_Cita')}**")

                # --- SECCIÓN 4: EXPORTAR ---
                informe_texto = f"""INFORME FORENSE - MOTOR CRÍTICO
--------------------------------
ARGUMENTO ANALIZADO: {input_usuario}
FECHA: {json.dumps(data.get('Clasificacion'))}
NIVEL DE ALARMISMO: {alarmismo}%

1. PUNTO DE DOLOR:
{data.get('Punto_de_Dolor')}

2. RIESGO TÉCNICO REAL:
{data.get('Riesgo_Real')}

3. DESARTICULACIÓN LÓGICA:
{data.get('Desarticulacion')}

FUENTE CITADA: {data.get('Autor_Cita')}
"""
                st.download_button(
                    label="⬇️ Descargar Informe (TXT)",
                    data=informe_texto,
                    file_name="informe_forense.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error("Error en el análisis. Inténtalo de nuevo.")
                st.write(e)