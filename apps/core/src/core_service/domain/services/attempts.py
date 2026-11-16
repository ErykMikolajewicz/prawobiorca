from hashlib import sha256


def get_login_attempts_key(username: str, ip_address: str) -> str:
    username_hash = sha256(username.encode("utf-8")).hexdigest()
    return f"login:{username_hash}:{ip_address}"


def get_registration_attempts_key(ip_address: str) -> str:
    return f"registration:{ip_address}"
