import re
import youtube_transcript_api as yta
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, 
    NoTranscriptFound, 
    VideoUnavailable
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

def extract_video_id(url: str) -> str:
    """
    Extracts YouTube video ID from any format of URL.
    
    Args:
        url: YouTube URL in any format
        
    Returns:
        str: Video ID if found, empty string otherwise
    """
    logger.debug(f"Extracting video ID from URL: {url}")
    
    if not url or not isinstance(url, str):
        logger.warning(f"Invalid URL provided to extract_video_id: {url}")
        return ""
    
    patterns = [
        r"v=([A-Za-z0-9_\-]{11})",
        r"youtu\.be/([A-Za-z0-9_\-]{11})",
        r"embed/([A-Za-z0-9_\-]{11})",
        r"shorts/([A-Za-z0-9_\-]{11})",
    ]

    for p in patterns:
        match = re.search(p, url)
        if match:
            video_id = match.group(1)
            logger.debug(f"Successfully extracted video ID: {video_id}")
            return video_id
    
    logger.warning(f"Could not extract video ID from URL: {url}")
    return ""

def format_timestamp(seconds: float) -> str:
    """
    Converts seconds to HH:MM:SS format.
    """
    seconds = int(seconds)
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60

    if h > 0:
        return f"{h:02}:{m:02}:{s:02}"
    else:
        return f"{m:02}:{s:02}"


def get_youtube_transcript(
    url: str,
    preferred_lang: str = "en"
) -> str:
    """
    Fetch and format the transcript for a YouTube video.
    
    Args:
        url: YouTube video URL
        preferred_lang: Preferred language code (default: "en")
        
    Returns:
        str: Formatted transcript text
    """
    logger.info(f"Starting YouTube transcript extraction for URL: {url}")
    
    if not url or not isinstance(url, str):
        logger.error(f"Invalid URL provided: {url}")
        raise ValueError("Invalid URL: must be a non-empty string")
    
    video_id = extract_video_id(url)
    if not video_id:
        logger.error(f"Could not extract video ID from URL: {url}")
        raise ValueError(f"Could not extract video ID from URL: {url}. Please provide a valid YouTube URL.")

    logger.info(f"Processing YouTube video ID: {video_id}")
    
    try:
        logger.debug(f"Fetching transcript listings for video ID: {video_id}")
        ytt_api = yta.YouTubeTranscriptApi()
        listings = ytt_api.list(video_id)
        
        logger.debug(f"Available transcript languages for video {video_id}: {[t.language_code for t in listings]}")

        # Try to find transcript in preferred language
        try:
            logger.debug(f"Attempting to find manual transcript in language: {preferred_lang}")
            transcript_obj = listings.find_transcript([preferred_lang])
            logger.info(f"Found manual transcript in {preferred_lang} for video {video_id}")
        except yta._errors.NoTranscriptFound:
            logger.debug(f"No manual transcript in {preferred_lang}, trying generated transcript")
            try:
                transcript_obj = listings.find_generated_transcript([preferred_lang])
                logger.info(f"Found generated transcript in {preferred_lang} for video {video_id}")
            except yta._errors.NoTranscriptFound:
                logger.warning(f"No transcript in {preferred_lang}, using first available language")
                try:
                    transcript_obj = next(iter(listings))
                    logger.info(f"Using transcript in language: {transcript_obj.language_code}")
                except StopIteration:
                    logger.error(f"No transcripts available for video {video_id}")
                    raise ValueError(f"No transcripts available for this video.")

        # Fetch the actual transcript
        logger.debug(f"Fetching transcript data for video {video_id}")
        transcript = transcript_obj.fetch()
        
        if not transcript:
            logger.error(f"Transcript fetch returned empty data for video {video_id}")
            raise ValueError("Transcript data is empty")
        
        logger.info(f"Successfully fetched transcript with {len(transcript)} entries for video {video_id}")

        # Format transcript
        logger.debug(f"Formatting transcript for video {video_id}")
        lines = []
        for entry in transcript:
            text = entry.get('text', '').strip()
            # Clean up the text
            text = text.replace("\n", " ")
            text = ' '.join(text.split())  # Normalize whitespace
            if text:  # Only add non-empty lines
                lines.append(text)

        # Join with proper spacing and create paragraphs every 5-7 entries for readability
        formatted_lines = []
        for i, line in enumerate(lines):
            formatted_lines.append(line)
            # Add paragraph break every 6 entries
            if (i + 1) % 6 == 0 and i < len(lines) - 1:
                formatted_lines.append("\n\n")
            else:
                formatted_lines.append(" ")
        
        formatted_transcript = "".join(formatted_lines).strip()
        transcript_length = len(formatted_transcript)
        logger.info(f"Successfully extracted {transcript_length} characters from YouTube video {video_id}")
        return formatted_transcript
    
    except yta._errors.TranscriptsDisabled:
        logger.error(f"Transcripts are disabled for video {video_id}")
        raise ValueError(f"Transcripts are disabled for this video.")
    except yta._errors.NoTranscriptFound:
        logger.error(f"No transcript found for video {video_id}")
        raise ValueError(f"No transcript available for this video.")
    except yta._errors.VideoUnavailable:
        logger.error(f"Video {video_id} is unavailable")
        raise ValueError(f"This video is unavailable. It may be private, deleted, or restricted.")
    except ValueError:
        # Re-raise ValueError as-is (already logged)
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching transcript for video {video_id}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to fetch transcript: {str(e)}")


def process_videos_batch(videos, request_id: str):
    """
    Extract transcripts from multiple YouTube videos.
    
    Args:
        videos: List of video URLs to process
        request_id: Request ID for logging
        
    Returns:
        Tuple of (combined_output, successful_count, failed_count)
    """
    from typing import List
    
    num_videos = len(videos)
    logger.info(f"[Request {request_id}] Starting video transcript extraction ({num_videos} videos)")
    
    combined_output = []
    successful_sources = 0
    failed_sources = 0
    
    for idx, url in enumerate(videos, 1):
        try:
            logger.info(f"[Request {request_id}] Processing video {idx}/{num_videos}: {url}")
            transcript = get_youtube_transcript(url)
            combined_output.append(transcript)
            successful_sources += 1
            logger.info(f"[Request {request_id}] Successfully processed video: {url}")
        except Exception as e:
            failed_sources += 1
            logger.error(f"[Request {request_id}] Failed to process video {url}: {str(e)}")
    
    return combined_output, successful_sources, failed_sources