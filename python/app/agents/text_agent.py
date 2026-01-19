from typing import Dict, Any
from app.agents.state import StudyGuideState, ContentItem
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

class TextAgent:
    def __init__(self):
        self.name = "TextAgent"

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        """
        Process all text inputs in the state.

        Args:
            state: Current workflow state containing text_inputs

        Returns:
            Dict with updated state fields (text_content, errors, processing_stats)
        """
        request_id = state["request_id"]
        text_inputs = state.get("text_inputs", [])

        if not text_inputs:
            logger.info(f"[{request_id}] [{self.name}] No text inputs to process")
            return {
                "text_content": [],
                "current_step": "text_complete"
            }

        logger.info(f"[{request_id}] [{self.name}] Processing {len(text_inputs)} text inputs")

        results = []
        new_errors = []  # Only track new errors from this agent
        success_count = 0
        fail_count = 0

        for idx, text in enumerate(text_inputs, 1):
            try:
                if text and isinstance(text, str) and len(text.strip()) > 0:
                    cleaned_text = text.strip()
                    results.append(ContentItem(
                        source=f"text_input_{idx}",
                        source_type="text",
                        content=cleaned_text,
                        metadata={
                            "index": idx,
                            "original_length": len(text),
                            "cleaned_length": len(cleaned_text)
                        }
                    ))
                    success_count += 1
                    logger.debug(f"[{request_id}] [{self.name}] Successfully processed text input {idx}/{len(text_inputs)}")
                else:
                    logger.warning(f"[{request_id}] [{self.name}] Skipping empty or invalid text input {idx}/{len(text_inputs)}")
                    fail_count += 1

            except Exception as e:
                fail_count += 1
                error_msg = f"Text input {idx}: {str(e)}"
                new_errors.append(error_msg)
                logger.error(f"[{request_id}] [{self.name}] Error processing text input {idx}: {str(e)}")

        logger.info(f"[{request_id}] [{self.name}] Completed: {success_count} successful, {fail_count} failed")

        return {
            "text_content": results,
            "errors": new_errors,  # Only new errors, will be concatenated by reducer
            "processing_stats": {"text_success": success_count, "text_fail": fail_count},
            "current_step": "text_complete"
        }

