# Content extraction service
import trafilatura
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def extract_web_article(url):
    """
    Extract article content and metadata from a web URL.
    
    Args:
        url: The URL to extract content from
    
    Returns:
        dict: Article data including title, author, date, text, and metadata
    """
    logger.info(f"Starting web article extraction for URL: {url}")
    
    if not url or not isinstance(url, str):
        logger.error(f"Invalid URL provided: {url}")
        raise ValueError(f"Invalid URL: must be a non-empty string")
    
    if not url.startswith(('http://', 'https://')):
        logger.error(f"URL missing protocol (http:// or https://): {url}")
        raise ValueError(f"URL must start with http:// or https://: {url}")
    
    try:
        # Step 1: Download
        logger.debug(f"Downloading content from URL: {url}")
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            logger.error(f"Failed to download URL (received None): {url}")
            raise ValueError(f"Failed to download URL: {url}. The URL may be invalid, unreachable, or blocked.")
        
        logger.info(f"Successfully downloaded content from URL: {url} (size: {len(downloaded)} bytes)")

        # Step 2: Extract clean text
        logger.debug(f"Extracting text content from downloaded HTML: {url}")
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            include_formatting=True,
            output_format='txt'
        )
        
        if text is None:
            logger.error(f"Failed to extract content from downloaded HTML: {url}")
            raise ValueError(f"Failed to extract content from: {url}. The page may not contain readable text.")
        
        # Clean up the text - remove excessive whitespace while preserving structure
        import re
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
        text = re.sub(r' +', ' ', text)  # Remove excessive spaces
        text = text.strip()
        
        text_length = len(text)
        logger.info(f"Successfully extracted {text_length} characters of text from: {url}")

        # Step 3: Extract metadata
        logger.debug(f"Extracting metadata from URL: {url}")
        try:
            metadata = trafilatura.extract_metadata(downloaded)
            
            result = {
                "title": metadata.title if metadata else None,
                "author": metadata.author if metadata else None,
                "date": metadata.date if metadata else None,
                "text": text,
                "raw_metadata": metadata.as_dict() if metadata else {}
            }
            
            logger.info(f"Successfully extracted article from {url} - Title: {result['title'] or 'N/A'}, Author: {result['author'] or 'N/A'}")
            return result
            
        except Exception as e:
            logger.warning(f"Failed to extract metadata from {url}: {str(e)}. Returning content without metadata.")
            return {
                "title": None,
                "author": None,
                "date": None,
                "text": text,
                "raw_metadata": {}
            }
    
    except ValueError:
        # Re-raise ValueError as-is (already logged)
        raise
    except Exception as e:
        logger.error(f"Unexpected error extracting web article from {url}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to extract web article from {url}: {str(e)}")


def process_urls_batch(urls, request_id: str):
    """
    Extract article content from multiple URLs.
    
    Args:
        urls: List of URLs to process
        request_id: Request ID for logging
        
    Returns:
        Tuple of (combined_output, successful_count, failed_count)
    """
    from typing import List
    
    num_urls = len(urls)
    logger.info(f"[Request {request_id}] Starting URL extraction ({num_urls} URLs)")
    
    combined_output = []
    successful_sources = 0
    failed_sources = 0
    
    for idx, url in enumerate(urls, 1):
        try:
            logger.info(f"[Request {request_id}] Processing URL {idx}/{num_urls}: {url}")
            article = extract_web_article(url)
            combined_output.append(article["text"])
            successful_sources += 1
            logger.info(f"[Request {request_id}] Successfully processed URL: {url}")
        except Exception as e:
            failed_sources += 1
            logger.error(f"[Request {request_id}] Failed to process URL {url}: {str(e)}")
    
    return combined_output, successful_sources, failed_sources