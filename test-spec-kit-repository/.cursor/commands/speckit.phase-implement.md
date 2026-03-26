---
description: Implement the spec phase by phase, creating a separate branch and PR for each. Setup and Foundation phases are combined into the first PR. The command is resumable via a state file.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty). Supported arguments:
- `resume` or `--resume`: Resume from the last saved phase state without prompting
- `--from <N>`: Start from phase group N (e.g. `--from 2`)

## Pre-Execution Checks

**Check for extension hooks (before implementation)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_implement` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter to only hooks where `enabled: true`
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    
    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR, BRANCH, and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Detect the repository default branch**:
   - Run: `git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}'`
   - If that fails (no remote configured), fall back to `main`
   - Store as DEFAULT_BRANCH

3. **Load or initialize state**:
   - Check if `FEATURE_DIR/phase-implement-state.json` exists
   - **If state file exists**:
     - Read the file and print current progress:
       ```
       Existing phase-implement session found
       ========================================
       Feature      : <feature_name>
       Base branch  : <base_branch>
       Completed PRs: <completed_groups count>
       Next group   : <current_group>
       ```
     - If `resume` or `--resume` is in user input: continue silently from `current_group`
     - Otherwise ask: "Resume this session? (yes/no)" and wait for response
       - If "no": ask "Start fresh? This will discard the saved state. (yes/no)"
         - If "yes": delete `FEATURE_DIR/phase-implement-state.json` and proceed as a fresh run
         - If "no": halt
   - **If `--from <N>` is in user input**: override `current_group` to N (ask for confirmation if N > 1 and would skip incomplete groups)
   - **If no state file exists**: this is a fresh run, proceed to step 4

4. **Load implementation context**:
   - **REQUIRED**: Read `tasks.md` for the complete task list and execution plan
   - **REQUIRED**: Read `plan.md` for tech stack, architecture, and file structure
   - **IF EXISTS**: Read `data-model.md` for entities and relationships
   - **IF EXISTS**: Read `contracts/` for API specifications and test requirements
   - **IF EXISTS**: Read `research.md` for technical decisions and constraints
   - **IF EXISTS**: Read `quickstart.md` for integration scenarios

5. **Parse tasks.md and build the execution plan**:
   - Identify all `## Phase N:` headings (Phase 1, Phase 2, Phase 3, ...)
   - For each phase extract:
     - Phase number and title (the text after `Phase N:`)
     - Purpose line (the line after `**Purpose**:` if present)
     - All task lines (lines matching `- [ ]` or `- [X]` or `- [x]`)
   - Group phases into **PR groups**:
     - **Group 1**: Phase 1 (Setup) + Phase 2 (Foundational) → one combined PR
     - **Group 2, 3, ...**: each remaining Phase gets its own PR
   - Derive branch names using BRANCH as the namespace:
     - Group 1: `<BRANCH>/phase-1-2-setup-foundation`
     - Group N (for phase P): `<BRANCH>/phase-<P>-<title-slug>` where title-slug is lowercase, max 30 chars, spaces replaced with hyphens, non-alphanumeric characters removed
   - PR target (base) branches:
     - Group 1 PR targets: DEFAULT_BRANCH
     - Group N PR targets: previous group's branch
   - Display the full execution plan:
     ```
     Phase Implementation Plan
     =========================
     Feature branch : <BRANCH>
     Base branch    : <DEFAULT_BRANCH>

     PR #1  branch  : <BRANCH>/phase-1-2-setup-foundation
            targets : <DEFAULT_BRANCH>
            phases  : Phase 1 (Setup) + Phase 2 (Foundational)

     PR #2  branch  : <BRANCH>/phase-3-<slug>
            targets : <BRANCH>/phase-1-2-setup-foundation
            phases  : Phase 3 (<title>)

     PR #3  branch  : <BRANCH>/phase-4-<slug>
            targets : <BRANCH>/phase-3-<slug>
            phases  : Phase 4 (<title>)
     ...
     ```
   - Ask: "Proceed with this plan? (yes/no)" and wait for confirmation before continuing.

6. **Initialize state file** (fresh run only):
   Create `FEATURE_DIR/phase-implement-state.json`:
   ```json
   {
     "feature_dir": "<FEATURE_DIR>",
     "feature_name": "<basename of FEATURE_DIR>",
     "spec_path": "<FEATURE_DIR>/spec.md",
     "base_branch": "<DEFAULT_BRANCH>",
     "feature_branch": "<BRANCH>",
     "started_at": "<ISO 8601 timestamp>",
     "updated_at": "<ISO 8601 timestamp>",
     "groups": [],
     "current_group": 1,
     "total_groups": <total number of groups>
   }
   ```

