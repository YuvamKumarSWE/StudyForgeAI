from typing import Dict, Any
from app.agents.state import StudyGuideState, ContentItem
from app.services.pdfExtraction import extract_pdf_text
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class PDFAgent:
    def __init__(self):
        self.name = "PDFAgent"

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        request_id = state["request_id"]
        pdf_files = state.get("pdf_files", [])

        if not pdf_files:
            logger.info(f"[{request_id}] [{self.name}] No PDF files to process")
            return {
                "pdf_content": [],
                "current_step": "pdf_complete"
            }

        logger.info(f"[{request_id}] [{self.name}] Processing {len(pdf_files)} PDF files")

        results = []
        new_errors = []  # Only track new errors from this agent
        success_count = 0
        fail_count = 0

        for idx, pdf_file in enumerate(pdf_files, 1):
            filename = getattr(pdf_file, 'filename', f'pdf_{idx}')

            try:
                logger.info(f"[{request_id}] [{self.name}] Processing PDF {idx}/{len(pdf_files)}: {filename}")

                content = await extract_pdf_text(pdf_file)

                if content and content.strip():
                    results.append(ContentItem(
                        source=filename,
                        source_type="pdf",
                        content=content,
                        metadata={"filename": filename, "index": idx}
                    ))
                    success_count += 1
                    logger.info(f"[{request_id}] [{self.name}] Successfully extracted {len(content)} characters from {filename}")
                else:
                    logger.warning(f"[{request_id}] [{self.name}] No content extracted from {filename}")
                    fail_count += 1
                    new_errors.append(f"PDF {filename}: No content could be extracted")

            except Exception as e:
                fail_count += 1
                error_msg = f"PDF {filename}: {str(e)}"
                new_errors.append(error_msg)
                logger.error(f"[{request_id}] [{self.name}] Error processing {filename}: {str(e)}")

        logger.info(f"[{request_id}] [{self.name}] Completed: {success_count} successful, {fail_count} failed")

        return {
            "pdf_content": results,
            "errors": new_errors,
            "processing_stats": {"pdf_success": success_count, "pdf_fail": fail_count},
            "current_step": "pdf_complete"
        }

