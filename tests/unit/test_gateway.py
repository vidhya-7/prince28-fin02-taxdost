import json

import httpx
import pytest

from taxdost.llm.gateway import (
    PRICES_USD,
    CircuitBreaker,
    FakeLLM,
    LLMError,
    LLMGateway,
    LLMUnavailable,
    OpenAICompatProvider,
    Reply,
    cost_inr,
    estimate_tokens,
)


def err(message="provider failed", retryable=True, retry_after=None):
    return LLMError(message, retryable=retryable, retry_after=retry_after)


def gateway(*providers, **kwargs):
    async def no_wait(_seconds):
        return None

    return LLMGateway(
        list(providers),
        sleep=no_wait,
        **kwargs,
    )


MESSAGES = [{"role": "user", "content": "Hello"}]


@pytest.mark.asyncio
async def test_generate_returns_answer_tokens_and_cost():
    provider = FakeLLM("gemini", "gemini-3.5-flash-lite", ["Hello there"])
    result = await gateway(provider).generate(MESSAGES)

    assert result.text == "Hello there"
    assert result.provider == "gemini"
    assert result.tokens_in == 12
    assert result.tokens_out == 2
    assert result.cost_inr > 0
    assert result.fallback_used is False


@pytest.mark.asyncio
async def test_retryable_error_is_retried():
    provider = FakeLLM(
        "gemini",
        "gemini-3.5-flash-lite",
        [
            err("rate limited", retry_after=1),
            "Recovered",
        ],
    )
    result = await gateway(provider).generate(MESSAGES)

    assert result.text == "Recovered"
    assert provider.calls == 2
    assert result.attempts == 2


@pytest.mark.asyncio
async def test_fallback_after_primary_failures():
    primary = FakeLLM("gemini", "gemini-3.5-flash-lite", [err(), err()])
    fallback = FakeLLM("groq", "openai/gpt-oss-20b", ["Fallback answer"])

    result = await gateway(primary, fallback).generate(MESSAGES)

    assert result.text == "Fallback answer"
    assert result.provider == "groq"
    assert result.fallback_used is True


@pytest.mark.asyncio
async def test_non_retryable_error_is_not_retried():
    provider = FakeLLM("gemini", script=[err("bad API key", retryable=False), "unused"])
    fallback = FakeLLM("groq", script=["Backup"])

    result = await gateway(provider, fallback).generate(MESSAGES)

    assert provider.calls == 1
    assert result.text == "Backup"


@pytest.mark.asyncio
async def test_all_providers_down_raises_unavailable():
    primary = FakeLLM("gemini", script=[err(), err()])
    fallback = FakeLLM("groq", script=[err(), err()])

    with pytest.raises(LLMUnavailable):
        await gateway(primary, fallback).generate(MESSAGES)


@pytest.mark.asyncio
async def test_no_providers_configured():
    with pytest.raises(LLMUnavailable, match="no LLM provider"):
        await gateway().generate(MESSAGES)


@pytest.mark.asyncio
async def test_repeated_failures_open_circuit():
    provider = FakeLLM("gemini", script=[err(), err(), err(), err(), err(), err()])
    client = gateway(provider)

    for _ in range(3):
        with pytest.raises(LLMUnavailable):
            await client.generate(MESSAGES)

    assert client.breakers["gemini"].state == "open"


@pytest.mark.asyncio
async def test_open_circuit_skips_provider():
    provider = FakeLLM("gemini", script=["Should not be used"])
    client = gateway(provider)
    client.breakers["gemini"]._opened_at = client._clock()

    with pytest.raises(LLMUnavailable, match="circuit open"):
        await client.generate(MESSAGES)

    assert provider.calls == 0


@pytest.mark.asyncio
async def test_half_open_circuit_recovers():
    now = [0.0]
    breaker = CircuitBreaker(threshold=1, cooldown=10, clock=lambda: now[0])

    breaker.failure()
    assert breaker.state == "open"
    now[0] = 11.0

    assert breaker.state == "half-open"
    assert breaker.allow()
    breaker.success()
    assert breaker.state == "closed"


def test_circuit_breaker_state_transitions():
    now = [0.0]
    breaker = CircuitBreaker(threshold=2, cooldown=5, clock=lambda: now[0])

    assert breaker.state == "closed"
    breaker.failure()
    assert breaker.state == "closed"
    breaker.failure()
    assert breaker.state == "open"
    assert breaker.allow() is False

    now[0] = 6.0
    assert breaker.state == "half-open"
    breaker.success()
    assert breaker.state == "closed"


@pytest.mark.asyncio
async def test_stream_yields_pieces_and_final_result():
    provider = FakeLLM("gemini", script=["Hello from stream"])
    output = [item async for item in gateway(provider).stream(MESSAGES)]

    assert output[:-1] == ["Hello ", "from ", "stream "]
    assert isinstance(output[-1], type(await gateway(FakeLLM()).generate(MESSAGES)))


