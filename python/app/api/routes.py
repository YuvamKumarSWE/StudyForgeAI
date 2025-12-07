from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import json
import time
import os
from dotenv import load_dotenv
from app.services.pdfExtraction import process_pdfs_batch
from app.services.webArticleExtraction import process_urls_batch
from app.services.youtubeTranscript import process_videos_batch
from app.services.textProcessing import process_text_inputs_batch
from app.services.gemini import generate_study_guide_from_text
from app.utils.logger import setup_logger

# Load environment variables
load_dotenv()
logger = setup_logger(__name__)
router = APIRouter()

@router.get("/api/health")
def health_check():
    logger.info("Health check requested")
    return {"status": "healthy"}

@router.post("/api/get-output")
async def get_output(
    pdfs: List[UploadFile] = File(default=[]),
    sources: str = Form(default="{}")
):
    start_time = time.time()
    request_id = f"{int(start_time * 1000)}"
    
    logger.info(f"[Request {request_id}] Starting get_output request")
    
    try:
        # Parse sources JSON
        try:
            other_sources = json.loads(sources)
            logger.debug(f"[Request {request_id}] Parsed sources JSON successfully")
        except json.JSONDecodeError as e:
            logger.error(f"[Request {request_id}] Failed to parse sources JSON: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON in sources parameter: {str(e)}")

        urls = other_sources.get("urls", [])
        videos = other_sources.get("videos", [])
        text_inputs = other_sources.get("text", [])

        # Log input summary
        logger.info(f"[Request {request_id}] Processing {len(pdfs)} PDFs, {len(urls)} URLs, {len(videos)} videos, {len(text_inputs)} text inputs")

        # Process all input sources
        combined_output = []
        successful_sources = 0
        failed_sources = 0

        # Extract PDF content
        pdf_output, pdf_success, pdf_fail = await process_pdfs_batch(pdfs, request_id)
        combined_output.extend(pdf_output)
        successful_sources += pdf_success
        failed_sources += pdf_fail

        # Extract URL article content
        url_output, url_success, url_fail = process_urls_batch(urls, request_id)
        combined_output.extend(url_output)
        successful_sources += url_success
        failed_sources += url_fail

        # Extract YouTube transcripts
        video_output, video_success, video_fail = process_videos_batch(videos, request_id)
        combined_output.extend(video_output)
        successful_sources += video_success
        failed_sources += video_fail

        # Process raw text input
        text_output, text_success, text_fail = process_text_inputs_batch(text_inputs, request_id)
        combined_output.extend(text_output)
        successful_sources += text_success
        failed_sources += text_fail

        # Log extraction summary
        total_sources = successful_sources + failed_sources
        logger.info(f"[Request {request_id}] Source extraction complete: {successful_sources}/{total_sources} successful, {failed_sources} failed")

        # Check if we have any content to process
        if not combined_output:
            logger.error(f"[Request {request_id}] No content extracted from any sources")
            raise HTTPException(
                status_code=400, 
                detail="No content could be extracted from the provided sources. Please check your inputs and try again."
            )

        # Generate study guide from combined content
        final_output_text = "\n\n".join(combined_output)
        final_output_text = generate_study_guide_from_text(final_output_text, request_id)

        # Log completion
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"[Request {request_id}] Request completed successfully in {duration:.2f} seconds")
        logger.info(f"[Request {request_id}] Final output length: {len(final_output_text)} characters")

        return {
            "study_guide": final_output_text
        }
    
    except HTTPException:
        raise
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        logger.error(f"[Request {request_id}] Unexpected error after {duration:.2f} seconds: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while processing your request: {str(e)}"
        )