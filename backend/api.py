"""
FastAPI entrypoint exposing the core APC research services that were previously
wired through Streamlit. Run with:
    uvicorn api:app --reload
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Optional
from io import BytesIO

from fastapi import Body, FastAPI, HTTPException, Query, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.concurrency import run_in_threadpool

from api_schemas import (
    ApcChatRequest,
    GenerateCptRequest,
    ResearchSectionRunRequest,
    RunAllRequest,
    CptCodeResult,
    ResearchRunResult,
    ChatRequest
)
from llm_wrapper import query_llm, stream_llm
from services import apc_orchestrator
from services.cpt_service import get_cpt_codes_for_topic
from services.utils import (
    get_chat_history,
    get_research_session,
    save_chat_message,
)
from services.common import get_or_generate_cpt_description
from services.final_assessment_service import create_excel_output, create_pdf_output

app = FastAPI(title="CCV Research API", version="0.1.0")

# ---------- Helpers ----------
CACHE_DIR = Path("output/services_findings")


def _section1_cache_path(cpt: str) -> Path:
    return CACHE_DIR / cpt / "section_1_results.json"


# ---------- Routes ----------
@app.get("/health")
async def health():
    return {"status": "ok"} 


@app.post("/chat", response_description="Streaming LLM response",
          responses={
              200: {"content": {"text/plain": {}}}
          })
async def chat(req: ChatRequest):
    messages = req.messages
    try:
        stream = stream_llm(messages, req.model)
        return StreamingResponse(stream, media_type="text/plain")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=str(exc)) from exc


@app.post("/cpt/generate", response_model=list[CptCodeResult])
async def generate_cpt(req: GenerateCptRequest):
    return await run_in_threadpool(get_cpt_codes_for_topic, req.topic, req.model)




@app.post("/research/sections/{section_id}/run")
async def run_section(section_id: int, req: ResearchSectionRunRequest):
    try:
        result = await run_in_threadpool(
            apc_orchestrator.conduct_section_research,
            section_id,
            req.cpt,
            req.context or "",
            req.model,
            req.use_cache,
        )
        return {"section_id": section_id, "result": result}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=str(exc)) from exc


@app.post("/research/run-all", response_model=ResearchRunResult)
async def run_all(req: RunAllRequest):
    result = await run_in_threadpool(
        apc_orchestrator.conduct_all_sections_research,
        req.cpt,
        req.context or "",
        req.model,
        req.sections_to_run,
        req.use_cache,
    )
    return result




@app.post("/research/sections/chat")
async def chat_section(req: ApcChatRequest):
    messages = req.messages
    try:
        ai_response = await run_in_threadpool(query_llm, messages, req.model)
        if not ai_response:
            raise HTTPException(500, detail="LLM did not return a response")
        # await run_in_threadpool(
        #     save_chat_message, req.session_id, req.cpt, section_id, req.question, ai_response
        # )
        return {"answer": ai_response}
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(400, detail=str(exc)) from exc


@app.get("/export/excel")
async def export_excel(session_id: str):
    session = await run_in_threadpool(get_research_session, session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")
    file_bytes = await run_in_threadpool(create_excel_output, session["result"], session["cpt_code"])
    filename = f"apc_research_{session['cpt_code']}.xlsx"
    if isinstance(file_bytes, (bytes, bytearray)):
        content = file_bytes
    elif isinstance(file_bytes, BytesIO):
        content = file_bytes.getvalue()
    elif hasattr(file_bytes, "getbuffer"):
        content = file_bytes.getbuffer().tobytes()
    elif hasattr(file_bytes, "getvalue"):
        content = file_bytes.getvalue()
    else:
        content = bytes(file_bytes)  # type: ignore[arg-type]
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.get("/export/pdf")
async def export_pdf(session_id: str):
    session = await run_in_threadpool(get_research_session, session_id)
    if not session:
        raise HTTPException(404, detail="Session not found")
    file_bytes = await run_in_threadpool(create_pdf_output, session["result"], session["cpt_code"])
    filename = f"apc_research_{session['cpt_code']}.pdf"
    if isinstance(file_bytes, (bytes, bytearray)):
        content = file_bytes
    elif isinstance(file_bytes, BytesIO):
        content = file_bytes.getvalue()
    elif hasattr(file_bytes, "getbuffer"):
        content = file_bytes.getbuffer().tobytes()
    elif hasattr(file_bytes, "getvalue"):
        content = file_bytes.getvalue()
    else:
        content = bytes(file_bytes)  # type: ignore[arg-type]
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )



# @app.get("/cpt/{code}/description")
# async def get_cpt_description(code: str, use_llm_fallback: bool = Query(False)):
#     desc = await run_in_threadpool(
#         get_or_generate_cpt_description,
#         code,
#         "gpt-4.1-mini",
#         use_llm_fallback,
#     )
#     if not desc:
#         raise HTTPException(404, detail="CPT description not found")
#     return desc

# @app.get("/research/sections/1/cached")
# async def get_section1_cache(cpt: str = Query(...)):
#     path = _section1_cache_path(cpt)
#     if not path.exists():
#         raise HTTPException(404, detail="No cache for section 1")
#     with path.open("r", encoding="utf-8") as f:
#         data = json.load(f)
#     return data


# @app.get("/research/sections/{section_id}/chat")
# async def get_chat(section_id: str, session_id: str, cpt: str):
#     return await run_in_threadpool(get_chat_history, session_id, cpt, section_id)


# @app.get("/sessions")
# async def list_sessions():
#     return await run_in_threadpool(get_all_research_sessions)


# @app.post("/sessions")
# async def create_session(req: SessionCreateRequest):
#     await run_in_threadpool(
#         save_research_session,
#         req.session_id,
#         req.topic,
#         req.cpt,
#         req.model,
#         req.analysis_result,
#     )
#     return {"session_id": req.session_id}


# @app.get("/sessions/{session_id}")
# async def get_session(session_id: str):
#     session = await run_in_threadpool(get_research_session, session_id)
#     if not session:
#         raise HTTPException(404, detail="Session not found")
#     return session


# @app.patch("/sessions/{session_id}")
# async def patch_session(session_id: str, req: SessionUpdateRequest):
#     await run_in_threadpool(update_research_topic, session_id, req.topic)
#     return {"session_id": session_id, "topic": req.topic}


# @app.delete("/sessions/{session_id}")
# async def delete_session(session_id: str):
#     await run_in_threadpool(delete_research_session, session_id)
#     return {"deleted": session_id}


# @app.get("/notes")
# async def get_notes_endpoint(session_id: str, cpt: str):
#     return {"notes": await run_in_threadpool(get_notes, session_id, cpt)}


# @app.put("/notes")
# async def put_notes(req: NotesRequest):
#     await run_in_threadpool(save_notes, req.session_id, req.cpt, req.notes)
#     return {"saved": True}


# @app.post("/feedback/accuracy")
# async def post_accuracy_feedback(req: AccuracyFeedbackRequest):
#     await run_in_threadpool(
#         save_accuracy_feedback, req.session_id, req.cpt, req.section_id, req.rating, req.reason
#     )
#     return {"saved": True}


# @app.get("/feedback/accuracy")
# async def get_accuracy(session_id: str, cpt: str, section_id: str):
#     fb = await run_in_threadpool(get_accuracy_feedback, session_id, cpt, section_id)
#     if not fb:
#         raise HTTPException(404, detail="Feedback not found")
#     return fb



