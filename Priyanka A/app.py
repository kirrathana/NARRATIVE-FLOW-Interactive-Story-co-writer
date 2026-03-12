import streamlit as st
import ollama
import random
import json
import os
import speech_recognition as sr
from datetime import datetime

# -------------------------------
# PAGE CONFIG
# -------------------------------
st.set_page_config(page_title="WriterBuddy", layout="wide")

DATA_FILE = "stories.json"

# -------------------------------
# LOAD & SAVE PERMANENT STORIES
# -------------------------------
def load_stories():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_stories():
    with open(DATA_FILE, "w") as f:
        json.dump(st.session_state.stories, f)

# -------------------------------
# SESSION STATE
# -------------------------------
if "stories" not in st.session_state:
    st.session_state.stories = load_stories()

if "current_story" not in st.session_state:
    st.session_state.current_story = None

if "genre" not in st.session_state:
    st.session_state.genre = "Fantasy"

if "response_length" not in st.session_state:
    st.session_state.response_length = "Medium"

if "pending_input" not in st.session_state:
    st.session_state.pending_input = ""

# -------------------------------
# GENRE BACKGROUND IMAGES
# -------------------------------
def apply_theme(genre):

    backgrounds = {
        "Fantasy": "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee",
        "Horror": "https://images.unsplash.com/photo-1506318137071-a8e063b4bec0",
        "Romance": "https://images.unsplash.com/photo-1518199266791-5375a83190b7",
        "Sci-Fi": "https://images.unsplash.com/photo-1462331940025-496dfbfc7564",
        "Thriller": "https://images.unsplash.com/photo-1492724441997-5dc865305da7"
    }

    bg = backgrounds.get(genre)

    st.markdown(f"""
        <style>
        .stApp {{
            background-image: url("{bg}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}

        .block-container {{
            background-color: rgba(255,255,255,0.92);
            padding: 30px;
            border-radius: 15px;
        }}

        .stButton>button {{
            background-color: #2E8B57;
            color: white;
            border-radius: 8px;
            font-weight: bold;
        }}
        </style>
    """, unsafe_allow_html=True)

# -------------------------------
# STORY FUNCTIONS
# -------------------------------
def create_story():
    title = f"Story {len(st.session_state.stories)+1}"
    st.session_state.stories[title] = {
        "created": str(datetime.now()),
        "messages": []
    }
    st.session_state.current_story = title
    save_stories()

def save_message(role, content):
    st.session_state.stories[st.session_state.current_story]["messages"].append({
        "role": role,
        "content": content
    })
    save_stories()

# -------------------------------
# RESPONSE LENGTH
# -------------------------------
def length_instruction():
    if st.session_state.response_length == "Short":
        return "Write only 3 short sentences."
    elif st.session_state.response_length == "Medium":
        return "Write one well-developed paragraph."
    else:
        return "Write a detailed, descriptive long response."

# -------------------------------
# OLLAMA RESPONSE
# -------------------------------
def generate_ai_response():

    story = st.session_state.current_story
    messages = st.session_state.stories[story]["messages"]

    system_prompt = {
        "role": "system",
        "content": f"You are a creative story writer in {st.session_state.genre} genre. {length_instruction()}"
    }

    full_messages = [system_prompt] + messages

    try:
        response = ollama.chat(
            model="phi",
            messages=full_messages
        )
        return response["message"]["content"]
    except:
        return "⚠ Ollama is not running. Please start Ollama."

# -------------------------------
# VOICE INPUT
# -------------------------------
def voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening...")
        audio = recognizer.listen(source, timeout=5)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except:
        return ""

# -------------------------------
# MAGIC SUGGESTIONS
# -------------------------------
def get_magic():
    ideas = [
        "Introduce betrayal.",
        "Add mysterious stranger.",
        "Reveal hidden secret.",
        "Create emotional tension.",
        "Add shocking plot twist.",
        "Introduce internal conflict."
    ]
    return random.sample(ideas, 3)

# -------------------------------
# SIDEBAR
# -------------------------------
with st.sidebar:

    st.title("✍️ WriterBuddy")

    if st.button("➕ New Story"):
        create_story()
        st.rerun()

    st.session_state.genre = st.selectbox(
        "Genre",
        ["Fantasy", "Horror", "Romance", "Sci-Fi", "Thriller"]
    )

    st.session_state.response_length = st.radio(
        "Response Length",
        ["Short", "Medium", "Long"]
    )

    st.markdown("---")
    st.subheader("📚 Story History")

    for story in st.session_state.stories:
        if st.button(story):
            st.session_state.current_story = story
            st.rerun()

    if st.session_state.current_story:
        st.markdown("---")
        new_title = st.text_input("Rename Story", value=st.session_state.current_story)
        if st.button("Save Title"):
            if new_title not in st.session_state.stories:
                st.session_state.stories[new_title] = st.session_state.stories.pop(
                    st.session_state.current_story
                )
                st.session_state.current_story = new_title
                save_stories()
                st.rerun()

# Apply theme
apply_theme(st.session_state.genre)

# -------------------------------
# MAIN PAGE
# -------------------------------
st.title("WriterBuddy – AI Story Co-Writer")

if not st.session_state.current_story:
    st.info("Create a New Story to begin ✨")
    st.stop()

for msg in st.session_state.stories[st.session_state.current_story]["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -------------------------------
# MAGIC BUTTON
# -------------------------------
if st.button("✨ Magic Suggestion"):
    for idea in get_magic():
        if st.button(idea):
            st.session_state.pending_input = idea

# -------------------------------
# QUICK BOOST
# -------------------------------
st.markdown("### 💡 Quick Boost")
cols = st.columns(5)

boosts = [
    "Add tension.",
    "Add plot twist.",
    "Deepen emotion.",
    "Introduce character.",
    "Improve dialogue."
]
c
for col, text in zip(cols, boosts):
    if col.button(text):
        st.session_state.pending_input = text

# -------------------------------
# USER INPUT + VOICE
# -------------------------------
col1, col2 = st.columns([4,1])

user_input = col1.chat_input("Continue your story...")

if col2.button("🎤"):
    voice_text = voice_input()
    if voice_text:
        user_input = voice_text

if st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = ""

if user_input:

    save_message("user", user_input)

    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_ai_response()
            st.markdown(response)

    save_message("assistant", response)
https://github.com/AdluriPriyanka/WriterBuddy.git