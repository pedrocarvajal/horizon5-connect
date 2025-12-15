import unittest

from vendor.services.analytic.helpers.get_win_ratio import get_win_ratio


class TestGetWinRatio(unittest.TestCase):
    def test_get_win_ratio_all_winners_returns_one(self) -> None:
        trades_profits = [100.0, 50.0, 25.0, 75.0]

        result = get_win_ratio(trades_profits)

        assert result == 1.0

    def test_get_win_ratio_all_losers_returns_zero(self) -> None:
        trades_profits = [-100.0, -50.0, -25.0, -75.0]

        result = get_win_ratio(trades_profits)

        assert result == 0.0

    def test_get_win_ratio_half_winners_returns_half(self) -> None:
        trades_profits = [100.0, -50.0, 25.0, -75.0]

        result = get_win_ratio(trades_profits)

        assert result == 0.5

    def test_get_win_ratio_empty_list_returns_zero(self) -> None:
        result = get_win_ratio([])

        assert result == 0.0

    def test_get_win_ratio_single_winner_returns_one(self) -> None:
        result = get_win_ratio([100.0])

        assert result == 1.0

    def test_get_win_ratio_single_loser_returns_zero(self) -> None:
        result = get_win_ratio([-100.0])

        assert result == 0.0

    def test_get_win_ratio_zero_profit_not_counted_as_winner(self) -> None:
        trades_profits = [100.0, 0.0, -50.0]

        result = get_win_ratio(trades_profits)

        assert abs(result - (1.0 / 3.0)) < 0.0001

    def test_get_win_ratio_with_mixed_profits(self) -> None:
        test_cases = [
            ([100.0, 50.0, -25.0, -75.0, 30.0], 0.6),
            ([100.0, -50.0], 0.5),
            ([-10.0, -20.0, 5.0], 1.0 / 3.0),
        ]

        for trades, expected in test_cases:
            with self.subTest(trades=trades):
                result = get_win_ratio(trades)

                assert abs(result - expected) < 0.0001
