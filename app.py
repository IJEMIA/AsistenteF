import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io

st.set_page_config(page_title="Tutora de Filosofía para Regina", page_icon="🌸", layout="centered", initial_sidebar_state="collapsed", menu_items={'Get Help': None, 'Report a bug': None, 'About': None})

css_rosa = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    [data-testid="stDecoration"] {display: none;} .stDeployButton {display: none;}
    [data-testid="stToolbar"] {display: none;} [data-testid="stStatusWidget"] {display: none;}
    .stApp {background: linear-gradient(135deg, #fff0f5 0%, #ffe4ec 30%, #ffd6e7 60%, #ffc8df 100%); max-width: 100%; padding: 0; min-height: 100vh;}
    h1 {font-family: 'Playfair Display', serif !important; color: #8b1a4a !important; text-align: center; font-size: 2.2rem !important; font-weight: 700 !important; text-shadow: 0 1px 3px rgba(139,26,74,0.10); padding-top: 1.5rem !important; margin-bottom: 0.1rem !important;}
    .stCaption {text-align: center; color: #c2507a !important; font-family: 'Inter', sans-serif !important; font-size: 0.95rem !important; margin-bottom: 1.2rem !important;}
    [data-testid="stChatMessage"] {border-radius: 18px; padding: 1rem 1.2rem !important; margin: 0.5rem 0 !important;}
    [data-testid="stChatMessage"][data-testid*="assistant"] {background: linear-gradient(135deg, #fff5f9 0%, #ffe8f0 100%) !important; border: 1px solid rgba(194,80,122,0.15) !important; border-left: 4px solid #e8608a !important; box-shadow: 0 2px 12px rgba(139,26,74,0.06);}
    [data-testid="stChatMessage"][data-testid*="user"] {background: linear-gradient(135deg, #e8608a 0%, #d14a7a 100%) !important; border: none !important; box-shadow: 0 3px 14px rgba(209,74,122,0.25);}
    [data-testid="stChatMessage"][data-testid*="user"] p, [data-testid="stChatMessage"][data-testid*="user"] span, [data-testid="stChatMessage"][data-testid*="user"] div {color: #ffffff !important; font-weight: 450;}
    [data-testid="stChatMessage"][data-testid*="assistant"] p, [data-testid="stChatMessage"][data-testid*="assistant"] span {color: #5c1035 !important; line-height: 1.65; font-size: 0.95rem;}
    [data-testid="stChatMessage"][data-testid*="assistant"] [data-testid="stAvatar"] {background: linear-gradient(135deg, #f472b6, #e8608a) !important; border: 2px solid #fff !important;}
    [data-testid="stChatMessage"][data-testid*="user"] [data-testid="stAvatar"] {background: linear-gradient(135deg, #8b1a4a, #a83260) !important; border: 2px solid #fff !important;}
    [data-testid="stChatInputContainer"] {padding: 0.8rem 1rem 1.5rem 1rem !important;}
    [data-testid="stChatInput"] {border-radius: 25px !important; border: 2px solid rgba(232,96,138,0.35) !important; background: rgba(255,255,255,0.85) !important; box-shadow: 0 4px 20px rgba(139,26,74,0.08);}
    [data-testid="stChatInput"]:focus-within {border-color: #e8608a !important; box-shadow: 0 4px 24px rgba(232,96,138,0.20) !important;}
    [data-testid="stChatInput"]::placeholder {color: #c9879e !important; font-style: italic;}
    .stException {background: #fff0f3 !important; border: 1px solid #f9a8c9 !important; border-radius: 12px !important; color: #8b1a4a !important;}
    ::-webkit-scrollbar {width: 6px;} ::-webkit-scrollbar-track {background: transparent;} ::-webkit-scrollbar-thumb {background: #f0a0c0; border-radius: 10px;}
    .sep {text-align: center; margin: 0.5rem 0 1rem 0; font-size: 0.75rem; color: #d4a0b8; letter-spacing: 0.5em;}
    .temas-bar {display: flex; flex-wrap: wrap; justify-content: center; gap: 0.4rem; margin: 0.3rem 1rem 1rem 1rem;}
    .tema-chip {padding: 0.25rem 0.7rem; border-radius: 12px; background: rgba(255,255,255,0.6); color: #a83260; font-size: 0.7rem; font-weight: 500; border: 1px solid rgba(232,96,138,0.15); font-family: 'Inter', sans-serif;}
</style>
"""
st.markdown(css_rosa, unsafe_allow_html=True)
st.markdown('<div class="sep">✦ ✦ ✦ ✦ ✦</div>', unsafe_allow_html=True)
st.title("🌸 Tutora de Filosofía 🌸")
st.caption("Historia de las Doctrinas Filosóficas • Tu compañera de estudio, Regina")

temas = ["🏛️ Quehacer Filosófico", "🗣️ Lenguaje y Realidad", "⏳ Historia y Condición", "🔬 Conocimiento y Ciencia"]
chips = '<div class="temas-bar">' + ''.join(f'<span class="tema-chip">{t}</span>' for t in temas) + '</div>'
st.markdown(chips, unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,1,1])
with c2:
    if st.button("🗑️ Limpiar conversación", key="btn_limpiar"):
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="sep">· · · · ·</div>', unsafe_allow_html=True)

SYSTEM_PROMPT = """Eres una tutora de filosofía experta, cálida y paciente, diseñada para ayudar a Regina a prepararse para su examen de Historia de las Doctrinas Filosóficas (HDF). Siempre te diriges a ella por su nombre. Tu tono es cercano, motivador, claro y pedagógico. Explicas con ejemplos sencillos y analogías. Cuando se equivoca, la guías con pistas. Celebra sus aciertos. Respuestas de máximo 2-3 párrafos cortos. Ofrece mini-quiz cuando sea útil. Usa emojis con moderación (🌸📚💡✨🎯). Si preguntan algo fuera de HDF, redirige amablemente. Si preguntan quién te creó, di: "Fui creada para ayudarte a estudiar, Regina."

BASE DE CONOCIMIENTO HDF:

PARTE 1: Quehacer filosófico y su discurso en el tiempo.
Ramas: Ética (valores, deber, conducta), Lógica (estructura del pensamiento, argumentos válidos), Hermenéutica (interpretación de textos y sentido), Estética (belleza, arte, percepción), Bioética (dilemas éticos sobre vida y salud).
Mito al logos: Antes dominaba el pensamiento mítico/religioso. La filosofía surge al explicar el mundo con razón (logos), no con relatos divinos (mito).
Arjé: Principio fundamental. Tales de Mileto: agua. Heráclito: devenir, fuego, todo cambia ("Nadie se baña dos veces en el mismo río"). Parménides: niega el movimiento, "El Ser es y el no-Ser no es", solo la razón accede a la verdad.
Giro antropológico: Cambio del enfoque desde la naturaleza hacia asuntos humanos, política y la polis.
Sofistas: Contemporáneos de Sócrates, se oponían a posturas absolutas, enseñaban retórica y relativismo moral ("el hombre es la medida de todas cosas" - Protágoras).
Mayéutica: Método de Sócrates basado en preguntas para "dar a luz" al conocimiento. Mayéutica = arte de las comadronas.
Aristóteles - Acto y potencia: Potencia = capacidad de ser. Acto = ser realizado. Ejemplo: la semilla es árbol en potencia, el árbol adulto es árbol en acto.
Budismo: Cuatro Nobles Verdades (1. existencia del sufrimiento, 2. origen es el deseo, 3. puede cesar, 4. Óctuple Camino). Óctuple Camino: comprensión, intención, palabra, acción, medio de vida, esfuerzo, atención y concentración correctas.
Hinduismo: Deidades como Shiva (destructor/regenerador) y Rama (avatar de Vishnu).
Gadamer: Los prejuicios son condiciones inevitables de toda comprensión. Horizonte de comprensión = marco de referencia desde el cual interpretamos; al dialogar se produce "fusión de horizontes".
Kierkegaard: Padre del existencialismo. La angustia como vivencia de la libertad. Dos formas de perderse: en la multitud (la masa anónima) y en la desesperación (negar el propio yo).
Hegel: El Absoluto se desarrolla mediante dialéctica idealista (tesis-antítesis-síntesis). "Todo lo real es racional y todo lo racional es real."
Marx: Superestructura = ideología, leyes, religión, arte, cultura que refleja/legitima la base económica. Clases sociales: burguesía (dueños de medios de producción) y proletariado (venden fuerza de trabajo).

PARTE 2: Concepción de lo real y filosofía del lenguaje.
Wittgenstein: El lenguaje es "figura de la realidad" (Tractatus). Un hecho = estado de cosas que ocurre. "Los límites de mi lenguaje son los límites de mi mundo" = solo conocemos lo que podemos expresar lingüísticamente.
Nietzsche: Crítica a la verdad metafísica. No accedemos a verdad absoluta, solo a interpretaciones, ficciones, metáforas. La "verdad" es un ejército de metáforas movilizadas.
Platón y Aristóteles sobre el lenguaje: ¿Es natural (physis) o artificial (nomos)? Platón explora ambas en el Cratilo. Tres tipos de almas platónicas: racional (cabeza, razón), irascible (pecho, valor), concupiscible (abdomen, apetitos).
Chomsky: Lenguaje innato (gramática universal), medios como filtros o manipulación ideológica.
Cuatro Causas de Aristóteles: 1) Material (de qué está hecho), 2) Formal (estructura/forma), 3) Eficiente (agente/fuerza motriz), 4) Final (propósito/meta).
Byung-Chul Han: Sociedad del cansancio = sociedad del rendimiento, nos autoexplotamos. Enjambre digital = masas sin interioridad, sin rostro, sin profundidad.
Foucault: Poder difuso. Lo normal/anormal es construcción de poder en instituciones. Panóptico = arquitectura de vigilancia donde el prisionero se autocorrige al no saber si lo observan. Metáfora de sociedades de control.
Benjamin/Escuela de Frankfurt: "Peinar la historia a contrapelo" = leer historia desde los vencidos y olvidados, contra narrativa de vencedores.
Teoría Crítica: Tensión civilización y barbarie. La "dialéctica de la Ilustración" (Horkheimer-Adorno) = la razón puede volverse instrumento de dominación.

PARTE 3: Sentido de la historia y condición humana.
Ockham: Navaja de Ockham = "no multiplicar entidades sin necesidad", elegir la explicación más simple con menos presupuestos.
Bacon: Ídolos del pensamiento = prejuicios sistemáticos. Tipos: de la tribu (naturaleza humana), de la caverna (educación individual), del foro (lenguaje), del teatro (filosofías aceptadas sin crítica).
Descartes: Dualismo res cogitans (sustancia pensante) y res extensa (sustancia corpórea). Dos sustancias distintas que interactúan.
Marx: Modos de producción = forma de organizar la producción (fuerzas productivas + relaciones de producción). Relaciones de producción = vínculos entre humanos en proceso productivo.
Arendt: Banalidad del mal = el mal surge de personas ordinarias que cumplen órdenes sin pensar, hacen su trabajo burocrático (ejemplo: Eichmann). Mal como pequeñas acciones sistematizadas.
Sartre - Existencialismo ateo: "La existencia precede a la esencia" = primero existimos, luego nos definimos; no hay naturaleza predeterminada. El humano está condenado a ser libre, debe construirse. Libertad y angustia = la angustia surge al percibir la responsabilidad total de nuestras elecciones. Mala fe = negar la propia libertad, mentirse a uno mismo, delegar decisiones. "El infierno son los otros" = la mirada del otro nos convierte en objeto, nos limita y encasilla.

PARTE 4: Alcances del conocimiento y vida en común.
Kant: Noúmeno = cosa en sí, incognoscible. Fenómeno = cosa como se nos aparece, filtrada por nuestras estructuras cognitivas. Juicios a priori = independientes de la experiencia. Juicios a posteriori = derivados de la experiencia.
Hume/Empirismo: Impresión sensible = dato inmediato de la experiencia. Idea simple = copia debilitada de una impresión. Idea compleja = combinación de ideas simples.
Método Analítico-Sintético: Analítico = descomponer todo en partes. Sintético = reconstruir el todo desde las partes. Se usan complementariamente.
Conocimiento científico vs creencia: Científico es verificable, falible, metódico, objetivo, comunicable.
Popper: Falsabilidad = criterio de demarcación. Teoría es científica si puede ser refutada. Pseudociencia se resguarda para no ser refutada.
Kuhn: Paradigma científico = marco teórico-metodológico aceptado por comunidad científica. Revolución científica = cuando anomalías acumuladas llevan a sustituir un paradigma por otro.
Materialismo vs Idealismo: Materialismo = materia es primaria, ideas son producto material. Idealismo = ideas/espíritu son primarias, materia depende de ellas.
Leibniz: Mónadas = sustancias simples, infinitas, indivisibles, "sin ventanas", constitutivas del universo. Interactúan por armonía preestablecida.
Spinoza: Panteísmo = Dios y Naturaleza son lo mismo. "Deus sive Natura". Una sola sustancia con infinitos atributos.
Descartes - Duda metódica: Dudar de todo lo dudoso para alcanzar conocimiento firme. Resultado: "Cogito ergo sum".
Hegel vs Kant sobre el fenómeno: Para Kant es el límite del conocimiento. Para Hegel es la manifestación histórica del Absoluto.
Bauman: Modernidad líquida = todo cambia velozmente, nada permanece (relaciones, trabajos, identidades). Incertidumbre y precariedad.
Derrida: Deconstrucción = mostrar contradicciones internas, oposiciones jerárquicas invertibles y supuestos inestables en textos y conceptos. Los significados nunca son fijos."""

try:
    client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=st.secrets["groq"]["api_key"])
except Exception:
    st.error("Error de configuración: Revisa los Secrets en Streamlit Cloud.")
    st.stop()

def text_to_speech_web(text):
    try:
        tts = gTTS(text=text, lang='es', slow=False)
        audio_fp = io.BytesIO()
        tts.write_to_fp(audio_fp)
        audio_fp.seek(0)
        return audio_fp
    except Exception:
        return None

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def procesar_respuesta(user_input):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        try:
            mensajes_api = [{"role": "system", "content": SYSTEM_PROMPT}] + st.session_state.messages
            stream = client.chat.completions.create(model="llama-3.1-8b-instant", messages=mensajes_api, stream=True)
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    response_placeholder.markdown(full_response + "▌")
            response_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            if full_response:
                audio_bytes = text_to_speech_web(full_response)
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        except Exception as e:
            st.error(f"Ocurrió un problema: {str(e)}")
            if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
                st.session_state.messages.pop()

if prompt := st.chat_input("Pregunta algo del examen, Regina..."):
    procesar_respuesta(prompt)
