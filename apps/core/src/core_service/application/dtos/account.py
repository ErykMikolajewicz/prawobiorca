import re
from string import punctuation

from pydantic import BaseModel, Field, SecretStr, field_validator

from core_service.domain.consts import MAX_PASSWORD_BYTES


class LoginData(BaseModel):
    username: str
    password: SecretStr


class RegistrationData(LoginData):
    password: SecretStr = Field(min_length=8, max_length=32)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr):
        password_str = value.get_secret_value()
        if len(password_str.encode("utf-8")) > MAX_PASSWORD_BYTES:
            raise ValueError(f"Password must not exceed {MAX_PASSWORD_BYTES} UTF-8 bytes.")
        if not re.search(r"[A-Z]", password_str):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password_str):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password_str):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(f"[{re.escape(punctuation)}]", password_str):
            raise ValueError("Password must contain at least one special character.")
        return value
