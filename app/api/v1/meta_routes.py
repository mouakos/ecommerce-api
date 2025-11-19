"""Meta / utility routes (health, readiness, test email)."""

from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/health", summary="Service health check")
async def health() -> dict[str, str]:
    """Lightweight health endpoint used for container orchestrator checks.

    Returns a simple JSON body allowing external systems (Docker, k8s, load balancers)
    to verify the application process is responsive.
    """
    return {"status": "ok"}

