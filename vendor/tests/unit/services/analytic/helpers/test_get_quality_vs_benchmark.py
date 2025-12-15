import unittest
from typing import ClassVar, List

from vendor.enums.quality_vs_benchmark_method import QualityVsBenchmarkMethod
from vendor.services.analytic.helpers.get_quality_vs_benchmark import get_quality_vs_benchmark


class TestGetQualityVsBenchmark(unittest.TestCase):
    _STRATEGY_NAV_HISTORY: ClassVar[List[float]] = [100.0, 102.0, 104.0, 103.0, 106.0, 108.0, 110.0]
    _BENCHMARK_PRICE_HISTORY: ClassVar[List[float]] = [50.0, 50.5, 51.0, 50.8, 51.5, 52.0, 52.5]
    _BENCHMARK_INITIAL_PRICE: float = 50.0

    def test_get_quality_vs_benchmark_returns_normalized_score(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.05,
            information_ratio=0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert 0.0 <= score <= 1.0

    def test_get_quality_vs_benchmark_excellent_alpha_returns_high_score(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.25,
            information_ratio=1.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert score > 0.7

    def test_get_quality_vs_benchmark_poor_alpha_returns_low_score(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=-0.25,
            information_ratio=-0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert score < 0.5

    def test_get_quality_vs_benchmark_insufficient_strategy_data_returns_zero(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.10,
            information_ratio=0.5,
            strategy_nav_history=[100.0],
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert score == 0.0

    def test_get_quality_vs_benchmark_insufficient_benchmark_data_returns_zero(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.10,
            information_ratio=0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=[50.0],
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert score == 0.0

    def test_get_quality_vs_benchmark_zero_initial_price_returns_zero(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.10,
            information_ratio=0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=0.0,
        )

        assert score == 0.0

    def test_get_quality_vs_benchmark_empty_histories_returns_zero(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.10,
            information_ratio=0.5,
            strategy_nav_history=[],
            benchmark_price_history=[],
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert score == 0.0

    def test_get_quality_vs_benchmark_zero_alpha_and_ir_returns_mid_score(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.FQS_BENCHMARK,
            alpha=0.0,
            information_ratio=0.0,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert 0.3 < score < 0.7

    def test_get_quality_vs_benchmark_alpha_method(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.ALPHA,
            alpha=0.15,
            information_ratio=0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert 0.0 <= score <= 1.0

    def test_get_quality_vs_benchmark_information_ratio_method(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.INFORMATION_RATIO,
            alpha=0.10,
            information_ratio=1.0,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert 0.0 <= score <= 1.0

    def test_get_quality_vs_benchmark_excess_sharpe_method(self) -> None:
        score = get_quality_vs_benchmark(
            method=QualityVsBenchmarkMethod.EXCESS_SHARPE,
            alpha=0.10,
            information_ratio=0.5,
            strategy_nav_history=self._STRATEGY_NAV_HISTORY,
            benchmark_price_history=self._BENCHMARK_PRICE_HISTORY,
            benchmark_initial_price=self._BENCHMARK_INITIAL_PRICE,
        )

        assert 0.0 <= score <= 1.0
