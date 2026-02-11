# Extracting Entry Signals from SQX Files

How to find and understand entry signal conditions.

## .txt File (Primary)

### Where to Search

Section `Trading signals (On Bar Open)` (after line 40).

```bash
grep -A 10 "Trading signals" file.txt
```

### What to Look For

```text
LongEntrySignal = (SMA(Main chart,SMAPeriod1, PRICE_CLOSE)[1] is rising for 4 bars);

ShortEntrySignal = (((CloseMonthly(Main chart)[1] is lower than OpenDaily(Main chart)[1] for 7 bars)
   and (HighMonthly(Main chart)[1] is falling for 3 bars))
   and (ADX(Main chart,ADXPeriod1).-DI[1] is rising for 4 bars));
```

### Signal Syntax Reference

| Syntax                          | Meaning                     |
| ------------------------------- | --------------------------- |
| `[1]`                           | Previous closed bar (shift) |
| `is rising for N bars`          | Values increasing           |
| `is falling for N bars`         | Values decreasing           |
| `is lower than ... for N bars`  | A < B consecutively         |
| `is higher than ... for N bars` | A > B consecutively         |
| `crosses above`                 | Was below, now above        |
| `crosses below`                 | Was above, now below        |
| `and` / `or`                    | Logical operators           |

### Multi-Timeframe Indicators

| Pattern                           | Timeframe    |
| --------------------------------- | ------------ |
| `Close(chart)[1]`                 | Main TF      |
| `CloseDaily(chart)[1]`            | D1           |
| `CloseWeekly(chart)[1]`           | W1           |
| `CloseMonthly(chart)[1]`          | MN1          |
| `HighMonthly`, `LowMonthly`, etc. | Same pattern |

## .mq5 File (Confirmation)

### Where to Search

Search for signal assignments (around line 360).

```bash
grep -E "LongEntrySignal =|ShortEntrySignal =" file.mq5
```

### What to Look For

```cpp
LongEntrySignal = (sqIsRising(SMA_1, 4, true, 1 + 1, 0));

ShortEntrySignal = (((sqIsLowerCount("sqMonthly(NULL,0,\"Close\", 1)","sqDaily(NULL,0,\"Open\", 1)",7,true,1))
  &&   (sqIsFalling("sqMonthly(NULL,0,\"High\", 1)", 3, false, 0 + 1, 0)))
  &&   (sqIsRising(ADX_1, 4, true, 1 + 1, 2)));
```

### Signal Functions Mapping

| .txt Pattern              | .mq5 Function                                   | Parameters         |
| ------------------------- | ----------------------------------------------- | ------------------ |
| `is rising for N bars`    | `sqIsRising(ind, N, allow, shift, buf)`         | See below          |
| `is falling for N bars`   | `sqIsFalling(ind, N, allow, shift, buf)`        | See below          |
| `is lower than ... for N` | `sqIsLowerCount(left, right, N, strict, shift)` | See below          |
| `crosses above`           | `indyCrossesAbove(...)`                         | Two values + shift |

### Function Parameters

**sqIsRising / sqIsFalling:**

- `ind`: Indicator handle (e.g., `SMA_1`) or expression string
- `N`: Number of bars
- `allow`: Allow same values (true/false)
- `shift`: Starting bar (note: `1 + 1 = 2`)
- `buf`: Buffer index

**sqIsLowerCount / sqIsHigherCount:**

- `left/right`: Expression strings (e.g., `"sqMonthly(NULL,0,\"Close\", 1)"`)
- `N`: Consecutive bars
- `strict`: Allow equal (true = not strict)
- `shift`: Base shift

## Entry Rules Section

### Where to Search

```bash
grep -A 15 "Long entry" file.txt
grep -A 15 "Short entry" file.txt
```

### What to Look For

```text
if LongEntrySignal
{
    Open Long order at Market;
    Stop Loss = StopLossCoef1 * ATR(14);
    Profit target = ProfitTargetCoef1 * ATR(14);
}
```

### Short Priority Pattern

```text
if (ShortEntrySignal
   and Not LongEntrySignal)
```

**Meaning**: Short only if Long is false.

## Special Attention

- **Shift `[1]`**: Always use previous bar (closed data)
- **Expression strings**: Have internal +1 shift (see buffer-mechanics.md)
- **Buffer index**: ADX uses `2` for -DI, `1` for +DI
- **Short priority**: Usually requires `Not LongEntrySignal`
