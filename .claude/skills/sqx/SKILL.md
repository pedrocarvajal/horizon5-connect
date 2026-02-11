---
name: sqx
description: Skills for analyzing StrategyQuant X generated Expert Advisors
version: 1.1.0
user-invocable: false
---

# StrategyQuant X (SQX) Analysis Skills

Knowledge base for extracting trading logic from SQX generated EA files.

## File Types

| Type        | Extension | Purpose              | Priority    |
| ----------- | --------- | -------------------- | ----------- |
| Pseudo Code | `.txt`    | Human-readable logic | **Primary** |
| Full Source | `.mq5`    | Complete MQL5 code   | Secondary   |

**Rule**: Always use `.txt` first. Only search `.mq5` for implementation details.

## Sub-skills

| Skill                 | What to Extract       | Where to Search             |
| --------------------- | --------------------- | --------------------------- |
| `metadata.md`         | Symbol, TF, dates     | Lines 1-9 header            |
| `parameters.md`       | Periods, coefficients | Strategy Parameters section |
| `trading-options.md`  | Time exits, limits    | Trading options section     |
| `entry-signals.md`    | Entry conditions      | Trading signals section     |
| `exit-signals.md`     | Exit conditions       | Exit signals section        |
| `sl-pt.md`            | SL/PT formulas        | Entry rules section         |
| `signal-functions.md` | sqIsRising, etc.      | Signal function calls       |
| `buffer-mechanics.md` | Shift calculations    | loadIndicatorValues         |
| `verification.md`     | Audit checklist       | Compare source vs impl      |

## Quick Reference

### .txt File Structure

```text
Lines 1-9     → Header (symbol, TF, dates)
Lines 12-25   → Strategy Parameters
Lines 25-40   → Trading options
Lines 40-55   → Trading signals (entry conditions)
Lines 55-90   → Entry rules (SL/PT formulas)
Lines 90-110  → Exit rules
```

### Key Search Patterns (.mq5)

```bash
grep "#define.*_1" file.mq5              # Indicator handles
grep -E "LongEntrySignal =|ShortEntrySignal =" file.mq5  # Signal logic
grep -E "sqGetSLLevel|sqGetPTLevel" file.mq5  # SL/PT calculations
grep "sqGetExpressionByIdentification" file.mq5  # Expression shifts
```

## Decision Flow

```text
What do you need?
    │
    ├─> Symbol/timeframe  → metadata.md
    ├─> Indicator periods → parameters.md
    ├─> Time exits        → trading-options.md
    ├─> Entry conditions  → entry-signals.md
    ├─> Exit conditions   → exit-signals.md
    ├─> SL/PT formulas    → sl-pt.md
    ├─> Signal functions  → signal-functions.md
    ├─> Shift mechanics   → buffer-mechanics.md
    └─> Audit checklist   → verification.md
```

## Critical Knowledge

### Shift Rules

| .txt Pattern    | .mq5 Shift        | Final Shift |
| --------------- | ----------------- | ----------- |
| `Indicator[1]`  | `1 + 1`           | 2           |
| `Expression[1]` | `1` + internal +1 | 2           |
| `Indicator[0]`  | `0 + 1`           | 1           |

### Buffer Order

```text
buffer[0] = OLDEST value
buffer[n-1] = NEWEST value
```

**No ArraySetAsSeries** - SQX does not use it.
