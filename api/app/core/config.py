from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"

_DEFAULT_SECRET_KEY = "changeme-secret-key-altere-isso-em-producao"
_DEFAULT_SECRET_SALT = "changeme-salt-altere-isso-em-producao"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), env_file_encoding="utf-8-sig")

    secret_key: str = _DEFAULT_SECRET_KEY
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8
    database_url: str = "postgresql://sfha:sfha@localhost:5432/sfha_db"
    cors_origin: str = "http://localhost:4200"
    secret_salt: str = _DEFAULT_SECRET_SALT

    # Azure AI Speech (Speech-to-Text)
    azure_speech_key: str = ""
    azure_speech_region: str = ""  # ex: brazilsouth, eastus

    # Azure AI Language (Text Analytics — sentimento)
    azure_language_endpoint: str = ""  # ex: https://<resource>.cognitiveservices.azure.com/
    azure_language_key: str = ""

    # Azure OpenAI (GPT-4o — análise LLM)
    azure_openai_endpoint: str = ""  # ex: https://seu-recurso.openai.azure.com/
    azure_openai_api_key: str = ""
    azure_openai_deployment_name: str = "gpt-4o"
    azure_openai_api_version: str = "2024-02-01"

    @model_validator(mode="after")
    def validar_segredos(self) -> "Settings":
        if self.secret_key == _DEFAULT_SECRET_KEY:
            raise ValueError(
                "SECRET_KEY não configurada. Defina SECRET_KEY em api/.env antes de iniciar."
            )
        if self.secret_salt == _DEFAULT_SECRET_SALT:
            raise ValueError(
                "SECRET_SALT não configurada. Defina SECRET_SALT em api/.env antes de iniciar."
            )
        return self


settings = Settings()
