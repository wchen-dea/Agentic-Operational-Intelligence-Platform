"""Module for models."""

from typing import Literal

from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    store_id: str | None = None
    region: str | None = None
    persona: Literal["store_manager", "executive"] = "store_manager"
    session_id: str | None = None


class KPIRequest(BaseModel):
    store_id: str | None = None
    region: str | None = None


class OperationalBriefRequest(BaseModel):
    store_id: str | None = None
    region: str | None = None
    persona: Literal["store_manager", "executive"] = "store_manager"
