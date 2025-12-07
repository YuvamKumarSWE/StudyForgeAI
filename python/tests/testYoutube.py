import sys
import os

# Add the parent directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from app.services.youtubeTranscript import get_youtube_transcript

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

text2 = get_youtube_transcript(url)
print(text2[:500])
