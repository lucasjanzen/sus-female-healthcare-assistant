import celery_app  # noqa: F401 — inicializa o app Celery com broker Redis antes dos shared_tasks

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import validation_exception_handler
from app.models import audit_acessos, consulta, paciente, user  # noqa: F401
from app.routers import admin_paciente as admin_paciente_router
from app.routers import analise as analise_router
from app.routers import auth
from app.routers import consulta as consulta_router
from app.routers import fila as fila_router
from app.routers import paciente as paciente_router
from app.routers import speech as speech_router

app = FastAPI(
    title="CASF API",
    description="Centro de Assistencia a Saude Feminina",
    version="1.0.0",
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticacao"])
app.include_router(paciente_router.router, prefix="/pacientes", tags=["Pacientes"])
app.include_router(
    admin_paciente_router.router, prefix="/admin/pacientes", tags=["Admin - Pacientes"]
)
app.include_router(consulta_router.router, prefix="/consulta", tags=["Consulta"])
app.include_router(fila_router.router, prefix="/fila", tags=["Fila"])
app.include_router(analise_router.router, prefix="/analises", tags=["Analises"])
app.include_router(speech_router.router, prefix="/speech", tags=["Speech"])


@app.get("/health", tags=["Status"])
def health_check():
    from sqlalchemy import text
    from app.db.session import SessionLocal
    checks: dict[str, str] = {}

    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {exc}"

    try:
        import celery_app as _celery_module
        ping = _celery_module.celery_app.control.ping(timeout=1)
        checks["celery"] = "ok" if ping else "no workers"
    except Exception as exc:
        checks["celery"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    from fastapi import Response
    status_code = 200 if all_ok else 503
    return Response(
        content=__import__("json").dumps({"status": "ok" if all_ok else "degraded", **checks}),
        media_type="application/json",
        status_code=status_code,
    )
