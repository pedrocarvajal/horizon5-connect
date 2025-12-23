# Backtest Execution Guide

## Command Structure

```bash
uv run python backtest.py --portfolio-path <path> --from-date <date> [--to-date <date>] [--restore-ticks true|false]
```

## Arguments

### Required

| Argument | Description |
|----------|-------------|
| `--portfolio-path` | Path to portfolio file (e.g., `portfolios/xauusd-test.py`) |
| `--from-date` | Start date in `YYYY-MM-DD` format |

### Optional

| Argument | Description |
|----------|-------------|
| `--to-date` | End date in `YYYY-MM-DD` format (defaults to today) |
| `--restore-ticks` | Set to `true` to force full data cleanup before backtest (10s delay warning) |

## Examples

```bash
uv run python backtest.py --portfolio-path portfolios/xauusd-test.py --from-date 2022-01-01

uv run python backtest.py --portfolio-path portfolios/gbpusd-test.py --from-date 2021-06-01 --to-date 2024-01-01

uv run python backtest.py --portfolio-path portfolios/eurusd-test.py --from-date 2022-01-01 --restore-ticks true
```

## Analyzing Results

The backtest outputs a report with key metrics:

- **Return %**: Total portfolio return
- **Max Drawdown %**: Largest peak-to-trough decline
- **Sharpe Ratio**: Risk-adjusted return measure
- **Win Rate**: Percentage of profitable trades
- **Number of trades**: Total executed trades

Results are sent to Horizon Router API and logged to console.

## Troubleshooting

| Error | Solution |
|-------|----------|
| No enabled assets found | Check portfolio has at least one asset with `enabled=True` |
| Authentication errors | Run authentication setup first |
| Date parsing errors | Use `YYYY-MM-DD` format strictly |
