# Incremental Scanning

LucidShark supports two modes of incremental scanning:

1. **Default Mode (Uncommitted Changes)** - Scans only files with uncommitted changes (staged, unstaged, untracked). No extra flags needed.
2. **Branch Comparison Mode (`--base-branch`)** - Filters results to files changed since a branch. Useful for PR reviews and CI pipelines.

CLI examples use `./lucidshark`, the project-local binary installed by `curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash`. If you installed with `pip install lucidshark` (or run it with `uvx lucidshark`), use `lucidshark` instead.

## Default Mode: Uncommitted Changes

**When developing locally, you don't need any special flags.** By default, LucidShark scans only uncommitted changes:

```bash
# Scans only uncommitted changes (default behavior)
./lucidshark scan --linting --type-checking

# Same via MCP
scan(domains=["linting", "type_checking"])
```

This mode:
- Detects staged files (`git add`)
- Detects unstaged modifications
- Detects untracked files
- Runs tools only on these files (where supported)

Use `--all-files` (CLI) or `all_files=true` (MCP) for a full project scan.

## Branch Comparison Mode: `--base-branch`

Use `--base-branch` when you want to filter results based on branch comparison. This is useful for:

- **Pull Request reviews**: Focus on the code being changed in the PR
- **CI pipelines**: Enforce standards on new/modified code only
- **Pre-merge checks**: Verify changes meet quality thresholds

### How It Works

1. **Full analysis runs** - All checks execute for accuracy (tests, linting, etc.)
2. **Results are filtered** - Only changed files are reported
3. **Threshold applies to filtered result** - Per-domain scope configuration

