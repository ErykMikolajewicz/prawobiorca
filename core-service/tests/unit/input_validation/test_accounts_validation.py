import pytest


@pytest.mark.parametrize(
    ("password", "error_detail"),
    [
        ("nouppercase1!", "Password must contain at least one uppercase letter."),
        ("NOLOWERCASE1!", "Password must contain at least one lowercase letter."),
        ("NoDigits!!", "Password must contain at least one digit."),
        ("NoSpecial1", "Password must contain at least one special character."),
    ],
)
async def test_create_account_weak_passwords(client, password, error_detail):

    payload = {"username": "example@example.com", "password": password}

    response = await client.post("/api/accounts/register", json=payload)

    assert error_detail in response.text
