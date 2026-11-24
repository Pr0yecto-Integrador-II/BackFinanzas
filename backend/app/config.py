from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://finanzas:finanzas@localhost:5433/finanzas"
    redis_url: str = "redis://localhost:6380/0"
    jwt_secret: str = Field(min_length=32)  # HS256 pide una clave de al menos 256 bits
    access_token_minutes: int = 15
    refresh_token_days: int = 30
    cookie_secure: bool = True
    frontend_url: str = "http://localhost:4200"
    # Azure AI Speech (MVP 2, HU16). Opcionales: sin ellas el endpoint de voz responde 503.
    azure_speech_key: SecretStr | None = None
    azure_speech_region: str | None = None
    azure_speech_token_timeout_seconds: float = 5.0
    # Azure AI Vision (MVP 3, HU20). Opcionales: sin ellas el análisis de imágenes responde 503.
    azure_vision_key: SecretStr | None = None
    azure_vision_endpoint: str | None = None
    azure_vision_timeout_seconds: float = 10.0
    # `caption` solo existe en algunas regiones de Azure (en otras el servicio responde 400).
    azure_vision_features: str = "read,tags"
    vision_max_image_bytes: int = 4 * 1024 * 1024
    vision_requests_per_hour: int = 30


@lru_cache
def get_settings() -> Settings:
    return Settings()
