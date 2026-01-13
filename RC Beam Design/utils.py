"""Utility functions for API key management"""

import os
from dotenv import load_dotenv


def load_api_keys():
    """Load API keys from .env file"""
    load_dotenv()
    
    
def get_openai_api_key():
    """Get OpenAI API key from environment variables"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please set it in .env file")
    return api_key
