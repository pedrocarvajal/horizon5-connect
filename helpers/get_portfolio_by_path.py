import importlib.util
import inspect
from pathlib import Path

from interfaces.portfolio import PortfolioInterface
from services.logging import LoggingService


def get_portfolio_by_path(
    path: str,
) -> PortfolioInterface:
    log = LoggingService()
    log.setup("get_portfolio_by_path")

    path_obj = Path(path)
    resolved_path = path_obj if path_obj.is_absolute() else Path.cwd() / path_obj

    if not resolved_path.is_file():
        log.error(
            "Invalid value for --portfolio-path. Provide a Python file like "
            "portfolios/portfolio.py."
        )

    spec = importlib.util.spec_from_file_location(
        f"portfolio_module_{hash(resolved_path)}",
        resolved_path.as_posix(),
    )

    if spec is None or spec.loader is None:
        log.error("Unable to load portfolio module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    portfolio_classes = [
        member
        for _, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, PortfolioInterface) and member is not PortfolioInterface
    ]

    if not portfolio_classes:
        log.error("Portfolio file must define a PortfolioInterface implementation.")

    portfolio_class = portfolio_classes[0]

    try:
        return portfolio_class()
    except TypeError as exc:
        log.error(f"Failed to instantiate portfolio: {exc}")
