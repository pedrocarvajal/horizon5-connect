# SQX Strategy Verification

Checklist for auditing that an implementation matches the original SQX EA.

## Audit Procedure

### Step 1: Read Source Files

```bash
cat strategies/[Name]/source/*.txt
grep -E "LongEntrySignal =|ShortEntrySignal =" strategies/[Name]/source/*.mq5
```

### Step 2: Extract Key Values

**From .txt:**

- Indicator periods (SMAPeriod1, ADXPeriod1, etc.)
- SL/PT coefficients (StopLossCoef1/2, ProfitTargetCoef1/2)
- Trading options (MaxTradesPerDay, Min SL, etc.)

**From .mq5:**

- Signal function calls with exact parameters
- Shift values (look for `+ 1` patterns)
- Expression strings with internal shifts

### Step 3: Trace Each Signal

For each signal condition:

1. Find .txt description
2. Find .mq5 function call
3. Note all parameters
4. Calculate effective shift

## Verification Checklist

### 1. Parameters Match

| Parameter         | Where to Check (.txt) | What to Verify          |
| ----------------- | --------------------- | ----------------------- |
| Indicator periods | Strategy Parameters   | Match values            |
| SL coefficients   | Strategy Parameters   | Coef1=Long, Coef2=Short |
| PT coefficients   | Strategy Parameters   | Coef1=Long, Coef2=Short |
| Min SL/PT         | Trading options       | In pips                 |
| Max trades/day    | Trading options       | Integer value           |

### 2. Signal Functions

| Function               | Parameters to Verify                                 |
| ---------------------- | ---------------------------------------------------- |
| sqIsRising             | indicator, bars, allowSame, shift, buffer            |
| sqIsFalling            | indicator/expression, bars, allowSame, shift, buffer |
| sqIsLowerCount         | left, right, bars, notStrict, shift                  |
| sqIsHigherCount        | left, right, bars, notStrict, shift                  |
| indyCrossesAbove/Below | left, right, shift                                   |

### 3. Shift Values

| Signal Type     | .mq5 Shift  | With Expression +1 | Final |
| --------------- | ----------- | ------------------ | ----- |
| `Indicator[1]`  | `1 + 1 = 2` | N/A                | 2     |
| `Expression[1]` | `1`         | Yes (+1 internal)  | 2     |
| `Indicator[0]`  | `0 + 1 = 1` | N/A                | 1     |

### 4. Buffer Mechanics

- [ ] No `ArraySetAsSeries` in buffer loading
- [ ] Buffer[0] = oldest value
- [ ] Buffer[n-1] = newest value
- [ ] IsRising: checks old→new increasing
- [ ] IsFalling: checks old→new decreasing

### 5. SL/PT Calculations

| Check          | Long             | Short            |
| -------------- | ---------------- | ---------------- |
| SL coefficient | Coef1            | Coef2            |
| PT coefficient | Coef1            | Coef2            |
| SL direction   | price - distance | price + distance |
| PT direction   | price + distance | price - distance |
| Min applied    | After ATR calc   | After ATR calc   |

### 6. Time Exits

| Feature    | .mq5 Variable                    |
| ---------- | -------------------------------- |
| End of Day | `ExitAtEndOfDay`, `EODExitTime`  |
| Friday     | `ExitOnFriday`, `FridayExitTime` |

## Common Issues

### ArraySetAsSeries Bug

**Symptom**: Trades opposite direction or no trades.
**Cause**: `ArraySetAsSeries(values, true)` reverses order.
**Check**: Search for `ArraySetAsSeries` in code.

### Shift Off-by-One

**Symptom**: Enters early or late.
**Cause**: Not adding +1 for expression internal shift.
**Check**: Trace expression through `sqGetExpressionByIdentification`.

### Missing atLeastOnce

**Symptom**: Signal triggers when values are equal.
**Cause**: Not requiring actual change.
**Check**: Loop must set `atLeastOnce = true` when change detected.

## Report Template

```markdown
## Strategy Review: [Name]

### Summary

- **Status**: PASS / ISSUES FOUND
- **Critical Issues**: N
- **Warnings**: N

### Parameters

| Parameter    | SQX | Implementation | Match |
| ------------ | --- | -------------- | ----- |
| SMA Period   | 196 | ?              | ?     |
| SL Coef Long | 3.0 | ?              | ?     |

### Signals

| Signal      | SQX Shift | Impl Shift | Match |
| ----------- | --------- | ---------- | ----- |
| Long Entry  | 2         | ?          | ?     |
| Short Entry | 2         | ?          | ?     |

### Buffer Mechanics

- [ ] No ArraySetAsSeries
- [ ] Buffer order correct

### Issues Found

1. **Issue**: [Description]
   - **Location**: [file:line]
   - **Fix**: [Suggestion]
```
