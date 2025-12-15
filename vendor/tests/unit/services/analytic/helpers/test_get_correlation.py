import unittest

from vendor.services.analytic.helpers.get_correlation import get_correlation


class TestGetCorrelation(unittest.TestCase):
    def test_get_correlation_with_identical_returns_returns_one(self) -> None:
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]

        result = get_correlation(returns, returns)

        assert abs(result - 1.0) < 0.0001

    def test_get_correlation_with_inverse_returns_returns_negative_one(self) -> None:
        strategy_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        benchmark_returns = [-0.01, -0.02, 0.01, -0.03, 0.02]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert abs(result - (-1.0)) < 0.0001

    def test_get_correlation_returns_value_between_minus_one_and_one(self) -> None:
        strategy_returns = [0.01, 0.03, -0.02, 0.04, -0.01]
        benchmark_returns = [0.02, 0.01, -0.01, 0.03, 0.00]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert -1.0 <= result <= 1.0

    def test_get_correlation_with_zero_variance_strategy_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.01, 0.01, 0.01]
        benchmark_returns = [0.01, 0.02, 0.03, 0.04]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_correlation_with_zero_variance_benchmark_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03, 0.04]
        benchmark_returns = [0.05, 0.05, 0.05, 0.05]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_correlation_with_empty_lists_returns_zero(self) -> None:
        result = get_correlation([], [])

        assert result == 0.0

    def test_get_correlation_with_single_observation_returns_zero(self) -> None:
        result = get_correlation([0.01], [0.01])

        assert result == 0.0

    def test_get_correlation_with_different_lengths_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03]
        benchmark_returns = [0.01, 0.02]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_correlation_positive_correlation(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03, 0.04, 0.05]
        benchmark_returns = [0.02, 0.04, 0.06, 0.08, 0.10]

        result = get_correlation(strategy_returns, benchmark_returns)

        assert result > 0.9
