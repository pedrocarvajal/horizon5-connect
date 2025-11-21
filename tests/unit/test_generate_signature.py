# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest

from services.gateway.gateways.binance.helpers.generate_signature import generate_signature


class TestGenerateSignature(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _VALID_QUERY: str = "symbol=BTCUSDT&timestamp=1234567890"
    _VALID_SECRET: str = "test_secret"
    _EXPECTED_SIGNATURE_LENGTH: int = 64
    _ERROR_MESSAGE_EMPTY_QUERY: str = "Query string cannot be empty"
    _ERROR_MESSAGE_EMPTY_SECRET: str = "API secret cannot be empty"

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_generate_signature_basic(self) -> None:
        """Verify basic signature generation returns correct format."""
        signature = generate_signature(self._VALID_QUERY, self._VALID_SECRET)

        assert isinstance(signature, str)
        assert len(signature) == self._EXPECTED_SIGNATURE_LENGTH

    def test_generate_signature_deterministic(self) -> None:
        """Verify that identical inputs produce identical signatures."""
        signature1 = generate_signature(self._VALID_QUERY, self._VALID_SECRET)
        signature2 = generate_signature(self._VALID_QUERY, self._VALID_SECRET)

        assert signature1 == signature2

    def test_generate_signature_different_secrets(self) -> None:
        """Verify that different secrets produce different signatures."""
        signature1 = generate_signature(self._VALID_QUERY, "secret1")
        signature2 = generate_signature(self._VALID_QUERY, "secret2")

        assert signature1 != signature2

    def test_generate_signature_different_queries(self) -> None:
        """Verify that different query strings produce different signatures."""
        signature1 = generate_signature(self._VALID_QUERY, self._VALID_SECRET)
        signature2 = generate_signature("symbol=ETHUSDT&timestamp=1234567890", self._VALID_SECRET)

        assert signature1 != signature2

    def test_generate_signature_known_value(self) -> None:
        """Regression test with known Binance API signature value."""
        query = (
            "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000"
            "&timestamp=1499827319559"
        )
        secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
        expected = "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71"
        signature = generate_signature(query, secret)

        assert signature == expected

    def test_generate_signature_with_special_chars(self) -> None:
        """Verify signature generation with URL-encoded special characters."""

        query = "symbol=BTCUSDT&data=test%20value%26special"
        signature = generate_signature(query, self._VALID_SECRET)
        assert isinstance(signature, str)
        assert len(signature) == self._EXPECTED_SIGNATURE_LENGTH

    # ───────────────────────────────────────────────────────────
    # VALIDATION CASES
    # ───────────────────────────────────────────────────────────
    def test_generate_signature_empty_query_string(self) -> None:
        """Verify that empty query string raises ValueError with correct message."""

        with self.assertRaises(ValueError) as ctx:
            generate_signature("", self._VALID_SECRET)

        assert self._ERROR_MESSAGE_EMPTY_QUERY in str(ctx.exception)

    def test_generate_signature_empty_api_secret(self) -> None:
        """Verify that empty API secret raises ValueError with correct message."""

        with self.assertRaises(ValueError) as ctx:
            generate_signature(self._VALID_QUERY, "")

        assert self._ERROR_MESSAGE_EMPTY_SECRET in str(ctx.exception)
