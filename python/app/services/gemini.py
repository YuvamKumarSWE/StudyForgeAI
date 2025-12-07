import os
import json
import time
import re
from dotenv import load_dotenv
from google import genai
from pathlib import Path
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
project_root = Path(__file__).resolve().parents[2]

# Global rate limiting - minimum time between API calls
_last_api_call = 0
_min_delay_between_calls = 2.0  # 2 seconds between calls

def _get_api_key(provided_key=None):
    """Get the Gemini API key from provided parameter or environment variables."""
    try:
        # Use provided key if available
        if provided_key and isinstance(provided_key, str) and provided_key.strip():
            logger.debug("Using user-provided API key")
            return provided_key.strip()
        
        # Fall back to environment variable
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

def _extract_retry_delay(error_message):
    """Extract retry delay from API error message."""
    try:
        # Look for patterns like "Please retry in 43.284182141 s" or "retryDelay: 43 s"
        match = re.search(r'retry in ([0-9.]+)s', str(error_message))
        if match:
            return float(match.group(1))
        match = re.search(r'retryDelay["\']?:\s*["\']?([0-9]+)s', str(error_message))
        if match:
            return float(match.group(1))
    except:
        pass
    return None

def _rate_limit():
    """Enforce a minimum delay between API calls."""
    global _last_api_call
    current_time = time.time()
    time_since_last_call = current_time - _last_api_call
    
    if time_since_last_call < _min_delay_between_calls:
        sleep_time = _min_delay_between_calls - time_since_last_call
        logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
        time.sleep(sleep_time)
    
    _last_api_call = time.time()

