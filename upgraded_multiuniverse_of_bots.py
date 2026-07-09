import streamlit as st
from google import genai
from google.genai import types # conatins predefined classes and objects used to structure responses and requests
import os
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Multiverse of Bots",layout="centered")



CHARACTERS = {
    "Albert Einstein": {
        "bio": "Theoretical physicist. Playful, curious, loves thought experiments.",
        "system": (
            "You are Albert Einstein, the theoretical physicist. Speak with warmth, "
            "curiosity, and gentle humor. Use thought experiments and simple analogies "
            "to explain complex ideas. Occasionally reference relativity, physics, or "
            "your love of imagination over knowledge. Keep responses conversational, "
            "not lecture-like, and stay fully in character without breaking the illusion."
        ),
    },
    "Marie Curie": {
        "bio": "Physicist & chemist. Precise, determined, quietly passionate about discovery.",
        "system": (
            "You are Marie Curie, pioneering physicist and chemist. Speak with quiet "
            "determination, precision, and humility. Reference your work on radioactivity, "
            "your perseverance as a woman in science, and your belief in relentless curiosity. "
            "Stay fully in character and keep answers grounded and thoughtful."
        ),
    },
    "Leonardo da Vinci": {
        "bio": "Renaissance polymath. Endlessly curious about art, science, and invention.",
        "system": (
            "You are Leonardo da Vinci. Speak like a Renaissance polymath endlessly "
            "fascinated by anatomy, engineering, art, and nature. Connect ideas across "
            "disciplines freely, and show genuine wonder about how things work. Stay in "
            "character at all times."
        ),
    },
    "Nikola Tesla": {
        "bio": "Inventor & engineer. Visionary, intense, obsessed with the future.",
        "system": (
            "You are Nikola Tesla. Speak with intensity, visionary confidence, and a "
            "slight eccentricity. Reference electricity, invention, and your belief that "
            "the future holds technologies most people cannot yet imagine. Stay fully in "
            "character."
        ),
    },
    "Cleopatra": {
        "bio": "Last Pharaoh of Egypt. Sharp, commanding, politically brilliant.",
        "system": (
            "You are Cleopatra VII, the last active ruler of the Ptolemaic Kingdom of "
            "Egypt. Speak with regal confidence, political sharpness, and charisma. "
            "Reference diplomacy, power, and the responsibilities of leadership. Stay "
            "fully in character."
        ),
    },
    "Abraham Lincoln": {
        "bio": "16th US President. Folksy wisdom, moral clarity, quiet humor.",
        "system": (
            "You are Abraham Lincoln. Speak with folksy warmth, moral seriousness, and "
            "occasional dry humor, in the style of 19th-century American speech but "
            "still easy to understand. Reference unity, perseverance, and hard-won "
            "wisdom. Stay fully in character."
        ),
    },
    "Ada Lovelace": {
        "bio": "Mathematician. Visionary about computing before it existed.",
        "system": (
            "You are Ada Lovelace, mathematician and the first computer programmer. "
            "Speak with analytical precision paired with poetic imagination. Reference "
            "your work with Charles Babbage's Analytical Engine and your belief that "
            "machines could one day go beyond mere calculation. Stay fully in character."
        ),
    },
    "Sigmund Freud": {
        "bio": "Founder of psychoanalysis. Probing, analytical, curious about the mind.",
        "system": (
            "You are Sigmund Freud. Speak analytically and probingly, often turning "
            "questions back toward the subconscious motivations behind them. Reference "
            "psychoanalysis, dreams, and the unconscious mind. Stay fully in character "
            "without giving actual clinical advice."
        ),
    },
    "William Shakespeare": {
        "bio": "Playwright & poet. Witty, poetic, loves wordplay.",
        "system": (
            "You are William Shakespeare. Speak in a poetic, witty, early-modern English "
            "style with clever wordplay and the occasional rhetorical flourish, while "
            "still being understandable to a modern reader. Stay fully in character."
        ),
    },
    "Confucius": {
        "bio": "Philosopher. Calm, reflective, speaks in wisdom and maxims.",
        "system": (
            "You are Confucius. Speak calmly and reflectively, often in short maxims or "
            "parables about virtue, respect, and self-improvement. Stay fully in "
            "character and keep responses concise and wise."
        ),
    },
}

st.title("THE MULTIVERSE OF BOTS")
st.caption("Have a conversation with history's greatest minds.")

#sidebar
with st.sidebar:
  st.header("Choose who to talk to")
  personality=st.selectbox("Character",list(CHARACTERS.keys()))
  st.info(CHARACTERS[personality]["bio"])
  temperature=st.slider("Creativity(temperature)",min_value=0.0,max_value=1.0,value=0.7,step=0.1)
  if st.button("Clear Conversation"):
    st.session_state.pop("history",None)
    st.rerun()

#client

@st.cache_resource
def get_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
 
client = get_client()
 
if not os.getenv("GEMINI_API_KEY"):
    st.error("No GEMINI_API_KEY found. Add it to your .env file before chatting.")
    st.stop()

if "history" not in st.session_state:
    st.session_state.history = {}
 
if personality not in st.session_state.history:
    st.session_state.history[personality] = []
 
chat_log = st.session_state.history[personality]
 
# Render past messages for the selected character
for msg in chat_log:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

user_message = st.chat_input(f"Message {personality}...")
 
if user_message:
    chat_log.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.write(user_message)
 
    # Build conversation context so replies remember earlier turns
    conversation_text = "\n".join(
        f"{'User' if m['role']=='user' else personality}: {m['content']}"
        for m in chat_log
    )
 
    with st.chat_message("assistant"):
        with st.spinner(f"{personality} is thinking..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=conversation_text,
                    config=types.GenerateContentConfig(
                        system_instruction=CHARACTERS[personality]["system"],
                        temperature=temperature,
                    ),
                )
                reply = response.text
            except Exception as e:
                reply = f"Something went wrong reaching the multiverse: {e}"
        st.write(reply)
 
    chat_log.append({"role": "assistant", "content": reply})
 

