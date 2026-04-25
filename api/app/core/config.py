from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    secret_key: str = "changeme-secret-key-altere-isso-em-producao"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8
    database_url: str = "postgresql://sfha:sfha@db:5432/sfha_db"
    cors_origin: str = "http://localhost:4200"


settings = Settings()
