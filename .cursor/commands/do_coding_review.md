# Coding Review Command

Your mission is to perform a coding review on code provided by the user. To do this efficiently, follow a task list using the `todo_write` tool to track progress.

## Important

- Use `todo_write` tool to create/update tasks
- Use `read_file` and `list_dir` tools to read files

## Language

- All code to be reviewed is Python code. Follow Python best practices and conventions.

## Tasks

Execute each task step-by-step (in that specific order). For each task, follow this workflow:

1. Read the guideline document
2. Apply all necessary changes to the code
3. Re-read the guideline document and perform self-critical analysis
4. Verify that all rules were followed and changes were applied correctly
5. Only after verification is complete, move to the next task

### Task 1: Variable Naming Conventions

- Read `docs/clean-code/variable-name-convention.md`
- Apply all guidelines to the code
- Re-read `docs/clean-code/variable-name-convention.md`
- Perform self-critical analysis: verify each naming convention was applied (classes, variables, functions, enums, structs, files)
- Confirm all exceptions were respected

### Task 2: No Comments Policy

- Read `docs/clean-code/no-comments.md`
- Apply all guidelines to the code
- Re-read `docs/clean-code/no-comments.md`
- Perform self-critical analysis: verify all unnecessary comments were removed or code was refactored
- Confirm only acceptable comments remain (mathematical formulas with references)

### Task 3: Type Annotations

- Read `docs/clean-code/typings.md`
- Apply all guidelines to the code
- Re-read `docs/clean-code/typings.md`
- Perform self-critical analysis: verify instance vs class types, optional/union syntax, collection types, property return types
- Confirm all type hints follow the project standard (using Optional, Union, List, Dict from typing module)

### Task 4: Class Organization

- Read `docs/clean-code/class-organization.md`
- Apply all guidelines to the code, including:
  - **MUST ADD visual section separators** for each section (PROPERTIES, CONSTRUCTOR, PUBLIC METHODS, PRIVATE METHODS, GETTERS)
  - Reorganize methods according to the recommended section order
  - Verify access modifiers (underscore prefix for private members)
- Re-read `docs/clean-code/class-organization.md`
- Perform self-critical analysis:
  - ✓ Confirm section separators were ADDED to the code (lines with dashes and section names)
  - ✓ Verify section order is correct (constants → properties → constructor → public methods → private methods → getters)
  - ✓ Confirm access modifiers are properly assigned
  - ✓ Confirm each method is in the correct section

### Task 5: Code Smells Analysis

- Read `docs/clean-code/code-smells.md`
- Analyze the code without modifying it
- Generate a numbered report listing all code smells found
- For each smell, specify: smell type, location (line number), description, and recommendation

## Do not

- Do not read all the ".md" file in the first iteration, select the task, read the file, follow the guidelines, fix, and them next task.
- Do not create new functions
- Do not alter function return values or signatures
- Do not modify code structure or logic that could cause future errors
- Do not refactor working code unless there's a clear bug or violation
