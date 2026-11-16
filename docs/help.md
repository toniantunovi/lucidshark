# LucidShark Reference Documentation

LucidShark is a unified code quality tool that combines linting, type checking, formatting, security scanning, testing, coverage analysis, and duplication detection into a single pipeline.

## Quick Start

### Installation

**Standalone binary (Linux/macOS, no Python required):**
```bash
curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash
```

**pip (Python 3.10+):**
```bash
pip install lucidshark      # or run without installing: uvx lucidshark
```

**Note:** The install script creates a project-local `./lucidshark` binary; use `./lucidshark` to run the project-specific version. A pip install puts `lucidshark` on your `PATH`. Examples below use `./lucidshark`; with pip, drop the `./`.

The installer verifies the binary against the release's `SHA256SUMS` before installing it and aborts on mismatch. Releases published before checksums existed (0.8.4 and earlier) can only be installed with `--insecure-skip-checksum`. Every scanner or tool binary LucidShark downloads later is checked against a SHA-256 pinned inside LucidShark.

### Recommended Setup

```bash
./lucidshark init  # Configures Claude Code AND generates lucidshark.yml
# Restart Claude Code to apply changes
```

This single command detects your project's languages, generates a full `lucidshark.yml` with all supported tools enabled, and configures Claude Code integration. For advanced customization after initial setup, ask your AI assistant: "Autoconfigure LucidShark for this project".

### Run Scans

```bash
# Default: scan only changed files (uncommitted changes)
./lucidshark scan --linting --type-checking

# Full project scan (all domains, all files)
./lucidshark scan --all --all-files

# Run specific checks (on changed files by default)
./lucidshark scan --linting        # Linting only
./lucidshark scan --type-checking  # Type checking only
./lucidshark scan --sca            # Dependency vulnerabilities (always project-wide)
./lucidshark scan --sast           # Code security analysis

# Auto-fix linting issues (on changed files)
./lucidshark scan --linting --fix

# PR/CI: filter results to files changed since branch
./lucidshark scan --all --base-branch origin/main
```

---

## CLI Commands

### Global Options

These options belong to the top-level command and must come before the subcommand (`lucidshark --debug scan ...`, not `lucidshark scan --debug`):

| Option | Description |
|--------|-------------|
| `--version` | Show lucidshark version and exit |
| `--debug` | Enable debug logging |
| `--verbose`, `-v` | Enable verbose (info-level) logging |
| `--quiet`, `-q` | Reduce logging output to errors only |

### `lucidshark init` / `./lucidshark init`

Configure AI coding tools to use LucidShark **and** generate a `lucidshark.yml` configuration file with all domains enabled for the detected languages.

This command does two things:
1. **Configures AI tool integration**: Claude Code by default (`.mcp.json`, `.claude/skills/`, `.claude/CLAUDE.md`, `.claude/settings.json`), plus Cursor, Windsurf and Aider when their flags are given
2. **Generates `lucidshark.yml`** — detects project languages, loads pre-built templates with all supported tools, and writes a complete configuration

| Option | Description |
|--------|-------------|
| `--claude-code` | Configure Claude Code (the default when no tool flag is given) |
| `--cursor` | Configure Cursor: `.cursor/mcp.json` and `.cursor/rules/lucidshark.mdc` |
| `--windsurf` | Configure Windsurf: `.windsurf/rules/lucidshark.md`, and print an MCP snippet (with absolute paths) to merge into the global `~/.codeium/windsurf/mcp_config.json`, or `.devin/mcp_config.json` in Devin Desktop. `init` writes neither file |
| `--aider` | Configure Aider: `lint-cmd`, `auto-lint` and `read` in `.aider.conf.yml`, plus a `CONVENTIONS.md` section |
| `--all-tools` | Configure every supported tool |
| `--dry-run` | Show changes without applying |
| `--force` | Overwrite existing configuration (selected tools and `lucidshark.yml`) |
| `--remove` | Remove LucidShark from the selected tools' configuration |
| `--no-config` | Skip `lucidshark.yml` generation (only configure AI tool integration) |

Tool flags combine. Shared files are merged through managed sections, so user content in `CLAUDE.md`, `CONVENTIONS.md`, `.aider.conf.yml` and MCP JSON files is preserved. In `.aider.conf.yml`, keys you already set (such as your own `lint-cmd`) are left unchanged.

**Config generation details:**
- Detects languages by scanning file extensions and marker files (e.g., `pyproject.toml`, `package.json`, `Cargo.toml`)
- Loads pre-built templates for each detected language with all supported tools enabled
- Merges templates for multi-language projects (deduplicates tools and ignore patterns)
- Skips generation if `lucidshark.yml` already exists (use `--force` to overwrite)
- All domains are enabled: linting, type checking, formatting, security (SCA/SAST/IaC), testing, coverage, duplication

**Examples:**
```bash
# Full setup: Claude Code + config generation
./lucidshark init

# Configure Cursor and Aider instead of Claude Code
./lucidshark init --cursor --aider

# Configure every supported AI tool
./lucidshark init --all-tools

# Remove LucidShark integration
./lucidshark init --remove

# Only configure Claude Code, skip config generation
./lucidshark init --no-config

# Regenerate everything (overwrite existing)
./lucidshark init --force

# Preview changes without applying
./lucidshark init --dry-run
```

**Language templates and their tools:**

| Language | Linting | Type Checking | Formatting | Testing | Coverage |
|----------|---------|---------------|------------|---------|----------|
| Python | ruff | mypy, pyright | ruff_format | pytest | coverage_py |
| JavaScript | eslint, biome | — | prettier | jest, vitest, mocha, karma, playwright | istanbul, vitest_coverage |
| TypeScript | eslint, biome | typescript | prettier | jest, vitest, mocha, karma, playwright | istanbul, vitest_coverage |
| Go | golangci_lint | go_vet | gofmt | go_test | go_cover |
| Rust | clippy | cargo_check | rustfmt | cargo | tarpaulin |
| Java | checkstyle, pmd | spotbugs | — | maven | jacoco |
| Kotlin | ktlint | detekt | ktlint_format | maven | jacoco |
| C# | dotnet_format | dotnet_build | dotnet_format_whitespace | dotnet_test | dotnet_coverage |
| C | clang_tidy | cppcheck | clang_format | ctest | gcov |
| C++ | clang_tidy | cppcheck | clang_format | ctest | lcov |
| Scala | scalafix | scala_compile | scalafmt | sbt | scoverage |
| Swift | swiftlint | swift_compiler | swiftformat | swift_test | swift_coverage |
| Ruby | rubocop | sorbet | rubocop_format | rspec | simplecov |
| PHP | phpcs | phpstan | php_cs_fixer | phpunit | phpunit_coverage |

All languages also include: security scanning (trivy for SCA, opengrep for SAST, checkov for IaC) and duplication detection (duplo). Go additionally includes gosec for Go-specific SAST.

### `lucidshark scan`

Run the quality/security pipeline. By default, scans only changed files (uncommitted changes).

**Which domains run:** with no domain flag, `scan` runs only the security domains (SCA, SAST, IaC, container) enabled in `lucidshark.yml`. Linting, type checking, formatting, testing, coverage and duplication run only when their flag or `--all` is given. A non-security flag on its own (for example `--linting`) runs just that domain, without security scanning. This differs from the MCP `scan` tool, whose `domains` default is `["all"]`.

#### Scan Domains

| Flag | Domain | Description |
|------|--------|-------------|
| `--linting` | linting | Code style and linting (Ruff, ESLint, Biome, Clippy, Checkstyle, PMD, ktlint, golangci-lint, dotnet format, clang-tidy, Scalafix, SwiftLint, RuboCop, phpcs) |
| `--type-checking` | type_checking | Static type analysis (mypy, pyright, TypeScript, SpotBugs, detekt, cargo check, go vet, dotnet build, cppcheck, scalac, Swift compiler, Sorbet, PHPStan) |
| `--formatting` | formatting | Code formatting (Ruff Format, Prettier, ktlint, rustfmt, gofmt, dotnet format, clang-format, Scalafmt, SwiftFormat, RuboCop Format, PHP-CS-Fixer) |
| `--sca` | sca | Dependency vulnerability scanning (Trivy) |
| `--sast` | sast | Code security patterns (OpenGrep, gosec for Go) |
| `--iac` | iac | Infrastructure-as-Code scanning (Checkov) |
| `--container` | container | Container image scanning (Trivy) |
| `--testing` | testing | Run test suite (pytest, Jest, Vitest, Mocha, Karma, Playwright, Maven, cargo test, go test, dotnet test, CTest, sbt test, swift test, RSpec, PHPUnit) |
| `--coverage` | coverage | Coverage analysis (coverage.py, Istanbul, Vitest, JaCoCo, Tarpaulin, go cover, dotnet coverage, gcov/lcov, Scoverage, llvm-cov, SimpleCov, PHPUnit Clover). **Requires `--testing`** |
| `--duplication` | duplication | Code duplication detection (Duplo) |
| `--all` | all | Enable all domains |

#### Target Options

| Option | Description |
|--------|-------------|
| `path` | Path to scan (default: `.`) |
| `--files FILE [FILE ...]` | Specific files to scan (overrides default changed-files behavior) |
| `--all-files` | Scan entire project instead of just changed files |
| `--image IMAGE` | Container image to scan; can be specified multiple times (with `--container`) |
| `--base-branch BRANCH` | **For PR/CI workflows:** Filter results to files changed since this branch (e.g., `origin/main`). Unlike the default mode (which scans only uncommitted changes), this runs full analysis then filters results. Applies to all domains: linting, type_checking, coverage, duplication. See [Incremental Scanning](incremental-scanning.md). |

#### Output Options

| Option | Description |
|--------|-------------|
| `--format {ai,json,table,sarif,summary}` | Output format (default: `json`; `ai` is optimized for AI agents) |

#### Configuration Options

| Option | Description |
|--------|-------------|
| `--fail-on {critical,high,medium,low}` | Exit 1 if any issue in any domain is at or above this severity. Overrides the `fail_on` settings in `lucidshark.yml` |
| `--coverage-threshold PERCENT` | Coverage threshold (default: 80) |
| `--coverage-threshold-scope {changed,project,both}` | With `--base-branch`: apply coverage threshold to changed files (default), project, or both |
| `--linting-threshold-scope {changed,project,both}` | With `--base-branch`: apply linting threshold to changed files (default), project, or both |
| `--type-checking-threshold-scope {changed,project,both}` | With `--base-branch`: apply type checking threshold to changed files (default), project, or both |
| `--duplication-threshold PERCENT` | Maximum allowed duplication percentage (default: 10) |
| `--duplication-threshold-scope {changed,project,both}` | With `--base-branch`: apply duplication threshold to changed files, project, or both (default when `pipeline.duplication` is configured) |
| `--min-lines N` | Minimum lines for a duplicate block (default: 4) |
| `--config PATH` | Path to config file (default: first of `.lucidshark.yml`, `.lucidshark.yaml`, `lucidshark.yml`, `lucidshark.yaml` in the project root) |

#### Execution Options

| Option | Description |
|--------|-------------|
| `--dry-run` | Show what would be scanned without executing |
| `--sequential` | Disable parallel execution |
| `--fix` | Apply auto-fixes (linting and formatting) |
| `--stream` | Stream tool output in real-time as scans run |

**Examples:**
```bash
./lucidshark scan --linting --type-checking              # Default: changed files only
./lucidshark scan --all --all-files                       # Full project scan
./lucidshark scan --linting --files src/main.py src/utils.py  # Specific files
./lucidshark scan --linting --fix                         # Lint with auto-fix
./lucidshark scan --sca --sast --all-files --fail-on high    # Full security scan
./lucidshark scan --all --all-files --format sarif > results.sarif  # SARIF output
./lucidshark scan --container --image myapp:latest        # Container scanning
./lucidshark scan --all --stream                          # Stream output
./lucidshark scan --testing --coverage --base-branch origin/main  # PR-based incremental
```

#### CI Platform Integration

Use `--base-branch` to filter results to files changed in a PR. All scans run fully  -  only reporting is filtered. Works with all domains: linting, type_checking, coverage, and duplication. See [Incremental Scanning](incremental-scanning.md) for comprehensive documentation.

**GitHub Actions** (using pip install):
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'

- name: Install LucidShark
  run: pip install lucidshark

- name: Run LucidShark Incremental Scan
  run: |
    lucidshark scan --all \
      --base-branch origin/${{ github.base_ref }} \
      --coverage-threshold 80 \
      --duplication-threshold 10
```

**GitHub Actions** (using binary install):
```yaml
- name: Install LucidShark
  run: curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash

- name: Run LucidShark Incremental Scan
  run: |
    ./lucidshark scan --all \
      --base-branch origin/${{ github.base_ref }} \
      --coverage-threshold 80 \
      --duplication-threshold 10
```

**GitLab CI** (pip install):
```yaml
test:
  script:
    - pip install lucidshark
    - lucidshark scan --all \
        --base-branch origin/$CI_MERGE_REQUEST_TARGET_BRANCH_NAME \
        --coverage-threshold 80
```

**Bitbucket Pipelines** (pip install):
```yaml
- step:
    script:
      - pip install lucidshark
      - lucidshark scan --all \
          --base-branch origin/$BITBUCKET_PR_DESTINATION_BRANCH \
          --coverage-threshold 80
```

**Azure DevOps** (pip install):
```yaml
- script: |
    pip install lucidshark
    lucidshark scan --all \
      --base-branch origin/$(System.PullRequest.TargetBranch) \
      --coverage-threshold 80
```

**Important:** Use `fetch-depth: 0` (or equivalent) in your CI checkout step to ensure full git history is available for branch comparison.

### `lucidshark status` / `./lucidshark status`

Show LucidShark version, platform, installed scanner plugins and tool status. Takes no options.

**Examples:**
```bash
# Pip install
lucidshark status