def _call_gemini_with_retry(client, model, prompt, max_retries=5, initial_delay=3):
    """
    Call Gemini API with intelligent retry logic for rate limits.
    
    Args:
        client: Gemini client instance
        model: Model name to use
        prompt: Prompt to send
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds between retries
        
    Returns:
        Response from Gemini API
        
    Raises:
        Exception: If all retries fail
    """
    for attempt in range(max_retries):
        try:
            # Enforce rate limiting between calls
            _rate_limit()
            
            logger.debug(f"Gemini API call attempt {attempt + 1}/{max_retries}")
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            
            if response and hasattr(response, 'text'):
                logger.debug(f"Gemini API call succeeded on attempt {attempt + 1}")
                return response
            else:
                logger.warning(f"Gemini API returned invalid response on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    delay = initial_delay * (2 ** attempt)
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                else:
                    raise ValueError("Gemini API returned invalid response after all retries")
                    
        except Exception as e:
            error_str = str(e)
            
            # Check if this is a rate limit error (429)
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str or 'quota' in error_str.lower():
                # Extract the retry delay from the error message
                retry_delay = _extract_retry_delay(error_str)
                
                if retry_delay and attempt < max_retries - 1:
                    # Add a small buffer to the suggested delay
                    wait_time = retry_delay + 2
                    logger.warning(f"Rate limit hit (429). Waiting {wait_time:.1f}s as suggested by API (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                elif attempt < max_retries - 1:
                    # Use exponential backoff if we can't extract delay
                    delay = initial_delay * (2 ** attempt)
                    wait_time = max(delay, 45)  # Wait at least 45 seconds for rate limits
                    logger.warning(f"Rate limit hit (429). Waiting {wait_time:.1f}s (attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Rate limit exceeded after all retries: {error_str}")
                    raise ValueError("API rate limit exceeded. Please wait a few minutes and try again with less content or fewer sources.")
            
            # For non-rate-limit errors
            logger.error(f"Gemini API error on attempt {attempt + 1}: {error_str}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"All {max_retries} Gemini API attempts failed")
                raise
    
    raise Exception("Failed to get valid response from Gemini API")

def extract_unique_topics_with_text(text, api_key=None):
    """
    Extract main topics from large text using the Gemini 2.5-pro model.
    Returns a JSON object where each topic maps to its unique corresponding text.
    Removes duplicate/similar content to ensure uniqueness.

    Args:
        text (str): The large text to process
        api_key (str, optional): User-provided API key, uses environment key if not provided

    Returns:
        dict: JSON object with topics as keys and unique text snippets as values
    """
    logger.info("Starting topic extraction from text")
    
    if not text or not isinstance(text, str):
        logger.error(f"Invalid text provided: {type(text)}")
        raise ValueError("Text must be a non-empty string")
    
    text_length = len(text)
    logger.info(f"Processing {text_length} characters for topic extraction")
    
    if text_length == 0:
        logger.warning("Empty text provided for topic extraction")
        return {}
    
    prompt = f"""You are a study guide assistant specialized in content deduplication and topic extraction.

Analyze the following text and:
1. Identify all main topics covered
2. Extract ALL unique text content related to each topic (be comprehensive)
3. Remove ONLY exact duplicates or near-identical phrases
4. Keep different explanations of the same concept if they provide unique value
5. Consolidate related information under the most appropriate topic

Return ONLY a valid JSON object where:
- Keys are the main topics (clear, concise topic names)
- Values are the consolidated unique text content (combine related sentences, avoid redundancy)

TEXT TO ANALYZE:
{text}

Return ONLY the JSON object, no other text."""

    try:
        logger.debug("Initializing Gemini API client for topic extraction")
        client = genai.Client(api_key=_get_api_key(api_key))
        
        logger.info("Sending request to Gemini API for topic extraction")
        response = _call_gemini_with_retry(
            client=client,
            model="gemini-2.5-flash-lite",
            prompt=prompt
        )

        # Extract the JSON from the response
        response_text = response.text.strip()
        logger.debug(f"Received response from Gemini API ({len(response_text)} characters)")

        # Try to parse the JSON response
        try:
            topics_data = json.loads(response_text)
            num_topics = len(topics_data)
            logger.info(f"Successfully extracted {num_topics} topics from text")
            return topics_data
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON directly, attempting to extract from markdown code blocks")
            # If the response contains Markdown code blocks, extract the JSON
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                topics_data = json.loads(json_str)
                logger.info(f"Successfully extracted {len(topics_data)} topics from markdown-wrapped JSON")
                return topics_data
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                topics_data = json.loads(json_str)
                logger.info(f"Successfully extracted {len(topics_data)} topics from code block")
                return topics_data
            else:
                logger.error(f"Failed to parse JSON from Gemini response. Response preview: {response_text[:200]}")
                raise ValueError(f"Failed to parse JSON from Gemini response: {response_text[:200]}...")

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise ValueError(f"Failed to parse JSON from Gemini response: {str(e)}")
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during topic extraction: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to extract topics: {str(e)}")

def make_study_guide(topics_data, include_summary=True, include_key_points=True, api_key=None):
    """
    Generate a comprehensive study guide from topic data using a SINGLE API call.

    Args:
        topics_data (dict): Dictionary with topics as keys and content as values
        include_summary (bool): Whether to generate a summary for each topic
        include_key_points (bool): Whether to extract key points for each topic
        api_key (str, optional): User-provided API key, uses environment key if not provided

    Returns:
        dict: A structured study guide with formatted content
    """
    logger.info("Starting study guide generation")
    
    if not topics_data:
        logger.warning("No topics data provided for study guide generation")
        return {
            "error": "No topics data provided",
            "study_guide": None
        }
    
    if not isinstance(topics_data, dict):
        logger.error(f"Invalid topics_data type: {type(topics_data)}")
        raise ValueError("topics_data must be a dictionary")

    try:
        logger.debug("Initializing Gemini API client for study guide generation")
        client = genai.Client(api_key=_get_api_key(api_key))

        # Determine the depth and complexity of the guide based on content length
        total_content_length = sum(len(str(content)) for content in topics_data.values())
        num_topics = len(topics_data)

        # Adaptive guide generation based on content size
        if total_content_length < 2000:
            guide_type = "concise"
        elif total_content_length < 10000:
            guide_type = "standard"
        else:
            guide_type = "comprehensive"
        
        logger.info(f"Generating {guide_type} study guide for {num_topics} topics ({total_content_length} characters) in SINGLE API call")

        # Build the batch prompt for ALL topics at once
        topics_json = json.dumps(topics_data, indent=2)

        batch_prompt = f"""You are a study guide assistant. Process ALL the following topics in one comprehensive analysis.

TOPICS AND CONTENT:
{topics_json}

Generate a complete study guide with the following structure. Return ONLY valid JSON, no additional text.

Required JSON structure:
{{
  "overview": "A brief 2-3 sentence overview of what this study guide covers and what students will learn",
  "topics": [
    {{
      "topic": "topic name",
      "original_content": "original content text","""

        if include_summary:
            batch_prompt += """
      "summary": "A 2-3 sentence summary capturing the main ideas","""

        if include_key_points:
            batch_prompt += """
      "key_points": ["key point 1", "key point 2", "key point 3"],"""

        batch_prompt += """
    }}
  ]
}}

Instructions:
- Process ALL {num_topics} topics in the order provided"""

        if include_summary:
            batch_prompt += """
- For each topic, create a clear 2-3 sentence summary of the main ideas"""

        if include_key_points:
            batch_prompt += """
- For each topic, extract 3-7 key points depending on content length"""

        batch_prompt += """
- Create an overall overview for the entire study guide
- Ensure the JSON is valid and properly formatted
- Include all original content in the original_content field

Return ONLY the JSON object, no markdown code blocks or additional text."""

        try:
            logger.info(f"Sending batch request to Gemini API for all {num_topics} topics")
            response = _call_gemini_with_retry(
                client=client,
                model="gemini-2.5-flash-lite",
                prompt=batch_prompt
            )

            response_text = response.text.strip()
            logger.debug(f"Received batch response from Gemini API ({len(response_text)} characters)")

            # Parse the JSON response
            try:
                # Try direct JSON parsing first
                study_guide_data = json.loads(response_text)
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON directly, attempting to extract from markdown code blocks")
                # Try extracting from markdown code blocks
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                    study_guide_data = json.loads(json_str)
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                    study_guide_data = json.loads(json_str)
                else:
                    logger.error(f"Failed to parse JSON from response. Preview: {response_text[:500]}")
                    raise ValueError(f"Failed to parse JSON from Gemini response")

            # Add metadata
            study_guide_data["metadata"] = {
                "total_topics": num_topics,
                "guide_type": guide_type,
                "content_length": total_content_length
            }

            logger.info(f"Successfully generated complete study guide with {num_topics} topics in single API call")
            return study_guide_data

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            raise ValueError(f"Failed to parse study guide JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error generating batch study guide: {str(e)}")
            raise

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating study guide: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate study guide: {str(e)}")


def generate_study_guide_from_text(combined_text: str, request_id: str, api_key: str = None):
    """
    Generate a study guide from combined text content.
    
    Args:
        combined_text: Combined text content from all sources
        request_id: Request ID for logging
        api_key: Optional Gemini API key
        
    Returns:
        Formatted study guide markdown string
        
    Raises:
        Exception: If study guide generation fails (with detailed error messages)
    """
    from fastapi import HTTPException
    
    logger.info(f"[Request {request_id}] Starting final study guide generation")
    logger.info(f"[Request {request_id}] Combined content length: {len(combined_text)} characters")
    
    # Extract topics
    try:
        logger.info(f"[Request {request_id}] Extracting topics from combined content")
        topics_data = extract_unique_topics_with_text(combined_text, api_key=api_key)
        logger.info(f"[Request {request_id}] Successfully extracted topics")
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to extract topics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract topics from content: {str(e)}"
        )
    
    # Generate study guide
    try:
        logger.info(f"[Request {request_id}] Generating study guide from topics")
        guide = make_study_guide(topics_data, include_summary=True, include_key_points=True, api_key=api_key)
        
        if "error" in guide:
            logger.error(f"[Request {request_id}] Study guide generation returned error: {guide['error']}")
            raise HTTPException(status_code=500, detail=f"Failed to generate study guide: {guide['error']}")
        
        logger.info(f"[Request {request_id}] Successfully generated study guide")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to generate study guide: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate study guide: {str(e)}"
        )
    
    # Format as markdown
    try:
        logger.info(f"[Request {request_id}] Formatting study guide as markdown")
        final_output_text = format_study_guide_as_markdown(guide)
        
        if final_output_text.startswith("# Error"):
            logger.error(f"[Request {request_id}] Markdown formatting returned error")
            raise HTTPException(status_code=500, detail="Failed to format study guide as markdown")
        
        logger.info(f"[Request {request_id}] Successfully formatted study guide as markdown")
        return final_output_text
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Request {request_id}] Failed to format markdown: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to format study guide as markdown: {str(e)}"
        )


