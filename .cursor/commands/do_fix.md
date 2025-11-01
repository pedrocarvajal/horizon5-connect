# Fix Command

Your mission is to fix one or more errors provided by the user.
To do this efficiently, follow a task list using the `todo_write` tool to track progress.

## Important

- Use `todo_write` tool to create/update tasks
- Use `read_file`, `codebase_search`, and `grep` tools to analyze code
- Maintain existing code structure and architecture
- Apply clean code practices and clean architecture principles

## Tasks

Execute each task step-by-step (in that specific order). For each task, follow this workflow:

1. Analyze the context thoroughly
2. Implement necessary changes
3. Perform self-critical analysis
4. Request user to test the fix (unless user explicitly provided testing instructions)
5. Only after user confirmation or test execution, move to the next task

### Task 1: Error Context Analysis

- Identify all files involved in the error
- Trace the complete event flow related to the error section
- Analyze not just the isolated code fragment, but the entire context
- Document the root cause of the error

### Task 2: Root Cause Identification

- List all possible root causes
- Prioritize causes by likelihood
- Select the most probable root cause
- Validate the hypothesis through code analysis

### Task 3: Fix Implementation

- Apply the fix maintaining existing code structure and architecture
- Follow clean code best practices
- Ensure the solution is organized and maintainable
- Preserve clean architecture principles

### Task 4: Testing Request

- Request user to test the implemented fix
- If user provided explicit testing instructions, execute them
- Wait for user confirmation that the error is resolved
- Confirm no side effects or new issues were introduced

## Do not

- Do not modify unrelated code
- Do not change code structure unnecessarily
- Do not introduce new dependencies without justification
- Do not skip the analysis phase and jump to implementation
