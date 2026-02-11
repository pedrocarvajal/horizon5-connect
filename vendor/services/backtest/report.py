"""Backtest report generator for CSV exports and performance charts."""

from __future__ import annotations

import csv
import datetime
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from vendor.configs.timezone import TIMEZONE

matplotlib.use("Agg")

_DATETIME_MIN = datetime.datetime.min.replace(tzinfo=TIMEZONE)

STORAGE_BASE = Path("storage/backtests")


def generate_report(
    backtest_id: str,
    report: Dict[str, Any],
    trade_histories: Dict[str, List[Dict[str, Any]]],
    allocation: float,
) -> Path:
    """Generate backtest report files: CSVs and performance charts.

    Args:
        backtest_id: Unique backtest identifier.
        report: Portfolio report dictionary from on_end().
        trade_histories: Dict mapping strategy_id to list of trade dicts.
        allocation: Total portfolio allocation.

    Returns:
        Path to the generated report directory.
    """
    output_directory = STORAGE_BASE / backtest_id
    output_directory.mkdir(parents=True, exist_ok=True)

    all_trades: List[Dict[str, Any]] = []

    for strategy_id, trades in trade_histories.items():
        _write_orders_csv(output_directory, strategy_id, trades)
        _generate_strategy_chart(output_directory, strategy_id, trades, allocation)
        all_trades.extend(trades)

    if all_trades:
        _write_orders_csv(output_directory, "portfolio", all_trades)
        _generate_strategy_chart(output_directory, "portfolio", all_trades, allocation)

    _write_summary(output_directory, report)

    return output_directory


