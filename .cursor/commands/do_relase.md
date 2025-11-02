# Release Command

Your mission is to create a new release for the project following semantic versioning. To do this efficiently, follow a task list using the `todo_write` tool to track progress.

## Important

- Use `todo_write` tool to create/update tasks
- Use `read_file`, `grep`, and `run_terminal_cmd` tools as needed
- Follow semantic versioning: MAJOR.MINOR.PATCH
- All release files must be created in `docs/releases/` directory

## Release File Naming Convention

Release files must follow this pattern:

```
v{MAJOR}.{MINOR}.{PATCH}.md
```

Examples:

- `v0.1.0.md`
- `v0.2.0.md`
- `v1.0.0.md`
- `v1.2.3.md`

## Release File Format

Each release file must follow this structure:

```markdown
# Release v{VERSION}

Release Date: {YYYY-MM-DD}

Release Type: {Major | Minor | Patch}

## Commit Range

- **From:** {COMMIT_HASH} ({YYYY-MM-DD}) - {First commit message}
- **To:** {COMMIT_HASH} ({YYYY-MM-DD}) - {Last commit message}
- **Total Commits:** {N}

## Summary

{Brief summary of the release - 2-3 sentences describing the main theme or goal of this version}

## Breaking Changes

{List of breaking changes that require user action or migration}

- {Component/Module}: {Description of breaking change and migration path}

{If no breaking changes: "None"}

## New Features

{List of new features added in this release}

- {Feature Name}: {Description of what was added and why it's valuable}

{If no new features: "None"}

## Enhancements

{List of improvements to existing features}

- {Component/Module}: {Description of improvement}

{If no enhancements: "None"}

## Bug Fixes

{List of bugs fixed in this release}

- {Component/Module}: {Description of bug fixed}

{If no bug fixes: "None"}

## Dependencies

{List of dependency changes}

- Added: {new_package>=version}
- Updated: {package: old_version -> new_version}
- Removed: {removed_package}

{If no dependency changes: "None"}

## Technical Details

{Optional section for technical implementation details, architecture changes, or performance improvements}

- {Technical detail or metric}

## Migration Guide

{If breaking changes exist, provide step-by-step migration guide}

### From v{OLD_VERSION} to v{NEW_VERSION}

1. {Migration step}
2. {Migration step}

{If no migration needed: "No migration required"}

## Contributors

{List of contributors for this release}

- @{username}

## Notes

{Additional notes, known issues, or future plans}
```

## Git Release Title Format

Git release titles must follow this pattern:

```
v{MAJOR}.{MINOR}.{PATCH} - {Short descriptive title}
```

Examples:

- `v0.1.0 - Initial Release`
- `v0.2.0 - Enhanced Analytics Service`
- `v1.0.0 - Production Ready`
- `v1.2.1 - Hotfix: Gateway Connection`

## Semantic Versioning Rules

### MAJOR version (X.0.0)

Increment when you make incompatible API changes:

- Breaking changes to public interfaces
- Removal of deprecated features
- Major architecture changes

### MINOR version (0.X.0)

Increment when you add functionality in a backward-compatible manner:

- New features
- New indicators or strategies
- New services or modules
- Significant enhancements

### PATCH version (0.0.X)

Increment when you make backward-compatible bug fixes:

- Bug fixes
- Performance improvements
- Documentation updates
- Minor refactoring

## GitHub Best Practices

### Pre-release Versions

According to [GitHub documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository):

- **Version 0.x.x releases should be marked as pre-release**

  - These indicate the software is not yet production-ready
  - Use `--prerelease` flag with `gh release create`
  - Example: `v0.1.0`, `v0.2.0-alpha`, `v0.5.9-beta.3`

- **Version 1.0.0+ are stable releases**
  - Indicate production-ready software
  - Do not use `--prerelease` flag
  - Example: `v1.0.0`, `v2.3.4`

### Tag Naming Convention

