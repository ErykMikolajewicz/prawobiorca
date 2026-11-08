import re
from string import punctuation

from pydantic import BaseModel, Field, SecretStr, field_validator


class LoginData(BaseModel):
    username: str
    password: SecretStr = Field(min_length=8, max_length=32)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: SecretStr):
        password_str = value.get_secret_value()
        if not re.search(r"[A-Z]", password_str):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", password_str):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", password_str):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(f"[{re.escape(punctuation)}]", password_str):
            raise ValueError("Password must contain at least one special character.")
        return value
