from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file so the path is always absolute,
# regardless of which directory uvicorn/multiprocessing sets as CWD.
_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8-sig")

    secret_key: str = "changeme-secret-key-altere-isso-em-producao"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8
    database_url: str = "postgresql://sfha:sfha@localhost:5432/sfha_db"
    cors_origin: str = "http://localhost:4200"
    secret_salt: str = "changeme-salt-altere-isso-em-producao"


settings = Settings()
