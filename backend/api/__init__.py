from fastapi import APIRouter

from backend.api.simulation import router as simulation_router

api_router = APIRouter()
api_router.include_router(simulation_router)
