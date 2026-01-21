from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateCptRequest(BaseModel):
    topic: str
    model: str = Field(default="gpt-4.1-mini")


class ResearchSectionRunRequest(BaseModel):
    cpt: str
    context: Optional[str] = ""
    model: str = Field(default="gpt-4.1-mini")
    use_cache: bool = True


class RunAllRequest(BaseModel):
    cpt: str
    context: Optional[str] = ""
    model: str = Field(default="gpt-4.1-mini")
    sections_to_run: Optional[List[int]] = None
    use_cache: bool = True


class ChatRequest(BaseModel):
    session_id: str
    cpt: str
    section_id: str
    question: str
    model: str = Field(default="gpt-5")


class SessionCreateRequest(BaseModel):
    session_id: str
    topic: str
    cpt: str
    model: str
    analysis_result: str


class SessionUpdateRequest(BaseModel):
    topic: str


class NotesRequest(BaseModel):
    session_id: str
    cpt: str
    notes: str


class AccuracyFeedbackRequest(BaseModel):
    session_id: str
    cpt: str
    section_id: str
    rating: str
    reason: Optional[str] = None


class NcciRetrieveRequest(BaseModel):
    cpt: int
    top_k: int = 15
