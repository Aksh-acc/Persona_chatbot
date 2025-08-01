import streamlit as st
import os
import importlib
from dotenv import load_dotenv
load_dotenv()

# Streamlit Page Setup
st.set_page_config(page_title="Emotion AI Chatbot", page_icon="🤖")
st.title("🧠 Emotion AI Chatbot")

# Manual Personality Selection
persona = st.selectbox("Choose your chatbot personality:", 
                       ["Close Friend", "Professor", "Therapist"])

# Set system prompt based on selected persona
def get_persona_prompt(choice):
    if choice == "Close Friend":
        return "close_friends"
    elif choice == "Professor":
        return "professor"
    elif choice == "Therapist":
        return "therapist"
    else:
        return "default"

# Load correct Python file dynamically
selected_persona_module = get_persona_prompt(persona)
try:
    persona_module = importlib.import_module(f"personality.{selected_persona_module}")
    generate_response = persona_module.generate
except ModuleNotFoundError:
    st.error(f"Module for {selected_persona_module} not found.")
    st.stop()

# Initialize chat history
if "messages" not in st.session_state or st.session_state.get("current_persona") != persona:
    st.session_state.messages = [{"role": "system", "content": f"{persona} mode activated"}]
    st.session_state.current_persona = persona

# Display previous messages
for msg in st.session_state.messages[1:]:  # skip system message
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input from user
user_input = st.chat_input("Say something...")

# Handle input
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        # Call the dynamically loaded generate() function
        response = generate_response({
            "messages": st.session_state.messages,
            "persona": selected_persona_module
        })

        # Handle Langchain-style or raw response
        try:
            reply = response.choices[0].message["content"]  # If using a model that returns choices
        except:
            reply = response["messages"][-1].content  # Generic fallback
        
        st.markdown(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})
