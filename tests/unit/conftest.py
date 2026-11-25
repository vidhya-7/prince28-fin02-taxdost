import pytest
from fastapi.testclient import TestClient

from taxdost.api.deps import (
    check_db,
    get_gateway,
    get_repo,
    get_usage_repo,
)
from taxdost.api.main import create_app
from taxdost.config import Settings
from taxdost.llm.gateway import FakeLLM, LLMGateway

# Tiny fake records: unit tests never touch a real database or your data file.
SAMPLE = [
    {"id": "001", "title": "Alpha guideline", "year": 2023, "kind": "guideline"},
    {"id": "002", "title": "Beta circular", "year": 2024, "kind": "circular"},
    {"id": "003", "title": "Gamma notice", "year": 2025, "kind": "circular"},
]


class FakeRepo:
    """Behaves like DocumentRepository, but keeps rows in a Python list."""

    def __init__(self, rows):
        self.rows = rows

    async def list(self, *, q, filters, limit, offset):
        rows = [
            r
            for r in self.rows
            if (not q or q.lower() in str(r).lower())
            and all(str(r.get(k)) == v for k, v in filters.items())
        ]
        return len(rows), rows[offset : offset + limit]

    async def get(self, external_id):
        return next((r for r in self.rows if r["id"] == external_id), None)


class FakeUsage:
    """Returns predictable usage totals for API unit tests."""

    async def by_day(self, days=7):
        return [
            {
                "day": "2026-11-25",
                "calls": 3,
                "errors": 0,
                "fallbacks": 0,
                "tokens_in": 300,
                "tokens_out": 150,
                "cost_inr": 0.0642,
            }
        ]


@pytest.fixture
def settings():
    # Ignore the local .env so tests behave the same everywhere.
    return Settings(
        app_env="ci",
        database_url="postgresql://localhost:5432/unused",
        _env_file=None,
    )


@pytest.fixture
def db_state():
    return {"up": True}


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(settings, db_state, llm):
    app = create_app(settings)
    gateway = LLMGateway([llm])

    app.dependency_overrides[get_repo] = lambda: FakeRepo(SAMPLE)
    app.dependency_overrides[check_db] = lambda: db_state["up"]
    app.dependency_overrides[get_gateway] = lambda: gateway
    app.dependency_overrides[get_usage_repo] = lambda: FakeUsage()

    with TestClient(app) as test_client:
        yield test_client
