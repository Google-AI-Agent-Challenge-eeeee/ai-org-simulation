"""All API routers, aggregated under one ``api_router``.

``backend.main`` mounts this single router. Adding a new domain = one import
+ one ``api_router.include_router`` call below.
"""

from fastapi import APIRouter

api_router = APIRouter()


def _wire_routes() -> None:
    """Lazy import + include to avoid circular imports at module load.

    Called at the bottom of this file. Kept as a function for readability —
    a flat sequence of ``from .x import router`` + ``include_router(router)``.
    """

    from backend.api.routes.calendar import router as calendar_router
    from backend.api.routes.employees import router as employees_router
    from backend.api.routes.github import router as github_router
    from backend.api.routes.jira import router as jira_router
    from backend.api.routes.profile import router as profile_router
    from backend.api.routes.slack import router as slack_router
    from backend.api.simulation import router as simulation_router

    api_router.include_router(employees_router)
    api_router.include_router(profile_router)
    api_router.include_router(github_router)
    api_router.include_router(slack_router)
    api_router.include_router(jira_router)
    api_router.include_router(calendar_router)
    api_router.include_router(simulation_router)


_wire_routes()
