# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Horizon Connect is a quantitative trading framework for backtesting and deploying trading strategies across multiple exchanges. Currently implements Binance gateway integration with plans for multi-asset, multi-strategy portfolio management. The framework uses a multiprocessing architecture with separate processes for strategy execution and command handling.

## Development Commands

All commands use `uv` as the package manager.

**Testing:**
- `make run-tests` - Run all tests (unit, integration, e2e)
- `make run-tests-unit` - Run unit tests only
- `make run-tests-integration` - Run integration tests only
- `make run-tests-e2e` - Run end-to-end tests only

Single test: `uv run python -m unittest tests.unit.test_filename -v`

**Linting:**
- `make run-linter-checks` - Run Ruff and Pyright

**Running:**
- Backtest: `uv run python backtest.py --portfolio-path portfolios.low-risk --start-date YYYY-MM-DD --end-date YYYY-MM-DD`
- Production: `uv run python production.py --portfolio-path portfolios.low-risk`

## Code Quality Standards

**Type Checking:**
- Strict mypy configuration (`pyproject.toml:70-82`)
- All functions require type annotations (enforced by Ruff ANN rules)
- Use `typing.Optional[X]` not `X | None` (UP045 ignored)
- Use `typing.List/Dict` not `list/dict` (UP006, UP035 ignored)

**Linting:**
- Line length: 120 characters
- Ruff enforces: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear, comprehensions, datetimez, pytest-style, simplify, use-pathlib, pylint
- Test files exempt from type annotations and some pylint rules (`pyproject.toml:61-62`)

## Architecture

**Event-Driven Multiprocessing:**
- Main processes: `BacktestService`/`ProductionService` + `CommandsService`
- Communication via `multiprocessing.Queue` for commands and events
- See `backtest.py:43-80` and `production.py:27-57`

**Core Abstractions:**

1. **Portfolio** (`interfaces/portfolio.py`):
   - Container for multiple assets
   - Implements `PortfolioInterface` with `_assets: List[Type[AssetInterface]]`
   - Example: `portfolios/low-risk.py`

2. **Asset** (`interfaces/asset.py`):
   - Represents a trading instrument (e.g., BTCUSDT)
   - Contains multiple strategies
   - Lifecycle hooks: `setup()`, `on_tick()`, `on_transaction()`, `on_end()`
   - Example: `assets/btcusdt/__init__.py`

3. **Strategy** (`interfaces/strategy.py`):
   - Trading logic implementation
   - Lifecycle hooks: `setup()`, `on_tick()`, `on_new_minute()`, `on_new_hour()`, `on_new_day()`, `on_transaction()`, `on_end()`
   - Access to candle services and indicators
   - Example: `strategies/ema5_breakout/__init__.py`

4. **Indicator** (`interfaces/indicator.py`):
   - Technical analysis calculations
   - Hooks: `on_tick()`, `on_end()`
   - Properties: `key`, `values`
   - Available: `indicators/ma`, `indicators/volatility`, `indicators/price_velocity`, `indicators/price_acceleration`

5. **Gateway** (`interfaces/gateway.py`, `services/gateway/__init__.py`):
   - Facade pattern for exchange integrations
   - Configured in `configs/gateways.py`
   - Implementations: `services/gateway/gateways/binance` (active), `ib`, `kucoin` (stubs)
   - Handles: orders, positions, account info, symbol info, trading fees

**Key Services:**

- `AnalyticService` - Financial metrics calculation during backtests
- `BacktestService` - Historical simulation engine
- `ProductionService` - Live trading execution
- `CandleService` - Builds candlesticks from ticks, manages indicators
- `TicksService` - Downloads/manages historical tick data
- `CommandsService` - Processes commands from queue (KILL, EXECUTE)

**Data Models:**

- `TickModel` (`models/tick.py`) - Price data point with timestamp, bid/ask
- `OrderModel` (`models/order.py`) - Order lifecycle with side, type, status, volume, prices, commission, trades
- `SnapshotModel` (`models/snapshot.py`) - Analytics snapshot at a point in time

## Environment Configuration

Required variables in `.env`:
- `BINANCE_TESTNET`: "True"/"False" for sandbox mode (default: "True")
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`: Production credentials
- `BINANCE_TESTNET_API_KEY`, `BINANCE_TESTNET_API_SECRET`: Testnet credentials

Gateway configuration logic in `configs/gateways.py:7-14`.

## Helpers

Generic reusable helpers in `helpers/` (see `.cursor/rules/context.mdc:6-24`):

**Parsing:**
- `parse_int()`, `parse_float()`, `parse_optional_float()`, `parse_percentage()`, `parse_timestamp_ms()`

**Utilities:**
- `get_env()` - Environment variable retrieval
- `get_slug()` - URL-friendly slug generation
- `get_progress_between_dates()` - Progress percentage calculation
- `get_duration()` - Duration formatting
- `get_portfolio_by_path()` - Load portfolio from Python file path

Domain-specific helpers live in `services/*/helpers/`.

## Enums

All in `enums/` directory:
- `BacktestStatus`, `Command`, `HttpStatus`
- `OrderSide` (BUY, SELL), `OrderStatus`, `OrderType` (MARKET, LIMIT, STOP_LOSS, etc.)
- `OrderEvent`, `SnapshotEvent`
- `Timeframe` (includes `to_seconds()` method)

## Testing Structure

- `tests/unit/` - Unit tests for helpers and utilities
- `tests/integration/` - Gateway and service integration tests
- `tests/e2e/` - End-to-end backtest validation
- Integration test fixtures: `tests/integration/binance/CASES.md`

## Patterns

**Creating a new strategy:**
1. Inherit from `StrategyService`
2. Implement lifecycle methods (`on_tick`, `on_new_hour`, etc.)
3. Initialize `CandleService` with indicators in `__init__`
4. Register in asset's `_strategies` list

**Creating a new asset:**
1. Inherit from `AssetService`
2. Set `_symbol` and `_gateway_name`
3. Initialize strategies in `__init__`
4. Add to portfolio's `_assets` list

**Creating a new portfolio:**
1. Inherit from `PortfolioService`
2. Set `_id`
3. Implement `setup_assets()` with asset classes

## Notes

- Python 3.11+ required
- Uses Pydantic v2 for data models
- Polars (not pandas) for data processing
- Rich for terminal output formatting
- Current roadmap in README.md shows alpha 0.1.0 in progress
