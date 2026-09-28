from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session

router = APIRouter(tags=["Health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Liveness probe to confirm backend process is running."""
    return {"status": "ok", "service": "smart-health-backend"}


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check(session: AsyncSession = Depends(get_db_session)):
    """Readiness probe verifying live PostgreSQL database connectivity."""
    try:
        await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "error", "detail": str(e)}
