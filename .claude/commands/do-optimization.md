---
description: Optimize strategy settings through iterative backtesting
argument-hint: <asset> <strategy>
---

# Strategy Optimization Command

Optimize strategy configuration settings through systematic backtesting iterations. Analyzes trading logic, adjusts parameters, and validates robustness using in-sample/out-of-sample methodology.

## Arguments

- `$ARGUMENTS` - Required. Format: `<asset> <strategy>`
  - `<asset>`: Asset folder name (e.g., `btcusdt`)
  - `<strategy>`: Strategy class name (e.g., `DonchianBreakoutStrategy`, `RSIBollingerBreakoutStrategy`)

**Examples:**

- `/do-optimization btcusdt DonchianBreakoutStrategy`
- `/do-optimization btcusdt TurtleTradingStrategy`

## Constraints

- **Maximum Drawdown**: 30%
- **In-Sample Period**: 3 years minimum
- **Out-of-Sample**: Remaining data for robustness validation
- **Backtest Reference**: See `.claude/docs/how-to-run-backtest.md` for command usage and analysis

## Workflow

### Step 1: Parse Arguments

Extract asset and strategy from `$ARGUMENTS`:

1. Split arguments by space
2. Validate asset exists at `assets/<asset>/__init__.py`
3. Validate strategy class exists in asset file
4. If invalid, inform user and abort

### Step 2: Create Tracking File

Create `TRACKING-<ASSET>.md` at project root with structure:

```markdown
# Optimization: <ASSET> - <STRATEGY>

## Objective

Find optimal configuration for <STRATEGY> on <ASSET> with:

- Maximum drawdown: 30%
- Target: Highest return within drawdown constraint

## Strategy Understanding

[To be filled after analysis]

## Parameter Ranges

| Parameter | Min | Max | Step | Current |
| --------- | --- | --- | ---- | ------- |

[To be filled after analysis]

## Iteration Log

| #   | Date | Parameters Changed | Return % | Drawdown % | Profit Factor | Notes |
| --- | ---- | ------------------ | -------- | ---------- | ------------- | ----- |

[Iterations recorded here]

## Best Configuration

[To be updated when found]

## Out-of-Sample Validation

[Final validation results]
```

### Step 3: Understand Strategy

Before optimizing, deeply understand the strategy:

1. **Read strategy source**: `strategies/<strategy_folder>/__init__.py`
2. **Analyze trading logic**:
   - Entry conditions (when does it buy/sell?)
   - Exit conditions (stop loss, take profit, signals)
   - Indicators used and their parameters
   - Position sizing logic
3. **Identify configurable settings** in the asset's strategy initialization
4. **Document in TRACKING file**:
   - How the strategy works algorithmically
   - Market conditions where it performs well
   - Market conditions where it struggles
   - How each parameter affects behavior

**Inform user:**
"Strategy Analysis Complete:

- Logic: [summary]
- Key parameters: [list with current values]
- Expected behavior: [when it wins/loses]"

### Step 4: Create Test Portfolio

Create portfolio at `portfolios/<asset>-test.py`:

```python
"""Test portfolio for <asset> optimization."""

from vendor.services.portfolio import PortfolioService


class Portfolio(PortfolioService):
    """Single-asset test portfolio for optimization."""

    def __init__(self) -> None:
        super().__init__(
            name="<Asset> Test",
            assets=["assets.<asset>"],
            allocation=100_000,
        )
```

### Step 5: Establish Baseline

Run initial backtest with current settings (see `.claude/docs/how-to-run-backtest.md`):

1. Execute backtest with 3-year in-sample period
2. Record baseline metrics in storage/TRACKING-{(symbol)-(strategy)}.md file:
   - Return %
   - Max Drawdown %
   - Profit Factor
   - Win Rate
   - Number of trades
3. Review generated report at `storage/backtests/{backtest_id}/`

### Step 6: Iterative Optimization

For each iteration:

1. **Select parameter to adjust** based on:
   - Previous results analysis
   - Trading logic understanding
   - Parameter sensitivity

2. **Modify settings** in `assets/<asset>/__init__.py`

3. **Run backtest** and capture results

4. **Record in TRACKING file**:
   - Parameters changed
   - All metrics
   - Observations

5. **Analyze results**:
   - Did drawdown decrease?
   - Did return improve?
   - Is the change statistically significant?

6. **Decide next step**:
   - Continue adjusting same parameter
   - Move to different parameter
   - Revert if results worsened

**Guidelines:**

- Change ONE parameter at a time for clear causation
- If drawdown exceeds 30%, revert immediately
- Keep iterations focused and documented
- After 5-10 iterations, reassess approach

### Step 7: Out-of-Sample Validation

Once optimal in-sample configuration found:

1. Run backtest on out-of-sample period (most recent data)
2. Compare metrics to in-sample results
3. Check for overfitting indicators:
   - Significant performance degradation
   - Different behavior patterns
   - Inconsistent win rates

### Step 8: Report Results

Final report in TRACKING file and to user:

```
## Optimization Complete: <ASSET> - <STRATEGY>

### Final Configuration:
[Parameter values]

### In-Sample Results (YYYY-MM-DD to YYYY-MM-DD):
- Return: X%
- Max Drawdown: X%
- Profit Factor: X

### Out-of-Sample Results (YYYY-MM-DD to YYYY-MM-DD):
- Return: X%
- Max Drawdown: X%
- Profit Factor: X

### Robustness Assessment:
[Analysis of IS vs OOS consistency]

### Recommendations:
[Next steps or concerns]
```

## Important Notes

- **Context Preservation**: TRACKING file serves as memory between conversation compactions
- **One strategy at a time**: Complete optimization before moving to next strategy
- **Avoid overfitting**: Prioritize robustness over maximum in-sample returns
- **Document reasoning**: Explain why each parameter change was made
