from typing import Dict, Any
from app.agents.state import StudyGuideState, ContentItem
from app.services.webArticleExtraction import extract_web_article
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class WebAgent:
    def __init__(self):
        self.name = "WebAgent"

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        """
        Process all web URLs in the state.

        Args:
            state: Current workflow state containing urls

        Returns:
            Dict with updated state fields (url_content, errors, processing_stats)
        """
        request_id = state["request_id"]
        urls = state.get("urls", [])

        if not urls:
            logger.info(f"[{request_id}] [{self.name}] No web URLs to process")
            return {
                "url_content": [],
                "current_step": "web_complete"
            }

        logger.info(f"[{request_id}] [{self.name}] Processing {len(urls)} web URLs")

        results = []
        new_errors = []  # Only track new errors from this agent
        success_count = 0
        fail_count = 0

        for idx, url in enumerate(urls, 1):
            try:
                logger.info(f"[{request_id}] [{self.name}] Processing URL {idx}/{len(urls)}: {url}")

                # REUSE existing web article extraction function (uses trafilatura)
                # Note: This function is synchronous, but we're in an async context
                article = extract_web_article(url)

                content = article.get("text", "")

                if content and content.strip():
                    results.append(ContentItem(
                        source=url,
                        source_type="url",
                        content=content,
                        metadata={
                            "url": url,
                            "title": article.get("title"),
                            "author": article.get("author"),
                            "date": article.get("date"),
                            "index": idx
                        }
                    ))
                    success_count += 1
                    logger.info(f"[{request_id}] [{self.name}] Successfully extracted {len(content)} characters from {url}")
                else:
                    logger.warning(f"[{request_id}] [{self.name}] No content extracted from {url}")
                    fail_count += 1
                    new_errors.append(f"URL {url}: No content could be extracted")

            except Exception as e:
                fail_count += 1
                error_msg = f"URL {url}: {str(e)}"
                new_errors.append(error_msg)
                logger.error(f"[{request_id}] [{self.name}] Error processing {url}: {str(e)}")

        logger.info(f"[{request_id}] [{self.name}] Completed: {success_count} successful, {fail_count} failed")

        return {
            "url_content": results,
            "errors": new_errors,  # Only new errors, will be concatenated by reducer
            "processing_stats": {"url_success": success_count, "url_fail": fail_count},
            "current_step": "web_complete"
        }