# Binary install
./lucidshark status
```

### `lucidshark serve` / `./lucidshark serve`

Run LucidShark as a server for AI tool integration.

| Option | Description |
|--------|-------------|
| `--mcp` | Run as MCP server over stdio (the default when neither `--mcp` nor `--watch` is given) |
| `--watch` | Watch files and run a scan of all configured domains on each debounced batch of changes; results are printed to stdout as JSON |
| `--debounce MS` | File watcher debounce delay (default: 1000) |
| `path` | Project directory to serve (default: `.`) |

With a binary install, `serve --mcp` checks for a LucidShark update, applies it and restarts before serving. Other commands check for and download a new release in the background, and it is applied the next time LucidShark starts. Set `settings.auto_update: false` in `lucidshark.yml` to turn update checks off.

**Examples:**
```bash
# Pip install
lucidshark serve --mcp
lucidshark serve --watch
lucidshark serve --watch --debounce 500

# Binary install
./lucidshark serve --mcp
./lucidshark serve --watch
./lucidshark serve --watch --debounce 500
```


### `lucidshark help` / `./lucidshark help`

Display this documentation.

```bash
# Pip install
lucidshark help

# Binary install
./lucidshark help
```

### `lucidshark doctor` / `./lucidshark doctor`

Run health checks on the LucidShark setup and environment. Checks configuration, tools, environment, and AI integrations.

**Checks performed:**
- Configuration file exists and is valid
- Security tools installed (trivy, opengrep, gosec, checkov)
- Common linters/type checkers available (ruff, mypy, pyright)
- Python version (requires 3.10+)
- Git repository detected
- Claude Code MCP integration configured

Exits 0 when every check passes and 1 when any check fails.

**Examples:**
```bash
# Pip install
lucidshark doctor

# Binary install
./lucidshark doctor
```

### `lucidshark validate` / `./lucidshark validate`

Validate a `lucidshark.yml` configuration file and report errors/warnings.

| Option | Description |
|--------|-------------|
| `--config PATH` | Path to config file (default: first of `.lucidshark.yml`, `.lucidshark.yaml`, `lucidshark.yml`, `lucidshark.yaml` in the current directory) |

**Exit codes:**
- 0: Configuration is valid (may have warnings)
- 1: Configuration has errors
- 3: Configuration file not found

**Examples:**
```bash
# Pip install
lucidshark validate
lucidshark validate --config custom-config.yml

# Binary install
./lucidshark validate
./lucidshark validate --config custom-config.yml
```

### `lucidshark overview`

Generate a quality overview report (`QUALITY.md`) from scan results. This provides a git-committed quality dashboard - no server or SaaS required.

| Option | Description |
|--------|-------------|
| `--show` | Display overview to stdout (default if no mode specified) |
| `--preview` | Preview what would be written without saving |
| `--update` | Write QUALITY.md and update history file |
| `--scan` | Run a scan first if no cached results exist |
| `path` | Project directory (default: `.`) |

**IMPORTANT: Requires full project scan**

Overview requires a full project scan (`--all-files`) because it represents the entire repository's quality state. Partial/incremental scans are rejected:

```bash
# This will fail - incremental scan
./lucidshark scan --all
./lucidshark overview  # Error: requires full project scan

# This works - full project scan
./lucidshark scan --all --all-files
./lucidshark overview  # Success
```

**How it works:**
1. Reads cached scan results from `.lucidshark/last-scan.json`
2. Validates the scan was a full project scan (not incremental)
3. Calculates a health score (0-10) based on issues, coverage, and duplication
4. Generates a markdown overview with domain status, trends, and top files
5. Optionally saves to `QUALITY.md` and appends to history

**Examples:**
```bash
# Pip install
lucidshark overview                                # View overview
lucidshark overview --preview                      # Preview without saving
lucidshark overview --update                       # Update QUALITY.md
lucidshark scan --all --all-files && lucidshark overview --update  # Scan then update

# Binary install
./lucidshark overview                              # View overview
./lucidshark overview --preview                    # Preview without saving
./lucidshark overview --update                     # Update QUALITY.md
./lucidshark scan --all --all-files && ./lucidshark overview --update  # Scan then update
```

**CI Integration (recommended):**

Add to your CI pipeline to auto-commit quality updates on merge to main.

**GitHub Actions** (using pip install):

Uses `GITHUB_TOKEN` with explicit write permissions. No secrets needed.

```yaml
jobs:
  update-quality:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Required for pushing commits
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install LucidShark
        run: pip install lucidshark
      - name: Update Quality Overview
        run: |
          lucidshark scan --all --all-files
          lucidshark overview --update
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add QUALITY.md .lucidshark/quality-history.json
          git diff --staged --quiet || git commit -m "chore: update quality overview"
          git push
```

**GitHub Actions** (using binary install):

```yaml
jobs:
  update-quality:
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: write  # Required for pushing commits
    steps:
      - uses: actions/checkout@v4
      - name: Install LucidShark
        run: curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash
      - name: Update Quality Overview
        run: |
          ./lucidshark scan --all --all-files
          ./lucidshark overview --update
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add QUALITY.md .lucidshark/quality-history.json
          git diff --staged --quiet || git commit -m "chore: update quality overview"
          git push
```

**GitLab CI** (using pip install):

Requires a Project Access Token with `write_repository` scope stored in `GL_TOKEN` variable.
Go to Settings → Access Tokens → Create token with `write_repository` scope, then add to CI/CD Variables.

```yaml
update-quality:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - pip install lucidshark
    - lucidshark scan --all --all-files
    - lucidshark overview --update
    - git config user.name "GitLab CI"
    - git config user.email "gitlab-ci@${CI_SERVER_HOST}"
    - git remote set-url origin "https://oauth2:${GL_TOKEN}@${CI_SERVER_HOST}/${CI_PROJECT_PATH}.git"
    - git add QUALITY.md .lucidshark/quality-history.json
    - git diff --staged --quiet || git commit -m "chore: update quality overview"
    - git push origin HEAD:$CI_COMMIT_BRANCH
```

**Bitbucket Pipelines** (using pip install):

Requires an SSH keypair with write access. Go to Repository Settings → Access keys → Add key (with write permission), then add the private key to Repository Settings → SSH keys.

```yaml
pipelines:
  branches:
    main:
      - step:
          name: Update Quality Overview
          script:
            - pip install lucidshark
            - lucidshark scan --all --all-files
            - lucidshark overview --update
            - git config user.name "Bitbucket Pipelines"
            - git config user.email "pipelines@bitbucket.org"
            - git add QUALITY.md .lucidshark/quality-history.json
            - git diff --staged --quiet || git commit -m "chore: update quality overview"
            - git push origin main
```

**Azure DevOps** (using pip install):

Grant the build service "Contribute" permission: Project Settings → Repositories → Security → [Build Service] → Contribute: Allow. Checkout with `persistCredentials: true`.

```yaml
trigger:
  branches:
    include:
      - main

steps:
  - checkout: self
    persistCredentials: true  # Required for pushing

  - script: |
      pip install lucidshark
      lucidshark scan --all --all-files
      lucidshark overview --update
      git config user.name "Azure Pipelines"
      git config user.email "azuredevops@microsoft.com"
      git add QUALITY.md .lucidshark/quality-history.json
      git diff --staged --quiet || git commit -m "chore: update quality overview"
      git push origin HEAD:$(Build.SourceBranchName)
    displayName: Update Quality Overview
```

**Output file:** `QUALITY.md` at project root (configurable via `overview.file` in config)

**History file:** `.lucidshark/quality-history.json` (tracks up to 90 snapshots for trend analysis)

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All checks passed |
| 1 | A `fail_on` rule in `lucidshark.yml` failed (including coverage `below_threshold` and duplication `above_threshold`), an issue is at or above `--fail-on`, or a mandatory tool was skipped or failed. Without `fail_on` or `--fail-on`, issues and threshold misses are reported but don't change the exit code |
| 2 | Tool/scanner execution error, or invalid command-line arguments |
| 3 | Config file not found or not parseable, scan path not found, a configured tool not installed, or `--coverage` without `--testing`. Invalid values in a config that parses only produce warnings |

---

## MCP Tools Reference

LucidShark exposes these tools via MCP (Model Context Protocol) for AI agent integration:

### `scan`

Run quality checks on the codebase or specific files. Supports partial scanning via the `files` parameter for faster feedback on changed files.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `domains` | array of strings | `["all"]` | Domains to check |
| `files` | array of strings | (none) | Specific files to check (relative paths). When provided, only these files are scanned. |
| `all_files` | boolean | `false` | Scan entire project instead of just changed files. By default, only uncommitted changes are scanned. |
| `fix` | boolean | `false` | Apply auto-fixes for linting and formatting issues |
| `base_branch` | string | (none) | Filter results to files changed since this branch (e.g., `origin/main`). Full analysis runs; only reporting is filtered. |
| `coverage_threshold_scope` | string | `"changed"` | With `base_branch`: apply coverage threshold to `changed`, `project`, or `both` |
| `linting_threshold_scope` | string | `"changed"` | Accepted for parity with the CLI but currently has no effect over MCP |
| `type_checking_threshold_scope` | string | `"changed"` | Accepted for parity with the CLI but currently has no effect over MCP |
| `duplication_threshold_scope` | string | `"both"` | With `base_branch`: apply duplication threshold to `changed`, `project`, or `both` |

The MCP scope defaults are fixed: they do not read `threshold_scope` from `lucidshark.yml`. The MCP `scan` tool also does not apply `fail_on`; it reports issues and per-domain status, and the agent decides what to fix.

**Valid domains:** `linting`, `type_checking`, `formatting`, `sast`, `sca`, `iac`, `container`, `testing`, `coverage`, `duplication`, `all`

**Default Behavior:** Partial scanning (changed files only) is the default. Use `all_files=true` for full project scans.

**Partial Scanning Support by Domain:**

| Domain | Partial Scan Support | Behavior |
|--------|---------------------|----------|
| `linting` | ⚠️ Partial support | Ruff/ESLint/Biome/Checkstyle/PMD/ktlint/clang-tidy/Scalafix/RuboCop/phpcs support file args; Clippy, golangci-lint, dotnet format and SwiftLint are project-wide |
| `type_checking` | ⚠️ Partial support | mypy/pyright/cppcheck/detekt support file args; tsc/SpotBugs/cargo check/go vet/dotnet build/scala compile/swift compiler/Sorbet/PHPStan scan full project |
| `formatting` | ⚠️ Partial support | Ruff Format/Prettier/ktlint/rustfmt/gofmt/clang-format/Scalafmt/SwiftFormat/RuboCop Format/PHP-CS-Fixer support file args; dotnet format is project-wide |
| `sast` | ❌ Project-wide only | OpenGrep scans the project root and gosec scans `./...`; results are narrowed to changed files only with `base_branch` |
| `sca` | ❌ Project-wide only | Trivy dependency scan is inherently project-wide |
| `iac` | ❌ Project-wide only | Checkov scans entire project |
| `testing` | ⚠️ Partial support | Jest/Vitest/Mocha/Playwright support file args; pytest (always runs the full suite via its own discovery)/Karma/Maven/cargo test/go test/dotnet test/CTest/sbt/swift test/RSpec/PHPUnit are project-wide |
| `coverage` | ⚠️ Parse data, filter output | Coverage reads existing data files; output can be filtered to changed files; Tarpaulin/JaCoCo/go cover always project-wide |
| `duplication` | ❌ Project-wide only | Duplo scans entire project to detect cross-file duplicates |

**Response format:**
```json
{
  "total_issues": 5,
  "ignored_issues": 0,
  "blocking": true,
  "summary": "5 issues found: 1 critical, 2 high, 2 medium",
  "severity_counts": {"critical": 1, "high": 2, "medium": 2},
  "domain_status": {
    "linting": {"status": "pass", "display": "Pass", "issue_count": 0, "fixable_count": 0},
    "type_checking": {"status": "fail", "display": "3 issues", "issue_count": 3, "fixable_count": 0},
    "sast": {"status": "fail", "display": "1 issues", "issue_count": 1, "fixable_count": 0},
    "sca": {"status": "fail", "display": "1 issues", "issue_count": 1, "fixable_count": 0},
    "coverage": {"status": "pass", "display": "84.2% coverage (threshold: 80%)", "coverage_percent": 84.2, "threshold": 80, "scope_is_empty": false},
    "testing": {"status": "skipped", "display": "Skipped"}
  },
  "issues_by_domain": {
    "sast": [
      {"id": "security-123", "location": "config.py:23", "severity": "critical", "title": "Hardcoded password", "fixable": false}
    ]
  },
  "instructions": [
    {
      "priority": 1,
      "action": "FIX_SECURITY_HARDCODED_SECRET",
      "summary": "Hardcoded password in config.py:23",
      "file": "config.py",
      "line": 23,
      "column": 5,
      "problem": "Hardcoded credentials detected",
      "fix_steps": ["Remove hardcoded password", "Use environment variable"],
      "suggested_fix": null,
      "current_code": null,
      "documentation_url": null,
      "related_issues": [],
      "issue_id": "security-123"
    }
  ],
  "recommended_action": "..."
}
```

Additional keys appear when relevant: `ignored_issues_by_domain` (when issues are ignored via `ignore_issues`), `coverage_summary` and `duplication_summary` (when those domains ran), and `incremental_scan` (when `base_branch` is used). Duplication entries in `domain_status` carry `duplication_percent` and `threshold`.

Instruction `priority` follows severity: critical 1, high 2, medium 3, low 4, info 5. `blocking` is `true` when any instruction has priority 1 or 2.

On failure the response is `{"error": "...", "blocking": true, "total_issues": 0}`, plus `missing_tools` and `message` when configured tools are not installed.

The `domain_status` field shows all configured domains with their status:
- `pass`: Domain executed with no issues
- `fail`: Domain executed with issues found
- `skipped`: Domain is configured but wasn't executed in this scan

**Examples:**
```
# Default: scan only changed files (uncommitted changes)
scan(domains=["linting", "type_checking"])

# Explicit full project scan
scan(domains=["all"], all_files=true)

