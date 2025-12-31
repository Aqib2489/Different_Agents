import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_openai_api_key():
    """Get OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    return api_key

def get_serper_api_key():
    """Get Serper API key from environment variables."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise ValueError("SERPER_API_KEY not found in environment variables")
    return api_key
