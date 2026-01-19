from typing import Dict, Any
from app.agents.state import StudyGuideState, ContentItem
from app.services.youtubeTranscript import get_youtube_transcript, extract_video_id
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class YouTubeAgent:
    def __init__(self):
        self.name = "YouTubeAgent"

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        """
        Process all YouTube URLs in the state.

        Args:
            state: Current workflow state containing youtube_urls

        Returns:
            Dict with updated state fields (youtube_content, errors, processing_stats)
        """
        request_id = state["request_id"]
        youtube_urls = state.get("youtube_urls", [])

        if not youtube_urls:
            logger.info(f"[{request_id}] [{self.name}] No YouTube videos to process")
            return {
                "youtube_content": [],
                "current_step": "youtube_complete"
            }

        logger.info(f"[{request_id}] [{self.name}] Processing {len(youtube_urls)} YouTube videos")

        results = []
        new_errors = []  # Only track new errors from this agent
        success_count = 0
        fail_count = 0

        for idx, url in enumerate(youtube_urls, 1):
            try:
                logger.info(f"[{request_id}] [{self.name}] Processing video {idx}/{len(youtube_urls)}: {url}")

                # REUSE existing YouTube transcript extraction function
                # Note: This function is synchronous, but we're in an async context
                transcript = get_youtube_transcript(url)

                if transcript and transcript.strip():
                    video_id = extract_video_id(url)
                    results.append(ContentItem(
                        source=url,
                        source_type="youtube",
                        content=transcript,
                        metadata={
                            "url": url,
                            "video_id": video_id,
                            "index": idx
                        }
                    ))
                    success_count += 1
                    logger.info(f"[{request_id}] [{self.name}] Successfully extracted {len(transcript)} characters from {url}")
                else:
                    logger.warning(f"[{request_id}] [{self.name}] No transcript extracted from {url}")
                    fail_count += 1
                    new_errors.append(f"YouTube {url}: No transcript could be extracted")

            except Exception as e:
                fail_count += 1
                error_msg = f"YouTube {url}: {str(e)}"
                new_errors.append(error_msg)
                logger.error(f"[{request_id}] [{self.name}] Error processing {url}: {str(e)}")

        logger.info(f"[{request_id}] [{self.name}] Completed: {success_count} successful, {fail_count} failed")

        return {
            "youtube_content": results,
            "errors": new_errors,  # Only new errors, will be concatenated by reducer
            "processing_stats": {"youtube_success": success_count, "youtube_fail": fail_count},
            "current_step": "youtube_complete"
        }

