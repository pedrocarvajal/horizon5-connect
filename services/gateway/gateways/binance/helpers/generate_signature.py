# Code reviewed on 2025-11-19 by pedrocarvajal

import hashlib
import hmac


def generate_signature(
    query_string: str,
    api_secret: str,
) -> str:
    """
    Generate HMAC-SHA256 signature for Binance API authentication.

    Creates a hexadecimal signature by hashing the query string with the API secret
    using HMAC-SHA256 algorithm. This signature is required for authenticated
    Binance API requests.

    Args:
        query_string: URL-encoded query string (e.g., "symbol=BTCUSDT&timestamp=1234567890")
        api_secret: Binance API secret key used for signing

    Returns:
        Hexadecimal signature string (64 characters)

    Raises:
        ValueError: If query_string or api_secret is empty

    Examples:
        >>> generate_signature("symbol=BTCUSDT&timestamp=1234567890", "secret_key")
        "a1b2c3d4e5f6..."
    """
    if not query_string:
        raise ValueError("Query string cannot be empty")

    if not api_secret:
        raise ValueError("API secret cannot be empty")

    return hmac.new(
        api_secret.encode("utf-8"),
        query_string.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
