import unittest

from vendor.services.analytic.helpers.get_alpha import get_alpha


class TestGetAlpha(unittest.TestCase):
    def test_get_alpha_with_outperformance_returns_positive(self) -> None:
        strategy_returns = [0.02, 0.03, 0.01, 0.04]
        benchmark_returns = [0.01, 0.02, 0.00, 0.03]
        beta = 1.0

        result = get_alpha(strategy_returns, benchmark_returns, beta)

        assert result > 0.0

    def test_get_alpha_with_underperformance_returns_negative(self) -> None:
        strategy_returns = [0.01, 0.02, 0.00, 0.03]
        benchmark_returns = [0.02, 0.03, 0.01, 0.04]
        beta = 1.0

        result = get_alpha(strategy_returns, benchmark_returns, beta)

        assert result < 0.0

    def test_get_alpha_with_same_performance_and_beta_one_returns_zero(self) -> None:
        returns = [0.01, 0.02, 0.03, 0.04]
        beta = 1.0

        result = get_alpha(returns, returns, beta)

        assert result == 0.0

    def test_get_alpha_with_zero_beta_returns_strategy_mean(self) -> None:
        strategy_returns = [0.02, 0.04, 0.06, 0.08]
        benchmark_returns = [0.01, 0.02, 0.03, 0.04]
        beta = 0.0

        result = get_alpha(strategy_returns, benchmark_returns, beta)

        expected_mean = sum(strategy_returns) / len(strategy_returns)
        assert abs(result - expected_mean) < 0.0001

    def test_get_alpha_with_empty_lists_returns_zero(self) -> None:
        result = get_alpha([], [], 1.0)

        assert result == 0.0

    def test_get_alpha_with_single_observation_returns_zero(self) -> None:
        result = get_alpha([0.01], [0.01], 1.0)

        assert result == 0.0

    def test_get_alpha_with_different_lengths_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03]
        benchmark_returns = [0.01, 0.02]

        result = get_alpha(strategy_returns, benchmark_returns, 1.0)

        assert result == 0.0

    def test_get_alpha_with_high_beta_reduces_alpha(self) -> None:
        strategy_returns = [0.02, 0.03, 0.01, 0.04]
        benchmark_returns = [0.01, 0.02, 0.00, 0.03]
        low_beta = 0.5
        high_beta = 2.0

        alpha_low = get_alpha(strategy_returns, benchmark_returns, low_beta)
        alpha_high = get_alpha(strategy_returns, benchmark_returns, high_beta)

        assert alpha_low > alpha_high
