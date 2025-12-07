"""
Test script for the study guide generation functionality
"""
import sys
import os
import json

# Add the parent directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.gemini import extract_unique_topics_with_text, make_study_guide, format_study_guide_as_markdown


def test_with_sample_text():
    """Test the study guide generation with sample educational text"""

    # Sample educational text
    sample_text = """
    Machine Learning Fundamentals
    
    Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on the development of computer programs that can access data and use it to learn for themselves.
    
    There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Supervised learning uses labeled data to train models, where each example is paired with an output label. The algorithm learns to predict the output from the input data.
    
    Unsupervised learning works with unlabeled data. The algorithm tries to find patterns and relationships in the data without any guidance about what to look for. Common techniques include clustering and dimensionality reduction.
    
    Neural Networks
    
    Neural networks are computing systems inspired by biological neural networks. They consist of interconnected nodes (neurons) organized in layers. Each connection has a weight that adjusts as learning proceeds.
    
    A typical neural network has an input layer, one or more hidden layers, and an output layer. Deep learning refers to neural networks with many hidden layers. These deep networks can learn hierarchical representations of data.
    
    Training a neural network involves forward propagation and backpropagation. During forward propagation, input data passes through the network to produce an output. Backpropagation calculates the gradient of the loss function and updates the weights to minimize error.
    
    Data Preprocessing
    
    Data preprocessing is a crucial step in machine learning. Raw data often contains noise, missing values, and inconsistencies that can affect model performance. Preprocessing transforms raw data into a clean, usable format.
    
    Common preprocessing steps include handling missing values, scaling features, encoding categorical variables, and removing outliers. Feature scaling ensures all features contribute equally to the model. Normalization scales features to a range of 0 to 1, while standardization scales features to have zero mean and unit variance.
    """

    print("=" * 80)
    print("STEP 1: Extracting Topics from Text")
    print("=" * 80)

    # Extract topics
    topics_data = extract_unique_topics_with_text(sample_text)
    print(f"\nExtracted {len(topics_data)} topics:")
    print(json.dumps(topics_data, indent=2))

    print("\n" + "=" * 80)
    print("STEP 2: Generating Study Guide")
    print("=" * 80)

    # Generate a study guide with all features
    study_guide = make_study_guide(
        topics_data=topics_data,
        include_summary=True,
        include_key_points=True
    )

    print(f"\nStudy Guide Type: {study_guide['metadata']['guide_type']}")
    print(f"Total Topics: {study_guide['metadata']['total_topics']}")
    print(f"Content Length: {study_guide['metadata']['content_length']} characters")

    print("\n" + "=" * 80)
    print("STEP 3: Formatted Study Guide (JSON)")
    print("=" * 80)
    print(json.dumps(study_guide, indent=2))

    print("\n" + "=" * 80)
    print("STEP 4: Markdown Formatted Study Guide")
    print("=" * 80)

    # Format as Markdown
    markdown_guide = format_study_guide_as_markdown(study_guide)
    print(markdown_guide)

    # Save to file
    with open("study_guide_output.md", "w") as f:
        f.write(markdown_guide)

    print("\n✓ Study guide saved to 'study_guide_output.md'")

    return study_guide


def test_with_short_text():
    """Test with shorter text to see concise guide generation"""

    short_text = """
    Python is a high-level programming language known for its simplicity and readability. 
    It uses indentation to define code blocks and supports multiple programming paradigms.
    """

    print("\n" + "=" * 80)
    print("TESTING WITH SHORT TEXT")
    print("=" * 80)

    topics = extract_unique_topics_with_text(short_text)
    guide = make_study_guide(topics, include_summary=True, include_key_points=True)

    print(f"\nGuide Type: {guide['metadata']['guide_type']}")
    print(json.dumps(guide, indent=2))


def test_minimal_guide():
    """Test with summary and key points disabled"""

    minimal_topics = {
        "Python Basics": "Python is an interpreted, high-level programming language.",
        "Variables": "Variables store data that can be referenced and manipulated in a program."
    }

    print("\n" + "=" * 80)
    print("TESTING MINIMAL GUIDE (No Summary or Key Points)")
    print("=" * 80)

    guide = make_study_guide(
        topics_data=minimal_topics,
        include_summary=False,
        include_key_points=False
    )

    print(json.dumps(guide, indent=2))


if __name__ == "__main__":
    print("Testing Study Guide Generation\n")

    try:
        # Test 1: Full-featured guide with sample text
        test_with_sample_text()

        # Test 2: Short text (concise guide)
        test_with_short_text()

        # Test 3: Minimal guide
        test_minimal_guide()

        print("\n" + "=" * 80)
        print("ALL TESTS COMPLETED SUCCESSFULLY!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        import traceback
        traceback.print_exc()
