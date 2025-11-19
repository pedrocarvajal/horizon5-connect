import os
import shutil
import tempfile
import unittest
from pathlib import Path

from helpers.get_portfolio_by_path import get_portfolio_by_path
from interfaces.portfolio import PortfolioInterface


class MockPortfolio(PortfolioInterface):
    def get_assets(self):
        return []


class TestGetPortfolioByPath(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp()
        self.temp_file = Path(self.temp_dir) / "test_portfolio.py"

    def tearDown(self) -> None:
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_portfolio_by_path_with_valid_portfolio(self) -> None:
        portfolio_content = """
from interfaces.portfolio import PortfolioInterface

class TestPortfolio(PortfolioInterface):
    def get_assets(self):
        return []
"""
        self.temp_file.write_text(portfolio_content)

        portfolio = get_portfolio_by_path(str(self.temp_file))
        assert portfolio is not None
        assert isinstance(portfolio, PortfolioInterface)

    def test_get_portfolio_by_path_with_relative_path(self) -> None:
        portfolio_content = """
from interfaces.portfolio import PortfolioInterface

class TestPortfolio(PortfolioInterface):
    def get_assets(self):
        return []
"""
        self.temp_file.write_text(portfolio_content)

        original_cwd = os.getcwd()
        try:
            os.chdir(self.temp_dir)
            portfolio = get_portfolio_by_path("test_portfolio.py")
            assert portfolio is not None
            assert isinstance(portfolio, PortfolioInterface)
        finally:
            os.chdir(original_cwd)

