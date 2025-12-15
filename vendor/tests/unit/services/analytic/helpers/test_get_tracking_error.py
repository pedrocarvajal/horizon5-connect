import unittest

from vendor.services.analytic.helpers.get_tracking_error import get_tracking_error


class TestGetTrackingError(unittest.TestCase):
    def test_get_tracking_error_with_identical_returns_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, -0.01, 0.03]
        benchmark_returns = [0.01, 0.02, -0.01, 0.03]

        result = get_tracking_error(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_tracking_error_with_different_returns_returns_positive(self) -> None:
        strategy_returns = [0.02, 0.03, -0.02, 0.04]
        benchmark_returns = [0.01, 0.02, -0.01, 0.03]

        result = get_tracking_error(strategy_returns, benchmark_returns)

        assert result > 0.0

    def test_get_tracking_error_with_constant_excess_returns_near_zero(self) -> None:
        strategy_returns = [0.11, 0.12, 0.13, 0.14]
        benchmark_returns = [0.01, 0.02, 0.03, 0.04]

        result = get_tracking_error(strategy_returns, benchmark_returns)

        assert result < 0.0001

    def test_get_tracking_error_with_empty_lists_returns_zero(self) -> None:
        result = get_tracking_error([], [])

        assert result == 0.0

    def test_get_tracking_error_with_single_observation_returns_zero(self) -> None:
        result = get_tracking_error([0.01], [0.01])

        assert result == 0.0

    def test_get_tracking_error_with_different_lengths_returns_zero(self) -> None:
        strategy_returns = [0.01, 0.02, 0.03]
        benchmark_returns = [0.01, 0.02]

        result = get_tracking_error(strategy_returns, benchmark_returns)

        assert result == 0.0

    def test_get_tracking_error_with_two_observations_calculates_correctly(self) -> None:
        strategy_returns = [0.02, 0.04]
        benchmark_returns = [0.01, 0.02]

        result = get_tracking_error(strategy_returns, benchmark_returns)

        assert result > 0.0
