"""
Study Guide Agent - Handles study guide generation and formatting using LangChain.
"""
import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.agents.state import StudyGuideState
from app.utils.llm_utils import get_gemini_api_key
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# System prompt for study guide generation
STUDY_GUIDE_SYSTEM_PROMPT = """You are a study guide assistant. Process ALL the provided topics in one comprehensive analysis.
Generate a complete study guide with the following structure. Return ONLY valid JSON, no additional text."""


class StudyGuideAgent:
    """
    Agent responsible for generating and formatting the final study guide.
    Uses LangChain with Gemini for intelligent study guide generation.
    """

    def __init__(self):
        self.name = "StudyGuideAgent"

    def _make_study_guide(self, topics_data: Dict, include_summary: bool = True, include_key_points: bool = True) -> Dict:
        """
        Generate a comprehensive study guide from topic data using LangChain.

        Args:
            topics_data: Dictionary with topics as keys and content as values
            include_summary: Whether to generate a summary for each topic
            include_key_points: Whether to extract key points for each topic

        Returns:
            A structured study guide dict
        """
        if not topics_data:
            return {"error": "No topics data provided", "study_guide": None}

        if not isinstance(topics_data, dict):
            raise ValueError("topics_data must be a dictionary")

        num_topics = len(topics_data)
        total_content_length = sum(len(str(v)) for v in topics_data.values())

        # Determine guide type based on content size
        guide_type = "concise" if total_content_length < 2000 else "standard" if total_content_length < 10000 else "comprehensive"
        logger.info(f"Generating {guide_type} study guide for {num_topics} topics")

        # Build prompt
        human_prompt = f"""TOPICS AND CONTENT:
{json.dumps(topics_data, indent=2)}

Required JSON structure:
{{
  "overview": "A brief 2-3 sentence overview of what this study guide covers and what students will learn",
  "topics": [
    {{
      "topic": "topic name",
      "original_content": "original content text","""

        if include_summary:
            human_prompt += """
      "summary": "A 2-3 sentence summary capturing the main ideas","""

        if include_key_points:
            human_prompt += """
      "key_points": ["key point 1", "key point 2", "key point 3"],"""

        human_prompt += f"""
    }}
  ]
}}

Instructions:
- Process ALL {num_topics} topics in the order provided
- For each topic, create a clear 2-3 sentence summary of the main ideas
- For each topic, extract 3-7 key points depending on content length
- Create an overall overview for the entire study guide
- Ensure the JSON is valid and properly formatted
- Include all original content in the original_content field

Return ONLY the JSON object, no markdown code blocks or additional text."""

        # Create LLM and invoke directly
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-lite",
            google_api_key=get_gemini_api_key(),
            temperature=0.7,
            max_retries=5,
        )

        response = llm.invoke([
            SystemMessage(content=STUDY_GUIDE_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt)
        ])

        # Parse JSON response and add metadata
        study_guide_data = self._parse_json_response(response.content.strip())
        study_guide_data["metadata"] = {
            "total_topics": num_topics,
            "guide_type": guide_type,
            "content_length": total_content_length
        }

        logger.info(f"Successfully generated study guide with {num_topics} topics")
        return study_guide_data

    def _parse_json_response(self, response_text: str) -> Dict:
        """Parse JSON from LLM response, handling markdown code blocks."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON directly, attempting to extract from markdown code blocks")
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            else:
                logger.error(f"Failed to parse JSON from response. Preview: {response_text[:500]}")
                raise ValueError("Failed to parse JSON from LLM response")

    def _format_as_markdown(self, study_guide: Dict) -> str:
        """
        Format the study guide as a readable Markdown document.

        Args:
            study_guide: The structured study guide dict

        Returns:
            Markdown-formatted study guide string
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
                markdown += f"## 📖 Overview\n\n{study_guide['overview']}\n\n"

            # Add metadata
            if "metadata" in study_guide:
                meta = study_guide["metadata"]
                markdown += f"**📊 Topics Covered:** {meta.get('total_topics', 0)} | "
                markdown += f"**📈 Guide Type:** {meta.get('guide_type', 'standard').title()}\n\n"
                markdown += "---\n\n"
                markdown += "## 📑 Table of Contents\n\n"

                for idx, topic_entry in enumerate(study_guide["topics"], 1):
                    topic_name = topic_entry.get('topic', 'Unknown Topic')
                    markdown += f"{idx}. [{topic_name}](#topic-{idx})\n"

                markdown += "\n---\n\n"

            # Add each topic
            num_topics = len(study_guide["topics"])
            logger.info(f"Formatting {num_topics} topics as markdown")

            for idx, topic_entry in enumerate(study_guide["topics"], 1):
                topic_name = topic_entry.get('topic', 'Unknown Topic')
                markdown += f"<a id=\"topic-{idx}\"></a>\n\n"
                markdown += f"## {idx}. 🎯 {topic_name}\n\n"

                if "summary" in topic_entry and topic_entry["summary"]:
                    markdown += f"### 📝 Summary\n\n{topic_entry['summary']}\n\n"

                if "key_points" in topic_entry and topic_entry["key_points"]:
                    markdown += "### ✨ Key Points\n\n"
                    for point in topic_entry["key_points"]:
                        if point and not point.startswith("Error"):
                            markdown += f"- ✓ {point}\n"
                    markdown += "\n"

                if "original_content" in topic_entry and topic_entry["original_content"]:
                    content = topic_entry["original_content"].strip()
                    if content:
                        markdown += f"### 📄 Detailed Content\n\n{content}\n\n"

                if idx < num_topics:
                    markdown += "---\n\n"

            markdown += "\n---\n\n"
            markdown += "*Study guide generated successfully. Good luck with your studies! 🎓*\n"

            logger.info(f"Successfully formatted study guide as markdown ({len(markdown)} characters)")
            return markdown

        except Exception as e:
            logger.error(f"Error formatting study guide as markdown: {str(e)}", exc_info=True)
            return f"# Error\nFailed to format study guide: {str(e)}"

    async def process(self, state: StudyGuideState) -> Dict[str, Any]:
        """
        Generate study guide from topics data and format as markdown.

        Args:
            state: Current workflow state containing topics_data

        Returns:
            Dict with updated state fields (study_guide_data, study_guide_markdown, errors)
        """
        request_id = state["request_id"]
        topics_data = state.get("topics_data", {})

        if not topics_data:
            logger.error(f"[{request_id}] [{self.name}] No topics data available for study guide generation")
            return {
                "study_guide_data": {},
                "study_guide_markdown": "",
                "errors": ["StudyGuideAgent: No topics available for study guide generation"],
                "current_step": "study_guide_failed"
            }

        logger.info(f"[{request_id}] [{self.name}] Generating study guide from {len(topics_data)} topics")

        try:
            study_guide = self._make_study_guide(
                topics_data,
                include_summary=True,
                include_key_points=True
            )

            if "error" in study_guide:
                logger.error(f"[{request_id}] [{self.name}] Study guide generation returned error: {study_guide['error']}")
                return {
                    "study_guide_data": {},
                    "study_guide_markdown": "",
                    "errors": [f"StudyGuideAgent: {study_guide['error']}"],
                    "current_step": "study_guide_failed"
                }

            logger.info(f"[{request_id}] [{self.name}] Study guide generated successfully")

            logger.info(f"[{request_id}] [{self.name}] Formatting study guide as markdown")
            markdown = self._format_as_markdown(study_guide)

            if markdown.startswith("# Error"):
                logger.error(f"[{request_id}] [{self.name}] Markdown formatting returned error")
                return {
                    "study_guide_data": study_guide,
                    "study_guide_markdown": "",
                    "errors": ["StudyGuideAgent: Failed to format study guide as markdown"],
                    "current_step": "study_guide_failed"
                }

            logger.info(f"[{request_id}] [{self.name}] Successfully generated {len(markdown)} character markdown study guide")

            return {
                "study_guide_data": study_guide,
                "study_guide_markdown": markdown,
                "errors": [],
                "current_step": "study_guide_complete"
            }

        except Exception as e:
            error_msg = f"StudyGuideAgent: {str(e)}"
            logger.error(f"[{request_id}] [{self.name}] Error generating study guide: {str(e)}")
            return {
                "study_guide_data": {},
                "study_guide_markdown": "",
                "errors": [error_msg],
                "current_step": "study_guide_failed"
            }

