"""Tests for structured document metadata extraction."""

import asyncio
import json

import pytest

from taxdost.llm.doc_meta import DocMeta
from taxdost.llm.extract import RESERVED, explain, extract, parse_json
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


def valid_reply() -> str:
    return json.dumps(VALID)


def test_parse_json_from_markdown_fence():
    result = parse_json(f"```json\n{valid_reply()}\n```")
    assert result["doc_kind"] == "guideline"


def test_parse_json_rejects_missing_object():
    with pytest.raises(ValueError, match="no JSON object"):
        parse_json("There is no JSON here.")


def test_parse_json_rejects_non_object():
    with pytest.raises(ValueError, match="no JSON object"):
        parse_json('["not", "an", "object"]')


def test_explain_validation_error():
    from pydantic import ValidationError

    with pytest.raises(ValidationError) as error:
        DocMeta.model_validate({"doc_kind": "unknown"})

    message = explain(error.value)
    assert "doc_kind" in message


def test_extract_valid_metadata():
    async def work():
        llm = FakeLLM(script=[valid_reply()])
        gateway = LLMGateway([llm])

        result = await extract(
            gateway,
            DocMeta,
            "Extract document metadata.",
            "extract_v1",
            "Income Tax Guideline",
            "Document text goes here.",
        )

        assert result.record is not None
        assert result.record.doc_kind == "guideline"
        assert result.attempts == 1
        assert result.errors == []
        assert llm.calls == 1

    asyncio.run(work())


def test_extract_retries_invalid_metadata():
    async def work():
        llm = FakeLLM(script=["not JSON", valid_reply()])
        gateway = LLMGateway([llm])

        result = await extract(
            gateway,
            DocMeta,
            "Extract document metadata.",
            "extract_v1",
            "Income Tax Guideline",
            "Document text goes here.",
        )

        assert result.record is not None
        assert result.attempts == 2
        assert len(result.errors) == 1
        assert llm.calls == 2
        assert "rejected" in llm.seen[1]["messages"][-1]["content"]

    asyncio.run(work())


def test_extract_returns_failure_after_max_attempts():
    async def work():
        llm = FakeLLM(script=["bad", "still bad"])
        gateway = LLMGateway([llm])

        result = await extract(
            gateway,
            DocMeta,
            "Extract document metadata.",
            "extract_v1",
            "Income Tax Guideline",
            "Document text goes here.",
            max_attempts=2,
        )

        assert result.record is None
        assert result.attempts == 2
        assert len(result.errors) == 2

    asyncio.run(work())


def test_native_schema_is_forwarded_to_provider():
    async def work():
        llm = FakeLLM(script=[valid_reply()])
        gateway = LLMGateway([llm])

        await extract(
            gateway,
            DocMeta,
            "Extract document metadata.",
            "extract_v1",
            "Income Tax Guideline",
            "Document text goes here.",
            native_schema=True,
        )

        response_format = llm.seen[0]["response_format"]
        assert response_format["type"] == "json_schema"
        assert response_format["json_schema"]["name"] == "DocMeta"

    asyncio.run(work())


def test_reserved_fields_are_known():
    assert "source" in RESERVED
    assert "pages" in RESERVED
    assert "extract" in RESERVED
