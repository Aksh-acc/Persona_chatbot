import streamlit as st
import os
import importlib
import uuid
from dotenv import load_dotenv
from personality.therapist import new_session  # Make sure other persona files have the same function
from groq import Groq
import whisper
import tempfile
import torchaudio
import time
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
load_dotenv()

# Streamlit Page Setup
st.set_page_config(page_title="Emotion AI Chatbot", page_icon="🤖")
st.title("🧠 Emotion AI Chatbot")

# Manual Personality Selection
persona = st.selectbox("Choose your chatbot personality:", 
                       ["Close Friend", "Professor", "Therapist"])

# Get the persona's module name
def get_persona_prompt(choice):
    if choice == "Close Friend":
        return "close_friends"
    elif choice == "Professor":
        return "professor"
    elif choice == "Therapist":
        return "therapist"
    return "default"

# Load selected personality module dynamically
selected_persona_module = get_persona_prompt(persona)
try:
    persona_module = importlib.import_module(f"personality.{selected_persona_module}")
    generate_response = persona_module.generate
except ModuleNotFoundError:
    st.error(f"Module for {selected_persona_module} not found.")
    st.stop()

# === SESSION STATE INIT ===
if "current_persona" not in st.session_state:
    st.session_state.current_persona = persona

if "messages" not in st.session_state or st.session_state.current_persona != persona:
    st.session_state.messages = [{"role": "system", "content": f"{persona} mode activated"}]
    st.session_state.current_persona = persona

if "chat_sessions" not in st.session_state:
    st.session_state.chat_sessions = []  # stores past full chats

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())

# === DISPLAY CHAT MESSAGES ===
for msg in st.session_state.messages[1:]:  # Skip system
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# === USER INPUT ===
user_input = st.chat_input("Say something...")
audio_value = st.audio_input("🎙️ Speak your message:")

if audio_value is not None:
    st.audio(audio_value, format="audio/wav")

    # Save audio file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_file.write(audio_value.read())
        temp_audio_path = temp_audio_file.name

    # Transcribe with Whisper
    model = whisper.load_model("base")
    result = model.transcribe(temp_audio_path)
    user_input = result["text"]
     
    st.success(f"🗣️ You said: {user_input}")


if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = generate_response({
            "messages": st.session_state.messages,
            "persona": selected_persona_module
        })
        try:
            reply = response.choices[0].message["content"]
        except:
            reply = response["messages"][-1].content
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        # === SPEECH SYNTHESIS ===
        # Save the response to a file
        # Note: Ensure you have the PlayAI TTS client installed and configured
        # pip install playai-tts
        speech_file_path = "speech.wav" 
        model = "playai-tts"
        voice = "Fritz-PlayAI"
        text = response.choices[0].message["content"] if "choices" in response else response["messages"][-1].content
        response_format = "wav"

        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format=response_format
        )

        response.write_to_file(speech_file_path)
        # Play the audio response
        st.audio(speech_file_path, format="/wav")
        st.session_state.messages.append({"role": "assistant_audio", "content": speech_file_path})

# === SIDEBAR ===
st.sidebar.title("🗂️ Sessions - Emotion AI")

# --- New Chat Button ---
if st.sidebar.button(" Save Chat"):
    # Save current chat
    if len(st.session_state.messages) > 1:
        st.session_state.chat_sessions.append({
            "id": st.session_state.current_session_id,
            "persona": st.session_state.current_persona,
            "title": st.session_state.messages[1]["content"][:25] + "...",  # Title from 1st user message
            "messages": st.session_state.messages.copy()
        })
    # Reset
if st.sidebar.button("🆕 New Chat"):
    st.session_state.messages = [{"role": "system", "content": f"{persona} mode activated"}]
    # st.session_state.current_session_id = str(uuid.uuid4())

# # --- Reset Chat ---
# if st.sidebar.button("🗑️ Reset Chat"):
#     st.session_state.clear()

# --- Show Past Chats ---
if st.session_state.chat_sessions:
    st.sidebar.subheader("🕓 Previous Chats")
    for i, chat in enumerate(reversed(st.session_state.chat_sessions)):
        with st.sidebar.expander(f"{chat['persona']} - {chat['title']}"):
            for msg in chat["messages"]:
                st.sidebar.markdown(f"**{msg['role'].capitalize()}**: {msg['content']}", unsafe_allow_html=True)

# --- Show Session Info ---
with st.sidebar.expander("⚙️ Current Session Config"):
    if "chat_config" not in st.session_state:
        st.session_state.chat_config = None
    config = new_session("New Chat")
    st.session_state.chat_config = config
    st.write("Session ID:", st.session_state.current_session_id)
    st.write("Chat Config:", st.session_state.chat_config)

# === TEXT TO VIDEO GENERATION ===
import requests
# Using runwayml API to convert text to video
from tools.text_to_video import generate_video_from_text, get_video_url

# st.page_config(page_title="Text to Video", page_icon="🎥")
st.title("🎬 AI Video Generator")

text_prompt = st.text_input("Enter text prompt for video generation:")
generate = st.button("Generate Video from Text")

if generate:
    if text_prompt:
        st.info("🎥 Sending prompt to video generation API...")
        uuid = generate_video_from_text(text_prompt)

        if uuid:
            st.success(f"✅ Prompt accepted. Job UUID: `{uuid}`")
            st.info("⏳ Waiting for video to be ready...")

            # Wait + Poll loop (adjust timing as needed)
            # Wait for video to be ready (real-time progress)
            with st.spinner("⏳ Waiting for video to be ready..."):
                video_url = get_video_url(uuid)
                if video_url:
                    st.success("✅ Video is ready!")
                    st.video(video_url)
                else:
                    st.error("⚠️ Video is not ready. Try again in a few moments.")
                time.sleep(2)  # Reduce delay if you want snappier feedback
        else:
            st.error("❌ Failed to start video generation.")
    else:
        st.error("Please enter a prompt first.")
else:
    st.info("Enter a text prompt and click 'Generate Video from Text' to start.")


