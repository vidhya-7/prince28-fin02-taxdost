"""POST /v1/chat (streaming) and GET /v1/usage."""

import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from taxdost.api.deps import GatewayDep, UsageDep
from taxdost.llm.gateway import LLMResult, LLMUnavailable

router = APIRouter(tags=["chat"])

PROMPT_VERSION = "chat_system_v1"


def load_prompt(directory: Path, name: str = PROMPT_VERSION) -> str:
    """Read a prompt file. A missing file stops the app at start-up."""
    return (directory / f"{name}.md").read_text(encoding="utf-8").strip()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    stream: bool = True


def sse(data: dict, event: str = "") -> str:
    """Format one server-sent event."""
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(data, ensure_ascii=False)}\n\n"


def summary(result: LLMResult) -> dict:
    return {key: value for key, value in asdict(result).items() if key != "text"}


@router.post("/chat")
async def chat(body: ChatRequest, request: Request, gateway: GatewayDep):
    messages = [
        {"role": "system", "content": request.app.state.system_prompt},
        {"role": "user", "content": body.message},
    ]

    try:
        if not body.stream:
            result = await gateway.generate(
                messages,
                prompt_version=PROMPT_VERSION,
            )
            return {"answer": result.text, **summary(result)}

        stream = gateway.stream(messages, prompt_version=PROMPT_VERSION)
        first = await anext(stream)

    except LLMUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=f"No model could answer: {exc}",
        ) from exc

    async def events() -> AsyncIterator[str]:
        item = first
        try:
            while True:
                if isinstance(item, LLMResult):
                    yield sse(summary(item), event="done")
                    return

                yield sse({"delta": item})
                item = await anext(stream)

        except LLMUnavailable as exc:
            yield sse({"detail": str(exc)}, event="error")

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    }

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers=headers,
    )


@router.get("/usage")
async def usage(
    repo: UsageDep,
    days: Annotated[int, Query(ge=1, le=90)] = 7,
) -> dict:
    """Tokens and rupees per day, from the llm_calls table."""
    rows = await repo.by_day(days)
    total = round(sum(row["cost_inr"] for row in rows), 4)

    return {
        "days": rows,
        "total_cost_inr": total,
        "calls": sum(row["calls"] for row in rows),
    }
