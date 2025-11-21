import unittest
from pathlib import Path

from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.portfolio import PortfolioInterface


class TestGetPortfolioByPath(unittest.TestCase):
    def test_get_portfolio_by_path_with_absolute_path(self) -> None:
        portfolio_path = Path(__file__).parent.parent.parent / "portfolios" / "low-risk.py"

        portfolio = get_portfolio_by_path(str(portfolio_path))

        assert portfolio is not None
        assert isinstance(portfolio, PortfolioInterface)
        assert portfolio.id == "low-risk"

    def test_get_portfolio_by_path_with_relative_path(self) -> None:
        portfolio = get_portfolio_by_path("portfolios/low-risk.py")

        assert portfolio is not None
        assert isinstance(portfolio, PortfolioInterface)
        assert portfolio.id == "low-risk"

