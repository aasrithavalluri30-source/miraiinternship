import streamlit as st
from google import genai
from google.genai import types
import requests
import json
import base64
import asyncio
import edge_tts
import io
import os
from dotenv import load_dotenv

# .env lives in the SAME folder as app.py
ENV_PATH = ".env"
loaded = load_dotenv(dotenv_path=ENV_PATH)
if not loaded:
    print(f"⚠️ Warning: no .env file found at '{ENV_PATH}'. Check ENV_PATH in app.py.")

# ============================================================
# PAGE CONFIG (must be the first Streamlit command)
# ============================================================
st.set_page_config(page_title="AI Visual Novel", layout="wide")

# ============================================================
# CUSTOM BACKGROUND
# ============================================================
BACKGROUND_IMAGE_PATH = "background.png"

def set_background(image_path):
    """Reads a local image and injects it as the app's CSS background."""
    try:
        with open(image_path, "rb") as f:
            data = f.read()
        encoded = base64.b64encode(data).decode()

        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/png;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            /* make the top Streamlit header transparent so the background shows through */
            [data-testid="stHeader"] {{
                background-color: rgba(0, 0, 0, 0);
            }}
            /* translucent panel behind text so it stays readable */
            .block-container {{
                background-color: rgba(0, 0, 0, 0.55);
                padding: 2rem;
                border-radius: 12px;
            }}
            /* apply the same background image to the sidebar */
            [data-testid="stSidebar"] {{
                background-image: url("data:image/png;base64,{encoded}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
            }}
            /* translucent panel inside the sidebar so text stays readable */
            [data-testid="stSidebar"] > div:first-child {{
                background-color: rgba(0, 0, 0, 0.55);
                padding: 1rem;
                border-radius: 12px;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
    except FileNotFoundError:
        st.warning(f"Background image '{image_path}' not found — using default background.")

set_background(BACKGROUND_IMAGE_PATH)

# ============================================================
# PHASE 1: GEMINI CLIENT (cached so it's not rebuilt every rerun)
# ============================================================
GEMINI_API_KEY = os.getenv("gemini_new_key")
GEMINI_MODEL = "gemini-2.5-flash"

@st.cache_resource
def get_gemini_client():
    if not GEMINI_API_KEY:
        st.error("gemini_new_key not found. Make sure it's set in your .env file.")
        st.stop()
    client = genai.Client(api_key=GEMINI_API_KEY)
    return client

client = get_gemini_client()

# ============================================================
# SIDEBAR: STORY SETTINGS
# ============================================================
st.sidebar.title("📖 Story Settings")

genre = st.sidebar.selectbox(
    "Story Genre",
    [
        "Fantasy", "Sci-Fi", "Horror", "Mystery", "Cyberpunk", "Post-Apocalyptic",
        "Romance", "Comedy", "Thriller", "Steampunk", "Historical Fiction",
        "Superhero", "Noir Detective", "Fairy Tale", "Space Opera",
        "Survival", "Slice of Life", "Dark Fantasy", "Adventure", "Western"
    ]
)

art_style = st.sidebar.selectbox(
    "Art Style",
    [
        "Anime", "Watercolor", "Pixel Art", "Realistic", "Comic Book", "Studio Ghibli",
        "Oil Painting", "Cyberpunk Neon", "Charcoal Sketch", "Low Poly 3D",
        "Vaporwave", "Dark Fantasy Art", "Concept Art", "Claymation",
        "Flat Vector Illustration", "Gothic", "Ink Wash", "Retro 80s",
        "Photorealistic CGI", "Storybook Illustration"
    ]
)

st.sidebar.divider()

# ============================================================
# SIDEBAR: VOICE SETTINGS (edge-tts)
# ============================================================
st.sidebar.subheader("🎙️ Narration Voice")

# A handful of edge-tts voices spanning different genders/accents.
# Full list: run `edge-tts --list-voices` in a terminal to see all ~300+.
VOICE_OPTIONS = {
    "Female (US)": "en-US-AriaNeural",
    "Male (US)": "en-US-GuyNeural",
    "Female (UK)": "en-GB-SoniaNeural",
    "Male (UK)": "en-GB-RyanNeural",
    "Female (Australian)": "en-AU-NatashaNeural",
    "Male (Australian)": "en-AU-WilliamNeural",
    "Female (Indian)": "en-IN-NeerjaNeural",
    "Male (Indian)": "en-IN-PrabhatNeural",
}

voice_label = st.sidebar.selectbox("Voice", list(VOICE_OPTIONS.keys()))
selected_voice = VOICE_OPTIONS[voice_label]

speed_percent = st.sidebar.slider(
    "Narration Speed", min_value=-50, max_value=50, value=0, step=10,
    help="0 = normal speed. Negative = slower. Positive = faster."
)
# edge-tts expects rate as a signed percentage string, e.g. "+20%" or "-30%"
speed_rate = f"{'+' if speed_percent >= 0 else ''}{speed_percent}%"

st.sidebar.divider()

# ============================================================
# SIDEBAR: SESSION HISTORY
# ============================================================
st.sidebar.subheader("📜 Session History")
if "history" in st.session_state and st.session_state.history:
    for i, turn in enumerate(st.session_state.history, start=1):
        preview = turn["story_text"][:60] + ("..." if len(turn["story_text"]) > 60 else "")
        with st.sidebar.expander(f"Turn {i}"):
            st.write(turn["story_text"])
else:
    st.sidebar.caption("No story turns yet.")

# ============================================================
# SIDEBAR: CLEAR CONVERSATION
# ============================================================
if st.sidebar.button("🗑️ Clear Conversation", type="secondary"):
    st.session_state.chat = None
    st.session_state.history = []
    st.session_state.current_options = []
    st.session_state.story_started = False
    st.rerun()

# ============================================================
# SESSION STATE INITIALIZATION
# ============================================================
if "chat" not in st.session_state:
    st.session_state.chat = None
if "history" not in st.session_state:
    st.session_state.history = []
if "current_options" not in st.session_state:
    st.session_state.current_options = []
if "story_started" not in st.session_state:
    st.session_state.story_started = False

# ============================================================
# PHASE 2: STRUCTURED JSON ENGINE
# ============================================================
def build_system_prompt(genre, art_style):
    """Instructs Gemini to ALWAYS reply with strict JSON, nothing else."""
    return f"""
You are the narrative engine for a {genre} visual novel, illustrated in a {art_style} art style.

RULES:
- You must respond ONLY with a single valid JSON object. No markdown, no code fences, no commentary.
- The JSON object must have exactly these three keys:
  1. "story_text": a vivid narrative paragraph (4-6 sentences) continuing the story.
  2. "image_prompt": a highly detailed prompt (art style, lighting, composition, mood)
     describing the current scene, ready to send to an image generation API.
  3. "options": a list of 2 to 3 short, distinct strings describing what the player can do next.

Example format:
{{"story_text": "...", "image_prompt": "...", "options": ["Option A", "Option B"]}}
"""

def parse_gemini_json(raw_text):
    """
    Gemini sometimes wraps JSON in ```json ... ``` fences even when told not to.
    Strip those defensively, then parse. Returns None on failure instead of crashing.
    """
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        cleaned = cleaned.replace("json", "", 1).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None

# ============================================================
# PHASE 4: IMAGE GENERATION (Pollinations)
# ============================================================
def generate_image(image_prompt):
    """
    Sends the prompt to Pollinations and returns raw image bytes.
    Returns None (instead of crashing) if the API is slow/down.
    """
    try:
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(image_prompt)}"
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException:
        st.toast("🖼️ Image server is busy, skipping visual...")
        return None

# ============================================================
# PHASE 4: TEXT-TO-SPEECH (edge-tts)
# ============================================================
async def _edge_tts_generate(text, voice, rate):
    """Async helper: streams TTS audio bytes from edge-tts into memory."""
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes

def generate_audio(story_text, voice=selected_voice, rate=speed_rate):
    """
    Converts story_text to speech using edge-tts and returns an in-memory
    MP3 buffer. Returns None if TTS fails, instead of crashing the app.
    """
    try:
        audio_bytes = asyncio.run(_edge_tts_generate(story_text, voice, rate))
        if not audio_bytes:
            raise ValueError("edge-tts returned no audio data")
        audio_buffer = io.BytesIO(audio_bytes)
        audio_buffer.seek(0)
        return audio_buffer
    except Exception as e:
        st.toast("🔇 Narration failed, continuing without audio...")
        return None

# ============================================================
# TURN ENGINE — sends a message to Gemini and builds one story turn
# ============================================================
def take_turn(user_message):
    with st.spinner("The story is unfolding..."):
        try:
            response = st.session_state.chat.send_message(user_message)
            raw_text = response.text
        except Exception:
            st.toast("⚠️ Story engine hiccupped, please try again...")
            return

        parsed = parse_gemini_json(raw_text)
        if parsed is None:
            st.toast("⚠️ Couldn't parse the story response, please try again...")
            return

        story_text = parsed.get("story_text", "")
        image_prompt = parsed.get("image_prompt", "")
        options = parsed.get("options", [])

        image_bytes = generate_image(image_prompt) if image_prompt else None
        audio_buffer = generate_audio(story_text) if story_text else None

        st.session_state.history.append({
            "story_text": story_text,
            "image_bytes": image_bytes,
            "audio_buffer": audio_buffer,
        })
        st.session_state.current_options = options

# ============================================================
# MAIN UI
# ============================================================
st.title("📖 AI-Powered Visual Novel")
st.caption(f"Genre: {genre} · Art Style: {art_style} · Voice: {voice_label}")

# --- Start screen ---
if not st.session_state.story_started:
    st.write("Press **Begin Story** to start your adventure.")
    if st.button("▶️ Begin Story", type="primary"):
        st.session_state.chat = client.chats.create(
            model=GEMINI_MODEL,
            history=[
                types.Content(
                    role="user",
                    parts=[types.Part(text=build_system_prompt(genre, art_style))]
                )
            ]
        )
        st.session_state.story_started = True
        take_turn("Begin the story.")
        st.rerun()

# --- Render full story history ---
else:
    for turn in st.session_state.history:
        st.write(turn["story_text"])
        if turn["image_bytes"]:
            st.image(turn["image_bytes"], width=500)
        if turn["audio_buffer"]:
            st.audio(turn["audio_buffer"], format="audio/mp3")
        st.divider()

    # --- PHASE 3: DYNAMIC UI GENERATION ---
    if st.session_state.current_options:
        st.caption(f"🔄 {len(st.session_state.current_options)} choices generated dynamically by the AI")
        st.subheader("What do you do?")
        cols = st.columns(len(st.session_state.current_options))
        for i, option_text in enumerate(st.session_state.current_options):
            with cols[i]:
                if st.button(option_text, key=f"option_{len(st.session_state.history)}_{i}"):
                    take_turn(option_text)
                    st.rerun()