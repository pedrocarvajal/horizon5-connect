---
description: Create a Horizon5 strategy from StrategyQuant X EA files
argument-hint: <files>
---

# Create Strategy From EA Files

Extract trading strategy logic from StrategyQuant X EA files and implement as a Horizon5 Python strategy class.

## Role

You are the strategy creation orchestrator. You launch the sqx-creator agent to convert StrategyQuant X EA files into Horizon5 Python strategy classes.

## Objective

**Goal**: Convert EA source files into a fully implemented, tested, and backtested Horizon5 strategy.

**Acceptance Criteria**:

- [ ] sqx-creator completed all phases (discovery, analysis, planning, execution, verification, backtest)
- [ ] Backtest ran successfully with sensible results

## Input Files

$ARGUMENTS

## Workflow

```text
/create-strategy-from <files>
         │
         ▼
┌─────────────────────────┐
│   sqx-creator agent     │  ← Analyzes EA, gathers user input,
│   (Phases 1-6)          │    implements Python strategy
└───────────┬─────────────┘
            │
            ▼
     [Backtest & Summary]
```

## Execution Protocol

### Step 1: Launch Creator Agent

Use the Task tool with `subagent_type: "sqx-creator"` to launch the creator agent:

```
Create a Horizon5 strategy from these EA files: $ARGUMENTS

After implementation, return:
1. Strategy name and folder path
2. Source files location
3. Asset file modified
4. Backtest results summary
```

### Step 2: Final Summary

After agent completes, provide:

- Files created
- Files modified
- Strategy configuration details
- Backtest results (return %, trades, win rate, drawdown)

## Agent Configuration

| Agent       | Purpose                                                              | User Interaction             |
| ----------- | -------------------------------------------------------------------- | ---------------------------- |
| sqx-creator | Analyzes EA, gathers preferences, implements strategy, runs backtest | Yes (timeframe, asset, name) |
