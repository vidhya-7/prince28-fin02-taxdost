"""Extract and validate metadata for TaxDost documents."""

import argparse
import asyncio

from taxdost.config import get_settings
from taxdost.db.session import make_engine, make_sessionmaker
from taxdost.llm.doc_meta import DocMeta
from taxdost.llm.extract import run
from taxdost.llm.gateway import build_gateway
from taxdost.llm.prompts import find_prompt_versions, load_prompt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--rpm", type=float, default=12)
    parser.add_argument("--chars", type=int, default=6000)
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--schema", action="store_true")
    args = parser.parse_args()

    settings = get_settings()

    versions = find_prompt_versions("extract", settings.prompts_dir)
    if not versions:
        raise SystemExit("No extract prompt found in the prompts directory.")

    prompt_path = versions[-1]
    version = prompt_path.stem
    number = int(version.rsplit("_v", 1)[1])
    prompt = load_prompt("extract", number, settings.prompts_dir)

    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)
    gateway = build_gateway(settings)

    async def work() -> None:
        counts = await run(
            sessionmaker,
            gateway,
            DocMeta,
            prompt,
            version,
            limit=args.limit,
            rpm=args.rpm,
            chars=args.chars,
            retry_failed=args.retry_failed,
            native=args.schema,
        )

        print("\nExtraction summary")
        for key, value in sorted(counts.items()):
            print(f"{key}: {value}")

        if counts["pending"] == 0:
            print("No pending documents for this prompt version.")

    asyncio.run(work())


if __name__ == "__main__":
    main()
