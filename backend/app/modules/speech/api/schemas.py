from pydantic import BaseModel, ConfigDict, Field


class SpeechTokenIn(BaseModel):
    """Cuerpo opcional y vacío: cualquier campo (voz, idioma, clave…) se rechaza con 422."""

    model_config = ConfigDict(extra="forbid")


class SpeechTokenOut(BaseModel):
    token: str = Field(description="Token temporal para SpeechConfig.fromAuthorizationToken.")
    region: str = Field(description="Región de Azure AI Speech, p. ej. 'eastus'.")
    expires_in_seconds: int = Field(description="Vigencia del token en segundos (máximo 600).")


class ErrorOut(BaseModel):
    code: str
    message: str
