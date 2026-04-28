from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import Engine, text

from app.core.config import settings
from app.db.session import Base, engine
from app.db.session_b import BaseB, engine_b
from app.models import consulta, paciente, user  # noqa: F401
from app.models import consulta_clinica, consulta_banco_b  # noqa: F401
from app.models import consulta_encerramento  # noqa: F401
from app.routers import admin_paciente as admin_paciente_router
from app.routers import auth, consulta as consulta_router
from app.routers import paciente as paciente_router
from app.routers import consulta_clinica as consulta_clinica_router
from app.routers import encerramento as encerramento_router
from app.routers import fila as fila_router

_MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"


def _run_migrations(eng: Engine) -> None:
    with eng.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename   VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMPTZ  DEFAULT now()
            )
        """))
        conn.commit()

        if not _MIGRATIONS_DIR.exists():
            return

        for sql_file in sorted(_MIGRATIONS_DIR.glob("*.sql")):
            row = conn.execute(
                text("SELECT 1 FROM schema_migrations WHERE filename = :f"),
                {"f": sql_file.name},
            ).fetchone()
            if row:
                continue
            conn.execute(text(sql_file.read_text(encoding="utf-8")))
            conn.execute(
                text("INSERT INTO schema_migrations (filename) VALUES (:f)"),
                {"f": sql_file.name},
            )
            conn.commit()


Base.metadata.create_all(bind=engine)
BaseB.metadata.create_all(bind=engine_b)
_run_migrations(engine)
_run_migrations(engine_b)

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
