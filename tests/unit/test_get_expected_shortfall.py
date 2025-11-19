import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "get_expected_shortfall",
    Path(__file__).parent.parent.parent / "services" / "analytic" / "helpers" / "get_expected_shortfall.py",
)
get_expected_shortfall_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_expected_shortfall_module)
get_expected_shortfall = get_expected_shortfall_module.get_expected_shortfall


class TestGetExpectedShortfall(unittest.TestCase):
    def test_get_expected_shortfall_insufficient_data(self) -> None:
        nav_history = [1000.0]
        assert get_expected_shortfall(nav_history) == 0.0

    def test_get_expected_shortfall_empty_list(self) -> None:
        nav_history: list[float] = []
        assert get_expected_shortfall(nav_history) == 0.0

    def test_get_expected_shortfall_default_confidence(self) -> None:
        nav_history = [1000.0, 990.0, 980.0, 970.0, 960.0]
        result = get_expected_shortfall(nav_history)
        assert isinstance(result, float)

    def test_get_expected_shortfall_custom_confidence(self) -> None:
        nav_history = [1000.0, 990.0, 980.0, 970.0, 960.0]
        result = get_expected_shortfall(nav_history, confidence_level=0.90)
        assert isinstance(result, float)

    def test_get_expected_shortfall_negative_returns(self) -> None:
        nav_history = [1000.0, 900.0, 800.0, 700.0]
        result = get_expected_shortfall(nav_history)
        assert result < 0

    def test_get_expected_shortfall_positive_returns(self) -> None:
        nav_history = [1000.0, 1010.0, 1020.0, 1030.0]
        result = get_expected_shortfall(nav_history)
        assert isinstance(result, float)

    def test_get_expected_shortfall_with_zero_nav(self) -> None:
        nav_history = [1000.0, 0.0, 1000.0]
        result = get_expected_shortfall(nav_history)
        assert isinstance(result, float)

