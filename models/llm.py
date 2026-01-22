import os
from langchain_groq import ChatGroq


def get_chatgroq_model():
    """
    Initialize and return Groq chat model
    """

    api_key = os.getenv("GROQ_API_KEY")
    model_name = "llama-3.1-8b-instant"

    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set in environment variables.")

    try:
        return ChatGroq(
            api_key=api_key,
            model=model_name,
            temperature=0.3
        )
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Groq model: {str(e)}")
