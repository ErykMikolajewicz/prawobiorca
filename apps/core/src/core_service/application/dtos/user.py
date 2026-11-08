from dataclasses import dataclass


@dataclass(frozen=True)
class CreateUserData:
    username: str
    hashed_password: bytes
