import unittest

from helpers.get_slug import get_slug


class TestGetSlug(unittest.TestCase):
    def test_get_slug_basic(self) -> None:
        assert get_slug("Hello World") == "hello-world"
        assert get_slug("Test String") == "test-string"

    def test_get_slug_with_default_separator(self) -> None:
        assert get_slug("Hello World") == "hello-world"
        assert get_slug("Test-String") == "test-string"

    def test_get_slug_with_custom_separator(self) -> None:
        assert get_slug("Hello World", separator="_") == "hello_world"
        assert get_slug("Test-String", separator="_") == "test_string"

    def test_get_slug_with_underscores(self) -> None:
        assert get_slug("hello_world") == "hello-world"
        assert get_slug("test_string", separator="_") == "test_string"

    def test_get_slug_with_special_characters(self) -> None:
        assert get_slug("Hello@World") == "hello-at-world"
        assert get_slug("Test@String") == "test-at-string"

    def test_get_slug_with_custom_dictionary(self) -> None:
        dictionary = {"@": "at", "#": "hash"}
        assert get_slug("Hello@World", dictionary=dictionary) == "hello-at-world"
        assert get_slug("Test#String", dictionary=dictionary) == "test-hash-string"

    def test_get_slug_with_accented_characters(self) -> None:
        assert get_slug("Café") == "cafe"
        assert get_slug("Résumé") == "resume"
        assert get_slug("Niño") == "nino"

    def test_get_slug_with_multiple_spaces(self) -> None:
        assert get_slug("Hello    World") == "hello-world"
        assert get_slug("Test   String") == "test-string"

    def test_get_slug_with_leading_trailing_separators(self) -> None:
        assert get_slug("-Hello World-") == "hello-world"
        assert get_slug("_Test String_") == "test-string"

    def test_get_slug_lowercase(self) -> None:
        assert get_slug("HELLO WORLD") == "hello-world"
        assert get_slug("TEST STRING") == "test-string"

    def test_get_slug_with_numbers(self) -> None:
        assert get_slug("Test123") == "test123"
        assert get_slug("Hello 123 World") == "hello-123-world"

    def test_get_slug_empty_string(self) -> None:
        assert get_slug("") == ""

    def test_get_slug_with_only_separators(self) -> None:
        assert get_slug("---") == ""
        assert get_slug("___") == ""

