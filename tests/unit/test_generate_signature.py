import unittest

from services.gateway.gateways.binance.helpers.generate_signature import generate_signature


class TestGenerateSignature(unittest.TestCase):
    def test_generate_signature_basic(self) -> None:
        query_string = "symbol=BTCUSDT&timestamp=1234567890"
        api_secret = "test_secret"
        signature = generate_signature(query_string, api_secret)
        assert isinstance(signature, str)
        assert len(signature) == 64

    def test_generate_signature_deterministic(self) -> None:
        query_string = "symbol=BTCUSDT&timestamp=1234567890"
        api_secret = "test_secret"
        signature1 = generate_signature(query_string, api_secret)
        signature2 = generate_signature(query_string, api_secret)
        assert signature1 == signature2

    def test_generate_signature_different_secrets(self) -> None:
        query_string = "symbol=BTCUSDT&timestamp=1234567890"
        signature1 = generate_signature(query_string, "secret1")
        signature2 = generate_signature(query_string, "secret2")
        assert signature1 != signature2

    def test_generate_signature_different_queries(self) -> None:
        api_secret = "test_secret"
        signature1 = generate_signature("symbol=BTCUSDT&timestamp=1234567890", api_secret)
        signature2 = generate_signature("symbol=ETHUSDT&timestamp=1234567890", api_secret)
        assert signature1 != signature2

    def test_generate_signature_empty_query_string(self) -> None:
        api_secret = "test_secret"
        with self.assertRaises(ValueError):
            generate_signature("", api_secret)

    def test_generate_signature_empty_api_secret(self) -> None:
        query_string = "symbol=BTCUSDT&timestamp=1234567890"
        with self.assertRaises(ValueError):
            generate_signature(query_string, "")

