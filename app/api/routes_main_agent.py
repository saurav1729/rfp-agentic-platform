from fastapi import APIRouter, Depends
from app.controllers.health_controller import health_check

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check_endpoint():
    return await health_check()
