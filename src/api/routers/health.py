"""src/api/routers/health.py — Health Check Endpoint (required by SumoPod)"""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint — diperlukan oleh SumoPod untuk monitoring container.
    Juga digunakan oleh Docker HEALTHCHECK directive.
    """
    return HealthResponse(
        status="ok",
        service="OmniResolve-AI",
        version="0.1.0",
    )
