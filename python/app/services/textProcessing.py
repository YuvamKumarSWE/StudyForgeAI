from app.utils.logger import setup_logger
from typing import List

logger = setup_logger(__name__)


def process_text_inputs_batch(text_inputs: List[str], request_id: str):
    """
    Process raw text inputs.
    
    Args:
        text_inputs: List of text strings to process
        request_id: Request ID for logging
        
    Returns:
        Tuple of (combined_output, successful_count, failed_count)
    """
    num_texts = len(text_inputs)
    logger.info(f"[Request {request_id}] Processing text inputs ({num_texts} entries)")
    
    combined_output = []
    successful_sources = 0
    failed_sources = 0
    
    for idx, t in enumerate(text_inputs, 1):
        try:
            if t and isinstance(t, str) and len(t.strip()) > 0:
                combined_output.append(t)
                successful_sources += 1
                logger.debug(f"[Request {request_id}] Added text input {idx}/{num_texts}")
            else:
                logger.warning(f"[Request {request_id}] Skipping empty or invalid text input {idx}/{num_texts}")
        except Exception as e:
            failed_sources += 1
            logger.error(f"[Request {request_id}] Error processing text input {idx}: {str(e)}")
    
    return combined_output, successful_sources, failed_sources
