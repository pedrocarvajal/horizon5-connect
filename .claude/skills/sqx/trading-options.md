# Extracting Trading Options from SQX Files

How to find time exits, trade limits, and SL/PT constraints.

## .txt File (Primary)

### Where to Search

Section `Trading options logic` (lines 25-40).

```bash
grep -A 15 "Trading options logic" file.txt
```

### What to Look For

| Pattern                            | Meaning        | Example       |
| ---------------------------------- | -------------- | ------------- |
| `Exit at End Of Day = true (HHMM)` | Daily close    | `true (2300)` |
| `Exit On Friday = true (HHMM)`     | Friday close   | `true (2300)` |
| `MaxTradesPerDay = N`              | Daily limit    | `1`           |
| `Min SL: N, Max SL: N`             | SL constraints | `15, 0`       |
| `Min PT: N, Max PT: N`             | PT constraints | `15, 0`       |

### Time Format

```text
(2300) → 23:00
(0038) → 00:38
```

### Min/Max Rules

- `0` = unlimited
- Values are in pips/ticks

## .mq5 File (Confirmation)

### Where to Search

Trading Options variables section (lines 117-150).

```bash
grep -E "Exit|MaxTrades|Minimum|Maximum" file.mq5 | head -15
```

### What to Look For

```cpp
input bool ExitAtEndOfDay = true;
input string EODExitTime = "23:00";

input bool ExitOnFriday = true;
input string FridayExitTime = "23:00";

input int MaxTradesPerDay = 1;

input int MinimumSL = 15;
input int MinimumPT = 15;
input int MaximumSL = 0;
input int MaximumPT = 0;
```

## Quick Reference

| .txt Pattern                       | .mq5 Variable                    |
| ---------------------------------- | -------------------------------- |
| `Exit at End Of Day = true (2300)` | `ExitAtEndOfDay`, `EODExitTime`  |
| `Exit On Friday = true (2300)`     | `ExitOnFriday`, `FridayExitTime` |
| `MaxTradesPerDay = 1`              | `MaxTradesPerDay`                |
| `Min SL: 15`                       | `MinimumSL`                      |
| `Min PT: 15`                       | `MinimumPT`                      |

## Special Attention

- **Time format difference**: .txt uses `(HHMM)`, .mq5 uses `"HH:MM"`
- **0 = unlimited**: For Max SL/PT
- **Units**: Min/Max in pips, not price
