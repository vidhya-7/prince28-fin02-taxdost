"""Structured metadata extraction, saved into a real Postgres database."""

import json

import pytest
from sqlalchemy import select

from taxdost.config import Settings
from taxdost.db.models import Document, Page
from taxdost.db.session import make_engine, make_sessionmaker
from taxdost.llm.doc_meta import DocMeta
from taxdost.llm.extract import run
from taxdost.llm.gateway import FakeLLM, LLMGateway

VALID = {
    "doc_kind": "guideline",
    "year": 2025,
    "language": "en",
    "summary": "A guideline explaining income tax deductions and filing requirements.",
    "topics": ["income tax", "deductions"],
    "act": ["Income-tax Act"],
    "section": ["80C"],
    "old_section": [],
    "assessment_or_tax_year": ["2025-26"],
    "limit_amount": ["150000"],
}


@pytest.fixture
async def sessionmaker(database_url):
    engine = make_engine(Settings(app_env="ci", database_url=database_url, _env_file=None))

    factory = make_sessionmaker(engine)

    async with factory() as session:
        await session.execute(Page.__table__.delete())
        await session.execute(Document.__table__.delete())
        await session.commit()

    yield factory
    await engine.dispose()


async def test_extracted_metadata_is_saved_without_losing_parser_metadata(sessionmaker):
    async with sessionmaker() as session:
        document = Document(
            external_id="extract-test-001",
            title="Income Tax Guideline",
            sha256="cd" * 32,
            doc_type="pdf",
            metadata_={"parser": "pymupdf", "pages": 1},
        )
        session.add(document)
        await session.flush()

        session.add(
            Page(
                document_id=document.id,
                page_no=1,
                text="Income Tax Guideline. Section 80C explains deductions.",
            )
        )
        await session.commit()

    llm = FakeLLM(script=[json.dumps(VALID)])
    gateway = LLMGateway([llm])

    counts = await run(
        sessionmaker,
        gateway,
        DocMeta,
        "Extract document metadata.",
        "extract_v1",
        rpm=1000,
    )

    assert counts["pending"] == 1
    assert counts["ok"] == 1
    assert counts["failed"] == 0
    assert llm.calls == 1

    async with sessionmaker() as session:
        saved = await session.scalar(
            select(Document).where(Document.external_id == "extract-test-001")
        )

        assert saved.metadata_["parser"] == "pymupdf"
        assert saved.metadata_["pages"] == 1
        assert saved.metadata_["doc_kind"] == "guideline"
        assert saved.metadata_["section"] == ["80C"]
        assert saved.metadata_["extract"]["prompt"] == "extract_v1"
        assert "error" not in saved.metadata_["extract"]
