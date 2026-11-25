import pytest

from taxdost.config import Settings
from taxdost.db.llm_calls import UsageRepository, make_recorder
from taxdost.db.session import make_engine, make_sessionmaker
from taxdost.llm.gateway import FakeLLM, LLMGateway


@pytest.mark.asyncio
async def test_llm_call_is_recorded_and_aggregated(database_url):
    settings = Settings(
        app_env="ci",
        database_url=database_url,
        _env_file=None,
    )

    engine = make_engine(settings)
    sessionmaker = make_sessionmaker(engine)
    recorder = make_recorder(sessionmaker)

    provider = FakeLLM(
        "fake",
        "fake-model",
        ["Integration test answer"],
    )
    client = LLMGateway(
        [provider],
        recorder=recorder,
        usd_inr=settings.usd_inr,
    )

    try:
        result = await client.generate(
            [{"role": "user", "content": "Hello"}],
            purpose="integration-test",
            prompt_version="test-v1",
        )

        assert result.text == "Integration test answer"

        async with sessionmaker() as session:
            repository = UsageRepository(session)
            rows = await repository.by_day(days=1)

        assert rows
        assert rows[0]["calls"] >= 1
        assert rows[0]["tokens_in"] >= 1
        assert rows[0]["tokens_out"] >= 1

    finally:
        await engine.dispose()
