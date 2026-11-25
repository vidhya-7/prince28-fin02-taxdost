import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from taxdost.config import get_settings

settings = get_settings()

url = (
    "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent"
)

payload = {
    "contents": [{"parts": [{"text": "Reply with exactly: Hello from TaxDost!"}]}],
    "generationConfig": {"maxOutputTokens": 20},
}

request = Request(
    url,
    data=json.dumps(payload).encode(),
    headers={
        "x-goog-api-key": settings.gemini_api_key,
        "Content-Type": "application/json",
    },
    method="POST",
)

try:
    with urlopen(request, timeout=90) as response:
        result = json.loads(response.read().decode())
        print("SUCCESS")
        print(result["candidates"][0]["content"]["parts"][0]["text"])
except HTTPError as error:
    print("HTTP ERROR:", error.code)
    print(error.read().decode()[:500])
except (URLError, TimeoutError, KeyError, ValueError) as error:
    print("FAILED:", type(error).__name__, error)
