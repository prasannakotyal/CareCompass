import os
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure the Gemini-Pro AI model
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Initialize the model
model = genai.GenerativeModel(model_name='gemini-1.5-flash')

def medichat_app():
    st.title("‍⚕️ MediChat - Your Medical Assistant")

    # Initialize session state for messages
    if "history" not in st.session_state:
        st.session_state["history"] = [
            {"role": "assistant", "content": "Hello! I'm MediChat, your medical assistant. How can I assist you with your health today?"}
        ]

    # Display the chat history
    for msg in st.session_state.history:
        if msg["role"] == "user":
            st.chat_message("user", avatar="🧑‍💻").write(msg["content"])
        else:
            st.chat_message("assistant", avatar="🤖").write(msg["content"])

    # User input handling
    user_input = st.chat_input("Type your message here...")

    if user_input:
        # Append user message to history
        st.session_state.history.append({"role": "user", "content": user_input})
        st.chat_message("user", avatar="🧑‍💻").write(user_input)

        # Construct the prompt by concatenating the conversation history
        conversation = ""
        for msg in st.session_state.history:
            if msg["role"] == "user":
                conversation += f"User: {msg['content']}\n"
            else:
                conversation += f"Assistant: {msg['content']}\n"

        # Add system prompt to guide the assistant's behavior
        system_prompt = (
            "You are MediChat, a helpful and knowledgeable medical assistant developed to provide accurate and reliable medical information. "
            "Always ensure your responses are based on established medical knowledge and guidelines. When providing advice, encourage users to consult with healthcare professionals for personalized guidance."
        )

        full_prompt = f"{system_prompt}\n\n{conversation}\nAssistant:"

        # Generate response from the model
        try:
            response = model.generate_content(full_prompt)
            assistant_response = response.text.strip()
        except Exception as e:
            assistant_response = "I'm sorry, but I'm currently unable to process your request. Please try again later."

        # Append assistant response to history
        st.session_state.history.append({"role": "assistant", "content": assistant_response})
        st.chat_message("assistant", avatar="🤖").write(assistant_response)

    # Add a button to clear the chat history
    if st.button("Clear Conversation"):
        st.session_state.history = [
            {"role": "assistant", "content": "Hello! I'm MediChat, your medical assistant. How can I assist you with your health today?"}
        ]
        st.experimental_rerun()
