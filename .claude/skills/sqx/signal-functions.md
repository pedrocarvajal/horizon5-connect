# SQX Signal Function Reference

How to find and understand signal detection functions in SQX files.

## Function Overview

| Function           | .txt Pattern                    | Purpose              |
| ------------------ | ------------------------------- | -------------------- |
| `sqIsRising`       | `is rising for N bars`          | Values increasing    |
| `sqIsFalling`      | `is falling for N bars`         | Values decreasing    |
| `sqIsLowerCount`   | `is lower than ... for N bars`  | A < B consecutively  |
| `sqIsHigherCount`  | `is higher than ... for N bars` | A > B consecutively  |
| `indyCrossesAbove` | `crosses above`                 | Was below, now above |
| `indyCrossesBelow` | `crosses below`                 | Was above, now below |

## sqIsRising / sqIsFalling

### Where to Search (.mq5)

```bash
grep -E "sqIsRising|sqIsFalling" file.mq5
```

### What to Look For

```cpp
sqIsRising(SMA_1, 4, true, 1 + 1, 0)
sqIsFalling("sqMonthly(NULL,0,\"High\", 1)", 3, false, 0 + 1, 0)
```

### Parameter Breakdown

| Position | Name      | Example                   | Meaning                        |
| -------- | --------- | ------------------------- | ------------------------------ |
| 1        | indicator | `SMA_1` or `"expression"` | Handle or expression string    |
| 2        | bars      | `4`                       | Number of bars to check        |
| 3        | allowSame | `true`                    | Allow equal consecutive values |
| 4        | shift     | `1 + 1`                   | Starting bar (**note the +1**) |
| 5        | buffer    | `0`                       | Buffer index                   |

### Buffer Logic (Critical)

```text
buffer[0] = oldest value
buffer[n-1] = newest value

Rising: buffer[0] <= buffer[1] <= ... <= buffer[n-1]
Falling: buffer[0] >= buffer[1] >= ... >= buffer[n-1]
```

### atLeastOnce Requirement

Both functions require at least ONE actual change:

- Rising: at least one `buffer[i] > buffer[i-1]`
- Falling: at least one `buffer[i] < buffer[i-1]`

## sqIsLowerCount / sqIsHigherCount

### Where to Search (.mq5)

```bash
grep -E "sqIsLowerCount|sqIsHigherCount" file.mq5
```

### What to Look For

```cpp
sqIsLowerCount("sqMonthly(NULL,0,\"Close\", 1)", "sqDaily(NULL,0,\"Open\", 1)", 7, true, 1)
```

### Parameter Breakdown

| Position | Name      | Example            | Meaning            |
| -------- | --------- | ------------------ | ------------------ |
| 1        | left      | `"sqMonthly(...)"` | Left expression    |
| 2        | right     | `"sqDaily(...)"`   | Right expression   |
| 3        | bars      | `7`                | Consecutive bars   |
| 4        | notStrict | `true`             | Allow equal values |
| 5        | shift     | `1`                | Base shift         |

### Loop Logic

```cpp
for (int i = 0; i < bars; i++) {
    leftValue = getExpression(left, shift + i);
    rightValue = getExpression(right, shift + i);
    // Check left < right (or > for Higher)
}
```

## indyCrossesAbove / indyCrossesBelow

### Where to Search (.mq5)

```bash
grep -E "indyCrossesAbove|indyCrossesBelow" file.mq5
```

### What to Look For

```cpp
indyCrossesAbove("sqDaily(NULL,0,\"Open\", 1)", "sqWeekly(NULL,0,\"High\", 1)", shift)
```

### Cross Logic

```text
CrossesAbove: previous(A) <= previous(B) AND current(A) > current(B)
CrossesBelow: previous(A) >= previous(B) AND current(A) < current(B)
```

## Expression Strings

### Where to Search

```bash
grep "sqGetExpressionByIdentification" file.mq5
```

### What to Look For

```cpp
double sqGetExpressionByIdentification(string id, int shift) {
    if (id == "sqMonthly(NULL,0,\"Close\", 1)") {
        return sqMonthly(NULL, 0, "Close", shift + 1);  // NOTE: +1 added
    }
    if (id == "sqDaily(NULL,0,\"Open\", 1)") {
        return sqDaily(NULL, 0, "Open", shift + 1);     // NOTE: +1 added
    }
}
```

### Critical: Internal +1 Shift

Expression strings have internal shift embedded:

- `"sqMonthly(NULL,0,\"High\", 1)"` → adds +1 to shift
- When shift=1 is passed, actual shift becomes 2

## ADX Buffer Indexes

### Special Attention

ADX uses different buffers:

| Buffer | Meaning       |
| ------ | ------------- |
| `0`    | Main ADX line |
| `1`    | +DI line      |
| `2`    | -DI line      |

Example: `sqIsRising(ADX_1, 4, true, 2, 2)` uses -DI buffer.

## Shift Summary

| .txt Pattern                     | .mq5 Call       | Effective Shift    |
| -------------------------------- | --------------- | ------------------ |
| `Indicator[1]`                   | `shift = 1 + 1` | 2                  |
| `Expression[1]` with +1 internal | `shift = 1`     | 2 (1 + internal 1) |
| `Indicator[0]`                   | `shift = 0 + 1` | 1                  |