# Scan specific files only
scan(domains=["linting", "type_checking"], files=["src/main.py", "src/utils.py"])

# Lint with auto-fix (on changed files by default)
scan(domains=["linting"], fix=true)

# Security scan - SAST and SCA always scan the whole project
scan(domains=["sca", "sast"])

# Incremental scan - filter to files changed since main
scan(domains=["all"], base_branch="origin/main")

# Incremental scan with scope configuration
scan(
    domains=["all"],
    base_branch="origin/main",
    coverage_threshold_scope="both",
    duplication_threshold_scope="both"
)
```

### `check_file`

Check a specific file and return issues with fix instructions. This is a convenience wrapper around `scan(files=[file_path])` that picks domains from the file's language:

- Every language: linting, SAST, SCA
- Python, JavaScript/TypeScript, Java/Kotlin, Rust, Go, C/C++, PHP, Swift: also type checking, formatting, testing and coverage
- Terraform: IaC only
- YAML/JSON: IaC and SAST

Because SCA is project-wide and testing may run the test suite, `check_file` can take as long as a scan.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Path to file (relative to project root) |

**When to use:**
- Feedback on a single file you just modified, without choosing domains yourself
- Checking a specific file before committing
- For a faster check, call `scan(domains=["linting", "type_checking"], files=[...])` instead

**Example:**
```
check_file(file_path="src/main.py")
```

**Note:** For checking multiple files, use `scan(files=["file1.py", "file2.py"])` instead.

### `get_fix_instructions`

Get detailed fix instructions for a specific issue. Use the `issue_id` from scan results.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_id` | string | Yes | Issue identifier from scan result |

**Example:**
```
get_fix_instructions(issue_id="security-123")
```

### `apply_fix`

Apply a Ruff auto-fix to a Python linting issue from the last scan. It runs `ruff check --select <rule> --fix <file>`, so every occurrence of that rule in the file is fixed. Non-linting issues and issues from other linters are rejected with an error. For other linters (ESLint, Biome, ...) and for formatting, use `scan(fix=true)` instead.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `issue_id` | string | Yes | Issue identifier to fix |

**Example:**
```
apply_fix(issue_id="linting-456")
```

### `get_status`

Get current LucidShark status and configuration.

**Parameters:** None

**Response format:**
```json
{
  "project_root": "/path/to/project",
  "available_tools": {
    "scanners": ["trivy", "opengrep", "gosec", "checkov"],
    "linters": ["ruff", "eslint", "biome", "clippy", "pmd", "golangci_lint"],
    "formatters": ["ruff_format", "prettier", "rustfmt", "gofmt"],
    "type_checkers": ["mypy", "pyright", "typescript", "spotbugs", "cargo_check", "go_vet"],
    "test_runners": ["pytest", "jest", "vitest", "karma", "playwright", "maven", "cargo", "go_test"],
    "coverage": ["coverage_py", "istanbul", "vitest_coverage", "jacoco", "tarpaulin", "go_cover"],
    "duplication": ["duplo"]
  },
  "enabled_domains": ["sca", "sast"],
  "cached_issues": 5
}
```

`enabled_domains` lists only the security domains (sca, sast, iac, container) enabled in `lucidshark.yml`.

### `get_help`

Get this documentation.

**Parameters:** None

**Response format:**
```json
{
  "documentation": "# LucidShark Reference Documentation...",
  "format": "markdown"
}
```

### `autoconfigure`

**AI-assisted customization of `lucidshark.yml`.** Use this after `lucidshark init` to refine the generated configuration. Returns step-by-step instructions for analyzing the codebase, installing required tools, and regenerating `lucidshark.yml` with customized settings. The AI analyzes the project, installs missing tools, asks 1-2 questions if needed, generates the configuration, validates it, and runs a verification scan.

> **Note:** `lucidshark init` is the recommended primary setup command. It generates `lucidshark.yml` automatically with all supported tools for detected languages. Use `autoconfigure` only when you need AI-guided customization beyond the defaults.

**Parameters:** None

**Usage:**
```
autoconfigure()
```

**Workflow after calling this tool:**

1. **Detect languages** -- Check for marker files (`package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `Cargo.toml`, etc.)
2. **Detect existing tools** -- Check for configs like `.eslintrc*`, `ruff.toml`, `tsconfig.json`, `mypy.ini`, `biome.json`
3. **Detect test frameworks** -- Check for `conftest.py`, `jest.config.*`, `karma.conf.*`, `playwright.config.*`
4. **Identify project-specific exclusions** -- Examine directory structure for generated code, vendored deps, etc.
5. **Ask 1-2 questions** -- Coverage threshold (if tests detected), strict vs gradual mode (for legacy codebases)
6. **Call `get_help()`** -- Read the Configuration Reference section for the full `lucidshark.yml` format
7. **Install required tools** -- Check if tools are installed, install missing ones, AND add them to dev dependencies (pyproject.toml, requirements-dev.txt, package.json, etc.)
8. **Generate `lucidshark.yml`** -- Write the config file based on detected project characteristics
9. **Call `validate_config()`** -- Verify the configuration is valid, fix any errors
10. **Restart the AI tool, then run a verification scan** -- The MCP server loads `lucidshark.yml` once at startup, so restart before calling `scan(domains=["all"])`

**Tool recommendations by language:**

| Language | Linter | Formatter | Type Checker | Test Runner | Coverage |
|----------|--------|-----------|-------------|-------------|----------|
| Python | ruff | ruff_format | mypy or pyright | pytest | coverage_py |
| JavaScript/TypeScript | eslint or biome | prettier | typescript (tsc, TypeScript only) | jest, vitest, mocha, karma, or playwright | istanbul or vitest_coverage |
| Java | checkstyle, pmd | -- | spotbugs | maven (JUnit) | jacoco |
| Kotlin | ktlint | ktlint_format | detekt | maven (JUnit) | jacoco |
| Rust | clippy | rustfmt | cargo_check | cargo | tarpaulin |
| Go | golangci_lint | gofmt | go_vet | go_test | go_cover |

**Security tools** (always recommended for all languages): trivy (SCA) + opengrep (SAST) + gosec (SAST, Go-specific)

**Response format:**
```json
{
  "instructions": "Follow these steps to configure LucidShark...",
  "analysis_steps": [
    {
      "step": 1,
      "action": "Detect languages and package managers",
      "files_to_check": ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "pom.xml", "build.gradle"],
      "what_to_look_for": "Presence of these files indicates the primary language(s)"
    },
    {
      "step": 2,
      "action": "Detect existing tools",
      "files_to_check": [".eslintrc*", "ruff.toml", "tsconfig.json", "mypy.ini", "biome.json"],
      "what_to_look_for": "Existing tool configurations to preserve"
    }
  ],
  "questions_to_ask": {
    "conditional_questions": [
      {
        "id": "coverage_threshold",
        "ask_when": "Tests detected",
        "default": 80
      },
      {
        "id": "strictness",
        "ask_when": "Large existing codebase",
        "options": ["strict (fail on issues)", "gradual (report only)"]
      }
    ]
  }
}
```

### `validate_config`

Validate a `lucidshark.yml` configuration file. Returns validation results with errors and warnings. Use after generating or modifying configuration to ensure it's valid.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `config_path` | string | No | Path to config file (relative to project root). Default: first of `.lucidshark.yml`, `.lucidshark.yaml`, `lucidshark.yml`, `lucidshark.yaml` in the project root |

**Response format:**
```json
{
  "valid": true,
  "config_path": "/path/to/project/lucidshark.yml",
  "errors": [],
  "warnings": [
    {
      "message": "Unknown key 'output.formatt'",
      "key": "output.formatt",
      "suggestion": "format"
    }
  ]
}
```

`config_path` is absolute. When no config file is found, the response is `{"valid": false, "error": "...", "errors": [], "warnings": [], "searched_for": [".lucidshark.yml", ".lucidshark.yaml", "lucidshark.yml", "lucidshark.yaml"]}`.

**Examples:**
```
validate_config()
validate_config(config_path="lucidshark.yml")
validate_config(config_path="configs/custom.yml")
```

**Validation includes:**
- YAML syntax errors
- Unknown configuration keys (with typo suggestions)
- Type errors (e.g., string where boolean expected)
- Invalid values (e.g., unknown severity level)

**Best practice:** Always call `validate_config()` after generating or modifying `lucidshark.yml` to catch configuration errors early.

---

## Configuration Reference (`lucidshark.yml`)

LucidShark auto-detects your project, but you can customize behavior with `lucidshark.yml` in your project root.

### Complete Configuration Example

```yaml
version: 1

# Project metadata
project:
  name: my-project
  languages:
    - python
    - typescript

# Pipeline configuration
pipeline:
  max_workers: 4  # Parallel execution workers

  linting:
    enabled: true
    exclude:          # Domain-level: exclude from linting only (still type-checked, tested, etc.)
      - "migrations/**"
      - "generated/**"
    tools:
      - name: ruff             # Reads its own config (pyproject.toml / ruff.toml)
      - name: eslint
      - name: biome
      - name: clippy           # For Rust projects
      - name: checkstyle       # For Java projects (style checking)
      - name: pmd              # For Java projects (bug detection, managed)
      - name: golangci_lint    # For Go projects

  type_checking:
    enabled: true
    exclude:          # Domain-level: exclude from type checking only (still linted, tested, etc.)
      - "**/*_pb2.py"
    tools:
      - name: mypy
        strict: true
      - name: pyright
      - name: typescript
      - name: spotbugs     # For Java projects (requires compiled classes)
      - name: cargo_check  # For Rust projects
      - name: go_vet       # For Go projects

  formatting:
    enabled: true
    tools:
      - name: ruff_format
      - name: prettier
      - name: rustfmt
      - name: gofmt

  security:
    enabled: true
    exclude:          # Domain-level: exclude from security only
      - "tests/**"
      - "examples/**"
    tools:
      - name: trivy
        domains: [sca, container]
      - name: opengrep
        domains: [sast]
      - name: checkov
        domains: [iac]

  testing:
    enabled: true
    command: "npm test"             # Optional: custom shell command overrides plugin-based runner
    post_command: "npm run cleanup" # Optional: runs after command completes
    # Note: test runners do not read exclude patterns; use your test runner's own config to skip tests
    tools:
      - name: pytest      # Python unit tests
      - name: jest        # JavaScript/TypeScript tests
      - name: karma       # Angular unit tests (Jasmine)
      - name: playwright  # E2E tests
      - name: maven       # Java tests (JUnit/TestNG via Maven/Gradle)
      - name: cargo       # Rust tests (cargo test)
      - name: go_test     # Go tests (go test)

  # IMPORTANT: Coverage requires testing to be enabled (see "Testing and Coverage Integration")
  # Testing produces the coverage files that coverage analysis reads
  coverage:
    enabled: true
    exclude:          # Domain-level: applied by jacoco and scoverage only
      - "scripts/**"
    tools: [coverage_py]  # coverage_py for Python, istanbul/vitest_coverage for JS/TS, jacoco for Java, tarpaulin for Rust, go_cover for Go
    threshold: 80  # Fail if coverage below this
    threshold_scope: changed  # With --base-branch: changed (default), project, or both

  duplication:
    enabled: true
    threshold: 10.0  # Max allowed duplication percentage
    threshold_scope: both  # With --base-branch: changed, project, or both (default)
    min_lines: 4     # Minimum lines for a duplicate block
    min_chars: 3     # Minimum characters per line
    exclude:         # Domain-level: exclude from duplication scan only
      - "htmlcov/**"
      - "generated/**"

# Failure thresholds (per-domain)
fail_on:
  linting: error           # error, none ("error" = any HIGH or CRITICAL issue)
  type_checking: error     # error, none
  formatting: error        # error, none
  security: high           # critical, high, medium, low, info, none
  testing: any             # any, none
  coverage: below_threshold  # below_threshold, any, none
  duplication: above_threshold  # above_threshold, any, none, or percentage (e.g., "5%")

# Alternative: single threshold for all security
# fail_on: high

# Ignore specific issues by rule ID (acknowledged but excluded from fail thresholds)
ignore_issues:
  - E501                                    # Simple form: just the rule ID (global)
  - rule_id: CVE-2021-3807                  # Structured form with reason
    reason: "Not exploitable in our context"
  - rule_id: CKV_AWS_18                     # Structured form with reason and expiry
    reason: "Access logging not required for dev buckets"
    expires: 2027-06-01
  - rule_id: S101                           # Path-scoped: only ignore in specific files
    reason: "Assert is OK in tests"
    paths:
      - "tests/**"
      - "**/test_*.py"

