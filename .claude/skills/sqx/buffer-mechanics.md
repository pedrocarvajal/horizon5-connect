# SQX Buffer and Shift Mechanics

Critical knowledge for understanding how SQX loads indicator values.

## CopyBuffer Behavior

### MQL5 Standard

```cpp
CopyBuffer(handle, buffer_num, start_pos, count, buffer[])
```

### Buffer Order (WITHOUT ArraySetAsSeries)

```text
CopyBuffer(handle, 0, shift=2, count=4, buffer)

Copies bars: 2, 3, 4, 5
Buffer contents:
  buffer[0] = value at bar 5 (OLDEST)
  buffer[1] = value at bar 4
  buffer[2] = value at bar 3
  buffer[3] = value at bar 2 (NEWEST)
```

**Rule**: buffer[0] = OLDEST, buffer[n-1] = NEWEST.

## loadIndicatorValues Functions

### Where to Search (.mq5)

```bash
grep -A 15 "bool loadIndicatorValues" file.mq5
```

### Indicator Version

```cpp
bool loadIndicatorValues(double& buffer[], uchar indyIndex, int bars, int shift, ...) {
    CopyBuffer(indicatorHandles[indyIndex], bufferIndex, shift, bars, buffer);
    // NO ArraySetAsSeries - buffer[0] = oldest
}
```

### Expression Version

```cpp
bool loadIndicatorValues(double& buffer[], string expression, int bars, int shift, ...) {
    for (int a = 0; a < bars; a++) {
        int curShift = shift + bars - 1 - a;
        buffer[a] = sqGetExpressionByIdentification(expression, curShift);
    }
}
```

### Expression Shift Calculation

With `shift=1` and `bars=3`:

| Loop a | curShift Formula | curShift | Buffer Index |
| ------ | ---------------- | -------- | ------------ |
| 0      | 1 + 3 - 1 - 0    | 3        | buffer[0]    |
| 1      | 1 + 3 - 1 - 1    | 2        | buffer[1]    |
| 2      | 1 + 3 - 1 - 2    | 1        | buffer[2]    |

Result: `buffer = [bar3, bar2, bar1]` where bar3 is oldest.

## Expression Internal Shift

### Where to Search (.mq5)

```bash
grep -A 10 "sqGetExpressionByIdentification" file.mq5
```

### What to Look For

```cpp
double sqGetExpressionByIdentification(string id, int shift) {
    if (id == "sqMonthly(NULL,0,\"High\", 1)") {
        return sqMonthly(NULL, 0, "High", shift + 1);  // Adds +1
    }
}
```

### Shift Trace Example

Original call:

```cpp
sqIsFalling("sqMonthly(NULL,0,\"High\", 1)", 3, false, 0 + 1, 0)
```

1. Function receives: `shift=1`, `bars=3`
2. `loadIndicatorValues` calculates curShift: 3, 2, 1
3. `sqGetExpressionByIdentification` adds +1: 4, 3, 2
4. Final buffer: `[bar4, bar3, bar2]`

## Shift Reference Table

| .txt Pattern    | .mq5 shift  | With Expression +1 | Final Bars |
| --------------- | ----------- | ------------------ | ---------- |
| `Indicator[1]`  | `1 + 1 = 2` | N/A                | 2+         |
| `Expression[1]` | `0 + 1 = 1` | +1 internal        | 2+         |
| `Indicator[0]`  | `0 + 1 = 1` | N/A                | 1+         |

## Common Traps

### Trap 1: ArraySetAsSeries

**Wrong behavior**: If `ArraySetAsSeries(values, true)` is used:

- buffer[0] becomes NEWEST instead of OLDEST
- Rising/Falling logic inverts

**How to check**: Search for `ArraySetAsSeries` in buffer loading code.

### Trap 2: Missing Expression +1

**Wrong**: Using shift=1 for expression with internal +1
**Right**: Account for internal shift, use shift=2

### Trap 3: Wrong Rising/Falling Direction

With correct order (buffer[0]=oldest):

- Rising: buffer[i] >= buffer[i-1] moving forward
- Falling: buffer[i] <= buffer[i-1] moving forward

## Verification Checklist

- [ ] No `ArraySetAsSeries` in loadIndicatorValues
- [ ] Expression internal shifts identified
- [ ] Buffer[0] = oldest, buffer[n-1] = newest
- [ ] IsRising checks increasing from old to new
- [ ] IsFalling checks decreasing from old to new
