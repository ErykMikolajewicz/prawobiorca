import pytest
from fastapi import status


@pytest.mark.parametrize(
    ("password", "error_detail"),
    [
        ("nouppercase1!", "Password must contain at least one uppercase letter."),
        ("NOLOWERCASE1!", "Password must contain at least one lowercase letter."),
        ("NoDigits!!", "Password must contain at least one digit."),
        ("NoSpecial1", "Password must contain at least one special character."),
        ("Aa1!" + "😀" * 17 + "a", "Password must not exceed 72 UTF-8 bytes."),
    ],
)
async def test_create_account_weak_passwords(client, password, error_detail):

    payload = {"username": "example@example.com", "password": password}

    response = await client.post("/api/accounts/register", json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert error_detail in response.text
