from __future__ import annotations

import asyncio
from collections.abc import Iterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.core.config import get_settings
from backend.orchestration import session_flow

router = APIRouter(prefix="/api/sessions", tags=["simulation"])


@router.post("")
async def create_session(body: dict | None = None) -> dict[str, str]:
    return session_flow.create_session()


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
    return session_flow.get_report(session_id)


@router.get("/{session_id}/stream")
async def simulation_stream(session_id: str, mode: str | None = None) -> StreamingResponse:
    settings = get_settings()
    llm_mode = mode if mode in ("stub", "vertex") else settings.llm_mode.value

    async def event_generator():
        loop = asyncio.get_event_loop()
        chunks = session_flow.iter_pipeline_sse(llm_mode)
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
                await asyncio.sleep(0.028)
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
