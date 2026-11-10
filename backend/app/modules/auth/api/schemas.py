import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")

    @field_validator("*", mode="after")
    @classmethod
    def _no_nul(cls, value: Any) -> Any:
        # PostgreSQL no admite NUL en texto: sin esto, una consulta por correo daría error 500.
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("No se admite el carácter nulo.")
        return value


class RegisterIn(_In):
    email: str = Field(max_length=300)
    password: str = Field(max_length=1000)
    password_confirmation: str = Field(max_length=1000)
    currency: str = Field(default="COP", max_length=3)


class LoginIn(_In):
    email: str = Field(max_length=300)
    password: str = Field(max_length=1000)


class ForgotPasswordIn(_In):
    email: str = Field(max_length=300)


class ResetPasswordIn(_In):
    token: str = Field(max_length=200)
    password: str = Field(max_length=1000)
    password_confirmation: str = Field(max_length=1000)


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    currency: str


class SessionOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class MessageOut(BaseModel):
    message: str
