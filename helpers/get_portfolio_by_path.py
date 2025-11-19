# Code reviewed on 2025-11-19 by pedrocarvajal

import importlib.util
import inspect
from pathlib import Path

from interfaces.portfolio import PortfolioInterface
from services.logging import LoggingService


def get_portfolio_by_path(
    path: str,
) -> PortfolioInterface:
    """
    Load portfolio from Python file path.

    Args:
        path: Path to Python file containing PortfolioInterface implementation
              Can be absolute or relative to current working directory

    Returns:
        PortfolioInterface instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If unable to load module, no portfolio class found, or instantiation fails
    """
    log = LoggingService()
    log.setup("get_portfolio_by_path")

    path_obj = Path(path)
    resolved_path = path_obj if path_obj.is_absolute() else Path.cwd() / path_obj

    if not resolved_path.is_file():
        error_msg = "Invalid value for --portfolio-path. Provide a Python file like portfolios/portfolio.py."
        log.error(error_msg)
        raise FileNotFoundError(error_msg)

    spec = importlib.util.spec_from_file_location(
        f"portfolio_module_{hash(resolved_path)}",
        resolved_path.as_posix(),
    )

    if spec is None or spec.loader is None:
        error_msg = "Unable to load portfolio module."
        log.error(error_msg)
        raise ValueError(error_msg)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    portfolio_classes = [
        member
        for _, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, PortfolioInterface) and member is not PortfolioInterface
    ]

    if not portfolio_classes:
        error_msg = "Portfolio file must define a PortfolioInterface implementation."
        log.error(error_msg)
        raise ValueError(error_msg)

    portfolio_class = portfolio_classes[0]

    try:
        return portfolio_class()
    except TypeError as exc:
        error_msg = f"Failed to instantiate portfolio: {exc}"
        log.error(error_msg)
        raise ValueError(error_msg) from exc
