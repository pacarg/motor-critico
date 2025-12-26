import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf

# ==========================================
# 1. CONFIGURACIÓN BÁSICA
# ==========================================

st.set_page_config(
    page_title="Motor Crítico", 
    layout="wide", 
    page_icon="🛡️"
)

# Estilos CSS para hacer el número del termómetro grande y visible
st.markdown("""
<style>
    div[data-testid="stMetricValue"] { font-size: 30px; font-weight: bold; }
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
# 4. CONFIGURACIÓN DEL MODELO IA
# ==========================================

# Nombre del modelo que confirmó funcionamiento en tu servidor
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

CONTEXTO DOCUMENTAL:
{BIBLIOTECA_CONOCIMIENTO}
"""

generation_config = {
    "temperature": 0.5,
    "max_output_tokens": 8192,
    "response_mime_type": "application/json", # Modo JSON activado para evitar errores
}

model = genai.GenerativeModel(
    model_name=MODEL_NAME,
    generation_config=generation_config,
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 5. INTERFAZ VISUAL (FRONTEND)
# ==========================================

# --- BARRA LATERAL CON LOGO ---
with st.sidebar:
    # 1. INTENTO DE CARGAR LOGO
    try:
        st.image("logo.png", use_column_width=True)
    except:
        # Si no encuentra el logo, no pasa nada, solo avisa discretamente
        st.info("💡 Sube una imagen llamada 'logo.png' a GitHub para personalizar este espacio.")
    
    st.markdown("---")
    
    st.title("🎛️ Panel de Control")
    
    # 2. MONITOR DE ESTADO
    if len(LISTA_ARCHIVOS) > 0:
        st.success(f"✅ **Sistema Online**\nConectado a {len(LISTA_ARCHIVOS)} fuentes internas.")
    else:
        st.error("⚠️ Sin documentos en carpeta 'datos'.")
    
    st.markdown("---")
    
    # 3. SELECTOR DE MODO
    modo = st.radio("Modo de Operación:", ["✍️ Escribir crítica", "📂 Casos Estratégicos"])
    
    st.markdown("---")
    st.caption("ℹ️ El **Nivel de Alarmismo** mide la distancia semántica entre la narrativa emocional del usuario y la realidad técnica de los documentos.")

# --- CUERPO PRINCIPAL ---
st.title("🛡️ Motor Crítico")
st.caption("Herramienta forense de análisis de narrativas tecnológicas - Guía Tecnológico")

# Lógica de entrada de datos (RECUPERAMOS LA LISTA BUENA)
if modo == "✍️ Escribir crítica":
    input_usuario = st.text_area("Introduce el argumento a analizar:", height=100)
else:
    input_usuario = st.selectbox("Selecciona un caso típico para analizar:", [
        "La IA es una caja negra que tomará decisiones de vida o muerte sin que sepamos por qué.",
        "La IA roba el alma de los artistas al copiar sus estilos y anula la creatividad humana.",
        "Los robots nos quitarán el trabajo y viviremos en la miseria absoluta.",
        "Siento que las aplicaciones me escuchan y vigilan para manipular lo que compro y pienso.",
        "Si un coche autónomo atropella a alguien por error, la culpa es del algoritmo, no de las personas.",
        "Nos estamos convirtiendo en simples datos para alimentar a la máquina y perdiendo nuestra esencia biológica."
    ])

# --- BOTÓN DE EJECUCIÓN ---
if st.button("🔍 EJECUTAR ANÁLISIS FORENSE", type="primary"):
    if not input_usuario:
        st.warning("El campo de texto está vacío.")
    else:
        with st.spinner('Analizando patrones lógicos y consultando biblioteca...'):
            try:
                # 1. Llamada a la IA
                response = model.generate_content(input_usuario)
                
                # 2. Limpieza y parseo de JSON
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)
                
                # 3. Extracción de métricas
                alarmismo = data.get('Nivel_Alarmismo', 0)
                
                # --- VISUALIZACIÓN DE RESULTADOS ---
                st.markdown("### 📊 Diagnóstico de Intensidad")
                
                # Definición de colores según gravedad
                if alarmismo < 30:
                    estado = "🟢 BAJO (Racional)"
                    bar_color = "green"
                elif alarmismo < 70:
                    estado = "🟡 MEDIO (Preocupante)"
                    bar_color = "orange"
                else:
                    estado = "🔴 CRÍTICO (Pánico/Falacia)"
                    bar_color = "red"

                # Layout del termómetro
                c1, c2 = st.columns([1, 3])
                with c1:
                    st.metric("Nivel de Alarmismo", f"{alarmismo}%")
                with c2:
                    st.write(f"**Clasificación:** {estado}")
                    st.progress(alarmismo / 100)
                    st.caption(f"Perfil detectado: {data.get('Clasificacion')}")

                st.markdown("---")

                # Tarjetas de Análisis
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

                # Evidencia Documental
                st.markdown("###")
                with st.expander("📚 VER EVIDENCIA DOCUMENTAL", expanded=True):
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente hallada: **{data.get('Autor_Cita')}**")

            except Exception as e:
                st.error("Error en el análisis.")
                st.write("Detalle del error técnico:", e)
                # Si falló el JSON pero hay texto, lo mostramos para depurar
                if 'response' in locals():
                    st.write("Respuesta cruda recibida:", response.text)