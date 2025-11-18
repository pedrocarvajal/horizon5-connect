import hashlib
import hmac


def generate_signature(
    query_string: str,
    api_secret: str,
) -> str:
    if not query_string:
        raise ValueError("Query string cannot be empty")

    if not api_secret:
        raise ValueError("API secret cannot be empty")

    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
