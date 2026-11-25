"""Check Gemini and Groq API connections."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from taxdost.config import get_settings


def ping(name, base_url, api_key, model):
    print(f"\nTesting {name} ({model})...")

    if not api_key:
        print(f"FAILED: {name} API key is missing")
        return

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": "Reply with: Hello from TaxDost!"}],
    }

    if name == "Groq":
        payload["max_completion_tokens"] = 256
        payload["reasoning_effort"] = "low"
    else:
        payload["max_tokens"] = 256

    request = Request(
        f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "TaxDost/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read().decode())
            choice = result["choices"][0]
            content = choice["message"].get("content")

            print("SUCCESS: API request completed")
            print("Answer:", repr(content))
            print("Finish reason:", choice.get("finish_reason"))
            print("Usage:", result.get("usage"))

            if not content:
                print("WARNING: No visible text was returned.")

    except HTTPError as error:
        print(f"FAILED: HTTP {error.code}")
        print(error.read().decode()[:500])
    except (URLError, TimeoutError, KeyError, ValueError) as error:
        print(f"FAILED: {type(error).__name__}: {error}")


def main():
    settings = get_settings()

    ping(
        "Gemini",
        settings.llm_primary_base_url,
        settings.gemini_api_key,
        settings.llm_primary_model,
    )

    ping(
        "Groq",
        settings.llm_fallback_base_url,
        settings.groq_api_key,
        settings.llm_fallback_model,
    )


if __name__ == "__main__":
    main()