# Global file/directory excludes (passed to the tools that support excludes; see "Understanding exclude vs ignore_issues")
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/__pycache__/**"
  - "**/.mypy_cache/**"
  - "**/.pytest_cache/**"
  - "**/.ruff_cache/**"
  - "**/htmlcov/**"

# Global settings
settings:
  strict_mode: true  # All configured tools must run successfully (default: true)
  auto_update: true  # Binary installs: self-update when a new release exists (default: true)

# Scanner options for the security domains (passed to Trivy, OpenGrep, Checkov)
scanners:
  sca:
    ignore_unfixed: true          # Trivy: skip vulnerabilities without a fix
    skip_db_update: false         # Trivy: don't refresh the vulnerability DB
    severity: [CRITICAL, HIGH]    # Trivy: only report these severities
  container:
    images: [myapp:latest]        # Trivy: images to scan (also: --image on the CLI)
  sast:
    ruleset: [auto]               # OpenGrep: ruleset (first entry is used; default auto)
    timeout: 300                  # OpenGrep: per-file timeout in seconds
  iac:
    framework: [terraform, kubernetes]  # Checkov: limit frameworks (default: all)
    skip_checks: [CKV_AWS_18]           # Checkov: checks to skip

# Output format
output:
  format: json  # ai, json, table, sarif, summary

# Quality Overview (QUALITY.md generation)
overview:
  file: QUALITY.md           # Output file name
  history_file: .lucidshark/quality-history.json  # History storage
  history_limit: 90          # Max snapshots to keep
  domains:                   # Domains to show in the table (see the overview section for defaults)
    - linting
    - type_checking
    - sast
    - sca
    - coverage
    - duplication
  top_files: 5               # Number of top files by issues to show
  health_score: true         # Show health score section
  domain_table: true         # Show domain status table
  issue_breakdown: true      # Show issues by severity
  security_summary: true     # Show security summary
  coverage_breakdown: true   # Show coverage section
  trend_chart: true          # Show score trend chart
```

#### Strict Mode and Tool Execution

By default, LucidShark runs in **strict mode** (`settings.strict_mode: true`). This means:

- **Every configured tool must run successfully**  -  if a tool is skipped (missing prerequisites, execution failed), a HIGH severity issue is created and the scan exits 1, whatever `fail_on` says
- **Test failures are reported as HIGH severity issues**  -  they fail the scan when `fail_on.testing` is set (or via `--fail-on`)
- **Coverage with no data is reported as an issue**  -  if coverage analysis finds no coverage data, the coverage domain fails; the exit code follows `fail_on.coverage`

**Skip reasons that cause failures in strict mode:**
| Skip Reason | Example | Blocks Scan? |
|-------------|---------|--------------|
| Missing prerequisite | SpotBugs: no compiled classes | ✅ Yes |
| Execution failed | Tool timed out or crashed | ✅ Yes |
| No applicable files | No `.py` files for mypy | ❌ No (informational) |

**Configured tools that are not installed** are caught before the scan starts, whatever `strict_mode` says: the CLI prints install instructions and exits with code 3, and the MCP `scan` tool returns a `missing_tools` error. Managed tools (Trivy, OpenGrep, Checkov, gosec, PMD, Checkstyle, SpotBugs, ktlint, detekt, duplo) are downloaded instead.

**To disable strict mode** (allow tool skips without failing):
```yaml
settings:
  strict_mode: false
```

With `strict_mode: false`, a tool skipped for a missing prerequisite is reported as informational, but a tool whose execution fails (timeout, crash) still fails the scan.

**Per-tool mandatory flag** (for fine-grained control when strict_mode is false):
```yaml
settings:
  strict_mode: false  # Lenient by default

pipeline:
  type_checking:
    tools:
      - name: mypy
        mandatory: true  # This specific tool must run
      - name: pyright
        mandatory: false  # Optional
```

#### Custom Commands

The linting, type checking, formatting, testing and coverage domains support `command`, `pre_command`, and `post_command` fields for custom shell commands
(security and duplication do not). This provides a unified way to override plugin-based runners.

**`pre_command`** runs a shell command before the main command (or plugin-based runner)
executes. If the pre-command fails (non-zero exit code), it is logged as a warning but
does **not** fail the pipeline. Use this for setup steps like starting services,
generating files, or preparing the environment.

**`command`** replaces the plugin-based runner with a custom shell command. When set,
LucidShark executes the command via the shell from the project root directory and skips
plugin discovery entirely (the `tools` list is ignored). A non-zero exit code is reported
as a HIGH-severity issue for testing and coverage commands. For linting, type checking and formatting commands the output is first parsed for issues (SARIF, JSON or text), and a generic HIGH-severity issue is created only if nothing can be parsed.

**`post_command`** runs a shell command after the main command (or plugin-based runner)
completes. If the post-command fails (non-zero exit code), it is logged as a warning but
does **not** fail the pipeline.

```yaml
pipeline:
  linting:
    command: "npm run lint -- --format json"  # Custom linting
  type_checking:
    command: "npm run typecheck"              # Custom type checking
  testing:
    pre_command: "docker compose up -d db"    # Start dependencies first
    command: "docker compose run --rm app pytest -x"
    post_command: "npm run cleanup"
  coverage:
    command: "npm run test:coverage"
```

Common use cases:

- **Environment setup**: `pre_command: "docker compose up -d db"` to start dependencies before running tests
- **Code generation**: `pre_command: "npm run codegen"` to generate types or schemas before type checking
- **Custom build steps**: `command: "make test"` when your workflow requires a build system
- **Docker-based environments**: `command: "docker compose run --rm app pytest"` to run inside a container
- **Cleanup**: `post_command: "rm -rf tmp/test-artifacts"` to remove temporary files
- **Report generation**: `post_command: "node scripts/merge-reports.js"` to post-process output

### Tool Availability

⚠️ **CRITICAL FOR AUTOCONFIGURE**: Only use tools from the lists below. NEVER use tools not listed here - they are not supported by LucidShark and will cause validation errors.

LucidShark validates that all configured tools are installed before running scans. If a configured tool is missing, the scan stops before it starts (CLI exit code 3) with an error message and, for most tools, install instructions.

#### Complete List of Supported Tools

**LINTING (lucidshark.linters):**
- ✅ `ruff` - Python linter (manual install: `pip install ruff`)
- ✅ `eslint` - JavaScript/TypeScript linter (manual install: `npm install -g eslint`)
- ✅ `biome` - JavaScript/TypeScript linter (manual install: `npm install -g @biomejs/biome`)
- ✅ `clippy` - Rust linter (manual install: `rustup component add clippy`)
- ✅ `golangci_lint` - Go linter (manual install: `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest`)
- ✅ `checkstyle` - Java linter (auto-downloaded)
- ✅ `pmd` - Java linter (auto-downloaded)
- ✅ `ktlint` - Kotlin linter (auto-downloaded)
- ✅ `dotnet_format` - C# linter (included with .NET SDK)
- ✅ `clang_tidy` - C/C++ linter (manual install: `brew install llvm` or `apt install clang-tidy`)
- ✅ `scalafix` - Scala linter (manual install: `cs install scalafix`)
- ✅ `swiftlint` - Swift linter (manual install: `brew install swiftlint`)
- ✅ `rubocop` - Ruby linter (manual install: `gem install rubocop`)
- ✅ `phpcs` - PHP linter (manual install: `composer require --dev squizlabs/php_codesniffer`)

**TYPE_CHECKING (lucidshark.type_checkers):**
- ✅ `mypy` - Python type checker (manual install: `pip install mypy`)
- ✅ `pyright` - Python type checker (manual install: `pip install pyright`)
- ✅ `typescript` - TypeScript type checker (manual install: `npm install -g typescript`)
- ✅ `spotbugs` - Java type checker (auto-downloaded)
- ✅ `detekt` - Kotlin static analyzer (auto-downloaded)
- ✅ `cargo_check` - Rust type checker (included with rustup)
- ✅ `go_vet` - Go type checker (included with Go toolchain)
- ✅ `dotnet_build` - C# type checker (included with .NET SDK)
- ✅ `cppcheck` - C/C++ static analyzer (manual install: `brew install cppcheck` or `apt install cppcheck`)
- ✅ `scala_compile` - Scala type checker (via sbt/mvn/gradle)
- ✅ `swift_compiler` - Swift type checker (included with Xcode / swift.org toolchain)
- ✅ `sorbet` - Ruby type checker (manual install: `gem install sorbet`)
- ✅ `phpstan` - PHP type checker (manual install: `composer require --dev phpstan/phpstan`)

**TESTING (lucidshark.test_runners):**
- ✅ `pytest` - Python test runner (manual install: `pip install pytest`)
- ✅ `jest` - JavaScript/TypeScript test runner (manual install: `npm install jest`)
- ✅ `vitest` - JavaScript/TypeScript test runner (manual install: `npm install vitest`)
- ✅ `mocha` - JavaScript/TypeScript test runner (manual install: `npm install mocha`)
- ✅ `karma` - JavaScript/TypeScript test runner (manual install: `npm install karma`)
- ✅ `playwright` - JavaScript/TypeScript E2E test runner (manual install: `npm install @playwright/test`)
- ✅ `maven` - Java/Kotlin test runner (manual install: `brew install maven` or download)
- ✅ `cargo` - Rust test runner (included with rustup)
- ✅ `go_test` - Go test runner (included with Go toolchain)
- ✅ `dotnet_test` - C# test runner (included with .NET SDK)
- ✅ `ctest` - C/C++ test runner (included with CMake)
- ✅ `sbt` - Scala test runner (manual install: `cs install sbt`)
- ✅ `swift_test` - Swift test runner (included with Xcode / swift.org toolchain)
- ✅ `rspec` - Ruby test runner (manual install: `gem install rspec`)
- ✅ `phpunit` - PHP test runner (manual install: `composer require --dev phpunit/phpunit`)

**COVERAGE (lucidshark.coverage):**
- ✅ `coverage_py` - Python coverage (manual install: `pip install coverage pytest-cov`)
- ✅ `istanbul` - JavaScript/TypeScript coverage (manual install: `npm install nyc`)
- ✅ `vitest_coverage` - JavaScript/TypeScript coverage (manual install: `npm install @vitest/coverage-v8`)
- ✅ `jacoco` - Java/Kotlin coverage (Maven/Gradle plugin in pom.xml/build.gradle)
- ✅ `tarpaulin` - Rust coverage (manual install: `cargo install cargo-tarpaulin`)
- ✅ `go_cover` - Go coverage (included with Go toolchain)
- ✅ `dotnet_coverage` - C# coverage (included with .NET SDK)
- ✅ `gcov` - C coverage (included with GCC)
- ✅ `lcov` - C++ coverage (manual install: `brew install lcov` or `apt install lcov`)
- ✅ `scoverage` - Scala coverage (sbt/Maven plugin)
- ✅ `swift_coverage` - Swift coverage (included with Xcode / swift.org toolchain)
- ✅ `simplecov` - Ruby coverage (manual install: `gem install simplecov`)
- ✅ `phpunit_coverage` - PHP coverage (via PHPUnit with Xdebug/PCOV)

**FORMATTING (lucidshark.formatters):**
- ✅ `ruff_format` - Python formatter (manual install: `pip install ruff`)
- ✅ `prettier` - JavaScript/TypeScript formatter (manual install: `npm install -g prettier`)
- ✅ `rustfmt` - Rust formatter (manual install: `rustup component add rustfmt`)
- ✅ `gofmt` - Go formatter (included with Go toolchain)
- ✅ `ktlint_format` - Kotlin formatter (auto-downloaded)
- ✅ `dotnet_format_whitespace` - C# formatter (included with .NET SDK)
- ✅ `clang_format` - C/C++ formatter (manual install: `brew install clang-format` or `apt install clang-format`)
- ✅ `scalafmt` - Scala formatter (manual install: `cs install scalafmt`)
- ✅ `swiftformat` - Swift formatter (manual install: `brew install swiftformat`)
- ✅ `rubocop_format` - Ruby formatter (manual install: `gem install rubocop`)
- ✅ `php_cs_fixer` - PHP formatter (manual install: `composer require --dev friendsofphp/php-cs-fixer`)

**SECURITY SCANNERS (lucidshark.scanners):**
- ✅ `trivy` - SCA/Container scanner (auto-downloaded)
- ✅ `opengrep` - SAST scanner (auto-downloaded)
- ✅ `gosec` - Go SAST scanner (auto-downloaded)
- ✅ `checkov` - IaC scanner (auto-downloaded)

**DUPLICATION (lucidshark.duplication):**
- ✅ `duplo` - Code duplication detector (auto-downloaded)

#### Auto-Downloaded Tools (No Manual Install Required)

The following tools are **automatically downloaded** by LucidShark:

| Tool | Domain | Description |
|------|--------|-------------|
| `trivy` | Security (SCA, Container) | Vulnerability scanner for dependencies and containers |
| `opengrep` | Security (SAST) | Static analysis for code security patterns |
| `gosec` | Security (SAST) | Go-specific security scanner with CWE-mapped rules |
| `checkov` | Security (IaC) | Infrastructure-as-Code security scanner |
| `duplo` | Duplication | Code duplication detection |
| `pmd` | Linting (Java) | Bug detection, design issues, complexity analysis |
| `checkstyle` | Linting (Java) | Style checking with Google or custom checks |
| `spotbugs` | Type Checking (Java) | Static analysis for bugs in compiled Java bytecode |
| `ktlint` | Linting/Formatting (Kotlin) | Kotlin linter and formatter |
| `detekt` | Type Checking (Kotlin) | Static analysis for code smells and complexity |

#### Manually Installed Tools

All other tools must be installed manually before use. If you configure a tool that isn't installed, LucidShark will fail with an error naming the missing tool (and the install command, where one is known).

**Linters:**

| Tool | Languages | Install Command |
|------|-----------|-----------------|
| `ruff` | Python | `pip install ruff` |
| `eslint` | JavaScript, TypeScript | `npm install -g eslint` |
| `biome` | JavaScript, TypeScript | `npm install -g @biomejs/biome` |
| `clippy` | Rust | `rustup component add clippy` |
| `golangci_lint` | Go | `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest` |
| `dotnet_format` | C# | Included with .NET SDK |
| `clang_tidy` | C, C++ | `brew install llvm` (macOS) or `apt install clang-tidy` |
| `scalafix` | Scala | `cs install scalafix` |
| `swiftlint` | Swift | `brew install swiftlint` |
| `rubocop` | Ruby | `gem install rubocop` |
| `phpcs` | PHP | `composer require --dev squizlabs/php_codesniffer` |

**Type Checkers:**

| Tool | Languages | Install Command |
|------|-----------|-----------------|
| `mypy` | Python | `pip install mypy` |
| `pyright` | Python | `pip install pyright` |
| `typescript` | TypeScript | `npm install -g typescript` |
| `cargo_check` | Rust | Included with Rust toolchain (`rustup`) |
| `go_vet` | Go | Included with Go toolchain |
| `dotnet_build` | C# | Included with .NET SDK |
| `cppcheck` | C, C++ | `brew install cppcheck` (macOS) or `apt install cppcheck` |
| `scala_compile` | Scala | Via sbt / Maven / Gradle |
| `swift_compiler` | Swift | Included with Xcode / swift.org toolchain |
| `sorbet` | Ruby | `gem install sorbet` |
| `phpstan` | PHP | `composer require --dev phpstan/phpstan` |

**Test Runners:**

| Tool | Languages | Install Command |
|------|-----------|-----------------|
| `pytest` | Python | `pip install pytest` |
| `jest` | JavaScript, TypeScript | `npm install jest` |
| `vitest` | JavaScript, TypeScript | `npm install vitest` |
| `mocha` | JavaScript, TypeScript | `npm install mocha` |
| `karma` | JavaScript, TypeScript | `npm install karma` |
| `playwright` | JavaScript, TypeScript | `npm install @playwright/test` |
| `maven` | Java, Kotlin | `brew install maven` (macOS) or download from maven.apache.org |
| `cargo` | Rust | Included with Rust toolchain (`rustup`) |
| `go_test` | Go | Included with Go toolchain |
| `dotnet_test` | C# | Included with .NET SDK |
| `ctest` | C, C++ | Included with CMake |
| `sbt` | Scala | `cs install sbt` |
| `swift_test` | Swift | Included with Xcode / swift.org toolchain |
| `rspec` | Ruby | `gem install rspec` |
| `phpunit` | PHP | `composer require --dev phpunit/phpunit` |

**Coverage Tools:**

| Tool | Languages | Install Command |
|------|-----------|-----------------|
| `coverage_py` | Python | `pip install coverage pytest-cov` |
| `istanbul` | JavaScript, TypeScript | `npm install nyc` |
| `vitest_coverage` | JavaScript, TypeScript | `npm install @vitest/coverage-v8` or `@vitest/coverage-istanbul` |
| `jacoco` | Java, Kotlin | Maven/Gradle plugin (configured in pom.xml/build.gradle) |
| `tarpaulin` | Rust | `cargo install cargo-tarpaulin` |
| `go_cover` | Go | Included with Go toolchain |
| `dotnet_coverage` | C# | Included with .NET SDK |
| `gcov` | C | Included with GCC |
| `lcov` | C++ | `brew install lcov` (macOS) or `apt install lcov` |
| `scoverage` | Scala | sbt/Maven plugin |
| `swift_coverage` | Swift | Included with Xcode / swift.org toolchain |
| `simplecov` | Ruby | `gem install simplecov` |
| `phpunit_coverage` | PHP | Via PHPUnit with Xdebug or PCOV |

**Formatters:**

| Tool | Languages | Install Command |
|------|-----------|-----------------|
| `ruff_format` | Python | `pip install ruff` (same as ruff linter) |
| `prettier` | JavaScript, TypeScript | `npm install -g prettier` |
| `rustfmt` | Rust | `rustup component add rustfmt` |
| `gofmt` | Go | Included with Go toolchain |
| `dotnet_format_whitespace` | C# | Included with .NET SDK |
| `clang_format` | C, C++ | `brew install clang-format` (macOS) or `apt install clang-format` |
| `scalafmt` | Scala | `cs install scalafmt` |
| `swiftformat` | Swift | `brew install swiftformat` |
| `rubocop_format` | Ruby | `gem install rubocop` (same as rubocop linter) |
| `php_cs_fixer` | PHP | `composer require --dev friendsofphp/php-cs-fixer` |

#### Validation Behavior

- Validation runs at the **start** of every scan (both CLI and MCP)
- Only tools **explicitly configured** in `lucidshark.yml` are validated
- Auto-detected tools (when no `tools` array is specified) are not validated
- Missing tools cause immediate failure with exit code 3 (CLI) or error response (MCP)

**Example error message:**

```
Error: Missing required tools

The following tools are configured but not installed:

  [linting] ruff
    Install: pip install ruff

  [type_checking] mypy
    Install: pip install mypy

Please install the missing tools and try again.

Note: Security tools (trivy, opengrep, gosec, checkov), duplo, pmd, checkstyle,
spotbugs, ktlint and detekt are downloaded automatically - no manual installation required.
```

### Common Configuration Examples

Copy-paste-ready configs for common project setups.

#### Python Only (Minimal)

Linting with Ruff and type checking with mypy. Good starting point for any Python project.

```yaml
version: 1
project:
  name: my-python-app
  languages: [python]
pipeline:
  linting:
    enabled: true
    tools:
      - name: ruff
  type_checking:
    enabled: true
    tools:
      - name: mypy
fail_on:
  linting: error
  type_checking: error
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/__pycache__/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/.mypy_cache/**"
  - "**/.ruff_cache/**"
  - "**/*.egg-info/**"
  - "**/htmlcov/**"
  - "**/dist/**"
  - "**/build/**"
```

#### TypeScript Only (Minimal)

Linting with ESLint and type checking with tsc. Works for any TypeScript or JavaScript project.

```yaml
version: 1
project:
  name: my-ts-app
  languages: [typescript, javascript]
pipeline:
  linting:
    enabled: true
    tools:
      - name: eslint
  type_checking:
    enabled: true
    tools:
      - name: typescript
fail_on:
  linting: error
  type_checking: error
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/node_modules/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/coverage/**"
```

#### Python with Testing and Coverage

Full Python quality pipeline: Ruff, mypy, pytest, and coverage.py with an 80% threshold.

```yaml
version: 1
project:
  name: my-python-app
  languages: [python]
pipeline:
  linting:
    enabled: true
    tools:
      - name: ruff
  type_checking:
    enabled: true
    tools:
      - name: mypy
        strict: true
  testing:
    enabled: true
    tools:
      - name: pytest
  coverage:
    enabled: true
    tools:
      - name: coverage_py
    threshold: 80
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/__pycache__/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/.mypy_cache/**"
  - "**/.pytest_cache/**"
  - "**/.ruff_cache/**"
  - "**/*.egg-info/**"
  - "**/.eggs/**"
  - "**/htmlcov/**"
  - "**/.tox/**"
  - "**/dist/**"
  - "**/build/**"
```

#### TypeScript Full Stack

ESLint, tsc, Jest, and Istanbul coverage. Suitable for React, Next.js, or Node.js projects.

```yaml
version: 1
project:
  name: my-fullstack-app
  languages: [typescript, javascript]
pipeline:
  linting:
    enabled: true
    tools:
      - name: eslint
  type_checking:
    enabled: true
    tools:
      - name: typescript
  testing:
    enabled: true
    tools:
      - name: jest
  coverage:
    enabled: true
    tools:
      - name: istanbul
    threshold: 80
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/node_modules/**"
  - "**/dist/**"
  - "**/build/**"
  - "**/coverage/**"
  - "**/.next/**"
  - "**/.nuxt/**"
```

#### Security Only (Any Language)

Dependency vulnerability scanning (Trivy SCA) and code security patterns (OpenGrep SAST, gosec for Go). No language-specific tools needed.

```yaml
version: 1
project:
  name: my-project
pipeline:
  security:
    enabled: true
    tools:
      - name: trivy
        domains: [sca]
      - name: opengrep
        domains: [sast]
fail_on:
  security: high
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/node_modules/**"
  - "**/__pycache__/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/dist/**"
  - "**/build/**"
```

#### Java Project

Checkstyle and PMD for linting, SpotBugs for type/bug analysis, Maven for testing, and JaCoCo for coverage. Checkstyle enforces coding style, while PMD detects bugs, design issues, and complexity problems.

```yaml
version: 1
project:
  name: my-java-app
  languages: [java]
pipeline:
  linting:
    enabled: true
    tools:
      - name: checkstyle
      - name: pmd
  type_checking:
    enabled: true
    tools:
      - name: spotbugs
  testing:
    enabled: true
    tools:
      - name: maven
    # Optional: skip integration tests by overriding the maven runner's command
    # command: "mvn test jacoco:report -B -DskipITs"
  coverage:
    enabled: true
    tools:
      - name: jacoco
    threshold: 80
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/target/**"
  - "**/.gradle/**"
  - "**/build/**"
```

#### Rust Project

Clippy for linting, cargo check for type checking, cargo test for testing, and Tarpaulin for coverage.

```yaml
version: 1
project:
  name: my-rust-app
  languages: [rust]
pipeline:
  linting:
    enabled: true
    tools:
      - name: clippy
  type_checking:
    enabled: true
    tools:
      - name: cargo_check
  testing:
    enabled: true
    tools:
      - name: cargo
  coverage:
    enabled: true
    tools:
      - name: tarpaulin
    threshold: 80
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/target/**"
```

#### Go Project

golangci-lint for linting, go vet for type checking, go test for testing, gofmt for formatting, and go cover for coverage.

```yaml
version: 1
project:
  name: my-go-app
  languages: [go]
pipeline:
  linting:
    enabled: true
    tools:
      - name: golangci_lint
  formatting:
    enabled: true
    tools:
      - name: gofmt
  type_checking:
    enabled: true
    tools:
      - name: go_vet
  testing:
    enabled: true
    tools:
      - name: go_test
  coverage:
    enabled: true
    tools:
      - name: go_cover
    threshold: 80
fail_on:
  linting: error
  type_checking: error
  testing: any
  coverage: below_threshold
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/vendor/**"
```

### Configuration Sections

#### `project`

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Project name |
| `languages` | array | Detected/specified languages |

#### `pipeline`

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `max_workers` | int | 4 | Maximum parallel workers |
| `linting.enabled` | bool | true | Enable linting |
| `linting.exclude` | array | [] | Patterns to exclude from linting (combined with global `exclude`) |
| `linting.threshold_scope` | string | "changed" | With `--base-branch`: apply threshold to `changed`, `project`, or `both` |
| `linting.tools` | array | (auto) | List of linting tools |
| `type_checking.enabled` | bool | true | Enable type checking |
| `type_checking.exclude` | array | [] | Patterns to exclude from type checking (combined with global `exclude`) |
| `type_checking.threshold_scope` | string | "changed" | With `--base-branch`: apply threshold to `changed`, `project`, or `both` |
| `type_checking.tools` | array | (auto) | List of type checkers |
| `formatting.enabled` | bool | true | Enable formatting checks |
| `formatting.exclude` | array | [] | Patterns to exclude from formatting checks (combined with global `exclude`) |
| `formatting.threshold_scope` | string | "changed" | With `--base-branch`: apply threshold to `changed`, `project`, or `both` |
| `formatting.tools` | array | (auto) | List of formatters |
| `security.enabled` | bool | true | Enable security scanning |
| `security.exclude` | array | [] | Patterns to exclude from security scanning, added to the global excludes |
| `security.tools` | array | (auto) | Security tools with domains |
| `linting.pre_command` | string | (none) | Shell command to run before linting starts |
| `linting.command` | string | (none) | Custom shell command (overrides plugin-based runner) |
| `linting.post_command` | string | (none) | Shell command to run after linting completes |
| `type_checking.pre_command` | string | (none) | Shell command to run before type checking starts |
| `type_checking.command` | string | (none) | Custom shell command (overrides plugin-based runner) |
| `type_checking.post_command` | string | (none) | Shell command to run after type checking completes |
| `formatting.pre_command` / `command` / `post_command` | string | (none) | Same as for linting |
| `testing.enabled` | bool | true | Enable test execution |
| `testing.pre_command` | string | (none) | Shell command to run before tests start (e.g., start services) |
| `testing.command` | string | (none) | Custom shell command to run tests (overrides plugin-based runner) |
| `testing.post_command` | string | (none) | Shell command to run after tests complete (cleanup, reports, etc.) |
| `testing.exclude` | array | [] | Accepted, but test runners do not read exclude patterns; use the runner's own config to skip tests |
| `testing.tools` | array | (auto) | Test frameworks |
| `coverage.enabled` | bool | false | Enable coverage analysis |
| `coverage.pre_command` | string | (none) | Shell command to run before coverage analysis starts |
| `coverage.command` | string | (none) | Custom shell command (overrides plugin-based runner) |
| `coverage.post_command` | string | (none) | Shell command to run after coverage completes |
| `coverage.exclude` | array | [] | Patterns to exclude from coverage analysis (applied by jacoco and scoverage only) |
| `coverage.tools` | array | **required** | Coverage tools (coverage_py, istanbul, vitest_coverage, jacoco, tarpaulin, go_cover, dotnet_coverage, gcov, lcov, scoverage, swift_coverage, simplecov, phpunit_coverage) |
| `coverage.threshold` | int | 80 | Coverage percentage threshold |
| `coverage.threshold_scope` | string | "changed" | With `--base-branch`: apply threshold to `changed`, `project`, or `both` |
| `coverage.extra_args` | array | [] | Accepted but currently not used by any coverage plugin. To pass build arguments, use `testing.command` |
| `duplication.enabled` | bool | false | Enable duplication detection |
| `duplication.threshold` | float | 10.0 | Max allowed duplication percentage |
| `duplication.threshold_scope` | string | "both" | With `--base-branch`: apply threshold to `changed`, `project`, or `both`. The default `both` prevents project-wide duplication from creeping up over time. See [Incremental Scanning](incremental-scanning.md#duplication) for details. |
| `duplication.min_lines` | int | 4 | Minimum lines for a duplicate block |
| `duplication.min_chars` | int | 3 | Minimum characters per line |
| `duplication.exclude` | array | [] | Patterns to exclude from duplication scan (combined with global `exclude`) |
| `duplication.baseline` | bool | false | Only report NEW duplicates after first run |
| `duplication.cache` | bool | true | Cache processed files for faster re-runs |
| `duplication.use_git` | bool | true | Use git ls-files for file discovery when available |
| `duplication.tools` | array | (auto) | Duplication detection tools (duplo) |

`enabled` defaults to `true` for a linting, type checking, formatting, security or testing section that is present, and to `false` for coverage and duplication. A domain with no section at all runs when its CLI flag (or `--all`) is given.

#### Tool Configuration

Each tool in a pipeline section can have:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Tool identifier (ruff, mypy, trivy, etc.) |
| `strict` | bool | Strict mode. Read by mypy only; for pyright, set `typeCheckingMode = "strict"` in pyrightconfig.json or `[tool.pyright]` |
| `domains` | array | Security domains for scanner (sca, sast, iac, container) |
| `mandatory` | bool | Tool must run even when `settings.strict_mode` is false |

Tools read their own configuration files (`pyproject.toml`, `ruff.toml`, `.eslintrc*`, `tsconfig.json`, ...). Other keys on a tool entry, such as `config: path` or tool-specific options, are accepted but currently not passed to the tool. Scanner options for Trivy, OpenGrep and Checkov go under the top-level `scanners:` section (see the complete example above).

#### `fail_on`

Per-domain failure thresholds:

| Domain | Valid Values |
|--------|--------------|
| `linting` | `error`, `none` |
| `type_checking` | `error`, `none` |
| `formatting` | `error`, `none` |
| `security` | `critical`, `high`, `medium`, `low`, `info`, `none` |
| `testing` | `any`, `none` |
| `coverage` | `below_threshold`, `any`, `none` |
| `duplication` | `above_threshold`, `any`, `none`, or percentage (e.g., `5%`) |

**Severity-based values:**
- `error` (linting, type checking, formatting): Fail if any non-ignored issue in the domain is HIGH or CRITICAL. MEDIUM and LOW issues (for example most Ruff findings) do not fail the scan
- `critical` ... `info` (security): Fail if any non-ignored issue is at or above that severity
- `any` (testing, coverage, duplication): Fail on any non-ignored issue in the domain

**Threshold-based values:**
- `below_threshold` (coverage): Fail if coverage percentage is below `pipeline.coverage.threshold`
- `above_threshold` (duplication): Fail if duplication percentage exceeds `pipeline.duplication.threshold`
- `N%` (duplication): Fail if duplication percentage exceeds N

The string form (`fail_on: high`) applies to the security domains only. The CLI flag `--fail-on` overrides `fail_on` for every domain.

#### Understanding `exclude` vs `ignore_issues`

LucidShark provides two distinct mechanisms for filtering unwanted results. It's important to understand when to use each:

**`exclude` - File/Directory Level Filtering**
- **What it does**: Prevents files and directories from being scanned
- **When to use**: For build artifacts, dependencies, generated code, cache directories - anything that shouldn't be analyzed
- **Behavior**: Patterns are applied by the tools that support them: Ruff, ESLint, Checkstyle, PMD, ktlint, clang-tidy, Scalafix, RuboCop, mypy, all formatters, the security scanners (Trivy, OpenGrep, gosec, Checkov), duplo, and the jacoco and scoverage coverage plugins. Other linters and type checkers, all test runners, and the remaining coverage plugins do not read them; configure excludes in those tools' own config files
- **Performance**: Improves scan speed by reducing files to analyze
- **Example use cases**:
  - `node_modules/`, `.venv/`, `dist/`, `build/` - dependencies and build outputs
  - `**/__pycache__/**`, `**/.mypy_cache/**` - cache directories
  - `migrations/`, `*.min.js` - generated or minified code

**`ignore_issues` - Issue Level Filtering**
- **What it does**: Files are scanned normally, but specific rule violations are acknowledged and suppressed
- **When to use**: When a specific rule doesn't apply to your project or you've accepted a particular issue
- **Behavior**: Issues are still detected and appear in output (tagged as "ignored"), but don't cause failures
- **Performance**: No performance benefit - files are still fully scanned
- **Example use cases**:
  - `E501` - Line length rule that doesn't match your team's style
  - `CVE-2021-3807` - Known vulnerability that's not exploitable in your context
  - `S101` - Assert usage that's acceptable in test files

**Quick Decision Guide**:
- Don't want to scan certain files? → Use `exclude`
- Want to scan files but suppress specific rules? → Use `ignore_issues`

---

#### Understanding Global vs Domain-Level `exclude`

Within the `exclude` mechanism, you can specify patterns at two levels:

**Global `exclude` (Top-Level Configuration)**
- **What it does**: Excludes files/directories from every domain whose tools support excludes (linting, type checking, formatting, security, duplication; coverage via jacoco and scoverage). Test runners don't read exclude patterns
- **When to use**: For files that should NEVER be scanned by any tool
- **Scope**: Applies across the entire pipeline
- **Example use cases**:
  - Build outputs: `**/dist/**`, `**/build/**`, `**/target/**`
  - Dependencies: `**/node_modules/**`, `**/.venv/**`, `**/vendor/**`
  - Caches: `**/__pycache__/**`, `**/.mypy_cache/**`, `**/.ruff_cache/**`
  - Version control: `**/.git/**`

**Domain-Level `exclude` (Pipeline Section Configuration)**
- **What it does**: Excludes files/directories from ONLY that specific domain
- **When to use**: For files that should be scanned by some domains but not others
- **Scope**: Applies only to the specific pipeline section (e.g., `pipeline.linting.exclude`)
- **Example use cases**:
  - `pipeline.linting.exclude: ["migrations/**"]` - Don't lint migrations, but still type-check and test them
  - `pipeline.type_checking.exclude: ["**/*_pb2.py"]` - Don't type-check generated protobuf files, but still lint them
  - `pipeline.security.exclude: ["tests/**", "examples/**"]` - Don't run security scans on test/example code
  - `pipeline.testing.exclude` is accepted but has no effect: test runners don't read exclude patterns, so skip tests through the runner's own config

