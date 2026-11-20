import argparse
import json
import sys
import time
import urllib.error
import urllib.request


def get_response(url: str):
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=15) as response:
        body = response.read().decode("utf-8")
        return response.status, body


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("--expect-version")
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")
    health_url = f"{base_url}/health"

    # Wait until the expected version is live, if one was specified.
    deadline = time.time() + 300

    while True:
        try:
            status, body = get_response(health_url)
            health = json.loads(body)

            if status == 200 and health.get("status") == "ok":
                version = health.get("version", "unknown")

                if not args.expect_version or version == args.expect_version:
                    print(f"ok   /health -> {status}, version {version}")
                    break

                print(f"waiting: /health -> {status}, version {version}")

        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            print(f"waiting: /health -> {error}")

        if time.time() >= deadline:
            print("Smoke test failed: expected version did not become live.")
            sys.exit(1)

        time.sleep(5)

    # Check database readiness.
    try:
        status, body = get_response(f"{base_url}/ready")
        ready = json.loads(body)

        if status != 200 or ready.get("status") != "ready":
            raise RuntimeError(f"/ready failed: {status} {body}")

        print(f"ok   /ready -> {status} {ready}")

    except Exception as error:
        print(f"Smoke test failed: {error}")
        sys.exit(1)

    # Check that the documents API is serving requests.
    try:
        status, _ = get_response(f"{base_url}/v1/documents?limit=1")

        if status != 200:
            raise RuntimeError(f"/v1/documents returned {status}")

        print(f"ok   /v1/documents?limit=1 -> {status}")

    except Exception as error:
        print(f"Smoke test failed: {error}")
        sys.exit(1)

    print("Smoke test passed")


if __name__ == "__main__":
    main()
