# Extracting Parameters from SQX Files

How to find all configurable values: periods, coefficients, multipliers.

## .txt File (Primary)

### Where to Search

Section `Strategy Parameters` (lines 12-25 typically).

```bash
grep -A 20 "Strategy Parameters" file.txt
```

### What to Look For

| Pattern                 | Type             | Example                       |
| ----------------------- | ---------------- | ----------------------------- |
| `int XXXPeriodN = N`    | Indicator period | `SMAPeriod1 = 196`            |
| `double XXXCoefN = N.N` | Multiplier       | `StopLossCoef1 = 3`           |
| `Main chart = ...`      | TF reference     | `Current Symbol / Current TF` |

### Naming Convention

```text
[Prefix][Number] = value

Coef1 / 1 → Long parameters
Coef2 / 2 → Short parameters
```

Examples:

- `StopLossCoef1` → Long SL multiplier
- `StopLossCoef2` → Short SL multiplier
- `SMAPeriod1` → SMA period

## .mq5 File (Confirmation)

### Where to Search

Input declarations (lines 80-100).

```bash
grep -E "^input (int|double)" file.mq5 | head -20
```

### What to Look For

```cpp
input int SMAPeriod1 = 196;           //SMAPeriod1
input double ProfitTargetCoef1 = 4.6; //ProfitTargetCoef1
input double StopLossCoef1 = 3;       //StopLossCoef1
```

## Indicator Definitions

### Where to Search

`#define` statements (lines 220-230).

```bash
grep "#define.*_1" file.mq5
```

### What to Look For

```cpp
#define SMA_1 0     //iMA(NULL,0, SMAPeriod1, 0, MODE_SMA, PRICE_CLOSE)
#define ADX_1 1     //iCustom(NULL,0, "SqADX", ADXPeriod1)
#define ATR_1 2     //iCustom(NULL, 0, "SqATR", 14)
```

**Comment = actual indicator call with parameters.**

### Indicator Initialization

```bash
grep "indicatorHandles\[" file.mq5
```

**Note**: `indicatorHandles[X] = 255` means unused placeholder.

## Special Attention

- **Coef1 vs Coef2**: Always direction-specific
- **ATR(14)**: Often hardcoded even when other periods vary
- **Period values**: May be variables or hardcoded
