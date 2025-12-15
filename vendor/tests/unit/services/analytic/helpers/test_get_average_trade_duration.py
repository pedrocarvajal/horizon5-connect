import unittest

from vendor.services.analytic.helpers.get_average_trade_duration import get_average_trade_duration


class TestGetAverageTradeDuration(unittest.TestCase):
    def test_get_average_trade_duration_returns_mean(self) -> None:
        durations = [60.0, 120.0, 180.0, 240.0]

        result = get_average_trade_duration(durations)

        assert result == 150.0

    def test_get_average_trade_duration_empty_list_returns_zero(self) -> None:
        result = get_average_trade_duration([])

        assert result == 0.0

    def test_get_average_trade_duration_single_value_returns_same(self) -> None:
        result = get_average_trade_duration([120.0])

        assert result == 120.0

    def test_get_average_trade_duration_all_same_returns_same(self) -> None:
        durations = [60.0, 60.0, 60.0, 60.0]

        result = get_average_trade_duration(durations)

        assert result == 60.0

    def test_get_average_trade_duration_with_zero_duration(self) -> None:
        durations = [0.0, 60.0, 120.0]

        result = get_average_trade_duration(durations)

        assert result == 60.0

    def test_get_average_trade_duration_scalping_range(self) -> None:
        durations = [5.0, 10.0, 15.0, 20.0, 10.0]

        result = get_average_trade_duration(durations)

        assert result < 60.0

    def test_get_average_trade_duration_swing_trade_range(self) -> None:
        durations = [300.0, 480.0, 720.0, 600.0]

        result = get_average_trade_duration(durations)

        assert 240.0 < result < 1440.0

    def test_get_average_trade_duration_position_trade_range(self) -> None:
        durations = [1500.0, 2880.0, 4320.0]

        result = get_average_trade_duration(durations)

        assert result > 1440.0
