import unittest

from helpers.get_slug import get_slug


class TestGetSlug(unittest.TestCase):
    _HELLO_WORLD: str = "Hello World"
    _TEST_STRING: str = "Test String"
    _EXPECTED_HELLO_WORLD: str = "hello-world"
    _EXPECTED_TEST_STRING: str = "test-string"
    _SEPARATOR_UNDERSCORE: str = "_"
    _SEPARATOR_DEFAULT: str = "-"

    def test_get_slug_converts_text_to_lowercase_with_separators(self) -> None:
        test_cases = [
            (self._HELLO_WORLD, self._EXPECTED_HELLO_WORLD),
            (self._TEST_STRING, self._EXPECTED_TEST_STRING),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_preserves_existing_hyphens(self) -> None:
        test_cases = [
            (self._HELLO_WORLD, self._EXPECTED_HELLO_WORLD),
            ("Test-String", self._EXPECTED_TEST_STRING),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_uses_custom_separator(self) -> None:
        test_cases = [
            (self._HELLO_WORLD, "hello_world"),
            ("Test-String", "test_string"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(
                    text,
                    separator=self._SEPARATOR_UNDERSCORE,
                )

                assert result == expected

    def test_get_slug_converts_underscores_to_custom_separator(self) -> None:
        result_default = get_slug("hello_world")
        result_underscore = get_slug(
            "test_string",
            separator=self._SEPARATOR_UNDERSCORE,
        )

        assert result_underscore == "test_string"
        assert result_default == self._EXPECTED_HELLO_WORLD

    def test_get_slug_converts_special_characters_using_dictionary(self) -> None:
        test_cases = [
            ("Hello@World", "hello-at-world"),
            ("Test@String", "test-at-string"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_uses_custom_dictionary(self) -> None:
        dictionary = {"@": "at", "#": "hash"}
        test_cases = [
            ("Hello@World", "hello-at-world"),
            ("Test#String", "test-hash-string"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(
                    text,
                    dictionary=dictionary,
                )

                assert result == expected

    def test_get_slug_removes_accented_characters(self) -> None:
        test_cases = [
            ("Café", "cafe"),
            ("Résumé", "resume"),
            ("Niño", "nino"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_normalizes_multiple_spaces(self) -> None:
        test_cases = [
            ("Hello    World", self._EXPECTED_HELLO_WORLD),
            ("Test   String", self._EXPECTED_TEST_STRING),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_strips_leading_trailing_separators(self) -> None:
        test_cases = [
            ("-Hello World-", self._EXPECTED_HELLO_WORLD),
            ("_Test String_", self._EXPECTED_TEST_STRING),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_converts_uppercase_to_lowercase(self) -> None:
        test_cases = [
            ("HELLO WORLD", self._EXPECTED_HELLO_WORLD),
            ("TEST STRING", self._EXPECTED_TEST_STRING),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_preserves_numbers(self) -> None:
        test_cases = [
            ("Test123", "test123"),
            ("Hello 123 World", "hello-123-world"),
        ]

        for text, expected in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == expected

    def test_get_slug_returns_empty_for_empty_string(self) -> None:
        assert get_slug("") == ""

    def test_get_slug_returns_empty_for_only_separators(self) -> None:
        test_cases = ["---", "___"]

        for text in test_cases:
            with self.subTest(text=text):
                result = get_slug(text)

                assert result == ""