7. **For each phase group** (loop from `current_group` through `total_groups`):

   ### a. Determine base branch
   - Group 1: base = DEFAULT_BRANCH
   - Group N > 1: base = previous group's `branch` value from state file `groups` array

   ### b. Create and switch to the phase branch
   ```sh
   git fetch origin
   git checkout <base-branch>
   git pull origin <base-branch>
   git checkout -b <phase-branch-name>
   ```

   ### c. Ensure spec files are accessible on this branch
   - Verify that `tasks.md` and `plan.md` exist on this branch (they live in FEATURE_DIR under `specs/`)
   - If they are missing (they may only exist on BRANCH but not on DEFAULT_BRANCH), copy them:
     ```sh
     git checkout <BRANCH> -- <relative-path-to-FEATURE_DIR>/
     ```
   - If spec files still cannot be found after the copy attempt, halt with a clear error.

   ### d. Project setup verification (Group 1 only)
   Create or verify ignore files based on the actual project setup detected in `plan.md`:

   **Detection & Creation Logic**:
   - Check if the repository is a git repo (`git rev-parse --git-dir 2>/dev/null`) → create/verify `.gitignore`
   - Check if Dockerfile* exists or Docker mentioned in plan.md → create/verify `.dockerignore`
   - Check if `.eslintrc*` or `eslint.config.*` exists → create/verify `.eslintignore` or add `ignores` entries
   - Check if `.prettierrc*` exists → create/verify `.prettierignore`
   - Check if `.npmrc` or `package.json` exists → create/verify `.npmignore` (if publishing)
   - Check if `*.tf` files exist → create/verify `.terraformignore`

   **If ignore file already exists**: append only missing critical patterns
   **If missing**: create with full pattern set for the detected technology stack

   ### e. Implement tasks for phases in this group
   Follow the same implementation rules as `speckit.implement`:
   - Execute tasks phase-by-phase within the group
   - Run sequential tasks in order; tasks marked `[P]` can run in parallel
   - Apply TDD approach: write and run failing tests before implementing if test tasks are present
   - File-based coordination: tasks affecting the same files must run sequentially
   - Mark each completed task as `[X]` in `tasks.md`
   - Report progress after each completed task
   - Halt if a non-parallel task fails; for parallel tasks `[P]`, continue and report failures

   ### f. Commit and push
   ```sh
   git add -A
   git commit -m "feat: implement <phase-title(s)> for <feature-name>

   Implements:
   <bullet list of phase titles in this group>

   Spec: <FEATURE_DIR>/spec.md"
   git push -u origin <phase-branch-name>
   ```

   ### g. Create pull request
   Build the PR body using the following template:

   ```markdown
   ## <Feature Name>: <Phase Title(s)>

   **Spec**: `<FEATURE_DIR>/spec.md`
   **Feature branch**: `<BRANCH>`

   ---

   ### Phases in this PR

   <For each phase in the group:>

   #### Phase <N>: <Title>

   **Purpose**: <purpose line from tasks.md>

   **Tasks**:
   <copy the full task checklist from tasks.md for this phase, preserving current checkbox state>

   ---
   <end for each phase>
   ```

   Run:
   ```sh
   gh pr create \
     --title "<Feature Name>: <Phase Title(s)>" \
     --body "<PR body above>" \
     --base <base-branch> \
     --head <phase-branch-name>
   ```
   Capture the PR URL printed by `gh pr create`.

   ### h. Update state file
   Append to `groups` array in `FEATURE_DIR/phase-implement-state.json`:
   ```json
   {
     "group_number": <N>,
     "phases": [<list of phase numbers>],
     "title": "<phase title(s)>",
     "branch": "<phase-branch-name>",
     "base_branch": "<base-branch>",
     "pr_url": "<pr-url>",
     "status": "open",
     "completed_at": "<ISO 8601 timestamp>"
   }
   ```
   Set `current_group` to N + 1 and update `updated_at`.

   Commit the updated state file and any task progress to the phase branch:
   ```sh
   git add "<FEATURE_DIR>/phase-implement-state.json"
   git add "<FEATURE_DIR>/tasks.md"
   git diff --cached --quiet || git commit -m "chore: update phase-implement state and task progress"
   git push
   ```

   ### i. Report and prompt
   Print:
   ```
   ✓ Group <N> complete
     Branch : <phase-branch-name>
     PR     : <pr-url>
   ```
   If there are more groups remaining, ask: "Proceed to group <N+1> (<next-phase-title>)? (yes / no / stop)"
   - `yes`: continue the loop to the next group
   - `no` or `stop`: save state, print resume instructions, and halt:
     ```
     Session paused. To resume, run:
       /speckit.phase-implement --resume
     ```

8. **Completion**:
   - All groups have been implemented and PRs created
   - Print a summary table:
     ```
     Phase Implementation Complete!
     ================================
     | PR  | Branch                              | Phases      | PR URL   |
     |-----|-------------------------------------|-------------|----------|
     | #1  | .../phase-1-2-setup-foundation      | Phase 1, 2  | <url>    |
     | #2  | .../phase-3-<slug>                  | Phase 3     | <url>    |
     | #3  | .../phase-4-<slug>                  | Phase 4     | <url>    |
     ```
   - Update `FEATURE_DIR/phase-implement-state.json`: set `"completed": true` and `updated_at`
   - Print merge guidance:
     ```
     Next steps:
     - PRs are stacked — merge them in order: PR #1 → PR #2 → PR #3 → ...
     - After each merge, GitHub will automatically retarget the next PR to the default branch.
     - Run /speckit.checklist to validate acceptance criteria before merging.
     ```

9. **Check for extension hooks** (after completion):
   - Check if `.specify/extensions.yml` exists in the project root.
   - If it exists, read it and look for entries under the `hooks.after_implement` key
   - If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
   - Filter to only hooks where `enabled: true`
   - For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
     - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
     - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
   - For each executable hook, output the following based on its `optional` flag:
     - **Optional hook** (`optional: true`):
       ```
       ## Extension Hooks

       **Optional Hook**: {extension}
       Command: `/{command}`
       Description: {description}

       Prompt: {prompt}
       To execute: `/{command}`
       ```
     - **Mandatory hook** (`optional: false`):
       ```
       ## Extension Hooks

       **Automatic Hook**: {extension}
       Executing: `/{command}`
       EXECUTE_COMMAND: {command}
       ```
   - If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
