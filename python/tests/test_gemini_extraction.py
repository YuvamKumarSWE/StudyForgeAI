#!/usr/bin/env python3
"""
Test for the extract_unique_topics_with_text function.
Tests deduplication of similar content across topics.
"""

import sys
import os
import json

# Add the parent directory to the path so we can import from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.topics_agent import TopicsAgent

# Create agent instance for testing
_topics_agent = TopicsAgent()

def extract_unique_topics_with_text(text: str) -> dict:
    """Wrapper for testing"""
    return _topics_agent._extract_topics(text)

def test_extract_unique_topics():
    """Test the extract_unique_topics_with_text function with a sample text containing duplicates."""

    # Sample text with 2 topics, each having similar/repeated information
    sample_text = """
    Machine learning is a subset of artificial intelligence that enables computers to learn without being explicitly programmed.
    ML algorithms build mathematical models based on training data to make predictions or decisions.
    Machine learning uses statistical techniques to give computers the ability to learn from data.
    ML is a method of data analysis that automates analytical model building.

    Deep learning is part of machine learning that uses neural networks with multiple layers.
    Deep learning algorithms are inspired by the structure and function of the human brain.
    Neural networks in deep learning can automatically learn features from data.
    Deep learning uses artificial neural networks to model complex patterns in data.
    Deep learning is a subset of machine learning that uses neural networks with many layers.
    """

    print("Testing extract_unique_topics_with_text function...")
    print("=" * 60)
    print("Sample text contains:")
    print("- Machine Learning topic with repeated/similar information")
    print("- Deep Learning topic with repeated/similar information")
    print("=" * 60)

    try:
        result = extract_unique_topics_with_text(sample_text)

        print("Result:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        print("\n" + "=" * 60)
        print("Test completed successfully!")

    except Exception as e:
        print(f"Error occurred: {e}")
        print("Make sure your GEMINI_API_KEY is set in the .env file")

if __name__ == "__main__":
    test_extract_unique_topics()
