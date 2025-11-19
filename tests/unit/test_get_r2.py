import importlib.util
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "get_r2",
    Path(__file__).parent.parent.parent / "services" / "analytic" / "helpers" / "get_r2.py",
)
get_r2_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(get_r2_module)
get_r2 = get_r2_module.get_r2


class TestGetR2(unittest.TestCase):
    def test_get_r2_insufficient_data(self) -> None:
        values = [100.0]
        assert get_r2(values) == 0.0

    def test_get_r2_empty_list(self) -> None:
        values: list[float] = []
        assert get_r2(values) == 0.0

    def test_get_r2_perfect_linear(self) -> None:
        values = [100.0, 110.0, 120.0, 130.0, 140.0]
        result = get_r2(values)
        assert result > 0.9

    def test_get_r2_no_variance(self) -> None:
        values = [100.0, 100.0, 100.0, 100.0]
        assert get_r2(values) == 0.0

    def test_get_r2_volatile(self) -> None:
        values = [100.0, 50.0, 150.0, 75.0, 125.0]
        result = get_r2(values)
        assert 0.0 <= result <= 1.0

    def test_get_r2_negative_trend(self) -> None:
        values = [100.0, 90.0, 80.0, 70.0, 60.0]
        result = get_r2(values)
        assert result > 0.9

    def test_get_r2_mixed_trend(self) -> None:
        values = [100.0, 105.0, 98.0, 110.0, 95.0]
        result = get_r2(values)
        assert 0.0 <= result <= 1.0

