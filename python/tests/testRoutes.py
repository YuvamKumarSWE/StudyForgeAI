import requests
import json

url = "http://localhost:8000/api/get-output"

# files = [
#     ('pdfs', ('python/app/sample.pdf', open('python/app/sample.pdf', 'rb'), 'application/pdf'))
# ]

payload = {
    "urls": ["https://www.tie-a-tie.net/fourinhand/"],
    "videos": ["https://www.youtube.com/watch?v=fAQmCNWJHb8"],
    "text": ["hello from python test"]
}

data = {
    "sources": json.dumps(payload)
}

response = requests.post(url, data=data)

print(response.status_code)
print(response.json())
