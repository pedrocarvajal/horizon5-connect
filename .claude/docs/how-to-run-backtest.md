# Backtest Execution Guide

## Command Structure

```bash
uv run python backtest.py --portfolio-path <path> --from-date <date> [--to-date <date>] [--restore-ticks true|false]
```

## Arguments

### Required

| Argument | Description |
|----------|-------------|
| `--portfolio-path` | Path to portfolio file (e.g., `portfolios/bitcoin.py`) |
| `--from-date` | Start date in `YYYY-MM-DD` format |

### Optional

| Argument | Description |
|----------|-------------|
| `--to-date` | End date in `YYYY-MM-DD` format (defaults to today) |
| `--restore-ticks` | Set to `true` to force full data cleanup before backtest (10s delay warning) |

## Examples

```bash
uv run python backtest.py --portfolio-path portfolios/bitcoin.py --from-date 2023-02-11

uv run python backtest.py --portfolio-path portfolios/bitcoin.py --from-date 2023-02-11 --to-date 2026-02-11

uv run python backtest.py --portfolio-path portfolios/bitcoin.py --from-date 2023-02-11 --restore-ticks true
```

## Analyzing Results

The backtest outputs a report to console and generates files at `storage/backtests/{backtest_id}/`:

- **summary.txt**: Text report with all metrics
- **orders_{strategy_id}.csv**: CSV with all trade orders per strategy
- **orders_portfolio.csv**: Consolidated CSV of all trades
- **performance_{strategy_id}.png**: Equity curve + drawdown chart per strategy
- **performance_portfolio.png**: Portfolio-level performance chart

### Key Metrics

- **Return %**: Total portfolio return
- **Max Drawdown %**: Largest peak-to-trough decline
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss ratio
- **Number of trades**: Total executed trades

## Troubleshooting

| Error | Solution |
|-------|----------|
| No enabled assets found | Check portfolio has at least one asset in `assets` list |
| API credentials required | Non-blocking for backtests, kline data uses public API |
| Date parsing errors | Use `YYYY-MM-DD` format strictly |
