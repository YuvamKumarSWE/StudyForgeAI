"""
Topics Agent - Handles topic extraction and deduplication using LangChain.
"""
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.state import StudyGuideState
from app.utils.llm_utils import get_gemini_api_key
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# System prompt for topic extraction
TOPIC_EXTRACTION_SYSTEM_PROMPT = """You are a study guide assistant specialized in content deduplication and topic extraction.

Analyze the provided text and:
1. Identify all main topics covered
2. Extract ALL unique text content related to each topic (be comprehensive)
3. Remove ONLY exact duplicates or near-identical phrases
4. Keep different explanations of the same concept if they provide unique value
5. Consolidate related information under the most appropriate topic

Return ONLY a valid JSON object where:
- Keys are the main topics (clear, concise topic names)
- Values are the consolidated unique text content (combine related sentences, avoid redundancy)

Return ONLY the JSON object, no other text."""


class TopicsAgent:
    """
    Agent responsible for extracting topics and deduplicating content.
    Uses LangChain with Gemini for intelligent topic extraction.
    """

    def __init__(self):
        self.name = "TopicsAgent"

    def _extract_topics(self, text: str) -> Dict[str, str]:
        """
        Extract main topics from text using LangChain with Gemini.

        Args:
            text: The text to extract topics from

        Returns:
            Dict with topics as keys and content as values
        """
        if not text or not isinstance(text, str) or len(text.strip()) == 0:
            raise ValueError("Text must be a non-empty string")

        logger.info(f"Extracting topics from {len(text)} characters")

        # Create LLM and invoke directly
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=get_gemini_api_key(),
            temperature=0.7,
            max_retries=5,
        )

        response = llm.invoke([
            SystemMessage(content=TOPIC_EXTRACTION_SYSTEM_PROMPT),
            HumanMessage(content=f"TEXT TO ANALYZE:\n{text}")
        ])

        # Parse JSON response
        return self._parse_json_response(response.content.strip())

    def _parse_json_response(self, response_text: str) -> Dict[str, str]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            topics_data = json.loads(response_text)
            logger.info(f"Successfully extracted {len(topics_data)} topics from text")
            return topics_data
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON directly, attempting to extract from markdown code blocks")
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
                logger.error(f"Failed to parse JSON from LLM response. Response preview: {response_text[:200]}")
                raise ValueError(f"Failed to parse JSON from LLM response: {response_text[:200]}...")

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        """
        Extract topics from combined content and deduplicate.

        Args:
            state: Current workflow state containing combined_text

        Returns:
            Dict with updated state fields (topics_data, errors)
        """
        request_id = state["request_id"]
        combined_text = state.get("combined_text", "")

        if not combined_text or not combined_text.strip():
            logger.error(f"[{request_id}] [{self.name}] No combined text available for topic extraction")
            return {
                "topics_data": {},
                "errors": ["TopicsAgent: No content available for topic extraction"],
                "current_step": "topics_failed"
            }

        logger.info(f"[{request_id}] [{self.name}] Extracting topics from {len(combined_text)} characters")

        try:
            topics_data = self._extract_topics(combined_text)

            if topics_data:
                num_topics = len(topics_data)
                logger.info(f"[{request_id}] [{self.name}] Successfully extracted {num_topics} topics")
                return {
                    "topics_data": topics_data,
                    "errors": [],
                    "current_step": "topics_complete"
                }
            else:
                logger.warning(f"[{request_id}] [{self.name}] Topic extraction returned empty result")
                return {
                    "topics_data": {},
                    "errors": ["TopicsAgent: No topics could be extracted from the content"],
                    "current_step": "topics_failed"
                }

        except Exception as e:
            error_msg = f"TopicsAgent: {str(e)}"
            logger.error(f"[{request_id}] [{self.name}] Error extracting topics: {str(e)}")
            return {
                "topics_data": {},
                "errors": [error_msg],
                "current_step": "topics_failed"
            }

