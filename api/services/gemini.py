"""Gemini AI service for medical chat."""

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# Initialize client with API key
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

SYSTEM_PROMPT = """You are MediChat, a helpful and knowledgeable medical assistant developed to provide accurate and reliable medical information.

Guidelines:
- Provide helpful, accurate medical information based on established medical knowledge
- Always encourage users to consult healthcare professionals for personalized guidance
- Be empathetic and supportive in your responses
- If you're unsure about something, say so clearly
- Never diagnose conditions - only provide general information
- For emergencies, always advise calling emergency services immediately

Remember: You are an AI assistant, not a replacement for professional medical care."""


def chat(message: str, history: list[dict]) -> str:
    """
    Send a message to Gemini and get a response.

    Args:
        message: User's message
        history: List of previous messages [{"role": "user"|"assistant", "content": "..."}]

    Returns:
        Assistant's response text
    """
    try:
        # Build conversation context
        conversation = ""
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation += f"{role}: {msg['content']}\n"

        # Add current message
        conversation += f"User: {message}\nAssistant:"

        # Create config with system instruction
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        )

        # Generate response
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=conversation,
            config=config,
        )
        return response.text.strip()

    except Exception as e:
        print(f"Gemini API error: {e}")
        return "I'm sorry, but I'm currently unable to process your request. Please try again later."


def is_configured() -> bool:
    """Check if Gemini API is configured."""
    return bool(os.environ.get("GEMINI_API_KEY"))
