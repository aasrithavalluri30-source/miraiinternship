import streamlit as st
import requests
import random
import base64

st.title("AI IMAGE STUDIO")
def set_background(image_path):
    with open(image_path, "rb") as f:
        img_data = f.read()
    b64_img = base64.b64encode(img_data).decode()

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{b64_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}

        [data-testid="stSidebar"] {{
            background-image: url("data:image/png;base64,{b64_img}");
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        }}

        [data-testid="stSidebar"] > div:first-child {{
            background-color: rgba(0, 0, 0, 0.45);
        }}

        .stApp, .stApp p, .stApp label, .stApp span, .stApp div {{
            color: white;
        }}

        div[data-testid="stAlert"] {{
            background-color: rgba(0, 0, 0, 0.5);
        }}
        div[data-testid="stAlert"] p {{
            color: white !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

set_background("assets/wallpaper.png")

# Sidebar settings
st.sidebar.header("Settings")

art_style = st.sidebar.selectbox(
    "Select art style",
    ["anime style", "vintage", "realistic", "sketch", "3d render"]
)

width = st.sidebar.slider("Image width", min_value=256, max_value=1024, value=768)
height = st.sidebar.slider("Image height", min_value=256, max_value=1024, value=768)

magic_enhance = st.sidebar.checkbox("✨Enable Magic Enhance")

MAGIC_WORDS = ", masterpiece, 8k resolution, highly detailed, trending on artstation, unreal engine 5 render"

# Richer style descriptors so each style actually shifts the output
STYLE_PROMPTS = {
    "anime style": "anime style, cel shaded, vibrant anime art",
    "vintage": "vintage sepia photograph, old film grain, 1920s aesthetic",
    "realistic": "photorealistic, hyper detailed, DSLR photo",
    "sketch": "pencil sketch, hand-drawn, cross-hatching, black and white",
    "3d render": "3D render, octane render, cinematic lighting, blender"
}

SURPRISE_PROMPTS = [
    "An astronaut riding a horse on Mars",
    "A cyberpunk street food vendor in Tokyo",
    "A dragon made entirely of stained glass",
    "A tiny robot gardening on the moon",
    "An underwater library full of glowing jellyfish",
    "A steampunk owl wearing a monocle and top hat",
    "A floating island city powered by giant crystals",
    "A samurai cat guarding a bowl of ramen",
    "A treehouse village connected by rainbow bridges",
    "A vintage train flying through a nebula",
    "A wizard's cluttered potion shop at midnight",
    "A giant turtle carrying an entire forest on its back",
    "A neon-lit noodle stand in a rainy cyberpunk alley",
    "A fox made of autumn leaves running through a forest",
    "A retro-futuristic diner on the surface of the moon"
]

#  Session state
if "image_bytes" not in st.session_state:
    st.session_state.image_bytes = None
if "image_caption" not in st.session_state:
    st.session_state.image_caption = None
if "history" not in st.session_state:
    st.session_state.history = []

# Clear Conversation button
st.sidebar.divider()
if st.sidebar.button("🗑️ Clear Conversation"):
    st.session_state.image_bytes = None
    st.session_state.image_caption = None
    st.session_state.history = []
    st.session_state.user_prompt_input = ""
    st.rerun()

#  Shared generation function
def generate_image(prompt_text):
    # Style descriptor goes first so the model weights it more heavily
    full_prompt = f"{STYLE_PROMPTS[art_style]}, {prompt_text}"
    if magic_enhance:
        full_prompt += MAGIC_WORDS

    with st.spinner("Rendering the image..."):
        encoded_prompt = requests.utils.quote(full_prompt)
        # Random seed forces a fresh generation instead of a cached/similar result
        seed = random.randint(0, 999999)
        url = (
            f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            f"?width={width}&height={height}&seed={seed}&nologo=true"
        )

        try:
            response = requests.get(url, timeout=60)
            if response.status_code == 200:
                st.session_state.image_bytes = response.content
                st.session_state.image_caption = full_prompt

                st.session_state.history.append({
                    "bytes": response.content,
                    "caption": full_prompt,
                    "style": art_style
                })
                # keep only the last 10 to avoid unbounded memory growth
                st.session_state.history = st.session_state.history[-10:]
            else:
                st.error(f"Something went wrong. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            st.error(f"Request failed: {e}")

#  Main UI
user_prompt = st.text_input("Describe the image", key="user_prompt_input")

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate Image"):
        if user_prompt:
            generate_image(user_prompt)
        else:
            st.warning("Please enter a description first.")

with col2:
    if st.button("🎲 Surprise Me!"):
        random_prompt = random.choice(SURPRISE_PROMPTS)
        st.info(f"Surprise prompt: {random_prompt}")
        generate_image(random_prompt)

#  Display + download (persists across reruns)
if st.session_state.image_bytes is not None:
    st.image(st.session_state.image_bytes, caption=st.session_state.image_caption, use_container_width=True)

    st.download_button(
        label="Download image",
        data=st.session_state.image_bytes,
        file_name=f"{art_style}_image.png",
        mime="image/png"
    )

# Session history gallery
if st.session_state.history:
    st.divider()
    st.subheader("📜 Session History")

    for i, item in enumerate(reversed(st.session_state.history)):
        cols = st.columns([1, 3])
        with cols[0]:
            st.image(item["bytes"], width=100)
        with cols[1]:
            st.caption(f"**Style:** {item['style']}")
            st.caption(item["caption"])

























# import streamlit as st
# import requests
# import random
# import base64

# st.title("AI IMAGE STUDIO")
# def set_background(image_path):
#     with open(image_path, "rb") as f:
#         img_data = f.read()
#     b64_img = base64.b64encode(img_data).decode()

#     st.markdown(
#         f"""
#         <style>
#         .stApp {{
#             background-image: url("data:image/png;base64,{b64_img}");
#             background-size: cover;
#             background-position: center;
#             background-repeat: no-repeat;
#             background-attachment: fixed;
#         }}

#         /* NEW: apply the same image to the sidebar */
#         [data-testid="stSidebar"] {{
#             background-image: url("data:image/png;base64,{b64_img}");
#             background-size: cover;
#             background-position: center;
#             background-repeat: no-repeat;
#         }}

#         /* NEW: dark overlay so sidebar text stays readable */
#         [data-testid="stSidebar"] > div:first-child {{
#             background-color: rgba(0, 0, 0, 0.45);
#         }}

#         /* Make all general text white */
#         .stApp, .stApp p, .stApp label, .stApp span, .stApp div {{
#             color: white;
#         }}

#         /* Override the info box specifically */
#         div[data-testid="stAlert"] {{
#             background-color: rgba(0, 0, 0, 0.5);
#         }}
#         div[data-testid="stAlert"] p {{
#             color: white !important;
#         }}
#         </style>
#         """,
#         unsafe_allow_html=True
#     )

# set_background("assets/wallpaper.png")

# # Sidebar settings
# st.sidebar.header("Settings")

# art_style = st.sidebar.selectbox(
#     "Select art style",
#     ["anime style", "vintage", "realistic", "sketch", "3d render"]
# )

# width = st.sidebar.slider("Image width", min_value=256, max_value=1024, value=768)
# height = st.sidebar.slider("Image height", min_value=256, max_value=1024, value=768)

# # Task 3: Magic Enhance checkbox
# magic_enhance = st.sidebar.checkbox("✨Enable Magic Enhance")

# MAGIC_WORDS = ", masterpiece, 8k resolution, highly detailed, trending on artstation, unreal engine 5 render"

# # Task 4: list of surprise prompts
# SURPRISE_PROMPTS = [
#     "An astronaut riding a horse on Mars",
#     "A cyberpunk street food vendor in Tokyo",
#     "A dragon made entirely of stained glass",
#     "A tiny robot gardening on the moon",
#     "An underwater library full of glowing jellyfish",
#     "A steampunk owl wearing a monocle and top hat",
#     "A floating island city powered by giant crystals",
#     "A samurai cat guarding a bowl of ramen",
#     "A treehouse village connected by rainbow bridges",
#     "A vintage train flying through a nebula",
#     "A wizard's cluttered potion shop at midnight",
#     "A giant turtle carrying an entire forest on its back",
#     "A neon-lit noodle stand in a rainy cyberpunk alley",
#     "A fox made of autumn leaves running through a forest",
#     "A retro-futuristic diner on the surface of the moon"
# ]

# #  Session state 
# if "image_bytes" not in st.session_state:
#     st.session_state.image_bytes = None
# if "image_caption" not in st.session_state:
#     st.session_state.image_caption = None

# # NEW: history list to store every past generation
# if "history" not in st.session_state:
#     st.session_state.history = []

# # NEW: Clear Conversation button in the sidebar
# st.sidebar.divider()
# if st.sidebar.button("🗑️ Clear Conversation"):
#     st.session_state.image_bytes = None
#     st.session_state.image_caption = None
#     st.session_state.history = []
#     st.session_state.user_prompt_input = ""   
#     st.rerun()
# STYLE_PROMPTS = {
#     "anime style": "anime style, cel shaded, vibrant anime art",
#     "vintage": "vintage sepia photograph, old film grain, 1920s aesthetic",
#     "realistic": "photorealistic, hyper detailed, DSLR photo",
#     "sketch": "pencil sketch, hand-drawn, cross-hatching, black and white",
#     "3d render": "3D render, octane render, cinematic lighting, blender"
# }

# def generate_image(prompt_text):
#     full_prompt = f"{STYLE_PROMPTS[art_style]}, {prompt_text}"
#     if magic_enhance:
#         full_prompt += MAGIC_WORDS


#     with st.spinner("Rendering the image..."):
#         encoded_prompt = requests.utils.quote(full_prompt)
#         # Task 1: width & height actually sent as URL parameters
#         url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"

#         try:
#             response = requests.get(url, timeout=60)
#             if response.status_code == 200:
#                 st.session_state.image_bytes = response.content
#                 st.session_state.image_caption = full_prompt

#                 # NEW: save this generation into history
#                 st.session_state.history.append({
#                     "bytes": response.content,
#                     "caption": full_prompt,
#                     "style": art_style
#                 })
#                 # NEW: keep only the last 10 to avoid unbounded memory growth
#                 st.session_state.history = st.session_state.history[-10:]
#             else:
#                 st.error(f"Something went wrong. Status code: {response.status_code}")
#         except requests.exceptions.RequestException as e:
#             st.error(f"Request failed: {e}")

# #  Main UI
# user_prompt = st.text_input("Describe the image", key="user_prompt_input")

# col1, col2 = st.columns(2)

# with col1:
#     if st.button("Generate Image"):
#         if user_prompt:
#             generate_image(user_prompt)
#         else:
#             st.warning("Please enter a description first.")

# with col2:
#     # Task 4: Surprise Me button
#     if st.button("🎲 Surprise Me!"):
#         random_prompt = random.choice(SURPRISE_PROMPTS)
#         st.info(f"Surprise prompt: {random_prompt}")
#         generate_image(random_prompt)

# #  Display + download (persists across reruns)
# if st.session_state.image_bytes is not None:
#     st.image(st.session_state.image_bytes, caption=st.session_state.image_caption, use_container_width=True)

#     # Task 2: correct + dynamic file extension
#     st.download_button(
#         label="Download image",
#         data=st.session_state.image_bytes,
#         file_name=f"{art_style}_image.png",
#         mime="image/png"
#     )

# # NEW: Session history gallery
# if st.session_state.history:
#     st.divider()
#     st.subheader("📜 Session History")

#     # show most recent first
#     for i, item in enumerate(reversed(st.session_state.history)):
#         cols = st.columns([1, 3])
#         with cols[0]:
#             st.image(item["bytes"], width=100)
#         with cols[1]:
#             st.caption(f"**Style:** {item['style']}")
#             st.caption(item["caption"])