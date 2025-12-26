import streamlit as st
import google.generativeai as genai
import json
import os
import pypdf  # Librería para leer tus PDFs

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

# En lugar de escribir la clave, le decimos que la busque en la "Caja Fuerte" de la nube
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    # Esto es solo por si lo corres en local sin configurar secrets, 
    # pero para GitHub es mejor que esta parte no tenga tu clave real o uses un archivo secrets.toml local no subido.
    st.error("Falta la API Key en los secretos.")

# --- FUNCIÓN: LECTOR AUTOMÁTICO DE DOCUMENTOS ---
def cargar_biblioteca_desde_pdfs(carpeta="datos"):
    texto_total = ""
    archivos_leidos = []
    
    # Verificamos si la carpeta existe
    if not os.path.exists(carpeta):
        return "ADVERTENCIA: No se encontró la carpeta 'datos'. Crea la carpeta y pon tus PDFs dentro.", []

    # Buscamos archivos en la carpeta
    archivos = [f for f in os.listdir(carpeta) if f.endswith('.pdf')]
    
    if not archivos:
        return "ADVERTENCIA: La carpeta 'datos' está vacía. Añade PDFs.", []

    # Leemos cada PDF
    for archivo in archivos:
        try:
            ruta_pdf = os.path.join(carpeta, archivo)
            reader = pypdf.PdfReader(ruta_pdf)
            texto_pdf = ""
            for page in reader.pages:
                texto_pdf += page.extract_text() + "\n"
            
            # Añadimos etiqueta para que la IA sepa qué documento es
            texto_total += f"\n--- INICIO DOCUMENTO: {archivo} ---\n"
            texto_total += texto_pdf
            texto_total += f"\n--- FIN DOCUMENTO: {archivo} ---\n"
            archivos_leidos.append(archivo)
        except Exception as e:
            st.error(f"Error leyendo {archivo}: {e}")

    return texto_total, archivos_leidos

# --- CARGA INICIAL (Solo se ejecuta una vez al arrancar) ---
# Usamos cache de Streamlit para no releer los PDFs en cada clic
@st.cache_resource
def obtener_conocimiento():
    return cargar_biblioteca_desde_pdfs()

BIBLIOTECA_CONOCIMIENTO, LISTA_ARCHIVOS = obtener_conocimiento()

# --- INSTRUCCIONES DEL CEREBRO ---
SYSTEM_INSTRUCTION = f"""
ROL: Eres el "Motor de Desarticulación Lógica". 
TU BASE DE DATOS: Tienes acceso al contenido completo de los siguientes documentos internos: {LISTA_ARCHIVOS}.

TAREA: Analiza el argumento del usuario basándote PRIORITARIAMENTE en la información de tus documentos.
Si la respuesta está en los documentos, úsala. Si no, usa tu criterio general pero avísalo.

FORMATO JSON OBLIGATORIO:
{{
  "Clasificacion": "GRUPO A (Técnico) o GRUPO B (Cultural)",
  "Punto de Dolor": "Identifica la emoción...",
  "Riesgo Real": "Identifica el problema técnico según los textos...",
  "Narrativa Exagerada": "Desmonta la falacia...",
  "Cita": "Cita textual extraída de los documentos proporcionados...",
  "Autor_Cita": "Nombre del documento o autor (ej: Evaluacion_Grok.pdf)"
}}

CONTEXTO (TUS DOCUMENTOS):
{BIBLIOTECA_CONOCIMIENTO}
"""

model = genai.GenerativeModel(
    model_name="models/gemini-flash-latest",
    system_instruction=SYSTEM_INSTRUCTION
)

# ==========================================
# 2. INTERFAZ VISUAL
# ==========================================

st.set_page_config(page_title="Motor Crítico", layout="wide", page_icon="🛡️")

st.markdown("""
<style>
    .big-font { font-size:20px !important; }
    .stAlert { padding: 15px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- BARRA LATERAL (LIMPIA) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2083/2083213.png", width=80)
    st.title("Panel de Control")
    
    # Muestra solo el conteo, sin revelar los nombres de archivo
    if len(LISTA_ARCHIVOS) > 0:
        st.success(f"✅ **Sistema Online**\nMotor conectado a {len(LISTA_ARCHIVOS)} fuentes académicas internas.")
    else:
        st.error("⚠️ No se detectaron documentos.")
    
    st.markdown("---")
    modo = st.radio("Modo de consulta:", ["✍️ Escribir crítica nueva", "📂 Casos predefinidos"])

# --- CUERPO PRINCIPAL ---
st.title("🛡️ Motor Crítico")
st.caption("Herramienta de análisis forense de narrativas sobre IA")

if modo == "✍️ Escribir crítica nueva":
    input_usuario = st.text_area("Argumento:", height=100)
else:
    input_usuario = st.selectbox("Selecciona un caso típico para analizar:", [
        # CASO 1: OPACIDAD (Provoca a Carabantes)
        "La IA es una caja negra que tomará decisiones de vida o muerte sin que sepamos por qué.",
        
        # CASO 2: CREATIVIDAD (Provoca a Benjamin/Heidegger)
        "La IA roba el alma de los artistas al copiar sus estilos y anula la creatividad humana.",
        
        # CASO 3: ECONOMÍA (Provoca análisis de falacia laboral)
        "Los robots nos quitarán el trabajo y viviremos en la miseria absoluta.",
        
        # CASO 4: VIGILANCIA (Provoca a Shoshana Zuboff)
        "Siento que las aplicaciones me escuchan y vigilan para manipular lo que compro y pienso.",
        
        # CASO 5: RESPONSABILIDAD (Provoca a UNESCO)
        "Si un coche autónomo atropella a alguien por error, la culpa es del algoritmo, no de las personas.",
        
        # CASO 6: DESHUMANIZACIÓN (Provoca a Heidegger)
        "Nos estamos convirtiendo en simples datos para alimentar a la máquina y perdiendo nuestra esencia biológica."
    ])

if st.button("🔍 ANALIZAR CON BIBLIOTECA LOCAL", type="primary"):
    if not input_usuario:
        st.warning("Escribe algo.")
    else:
        with st.spinner('Leyendo tus PDFs y analizando...'):
            try:
                response = model.generate_content(input_usuario)
                texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
                data = json.loads(texto_limpio)

                st.markdown("---")
                st.subheader(f"🏷️ {data.get('Clasificacion')}")
                
                c1, c2, c3 = st.columns(3)
                with c1: st.error(f"**😫 Dolor**\n\n{data.get('Punto de Dolor')}")
                with c2: st.warning(f"**⚠️ Riesgo**\n\n{data.get('Riesgo Real')}")
                with c3: st.success(f"**🧠 Desarticulación**\n\n{data.get('Narrativa Exagerada')}")

                st.markdown("###")
                with st.expander("📚 CITA DE TUS DOCUMENTOS", expanded=True):
                    st.info(f'"{data.get("Cita")}"')
                    st.caption(f"📍 Fuente: **{data.get('Autor_Cita')}**")

            except Exception as e:
                st.error("Error analizando.")
                st.write(e)