- Always prefix version names with the letter `v`
- Follow semantic versioning: `v{MAJOR}.{MINOR}.{PATCH}`
- For pre-release versions: `v{MAJOR}.{MINOR}.{PATCH}-{identifier}`
  - Examples: `v0.2.0-alpha`, `v5.9-beta.3`, `v1.0.0-rc.1`

### Latest Release

- Use `--latest` flag to explicitly set a release as the latest
- If not set, GitHub determines latest by:
  - Higher semantic version
  - Creation date
- Recommended to always use `--latest` for clarity

### Release Notes

- Always include comprehensive release notes using `--notes-file`
- Release notes should be in Markdown format
- Include all sections: Summary, Breaking Changes, New Features, Bug Fixes, etc.
- @mention contributors to automatically generate Contributors section

## Tasks

Execute each task step-by-step (in that specific order). For each task, follow this workflow:

1. Execute the task requirements
2. Verify the output is correct
3. Update the task status
4. Only after verification is complete, move to the next task

### Task 1: Read Current Version

- Read `pyproject.toml` file
- Extract current version from `[project]` section under `version` key
- Store the current version (format: MAJOR.MINOR.PATCH)
- Display current version to user

### Task 2: Locate Last Release File

- Based on current version, construct the release filename: `v{current_version}.md`
- Check if file exists in `docs/releases/` directory
- If file exists:
  - Read the file content
  - Note the release date and changes documented
- If file does NOT exist:
  - Check if ANY release files exist in `docs/releases/` directory
  - If NO release files exist at all:
    - This is the FIRST release ever for the project
    - Should create v0.1.0 as the initial release
    - Analyze ALL commits from project start
  - If other release files exist but not for current version:
    - Find the most recent release file
    - Use that as the starting point

### Task 3: Get Git Commit History

- If last release file exists:
  - Extract the release date from the file
  - Get all commits since that date: `git log --since="{YYYY-MM-DD}" --oneline --no-merges`
  - Get the full commit history for analysis: `git log --since="{date}" --no-merges --pretty=format:"%h - %s (%an, %ar)"`
- If no last release file (FIRST RELEASE):
  - Get ALL commits from project start: `git log --oneline --no-merges`
  - Get the full commit history: `git log --no-merges --pretty=format:"%h - %s (%an, %ar)"`
  - These commits will be used to create the initial v0.1.0 release
- Store commit list for analysis

### Task 4: Analyze Changes

Categorize commits into:

Breaking Changes:

- Look for: "BREAKING", "breaking change", major refactors, API changes, removed features
- Analyze commit messages and code changes for backward incompatibility

New Features:

- Look for: "feat:", "add", "new", "implement", "create"
- Identify new modules, services, indicators, strategies

Enhancements:

- Look for: "enhance", "improve", "optimize", "refactor", "update"
- Identify improvements to existing functionality

Bug Fixes:

- Look for: "fix:", "bug", "hotfix", "patch", "resolve"
- Identify resolved issues

Dependencies:

- Check `git diff v{old_version}..HEAD -- pyproject.toml` if previous version exists
- Look for changes in dependencies section

Technical Details:

- Performance improvements
- Architecture changes
- Internal refactoring

### Task 5: Determine Version Bump

SPECIAL CASE - If this is the FIRST release (no previous release files exist):

- Ignore current version in pyproject.toml
- Set new version to: `0.1.0`
- Skip to Task 6

For subsequent releases, based on the analysis:

- If Breaking Changes exist → MAJOR bump (unless currently 0.x.x, then MINOR bump)
- If New Features exist (no breaking changes) → MINOR bump
- If Only Bug Fixes/Enhancements (no breaking changes, no new features) → PATCH bump

Calculate new version:

- Current: `{MAJOR}.{MINOR}.{PATCH}`
- New: `{NEW_MAJOR}.{NEW_MINOR}.{NEW_PATCH}`

Display proposed version bump to user and wait for confirmation.

### Task 6: Create Release File

