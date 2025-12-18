---
description: Create a new strategy using previous contex
argument-hint: <extra_indications>
---

Use these instructions when you already have context about a strategy that was being discussed or researched and now needs to be developed.
Your goal is to act like an experienced developer: work incrementally, validate each step, and never generate all the code at once.

## PHASE 1: Framework exploration and learning

Before writing any code, you must understand how the framework works:

1. **Study a reference strategy**: Read `strategies/meb_faber_timing/__init__.py` to understand:
   - The base structure of a strategy (inheritance from `StrategyService`)
   - Lifecycle methods available for override:
     - `on_tick(tick: TickModel)` - Called on every market tick
     - `on_new_hour()` - Called when transitioning to a new hour
     - `on_new_day()` - Called when transitioning to a new day
     - `on_new_week()` - Called when transitioning to a new week
     - `on_new_month()` - Called when transitioning to a new month
     - `on_transaction(order: OrderModel)` - Called when an order status changes
     - `on_end()` - Called at the end of strategy execution
   - How indicators and `CandleService` are used
   - How to open/close orders with the `orderbook`

2. **Study available indicators**: Review `vendor/indicators/` for built-in indicators:
   - `ma` - Moving Average (SMA/EMA)
   - `rsi` - Relative Strength Index
   - `atr` - Average True Range
   - `adx` - Average Directional Index
   - `donchian_channel` - Donchian Channel (high/low breakout)
   - `rsi_bollinger_bands` - RSI with Bollinger Bands
   - `volatility` - Volatility indicator
   - `price_velocity` - Price velocity measurement
   - `price_acceleration` - Price acceleration measurement

   If a required indicator doesn't exist, you can create a new one following the existing indicator patterns.

3. **Study a reference asset**: Read `assets/xauusd/__init__.py` to understand:
   - How strategies are linked to an asset
   - The `settings` configuration for each strategy
   - The allocation system

4. **Study the portfolio**: Read `portfolios/low-risk.py` to understand how assets are linked to the portfolio.

5. **Document your findings**: Before continuing, briefly describe what you understood about the framework and how you plan to apply it to the new strategy.

## PHASE 2: Infrastructure preparation

1. **Check if the asset exists**: Look in `assets/` directory for the target asset.

   **If the asset already exists:**
   - Verify the asset configuration is correct for your strategy
   - Add your new strategy to the existing asset's strategies list
   - Proceed to step 3

   **If the asset does NOT exist:**
   - Create the new asset folder `assets/<asset_name>/__init__.py` following the structure of `assets/xauusd/__init__.py`
   - Link the asset in `portfolios/low-risk.py`
   - **STOP HERE**: Historical data must be downloaded before continuing. Inform the user:
     ```
     The asset <asset_name> has been created but requires historical data download.
     Please run the data download process for this asset and let me know when it's complete.
     The download may take considerable time depending on the data range needed.
     ```
   - **Wait for user confirmation** that data download is complete before proceeding

2. **Link to portfolio**: If not already linked, ensure the asset is linked in `portfolios/low-risk.py`.

3. **Create the strategy folder**: Create `strategies/<strategy_name>/__init__.py` with the minimal structure (just the empty class inheriting from `StrategyService`).

4. **Validate**: Run a short backtest to confirm there are no import errors:
   ```bash
   uv run python backtest.py --portfolio-path portfolios/low-risk.py --from-date 2024-01-01
   ```

   **Note**: If this is a new asset and the backtest fails due to missing data, remind the user that historical data must be downloaded first.

## PHASE 3: Incremental development with validation

Implement the strategy step by step. After each step, add temporary logs and run a backtest to validate:

### Step 3.1: Initial configuration
- Implement `__init__` with settings and `CandleService` with required indicators
- Add logs to confirm indicators initialize correctly
- **Validate**: Run backtest and verify logs

### Step 3.2: Data processing
- Implement the appropriate lifecycle methods based on your strategy needs:
  - `on_tick` for tick-by-tick strategies
  - `on_new_hour` for hourly evaluation
  - `on_new_day` for daily evaluation
  - `on_new_week` for weekly evaluation
  - `on_new_month` for monthly evaluation
- Add logs showing price values and indicators on each evaluation
- **Validate**: Run backtest and verify values make sense (not NaN, within expected ranges)

### Step 3.3: Entry logic
- Implement entry conditions and the method to open positions
- Add detailed logs: current price, indicator value, generated signal, calculated volume
- **Validate**: Run backtest and verify:
  - Do entries occur when expected according to strategy rules?
  - Are volume and price correct?
  - Do the numbers add up mathematically?

### Step 3.4: Exit logic
- Implement exit conditions (TP, SL, or close signals)
- Add logs for each close: reason, entry price, exit price, profit
- **Validate**: Run backtest and verify:
  - Do exits occur according to the rules?
  - Is the profit calculation correct?

### Step 3.5: State management
- Implement `on_transaction` to handle order state
- Verify state updates correctly (position open/closed)
- **Validate**: Run complete 1-year backtest

## PHASE 4: Complete validation

1. **1-year backtest**: Run with sufficient history:
   ```bash
   uv run python backtest.py --portfolio-path portfolios/low-risk.py --from-date 2024-01-01
   ```

2. **Results analysis**: Review logs and metrics:
   - Is the number of trades reasonable for the strategy?
   - Is the drawdown within expectations?
   - Does the performance make sense?

3. **Identify anomalies**: If something doesn't add up (strange numbers, unexpected behavior), investigate before continuing.

## PHASE 5: Extended backtest and cleanup

1. **Full backtest**: When confident, run the complete backtest:
   ```bash
   uv run python backtest.py --portfolio-path portfolios/low-risk.py --from-date 2019-01-01
   ```

2. **Log cleanup**: Remove redundant debug logs and keep only critical ones needed for production/backtest monitoring:
   - Position open/close logs
   - Signal evaluation logs (monthly or according to strategy frequency)
   - Error or anomaly condition logs

## IMPORTANT RULES

- **Never generate all code at once**: Work incrementally
- **Always validate before moving forward**: A backtest after each significant change
- **Question the numbers**: If something doesn't make mathematical sense, investigate
- **Logs are your main debug tool**: Use them generously during development
- **Document your reasoning**: Explain what you're validating at each step

$ARGUMENTS
