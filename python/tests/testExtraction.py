import sys
import os

# Add the parent directory to sys.path so 'app' can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.webArticleExtraction import extract_web_article

result = extract_web_article("https://en.wikipedia.org/wiki/Python_(programming_language)")
print(result["title"])
print(result["text"][:500])
