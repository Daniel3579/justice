import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "{}"}
)

print(response.json())