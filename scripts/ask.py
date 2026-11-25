"""Ask TaxDost a question from the command line."""

import argparse
import json
import sys
import time

import httpx


def show_problem(response: httpx.Response) -> None:
    """Display an API error in a readable format."""
    response.read()

    try:
        detail = response.json().get("detail", response.text)
    except (ValueError, AttributeError):
        detail = response.text

    print(f"\nAPI error ({response.status_code}): {detail}", file=sys.stderr)


def summary(info: dict, first: float, total: float) -> None:
    """Display model and usage information."""
    print("\n\n--- TaxDost usage ---")
    print(f"Provider:       {info.get('provider', 'unknown')}")
    print(f"Model:          {info.get('model', 'unknown')}")
    print(f"First word:     {first:.2f}s")
    print(f"Total time:     {total:.2f}s")
    print(f"Input tokens:   {info.get('tokens_in', 0)}")
    print(f"Output tokens:  {info.get('tokens_out', 0)}")
    print(f"Cost:           INR {info.get('cost_inr', 0)}")
    print(f"Attempts:       {info.get('attempts', 0)}")
    print(f"Fallback used:  {info.get('fallback_used', False)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask TaxDost a question.")
    parser.add_argument("question", help="Your tax question")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="TaxDost API base URL",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Return a normal JSON response instead of streaming",
    )
    args = parser.parse_args()

    payload = {
        "message": args.question,
        "stream": not args.json,
    }

    url = f"{args.url.rstrip('/')}/v1/chat"
    started = time.perf_counter()
    first_word = None

    try:
        with httpx.stream(
            "POST",
            url,
            json=payload,
            timeout=120,
        ) as response:
            if response.status_code >= 400:
                show_problem(response)
                return

            if args.json:
                response.read()
                body = response.json()
                print(body.get("answer", ""))
                total = time.perf_counter() - started
                summary(body, total, total)
                return

            event_name = ""

            for line in response.iter_lines():
                if line.startswith("event:"):
                    event_name = line[6:].strip()

                elif line.startswith("data:"):
                    data = json.loads(line[5:].strip())

                    if event_name == "done":
                        total = time.perf_counter() - started
                        if first_word is None:
                            first_word = total
                        summary(data, first_word, total)

                    elif event_name == "error":
                        print(
                            f"\n\nStream error: {data.get('detail', 'Unknown error')}",
                            file=sys.stderr,
                        )

                    else:
                        piece = data.get("delta", "")
                        if piece:
                            if first_word is None:
                                first_word = time.perf_counter() - started
                            print(piece, end="", flush=True)

                    event_name = ""

    except httpx.TransportError as exc:
        print(
            f"Could not connect to TaxDost at {url}: {exc}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
