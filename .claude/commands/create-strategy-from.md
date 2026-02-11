---
description: Create a Horizon5 strategy from StrategyQuant X EA files
argument-hint: <files>
---

# Create Strategy From EA Files

Extract trading strategy logic from StrategyQuant X EA files and implement as Horizon5 strategy class.

## Role

You are the strategy creation orchestrator. You launch the sqx-creator agent to convert StrategyQuant X EA files into Horizon5 strategy classes.

## Objective

**Goal**: Convert EA source files into a fully implemented and deployed Horizon5 strategy.

**Acceptance Criteria**:

- [ ] sqx-creator completed all phases (discovery, analysis, planning, execution)
- [ ] Deployment successful

## Input Files

$ARGUMENTS

## Workflow

```text
/create-strategy-from <files>
         │
         ▼
┌─────────────────────────┐
│   sqx-creator agent     │  ← Analyzes EA, gathers user input,
│   (Phases 1-4)          │    implements strategy
└───────────┬─────────────┘
            │
            ▼
     [Deploy & Summary]
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
```

### Step 2: Deploy

Once the creator finishes:

- Run `make deploy`
- Provide final summary

### Step 3: Final Summary

After successful deployment, provide:

- Files created
- Files modified
- Strategy configuration details
- Deployment status

## Agent Configuration

| Agent       | Purpose                                               | User Interaction             |
| ----------- | ----------------------------------------------------- | ---------------------------- |
| sqx-creator | Analyzes EA, gathers preferences, implements strategy | Yes (timeframe, asset, name) |
