from __future__ import annotations

import asyncio
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from backend.core.config import get_settings
from backend.orchestration import session_flow
from backend.services import prd_file_parser

router = APIRouter(prefix="/api/sessions", tags=["simulation"])


@router.post("")
async def create_session(body: dict | None = None) -> dict[str, str]:
    return session_flow.create_session(body)


@router.post("/from-file")
async def create_session_from_file(body: dict | None = None) -> dict[str, object]:
    payload = body or {}
    try:
        parsed_file = prd_file_parser.parse_prd_file_upload(payload)
    except prd_file_parser.PrdFileParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    session_payload = {
        **payload,
        "prd": parsed_file.text,
    }
    session = session_flow.create_session(session_payload)
    return {
        **session,
        "file_name": parsed_file.file_name,
        "page_count": parsed_file.page_count,
        "extracted_chars": len(parsed_file.text),
    }


@router.get("/{session_id}/requirements")
async def get_requirements(session_id: str) -> dict:
    return session_flow.get_requirements_summary(session_id)


@router.post("/{session_id}/requirements/accept")
async def accept_requirements(session_id: str, body: dict | None = None) -> dict[str, bool]:
    return session_flow.accept_requirements(session_id)


@router.post("/{session_id}/requirements/revise")
async def revise_requirements(session_id: str, body: dict | None = None) -> dict:
    return session_flow.revise_requirements(session_id)


@router.get("/{session_id}/teams")
async def get_teams(session_id: str) -> dict:
    return session_flow.get_team_candidates(session_id)


@router.post("/{session_id}/teams/select")
async def select_team(session_id: str, body: dict | None = None) -> dict[str, bool]:
    team_id = body.get("teamId") if body else None
    return session_flow.select_team(session_id, team_id)


@router.get("/{session_id}/report")
async def get_report(session_id: str) -> dict:
    try:
        return session_flow.get_report(session_id)
    except session_flow.ReportNotReadyError as exc:
        detail: dict[str, str] = {
            "code": "REPORT_NOT_READY",
            "message": "Report is not ready. Run the simulation stream first.",
            "sessionId": exc.session_id,
        }
        if exc.generation_error:
            detail["generationError"] = exc.generation_error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        ) from exc


@router.get("/{session_id}/stream")
async def simulation_stream(session_id: str, mode: str | None = None) -> StreamingResponse:
    settings = get_settings()
    llm_mode = _resolve_simulation_llm_mode(mode, settings)

    async def event_generator():
        loop = asyncio.get_event_loop()
        chunks = session_flow.iter_pipeline_sse(session_id, llm_mode)
        stop = object()

        def next_or_stop(iterator: Iterator[str]) -> str | object:
            try:
                return next(iterator)
            except StopIteration:
                return stop

        while True:
            chunk = await loop.run_in_executor(None, next_or_stop, chunks)
            if chunk is stop:
                break
            yield chunk
            if isinstance(chunk, str) and chunk.startswith("event: message"):
                await asyncio.sleep(0.004)
            else:
                await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


def _resolve_simulation_llm_mode(mode: str | None, settings) -> str:
    if mode in ("stub", "vertex"):
        return mode

    configured = settings.simulation_llm_mode or settings.llm_mode
    if configured.value == "vertex":
        return "vertex"
    return "stub"
