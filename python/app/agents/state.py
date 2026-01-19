"""
State definition for the multi-agent study guide generation workflow.
"""
from typing import TypedDict, List, Dict, Any, Annotated
from operator import add


def merge_dicts(left: Dict, right: Dict) -> Dict:
    """Merge two dictionaries, with right values taking precedence."""
    if not left:
        return right
    if not right:
        return left
    merged = left.copy()
    merged.update(right)
    return merged


def last_value(left: str, right: str) -> str:
    """Return the last non-empty value."""
    return right if right else left


class ContentItem(TypedDict):
    """Structure for content extracted from each source."""
    source: str
    source_type: str  # 'pdf', 'url', 'youtube', 'text'
    content: str
    metadata: Dict[str, Any]


class StudyGuideState(TypedDict):
    """
    Shared state for the multi-agent workflow.

    All agents read from and write to this state.
    Uses Annotated types with reducers for fields that receive concurrent updates.
    """
    # Request metadata
    request_id: str

    # Input sources - populated by the main agent/router
    pdf_files: List[Any]  # UploadFile objects from FastAPI
    urls: List[str]
    youtube_urls: List[str]
    text_inputs: List[str]

    # Agent outputs - each agent populates its respective field (no concurrency issue)
    pdf_content: List[ContentItem]
    url_content: List[ContentItem]
    youtube_content: List[ContentItem]
    text_content: List[ContentItem]

    # Combined content - populated by collector
    all_content: List[ContentItem]
    combined_text: str

    # After topic extraction/deduplication
    topics_data: Dict[str, str]

    # Final outputs
    study_guide_data: Dict[str, Any]
    study_guide_markdown: str

    # Processing metadata - use reducers for concurrent updates
    current_step: Annotated[str, last_value]
    errors: Annotated[List[str], add]  # Concatenate error lists
    processing_stats: Annotated[Dict[str, Any], merge_dicts]  # Merge stats dicts


def create_initial_state(
    request_id: str,
    pdf_files: List[Any] = None,
    urls: List[str] = None,
    youtube_urls: List[str] = None,
    text_inputs: List[str] = None
) -> StudyGuideState:
    """
    Create an initial state for the workflow.

    Args:
        request_id: Unique identifier for the request
        pdf_files: List of PDF UploadFile objects
        urls: List of web article URLs
        youtube_urls: List of YouTube video URLs
        text_inputs: List of raw text inputs

    Returns:
        StudyGuideState: Initialized state dictionary
    """
    return StudyGuideState(
        request_id=request_id,
        pdf_files=pdf_files or [],
        urls=urls or [],
        youtube_urls=youtube_urls or [],
        text_inputs=text_inputs or [],
        pdf_content=[],
        url_content=[],
        youtube_content=[],
        text_content=[],
        all_content=[],
        combined_text="",
        topics_data={},
        study_guide_data={},
        study_guide_markdown="",
        current_step="initialized",
        errors=[],
        processing_stats={
            "pdf_success": 0,
            "pdf_fail": 0,
            "url_success": 0,
            "url_fail": 0,
            "youtube_success": 0,
            "youtube_fail": 0,
            "text_success": 0,
            "text_fail": 0,
        }
    )

