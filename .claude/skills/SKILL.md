---
name: horizon5-skills
description: Skills index for Horizon5 portfolio trading framework
user-invocable: false
---

# Horizon5 Skills Index

Knowledge base for working with the Horizon5 algorithmic trading portfolio.

## Available Skills

| Skill  | Description                      | When to Use                         |
| ------ | -------------------------------- | ----------------------------------- |
| `sqx/` | StrategyQuant X EA file analysis | Working with SQX-generated EA files |

## Skill Domains

### SQX (StrategyQuant X)

Skills for analyzing and extracting logic from StrategyQuant X generated Expert Advisors and converting them to Horizon5 Python strategies.

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

## Usage

These skills are referenced by agents via @.claude/skills/. The `/create-strategy-from` command orchestrates agents that use `sqx/` skills.
