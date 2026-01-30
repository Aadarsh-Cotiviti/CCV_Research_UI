from __future__ import annotations

from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


class GenerateCptRequest(BaseModel):
    topic: str
    model: str = Field(default="gpt-4.1-mini")


class CptCodeResult(BaseModel):
    code: str = Field(..., examples=["31628"])
    description: str = Field(
        ...,
        examples=[ "Bronchoscopy, rigid or flexible, including fluoroscopic guidance, when performed; "
            "with transbronchial lung biopsy(s), single lobe"],
    )
    source: str = Field(..., examples=["internal_kb"])


class ResearchSectionRunRequest(BaseModel):
    cpt: str
    context: Optional[str] = ""
    model: str = Field(default="gpt-4.1-mini")
    use_cache: bool = True


class RunAllRequest(BaseModel):
    cpt: str
    context: Optional[str] = ""
    model: str = Field(default="gpt-4.1-mini")
    use_cache: bool = True


class ChatMessage(BaseModel):
    role: Literal["assistant", "user", "system"]
    content: str


class ChatRequest(BaseModel):
    model: str = Field(default="gpt-5")
    messages: List[ChatMessage] = Field(default_factory=list)

class ApcChatRequest(BaseModel):
    session_id: str
    cpt: str
    section_id: str
    question: str
    model: str = Field(default="gpt-5")
    messages: List[ChatMessage] = Field(default_factory=list)


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

class NeighbouringCode(BaseModel):
    cpt_code: str
    description: str
    source: str

class LlmRecoding(BaseModel):
    recoding_possibilities: str
    source: str

class InternalLlmRecodingResult(BaseModel):
    cpt_code: str
    description: str
    description_source: str
    llm_recoding: LlmRecoding

class Section1Data(BaseModel):
    neighbouring_codes: List[NeighbouringCode]
    internal_recoding_result: List[dict]  # empty list in sample; tighten if you have a schema
    internal_llm_recoding_result: List[InternalLlmRecodingResult]
    external_full_llm_result: List[dict]  # empty list in sample; tighten if you have a schema

class SectionSuccess(BaseModel):
    section_num: int
    status: Literal["success"]
    data: Union[Section1Data, str]  # str for section 6 content; structured for section 1

class SectionError(BaseModel):
    section_num: int
    status: Literal["error"]
    error: str

SectionResult = Union[SectionSuccess, SectionError]

class ResearchRunResult(BaseModel):
    target_cpt: str
    context_details: str
    model: str
    sections: Dict[str, SectionResult]