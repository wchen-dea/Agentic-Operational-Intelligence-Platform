from __future__ import annotations
from typing import Optional, Literal
from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    store_id: Optional[str] = None
    region: Optional[str] = None
    persona: Literal["store_manager", "executive"] = "store_manager"


class KPIRequest(BaseModel):
    store_id: Optional[str] = None
    region: Optional[str] = None


class OperationalBriefRequest(BaseModel):
    store_id: Optional[str] = None
    region: Optional[str] = None
    persona: Literal["store_manager", "executive"] = "store_manager"
