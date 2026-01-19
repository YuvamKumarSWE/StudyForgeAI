from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
import json
import time
from dotenv import load_dotenv

from app.workflow import generate_study_guide_from_inputs
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
        try:
            other_sources = json.loads(sources)
            logger.debug(f"[Request {request_id}] Parsed sources JSON successfully")
        except json.JSONDecodeError as e:
            logger.error(f"[Request {request_id}] Failed to parse sources JSON: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON in sources parameter: {str(e)}")

        urls = other_sources.get("urls", [])
        videos = other_sources.get("videos", [])
        text_inputs = other_sources.get("text", [])

        logger.info(f"[Request {request_id}] Processing {len(pdfs)} PDFs, {len(urls)} URLs, {len(videos)} videos, {len(text_inputs)} text inputs")

        final_output_text = await generate_study_guide_from_inputs(
            pdfs=pdfs,
            urls=urls,
            videos=videos,
            text=text_inputs,
            request_id=request_id
        )

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