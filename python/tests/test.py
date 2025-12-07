import os
import sys

# Add the parent directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.youtubeTranscript import get_youtube_transcript

def main():
    # pdf_path = "sample.pdf"
    # extracted_text = extract_pdf_text(pdf_path)
    # print(f"Extracted {len(extracted_text)} characters from PDF")

    sample_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    transcript = get_youtube_transcript(sample_url)
    print("Transcript length:", len(transcript))
    print("First 500 characters:", transcript[:500])


if __name__ == "__main__":
    main()