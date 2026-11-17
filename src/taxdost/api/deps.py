"""Dependencies: endpoints ask for these instead of building them."""

from typing import Annotated

from fastapi import Depends, Request

from taxdost.config import Settings
from taxdost.store import RecordStore


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_store(request: Request) -> RecordStore:
    return request.app.state.store


SettingsDep = Annotated[Settings, Depends(get_app_settings)]
StoreDep = Annotated[RecordStore, Depends(get_store)]
