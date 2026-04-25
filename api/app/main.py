from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.session import Base, engine
from app.models import user  # noqa: F401 — registra modelos antes de create_all
from app.routers import auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PrenaIA API",
    description="Sistema de Assistência à Saúde Feminina",
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


@app.get("/health", tags=["Status"])
def health_check():
    return {"status": "ok"}
