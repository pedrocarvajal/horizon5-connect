---
name: horizon5-skills
description: Skills index for Horizon5 portfolio trading framework
version: 1.0.0
user-invocable: false
---

# Horizon5 Skills Index

Knowledge base for working with the Horizon5 algorithmic trading portfolio.

## Available Skills

| Skill          | Description                      | When to Use                         |
| -------------- | -------------------------------- | ----------------------------------- |
| `sqx/`         | StrategyQuant X EA file analysis | Working with SQX-generated EA files |
| `formatting/`  | MQL5 code formatting rules       | Writing or reviewing any MQL5 code  |

## Skill Domains

### SQX (StrategyQuant X)

Skills for analyzing and extracting logic from StrategyQuant X generated Expert Advisors.

```text
sqx/
├── SKILL.md              # Index and overview
├── metadata.md           # Extract header and metadata
├── parameters.md         # Read strategy parameters
├── trading-options.md    # Trading options (exits, limits)
├── entry-signals.md      # Entry signal conditions
├── exit-signals.md       # Exit signal conditions
├── sl-pt.md              # Stop Loss / Profit Target rules
├── signal-functions.md   # Signal function implementations
├── buffer-mechanics.md   # CopyBuffer and shift mechanics
└── verification.md       # Implementation verification
```

### Formatting

Code formatting and organization rules derived from the canonical reference files (`Horizon.mq5`, `SEOrderPersistence.mqh`, `Soweto.mqh`).

```text
formatting/
└── SKILL.md              # Complete formatting rules
```

## Usage

These skills are referenced by agents via `@.claude/skills/`. The `/create-strategy-from` command orchestrates agents that use `sqx/` skills. The `formatting/` skill applies to all MQL5 code writing and review.
