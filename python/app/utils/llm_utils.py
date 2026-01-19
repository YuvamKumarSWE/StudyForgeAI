import os
from dotenv import load_dotenv
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
project_root = Path(__file__).resolve().parents[2]


def get_gemini_api_key():
    """Get the Gemini API key from environment variables."""
    load_dotenv(dotenv_path=project_root / ".env")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables!")
    return api_key
