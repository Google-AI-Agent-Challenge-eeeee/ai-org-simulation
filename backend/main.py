from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.simulation import router as simulation_router
from backend.core.config import get_settings
from backend.core.logger import get_logger, setup_logger

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    setup_logger()
    logger = get_logger("backend.startup")
    logger.info("API starting in '%s' mode (llm_mode=%s)", settings.env, settings.llm_mode)
    yield
    logger.info("API shutting down")


app = FastAPI(
    title="AI Org Simulation API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulation_router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = get_logger("backend.error")
    logger.exception("Unhandled exception at %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error"},
    )


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "env": settings.env.value,
        "llm_mode": settings.llm_mode.value,
    }
