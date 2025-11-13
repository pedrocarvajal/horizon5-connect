import argparse
import datetime
import importlib.util
import inspect
from multiprocessing import Process, Queue
from pathlib import Path
from typing import Any

from configs.timezone import TIMEZONE
from interfaces.portfolio import PortfolioInterface
from services.backtest import BacktestService
from services.commands import CommandsService


class Backtest(BacktestService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        super().run()


class Commands(CommandsService):
    # ───────────────────────────────────────────────────────────
    # CONSTRUCTOR
    # ───────────────────────────────────────────────────────────
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)


def _parse_date(
    value: str,
    parser: argparse.ArgumentParser,
    argument: str,
) -> datetime.datetime:
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=TIMEZONE)
    except ValueError:
        parser.error(f"Invalid value for {argument}. Use YYYY-MM-DD (e.g. 2024-01-31).")


def _load_portfolio(
    path: str,
    parser: argparse.ArgumentParser,
) -> PortfolioInterface:
    path_obj = Path(path)
    resolved_path = path_obj if path_obj.is_absolute() else Path.cwd() / path_obj

    if not resolved_path.is_file():
        parser.error(
            "Invalid value for --portfolio-path. Provide a Python file like "
            "portfolios/portfolio.py."
        )

    spec = importlib.util.spec_from_file_location(
        f"portfolio_module_{hash(resolved_path)}",
        resolved_path.as_posix(),
    )

    if spec is None or spec.loader is None:
        parser.error("Unable to load portfolio module.")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    portfolio_classes = [
        member
        for _, member in inspect.getmembers(module, inspect.isclass)
        if issubclass(member, PortfolioInterface) and member is not PortfolioInterface
    ]

    if not portfolio_classes:
        parser.error("Portfolio file must define a PortfolioInterface implementation.")

    portfolio_class = portfolio_classes[0]

    try:
        return portfolio_class()
    except TypeError as exc:
        parser.error(f"Failed to instantiate portfolio: {exc}")


if __name__ == "__main__":
    commands_queue = Queue()
    events_queue = Queue()

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--portfolio-path",
        required=True,
    )

    parser.add_argument(
        "--from-date",
        required=True,
    )

    parser.add_argument(
        "--to-date",
        required=False,
    )

    parser.add_argument(
        "--restore-ticks",
        required=False,
        choices=["true", "false"],
        default="false",
    )

    args = parser.parse_args()

    from_date = _parse_date(
        args.from_date,
        parser,
        "--from-date",
    )

    to_date = (
        _parse_date(args.to_date, parser, "--to-date")
        if args.to_date
        else datetime.datetime.now(tz=TIMEZONE)
    )

    portfolio = _load_portfolio(args.portfolio_path, parser)
    assets = getattr(portfolio, "assets", None)

    if assets is None:
        assets = getattr(portfolio, "_assets", None)

    if not assets:
        parser.error("Portfolio must define at least one asset.")

    processes = [
        Process(
            target=Commands,
            kwargs={
                "commands_queue": commands_queue,
                "events_queue": events_queue,
            },
        ),
    ]

    for asset in assets:
        processes.append(
            Process(
                target=Backtest,
                kwargs={
                    "asset": asset,
                    "from_date": from_date,
                    "to_date": to_date,
                    "commands_queue": commands_queue,
                    "events_queue": events_queue,
                    "args": args,
                },
            )
        )

    for process in processes:
        process.start()

    for process in processes:
        process.join()
