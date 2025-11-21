# Code reviewed on 2025-11-21 by Pedro Carvajal

import unittest
from pathlib import Path

from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.portfolio import PortfolioInterface


class TestGetPortfolioByPath(unittest.TestCase):
    # ───────────────────────────────────────────────────────────
    # CONSTANTS
    # ───────────────────────────────────────────────────────────
    _PORTFOLIO_ID: str = "low-risk"
    _PORTFOLIO_FILENAME: str = "low-risk.py"
    _PORTFOLIO_DIR: str = "portfolios"

    # ───────────────────────────────────────────────────────────
    # SUCCESS CASES
    # ───────────────────────────────────────────────────────────
    def test_get_portfolio_by_path_with_absolute_path_returns_portfolio(self) -> None:
        """Verify portfolio loading with absolute file path."""
        portfolio_path = (
            Path(__file__).parent.parent.parent / self._PORTFOLIO_DIR / self._PORTFOLIO_FILENAME
        )
        portfolio = get_portfolio_by_path(str(portfolio_path))

        assert portfolio is not None
        assert isinstance(portfolio, PortfolioInterface)
        assert portfolio.id == self._PORTFOLIO_ID

    def test_get_portfolio_by_path_with_relative_path_returns_portfolio(self) -> None:
        """Verify portfolio loading with relative file path."""
        portfolio_path = f"{self._PORTFOLIO_DIR}/{self._PORTFOLIO_FILENAME}"
        portfolio = get_portfolio_by_path(portfolio_path)

        assert portfolio is not None
        assert isinstance(portfolio, PortfolioInterface)
        assert portfolio.id == self._PORTFOLIO_ID
