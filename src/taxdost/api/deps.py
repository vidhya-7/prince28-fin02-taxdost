"""Dependencies: endpoints ask for these instead of building them."""

import asyncio
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from taxdost.config import Settings
from taxdost.db.llm_calls import UsageRepository
from taxdost.db.repository import DocumentRepository
from taxdost.llm.gateway import LLMGateway


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """One session per request, closed automatically afterwards."""
    async with request.app.state.sessionmaker() as session:
        yield session


async def get_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DocumentRepository:
    return DocumentRepository(session)


async def get_usage_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UsageRepository:
    return UsageRepository(session)


def get_gateway(request: Request) -> LLMGateway:
    return request.app.state.gateway


async def check_db(request: Request) -> bool:
    """Can we run SELECT 1 within 2 seconds?"""
    try:
        async with request.app.state.engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=2)
        return True
    except Exception:
        return False


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
RepoDep = Annotated[DocumentRepository, Depends(get_repo)]
UsageDep = Annotated[UsageRepository, Depends(get_usage_repo)]
GatewayDep = Annotated[LLMGateway, Depends(get_gateway)]
DbCheckDep = Annotated[bool, Depends(check_db)]
