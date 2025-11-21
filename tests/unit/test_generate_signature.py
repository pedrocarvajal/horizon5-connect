import unittest

from services.gateway.gateways.binance.helpers.generate_signature import generate_signature


class TestGenerateSignature(unittest.TestCase):
    VALID_QUERY = "symbol=BTCUSDT&timestamp=1234567890"
    VALID_SECRET = "test_secret"

    def test_generate_signature_basic(self) -> None:
        """Verify basic signature generation returns correct format."""
        signature = generate_signature(self.VALID_QUERY, self.VALID_SECRET)
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)

    def test_generate_signature_deterministic(self) -> None:
        """Verify that identical inputs produce identical signatures."""
        signature1 = generate_signature(self.VALID_QUERY, self.VALID_SECRET)
        signature2 = generate_signature(self.VALID_QUERY, self.VALID_SECRET)
        self.assertEqual(signature1, signature2)

    def test_generate_signature_different_secrets(self) -> None:
        """Verify that different secrets produce different signatures."""
        signature1 = generate_signature(self.VALID_QUERY, "secret1")
        signature2 = generate_signature(self.VALID_QUERY, "secret2")
        self.assertNotEqual(signature1, signature2)

    def test_generate_signature_different_queries(self) -> None:
        """Verify that different query strings produce different signatures."""
        signature1 = generate_signature("symbol=BTCUSDT&timestamp=1234567890", self.VALID_SECRET)
        signature2 = generate_signature("symbol=ETHUSDT&timestamp=1234567890", self.VALID_SECRET)
        self.assertNotEqual(signature1, signature2)

    def test_generate_signature_known_value(self) -> None:
        """Regression test with known Binance API signature value."""
        query = "symbol=LTCBTC&side=BUY&type=LIMIT&timeInForce=GTC&quantity=1&price=0.1&recvWindow=5000&timestamp=1499827319559"
        secret = "NhqPtmdSJYdKjVHjA7PZj4Mge3R5YNiP1e3UZjInClVN65XAbvqqM6A7H5fATj0j"
        expected = "c8db56825ae71d6d79447849e617115f4a920fa2acdcab2b053c4b2838bd6b71"
        signature = generate_signature(query, secret)
        self.assertEqual(signature, expected)

    def test_generate_signature_with_special_chars(self) -> None:
        """Verify signature generation with URL-encoded special characters."""
        query = "symbol=BTCUSDT&data=test%20value%26special"
        signature = generate_signature(query, self.VALID_SECRET)
        self.assertIsInstance(signature, str)
        self.assertEqual(len(signature), 64)

    def test_generate_signature_empty_query_string(self) -> None:
        """Verify that empty query string raises ValueError with correct message."""
        with self.assertRaises(ValueError) as ctx:
            generate_signature("", self.VALID_SECRET)
        self.assertIn("Query string cannot be empty", str(ctx.exception))

    def test_generate_signature_empty_api_secret(self) -> None:
        """Verify that empty API secret raises ValueError with correct message."""
        with self.assertRaises(ValueError) as ctx:
            generate_signature(self.VALID_QUERY, "")
        self.assertIn("API secret cannot be empty", str(ctx.exception))
