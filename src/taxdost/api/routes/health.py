from fastapi import APIRouter, Response

from taxdost.api.deps import SettingsDep, StoreDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: SettingsDep) -> dict[str, str]:
    """Liveness: is the process alive? Instant. Never touches the DB or the LLM."""
    return {"status": "ok", "app": settings.app_name, "env": settings.app_env}


@router.get("/ready")
def ready(store: StoreDep, response: Response) -> dict:
    """Readiness: can this instance serve traffic right now?"""
    checks = {"records_loaded": store.ready}
    ok = all(checks.values())
    if not ok:
        response.status_code = 503
    return {"status": "ready" if ok else "not_ready", "checks": checks}