- Create new file: `docs/releases/v{NEW_VERSION}.md`
- Use the release file format template (see above)
- Fill in all sections based on the analysis from Task 4:
  - Set release date to current date (YYYY-MM-DD format)
  - Set release type (Major/Minor/Patch)
  - **Add Commit Range section:**
    - Get first commit: `git log --no-merges --reverse --pretty=format:"%h - %ad - %s" --date=short | head -1`
    - Get last commit (before release): `git log --no-merges --pretty=format:"%h - %ad - %s" --date=short | grep -v "chore: release" | head -1`
    - Get total commits: `git log --oneline --no-merges | grep -v "chore: release" | wc -l`
    - Format: From {hash} ({date}) - {message} to {hash} ({date}) - {message}
  - Write concise summary (2-3 sentences)
  - List breaking changes with migration paths
  - List new features with descriptions
  - List enhancements
  - List bug fixes
  - List dependency changes
  - Add technical details if relevant
  - Create migration guide if breaking changes exist
  - Add notes if needed
- Save the file
- Display the file path to user

### Task 7: Update pyproject.toml

- Read `pyproject.toml`
- Locate the `version = "{CURRENT_VERSION}"` line in `[project]` section
- Replace with `version = "{NEW_VERSION}"`
- Save the file
- Verify the change by reading the file again

### Task 8: User Confirmation

Before executing git operations, display a summary for user review:

- Version bump: {OLD_VERSION} → {NEW_VERSION}
- Release type: {Major | Minor | Patch}
- Release file: docs/releases/v{NEW_VERSION}.md
- Number of changes: {N} breaking, {N} features, {N} enhancements, {N} fixes
- Git operations to execute:
  - Commit release files
  - Create tag v{NEW_VERSION}
  - Push to origin/main
  - Create GitHub release

Ask user: "Do you want to proceed with publishing this release? (yes/no)"

Wait for user confirmation before proceeding to Task 9.

If user responds "no" or requests changes:

- Stop the process
- Allow user to manually edit release file or make adjustments
- User can restart from this task when ready

If user responds "yes":

- Proceed to Task 9

### Task 9: Git Operations

Execute git commands using GitHub CLI for full integration:

1. Stage changes:

   ```bash
   git add docs/releases/v{NEW_VERSION}.md pyproject.toml
   ```

2. Commit changes:

   ```bash
   git commit -m "chore: release v{NEW_VERSION}"
   ```

3. Push commit:

   ```bash
   git push origin main
   ```

4. Create GitHub release with tag (using GitHub CLI):

   Determine if this is a pre-release:

   - If version is `0.x.x` → Add `--prerelease` flag (pre-production software)
   - If version is `1.0.0+` → Release as stable (no flag needed)

   For pre-release (v0.x.x):

   ```bash
   gh release create v{NEW_VERSION} \
     --title "v{NEW_VERSION} - {Short descriptive title}" \
     --notes-file docs/releases/v{NEW_VERSION}.md \
     --prerelease \
     --latest
   ```

   For stable release (v1.0.0+):

   ```bash
   gh release create v{NEW_VERSION} \
     --title "v{NEW_VERSION} - {Short descriptive title}" \
     --notes-file docs/releases/v{NEW_VERSION}.md \
     --latest
   ```

   **Note:** The `gh release create` command automatically:

   - Creates the git tag (no need for separate `git tag` command)
   - Pushes the tag to remote
   - Creates the GitHub release with full description
   - Uses `--latest` to mark as the latest release (recommended)

   If `gh` CLI is not installed or not authenticated:

   First, try to authenticate:

   ```bash
   gh auth login
   ```

   If authentication fails or gh is not available, display manual instructions:

   - Go to: https://github.com/{user}/{repo}/releases/new
   - Tag: v{NEW_VERSION}
   - Title: v{NEW_VERSION} - {Short descriptive title}
   - Description: Copy content from `docs/releases/v{NEW_VERSION}.md`
   - Check "Set as the latest release"
   - If version is 0.x.x, check "This is a pre-release"
   - Click "Publish release"

### Task 10: Verification