@pytest.mark.asyncio
async def test_stream_falls_back_before_any_piece():
    primary = FakeLLM("gemini", script=[err("unavailable")])
    fallback = FakeLLM("groq", script=["Backup response"])

    output = [item async for item in gateway(primary, fallback).stream(MESSAGES)]

    assert "".join(item for item in output if isinstance(item, str)) == "Backup response "
    assert output[-1].fallback_used is True


@pytest.mark.asyncio
async def test_stream_does_not_switch_after_partial_answer():
    primary = FakeLLM("gemini", script=[("partial", err("connection lost"))])
    fallback = FakeLLM("groq", script=["Must not appear"])

    stream = gateway(primary, fallback).stream(MESSAGES)
    pieces = []

    with pytest.raises(LLMUnavailable, match="mid-answer"):
        async for item in stream:
            if isinstance(item, str):
                pieces.append(item)

    assert pieces
    assert fallback.calls == 0


@pytest.mark.asyncio
async def test_recorder_failure_does_not_break_answer():
    async def broken_recorder(_row):
        raise RuntimeError("database unavailable")

    provider = FakeLLM("gemini", script=["Still works"])
    result = await gateway(provider, recorder=broken_recorder).generate(MESSAGES)

    assert result.text == "Still works"


def test_cost_table_and_unknown_model():
    assert "gemini-3.8-flash" in PRICES_USD
    assert "gemini-3.5-flash-lite" in PRICES_USD
    assert cost_inr("unknown-model", 100, 100, 95) == 0


def test_missing_token_estimate():
    assert estimate_tokens("12345678") == 2
    assert estimate_tokens("") == 1


@pytest.mark.asyncio
async def test_provider_sends_openai_request_and_reads_reply():
    seen = {}

    async def handler(request):
        seen["url"] = str(request.url)
        seen["body"] = json.loads(request.content)
        seen["authorization"] = request.headers["authorization"]
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Provider answer"}}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3},
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1/", "secret", "test-model", client=client
    )

    reply = await provider.generate(MESSAGES)

    assert seen["url"] == "https://llm.test/v1/chat/completions"
    assert seen["authorization"] == "Bearer secret"
    assert seen["body"]["model"] == "test-model"
    assert reply.text == "Provider answer"
    assert reply.tokens_in == 5
    await client.aclose()


@pytest.mark.asyncio
async def test_http_errors_become_llm_errors():
    async def handler(_request):
        return httpx.Response(
            429,
            headers={"retry-after": "2"},
            text="Too many requests",
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1", "secret", "test-model", client=client
    )

    with pytest.raises(LLMError) as caught:
        await provider.generate(MESSAGES)

    assert caught.value.retryable is True
    assert caught.value.retry_after == 2
    await client.aclose()


@pytest.mark.asyncio
async def test_provider_reads_sse_stream():
    events = [
        'data: {"choices":[{"delta":{"content":"Hello "}}]}',
        'data: {"choices":[{"delta":{"content":"world"},"finish_reason":"stop"}]}',
        "data: [DONE]",
        "",
    ]

    async def handler(_request):
        return httpx.Response(
            200,
            content=("\n".join(events)).encode(),
            headers={"content-type": "text/event-stream"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1", "secret", "test-model", client=client
    )
    usage = Reply()
    pieces = [piece async for piece in provider.stream(MESSAGES, usage)]

    assert pieces == ["Hello ", "world"]
    await client.aclose()


@pytest.mark.asyncio
async def test_incomplete_stream_raises_error():
    async def handler(_request):
        return httpx.Response(
            200,
            content=b'data: {"choices":[{"delta":{"content":"Hello"}}]}\n',
            headers={"content-type": "text/event-stream"},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1", "secret", "test-model", client=client
    )

    with pytest.raises(LLMError, match="ended early"):
        async for _ in provider.stream(MESSAGES, Reply()):
            pass

    await client.aclose()


@pytest.mark.asyncio
async def test_timeout_is_not_retryable_but_connection_error_is():
    async def timeout_handler(_request):
        raise httpx.ReadTimeout("timed out")

    client = httpx.AsyncClient(transport=httpx.MockTransport(timeout_handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1", "secret", "test-model", client=client
    )

    with pytest.raises(LLMError) as caught:
        await provider.generate(MESSAGES)

    assert caught.value.retryable is False
    await client.aclose()

    async def connection_handler(_request):
        raise httpx.ConnectError("connection dropped")

    client = httpx.AsyncClient(transport=httpx.MockTransport(connection_handler))
    provider = OpenAICompatProvider(
        "test", "https://llm.test/v1", "secret", "test-model", client=client
    )

    with pytest.raises(LLMError) as caught:
        await provider.generate(MESSAGES)

    assert caught.value.retryable is True
    await client.aclose()