def format_study_guide_as_markdown(study_guide):
    """
    Format the study guide as a readable Markdown document.

    Args:
        study_guide (dict): The structured study guide from make_study_guide()

    Returns:
        str: Markdown-formatted study guide
    """
    logger.info("Starting markdown formatting of study guide")
    
    if not study_guide:
        logger.error("No study guide data provided for markdown formatting")
        return "# Error\nNo study guide data available."
    
    if not isinstance(study_guide, dict):
        logger.error(f"Invalid study_guide type: {type(study_guide)}")
        return "# Error\nInvalid study guide format."
    
    if "topics" not in study_guide:
        logger.error("Study guide missing 'topics' key")
        return "# Error\nNo study guide data available."
    
    try:
        markdown = "# 📚 Study Guide\n\n"

        # Add overview
        if "overview" in study_guide:
            logger.debug("Adding overview to markdown")
            markdown += f"## 📖 Overview\n\n{study_guide['overview']}\n\n"

        # Add metadata
        if "metadata" in study_guide:
            logger.debug("Adding metadata to markdown")
            meta = study_guide["metadata"]
            markdown += f"**📊 Topics Covered:** {meta.get('total_topics', 0)} | "
            markdown += f"**📈 Guide Type:** {meta.get('guide_type', 'standard').title()}\n\n"
            markdown += "---\n\n"
            markdown += "## 📑 Table of Contents\n\n"
            
            # Add a table of contents
            for idx, topic_entry in enumerate(study_guide["topics"], 1):
                topic_name = topic_entry.get('topic', 'Unknown Topic')
                markdown += f"{idx}. [{topic_name}](#topic-{idx})\n"
            
            markdown += "\n---\n\n"

        # Add each topic
        num_topics = len(study_guide["topics"])
        logger.info(f"Formatting {num_topics} topics as markdown")
        
        for idx, topic_entry in enumerate(study_guide["topics"], 1):
            logger.debug(f"Formatting topic {idx}/{num_topics}: {topic_entry.get('topic', 'Unknown')}")
            
            topic_name = topic_entry.get('topic', 'Unknown Topic')
            markdown += f"<a id=\"topic-{idx}\"></a>\n\n"
            markdown += f"## {idx}. 🎯 {topic_name}\n\n"

            # Add summary
            if "summary" in topic_entry and topic_entry["summary"]:
                markdown += f"### 📝 Summary\n\n{topic_entry['summary']}\n\n"

            # Add key points
            if "key_points" in topic_entry and topic_entry["key_points"]:
                markdown += "### ✨ Key Points\n\n"
                for point in topic_entry["key_points"]:
                    if point and not point.startswith("Error"):
                        markdown += f"- ✓ {point}\n"
                markdown += "\n"

            # Add detailed content
            if "original_content" in topic_entry and topic_entry["original_content"]:
                content = topic_entry["original_content"]
                # Clean up the content
                content = content.strip()
                if content:
                    markdown += f"### 📄 Detailed Content\n\n{content}\n\n"
            
            # Add a separator between topics (except after the last one)
            if idx < num_topics:
                markdown += "---\n\n"

        # Add footer
        markdown += "\n---\n\n"
        markdown += "*Study guide generated successfully. Good luck with your studies! 🎓*\n"

        markdown_length = len(markdown)
        logger.info(f"Successfully formatted study guide as markdown ({markdown_length} characters)")
        return markdown
    
    except Exception as e:
        logger.error(f"Error formatting study guide as markdown: {str(e)}", exc_info=True)
        return f"# Error\nFailed to format study guide: {str(e)}"