**How They Combine**:
The effective exclusions for any domain are the **union** of:
1. Global `exclude` patterns
2. `.lucidsharkignore` file patterns
3. Domain-specific `exclude` patterns

**Example Configuration**:
```yaml
# Global: Never scan these files in any domain
exclude:
  - "**/.git/**"
  - "**/node_modules/**"
  - "**/__pycache__/**"
  - "**/dist/**"
  - "**/build/**"

pipeline:
  linting:
    tools: [ruff]
    exclude:
      - "migrations/**"        # Don't lint migrations
      - "generated/**"          # Don't lint generated code

  type_checking:
    tools: [mypy]
    exclude:
      - "**/*_pb2.py"          # Don't type-check protobuf files
      - "**/*_pb2.pyi"

  security:
    exclude:
      - "tests/**"             # Don't run security scans on tests
      - "examples/**"
```

In this example:
- `dist/`, `node_modules/`, etc. are excluded from **every domain that supports excludes**
- `migrations/` is excluded from **linting only** (still type-checked, tested, scanned for security)
- Protobuf files are excluded from **type checking only** (still linted)
- Tests/examples are excluded from **security scanning only** (still linted and type-checked)

**Quick Decision Guide**:
- Should this file NEVER be scanned by anything? → Use global `exclude`
- Should this file be excluded from only specific checks? → Use domain-level `exclude`

