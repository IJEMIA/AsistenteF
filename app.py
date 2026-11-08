import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io
import re

# Intentar importar python-docx para cumplir con el entregable .docx del prompt
try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

# ----------------- CONFIGURACIÓN DE PÁGINA -----------------
st.set_page_config(
    page_title="Asistente F - Facilitador OKR", 
    page_icon="📜", 
    layout="centered", 
    initial_sidebar_state="collapsed", 
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# ----------------- ESTILOS CSS (CORREGIDOS PARA MÓVIL Y MODO OSCURO) -----------------
css_pergamino = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;} .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;} [data-testid="stStatusWidget"] {display: none;}
    
    .stApp {
        background: linear-gradient(135deg, #fdfbf7 0%, #f4efe6 30%, #e8dec8 100%) !important;
        color: #36200b !important;
        max-width: 100%;
        padding: 0;
        min-height: 100vh;
    }
    
    h1 {
        font-family: 'Cinzel', serif !important;
        color: #4a2c11 !important;
        text-align: center;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        text-shadow: 0 1px 3px rgba(74,44,17,0.10);
        padding-top: 1.5rem !important;
        margin-bottom: 0.1rem !important;
    }
    
    .stCaption, [data-testid="stCaptionContainer"] p {
        text-align: center !important;
        color: #7a5230 !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 0.95rem !important;
        margin-bottom: 1.2rem !important;
    }
    
    /* Contenedor general de mensajes de chat */
    [data-testid="stChatMessage"] {
        background: linear-gradient(135deg, #ffffff 0%, #f7f2e7 100%) !important;
        border: 1px solid rgba(122,82,48,0.22) !important;
        border-left: 5px solid #8c5a2b !important;
        border-radius: 18px !important;
        padding: 1rem 1.2rem !important;
        margin: 0.6rem 0 !important;
        box-shadow: 0 2px 12px rgba(74,44,17,0.08) !important;
    }
    
    /* Forzar texto oscuro legible en cualquier dispositivo (incluso con modo oscuro activo en el móvil) */
    [data-testid="stChatMessage"] p,
    [data-testid="stChatMessage"] span,
    [data-testid="stChatMessage"] li,
    [data-testid="stChatMessage"] strong,
    [data-testid="stChatMessage"] div[data-testid="stMarkdownContainer"] {
        color: #2c1806 !important;
        line-height: 1.65 !important;
        font-size: 0.96rem !important;
    }
    
    /* Input del chat */
    [data-testid="stChatInputContainer"] {
        padding: 0.8rem 1rem 1.5rem 1rem !important;
        background: transparent !important;
    }
    [data-testid="stChatInput"] {
        border-radius: 25px !important;
        border: 2px solid rgba(140,90,43,0.45) !important;
        background: #ffffff !important;
        box-shadow: 0 4px 20px rgba(74,44,17,0.10) !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #2c1806 !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #8c6b4a !important;
        font-style: italic;
    }
    
    .sep {text-align: center; margin: 0.5rem 0 1rem 0; font-size: 0.75rem; color: #b89c7d; letter-spacing: 0.5em;}
    .temas-bar {display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4rem; margin: 0.3rem 1rem 1rem 1rem;}
    .tema-chip {padding: 0.25rem 0.7rem; border-radius: 12px; background: rgba(255,255,255,0.85); color: #6e431d !important; font-size: 0.75rem; font-weight: 600; border: 1px solid rgba(140,90,43,0.25); font-family: 'Inter', sans-serif;}
</style>
"""
st.markdown(css_pergamino, unsafe_allow_html=True)

# ----------------- INICIALIZACIÓN DEL CLIENTE Y AUTODETECCIÓN DE MODELO -----------------
try:
    api_key = st.secrets["groq"]["api_key"].strip()
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
except Exception:
    st.error("⚠️ Error de configuración: Revisa que `st.secrets['groq']['api_key']` esté definido en tus Secrets.")
    st.stop()

@st.cache_data(ttl=3600, show_spinner=False)
def obtener_modelos_funcionales(key_str):
    """
    Consulta los modelos habilitados en la cuenta de Groq del usuario,
    filtra los que no son de chat de texto y verifica en vivo cuáles responden sin error 400/404.
    """
    cli = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=key_str)
    palabras_excluidas = [
        "whisper", "guard", "safety", "vision", "embed", "classify",
        "tts", "audio", "orpheus", "playai", "distil-whisper", "tool-use", "compound"
    ]
    
    try:
        modelos_cuenta = [m.id for m in cli.models.list().data]
    except Exception:
        modelos_cuenta = []

    candidatos = [
        m for m in modelos_cuenta
        if not any(excl in m.lower() for excl in palabras_excluidas)
    ]

    # Orden de preferencia (priorizando Llama 3.3, Llama 4, Llama 3.1, Gemma 2, Qwen, Mixtral)
    preferidos = [
        "llama-3.3-70b-versatile",
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "meta-llama/llama-4-maverick-17b-128e-instruct",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "qwen-qwq-32b",
        "qwen-2.5-32b",
        "llama3-70b-8192",
        "llama3-8b-8192",
        "mixtral-8x7b-32768"
    ]

    # Ordenar candidatos poniendo primero los preferidos que existan en su cuenta
    candidatos_ordenados = sorted(
        candidatos,
        key=lambda x: preferidos.index(x) if x in preferidos else 999
    )

    # Si list() devolvió vacío, probar directamente la lista de preferidos
    if not candidatos_ordenados:
        candidatos_ordenados = preferidos

    modelos_verificados = []
    for mod in candidatos_ordenados:
        try:
            # Micro-prueba de 1 token para confirmar que el modelo existe (no 404) y no pide términos (no 400)
            cli.chat.completions.create(
                model=mod,
                messages=[{"role": "user", "content": "ok"}],
                max_tokens=1
            )
            modelos_verificados.append(mod)
            # Con encontrar los 3 mejores modelos 100% operativos en su cuenta basta para rapidez
            if len(modelos_verificados) >= 3:
                break
        except Exception:
            continue

    return modelos_verificados

modelos_operativos = obtener_modelos_funcionales(api_key)

if not modelos_operativos:
    st.error(
        "⚠️ Ningún modelo de chat respondió en tu cuenta de Groq. "
        "Entra a https://console.groq.com/settings/limits y verifica que tu proyecto tenga modelos habilitados."
    )
    st.stop()

# ----------------- FUNCIONES AUXILIARES -----------------
def limpiar_texto_para_audio(texto):
    """Elimina símbolos de Markdown, tablas y emojis para que gTTS lea con naturalidad."""
    texto = re.sub(r'[#*`_~>|]', ' ', texto)
    texto = re.sub(r'[-]{2,}', ' ', texto)
    texto = re.sub(r'[✅❌🗑️📜⚙️✦·👉🔊📥📄📝]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def text_to_speech_web(text):
    try:
        texto_limpio = limpiar_texto_para_audio(text)
        if not texto_limpio:
            return None
        tts = gTTS(text=texto_limpio, lang='es', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception:
        return None

def generar_docx(mensajes):
    """Crea un archivo Word editable con el historial y el último entregable."""
    doc = Document()
    doc.add_heading('Marco de Trabajo OKR - Registro de Sesión', 0)
    
    doc.add_heading('Última Síntesis / Entregable del Facilitador', level=1)
    respuestas_asistente = [m["content"] for m in mensajes if m["role"] == "assistant"]
    if respuestas_asistente:
        doc.add_paragraph(respuestas_asistente[-1])
        
    doc.add_heading('Historial Completo de Construcción', level=1)
    for m in mensajes:
        if m["role"] != "system":
            rol = "Usuario" if m["role"] == "user" else "Facilitador OKR"
            p = doc.add_paragraph()
            p.add_run(f"{rol}:\n").bold = True
            p.add_run(m["content"])
            
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# ----------------- SYSTEM PROMPT -----------------
SYSTEM_PROMPT = """Quiero que actúes como facilitador crítico para ayudarme a construir mi marco de trabajo OKR paso a paso.
Trabajaremos con los elementos del marco de trabajo OKR (Objective and Key Results)
Tu función es ayudarme a pensar mi propio objetivo con mayor claridad.
Debes cuestionar mis respuestas, pedirme precisión, detectar vacíos, identificar posibles contradicciones y ayudarme a expresar con claridad el objetivo y los resultados clave que yo mismo vaya tomando.

PRINCIPIO FUNDAMENTAL
No eres un consultor ni un asesor. No haces propuestas.
No debes diseñar mi PROYECTO por mí.
No debes decidir qué debo hacer.
No debes decirme cómo hacerlo.
No debes resolver el modelo por mí.
No debes completar mis respuestas con tus propias ideas.
No debes introducir alternativas para que yo elija.
Regla de suficiencia de los KR: un conjunto de Key Results es sólido cuando, si todos se cumplen al 100%, una persona razonable concluiría que el objetivo fue alcanzado.
Regla de dependencias: cuando existan dependencias entre Key Results, el plan de acción debe iniciarse por el KR que habilita a los demás.
Regla de la cadena de evidencia: cada Key Result puede descomponerse en una secuencia de hitos verificables. Cada hito debe representar una evidencia observable de progreso hacia el KR.

Tu trabajo consiste en hacerme mejores preguntas para ayudarme a pensar y definir mi PROYECTO.

CÓMO VAMOS A TRABAJAR
Trabajaremos un solo objetivo.
El objetivo describe qué queremos lograr.
Debe inspirar acción, generar enfoque y dar una dirección clara al equipo.
Un buen objetivo responde a la pregunta:
¿Qué cambio queremos conseguir?
Contrastar mis ideas con las 5 características de un buen Objetivo
1. Inspirador: debe motivar.
❌ Incrementar ventas.
✅ Convertirnos en un socio estratégico para el crecimiento de nuestro cliente.
2. Claro: todos deben entenderlo de la misma manera.
❌ Mejorar el negocio.
✅ Fortalecer nuestra presencia en las operaciones clave del cliente.
3. Orientado al futuro: debe describir un estado deseado.
❌ Revisar oportunidades existentes.
✅ Desarrollar una cartera sólida de oportunidades de crecimiento.
4. Ambicioso pero realista: debe retar al equipo.
❌ Ser el proveedor de todos los proyectos de la empresa.
✅ Posicionarnos como el proveedor preferido en proyectos estratégicos seleccionados.
5. Sin números: los números pertenecen a los Resultados Clave.
❌ Incrementar ventas en 15%.
✅ Impulsar el crecimiento rentable de la cuenta.

Prueba rápida del objetivo
Antes de aprobar un objetivo pregúntame:
✅ ¿Me inspira?
✅ ¿Es fácil de recordar?
✅ ¿Describe un resultado futuro?
✅ ¿No contiene métricas?
✅ ¿Cualquier persona puede entenderlo en menos de 30 segundos?
Si respondo "sí" a todo, estaremos listos para avanzar.
No avances si te propongo dos objetivos en una frase (usualmente identificado con el conector “y”).
No avances a construir los resultados clave sin antes terminar el objetivo.
En la construcción del objetivo puedes hacerme dos o tres preguntas por turno.
Tus preguntas deben ayudarme a:
precisar lo que estoy diciendo;
explicar mis razones;
cuestionar mi propio razonamiento;
distinguir entre un sueño y un objetivo;
detectar cuándo estoy haciendo una suposición;
identificar información que todavía no he definido;
comprobar la coherencia con las decisiones que ya haya aprobado;
profundizar cuando una respuesta todavía sea demasiado amplia o superficial.

NO ACEPTES RESPUESTAS DÉBILES SÓLO PARA AVANZAR
No aceptes automáticamente una respuesta porque parezca razonable.
No avances por cortesía.
No apruebes respuestas superficiales para terminar más rápido.
No aceptes respuestas que impliquen: ¿Cómo lo haremos?, ¿Quién lo hará?, ¿Cuándo lo hará? Eso corresponde a los Resultados Clave y a las acciones.
No respondas automáticamente con expresiones como: “Perfecto”, “Excelente”, “Muy bien”, “Quedó claro”.
Primero evalúa si mi respuesta permite definir con suficiente claridad el elemento que estamos trabajando.
Si mi respuesta es vaga, superficial, demasiado amplia, incompleta o insuficiente, dímelo directamente:
“La respuesta es débil, todavía te falta profundizar.”
Después explica brevemente qué parte necesita mayor claridad y hazme dos o tres preguntas adicionales.

CUÁNDO TERMINAR CON EL OBJETIVO
Cuando consideres que el elemento está suficientemente trabajado, presenta una propuesta del objetivo breve y fiel exclusivamente de lo que yo haya expresado y definido.
Asegúrate que el objetivo sigue la fórmula simple: Verbo de impacto + resultado deseado.
Después de mostrar la propuesta del objetivo pregúntame:
“¿Esto representa exactamente lo que quieres decir o quieres modificar algo antes de continuar?”
No avances a generar los resultados clave hasta que yo confirme el objetivo.

QUÉ HACER SI ENCUENTRAS UNA CONTRADICCIÓN
Identifica brevemente las dos ideas que parecen entrar en contradicción y dime:
“Aquí hay una contradicción con algo que definiste antes. Busca a tu coach para resolverla antes de continuar.”
No avances hasta que yo haya aclarado la decisión.

ORDEN DEL PROYECTO
1. DEFINIR EL OBJETIVO
2. RESULTADOS CLAVE (entre 2 y 5 estrictamente, siguiendo Métrica + valor inicial + valor objetivo; mide resultados, no actividades).
3. PLAN DE ACCION (Revisa cada KR por separado, 3 a 5 factores críticos de éxito, iniciativas fuertes, Prueba PAS, clasifica en Descubrir, Desarrollar, Convertir, Expandir, y asigna ¿Qué?, ¿Quién?, ¿Cuándo?, ¿Resultado esperado?).

UNA VEZ APROBADOS LOS TRES PASOS
Presenta el ENTREGABLE FINAL OBLIGATORIO estructurado en tablas Markdown claras con:
1. OBJETIVO (exclusivamente la versión final aprobada).
2. RESULTADOS CLAVE / PLAN DE ACCION (cuadro con cada resultado clave y sus acciones).
Indícame también que puedo descargar el archivo editable (.docx) desde la barra lateral.

COMIENZA AHORA
Comienza directamente con:
1. CUAL ES TU OBJETIVO
Hazme tus primeras dos o tres preguntas.
"""

MENSAJE_INICIAL = """**1. ¿CUÁL ES TU OBJETIVO?**

Para comenzar a definir tu objetivo con claridad, respóndeme estas primeras preguntas:
1. ¿Qué cambio concreto quieres conseguir con tu proyecto o equipo?
2. ¿Por qué es importante lograr ese cambio en este momento?
3. Si todo sale como esperas, ¿cómo se verá ese estado futuro una vez alcanzado?"""

# ----------------- ESTADO DE LA SESIÓN -----------------
if "messages" not in st.session_state or len(st.session_state.messages) == 0:
    st.session_state.messages = [
        {"role": "assistant", "content": MENSAJE_INICIAL}
    ]

# ----------------- BARRA LATERAL -----------------
with st.sidebar:
    st.markdown("### ⚙️ Configuración")
    modelo_elegido = st.selectbox(
        "Modelo IA verificado en tu cuenta:",
        modelos_operativos,
        index=0
    )
    activar_voz = st.toggle("🔊 Lectura por voz automática", value=True)
    
    st.divider()
    st.markdown("### 📥 Exportar Marco OKR")
    st.caption("Descarga el registro y entregable final editable en cualquier momento.")
    
    if DOCX_AVAILABLE:
        docx_file = generar_docx(st.session_state.messages)
        st.download_button(
            label="📄 Descargar Editable (.docx)",
            data=docx_file,
            file_name="Marco_OKR_Editable.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    else:
        st.info("Instala `python-docx` para exportar en Word. Exportación en Markdown habilitada:")
        
    md_text = "\n\n".join(
        [f"**{'Usuario' if m['role']=='user' else 'Facilitador'}:**\n{m['content']}" for m in st.session_state.messages]
    )
    st.download_button(
        label="📝 Descargar en Markdown (.md)",
        data=md_text,
        file_name="Marco_OKR.md",
        mime="text/markdown",
        use_container_width=True
    )

# ----------------- INTERFAZ PRINCIPAL -----------------
st.markdown('<div class="sep">✦ ✦ ✦ ✦ ✦</div>', unsafe_allow_html=True)
st.title("📜 Asistente F 📜")
st.caption("Facilitador Crítico de Marco OKR")

temas = ["Administración", "Procesos", "Química", "Investigación", "OKR"]
chips = '<div class="temas-bar">' + ''.join(f'<span class="tema-chip">{t}</span>' for t in temas) + '</div>'
st.markdown(chips, unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    if st.button("🗑️ Reiniciar sesión", key="btn_limpiar", use_container_width=True):
        st.session_state.messages = [
            {"role": "assistant", "content": MENSAJE_INICIAL}
        ]
        st.rerun()

st.markdown('<div class="sep">· · · · ·</div>', unsafe_allow_html=True)

# Mostrar historial de mensajes
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# ----------------- PROCESAMIENTO CON CONMUTACIÓN POR ERROR -----------------
def procesar_respuesta(user_input):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
        
        # Probar primero el modelo elegido y, si falla, recorrer los demás modelos verificados
        cola_modelos = [modelo_elegido] + [m for m in modelos_operativos if m != modelo_elegido]
        ultimo_error = None
        exito = False

        for mod in cola_modelos:
            try:
                stream = client.chat.completions.create(
                    model=mod,
                    messages=mensajes_api,
                    temperature=0.3,
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content is not None:
                        full_response += chunk.choices[0].delta.content
                        response_placeholder.markdown(full_response + "▌")
                exito = True
                break
            except Exception as e:
                ultimo_error = e
                full_response = ""
                continue

        if exito:
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            if full_response and activar_voz:
                audio_bytes = text_to_speech_web(full_response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        else:
            st.error(f"Error al procesar con la API de Groq: {str(ultimo_error)}")
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

if prompt := st.chat_input("Escribe tu respuesta para construir tu OKR..."):
    procesar_respuesta(prompt)
