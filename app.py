import streamlit as st
from openai import OpenAI
from gtts import gTTS
import io

st.set_page_config(
    page_title="Asistente F - Tutor de Historia", 
    page_icon="📜", 
    layout="centered", 
    initial_sidebar_state="collapsed", 
    menu_items={'Get Help': None, 'Report a bug': None, 'About': None}
)

# Estilo personalizado adaptado a temática histórica (tonos sepia y terracota)
css_historia = """
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
    [data-testid="stChatMessage"][data-testid*="assistant"] p, [data-testid="stChatMessage"][data-testid*="assistant"] span {color: #36200b !important; line-height: 1.65; font-size: 0.95rem;}
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
st.markdown(css_historia, unsafe_allow_html=True)
st.markdown('<div class="sep">✦ ✦ ✦ ✦ ✦</div>', unsafe_allow_html=True)
st.title("📜 Asistente F 📜")
st.caption("Tu compañero de viaje por la Historia Universal • Aprende a tu ritmo")

temas = ["🏛️ Edad Antigua", "🏰 Edad Media", "🎨 Edad Moderna", "🏭 Edad Contemporánea"]
chips = '<div class="temas-bar">' + ''.join(f'<span class="tema-chip">{t}</span>' for t in temas) + '</div>'
st.markdown(chips, unsafe_allow_html=True)

c1, c2, c3 = st.columns([1,1,1])
with c2:
    if st.button("🗑️ Limpiar conversación", key="btn_limpiar"):
        st.session_state.messages = []
        st.rerun()

st.markdown('<div class="sep">· · · · ·</div>', unsafe_allow_html=True)

SYSTEM_PROMPT = """Eres el Asistente F, un experto en Historia Universal sumamente amable, paciente, entusiasta y didáctico. Tu misión es hacer que la historia sea accesible, apasionante y fácil de comprender para cualquier estudiante. 

Pautas de comportamiento:
- Mantén siempre un tono cálido, respetuoso, motivador y acogedor.
- Explica los sucesos históricos como relatos interesantes, contextualizando las causas, desarrollos y consecuencias de manera sencilla y amena.
- Utiliza analogías del mundo actual para explicar conceptos complejos (como alianzas políticas, economía o conflictos).
- Si el usuario comete un error histórico, corrígelo con amabilidad y educación, ofreciendo datos o pistas para ayudarle a entender.
- Mantén respuestas breves y estructuradas (máximo 2 a 3 párrafos cortos por respuesta).
- Incorpora emojis temáticos con moderación para hacer la lectura fluida (📜🏛️⚔️🌍🎨👑).
- Puedes proponer breves preguntas o mini-quizzes al final de tus explicaciones para afianzar el aprendizaje.
- Si te preguntan quién te creó, responde amablemente: "Fui diseñado como Asistente F para acompañarte a explorar los grandes acontecimientos y procesos de la historia."
"""

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

if prompt := st.chat_input("Pregúntame cualquier duda sobre historia..."):
    procesar_respuesta(prompt)
