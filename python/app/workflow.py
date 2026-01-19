from typing import Dict, Any, List
from langgraph.graph import StateGraph, END

from app.agents.state import StudyGuideState, create_initial_state, ContentItem
from app.agents.pdf_agent import PDFAgent
from app.agents.youtube_agent import YouTubeAgent
from app.agents.web_agent import WebAgent
from app.agents.text_agent import TextAgent
from app.agents.topics_agent import TopicsAgent
from app.agents.study_guide_agent import StudyGuideAgent
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
pdf_agent = PDFAgent()
youtube_agent = YouTubeAgent()
web_agent = WebAgent()
text_agent = TextAgent()
topics_agent = TopicsAgent()
study_guide_agent = StudyGuideAgent()

async def route_inputs(state: StudyGuideState) -> Dict[str, Any]:
    """
    Route node - categorizes inputs and prepares for parallel processing.
    This is the entry point of the workflow.
    """
    request_id = state["request_id"]
    logger.info(f"[{request_id}] [Router] Categorizing inputs for parallel processing")

    # Log input summary
    pdf_count = len(state.get("pdf_files", []))
    url_count = len(state.get("urls", []))
    youtube_count = len(state.get("youtube_urls", []))
    text_count = len(state.get("text_inputs", []))

    logger.info(f"[{request_id}] [Router] Found: {pdf_count} PDFs, {url_count} URLs, {youtube_count} YouTube videos, {text_count} text inputs")

    return {
        "current_step": "routing_complete"
    }


async def process_pdfs(state: StudyGuideState) -> Dict[str, Any]:
    """Process PDF files using PDFAgent."""
    return await pdf_agent.process(state)


async def process_youtube(state: StudyGuideState) -> Dict[str, Any]:
    """Process YouTube videos using YouTubeAgent."""
    return await youtube_agent.process(state)


async def process_urls(state: StudyGuideState) -> Dict[str, Any]:
    """Process web URLs using WebAgent."""
    return await web_agent.process(state)


async def process_text(state: StudyGuideState) -> Dict[str, Any]:
    """Process text inputs using TextAgent."""
    return await text_agent.process(state)


async def collect_results(state: StudyGuideState) -> Dict[str, Any]:
    """
    Collector node - combines all extracted content from parallel agents.
    """
    request_id = state["request_id"]
    logger.info(f"[{request_id}] [Collector] Combining results from all agents")

    # Gather all content
    all_content: List[ContentItem] = []

    # Add content from each agent
    for content_item in state.get("pdf_content", []):
        all_content.append(content_item)

    for content_item in state.get("youtube_content", []):
        all_content.append(content_item)

    for content_item in state.get("url_content", []):
        all_content.append(content_item)

    for content_item in state.get("text_content", []):
        all_content.append(content_item)

    # Combine all text content
    text_parts = []
    for item in all_content:
        source = item.get("source", "unknown")
        source_type = item.get("source_type", "unknown")
        content = item.get("content", "")

        if content:
            # Add source header for context
            text_parts.append(f"\n{'='*60}")
            text_parts.append(f"Source: {source} (Type: {source_type})")
            text_parts.append(f"{'='*60}\n")
            text_parts.append(content)

    combined_text = "\n\n".join(text_parts)

    # Calculate stats
    stats = state.get("processing_stats", {})
    total_success = (
        stats.get("pdf_success", 0) +
        stats.get("url_success", 0) +
        stats.get("youtube_success", 0) +
        stats.get("text_success", 0)
    )
    total_fail = (
        stats.get("pdf_fail", 0) +
        stats.get("url_fail", 0) +
        stats.get("youtube_fail", 0) +
        stats.get("text_fail", 0)
    )

    logger.info(f"[{request_id}] [Collector] Combined {len(all_content)} content items ({total_success} successful, {total_fail} failed)")
    logger.info(f"[{request_id}] [Collector] Total combined text: {len(combined_text)} characters")

    return {
        "all_content": all_content,
        "combined_text": combined_text,
        "current_step": "collection_complete"
    }


async def extract_topics(state: StudyGuideState) -> Dict[str, Any]:
    """Extract topics and deduplicate content using TopicsAgent."""
    return await topics_agent.process(state)


async def generate_study_guide(state: StudyGuideState) -> Dict[str, Any]:
    """Generate final study guide using StudyGuideAgent."""
    return await study_guide_agent.process(state)


def should_continue_to_topics(state: StudyGuideState) -> str:
    """
    Conditional edge: Check if we have content to process.
    Returns the next node name or END.
    """
    combined_text = state.get("combined_text", "")

    if not combined_text or not combined_text.strip():
        logger.warning(f"[{state['request_id']}] No content extracted, cannot proceed to topic extraction")
        return "end_no_content"

    return "topics"


def should_continue_to_study_guide(state: StudyGuideState) -> str:
    """
    Conditional edge: Check if topics were extracted successfully.
    Returns the next node name or END.
    """
    topics_data = state.get("topics_data", {})

    if not topics_data:
        logger.warning(f"[{state['request_id']}] No topics extracted, cannot proceed to study guide generation")
        return "end_no_topics"

    return "study_guide"


async def end_no_content(state: StudyGuideState) -> Dict[str, Any]:
    """End node when no content is available."""
    request_id = state["request_id"]
    logger.error(f"[{request_id}] Workflow ended: No content could be extracted from any sources")

    return {
        "study_guide_markdown": "# Error\n\nNo content could be extracted from the provided sources. Please check your inputs and try again.",
        "errors": ["No content could be extracted from the provided sources"],
        "current_step": "failed_no_content"
    }


