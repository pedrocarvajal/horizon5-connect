# Extracting Metadata from SQX Files

How to quickly find symbol, timeframe, and strategy identification.

## .txt File (Primary)

### Where to Search

**Lines 1-9** - Header block.

### What to Look For

```bash
grep -E "Backtested on|Generated at|Strategy" file.txt | head -5
```

### Pattern Breakdown

```text
Line 2:  // Pseudo Source Code of Strategy 0.283
                                         └──┬──┘
                                       Strategy ID

Line 7:  //   Backtested on XAUUSD_darwinex_local / H1, 2021.01.01 - 2026.01.01
                            └───────┬───────────┘   └┬┘ └─────────┬──────────┘
                              Symbol (raw)          TF       Date range
```

### Symbol Cleanup

Remove broker suffix:

- `XAUUSD_darwinex_local` → `XAUUSD`
- `EURUSD_broker` → `EURUSD`

## .mq5 File (Confirmation)

### Where to Search

**Lines 1-10** - Same header format.

```bash
head -10 file.mq5
```

### Additional Info

| Lines | Pattern                      | Info                       |
| ----- | ---------------------------- | -------------------------- |
| 14-55 | `#property tester_indicator` | Required custom indicators |
| 83    | `CustomComment`              | EA identifier              |
| 85    | `MagicNumber`                | Default magic              |

## Special Attention

- **Multiple TFs**: Watch for comma-separated like `H1,D1`
- **Build version**: `Build 143` affects code structure
- **Custom indicators**: List of `#property tester_indicator` shows dependencies
