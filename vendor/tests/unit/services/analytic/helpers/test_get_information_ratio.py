import unittest

from vendor.services.analytic.helpers.get_information_ratio import get_information_ratio


class TestGetInformationRatio(unittest.TestCase):
    def test_get_information_ratio_positive_alpha_positive_tracking_error(self) -> None:
        result = get_information_ratio(alpha=0.10, tracking_error=0.05)

        assert result == 2.0

    def test_get_information_ratio_negative_alpha_returns_negative(self) -> None:
        result = get_information_ratio(alpha=-0.10, tracking_error=0.05)

        assert result == -2.0

    def test_get_information_ratio_zero_alpha_returns_zero(self) -> None:
        result = get_information_ratio(alpha=0.0, tracking_error=0.05)

        assert result == 0.0

    def test_get_information_ratio_zero_tracking_error_returns_zero(self) -> None:
        result = get_information_ratio(alpha=0.10, tracking_error=0.0)

        assert result == 0.0

    def test_get_information_ratio_both_zero_returns_zero(self) -> None:
        result = get_information_ratio(alpha=0.0, tracking_error=0.0)

        assert result == 0.0

    def test_get_information_ratio_excellent_ratio(self) -> None:
        result = get_information_ratio(alpha=0.15, tracking_error=0.10)

        assert abs(result - 1.5) < 0.0001

    def test_get_information_ratio_poor_ratio(self) -> None:
        result = get_information_ratio(alpha=0.02, tracking_error=0.10)

        assert abs(result - 0.2) < 0.0001

    def test_get_information_ratio_various_values(self) -> None:
        test_cases = [
            (0.20, 0.10, 2.0),
            (0.05, 0.10, 0.5),
            (-0.05, 0.10, -0.5),
            (0.10, 0.20, 0.5),
        ]

        for alpha, tracking_error, expected in test_cases:
            with self.subTest(alpha=alpha, tracking_error=tracking_error):
                result = get_information_ratio(alpha, tracking_error)

                assert abs(result - expected) < 0.0001
