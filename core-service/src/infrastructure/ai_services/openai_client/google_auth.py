import asyncio

import google.auth
from google.auth.credentials import Credentials
from google.auth.transport.requests import Request

_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

_credentials: Credentials | None = None


async def get_access_token() -> str:
    global _credentials
    if _credentials is None:
        _credentials, _ = await asyncio.to_thread(google.auth.default, scopes=_SCOPES)

    if not _credentials.valid:
        await asyncio.to_thread(_credentials.refresh, Request())

    return _credentials.token
