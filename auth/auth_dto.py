from typing import Optional
from pydantic import BaseModel, field_validator


class RegisterDto(BaseModel):
    name: str
    email: str
    password: str
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def pw_len(cls, v):
        if len(v) < 6:
            raise ValueError("Min 6 characters")
        return v


class LoginDto(BaseModel):
    email: str
    password: str


class RefreshDto(BaseModel):
    refresh_token: str