- Verify git tag was created: `git tag -l v{NEW_VERSION}`
- Verify remote has the tag: `git ls-remote --tags origin v{NEW_VERSION}`
- Display release URL: `https://github.com/{user}/{repo}/releases/tag/v{NEW_VERSION}`
- Confirm all files were updated correctly
- List summary of all changes made:
  - Version bumped from {OLD} to {NEW}
  - Release file created at docs/releases/v{NEW_VERSION}.md
  - Git tag created and pushed
  - GitHub release created (or manual instructions provided)

## Do Not

- Do not skip version numbers
- Do not create releases without analyzing commits
- Do not push to git without user confirmation
- Do not modify any source code during release process
- Do not delete or modify existing release files
- Do not create duplicate version tags
- Do not proceed if there are uncommitted changes (except release files)

## Pre-flight Checks

Before starting the release process, verify:

1. Working directory is clean (no uncommitted changes except what will be committed for release)
2. Current branch is `main` or default branch
3. Local branch is up to date with remote: `git pull origin main`
4. All tests are passing (if applicable)
5. User has confirmed they want to proceed with the release

## Special Case: First Release

When creating the very first release for a project that has NEVER had a release before:

1. Version Number:

   - MUST be v0.1.0 (ignore any version in pyproject.toml)
   - This establishes the baseline for all future releases

2. Commit Analysis:

   - Analyze ALL commits from the beginning of git history
   - Use: `git log --no-merges --pretty=format:"%h - %s (%an, %ar)"`
   - Include every commit since project inception

3. Categorization:

   - ALL functionality should be documented as "New Features"
   - Even if commits mention "fix" or "enhance", treat as features for first release
   - Do NOT categorize as breaking changes (nothing to break from)
   - List all major components, services, modules as new features

4. Release File Content:

   - Summary should describe the project purpose and initial capabilities
   - Breaking Changes section: "None (Initial Release)"
   - New Features: Comprehensive list of all project capabilities
   - Bug Fixes: "None (Initial Release)"
   - Dependencies: List ALL current dependencies from pyproject.toml
   - Migration Guide: "No migration required (Initial Release)"

5. Release Title:

   - Should be: `v0.1.0 - Initial Release`

6. Verification:
   - This creates the baseline for all future version comparisons
   - Future releases will compare against this v0.1.0 release date

## Common Scenarios

### Hotfix Release (PATCH bump)

- Critical bug fixes only
- Minimal changes since last release
- Fast-track process for urgent fixes

### Major Release (MAJOR bump)

- Breaking changes present
- Comprehensive migration guide required
- Extra attention to backward compatibility notes

### Subsequent Releases (after v0.1.0)

- Always have a previous release file to compare against
- Use the release date from the last release file to filter commits
- Categorize changes based on semantic versioning rules
- Version bump follows standard rules (MAJOR/MINOR/PATCH)

## Example Workflows

### Example 1: First Release Ever

For a brand new project with no previous releases:

1. Current version in pyproject.toml: `0.1.0` (or any version)
2. Check docs/releases/: EMPTY (no files)
3. Determine: This is FIRST release
4. Get ALL commits from project start: 47 commits total
5. Categorize all functionality as "New Features"
6. Version: FORCE to `0.1.0` (ignore pyproject.toml)
7. Create: `docs/releases/v0.1.0.md` with all project features
8. Update: `pyproject.toml` version to `0.1.0`
9. User confirmation: Display summary and wait for approval
10. Git tag: `v0.1.0`
11. Release title: `v0.1.0 - Initial Release`

### Example 2: Subsequent Release

For a project at v0.1.0 releasing v0.2.0:

1. Current version: `0.1.0`
2. Last release file: `docs/releases/v0.1.0.md` (created 2025-10-15)
3. Commits since 2025-10-15: 23 commits
4. Analysis finds: 3 new features, 5 enhancements, 2 bug fixes
5. Version bump: MINOR (new features added)
6. New version: `0.2.0`
7. Create: `docs/releases/v0.2.0.md`
8. Update: `pyproject.toml` version to `0.2.0`
9. User confirmation: Display summary and wait for approval
10. Git tag: `v0.2.0`
11. Release title: `v0.2.0 - Enhanced Analytics and Strategy Services`