async def end_no_topics(state: StudyGuideState) -> Dict[str, Any]:
    """End node when topic extraction fails."""
    request_id = state["request_id"]
    logger.error(f"[{request_id}] Workflow ended: Topic extraction failed")

    return {
        "study_guide_markdown": "# Error\n\nFailed to extract topics from the content. Please try again.",
        "errors": ["Failed to extract topics from the content"],
        "current_step": "failed_no_topics"
    }


# ====================
# Workflow Builder
# ====================

def create_study_guide_workflow() -> StateGraph:
    """
    Create and compile the LangGraph workflow for study guide generation.

    The workflow:
    1. Routes inputs to specialized agents
    2. Processes PDFs, YouTube videos, URLs, and text in PARALLEL
    3. Collects and combines all results
    4. Extracts topics and deduplicates content
    5. Generates and formats the final study guide

    Returns:
        Compiled StateGraph workflow
    """
    # Create the graph
    workflow = StateGraph(StudyGuideState)

    # Add nodes
    workflow.add_node("route", route_inputs)
    workflow.add_node("pdf", process_pdfs)
    workflow.add_node("youtube", process_youtube)
    workflow.add_node("url", process_urls)
    workflow.add_node("text", process_text)
    workflow.add_node("collect", collect_results)
    workflow.add_node("topics", extract_topics)
    workflow.add_node("study_guide", generate_study_guide)
    workflow.add_node("end_no_content", end_no_content)
    workflow.add_node("end_no_topics", end_no_topics)

    # Set entry point
    workflow.set_entry_point("route")

    # From router, fan out to all processing agents (parallel execution)
    workflow.add_edge("route", "pdf")
    workflow.add_edge("route", "youtube")
    workflow.add_edge("route", "url")
    workflow.add_edge("route", "text")

    # All processing agents converge at collector
    workflow.add_edge("pdf", "collect")
    workflow.add_edge("youtube", "collect")
    workflow.add_edge("url", "collect")
    workflow.add_edge("text", "collect")

    # From collector, conditionally proceed to topics or end
    workflow.add_conditional_edges(
        "collect",
        should_continue_to_topics,
        {
            "topics": "topics",
            "end_no_content": "end_no_content"
        }
    )

    # From topics, conditionally proceed to study guide or end
    workflow.add_conditional_edges(
        "topics",
        should_continue_to_study_guide,
        {
            "study_guide": "study_guide",
            "end_no_topics": "end_no_topics"
        }
    )

    # Terminal nodes
    workflow.add_edge("study_guide", END)
    workflow.add_edge("end_no_content", END)
    workflow.add_edge("end_no_topics", END)

    return workflow.compile()


# Create the compiled workflow singleton
study_guide_workflow = create_study_guide_workflow()

async def generate_study_guide_multi_agent(
    pdf_files: List[Any] = None,
    urls: List[str] = None,
    youtube_urls: List[str] = None,
    text_inputs: List[str] = None,
    request_id: str = None
) -> str:
    """
    Main entry point for multi-agent study guide generation.
    This function creates a new workflow state and executes the multi-agent workflow to generate a study guide from the provided inputs.
    """
    import time
    from fastapi import HTTPException

    # Generate request ID if not provided
    if not request_id:
        request_id = f"{int(time.time() * 1000)}"

    logger.info(f"[{request_id}] Starting multi-agent study guide generation")

    # Create initial state
    initial_state = create_initial_state(
        request_id=request_id,
        pdf_files=pdf_files or [],
        urls=urls or [],
        youtube_urls=youtube_urls or [],
        text_inputs=text_inputs or []
    )

    # Log input summary
    total_inputs = (
        len(initial_state["pdf_files"]) +
        len(initial_state["urls"]) +
        len(initial_state["youtube_urls"]) +
        len(initial_state["text_inputs"])
    )

    if total_inputs == 0:
        logger.error(f"[{request_id}] No inputs provided")
        raise HTTPException(
            status_code=400,
            detail="No inputs provided. Please provide at least one PDF, URL, YouTube video, or text input."
        )

    logger.info(f"[{request_id}] Processing {total_inputs} total inputs")

    try:
        # Execute the workflow
        final_state = await study_guide_workflow.ainvoke(initial_state)

        # Log completion
        errors = final_state.get("errors", [])
        if errors:
            logger.warning(f"[{request_id}] Workflow completed with {len(errors)} errors: {errors}")

        # Get the study guide markdown
        study_guide_markdown = final_state.get("study_guide_markdown", "")

        if not study_guide_markdown or study_guide_markdown.startswith("# Error"):
            error_detail = "; ".join(errors) if errors else "Unknown error"
            logger.error(f"[{request_id}] Study guide generation failed: {error_detail}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate study guide: {error_detail}"
            )

        logger.info(f"[{request_id}] Successfully generated study guide ({len(study_guide_markdown)} characters)")
        return study_guide_markdown

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error in workflow: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred: {str(e)}"
        )


# Backward compatibility function
async def generate_study_guide_from_inputs(
    pdfs: List[Any] = None,
    urls: List[str] = None,
    videos: List[str] = None,
    text: List[str] = None,
    request_id: str = None
) -> str:

    return await generate_study_guide_multi_agent(
        pdf_files=pdfs,
        urls=urls,
        youtube_urls=videos,  # Map 'videos' to 'youtube_urls'
        text_inputs=text,
        request_id=request_id
    )

