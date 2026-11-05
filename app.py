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
    [data-
