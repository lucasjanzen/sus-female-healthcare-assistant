from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exception_handlers import validation_exception_handler
from app.db.session import Base, engine
from app.models import audit_acessos, consulta, paciente, user  # noqa: F401
from app.routers import admin_paciente as admin_paciente_router
from app.routers import analise as analise_router
from app.routers import auth
from app.routers import consulta as consulta_router
from app.routers import fila as fila_router
from app.routers import paciente as paciente_router
from app.routers import speech as speech_router

Base.metadata.create_all(bind=engine)

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
    return {"status": "ok"}
