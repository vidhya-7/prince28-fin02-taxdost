import asyncio
import json
from pathlib import Path
from types import SimpleNamespace

from taxdost.llm.classify import (
    accuracy,
    build_messages,
    classify,
    find_leaks,
    parse_label,
)


def test_build_messages_separates_system_and_user_question():
    messages = build_messages("Classify the question.", "  Who can file ITR-1?  ")

    assert messages[0] == {
        "role": "system",
        "content": "Classify the question.",
    }
    assert messages[1] == {
        "role": "user",
        "content": "<question>\nWho can file ITR-1?\n</question>",
    }


def test_parse_label_accepts_docs():
    assert parse_label("docs") == "docs"


def test_parse_label_accepts_capitals_and_punctuation():
    assert parse_label("OFF-TOPIC!") == "off_topic"


def test_parse_label_rejects_invalid_or_multiple_labels():
    assert parse_label("maybe") == "invalid"
    assert parse_label("docs and personal") == "invalid"


def test_accuracy_calculates_correct_predictions():
    rows = [
        {"label": "docs", "got": "docs"},
        {"label": "personal", "got": "docs"},
        {"label": "off_topic", "got": "off_topic"},
    ]

    assert accuracy(rows) == 2 / 3
    assert accuracy([]) == 0.0


def test_find_leaks_detects_questions_inside_prompt():
    prompt = "Example question: Who can file ITR-1?"
    questions = [
        "who can file itr-1?",
        "What is Section 80C?",
    ]

    assert find_leaks(prompt, questions) == ["who can file itr-1?"]

    repo_root = Path(__file__).resolve().parents[2]

    prompt_files = list((repo_root / "prompts").glob("classify_v*.md"))
    assert len(prompt_files) >= 3

    testset = repo_root / "eval" / "prompt_testset.jsonl"
    rows = [json.loads(line) for line in testset.read_text(encoding="utf-8").splitlines()]

    assert len(rows) >= 20
    assert all(
        row.get("label") in {"docs", "personal", "off_topic"}
        and isinstance(row.get("question"), str)
        and row["question"].strip()
        for row in rows
    )


def test_classify_calls_gateway_and_returns_label():
    class FakeGateway:
        async def generate(self, messages, **options):
            self.messages = messages
            self.options = options
            return SimpleNamespace(text="docs")

    async def run_test():
        gateway = FakeGateway()

        label, result = await classify(
            gateway,
            "Classify the question.",
            "v2",
            "Who can file ITR-1?",
        )

        assert label == "docs"
        assert result.text == "docs"
        assert gateway.options == {
            "purpose": "classify",
            "prompt_version": "v2",
            "temperature": 0,
        }
        assert gateway.messages[1]["role"] == "user"

    asyncio.run(run_test())
