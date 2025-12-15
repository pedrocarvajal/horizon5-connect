import unittest

from vendor.enums.quality_method import QualityMethod
from vendor.models.backtest_expectation import BacktestExpectationModel
from vendor.services.analytic.helpers.get_quality import get_quality


class TestGetQuality(unittest.TestCase):
    def test_get_quality_fqs_with_excellent_metrics_returns_high_score(self) -> None:
        score, method = get_quality(
            method=QualityMethod.FQS,
            days_elapsed=365,
            performance_percentage=0.50,
            max_drawdown=-0.03,
            r_squared=0.9,
        )

        assert method == "fqs"
        assert score > 0.8

    def test_get_quality_fqs_with_poor_metrics_returns_low_score(self) -> None:
        score, method = get_quality(
            method=QualityMethod.FQS,
            days_elapsed=365,
            performance_percentage=0.01,
            max_drawdown=-0.40,
            r_squared=0.1,
        )

        assert method == "fqs"
        assert score < 0.3

    def test_get_quality_drawdown_method_returns_drawdown_name(self) -> None:
        _, method = get_quality(
            method=QualityMethod.DRAWDOWN,
            max_drawdown=-0.10,
        )

        assert method == "drawdown"

    def test_get_quality_profit_factor_method_returns_profit_factor_name(self) -> None:
        _, method = get_quality(
            method=QualityMethod.PROFIT_FACTOR,
            profit_factor=1.5,
        )

        assert method == "profit_factor"

    def test_get_quality_r_squared_method_returns_r_squared_name(self) -> None:
        _, method = get_quality(
            method=QualityMethod.R_SQUARED,
            r_squared=0.6,
        )

        assert method == "r_squared"

    def test_get_quality_win_ratio_method_returns_win_ratio_name(self) -> None:
        _, method = get_quality(
            method=QualityMethod.WIN_RATIO,
            win_ratio=0.55,
        )

        assert method == "win_ratio"

    def test_get_quality_score_normalized_to_zero_one(self) -> None:
        methods = [
            QualityMethod.FQS,
            QualityMethod.DRAWDOWN,
            QualityMethod.PROFIT_FACTOR,
            QualityMethod.R_SQUARED,
            QualityMethod.WIN_RATIO,
        ]

        for method in methods:
            with self.subTest(method=method):
                score, _ = get_quality(
                    method=method,
                    days_elapsed=365,
                    performance_percentage=0.20,
                    max_drawdown=-0.15,
                    r_squared=0.5,
                    profit_factor=1.5,
                    win_ratio=0.5,
                )

                assert 0.0 <= score <= 1.0

    def test_get_quality_with_custom_expectations(self) -> None:
        custom_expectations = BacktestExpectationModel(
            performance_percentage=[0.10, 0.50],
            max_drawdown=[-0.20, -0.05],
            r_squared=[0.5, 0.9],
        )

        score, method = get_quality(
            method=QualityMethod.FQS,
            expectations=custom_expectations,
            days_elapsed=365,
            performance_percentage=0.30,
            max_drawdown=-0.10,
            r_squared=0.7,
        )

        assert method == "fqs"
        assert 0.0 <= score <= 1.0

    def test_get_quality_annualizes_performance(self) -> None:
        score_90_days, _ = get_quality(
            method=QualityMethod.FQS,
            days_elapsed=90,
            performance_percentage=0.10,
            max_drawdown=-0.10,
            r_squared=0.5,
        )

        score_365_days, _ = get_quality(
            method=QualityMethod.FQS,
            days_elapsed=365,
            performance_percentage=0.10,
            max_drawdown=-0.10,
            r_squared=0.5,
        )

        assert score_90_days > score_365_days

    def test_get_quality_drawdown_lower_is_better(self) -> None:
        score_low_dd, _ = get_quality(
            method=QualityMethod.DRAWDOWN,
            max_drawdown=-0.05,
        )

        score_high_dd, _ = get_quality(
            method=QualityMethod.DRAWDOWN,
            max_drawdown=-0.25,
        )

        assert score_low_dd > score_high_dd