#### `exclude`

Global array of glob patterns for files/directories to exclude. Patterns are passed to every tool that supports excludes (test runners don't, and among coverage tools only jacoco and scoverage do).

```yaml
exclude:
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/dist/**"
  - "**/__pycache__/**"
```

Domain-specific `exclude` patterns can be set in each pipeline section (e.g., `pipeline.linting.exclude`) to exclude files from only that domain. The effective exclusions for any domain are the **union** of:
1. Global `exclude` patterns (this section)
2. `.lucidsharkignore` file patterns
3. Domain-specific `exclude` patterns

See [Understanding Global vs Domain-Level `exclude`](#understanding-global-vs-domain-level-exclude) above for when to use each, and [Exclude Patterns](exclude-patterns.md) for the full reference.

**Note**: To suppress specific rule violations while still scanning files, use `ignore_issues` instead. See [Understanding `exclude` vs `ignore_issues`](#understanding-exclude-vs-ignore_issues) above.

#### `ignore_issues`

Ignore specific issues by rule ID. Ignored issues are **acknowledged** -- they still appear in output (tagged as ignored) but are excluded from `fail_on` threshold checks and do not affect the exit code.

**IMPORTANT**: `ignore_issues` suppresses specific rule violations but files are still scanned. To skip scanning files entirely (e.g., build artifacts, dependencies), use `exclude` instead. See [Understanding `exclude` vs `ignore_issues`](#understanding-exclude-vs-ignore_issues) above.

Supports both simple strings and structured objects:

```yaml
ignore_issues:
  # Simple: just the rule ID (applies globally)
  - E501
  - CVE-2021-3807

  # Structured: with optional reason and expiry
  - rule_id: CKV_AWS_18
    reason: "Access logging not required for dev buckets"
    expires: 2027-06-01

  # Path-scoped: only ignore in specific files/directories
  - rule_id: S101
    reason: "Assert is the standard way to write tests"
    paths:
      - "tests/**"
      - "**/test_*.py"
```

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `rule_id` | yes | string | Native scanner rule ID (e.g., `E501`, `CVE-2021-3807`, `CKV_AWS_1`) |
| `reason` | no | string | Why this issue is being ignored |
| `expires` | no | date | ISO date (`YYYY-MM-DD`). After this date, the ignore stops working and a warning is emitted |
| `paths` | no | list | Gitignore-style patterns to scope the ignore. If not specified or empty, the ignore applies globally |

**Finding rule IDs:**

To find the correct `rule_id` to use in your configuration, look at the scan output:

- **Security issues (SCA/SAST/IaC/Container)**: Use the CVE or GHSA identifier from the issue title
  - Example: `CVE-2026-29062`, `GHSA-72hv-8253-57qq`, `CKV_AWS_18`
  - **Do NOT use** the internal LucidShark ID (e.g., `trivy-38a779a616911baf`) - this won't match
- **Linting/Type checking issues**: Use the rule code shown in brackets
  - Example: `E501`, `F401`, `S101`, `MethodArgumentCouldBeFinal`
- **Check the `rule_id` field** in JSON/AI output formats - this is the exact value you need

**Common mistake:**
```yaml
# ❌ WRONG - using internal LucidShark ID from scan output
ignore_issues:
  - trivy-38a779a616911baf

# ✅ CORRECT - using CVE/GHSA identifier from issue title
ignore_issues:
  - rule_id: CVE-2026-29062
    reason: "Waiting for Spring Boot update"
```

**Behavior:**
- Matched issues are tagged `ignored: true` in all output formats
- Ignored issues do not count toward `fail_on` thresholds
- Path-scoped ignores only suppress issues in files matching the specified patterns
- Empty or missing `paths` = global ignore (applies to all files)
- Issues without file paths (e.g., some SCA vulnerabilities) are not matched by path-scoped ignores
- Expired ignores stop working and produce a warning
- Unmatched rule IDs (typos, stale entries) produce a warning
- Use one entry per `rule_id`. If the same `rule_id` appears twice, the later entry replaces the earlier one, so put all `paths` for a rule in a single entry

Works for issues in all domains -- linting, type checking, security, testing, coverage, and duplication. Coverage `below_threshold` and duplication `above_threshold` / `N%` checks look at the measured percentage, not at individual issues, so ignoring issues does not change them. See [Exclude Patterns](exclude-patterns.md) for detailed examples of path-scoped ignores.

#### `overview`

Configuration for quality overview generation (`QUALITY.md`):

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | true | Accepted but currently not checked: `overview --update` always writes |
| `file` | string | "QUALITY.md" | Output file path (relative to project root) |
| `history_file` | string | ".lucidshark/quality-history.json" | History file path |
| `history_limit` | int | 90 | Maximum snapshots to retain in history |
| `domains` | array | (see below) | Domains shown in the status table. Without an `overview` section, all ten domains are shown. If an `overview` section omits `domains`, formatting and testing are left out. An empty list hides every row |
| `top_files` | int | 5 | Number of top files by issue count to display (0 to disable) |
| `health_score` | bool | true | Show health score section with visual bar |
| `domain_table` | bool | true | Show domain status table with trends |
| `issue_breakdown` | bool | true | Show issues grouped by severity |
| `security_summary` | bool | true | Show security-specific summary (SAST/SCA/IaC/Container) |
| `coverage_breakdown` | bool | true | Show test coverage section |
| `trend_chart` | bool | true | Show score trend chart from history |

**Health Score Calculation:**

The health score (0-10) is calculated as:
- Start with 10.0
- Deduct for issues: Critical (-2.0 each, max -4.0), High (-1.0 each, max -3.0), Medium (-0.3 each, max -2.0), Low (-0.1 each, max -1.0)
- Coverage bonus/penalty: Above 80% up to +0.5, below 60% up to -1.0
- Duplication penalty: Above 10% up to -1.0

**Example overview output:**

```markdown
# Repository Quality Overview

> **Branch:** main | **Updated:** 2026-03-11 | **Commit:** `abc1234`

## Health Score: 8.5 / 10  ████████░░

| Domain | Status | Issues | Trend |
|--------|--------|--------|-------|
| Linting | ✓ Pass | 0 | → |
| Type Checking | ✓ Pass | 0 | ↑ -2 |
| Coverage | ✓ Pass | 0 | → |

## Issues by Severity
- 🔴 **Critical:** 0
- 🟠 **High:** 0
- 🟡 **Medium:** 3
- 🔵 **Low:** 12

## Test Coverage
**82.5%** ████████░░ ↑ +2.3%
```

### Config File Locations

LucidShark builds its configuration from up to three layers:

1. Built-in defaults
2. Global config: `$LUCIDSHARK_HOME/config/config.yml`, or `.lucidshark/config/config.yml` under the current directory when `LUCIDSHARK_HOME` is not set
3. Project config: the `--config PATH` file, or else the first of `.lucidshark.yml`, `.lucidshark.yaml`, `lucidshark.yml`, `lucidshark.yaml` in the project root

The global and project configs are deep-merged: mappings are merged key by key, lists are replaced, and the project config wins.

### Environment Variable Expansion

Use `${VAR}` or `${VAR:-default}` syntax in configuration:

```yaml
project:
  name: ${PROJECT_NAME:-my-project}
```

---

## AI Tool Setup

### Claude Code

```bash
./lucidshark init
```

This creates:
- `.mcp.json` - MCP server configuration (auto-detects lucidshark path)
- `.claude/skills/lucidshark/SKILL.md` - Proactive scanning skill for Claude
- `.claude/CLAUDE.md` - Adds a managed section with scanning instructions
- `.claude/settings.json` - A PostToolUse hook that reminds Claude to scan after code edits, and `enabledMcpjsonServers: ["lucidshark"]`
- `lucidshark.yml` - Generated for the detected languages, unless it already exists or `--no-config` is given

For Cursor, Windsurf and Aider, use `--cursor`, `--windsurf`, `--aider` or `--all-tools`; see [`lucidshark init`](#lucidshark-init--lucidshark-init) for what each writes.

Or manually create `.mcp.json`:

**For pip install:**
```json
{
  "mcpServers": {
    "lucidshark": {
      "command": "lucidshark",
      "args": ["serve", "--mcp", "."]
    }
  }
}
```

**For binary install:**
```json
{
  "mcpServers": {
    "lucidshark": {
      "command": "./lucidshark",
      "args": ["serve", "--mcp", "."]
    }
  }
}
```

**Note:** The `command` path is auto-detected by `lucidshark init`. The positional argument `"."` ensures the MCP server runs in the project directory, not where LucidShark is installed.

---

## Best Practices for AI Agents

### Developer Experience Principles

LucidShark aims to provide a **fast, practical, and informative** experience that instills confidence. When using LucidShark via MCP, follow these principles:

1. **Keep the user informed** - Always communicate what you're doing at each step
2. **Be complete** - Show results for all domains that were checked
3. **Be actionable** - Every issue should have a clear path to resolution
4. **Be consistent** - Use the same output format every time for predictability

### Communicating Progress

Before and during scans, tell the user what's happening:

- **Before scanning**: "Running linting and type checks on changed files..."
- **During multi-domain scans**: "Checking linting... type checking... security..."
- **After scanning**: Present results in the structured format below

### Output Format Requirements

After every scan, present results in this structure:

#### 1. Issues List (grouped by domain)

List all issues organized by domain. For each domain, show:
- Domain name and issue count
- Individual issues with: file:line, severity, description, fix action

Example:
```
## Linting (3 issues)
- src/utils.py:45 [MEDIUM] Unused import 'os' → Remove import
- src/main.py:12 [LOW] Line too long → Auto-fixable
- src/main.py:89 [LOW] Missing docstring → Add docstring

## Type Checking (1 issue)
- src/api.py:67 [HIGH] Type 'str | None' incompatible with 'str'

## Security
✓ No issues found

## SCA
✓ No issues found
```

#### 2. Summary (always at the end)

Conclude with a summary across all domains. **Important:** Show ALL configured domains, not just the ones that were executed. Domains that weren't run in this scan should show "Skipped" status:

```
---
**Summary**: 4 total issues (0 critical, 1 high, 1 medium, 2 low)

| Domain | Status |
|--------|--------|
| Linting | 3 issues (2 auto-fixable) |
| Type Checking | 1 issue |
| Security | ✓ Pass |
| SCA | ✓ Pass |
| Testing | ⊘ Skipped |
| Coverage | ⊘ Skipped |
| Duplication | ⊘ Skipped |

**Recommended action**: Run `scan(fix=true)` to auto-fix 2 linting issues, then address the type error.
```

The "Skipped" status indicates domains that are configured in `lucidshark.yml` but weren't included in this specific scan run. This helps users understand what checks exist vs what was actually executed.

#### 3. When All Checks Pass

Even with no issues, confirm what was checked. Show all configured domains with their status:

```
**Scan Complete**: All checks passed ✓

| Domain | Status |
|--------|--------|
| Linting | ✓ Pass |
| Type Checking | ✓ Pass |
| Security | ✓ Pass |
| SCA | ✓ Pass |
| Testing | ⊘ Skipped |
| Coverage | ⊘ Skipped |

Ready to proceed.
```

This makes it clear which domains were executed (Pass) vs which are configured but not run (Skipped).

### Recommended Workflow

1. **After code changes**: Run scan (automatically checks only changed files)
   ```
   scan(domains=["linting", "type_checking"])
   ```

2. **Before commit**: Run full scan (comprehensive)
   ```
   scan(domains=["all"], all_files=true)
   ```

3. **To fix issues**: Use auto-fix (on changed files by default)
   ```
   scan(domains=["linting"], fix=true)
   ```

4. **For detailed guidance**: Get fix instructions
   ```
   get_fix_instructions(issue_id="...")
   ```

### Default Partial Scanning

LucidShark scans only changed files (uncommitted changes) by default. This is the recommended workflow:

| Scenario | Approach | Example |
|----------|----------|---------|
| After editing files | Default scan | `scan(domains=["linting", "type_checking"])` - scans changed files automatically |
| Quick single-file check | Use check_file | `check_file(file_path="src/main.py")` |
| Scan specific files | Use files param | `scan(domains=["linting"], files=["src/a.py", "src/b.py"])` |
| Before commit | Full scan | `scan(domains=["all"], all_files=true)` |
| Security audit | Full scan | `scan(domains=["sca", "sast", "iac"], all_files=true)` |

**Note:** SCA, SAST (OpenGrep, gosec) and IaC always scan the whole project. Linters, formatters and type checkers that accept file arguments scan only changed files by default.

### Domain Selection Guidelines

| Scenario | Recommended Domains |
|----------|---------------------|
| Quick style check | `["linting"]` (scans changed files by default) |
| After editing Python | `["linting", "type_checking"]` |
| After editing TypeScript | `["linting", "type_checking"]` |
| Before commit | `["all"]` with `all_files=true` |
| Security audit | `["sca", "sast", "iac"]` with `all_files=true` |
| Pre-release | `["all"]` with `all_files=true` and `fix=true` for linting |

### Handling Issues

1. **Priority order**: Fix high-priority issues first (priority 1-2)
2. **Auto-fixable**: Use `scan(fix=true)` to apply linter and formatter fixes; `apply_fix()` fixes a single Ruff (Python) linting rule
3. **Manual fixes**: Follow `fix_steps` from instructions
4. **Re-scan**: Always re-scan after fixes to verify

### Performance Tips

- **Default is fast**: Just call `scan()` - it automatically scans only changed files
- **Narrow single-file checks**: `scan(domains=["linting", "type_checking"], files=[...])` is faster than `check_file()`, which also runs SCA and, for most languages, tests and coverage
- **Reserve full scans for commits**: Use `all_files=true` only before committing
- **SCA is always full**: Dependency scanning requires full project context
- **Auto-fix is smart**: `scan(domains=["linting"], fix=true)` fixes only changed files

---

## Supported Tools

For detailed per-language tool coverage, detection, and configuration examples, see the [Language Reference](languages/README.md).

### Linting

| Tool | Languages | Partial Scan |
|------|-----------|--------------|
| Ruff | Python | ✅ Yes |
| ESLint | JavaScript, TypeScript | ✅ Yes |
| Biome | JavaScript, TypeScript, JSON | ✅ Yes |
| Checkstyle | Java | ✅ Yes |
| PMD | Java | ✅ Yes |
| ktlint | Kotlin | ✅ Yes |
| Clippy | Rust | ❌ No (Cargo workspace) |
| golangci-lint | Go | ❌ No (runs `./...`) |
| dotnet format | C# | ❌ No (project-wide) |
| clang-tidy | C, C++ | ✅ Yes |
| Scalafix | Scala | ✅ Yes |
| SwiftLint | Swift | ❌ No (project-wide) |
| RuboCop | Ruby | ✅ Yes |
| phpcs | PHP | ✅ Yes |

All linting tools support the `files` parameter for partial scanning, except Clippy, golangci-lint, dotnet format and SwiftLint, which always run on the whole project.

### Type Checking

| Tool | Languages | Partial Scan |
|------|-----------|--------------|
| mypy | Python | ✅ Yes |
| pyright | Python | ✅ Yes |
| TypeScript (tsc) | TypeScript | ❌ No (project-wide only) |
| SpotBugs (managed) | Java | ❌ No (requires compiled classes) |
| detekt (managed) | Kotlin | ✅ Yes |
| cargo check | Rust | ❌ No (Cargo workspace) |
| go vet | Go | ❌ No (package-wide) |
| dotnet build | C# | ❌ No (project-wide) |
| cppcheck | C, C++ | ✅ Yes |
| scala compile | Scala | ❌ No (project-wide) |
| Swift compiler | Swift | ❌ No (project-wide) |
| Sorbet | Ruby | ❌ No (project-wide) |
| PHPStan | PHP | ❌ No (project-wide) |

**Note:** TypeScript (tsc) does not support file-level scanning - it always analyzes the full project based on `tsconfig.json`. SpotBugs requires compiled Java classes (run `mvn compile` or `gradle build` first). cargo check operates on the full Cargo workspace. go vet operates on Go packages. dotnet build, scala compile, Swift compiler, Sorbet and PHPStan operate on full projects/packages.

### Security Scanning

| Tool | Domains | Partial Scan |
|------|---------|--------------|
| Trivy | SCA (dependencies), Container images | ❌ No (project-wide) |
| OpenGrep | SAST (code patterns) | ❌ No (project-wide) |
| gosec | SAST (Go-specific) | ❌ No (scans `./...`, Go projects only) |
| Checkov | IaC (Terraform, K8s, CloudFormation) | ❌ No (project-wide) |

**Note:** All security scanners scan the entire project. With `base_branch` (MCP) or `--base-branch` (CLI), their results are filtered to changed files.

### Testing

| Tool | Languages | Partial Scan |
|------|-----------|--------------|
| pytest | Python | ❌ No (always runs the full suite) |
| Jest | JavaScript, TypeScript | ✅ Yes |
| Vitest | JavaScript, TypeScript | ✅ Yes |
| Mocha | JavaScript, TypeScript | ✅ Yes |
| Karma | JavaScript, TypeScript (Angular) | ❌ No (config-based) |
| Playwright | JavaScript, TypeScript (E2E) | ✅ Yes |
| Maven | Java, Kotlin (JUnit/TestNG) | ❌ No (project-wide) |
| cargo test | Rust | ❌ No (Cargo workspace) |
| go test | Go | ❌ No (package-wide) |
| dotnet test | C# | ❌ No (project-wide) |
| CTest | C, C++ | ❌ No (project-wide) |
| sbt test | Scala | ❌ No (project-wide) |
| swift test | Swift | ❌ No (project-wide) |
| RSpec | Ruby | ❌ No (project-wide) |
| PHPUnit | PHP | ❌ No (project-wide) |

**Note:** Most test runners (pytest, jest, vitest, mocha, maven, go test, dotnet test, swift test) include coverage instrumentation automatically. Others do not: the cargo runner switches to `cargo tarpaulin` when coverage is enabled, and karma and playwright coverage depends on project config. Jest, Vitest, Mocha and Playwright can run specific test files; run the full test suite before commits to catch regressions.

### Coverage

| Tool | Languages | Partial Scan |
|------|-----------|--------------|
| coverage.py | Python | ⚠️ Partial (filter output) |
| Istanbul/nyc | JavaScript, TypeScript | ⚠️ Partial (filter output) |
| Vitest coverage | JavaScript, TypeScript | ⚠️ Partial (filter output) |
| JaCoCo | Java, Kotlin | ❌ No (project-wide) |
| Tarpaulin | Rust | ❌ No (Cargo workspace) |
| go cover | Go | ❌ No (project-wide) |
| dotnet coverage | C# | ❌ No (project-wide) |
| gcov | C | ❌ No (project-wide) |
| lcov | C++ | ❌ No (project-wide) |
| Scoverage | Scala | ❌ No (project-wide) |
| swift coverage (llvm-cov) | Swift | ❌ No (project-wide) |
| SimpleCov | Ruby | ⚠️ Partial (filter output) |
| PHPUnit Clover | PHP | ⚠️ Partial (filter output) |

**Note:** Coverage plugins only parse existing coverage data files  -  they never run tests. The testing domain produces coverage files, and the coverage domain reads them. If no coverage data is found, coverage returns a `no_coverage_data` error. Coverage output can be filtered to show only changed files.

**Java Coverage (JaCoCo):** For Java projects with integration tests that require Docker or external services, skip them by overriding the test command (the maven runner normally runs `mvn test jacoco:report -B`):
```yaml
pipeline:
  testing:
    enabled: true
    tools: [maven]
    command: "mvn test jacoco:report -B -DskipITs -Ddocker.skip=true"
  coverage:
    enabled: true
    tools: [jacoco]
    threshold: 80
```

### Duplication Detection

| Tool | Languages | Partial Scan |
|------|-----------|--------------|
| Duplo | Python, Rust, Java, Kotlin, JavaScript, TypeScript, C, C++, C#, Go, Scala, Swift, Ruby, PHP, Erlang, VB, HTML, CSS | ❌ No (project-wide) |

**Note:** Duplication detection always scans the entire project to find cross-file duplicates. This means missing exclusions in either the global `exclude` list or the domain-specific `exclude` will cause it to scan build artifacts, caches, vendored code, and generated files  -  producing noisy false positives. Always ensure comprehensive exclusions are in place. Examine your project's directory structure and exclude any directories that contain non-source-code files.

All domains support `exclude`  -  the effective excludes are the union of global `exclude`, `.lucidsharkignore`, and the domain's own `exclude` patterns.

**Configuration example:**
```yaml
pipeline:
  duplication:
    enabled: true
    threshold: 10.0    # Max allowed duplication percentage
    min_lines: 4       # Minimum lines for a duplicate block
    min_chars: 3       # Minimum characters per line
    exclude:           # Patterns to exclude from duplication scan
      - "htmlcov/**"
      - "generated/**"
      - "**/vendor/**"
      - "**/migrations/**"
      - "**/*.min.js"
      - "**/*.min.css"
      - "**/__snapshots__/**"
      - "**/fixtures/**"
      - "**/testdata/**"

# IMPORTANT: Also ensure global excludes are comprehensive
exclude:
  - "**/.git/**"
  - "**/.lucidshark/**"
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/venv/**"
  - "**/__pycache__/**"
  - "**/dist/**"
  - "**/build/**"
  # Add language-specific and project-specific excludes here
```

---

## Testing and Coverage Integration

**IMPORTANT: Coverage requires testing.** The coverage domain does not run tests itself  -  it analyzes coverage files produced by the testing domain. When you enable coverage, you MUST also enable testing.

### How It Works

1. **Most test runners generate coverage data automatically**  -  pytest, jest, vitest, maven, and go test include coverage instrumentation (e.g., `jest --coverage`, `coverage run -m pytest`, `mvn test jacoco:report`, `go test -coverprofile`). Others (cargo test, karma, playwright) require separate coverage tooling
2. **Coverage plugins only parse existing data**  -  The coverage domain reads coverage files produced by the testing domain. Coverage plugins never run tests themselves
3. **Error if no coverage data found**  -  If coverage plugins cannot find existing coverage data files, they return a `no_coverage_data` error issue directing users to enable the testing domain
4. **Error if coverage without testing**  -  If you try to run coverage without testing enabled, LucidShark returns an error

### Coverage Files by Language

Test runners that support it produce coverage files that the corresponding coverage plugin reads:

| Language | Test Runner | Coverage Plugin | How Coverage Is Generated | Coverage Data File |
|----------|-------------|-----------------|--------------------------|-------------------|
| **Python** | pytest | coverage_py | pytest auto-wraps with `coverage run -m pytest` | `.coverage` |
| **JavaScript/TypeScript** | jest | istanbul | The jest runner always adds `--coverage` | `coverage/coverage-final.json` (falls back to `.nyc_output/` + `nyc report`) |
| **JavaScript/TypeScript** | vitest | vitest_coverage | `vitest run --coverage` | `coverage/coverage-summary.json` |
| **Java (Maven)** | maven | jacoco | `mvn test jacoco:report` | `target/site/jacoco/jacoco.xml` |
| **Java (Gradle)** | maven | jacoco | `gradle test jacocoTestReport` | `build/reports/jacoco/test/jacocoTestReport.xml` |
| **Rust** | cargo | tarpaulin | When coverage is enabled and tarpaulin is installed, the cargo runner runs `cargo tarpaulin --out Json --output-dir target/tarpaulin` instead of `cargo test` | `target/tarpaulin/tarpaulin-report.json` |
| **Go** | go_test | go_cover | `go test -coverprofile=coverage.out ./...` | `coverage.out` |

**Note:** For Rust, plain `cargo test` does not produce coverage data; the cargo runner switches to `cargo tarpaulin` automatically when the coverage domain is enabled and `cargo-tarpaulin` is installed. For Karma and Playwright, coverage depends on project-level configuration, not LucidShark flags.

### Configuration Requirements

When configuring coverage in `lucidshark.yml`, you MUST also enable testing:

```yaml
pipeline:
  # REQUIRED: Testing must be enabled for coverage to work
  testing:
    enabled: true
    tools: [pytest]  # or jest, maven, cargo, go_test, etc.

  # Coverage analyzes the output from testing
  coverage:
    enabled: true
    tools: [coverage_py]  # or istanbul, vitest_coverage, jacoco, tarpaulin, go_cover
    threshold: 80
```

**Error example:** The following configuration is INVALID and will fail validation:

```yaml
# INVALID: Coverage without testing
pipeline:
  testing:
    enabled: false  # ERROR: Testing must be enabled for coverage
  coverage:
    enabled: true
```

### Configuring Test Runners to Produce Coverage Reports

Coverage plugins **only parse existing data files** — they never run tests. Your test runner must be configured to produce coverage output in the format and location that the corresponding coverage plugin expects. LucidShark's built-in test runners handle this automatically for most languages, but if you use custom test commands or have non-default output paths, you must ensure the coverage data lands in the right place.

#### Python (coverage_py)

**Expected file:** `.coverage` (binary SQLite file at project root)

LucidShark's pytest runner automatically wraps pytest with `coverage run -m pytest`, which produces the `.coverage` file. If you use a custom test command, you must ensure coverage data is generated:

```yaml
# Option A: Use the built-in pytest runner (recommended, automatic coverage)
pipeline:
  testing:
    enabled: true
    tools: [pytest]
  coverage:
    enabled: true
    tools: [coverage_py]
```

If using a custom command, ensure it generates the `.coverage` file:

```yaml
# Option B: Custom test command that produces .coverage
pipeline:
  testing:
    enabled: true
    command: "coverage run -m pytest tests/"
  coverage:
    enabled: true
    tools: [coverage_py]
```

**Test runner configuration (pyproject.toml):**

```toml
[tool.coverage.run]
source = ["src"]          # IMPORTANT: Set this to your source directory
omit = ["tests/*", "*/migrations/*"]

[tool.coverage.report]
fail_under = 80
```

Or via `.coveragerc`:

```ini
[run]
source = src
omit =
    tests/*
    */migrations/*
```

**Common pitfall:** If `source` is not configured in `.coveragerc` or `pyproject.toml`, coverage.py may measure coverage of test files and third-party packages instead of your source code. LucidShark auto-detects `src/` or the package directory, but explicit configuration is more reliable.

#### JavaScript/TypeScript with Jest (istanbul)

**Expected files:** `coverage/coverage-summary.json` or `coverage/coverage-final.json` (at project root)

LucidShark's Jest runner automatically adds `--coverage`, which generates Istanbul-format reports in the `coverage/` directory.

```yaml
# Option A: Use the built-in Jest runner (recommended, automatic coverage)
pipeline:
  testing:
    enabled: true
    tools: [jest]
  coverage:
    enabled: true
    tools: [istanbul]
```

**Jest configuration (jest.config.js or package.json):**

```js
// jest.config.js
module.exports = {
  coverageDirectory: "coverage",              // DEFAULT — must match what istanbul plugin expects
  coverageReporters: ["json-summary", "text"], // json-summary (or json) is needed by LucidShark
  collectCoverageFrom: [
    "src/**/*.{js,ts,jsx,tsx}",
    "!src/**/*.d.ts",
    "!src/**/index.{js,ts}",
  ],
};
```

Or in `package.json`:

```json
{
  "jest": {
    "coverageDirectory": "coverage",
    "coverageReporters": ["json-summary", "text"],
    "collectCoverageFrom": ["src/**/*.{js,ts,jsx,tsx}"]
  }
}
```

**Common pitfall:** If `coverageDirectory` is set to a custom path (e.g., `reports/coverage/`), the istanbul plugin will not find the report. Either use the default `coverage/` directory, or use a custom test command that outputs to the expected location.

**Fallback:** If no `coverage/` directory is found, the istanbul plugin falls back to `.nyc_output/` and runs `nyc report` to generate a summary. This requires `nyc` to be installed.

#### JavaScript/TypeScript with Vitest (vitest_coverage)

**Expected files:** `coverage/coverage-summary.json` or `coverage/coverage-final.json` (at project root)

LucidShark's Vitest runner automatically adds `--coverage --coverage.reporter=json-summary`.

```yaml
# Option A: Use the built-in Vitest runner (recommended, automatic coverage)
pipeline:
  testing:
    enabled: true
    tools: [vitest]
  coverage:
    enabled: true
    tools: [vitest_coverage]
```

**Vitest configuration (vitest.config.ts):**

```ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      provider: 'v8',                         // or 'istanbul'
      reporter: ['json-summary', 'text'],      // REQUIRED: json-summary for LucidShark
      reportsDirectory: './coverage',          // DEFAULT — must match what plugin expects
      include: ['src/**/*.{js,ts,jsx,tsx}'],
    },
  },
});
```

**Common pitfall:** You must install a coverage provider: `npm install @vitest/coverage-v8 --save-dev` (or `@vitest/coverage-istanbul`). Without it, `--coverage` silently produces no output.

#### Java with Maven (jacoco)

**Expected files (Maven):** `target/site/jacoco/jacoco.xml`, `target/jacoco.xml`, or `jacoco/jacoco.xml`
**Expected files (Gradle):** `build/reports/jacoco/test/jacocoTestReport.xml`

LucidShark's Maven runner automatically runs `mvn test jacoco:report` (or `gradle test jacocoTestReport`).

```yaml
# Option A: Use the built-in Maven runner (recommended)
pipeline:
  testing:
    enabled: true
    tools: [maven]
  coverage:
    enabled: true
    tools: [jacoco]
```

**Maven configuration (pom.xml) — JaCoCo plugin must be present:**

```xml
<build>
  <plugins>
    <plugin>
      <groupId>org.jacoco</groupId>
      <artifactId>jacoco-maven-plugin</artifactId>
      <version>0.8.12</version>
      <executions>
        <execution>
          <goals><goal>prepare-agent</goal></goals>
        </execution>
        <execution>
          <id>report</id>
          <phase>test</phase>
          <goals><goal>report</goal></goals>
        </execution>
      </executions>
    </plugin>
  </plugins>
</build>
```

**Gradle configuration (build.gradle):**

```groovy
plugins {
    id 'jacoco'
}

jacocoTestReport {
    reports {
        xml.required = true   // REQUIRED: LucidShark reads XML reports
        html.required = true  // Optional: for human viewing
    }
}

test {
    finalizedBy jacocoTestReport  // Auto-generate report after tests
}
```

**Common pitfall:** If the JaCoCo plugin is not configured in `pom.xml`/`build.gradle`, `mvn test` runs tests but produces no coverage data. The plugin must be declared in the build configuration.

#### Go (go_cover)

**Expected file:** `coverage.out` (at project root)

LucidShark's go_test runner automatically adds `-coverprofile=coverage.out` when the coverage domain is enabled.

```yaml
# Option A: Use the built-in go_test runner (recommended, automatic coverage)
pipeline:
  testing:
    enabled: true
    tools: [go_test]
  coverage:
    enabled: true
    tools: [go_cover]
```

If using a custom command:

```yaml
# Option B: Custom command — must write coverage.out at project root
pipeline:
  testing:
    enabled: true
    command: "go test -coverprofile=coverage.out ./..."
  coverage:
    enabled: true
    tools: [go_cover]
```

**Common pitfall:** The `-coverprofile` flag must write to `coverage.out` at the project root. If your tests write to a different path (e.g., `build/coverage.out`), the go_cover plugin will not find it.

#### Rust (tarpaulin)

**Expected file:** `target/tarpaulin/tarpaulin-report.json`

Tarpaulin is special: it both runs tests AND produces coverage data. LucidShark's cargo runner automatically uses `cargo tarpaulin` instead of `cargo test` when the coverage domain is enabled.

```yaml
# Option A: Use the built-in cargo runner (recommended, automatic coverage)
pipeline:
  testing:
    enabled: true
    tools: [cargo]
  coverage:
    enabled: true
    tools: [tarpaulin]
```

If using a custom command:

```yaml
# Option B: Custom command — must write report to target/tarpaulin/
pipeline:
  testing:
    enabled: true
    command: "cargo tarpaulin --out json --output-dir target/tarpaulin"
  coverage:
    enabled: true
    tools: [tarpaulin]
```

**Prerequisite:** Install tarpaulin: `cargo install cargo-tarpaulin`

#### C (gcov)

**Expected files:** `coverage.info` or `lcov.info` (at project root or build directory)

```yaml
pipeline:
  testing:
    enabled: true
    tools: [ctest]
  coverage:
    enabled: true
    tools: [gcov]
```

**CMake configuration for coverage:**

```cmake
# Add coverage flags
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} --coverage")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} --coverage")

# Add a coverage target
add_custom_target(coverage
    COMMAND lcov --capture --directory . --output-file coverage.info
    COMMAND lcov --remove coverage.info '/usr/*' --output-file coverage.info
    WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
)
```

If using a custom command:

```yaml
pipeline:
  testing:
    enabled: true
    command: "cmake --build build && ctest --test-dir build --output-on-failure"
    post_command: "lcov --capture --directory build --output-file coverage.info && lcov --remove coverage.info '/usr/*' --output-file coverage.info"
  coverage:
    enabled: true
    tools: [gcov]
```

### Coverage File Path Summary

Each coverage plugin looks for files at specific paths relative to the project root. If your test runner writes coverage data to a non-default location, coverage analysis will fail with a `no_coverage_data` error.

| Plugin | Expected Path(s) | Produced By |
|--------|-------------------|-------------|
| **coverage_py** | `.coverage` | `coverage run -m pytest` |
| **istanbul** | `coverage/coverage-summary.json`, `coverage/coverage-final.json`, or `.nyc_output/` | `jest --coverage` or `nyc` |
| **vitest_coverage** | `coverage/coverage-summary.json` or `coverage/coverage-final.json` | `vitest run --coverage` |
| **jacoco** (Maven) | `target/site/jacoco/jacoco.xml`, `target/jacoco.xml` | `mvn test jacoco:report` |
| **jacoco** (Gradle) | `build/reports/jacoco/test/jacocoTestReport.xml` | `gradle test jacocoTestReport` |
| **tarpaulin** | `target/tarpaulin/tarpaulin-report.json` | `cargo tarpaulin --out json` |
| **go_cover** | `coverage.out` | `go test -coverprofile=coverage.out` |
| **gcov** | `coverage.info` or `lcov.info` (root or build dir) | `lcov --capture` after compile with `--coverage` |

### Troubleshooting: "No coverage data found"

If you see a `no_coverage_data` error:

1. **Check that testing is enabled** — coverage requires the testing domain to run first
2. **Verify the coverage file exists** — after running tests, check that the expected file (see table above) exists at the project root
3. **Check your test runner configuration** — ensure it's configured to produce coverage output (see per-language sections above)
4. **Check the output path** — if your test runner uses a custom output directory, it must match what the coverage plugin expects
5. **Check reporter format** — for JS/TS, ensure `json-summary` is in the reporters list; for Java, ensure XML reports are enabled

### CLI Usage

When running scans from the command line:

```bash
# Correct: Both testing and coverage
./lucidshark scan --testing --coverage

# Correct: Use --all (includes both testing and coverage if configured)
./lucidshark scan --all

# ERROR: Coverage without testing
./lucidshark scan --coverage  # Will fail with error
```

### MCP Usage

When using the MCP scan tool:

```
# Correct: Both testing and coverage
scan(domains=["testing", "coverage"])

# Correct: Use "all"
scan(domains=["all"])

# ERROR: Coverage without testing
scan(domains=["coverage"])  # Will return error
```