def _write_orders_csv(
    output_directory: Path,
    name: str,
    trades: List[Dict[str, Any]],
) -> None:
    """Write trade orders to CSV file.

    Args:
        output_directory: Directory to write the CSV.
        name: Strategy name or 'portfolio' for the filename.
        trades: List of trade dictionaries.
    """
    if not trades:
        return

    filepath = output_directory / f"orders_{name}.csv"

    fieldnames = [
        "id",
        "strategy_id",
        "symbol",
        "side",
        "status",
        "volume",
        "price",
        "close_price",
        "take_profit_price",
        "stop_loss_price",
        "profit",
        "profit_percentage",
        "created_at",
        "updated_at",
    ]

    sorted_trades = sorted(trades, key=lambda t: t.get("created_at") or "")

    with filepath.open("w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(sorted_trades)


def _generate_strategy_chart(
    output_directory: Path,
    name: str,
    trades: List[Dict[str, Any]],
    allocation: float,
) -> None:
    """Generate performance + drawdown chart for a strategy.

    Args:
        output_directory: Directory to save the chart image.
        name: Strategy name or 'portfolio' for the filename.
        trades: List of trade dictionaries sorted by close date.
        allocation: Starting allocation for equity calculation.
    """
    if not trades:
        return

    sorted_trades = sorted(trades, key=lambda t: t.get("updated_at") or _DATETIME_MIN)

    dates: List[datetime.datetime] = []
    equity_values: List[float] = []
    cumulative_profit = 0.0

    dates.append(sorted_trades[0].get("created_at") or _DATETIME_MIN)
    equity_values.append(allocation)

    for trade in sorted_trades:
        cumulative_profit += trade.get("profit", 0)
        close_date = trade.get("updated_at") or _DATETIME_MIN
        dates.append(close_date)
        equity_values.append(allocation + cumulative_profit)

    peak = equity_values[0]
    drawdown_values: List[float] = []

    for equity in equity_values:
        peak = max(peak, equity)
        drawdown_pct = ((equity - peak) / peak) * 100 if peak > 0 else 0
        drawdown_values.append(drawdown_pct)

    fig, (ax_equity, ax_drawdown) = plt.subplots(  # type: ignore[misc]
        2,
        1,
        figsize=(14, 8),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )

    ax_equity.plot(dates, equity_values, color="#2196F3", linewidth=1.5)
    ax_equity.fill_between(dates, allocation, equity_values, alpha=0.1, color="#2196F3")
    ax_equity.axhline(y=allocation, color="#9E9E9E", linestyle="--", linewidth=0.8, alpha=0.6)
    ax_equity.set_ylabel("Equity ($)")
    ax_equity.set_title(f"Performance: {name}", fontsize=13, fontweight="bold")
    ax_equity.grid(True, alpha=0.3)

    def format_dollar(x: float, _pos: int) -> str:
        return f"${x:,.0f}"

    ax_equity.yaxis.set_major_formatter(FuncFormatter(format_dollar))

    final_equity = equity_values[-1]
    return_pct = ((final_equity - allocation) / allocation) * 100
    max_dd = min(drawdown_values)
    ax_equity.text(
        0.02,
        0.95,
        f"Return: {return_pct:+.2f}%  |  Final: ${final_equity:,.2f}  |  Max DD: {max_dd:.2f}%",
        transform=ax_equity.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
    )

    colors = ["#F44336" if d < 0 else "#4CAF50" for d in drawdown_values]
    ax_drawdown.bar(dates, drawdown_values, color=colors, width=0.8, alpha=0.7)
    ax_drawdown.set_ylabel("Drawdown (%)")
    ax_drawdown.set_xlabel("Date")
    ax_drawdown.grid(True, alpha=0.3)

    def format_percent(x: float, _pos: int) -> str:
        return f"{x:.1f}%"

    ax_drawdown.yaxis.set_major_formatter(FuncFormatter(format_percent))

    fig.autofmt_xdate()
    plt.tight_layout()

    filepath = output_directory / f"performance_{name}.png"
    fig.savefig(str(filepath), dpi=150, bbox_inches="tight")  # type: ignore[call-overload]
    plt.close(fig)


def _write_summary(output_directory: Path, report: Dict[str, Any]) -> None:
    """Write a text summary of the backtest report.

    Args:
        output_directory: Directory to write the summary.
        report: Portfolio report dictionary.
    """
    filepath = output_directory / "summary.txt"

    lines = [
        "=" * 60,
        f"  BACKTEST REPORT: {report.get('portfolio', 'N/A')}",
        "=" * 60,
        f"  Allocation:    ${report.get('allocation', 0):,.2f}",
        f"  Total Profit:  ${report.get('total_profit', 0):,.2f}",
        f"  Return:        {report.get('return_pct', 0):.2f}%",
        f"  Total Trades:  {report.get('total_trades', 0)}",
    ]

    for asset_report in report.get("assets", []):
        lines.append(f"\n  --- {asset_report.get('symbol', 'N/A')} ---")
        lines.append(f"  Allocation:  ${asset_report.get('allocation', 0):,.2f}")
        lines.append(f"  Balance:     ${asset_report.get('balance', 0):,.2f}")
        lines.append(f"  NAV:         ${asset_report.get('nav', 0):,.2f}")
        lines.append(f"  Profit:      ${asset_report.get('total_profit', 0):,.2f}")
        lines.append(f"  Return:      {asset_report.get('return_pct', 0):.2f}%")

        for strategy_report in asset_report.get("strategies", []):
            lines.append(f"\n    [{strategy_report.get('strategy_id', 'N/A')}]")
            lines.append(f"    Trades:        {strategy_report.get('total_trades', 0)}")
            wins = strategy_report.get("winning_trades", 0)
            losses = strategy_report.get("losing_trades", 0)
            lines.append(f"    Win/Loss:      {wins}/{losses}")
            lines.append(f"    Win Rate:      {strategy_report.get('win_rate', 0):.2f}%")
            lines.append(f"    Profit:        ${strategy_report.get('total_profit', 0):,.2f}")
            lines.append(f"    Gross Profit:  ${strategy_report.get('gross_profit', 0):,.2f}")
            lines.append(f"    Gross Loss:    ${strategy_report.get('gross_loss', 0):,.2f}")
            lines.append(f"    Avg Win:       ${strategy_report.get('average_win', 0):,.2f}")
            lines.append(f"    Avg Loss:      ${strategy_report.get('average_loss', 0):,.2f}")
            lines.append(f"    Profit Factor: {strategy_report.get('profit_factor', 0):.2f}")

    lines.append("=" * 60)

    filepath.write_text("\n".join(lines) + "\n")
