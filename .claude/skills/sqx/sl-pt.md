# Extracting Stop Loss / Profit Target from SQX Files

How to find SL/PT calculation methods and parameters.

## .txt File (Primary)

### Where to Search

Inside entry rules (Long entry / Short entry blocks).

```bash
grep -A 20 "Long entry" file.txt | grep -E "Stop Loss|Profit target"
grep -A 20 "Short entry" file.txt | grep -E "Stop Loss|Profit target"
```

### What to Look For

```text
Stop Loss = StopLossCoef1 * ATR(14);
Profit target = ProfitTargetCoef1 * ATR(14);
```

### SL/PT Methods

| Method         | Pattern            | Example                   |
| -------------- | ------------------ | ------------------------- |
| ATR Multiplier | `Coef * ATR(N)`    | `StopLossCoef1 * ATR(14)` |
| Fixed Pips     | `N pips`           | `50 pips`                 |
| Indicator      | `Indicator[shift]` | `ATR(14)[1]`              |
| Price Level    | `Low[1]`           | Use indicator as level    |

### Direction Coefficients

| Direction | SL              | PT                  |
| --------- | --------------- | ------------------- |
| Long      | `StopLossCoef1` | `ProfitTargetCoef1` |
| Short     | `StopLossCoef2` | `ProfitTargetCoef2` |

### Min/Max Limits

From Trading Options:

```text
Min SL: 15, Max SL: 0, Min PT: 15, Max PT: 0;
```

- Units: pips/ticks
- `0` = unlimited

## .mq5 File (Confirmation)

### Where to Search

Search for SL/PT functions (around line 383-431).

```bash
grep -E "sqGetSLLevel|sqGetPTLevel" file.mq5
```

### What to Look For

```cpp
// Long
sl = sqGetSLLevel("Current", ORDER_TYPE_BUY, openPrice, 2, StopLossCoef1 * sqGetIndicatorValue(ATR_1, 1));
pt = sqGetPTLevel("Current", ORDER_TYPE_BUY, openPrice, 2, ProfitTargetCoef1 * sqGetIndicatorValue(ATR_1, 1));

// Short
sl = sqGetSLLevel("Current", ORDER_TYPE_SELL, openPrice, 2, StopLossCoef2 * sqGetIndicatorValue(ATR_1, 1));
pt = sqGetPTLevel("Current", ORDER_TYPE_SELL, openPrice, 2, ProfitTargetCoef2 * sqGetIndicatorValue(ATR_1, 1));
```

### Value Type Parameter

The 4th parameter indicates calculation method:

| Code | Meaning              |
| ---- | -------------------- |
| `1`  | Pips                 |
| `2`  | Price Distance (ATR) |
| `3`  | Absolute Level       |

**Most common**: `2` (ATR-based).

### Min/Max Variables

```bash
grep -E "MinimumSL|MinimumPT|MaximumSL|MaximumPT" file.mq5
```

```cpp
input int MinimumSL = 15;   // in pips
input int MinimumPT = 15;   // in pips
input int MaximumSL = 0;    // 0 = unlimited
input int MaximumPT = 0;    // 0 = unlimited
```

## Quick Extraction Table

| What                | Where (.txt)        | Where (.mq5)                    |
| ------------------- | ------------------- | ------------------------------- |
| Long SL multiplier  | Strategy Parameters | `StopLossCoef1` input           |
| Long PT multiplier  | Strategy Parameters | `ProfitTargetCoef1` input       |
| Short SL multiplier | Strategy Parameters | `StopLossCoef2` input           |
| Short PT multiplier | Strategy Parameters | `ProfitTargetCoef2` input       |
| ATR period          | In formula `ATR(N)` | `sqGetIndicatorValue(ATR_1, 1)` |
| Min SL              | Trading options     | `MinimumSL` input               |
| Min PT              | Trading options     | `MinimumPT` input               |

## Special Attention

- **Coef1 vs Coef2**: Direction-specific (1=Long, 2=Short)
- **ATR period**: Usually hardcoded to 14
- **valueType=2**: Means ATR value already in price units
- **Min/Max applied after**: First calculate ATR, then apply limits
