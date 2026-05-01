from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.models import user, paciente  # noqa: F401
from app.models import consulta, consulta_clinica, consulta_banco_b  # noqa: F401
from app.models import consulta_encerramento, audit_acessos  # noqa: F401
from app.routers import admin_paciente as admin_paciente_router
from app.routers import auth
from app.routers import consulta as consulta_router
from app.routers import paciente as paciente_router
from app.routers import consulta_clinica as consulta_clinica_router
from app.routers import encerramento as encerramento_router
from app.routers import fila as fila_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="CASF API",
    description="Centro de Assistência à Saúde Feminina",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
app.include_router(paciente_router.router, prefix="/pacientes", tags=["Pacientes"])
app.include_router(admin_paciente_router.router, prefix="/admin/pacientes", tags=["Admin — Pacientes"])
app.include_router(consulta_router.router, prefix="/consulta", tags=["Consulta"])
app.include_router(consulta_clinica_router.router, prefix="/consulta", tags=["Consulta Clínica"])
app.include_router(encerramento_router.router, prefix="/consulta", tags=["Encerramento"])
app.include_router(fila_router.router, prefix="/fila", tags=["Fila de Consultas"])


@app.get("/health", tags=["Status"])
def health_check():
    return {"status": "ok"}
