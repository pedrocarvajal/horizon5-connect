---
description: Review code following clean-code guidelines
argument-hint: [file-or-folder]
---

# Code Review Command

Review code following clean-code guidelines. Analyzes files systematically and applies corrections.

## Arguments

- `$ARGUMENTS` - Path to file or folder to review

## Workflow

### Step 1: Identify Target

Determine if `$ARGUMENTS` is a file or folder:

- **If folder**: List all `.py` files and inform user: "This folder contains N files. I will analyze each one systematically, one at a time." Process each file separately following this workflow from the beginning.
- **If file**: Proceed to Step 2.

### Step 2: Understand Context

Before reviewing, gather context about the file:

1. Read the file content
2. Identify what type of file it is (class, interface, service, strategy, asset, portfolio, test, enum, model, helper)
3. Search for usages: find who imports or uses this file
4. Understand the data flow and action flow
5. Summarize: "This file is a [type] that [purpose]. It is used by [files/modules]."

### Step 3: Select Documentation Guide

Based on file type, select the appropriate documentation:

| File Type | Documentation Path                  |
| --------- | ----------------------------------- |
| Class     | `docs/clean-code/classes.md`        |
| Interface | `docs/clean-code/interfaces.md`     |
| Service   | `docs/clean-code/services.md`       |
| Strategy  | `docs/clean-code/strategies.md`     |
| Asset     | `docs/clean-code/assets.md`         |
| Portfolio | `docs/clean-code/portfolios.md`     |
| Test      | `docs/clean-code/tests.md`          |
| Enum      | `docs/clean-code/commons/enums.md`  |
| Model     | `docs/clean-code/commons/models.md` |

**If no specific documentation exists for the file type:**

- Ask user: "No specific documentation found for [type]. Should I review it as a class? Or should we create documentation for [type] first?"
- If user chooses to review as class, use `docs/clean-code/classes.md`
- If documentation is needed, notify user to create it before proceeding

### Step 4: Read Documentation and References

1. Read the selected documentation guide
2. Identify internal references (links to other docs like `variables.md`, `models.md`, etc.)
3. Read all referenced documentation

**Before proceeding, inform user:**

"I will review this file using:

- Primary guide: [documentation path]
- Referenced guides: [list of referenced docs]"

Use `AskUserQuestion` tool to ask if user wants to proceed with the review and apply corrections.

### Step 5: Execute Review

After user confirms:

1. **Analyze**: Compare file against all guidelines from documentation
2. **Identify issues**: List all deviations from guidelines
3. **Apply corrections**: Fix issues immediately using Edit tool

Issues to check (based on documentation):

- Hierarchy/structure order
- Naming conventions
- Formatting (multi-line parameters, imports order, etc.)
- Type hints
- Anti-patterns
- Missing or incorrect implementations

### Step 6: Validate Changes

After applying corrections, run validation:

1. Run linter checks: `./scripts/make/run-linter-checks.sh --file [filepath]`
2. Run tests: `./scripts/make/run-tests.sh`, but before you should ask

If any check fails, fix the issues before proceeding to Step 7.

### Step 7: Report Results

After all validations pass, report to user:

```
## Review Complete: [filename]

### Changes Applied:
- [List each modification with line reference]

### Guidelines Used:
- [List documentation files read]

### Validation:
- Linter checks: Passed
- Tests: Passed

### Notes:
- [Any observations or recommendations]
```

## Example Execution

```
User: /do-coding-review services/orderbook/__init__.py

Agent:
1. Reading file: services/orderbook/__init__.py
2. Context: This is a Service class (OrderbookService) that manages order lifecycle. Used by BacktestService and ProductionService.
3. Documentation: I will use docs/clean-code/services.md with references to classes.md and variables.md
4. [Asks user confirmation via AskUserQuestion]
5. [Applies corrections]
6. [Runs linter checks and tests]
7. [Reports changes]
```
