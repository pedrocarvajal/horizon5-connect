import unittest

from vendor.services.analytic.helpers.get_beta import get_beta


class TestGetBeta(unittest.TestCase):
    def test_get_beta_with_identical_returns_returns_one(self) -> None:
        returns = [0.01, 0.02, -0.01, 0.03, -0.02]

        result = get_beta(returns, returns)

        assert abs(result - 1.0) < 0.0001

    def test_get_beta_with_amplified_returns_returns_greater_than_one(self) -> None:
        benchmark_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        strategy_returns = [0.02, 0.04, -0.02, 0.06, -0.04]

        result = get_beta(strategy_returns, benchmark_returns)

        assert result > 1.0

    def test_get_beta_with_dampened_returns_returns_less_than_one(self) -> None:
        benchmark_returns = [0.02, 0.04, -0.02, 0.06, -0.04]
        strategy_returns = [0.01, 0.02, -0.01, 0.03, -0.02]

        result = get_beta(strategy_returns, benchmark_returns)

        assert 0.0 < result < 1.0

    def test_get_beta_with_inverse_returns_returns_negative(self) -> None:
        benchmark_returns = [0.01, 0.02, -0.01, 0.03, -0.02]
        strategy_returns = [-0.01, -0.02, 0.01, -0.03, 0.02]

        result = get_beta(strategy_returns, benchmark_returns)

        assert result < 0.0

    def test_get_beta_with_zero_variance_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03, 0.04]
        benchmark_returns = [0.05, 0.05, 0.05, 0.05]

        result = get_beta(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_beta_with_empty_lists_returns_zero(self) -> None:
        result = get_beta([], [])

        assert result == 0.0

    def test_get_beta_with_single_observation_returns_zero(self) -> None:
        result = get_beta([0.01], [0.01])

        assert result == 0.0

    def test_get_beta_with_different_lengths_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03]
        benchmark_returns = [0.01, 0.02]

        result = get_beta(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_beta_with_uncorrelated_returns_returns_near_zero(self) -> None:
        strategy_returns = [0.01, -0.01, 0.02, -0.02]
        benchmark_returns = [0.01, 0.02, -0.01, -0.02]

        result = get_beta(strategy_returns, benchmark_returns)

        assert abs(result) < 1.0
