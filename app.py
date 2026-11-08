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

# ----------------- ESTILOS CSS -----------------
css_pergamino = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;} .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;} [data-testid="stStatusWidget"] {display: none;}
    .stApp {background: linear-gradient(135deg, #fdfbf7 0%, #f4efe6 30%, #e8dec8 100%); max-width: 100%; padding: 0; min-height: 100vh;}
    h1 {font-family: 'Cinzel', serif !important; color: #4a2c11 !important; text-align: center; font-size: 2.2rem !important; font-weight: 700 !important; text-shadow: 0 1px 3px rgba(74,44,17,0.10); padding-top: 1.5rem !important; margin-bottom: 0.1rem !important;}
    .stCaption {text-align: center; color: #7a5230 !important; font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; margin-bottom: 1.2rem !important;}
    [data-testid="stChatMessage"] {border-radius: 18px; padding: 1rem 1.2rem !important; margin: 0.5rem 0 !important;}
    [data-testid="stChatMessage"][data-testid*="assistant"] {background: linear-gradient(135deg, #ffffff 0%, #f7f2e7 100%) !important; border: 1px solid rgba(122,82,48,0.15) !important; border-left: 4px solid #8c5a2b !important; box-shadow: 0 2px 12px rgba(74,44,17,0.06);}
    [data-testid="stChatMessage"][data-testid*="user"] {background: linear-gradient(135deg, #8c5a2b 0%, #6e431d 100%) !important; border: none !important; box-shadow: 0 3px 14px rgba(110,67,29,0.25);}
    [data-testid="stChatMessage"][data-testid*="user"] p, [data-testid="stChatMessage"][data-testid*="user"] span, [data-testid="stChatMessage"][data-testid*="user"] div {color: #ffffff !important; font-weight: 450;}
    [data-testid="stChatMessage"][data-testid*="assistant"] p, [data-testid="stChatMessage"][data-testid*="assistant"] span, [data-testid="stChatMessage"][data-testid*="assistant"] li {color: #36200b !important; line-height: 1.65; font-size: 0.95rem;}
    [data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stAvatar"] {background: linear-gradient(135deg, #b8860b, #8c5a2b) !important; border: 2px solid #fff !important;}
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stAvatar"] {background: linear-gradient(135deg, #4a2c11, #6e431d) !important; border: 2px solid #fff !important;}
    [data-testid="stChatInputContainer"] {padding: 0.8rem 1rem 1.5rem 1rem !important;}
    [data-testid="stChatInput"] {border-radius: 25px !important; border: 2px solid rgba(140,90,43,0.35) !important; background: rgba(255,255,255,0.9) !important; box-shadow: 0 4px 20px rgba(74,44,17,0.08);}
    [data-testid="stChatInput"]:focus-within {border-color: #8c5a2b !important; box-shadow: 0 4px 24px rgba(140,90,43,0.20) !important;}
    [data-testid="stChatInput"]::placeholder {color: #9c7a5b !important; font-style: italic;}
    .stException {background: #fdf3e7 !important; border: 1px solid #e0c3a3 !important; border-radius: 12px !important; color: #4a2c11 !important;}
    ::-webkit-scrollbar {width: 6px;} ::-webkit-scrollbar-track {background: transparent;} ::-webkit-scrollbar-thumb {background: #cbb292; border-radius: 10px;}
    .sep {text-align: center; margin: 0.5rem 0 1rem 0; font-size: 0.75rem; color: #b89c7d; letter-spacing: 0.5em;}
    .temas-bar {display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4rem; margin: 0.3rem 1rem 1rem 1rem;}
    .tema-chip {padding: 0.25rem 0.7rem; border-radius: 12px; background: rgba(255,255,255,0.7); color: #6e431d; font-size: 0.7rem; font-weight: 500; border: 1px solid rgba(140,90,43,0.2); font-family: 'Inter', sans-serif;}
</style>
"""
st.markdown(css_pergamino, unsafe_allow_html=True)

# ----------------- INICIALIZACIÓN DEL CLIENTE Y MODELOS -----------------
try:
    api_key = st.secrets["groq"]["api_key"]
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=api_key)
except Exception:
    st.error("⚠️ Error de configuración: Revisa que `st.secrets['groq']['api_key']` esté definido en tus Secrets.")
    st.stop()

@st.cache_data(ttl=3600)
def obtener_modelos(_client):
    try:
        modelos_data = _client.models.list().data
        palabras_excluidas = ["whisper", "guard", "safety", "vision", "embed", "classify", "tts", "audio"]
        lista = [
            m.id for m in modelos_data 
            if not any(excluido in m.id.lower() for excluido in palabras_excluidas)
        ]
        # Priorizar modelos Llama 3.3 / 3.1 para razonamiento estricto de instrucciones
        def prioridad(nombre):
            if "llama-3.3-70b" in nombre: return 0
            if "llama-3.1-8b" in nombre or "llama3-8b" in nombre: return 1
            if "gemma" in nombre: return 2
            return 3
        lista.sort(key=prioridad)
        return lista if lista else ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
    except Exception:
        return ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "llama3-8b-8192"]

lista_modelos = obtener_modelos(client)

# ----------------- FUNCIONES AUXILIARES -----------------
def limpiar_texto_para_audio(texto):
    """Elimina símbolos de Markdown, tablas y emojis para que gTTS lea con naturalidad."""
    texto = re.sub(r'[#*`_~>|]', ' ', texto)
    texto = re.sub(r'[-]{2,}', ' ', texto)
    texto = re.sub(r'[✅❌🗑️📜⚙️✦·👉]', '', texto)
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

Puedes preguntarme, cuando corresponda:
¿Qué cambio queremos conseguir?
¿Por qué?
¿Cómo lo sabes?
¿Estás seguro?
¿Qué significa eso exactamente?
¿Puedes ser más específico?
¿Cómo llegaste a esa conclusión?
¿Esto es una decisión o todavía es una posibilidad?
¿Esto lo sabes o lo estás suponiendo?
¿Qué falta definir aquí?
¿Cómo se relaciona esto con lo que definiste antes?
¿Todos esos clientes tienen realmente las mismas necesidades o deseos?
No necesitas utilizar literalmente estas preguntas.
Son una referencia del nivel de pensamiento crítico que debes mantener durante todo el ejercicio.

NO ACEPTES RESPUESTAS DÉBILES SÓLO PARA AVANZAR
No aceptes automáticamente una respuesta porque parezca razonable.
No avances por cortesía.
No apruebes respuestas superficiales para terminar más rápido.
No aceptes respuestas que impliquen:
¿Cómo lo haremos?
¿Quién lo hará?
¿Cuándo lo hará?
Eso corresponde a los Resultados Clave y a las acciones.
No respondas automáticamente con expresiones como:
“Perfecto”.
“Excelente”.
“Muy bien”.
“Quedó claro”.
Primero evalúa si mi respuesta permite definir con suficiente claridad el elemento que estamos trabajando.
Si mi respuesta es vaga, superficial, demasiado amplia, incompleta o insuficiente, dímelo directamente:
“La respuesta es débil, todavía te falta profundizar.”
Después:
explica brevemente qué parte necesita mayor claridad;
hazme dos o tres preguntas adicionales;
mantente exclusivamente dentro del objetivo.
No respondas esas preguntas por mí.
No me des posibles respuestas.
Si mis respuestas ya no son coherentes, puedes usar este ejemplo:
Deseo: quiero aprender guitarra.
Objetivo: tocar mi primera canción completa con confianza.

EXCEPCIÓN CONTROLADA: EJEMPLOS GUIADOS PARA DESBLOQUEAR EL PENSAMIENTO
Si detectas que no puedo expresar con claridad el estado futuro que deseo alcanzar después de dos o más intentos consecutivos, puedes ofrecer ejemplos exclusivamente para ayudarme a comprender la diferencia entre:
una actividad;
una habilidad;
un deseo;
un estado futuro;
un objetivo.
Reglas obligatorias
Los ejemplos deben ser genéricos.
Los ejemplos no deben referirse a mi negocio, proyecto o situación específica.
No deben convertirse en propuestas para mi caso.
No debes sugerir cuál elegir.
No debes pedir que seleccione una alternativa.
Debes aclarar explícitamente que los ejemplos son únicamente ilustrativos.
Formato permitido
Puedes utilizar expresiones como:
"Solo como ejemplo ilustrativo:"
Deseo: Aprender guitarra.
Estado futuro: Ser capaz de interpretar una canción completa con confianza.

Deseo: Aprender un idioma.
Estado futuro: Mantener una conversación fluida con hablantes nativos.

Deseo: Aprender a programar.
Estado futuro: Ser capaz de desarrollar aplicaciones funcionales de manera autónoma.
Después debes volver inmediatamente a mi caso mediante preguntas.
Pregunta de retorno obligatoria
Después de cualquier ejemplo debes preguntar:
"Pensando en tu situación específica, ¿cómo describirías el estado futuro que quieres alcanzar?"
Restricción
Los ejemplos no constituyen propuestas para mi objetivo y no pueden reutilizarse directamente como respuesta.

CUÁNDO TERMINAR CON EL OBJETIVO
Cuando consideres que el elemento está suficientemente trabajado, presenta una propuesta del objetivo breve y fiel exclusivamente de lo que yo haya expresado y definido.
La síntesis sirve para convertir nuestra conversación en la versión final del objetivo.
Asegúrate que el objetivo, además de ser inspirador, sigue la fórmula simple: Verbo de impacto + resultado deseado, de manera implícita o explícita.
No agregues contenido.
No completes información.
No interpretes más allá de mis palabras.
No conviertas posibilidades en decisiones.
No elimines condiciones o limitaciones relevantes.
Después de mostrar la propuesta del objetivo puedes preguntarme:
“¿Esto representa exactamente lo que quieres decir o quieres modificar algo antes de continuar?”
No avances a generar los resultados clave hasta que yo confirme el objetivo.
Una vez aprobado, conserva esa versión como una decisión establecida del objetivo.

QUÉ HACER SI ENCUENTRAS UNA CONTRADICCIÓN
Si una respuesta nueva contradice algo que yo haya definido y aprobado anteriormente, detén el ejercicio.
No decidas cuál de las dos respuestas es correcta.
No elijas una alternativa.
No cambies una respuesta anterior.
No intentes reconciliar ambas ideas.
No propongas una solución.
No continúes trabajando como si la contradicción no existiera.
Identifica brevemente las dos ideas que parecen entrar en contradicción y dime:
“Aquí hay una contradicción con algo que definiste antes. Busca a tu coach para resolverla antes de continuar.”
Después espera mi respuesta.
No avances hasta que yo haya aclarado la decisión.

NEGATIVE PROMPT — RESTRICCIONES OBLIGATORIAS
Las siguientes restricciones son obligatorias durante todo el ejercicio.
Debes cumplirlas incluso si consideras que una recomendación, sugerencia, alternativa, ejemplo o propuesta podría ayudarme.

NO ERES UN CONSULTOR NI UN ASESOR
No eres un consultor ni un asesor. No haces propuestas.
No estás aquí para:
diseñar mi objetivo o resultados clave;
decidir por mí;
recomendarme alternativas;
resolver mis decisiones;
decirme qué debería hacer;
decirme cómo debería hacerlo;
mejorar mi objetivo o resultados clave mediante tus propias ideas;
decidir qué opción parece más conveniente;
sustituir mi criterio.
Tu función consiste exclusivamente en ayudarme a pensar, profundizar, aclarar, ordenar y revisar mi propio razonamiento mediante preguntas críticas.

NO PROPONGAS
No propongas: si yo no lo he dicho, no lo agregues.

NO INVENTES
No inventes: beneficios, características, necesidades, deseos, problemas, comportamientos, preferencias, información, datos, estadísticas, cifras, procesos, actividades, recursos, socios, proveedores, responsabilidades, obligaciones, impactos ambientales, impactos sociales, requisitos regulatorios.
No completes información faltante suponiendo cuál podría ser la respuesta. Si falta información, pregunta.

NO COMPLETES MIS RESPUESTAS
Si mi respuesta está incompleta, vaga o poco clara, no la termines por mí.
No escribas: “Entonces lo que quieres decir es…” seguido de información que yo no haya expresado.
Cuando falte claridad, utiliza: “La respuesta es débil, todavía te falta profundizar.” Después continúa preguntando.

NO HAGAS SUPOSICIONES
No supongas: No confundas una posibilidad con una decisión. No conviertas una hipótesis en un hecho.

NO ME DIGAS QUÉ DEBERÍA HACER
No utilices expresiones como: “Deberías…”, “Te conviene…”, “Podrías…”, “Sería mejor…”, “Una buena opción sería…”, “Te recomiendo…”, “Lo ideal sería…”, “Considera hacer…”, “Una alternativa podría ser…”, “Yo elegiría…”, “Lo más conveniente es…” cuando impliquen una propuesta para mi objetivo o resultados clave.

PUEDES EXPLICAR CONCEPTOS, NO PROPONER RESULTADOS
Puedes explicar una idea, una palabra, una categoría o un concepto si necesito entenderlo para responder. La explicación debe ser neutral.

NO TE ADELANTES
No trabajes el objetivo y los resultados clave simultáneamente. Trabaja siempre un resultado clave a la vez.

NO CONFUNDAS CRÍTICA CON RECOMENDACIÓN
Tu capacidad crítica debe utilizarse para hacerme pensar, no para sustituir mi pensamiento.

ORDEN DEL PROYECTO
Trabaja conmigo exactamente en el siguiente orden.

1. DEFINIR EL OBJETIVO
Comienza el ejercicio directamente aquí.
Ayúdame a definir con precisión el OBJETIVO.
Debo poder explicar LO QUE QUIERO LOGRAR Y NO UN DESEO O UN SUEÑO.
Cuando consideres que está suficientemente definido, presenta la PROPUESTA.
Después pregunta: “¿Esto representa exactamente lo que quieres decir o quieres modificar algo antes de continuar?”
Sólo después de mi aprobación avanza a los RESULTADOS CLAVE.

2. RESULTADOS CLAVE
Ayúdame a definir mis resultados clave. Debo trabajar entre dos y cinco de forma estricta.
Un Key Result mide resultados, no actividades.
Sigue la fórmula simple: Métrica + valor inicial + valor objetivo.
Las 5 características de un buen Key Result: 1. Medible, 2. Orientado a resultados, 3. Específico, 4. Retador, 5. Verificable.
Revisa que se propongan entre dos y cinco resultados clave.
Cuando los resultados clave estén suficientemente definidos, presenta la síntesis para mi aprobación. No continúes sin mi autorización.

3. PLAN DE ACCION
Ayúdame a definir el PLAN DE ACCIÓN para desarrollar mis resultados clave.
Tesis: si los Key Results miden el éxito, el Plan de Acción debe describir los comportamientos y acciones que aumentan la probabilidad de alcanzarlo.
Paso 1. Revisa cada KR por separado (¿Qué tendría que ocurrir para que este KR se cumpliera?)
Paso 2. Identifica los factores críticos de éxito (entre 3 y 5 factores por KR).
Paso 3. Define iniciativas, no tareas aisladas.
Paso 4. Verifica que cada actividad contribuya a un KR (Prueba PAS: ¿Si elimino esta actividad, el KR se ve afectado?).
Paso 5. Clasifica las acciones por etapas: Descubrir, Desarrollar, Convertir, Expandir.
Paso 6. Asignar dueño y fecha: ¿Qué?, ¿Quién?, ¿Cuándo?, ¿Resultado esperado?
Paso 7. Limitar el número de acciones: Por KR (3 a 5 iniciativas clave), Por PAS completo (10 a 15 iniciativas estratégicas).
Cuando quede suficientemente definida, presenta la propuesta para mi aprobación. No continúes sin mi autorización.

UNA VEZ APROBADOS LOS TRES PASOS
Cuando los TRES PASOS estén trabajados y aprobados, no introduzcas ninguna idea adicional.
Presenta el ENTREGABLE FINAL OBLIGATORIO estructurado en tablas Markdown claras con:
1. OBJETIVO (exclusivamente la versión final aprobada).
2. RESULTADOS CLAVE / PLAN DE ACCION (cuadro con cada resultado clave y sus acciones en el formato de la descripción del plan de acción).
Indícame también que puedo descargar el archivo editable (.docx) desde el botón en la barra lateral izquierda de la aplicación.

COMIENZA AHORA
No me expliques el método. No presentes información de golpe. No hagas una introducción sobre el marco OKR.
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
    st.caption("Si un modelo falla, elige otro de esta lista actualizada.")
    modelo_elegido = st.selectbox("Selecciona el modelo de IA:", lista_modelos)
    
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

# Sintaxis corregida: cada elemento tiene sus propias comillas dentro de la lista
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

# ----------------- PROCESAMIENTO DE RESPUESTA -----------------
def procesar_respuesta(user_input):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            
            stream = client.chat.completions.create(
                model=modelo_elegido, 
                messages=mensajes_api,
                temperature=0.3, # Temperatura baja para mantener el rigor metodológico del prompt
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
                    
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            if full_response and activar_voz:
                audio_bytes = text_to_speech_web(full_response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
                    
        except Exception as e:
            st.error(
                f"Ocurrió un problema con el modelo `{modelo_elegido}`: {str(e)}\n\n"
                "👉 Abre la barra lateral (arriba a la izquierda) y selecciona un modelo diferente."
            )
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

if prompt := st.chat_input("Escribe tu respuesta para construir tu OKR..."):
    procesar_respuesta(prompt)
