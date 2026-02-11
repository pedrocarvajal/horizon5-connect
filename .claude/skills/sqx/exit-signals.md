# Extracting Exit Signals from SQX Files

How to find and understand exit signal conditions.

## .txt File (Primary)

### Where to Search

Search for exit signal definitions (after Trading signals section).

```bash
grep -E "LongExitSignal =|ShortExitSignal =" file.txt
```

### What to Look For

**Most common case:**

```text
LongExitSignal = false;
ShortExitSignal = false;
```

**Signal-based exit:**

```text
LongExitSignal = (SMA(Main chart,20)[1] crosses below SMA(Main chart,50)[1]);
```

## Exit Types

| Type         | Pattern         | Meaning                     |
| ------------ | --------------- | --------------------------- |
| No signal    | `= false`       | Exit via SL/PT or time only |
| Signal-based | `= (condition)` | Exit when condition met     |
| Time-based   | Trading options | End of day, Friday          |

## Exit Rules Section

### Where to Search

```bash
grep -A 10 "Long exit" file.txt
grep -A 10 "Short exit" file.txt
```

### What to Look For

```text
if ((LongExitSignal
   and Not LongEntrySignal)
   and (MarketPosition("Any", MagicNumber, "") is Long))
{
    Close all positions for Symbol = Any and Magic Number = MagicNumber;
}
```

**Exit logic**: Signal + Not entering + Has position = Close.

## .mq5 File (Confirmation)

### Where to Search

```bash
grep -E "LongExitSignal|ShortExitSignal|sqCloseAll" file.mq5
```

### Position Check Functions

| Function                       | Meaning            |
| ------------------------------ | ------------------ |
| `sqMarketPositionIsLong(...)`  | Has long position  |
| `sqMarketPositionIsShort(...)` | Has short position |

### Close Functions

| Function                       | Action             |
| ------------------------------ | ------------------ |
| `sqCloseAllPositions(...)`     | Close all matching |
| `sqClosePositionAtMarket(...)` | Close specific     |

## Time-Based Exits

### Where to Search

See trading-options.md for:

- `Exit at End Of Day`
- `Exit On Friday`

### Quick Reference

| .txt                               | .mq5                             |
| ---------------------------------- | -------------------------------- |
| `Exit at End Of Day = true (2300)` | `ExitAtEndOfDay`, `EODExitTime`  |
| `Exit On Friday = true (2300)`     | `ExitOnFriday`, `FridayExitTime` |

## Special Attention

- **`= false`**: Most common - no signal exit
- **Time exits**: Check Trading options section
- **Trailing stops**: Search for `sqTrailingStop` in .mq5
- **Break-even**: Search for `sqBreakEvenStop` in .mq5
