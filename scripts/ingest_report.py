"""Generate docs/INGEST_REPORT.md from the ingestion database."""

import asyncio
from pathlib import Path

from sqlalchemy import text

from taxdost.config import get_settings
from taxdost.db.session import make_engine

REPORT = Path("docs/INGEST_REPORT.md")
START = "<!-- generated:start -->"
END = "<!-- generated:end -->"


def update_report(documents: int, pages: int, dead_letter: int) -> None:
    generated = "\n".join(
        [
            START,
            "## Ingestion summary",
            "",
            f"- Documents ingested: {documents:,}",
            f"- Pages extracted: {pages:,}",
            f"- Dead-letter items: {dead_letter:,}",
            END,
        ]
    )

    if REPORT.exists():
        content = REPORT.read_text(encoding="utf-8")
    else:
        content = "# TaxDost ingestion report\n\n## What I learnt\n\n- \n- \n- \n"

    if START in content and END in content:
        before = content[: content.index(START)]
        after = content[content.index(END) + len(END) :]
        content = before + generated + after
    elif "## What I learnt" in content:
        position = content.index("## What I learnt")
        content = content[:position] + generated + "\n\n" + content[position:]
    else:
        content = content.rstrip() + "\n\n" + generated + "\n"

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(content, encoding="utf-8")


async def main() -> None:
    engine = make_engine(get_settings())

    try:
        async with engine.connect() as conn:
            documents = await conn.scalar(
                text("SELECT COUNT(*) FROM documents WHERE doc_type <> 'record'")
            )
            pages = await conn.scalar(
                text(
                    "SELECT COUNT(*) FROM pages p "
                    "JOIN documents d ON d.id = p.document_id "
                    "WHERE d.doc_type <> 'record'"
                )
            )
            dead_letter = await conn.scalar(
                text("SELECT COUNT(*) FROM ingest_items WHERE status = 'failed'")
            )

        documents = documents or 0
        pages = pages or 0
        dead_letter = dead_letter or 0

        update_report(documents, pages, dead_letter)

        print(f"documents={documents} pages={pages} dead_letter={dead_letter} -> {REPORT}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
