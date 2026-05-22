"""HTTP API layer.

Routers live under `backend.api.routes`. `api_router` is the single
entry-point `backend.main` mounts onto the FastAPI app — adding a new
domain means appending one `include_router` call in
`backend/api/routes/__init__.py`, not touching `main.py`.
"""

from backend.api.routes import api_router

__all__ = ["api_router"]
