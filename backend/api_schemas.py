from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union
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





class SectionSuccess(BaseModel):
    section_num: int
    status: Literal["success"]
    data: Union[str, str]  # str for section 6 content; structured for section 1

class SectionError(BaseModel):
    section_num: int
    status: Literal["error"]
    error: str

SectionResult = Union[SectionSuccess, SectionError]


# ---------- APC section response models ----------

class ErrorResult(BaseModel):
    success: Literal[False] = False
    content: Optional[Any] = None
    error: str
    section_id: str
    section_title: str


class CPTDescription(BaseModel):
    cpt_code: str
    description: str
    source: str


class CodeDescriptionNeighbor(BaseModel):
    cpt_code: str
    description: str
    source: str


class CodeDescriptionKbRecoding(BaseModel):
    cpt_code: str
    cpt_description: str
    change_type: str
    cpt_change_description: str
    resource: str


class CodeDescriptionNoChange(BaseModel):
    cpt_code: str
    description: str
    description_source: str
    status: str


class CodeDescriptionResult(BaseModel):
    neighbouring_codes: List[CodeDescriptionNeighbor]
    internal_recoding_result: List[CodeDescriptionKbRecoding]
    no_change_results: List[CodeDescriptionNoChange]
    internal_llm_recoding_result: List[Dict[str, Any]] = Field(default_factory=list)
    external_full_llm_result: List[Dict[str, Any]] = Field(default_factory=list)


class GuidelineResult(BaseModel):
    analysis_content: str
    cpt_descriptions: Dict[str, CPTDescription]
    source: str = "llm"


class PaymentTable(BaseModel):
    data: List[Dict[str, Any]]
    data_filtered: List[Dict[str, Any]]
    data_filtered_df: Optional[Any] = None
    exclusions: Dict[str, Any]
    excluded_cpt_codes: List[str]
    record_count: int
    record_count_filtered: int

    class Config:
        arbitrary_types_allowed = True


class TargetPaymentHistory(BaseModel):
    apc: PaymentTable
    asc: PaymentTable
    pnpp: PaymentTable
    source: str
    cpt_codes_analyzed: List[str]
    neighboring_codes: List[str]


class PaymentRateResult(BaseModel):
    analysis_content: str
    target_cpt_payment_history: TargetPaymentHistory
    cpt_descriptions: Dict[str, CPTDescription]
    source: str = "llm"


class DeviceDescription(BaseModel):
    hcpcs_code: str
    description: str
    source: str


class DeviceNoChange(BaseModel):
    hcpcs_code: str
    description: str
    description_source: str
    status: str


class DeviceCodeResult(BaseModel):
    device_codes_with_desc: List[DeviceDescription]
    internal_recoding_result: List[Dict[str, Any]]
    no_change_results: List[DeviceNoChange]
    internal_llm_recoding_result: List[Dict[str, Any]] = Field(default_factory=list)
    external_full_llm_result: List[Dict[str, Any]] = Field(default_factory=list)


class PtpTable(BaseModel):
    data: List[Dict[str, Any]]
    record_count: int


class PtpTablesForCpt(BaseModel):
    modifier_0: Optional[PtpTable] = None
    modifier_1: Optional[PtpTable] = None
    has_data: bool
    source: str


class NcciResult(BaseModel):
    analysis_content: str
    ptp_tables_by_cpt: Dict[str, PtpTablesForCpt]
    ncci_manual_by_cpt: Dict[str, Dict[str, Any]]
    ncci_chunk_details_by_cpt: Dict[str, Dict[str, Any]]
    neighboring_codes: List[str]
    cpt_descriptions: Dict[str, CPTDescription]
    source: str = "internal_kb"


class ReferenceMaterialResult(BaseModel):
    analysis_content: str
    cpt_descriptions: Dict[str, CPTDescription]
    source: str = "llm"


class PaymentHistoryEntry(BaseModel):
    data: List[Dict[str, Any]] = Field(default_factory=list)
    has_data: bool = False


class FinalAssessment(BaseModel):
    target_cpt: str
    cpt_descriptions: Dict[str, Dict[str, Any]]
    ncci_results: Dict[str, Dict[str, Any]]
    device_codes: List[DeviceDescription]
    payment_history: Dict[str, PaymentHistoryEntry]
    update_time: str
    source: str = "internal_kb"


SectionResponse = Union[
    CodeDescriptionResult,
    GuidelineResult,
    PaymentRateResult,
    DeviceCodeResult,
    NcciResult,
    ReferenceMaterialResult,
    FinalAssessment,
    ErrorResult,
]

