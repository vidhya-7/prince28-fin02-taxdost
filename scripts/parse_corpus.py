"""Parse downloaded corpus files and save documents/pages to Postgres."""

import argparse
import asyncio
import json
from pathlib import Path

from taxdost.config import get_settings
from taxdost.db.session import make_engine, make_sessionmaker
from taxdost.ingest.store import (
    document_id,
    failed_paths,
    parsed_ids,
    save_document,
    save_failure,
)
from taxdost.parse import ParseError, parse_file, parse_pdf_ocr

MANIFEST = Path("data/manifest.jsonl")


def load_records() -> list[dict]:
    """Load the latest downloaded manifest record for each URL."""
    latest = {}

    with MANIFEST.open(encoding="utf-8") as file:
        for line in file:
            record = json.loads(line)
            latest[record["url"]] = record

    return [
        record
        for record in latest.values()
        if record.get("status") == "downloaded"
        and record.get("path")
        and Path(record["path"]).is_file()
    ]


async def run(limit: int | None, retry_failed: bool, ocr: bool) -> None:
    settings = get_settings()
    engine = make_engine(settings)
    Session = make_sessionmaker(engine)

    already_parsed = 0
    failed_before = 0
    parsed_count = 0
    failure_count = 0
    page_count = 0

    try:
        async with Session() as session:
            existing_ids = await parsed_ids(session)
            previous_failures = await failed_paths(session)

            records = load_records()

            for record in records:
                external_id = document_id(record["sha256"])
                path = record["path"]

                if external_id in existing_ids:
                    already_parsed += 1
                    continue

                if path in previous_failures and not retry_failed:
                    failed_before += 1
                    continue

                if limit is not None and parsed_count + failure_count >= limit:
                    break

                try:
                    parsed = parse_file(Path(path))

                    if ocr is False:
                        pass

                except ParseError as error:
                    if error.reason == "no_text_layer" and ocr:
                        try:
                            parsed = parse_pdf_ocr(Path(path))
                        except ParseError as ocr_error:
                            await save_failure(session, record, ocr_error)
                            failure_count += 1
                            continue
                    else:
                        await save_failure(session, record, error)
                        failure_count += 1
                        continue

                await save_document(session, record, parsed)
                existing_ids.add(external_id)
                parsed_count += 1
                page_count += len(parsed.pages)

                print(f"PARSED: {record.get('title', path)} ({len(parsed.pages)} pages)")

    finally:
        await engine.dispose()

    print("\n--- Parsing summary ---")
    print(f"Downloaded files available: {len(load_records())}")
    print(f"Parsed this run: {parsed_count}")
    print(f"Pages saved: {page_count}")
    print(f"Failures this run: {failure_count}")
    print(f"Already parsed: {already_parsed}")
    print(f"Failed previously (skipped): {failed_before}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse downloaded TaxDost corpus files.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()

    asyncio.run(run(args.limit, args.retry_failed, args.ocr))


if __name__ == "__main__":
    main()