This approach ensures data is accurate (tests aren't skipped, cross-file issues are detected) while focusing your attention on the code you're changing.

## Quick Start

### Local Development (Default - Uncommitted Changes)

```bash
# Scan only uncommitted changes (default behavior)
./lucidshark scan --linting --type-checking

# Full project scan
./lucidshark scan --linting --type-checking --all-files
```

### PR/CI (Branch Comparison)

```bash
# Filter all results to files changed since main
./lucidshark scan --all --base-branch origin/main

# With specific domains
./lucidshark scan --linting --type-checking --coverage --duplication \
  --base-branch origin/main
```

### MCP (AI Agents)

```python
# Default: scan uncommitted changes
mcp__lucidshark__scan(domains=["linting", "type_checking"])

# Full project scan
mcp__lucidshark__scan(domains=["all"], all_files=True)

# PR/CI: filter to branch changes
mcp__lucidshark__scan(domains=["all"], base_branch="origin/main")
```

## Domain-Specific Behavior

### Linting & Type Checking

**Display:** Issues are filtered to only those in changed files.

**Threshold Checking:** The `threshold_scope` controls which issues are checked against `fail_on`:

| Scope | Display | Threshold Check |
|-------|---------|-----------------|
| `changed` (default) | Changed files only | Check changed files issues |
| `project` | Changed files only | Check ALL project issues |
| `both` | Changed files only | Check both; fail if either has issues |

The scope only matters when `fail_on.linting` / `fail_on.type_checking` is set in `lucidshark.yml`. Their failing value is `error`, which counts only HIGH/CRITICAL-severity issues (Ruff `E`/`F` findings, for example, are MEDIUM).

**Example with `scope: project`:**
```
Display: 2 issues in changed files
Project total: 15 issues
fail_on: error
Scope: project

Result: FAIL if any of the 15 project issues is HIGH/CRITICAL, not just the 2 displayed
```

This is useful when you want to see only your changes, but ensure the entire project stays clean.

**Example with `scope: changed`:**
```
Display: 2 issues in changed files
Project total: 15 issues
fail_on: error
Scope: changed

Result: FAIL only if one of those 2 issues is HIGH/CRITICAL (project issues ignored)
```

### Coverage

**Display:** Coverage metrics are filtered to changed files only.

**Threshold Checking:** The `threshold_scope` controls which coverage is checked:

| Scope | Display | Threshold Check |
|-------|---------|-----------------|
| `changed` (default) | Changed files coverage | Check changed files coverage |
| `project` | Changed files coverage | Check full project coverage |
| `both` | Changed files coverage | Check both; fail if either below threshold |

**Example:**
```
Display: 72% coverage on changed files
Project coverage: 85%
Threshold: 80%
Scope: changed

Result: FAIL (72% < 80% on changed files)
```

Unlike linting/type_checking, coverage filtering applies to both display AND the metrics used for threshold calculation (when scope=changed).

### Duplication

**Display:** Duplicates are filtered to those involving at least one changed file (file1 OR file2).

**Threshold Checking:** The `threshold_scope` controls which duplication percentage is checked:

| Scope | Display | Threshold Check |
|-------|---------|-----------------|
| `changed` | Duplicates involving changed files | Check filtered duplication % |
| `project` | Duplicates involving changed files | Check full project duplication % |
| `both` (default) | Duplicates involving changed files | Check both; fail if either exceeds threshold |

**Example:**
```
Display: Duplicates involving changed files (12%)
Project duplication: 8%
Threshold: 10%
Scope: changed

Result: FAIL (12% > 10% on changed files)
```

Like coverage, duplication filtering applies to both display AND the metrics used for threshold calculation (when scope=changed).

> **ℹ️ Why `scope=both` is the Default**
>
> The default `scope=both` prevents **project-wide duplication from creeping up over time**.
>
> With `scope=changed`, the filtered duplication percentage is calculated as:
> ```
> (duplicate_lines_involving_changed_files / total_project_lines) * 100
> ```
>
> **Example of creep with `scope=changed`:**
> - Project has 100,000 total lines
> - Threshold is 5%
> - Each PR adds ~50 duplicate lines involving changed files
> - Filtered percentage per PR: `50 / 100,000 = 0.05%` → PASS
> - After 200 PRs: project has 10,000 duplicate lines (10%) but each PR passed!
>
> With the default `scope=both`, the scan fails if **either** the filtered percentage OR the full project percentage exceeds the threshold, preventing this creep.
>
> **To use lenient checking (only changed files):**
> ```yaml
> pipeline:
>   duplication:
>     threshold: 5.0
>     threshold_scope: changed  # Only check changed files
> ```

## What Gets Included

### Default Mode (No `--base-branch`)

When running without `--base-branch`, LucidShark scans only uncommitted changes:

- **Staged changes** (`git add`)
- **Unstaged modifications**
- **Untracked files**

This is determined by:
```
git diff --cached --name-only      # Staged
git diff --name-only               # Unstaged
git ls-files --others --exclude-standard  # Untracked
```

### Branch Comparison Mode (`--base-branch`)

When using `--base-branch`, LucidShark includes:

**1. Committed Changes (Branch Comparison)**

Files committed to your branch since it diverged from the base:

```
git diff origin/main...HEAD --name-only
```

This uses git's three-dot syntax which compares against the merge-base.

**2. Uncommitted Local Changes** (when working locally)

- **Staged changes** (`git add`)
- **Unstaged modifications**
- **Untracked files**

### Summary

| Mode | Flag | What's Scanned/Filtered |
|------|------|------------------------|
| **Default (local dev)** | (none) | Uncommitted changes only |
| **Full project** | `--all-files` | All files in project |
| **Branch comparison (CI)** | `--base-branch origin/main` | Branch changes + uncommitted |

| Environment | Working Tree | `--base-branch` Behavior |
|-------------|--------------|--------------------------|
| **CI Pipeline** | Clean | Committed branch changes only |
| **Local Development** | Dirty | Committed + uncommitted changes |

## Configuration

### CLI Arguments

| Option | Description |
|--------|-------------|
| `--base-branch BRANCH` | Filter to files changed since this branch |
| `--coverage-threshold-scope` | Scope for coverage threshold |
| `--linting-threshold-scope` | Scope for linting threshold |
| `--type-checking-threshold-scope` | Scope for type checking threshold |
| `--duplication-threshold-scope` | Scope for duplication threshold |

### Configuration File (lucidshark.yml)

```yaml
pipeline:
  linting:
    enabled: true
    threshold_scope: changed  # default; or "project" or "both"
    tools:
      - name: ruff

  type_checking:
    enabled: true
    threshold_scope: changed  # default
    tools:
      - name: mypy

  testing:
    enabled: true  # coverage requires testing
    tools:
      - name: pytest

  coverage:
    enabled: true
    threshold: 80
    threshold_scope: changed  # default
    tools:
      - name: coverage_py

  duplication:
    enabled: true
    threshold: 10
    threshold_scope: both  # default; use "changed" for lenient checking
    tools:
      - name: duplo

# threshold_scope only affects the exit code of domains listed here
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
  duplication: above_threshold
```

CLI flags (`--coverage-threshold-scope`, etc.) take precedence over `threshold_scope` in the config file.

### MCP Parameters

```python
mcp__lucidshark__scan(
    domains=["all"],
    base_branch="origin/main",
    coverage_threshold_scope="changed",  # default
    duplication_threshold_scope="both"  # default
)
```

> **Note:** The MCP `scan` tool does not read `threshold_scope` from `lucidshark.yml`. Coverage defaults to `"changed"` and duplication to `"both"` unless you pass `coverage_threshold_scope` / `duplication_threshold_scope` explicitly. `linting_threshold_scope` and `type_checking_threshold_scope` are accepted but currently have no effect, and the MCP scan does not apply `fail_on`: it reports the filtered issues plus the coverage/duplication `passed` flags.

## CI Platform Integration

### GitHub Actions

```yaml
name: PR Quality Check

on:
  pull_request:
    branches: [main, develop]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Required for branch comparison

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install lucidshark
          pip install -e ".[dev]"  # your project's dependencies, for the test run

      - name: Run incremental scan
        run: |
          lucidshark scan --all \
            --base-branch origin/${{ github.base_ref }} \
            --coverage-threshold 80 \
            --duplication-threshold 10
```

**Important:** Use `fetch-depth: 0` to ensure full git history is available.

The job's exit code follows the `fail_on` section of `lucidshark.yml`: `--coverage-threshold` and `--duplication-threshold` set the thresholds, but the build only fails on them when `fail_on.coverage` / `fail_on.duplication` are set (see the [configuration example](#configuration-file-lucidsharkyml)).

### GitLab CI

```yaml
stages:
  - quality

quality:
  stage: quality
  image: python:3.11
  variables:
    GIT_DEPTH: 0
  script:
    - pip install lucidshark
    - pip install -e ".[dev]"  # your project's dependencies, for the test run
    - lucidshark scan --all
        --base-branch origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME
        --coverage-threshold 80
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### Bitbucket Pipelines

```yaml
pipelines:
  pull-requests:
    '**':
      - step:
          name: Quality Check
          image: python:3.11
          clone:
            depth: full
          script:
            - pip install lucidshark
            - pip install -e ".[dev]"  # your project's dependencies, for the test run
            - lucidshark scan --all
                --base-branch origin/$BITBUCKET_PR_DESTINATION_BRANCH
                --coverage-threshold 80
```

### Azure DevOps

```yaml
pr:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - checkout: self
    fetchDepth: 0

  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: |
      pip install lucidshark
      pip install -e ".[dev]"  # your project's dependencies, for the test run
    displayName: 'Install dependencies'

  - script: |
      lucidshark scan --all \
        --base-branch origin/$(System.PullRequest.TargetBranch) \
        --coverage-threshold 80
    displayName: 'Run incremental scan'
```

## Example Scenarios

These scenarios fail the scan only for domains that have a `fail_on` entry in `lucidshark.yml`; without one, results are reported but the exit code is 0. The CLI `--fail-on <severity>` flag overrides the config `fail_on` and applies to every non-ignored issue in every scanned domain, so threshold scopes have no effect when it is used.

### Scenario 1: Strict PR linting

Check linting only for issues in changed files, even if the project has existing issues. With `fail_on.linting: error`, the scan fails only on HIGH/CRITICAL linting issues in changed files (Ruff `E`/`F` findings are MEDIUM). To fail on any LOW-or-higher linting issue in changed files, add `--fail-on low`.

```bash
./lucidshark scan --linting --base-branch origin/main \
  --linting-threshold-scope changed
```

### Scenario 2: Coverage on changed files only

Changed files must have 80% coverage, but overall project can be lower.

```bash
./lucidshark scan --testing --coverage --base-branch origin/main \
  --coverage-threshold 80 --coverage-threshold-scope changed
```

### Scenario 3: Enforce both project and changed files

Fail if either project OR changed files exceed duplication threshold.

```bash
./lucidshark scan --duplication --base-branch origin/main \
  --duplication-threshold 10 --duplication-threshold-scope both
```

### Scenario 4: Full incremental scan before PR

Run all checks filtered to changed files:

```bash
./lucidshark scan --all --base-branch origin/main \
  --coverage-threshold 80 \
  --duplication-threshold 10 \
  --coverage-threshold-scope changed \
  --linting-threshold-scope changed
```

## Local Development Workflow

### Check changes before committing

```bash
# On your feature branch
git checkout feature/my-new-feature

# Edit some files
vim src/myapp/utils.py

# Check all quality metrics for your changes
./lucidshark scan --all --base-branch main

# Fix any issues, then commit
git add .
git commit -m "Add new utility function"
```

### Before creating a PR

```bash
# Ensure all changes meet quality standards
./lucidshark scan --all --base-branch origin/main \
  --coverage-threshold 80 \
  --duplication-threshold 10

# If it passes, push
git push origin feature/my-new-feature
```

## Known Behaviors

### Domain Behavior Summary

| Domain | Display Filtered | Threshold Scope Affects Display | Threshold Scope Affects Check |
|--------|:----------------:|:-------------------------------:|:-----------------------------:|
| Linting | Yes | No (always shows changed) | Yes |
| Type Checking | Yes | No (always shows changed) | Yes |
| Coverage | Yes | No (always shows changed) | Yes |
| Duplication | Yes | No (always shows changed) | Yes |
| Security | Yes (except findings with no file path) | N/A (no scope option) | N/A (`fail_on` sees the filtered findings) |
| Testing | No (all failures are shown) | N/A (no scope option) | N/A (`fail_on` sees every failure) |

**Key difference:** For linting/type_checking, `threshold_scope` only affects which issues are checked against `fail_on`, not what's displayed. For coverage/duplication, filtering affects both display and the metrics.

### Security Results Are Filtered Too, Test Failures Are Not

With `--base-branch` (CLI and MCP), issues are filtered to the changed files, including SAST, SCA and IaC findings. Two kinds of issue are never filtered:
- **Test failures.** The full suite runs, so a failing test is reported and trips `fail_on.testing: any` even when its test file didn't change on the branch
- **Issues with no file path**, such as container image findings or a tool that failed to run. They can't be attributed to a file, so they are always reported

In practice:
- An SCA vulnerability is reported only if the manifest/lockfile it was found in changed on the branch
- `fail_on.security` sees findings in changed files plus any finding without a file path
- Coverage and duplication are evaluated from their filtered percentages, according to `threshold_scope`

Run without `--base-branch` (for example with `--all-files`) to see project-wide security results.

### Deleted Files Not Reported

Deleted files are excluded from changed files detection. When you delete a file in a PR:
- Linting/type checking won't report old issues from the deleted file
- Coverage won't include the deleted file's metrics
- This is correct behavior - issues in deleted files don't matter

### Duplication Percentage Context

For filtered duplication results:
- `duplicate_lines` = lines in filtered duplicates (involving changed files)
- `total_lines` = original full project lines
- Percentage reflects "what portion of the project these duplicates represent"

This gives context: "50 duplicate lines involving your changes represent 0.5% of the project"

> **Note:** Because the filtered percentage is relative to the full project's line count, each PR's contribution appears small. Over many PRs, this can lead to **duplication creep** where the overall project exceeds the threshold while each individual PR passes. The default `threshold_scope: both` prevents this. See the [Duplication section](#duplication) for details.

### Testing Always Runs Full Suite

Even with `--base-branch`, all tests run and every test failure is reported (see [above](#security-results-are-filtered-too-test-failures-are-not)). Only coverage **reporting** is filtered. This ensures:
- Indirect coverage is measured (test for `module_a` covers `module_b`)
- Regressions are caught
- Coverage percentages are accurate

## FAQ

### Does this skip tests for unchanged files?

No. All tests run for accurate coverage measurement, and every test failure is reported. Only the reporting of other domains is filtered.

### What if I have no changes on my branch?

Full project results are shown with a warning.

### Why does CI need `fetch-depth: 0`?

Branch comparison requires full git history. Shallow clones fail to find the merge-base.

### Can I exclude uncommitted changes?

Currently no. Commit your work first or run in CI where the working tree is clean.

### Why run full analysis if only showing changed files?

1. **Indirect coverage**: A test for `module_a.py` might cover code in `module_b.py`
2. **Cross-file detection**: Linting and duplication can detect issues spanning files
3. **Regression detection**: Running all tests catches regressions
4. **Accurate metrics**: Partial runs produce misleading numbers

### What about merge commits?

The three-dot syntax (`main...HEAD`) compares against the merge-base, so merge commits from main into your branch don't count as "your changes."

## Error Handling

### Branch Not Found

```
Error: Could not compare against branch 'origin/main'.
Ensure the branch exists and git history is available (use fetch-depth: 0 in CI).
```

**Solutions:**
- Verify the branch name is correct
- In CI, ensure `fetch-depth: 0` or equivalent is set
- Run `git fetch origin main` to fetch the branch

### No Changed Files

```
Warning: No files changed since origin/main, showing full results
```

Full project results are shown when there are no changes.
