import os
from dotenv import load_dotenv
from pathlib import Path
from app.utils.logger import setup_logger
import time

logger = setup_logger(__name__)
project_root = Path(__file__).resolve().parents[2]

# Global rate limiting - minimum time between API calls
_last_api_call = 0
_min_delay_between_calls = 2.0  # 2 seconds between calls

def get_gemini_api_key():
    """Get the Gemini API key from environment variables."""
    try:
        # Load environment variable
        load_dotenv(dotenv_path=project_root / ".env")
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
            raise ValueError("GEMINI_API_KEY not found in environment variables!")
        logger.debug("Successfully retrieved GEMINI_API_KEY from environment")
        return api_key
    except Exception as e:
        logger.error(f"Error loading API key: {str(e)}")
        raise


def rate_limiting():
    """Enforce a minimum delay between API calls."""
    global _last_api_call
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call

    if time_since_last_call < _min_delay_between_calls:
        sleep_time = _min_delay_between_calls - time_since_last_call
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)

    _last_api_call = time.time()