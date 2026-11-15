# LucidShark

## 1. Problem Statement

AI coding assistants have fundamentally changed software development. Tools like Claude Code, GitHub Copilot, and Windsurf can generate hundreds of lines of code in seconds. But this speed creates a new problem: **developers cannot trust AI-generated code**.

The trust gap manifests in several ways:

- **Security vulnerabilities**: AI can introduce injection flaws, hardcoded secrets, insecure configurations
- **Code quality issues**: Linting errors, type mismatches, inconsistent patterns
- **Code duplication**: AI tends to copy-paste similar code blocks instead of reusing functions
- **Test gaps**: AI-generated code often lacks test coverage
- **Best practice violations**: AI doesn't know your team's conventions

Developers currently address this through manual review and fragmented tooling:

- Run ESLint, then Ruff, then mypy separately
- Run security scanners (Trivy, Semgrep/OpenGrep, gosec) as an afterthought
- Copy-paste error messages back to the AI for fixes
- Repeat until the code passes all checks

This workflow is **slow, manual, and error-prone**. The feedback loop between AI agents and deterministic quality tools is broken.

### 1.1 The Missing Layer

What developers need is a **trust layer** that:

1. **Auto-configures** quality tools for any codebase with a single command
2. **Unifies** linting, type checking, security, testing, coverage, and duplication detection in one pipeline
3. **Feeds back to AI agents** in real-time, instructing them to fix issues automatically

This trust layer doesn't replace existing tools - it orchestrates them and bridges the gap between deterministic analysis and AI-assisted development.

### 1.2 Vision: Guardrails for AI Coding

LucidShark is the **trust layer for AI-assisted development**. It provides:

```
./lucidshark init
→ Configures Claude Code integration
→ Detects project languages
→ Generates lucidshark.yml with all tools enabled
AI writes code → LucidShark checks → AI fixes → repeat
```

The core insight: **deterministic tools catch mistakes reliably, but the feedback loop to AI agents is broken**. LucidShark bridges this gap by letting your AI assistant configure and run quality checks.

| Traditional Workflow | LucidShark Workflow |
|---------------------|-------------------|
| AI writes code | AI writes code |
| Human runs linters manually | LucidShark runs automatically |
| Human reads error output | LucidShark formats instructions |
| Human tells AI what to fix | LucidShark tells AI what to fix |
| AI fixes, human re-runs | AI fixes, LucidShark re-checks |
| Repeat 5-10 times | Automated loop |

---

## 2. Goals

LucidShark is a **unified code quality and security scanner** with native AI agent integration. It achieves:

### 2.1 Zero-Config Initialization

```bash
./lucidshark init  # Configures Claude Code + generates lucidshark.yml
# Restart Claude Code to apply changes
```

LucidShark installs either via the install script (a project-local `./lucidshark` binary, as in most examples here) or with `pip install lucidshark` / `uvx lucidshark` (Python 3.10+), which provides a `lucidshark` command.

This single command:
- Configures Claude Code integration (MCP server, skills, hooks, CLAUDE.md)
- Detects languages by scanning file extensions and marker files
- Loads pre-built templates with all supported tools for each detected language
- Generates a complete `lucidshark.yml` configuration with all domains enabled

For advanced customization after initial setup, the `autoconfigure` MCP tool provides AI-assisted configuration refinement.

### 2.2 Unified Pipeline

A single configuration file controls:

| Domain | Tools | What It Catches |
|--------|-------|-----------------|
| **Linting** | Ruff, ESLint, Biome, Clippy, Checkstyle, PMD, ktlint, golangci-lint, dotnet format, clang-tidy, Scalafix, SwiftLint, RuboCop, phpcs | Style, code smells, bug detection |
| **Formatting** | Ruff Format, Prettier, ktlint, rustfmt, gofmt, dotnet format, clang-format, Scalafmt, SwiftFormat, RuboCop Format, PHP-CS-Fixer | Code formatting, whitespace style |
| **Type Checking** | mypy, TypeScript, Pyright, SpotBugs, detekt, cargo check, go vet, dotnet build, cppcheck, scalac, Swift compiler, Sorbet, PHPStan | Type errors, static analysis bugs |
| **Security** | Trivy, OpenGrep, gosec (Go), Checkov | Vulnerabilities, misconfigurations |
| **Testing** | pytest, Jest, Vitest, Mocha, Karma, Playwright, Maven/Gradle, cargo test, go test, dotnet test, CTest, sbt test, swift test, RSpec, PHPUnit | Test failures |
| **Coverage** | coverage.py, Istanbul, Vitest, JaCoCo, Tarpaulin, go cover, dotnet coverage, gcov/lcov, Scoverage, llvm-cov, SimpleCov, PHPUnit Clover | Coverage gaps |
| **Duplication** | Duplo | Code clones, duplicate blocks |

All results normalized to a common schema. One exit code for automation.

### 2.3 AI Agent Integration

LucidShark bridges deterministic tools and AI agents via MCP (Model Context Protocol):

```bash
# Configure Claude Code (creates MCP config and instructions)
./lucidshark init

# Then restart Claude Code for changes to take effect
```

When configured:
- LucidShark runs as an MCP server that AI tools connect to
- Issues are formatted as structured instructions for the AI
- The AI receives: "Fix issue X in file Y by doing Z"
- Automatic feedback loop until code passes

---

## 3. Non-Goals

LucidShark focuses on orchestration and integration, not reimplementing tools:

### 3.1 Not a Scanner/Linter

LucidShark does **not** implement:
- Custom linting rules (uses ESLint, Ruff, etc.)
- Custom security scanning (uses Trivy, OpenGrep, gosec, etc.)
- Custom test runners (uses pytest, Jest, Vitest, Mocha, etc.)

It orchestrates existing best-in-class tools.

### 3.2 Not a Dashboard

LucidShark is **CLI-first**:
- No web dashboard
- No hosted service
- No accounts or authentication

Results are local. Output uses standard mechanisms (exit codes, SARIF).

### 3.3 Not AI-Driven

AI does **not** make decisions:
- AI cannot suppress findings
- AI cannot change severity levels
- AI cannot skip checks

LucidShark uses AI to **explain and fix** issues, not to decide what matters.

---

## 4. Target Users

### 4.1 Primary: Developers Using AI Coding Tools

Developers who:
- Use Claude Code, Copilot, or similar AI assistants
- Want confidence that AI-generated code is production-ready
- Need fast feedback loops without manual tool orchestration
- Work in teams with shared quality standards

**Key motivation**: "I want to trust AI-generated code without manually running 5 different tools."

### 4.2 Secondary: DevOps Engineers

Engineers who:
- Want consistent quality gates across projects
- Need to onboard new projects quickly
- Manage tool versions and configurations

**Key motivation**: "I want to set up comprehensive quality checks in 5 minutes, not 5 hours."

### 4.3 Teams Adopting AI Coding

Teams that:
- Are increasing AI tool usage but worry about code quality
- Want guardrails before AI code reaches main branches
- Need visibility into what AI is introducing

**Key motivation**: "We want AI velocity with human-level quality."

---

## 5. Core Product Requirements

### 5.1 Project Setup

#### 5.1.1 The `init` Command (Primary Entry Point)

`lucidshark init` is the primary entry point for project setup. It does two things:

1. **Configures AI tool integration**: Claude Code by default (`.mcp.json`, `.claude/skills/`, `.claude/CLAUDE.md`, `.claude/settings.json`); `--cursor`, `--windsurf`, `--aider` and `--all-tools` configure other tools
2. **Generates `lucidshark.yml`** — detects languages, loads pre-built templates, writes complete configuration

The init command:
- Detects **languages** by scanning file extensions and marker files (e.g., `pyproject.toml`, `package.json`, `Cargo.toml`)
- Loads **pre-built templates** for each detected language with all supported tools enabled
- **Merges templates** for multi-language projects (deduplicates tools and ignore patterns)
- Enables **all domains**: linting, type checking, formatting, security (SCA/SAST/IaC), testing, coverage, duplication

Use `--no-config` to skip config generation (only configure Claude Code integration).
Use `--force` to overwrite existing `lucidshark.yml`.

#### 5.1.2 The `autoconfigure` MCP Tool (Advanced Customization)

The `autoconfigure()` MCP tool provides AI-assisted customization of the generated configuration. It can:
- Detect frameworks and existing tool configurations
- Ask targeted questions about coverage thresholds and strictness
- Regenerate `lucidshark.yml` with customized settings

#### 5.1.3 Configuration Generation

Generate `lucidshark.yml` with all settings:

```yaml
# Example lucidshark.yml
version: 1

project:
  name: my-fastapi-app
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

  formatting:
    enabled: true
    exclude:
      - "generated/**"
    tools:
      - name: ruff_format

  security:
    enabled: true
    tools:
      - name: trivy
        domains: [sca]
      - name: opengrep
        domains: [sast]

  testing:
    enabled: true
    command: "make test"       # Optional: custom shell command overrides plugin-based runner
    post_command: "make clean" # Optional: runs after command completes
    tools:
      - name: pytest

  coverage:
    enabled: true
    threshold: 80
    tools:
      - name: coverage_py

  duplication:
    enabled: true
    threshold: 10.0  # Max allowed duplication percentage
    threshold_scope: both  # "changed", "project", or "both" (default)
                           # Use "both" to prevent duplication creep over time
    min_lines: 4     # Minimum lines for a duplicate block
    exclude:         # Patterns to exclude from duplication scan
      - "htmlcov/**"
    tools:
      - name: duplo

fail_on:
  linting: error
  formatting: error
  type_checking: error
  security: high
  testing: any
  coverage: below_threshold  # Fail if coverage below threshold or no coverage data found
  duplication: above_threshold  # Fail if duplication exceeds pipeline.duplication.threshold

exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.venv/**"
```

#### Custom Commands

The `linting`, `type_checking`, `formatting`, `testing` and `coverage` domains support `command`, `pre_command`, and `post_command` fields for custom shell commands (`security` and `duplication` do not):

```yaml
pipeline:
  linting:
    command: "npm run lint -- --format json"  # Custom linting command
  type_checking:
    command: "npm run typecheck"              # Custom type checking
  testing:
    pre_command: "docker compose up -d db"    # Start dependencies first
    command: "docker compose run --rm app pytest"
    post_command: "rm -rf tmp/test-artifacts"
  coverage:
    command: "npm run test:coverage"
  formatting:
    command: "npm run format:check"          # Custom formatting check
```

**`pre_command`** runs a shell command before the main command (or plugin-based runner)
executes. Failures are logged as warnings and do not fail the pipeline. Use this for
setup steps like starting services, generating files, or preparing the environment.

**`command`** replaces the plugin-based runner with a custom shell command. When set,
LucidShark runs the command from the project root and skips plugin discovery entirely. A
non-zero exit code from `testing.command` is reported as a HIGH-severity issue. For linting, type checking and formatting commands the output is parsed for issues (SARIF, JSON or text), with a generic MEDIUM issue if nothing can be parsed; a failing coverage command is reported as MEDIUM.

**`post_command`** runs after the main command (or plugin-based runner) completes.
Failures are logged as warnings and do not fail the pipeline.

### 5.2 The `scan` Command

```bash
./lucidshark scan [--fix] [--format FORMAT]
```

Without a domain flag, the CLI runs only the security domains (`sca`, `sast`, `iac`, `container`) enabled in `lucidshark.yml`. Linting, type checking, formatting, testing, coverage and duplication run only when their flag (e.g. `--linting`) or `--all` is given; a single non-security flag such as `--linting` runs only that domain. The MCP `scan` tool defaults to `domains=["all"]`.

#### 5.2.1 Pipeline Execution

Execute the configured pipeline in order:

1. **Linting** → Run configured linters
2. **Formatting** → Check code formatting
3. **Type Checking** → Run type checkers
4. **Security** → Run security scanners
5. **Testing** → Run test suites
6. **Coverage** → Check coverage thresholds (fails automatically if tests failed)
7. **Duplication** → Detect code clones

Each stage produces normalized results. Stages can run in parallel where independent.

#### 5.2.2 Partial Scanning (Default Behavior)

LucidShark scans only changed files (uncommitted changes) by default. Use `--all-files` (CLI) or `all_files=true` (MCP) for full project scans.

| Domain | Partial Scan Support | Behavior |
|--------|---------------------|----------|
| **Linting** | ⚠️ Partial | Ruff/ESLint/Biome/Checkstyle/PMD/ktlint/clang-tidy/Scalafix/RuboCop/phpcs support file args; Clippy, golangci-lint (`./...`), dotnet format and SwiftLint are project-wide |
| **Formatting** | ⚠️ Partial | Ruff Format/Prettier/ktlint/rustfmt/gofmt/clang-format/Scalafmt/SwiftFormat/RuboCop Format/PHP-CS-Fixer support file args; dotnet format is project-wide |
| **Type Checking** | ⚠️ Partial | mypy/pyright/cppcheck/detekt support file args; tsc/SpotBugs/cargo check/dotnet build/scala compile/swift compiler/Sorbet/PHPStan always full; go vet runs package-wide (`./...`) |
| **SAST** | ❌ None | OpenGrep scans the project root and gosec scans `./...`; results are narrowed to changed files only with `--base-branch` |
| **SCA** | ❌ None | Trivy dependency scan always project-wide |
| **IaC** | ❌ None | Checkov always project-wide |
| **Testing** | ⚠️ Partial | Jest/Vitest/Mocha/Playwright support file args; pytest (always the full suite)/Karma/Maven/cargo test/dotnet test/CTest/sbt/swift test/RSpec/PHPUnit project-wide; go test runs package-wide (`./...`) |
| **Coverage** | ⚠️ Partial | Parses existing data, filter output; Tarpaulin/JaCoCo/dotnet coverage/Scoverage/swift coverage always project-wide; go cover parses project-wide coverprofile |

**Default workflow (partial scans):**
- After modifying files - scans changed files automatically
- During iterative development
- When fixing specific issues

**When to use full scans (`--all-files`):**
- Before committing code
- For comprehensive security audits
- For release preparation

#### 5.2.3 Unified Output

All results normalized to common schema. The JSON reporter (`--format json`, the default) emits `schema_version`, `issues`, `metadata` and `summary`, plus `coverage_summary`, `duplication_summary` and `tool_skips` when present:

```json
{
  "schema_version": "1.0",
  "issues": [
    {
      "id": "ruff-E501-abc123",
      "domain": "linting",
      "source_tool": "ruff",
      "severity": "medium",
      "rule_id": "E501",
      "title": "[E501] Line too long (120 > 88)",
      "description": "Line too long (120 > 88)",
      "recommendation": null,
      "documentation_url": "https://docs.astral.sh/ruff/rules/line-too-long",
      "file_path": "src/main.py",
      "line_start": 42,
      "line_end": 42,
      "column_start": 89,
      "column_end": 120,
      "code_snippet": null,
      "fixable": false,
      "suggested_fix": null,
      "dependency": null,
      "iac_resource": null,
      "ignored": false,
      "ignore_reason": null,
      "metadata": {}
    }
  ],
  "metadata": {
    "lucidshark_version": "0.10.0",
    "scan_started_at": "2026-01-01T12:00:00+00:00",
    "scan_finished_at": "2026-01-01T12:00:02+00:00",
    "duration_ms": 2140,
    "project_root": "/path/to/project",
    "scanners_used": [{ "name": "ruff", "domains": ["linting"], "success": true, "error": null }],
    "enabled_domains": ["linting"],
    "executed_domains": ["linting"],
    "all_files": false,
    "total_issues": 1
  },
  "summary": {
    "total": 1,
    "ignored_total": 0,
    "by_severity": { "medium": 1 },
    "by_scanner": { "linting": 1 }
  }
}
```

`summary.total`, `by_severity` and `by_scanner` (keyed by domain) count only non-ignored issues. Per-domain pass/fail/skipped status (`domain_status`) appears only in `--format ai` output and MCP responses (see 5.3.3).

#### 5.2.4 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success: no blocking issues |
| 1 | A `fail_on` rule failed (including coverage `below_threshold` and duplication `above_threshold`), an issue is at or above `--fail-on`, or a mandatory tool was skipped/failed. Without `fail_on` or `--fail-on`, issues and threshold misses are reported but don't change the exit code |
| 2 | Tool/scanner execution error, or invalid command-line arguments (argparse usage error) |
| 3 | Config file not found or not parseable, scan path not found, configured tool not installed, or `--coverage` without `--testing` |

#### 5.2.5 Auto-Fix Mode

```bash
./lucidshark scan --linting --formatting --fix
```

When `--fix` is enabled:
- Run fixable linters and formatters in fix mode (e.g. `ruff check --fix`, `eslint --fix`, `ruff format`)
- Report what was fixed
- Re-run checks to report remaining issues

### 5.3 The `serve` Command (AI Integration)

```bash
./lucidshark serve [--mcp | --watch] [--debounce MS] [PATH]
```

#### 5.3.1 MCP Server Mode

Run as an MCP (Model Context Protocol) server that AI tools can connect to:

```bash
./lucidshark serve --mcp
```

`serve` with neither `--mcp` nor `--watch` also runs the MCP server. On binary installs, `serve --mcp` checks for and applies a LucidShark update before serving unless `settings.auto_update: false` is set.

The MCP server provides 8 tools:
- `scan` - Run full pipeline or specific domains
- `check_file` - Check a specific file
- `get_fix_instructions` - Get detailed fix instructions for an issue
- `apply_fix` - Apply auto-fix for a fixable issue
- `get_status` - Get LucidShark status and configuration
- `get_help` - Get LLM-friendly documentation
- `autoconfigure` - Get AI-driven project setup instructions
- `validate_config` - Validate lucidshark.yml configuration

#### 5.3.2 File Watcher Mode

```bash
./lucidshark serve --watch
```

Watch for file changes and run checks on them:
- Changes are debounced (`--debounce MS`, default 1000); each batch of changed files is scanned with `scan(domains=["all"], files=<changed files>)`
- Each result is printed to stdout as JSON (the MCP scan response plus a `changed_files` list)

#### 5.3.3 AI Instruction Format

When serving AI agents, each issue is formatted as a flat fix instruction (`FixInstruction` in `mcp/formatter.py`). `priority` follows severity: critical 1, high 2, medium 3, low 4, info 5.

```json
{
  "priority": 2,
  "action": "FIX_SECURITY_HARDCODED_SECRET",
  "summary": "Hardcoded password detected in auth.py:23",
  "file": "src/api/auth.py",
  "line": 23,
  "column": 5,
  "problem": "Hardcoded passwords can be extracted from source code and version history.",
  "fix_steps": [
    "Move the password to an environment variable or secret store"
  ],
  "suggested_fix": null,
  "current_code": "password = \"admin123\"",
  "documentation_url": null,
  "related_issues": [],
  "issue_id": "opengrep-a1b2c3"
}
```

### 5.4 Configuration

#### 5.4.1 Configuration File

`lucidshark.yml` in project root:

```yaml
version: 1

project:
  name: string
  languages: [string]

pipeline:
  max_workers: number  # Default: 4 (parallel security scanner threads)

  linting:
    enabled: boolean
    pre_command: string   # Optional: runs before linting starts
    command: string       # Optional: custom shell command overrides plugin-based runner
    post_command: string  # Optional: runs after linting completes
    exclude: [string]  # Patterns to exclude from linting
    threshold_scope: string  # Default: "changed". Options: "changed", "project", "both" (applies with --base-branch)
    tools:
      - name: string
        mandatory: boolean  # Optional: override strict_mode for this tool
        # Other per-tool keys (e.g. config, options) are parsed but currently ignored;
        # tools read their own config files (pyproject.toml, .eslintrc, ...)

  type_checking:
    enabled: boolean
    pre_command: string   # Optional: runs before type checking starts
    command: string       # Optional: custom shell command overrides plugin-based runner
    post_command: string  # Optional: runs after type checking completes
    exclude: [string]  # Patterns to exclude from type checking
    threshold_scope: string  # Default: "changed". Options: "changed", "project", "both" (applies with --base-branch)
    tools:
      - name: string
        strict: boolean  # Read by mypy and pyright

  security:
    enabled: boolean
    exclude: [string]  # Patterns to exclude from security scanning (applied by MCP scans; the CLI currently ignores it)
    tools:
      - name: string
        domains: [sca, sast, iac, container]

  testing:
    enabled: boolean
    pre_command: string   # Optional: runs before tests start (e.g., start services)
    command: string       # Optional: custom shell command overrides plugin-based runner
    post_command: string  # Optional: runs after command completes
    exclude: [string]     # Accepted, but test runners do not read exclude patterns
    tools:
      - name: string

  coverage:
    enabled: boolean
    pre_command: string   # Optional: runs before coverage analysis starts
    command: string       # Optional: custom shell command overrides plugin-based runner
    post_command: string  # Optional: runs after coverage completes
    exclude: [string]  # Patterns to exclude from coverage analysis (applied by jacoco and scoverage only)
    threshold: number  # Default: 80
    threshold_scope: string  # Default: "changed". Options: "changed", "project", "both" (applies with --base-branch)
    tools:
      - name: string  # coverage_py for Python, istanbul/vitest_coverage for JS/TS, jacoco for Java, tarpaulin for Rust

  formatting:
    enabled: boolean
    pre_command: string   # Optional: runs before formatting check starts
    command: string       # Optional: custom shell command overrides plugin-based runner
    post_command: string  # Optional: runs after formatting check completes
    exclude: [string]  # Patterns to exclude from formatting check
    threshold_scope: string  # Accepted, but currently has no effect for formatting
    tools:
      - name: string  # ruff_format, prettier, rustfmt

  duplication:
    enabled: boolean
    exclude: [string]  # Patterns to exclude from duplication scan
    threshold: number  # Default: 10.0 (max allowed duplication %)
    threshold_scope: string  # Default: "both". Options: "changed", "project", "both"
                             # "both" prevents project-wide duplication from creeping up over time.
    min_lines: number  # Default: 4 (minimum lines for duplicate block)
    min_chars: number  # Default: 3 (minimum characters per line)
    baseline: boolean  # Default: false. Record known duplicates and report only new ones on later runs
    cache: boolean     # Default: true. Cache processed files for faster re-runs
    use_git: boolean   # Default: true. Use git ls-files for file discovery when in a git repo
    tools:
      - name: string  # duplo

# Scanner options for security domains (keys other than enabled/plugin are passed to the scanner).
# Note: a scanners.<domain> entry also enables that domain unless it sets enabled: false.
scanners:
  sca:
    ignore_unfixed: boolean   # Trivy: --ignore-unfixed
    skip_db_update: boolean   # Trivy: --skip-db-update
    severity: [string]        # Trivy: e.g. [CRITICAL, HIGH]
  container:
    images: [string]          # Trivy: images to scan (also set by --image)
  sast:
    ruleset: [string]         # OpenGrep: first entry passed as --config (default: auto)
    timeout: number           # OpenGrep: --timeout
  iac:
    framework: [string]       # Checkov: --framework (e.g. terraform, kubernetes)
    skip_checks: [string]     # Checkov: --skip-check

fail_on:
  linting: error | none        # error = fail only on HIGH/CRITICAL issues
  formatting: error | none     # error = fail only on HIGH/CRITICAL issues
  type_checking: error | none  # error = fail only on HIGH/CRITICAL issues
  security: critical | high | medium | low | info | none
  testing: any | none
  coverage: below_threshold | any | none  # Note: coverage only reads existing data; enable testing to generate coverage files
  duplication: above_threshold | any | none | percentage (e.g., "5%")

# Ignore specific issues by rule ID
ignore_issues:
  - string                          # Simple form: just the rule ID (global ignore)
  - rule_id: string                 # Structured form
    reason: string                  # Optional: why this is ignored
    expires: date                   # Optional: ISO date (YYYY-MM-DD) when this ignore expires
    paths:                          # Optional: limit ignore to specific files (gitignore-style patterns)
      - string

exclude:
  - string  # Global glob patterns. Not applied by test runners; among coverage plugins
            # only jacoco and scoverage apply them

output:
  format: ai | json | table | sarif | summary

# Global settings
settings:
  strict_mode: boolean  # Default: true  -  all configured tools must run successfully
  auto_update: boolean  # Default: true  -  binary installs check for and download new releases in the background on every command; `serve --mcp` also applies the update before serving

# Quality Overview (QUALITY.md generation)
overview:
  enabled: boolean           # Default: true  -  parsed but not currently checked
  file: string               # Default: "QUALITY.md"  -  output file name
  history_file: string       # Default: ".lucidshark/quality-history.json"
  history_limit: number      # Default: 90  -  max snapshots to keep
  domains: [string]          # Domain rows to show. No overview section, or domains: null = all 10 domains;
                             # an overview section without a domains key = all except formatting and testing;
                             # [] = no domain rows
  top_files: number          # Default: 5  -  number of top files by issues (0 to disable)
  health_score: boolean      # Default: true  -  show health score section
  domain_table: boolean      # Default: true  -  show domain status table
  issue_breakdown: boolean   # Default: true  -  show issues by severity
  security_summary: boolean  # Default: true  -  show security summary
  coverage_breakdown: boolean # Default: true  -  show coverage section
  trend_chart: boolean       # Default: true  -  show score trend chart
```

> **Note**: AI tool integration is configured via `lucidshark init`, not through lucidshark.yml.

#### 5.4.1.1 Strict Mode and Tool Execution

By default, LucidShark runs in **strict mode** (`settings.strict_mode: true`). This means:

- **Every configured tool must run successfully**  -  if a tool is skipped (not installed, missing prerequisites, execution failed), the scan fails with a HIGH severity issue
- **Testing failures block the scan**  -  if tests fail, a HIGH severity issue is created
- **Coverage with no data fails**  -  if coverage analysis finds 0 lines measured, the scan fails

| Skip Reason | Example | Blocks Scan (strict) |
|-------------|---------|---------------------|
| Tool not installed | mypy not in PATH | ✅ Yes |
| Missing prerequisite | No compiled classes for SpotBugs | ✅ Yes |
| Execution failed | Timeout, crash | ✅ Yes |
| No applicable files | No `.py` files for mypy | ❌ No (informational) |

**To disable strict mode** (allow tool skips without failing):
```yaml
settings:
  strict_mode: false
```

**Per-tool mandatory flag** (for fine-grained control when strict_mode is false):
```yaml
settings:
  strict_mode: false  # Lenient by default
pipeline:
  linting:
    tools:
      - name: ruff
        mandatory: true  # This specific tool must run
      - name: eslint
        mandatory: false  # Optional
```

Note: a tool whose execution fails (timeout, crash) still fails the scan even with `strict_mode: false` and `mandatory: false`; only skips such as "not installed" or "missing prerequisite" are relaxed.

#### 5.4.2 Exclude File

`.lucidsharkignore` supports gitignore syntax and contributes to the global exclude patterns:

```
# Dependencies
node_modules/
.venv/
vendor/

# Build artifacts
dist/
build/
*.pyc

# Generated files
*.generated.ts
```

#### 5.4.3 Inline Ignores

Support tool-native inline ignores:
- Ruff: `# noqa: E501`
- ESLint: `// eslint-disable-next-line`
- OpenGrep: `# nosemgrep`
- gosec: `// nosec G401` (Go)
- Checkov: `# checkov:skip=CKV_AWS_1`

#### 5.4.4 Issue Ignoring (`ignore_issues`)

Ignore specific issues by rule ID across all domains. Ignored issues are **acknowledged** -- they still appear in scan output (tagged as ignored) but are excluded from `fail_on` threshold checks and do not affect the exit code.

This is useful for:
- Known CVEs that are not exploitable in your context
- Accepted risks in non-production environments
- False positives from security scanners
- Linting rules that conflict with project conventions
- Rules that only apply to certain parts of the codebase (e.g., `assert` in tests)

**Configuration:**

```yaml
ignore_issues:
  # Simple form: just the rule ID (applies globally)
  - E501
  - CVE-2021-3807

  # Structured form: with reason and/or expiry
  - rule_id: CKV_AWS_18
    reason: "Access logging not required for internal dev buckets"
  - rule_id: CVE-2024-1234
    reason: "Not exploitable -- we don't use the affected API"
    expires: 2027-06-01

  # Path-scoped ignores: only apply to specific files/directories
  - rule_id: S101
    reason: "Assert statements are acceptable in test files"
    paths:
      - "tests/**"
      - "**/test_*.py"
  - rule_id: E402
    reason: "Module-level imports are fine in scripts"
    paths:
      - "scripts/**"
```

**Supported fields:**

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `rule_id` | yes | string | Native scanner rule ID (e.g., `E501`, `CVE-2021-3807`, `CKV_AWS_1`, `py/sql-injection`) |
| `reason` | no | string | Why this issue is being ignored |
| `expires` | no | date | ISO date (`YYYY-MM-DD`). After this date, the ignore stops working and a warning is emitted |
| `paths` | no | list | Gitignore-style patterns to scope the ignore. If not specified or empty, the ignore applies globally |

**Path-Scoped Ignores:**

The `paths` field limits an ignore rule to specific files or directories. This is useful when a rule violation is acceptable in some contexts but not others.

```yaml
ignore_issues:
  # Ignore assert usage (S101) only in test files
  - rule_id: S101
    reason: "Assert is the standard way to write tests"
    paths:
      - "tests/**"           # All files under tests/
      - "**/test_*.py"       # Any file starting with test_
      - "**/conftest.py"     # pytest fixtures

  # Ignore line length in generated code
  - rule_id: E501
    paths:
      - "generated/**"
      - "**/*.generated.py"

  # Ignore magic numbers in constants files
  - rule_id: PLR2004
    paths:
      - "**/constants.py"
      - "**/config.py"

  # Combine paths with expiry
  - rule_id: B101
    reason: "Temporary: assert in scripts during migration"
    expires: 2027-06-01
    paths:
      - "scripts/**"
```

**Path pattern syntax:**

The `paths` field uses gitignore-style patterns (same syntax as `exclude` and `.lucidsharkignore`):

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Match any characters except `/` | `*.py` matches `foo.py` |
| `**` | Match any directory depth | `tests/**` matches `tests/unit/test_foo.py` |
| `!` | Negate a pattern | `tests/**` + `!tests/integration/**` |
| `/` (trailing) | Match directories only | `scripts/` |

**Important:** Issues without a file path (e.g., some SCA dependency vulnerabilities) are **not** matched by path-scoped ignores. Use a global ignore (without `paths`) for such issues.

**Behavior:**

- Matched issues are tagged with `ignored: true` and `ignore_reason` in the output
- Ignored issues appear in all output formats (`json`, `table`, `sarif`, `ai`) but are visually distinguished
- Ignored issues are **excluded** from `fail_on` threshold checks (they do not affect the exit code)
- Coverage `below_threshold` and duplication `above_threshold` / `"N%"` checks use the coverage/duplication summary, not individual issues, so ignoring those issues does not change the outcome
- **One entry per `rule_id`**: if the same `rule_id` appears more than once, the last entry wins (its `paths`, `reason` and `expires` replace the earlier ones)
- **Path-scoped ignores** only suppress issues in files matching the specified patterns
- **Empty or missing `paths`** means global ignore (backward compatible)
- **Expired ignores** stop suppressing issues -- the issue is reported normally and a warning is emitted about the expired ignore entry
- **Unmatched rule IDs** (rule IDs that don't match any issue in the scan) produce a warning, helping catch typos and stale entries
- Rule IDs are matched against the `rule_id` field of `UnifiedIssue`, which uses each tool's native identifier format

**Comparison with other exclusion mechanisms:**

| Mechanism | Scope | Effect |
|-----------|-------|--------|
| `exclude` / `.lucidsharkignore` | Files/directories | Entire files skipped by scanners |
| Inline ignores (`# noqa`, `# nosemgrep`) | Single code location | Tool-native, per-line suppression |
| `ignore_issues` (global) | All occurrences of a rule | Acknowledged in output, excluded from fail thresholds |
| `ignore_issues` (with `paths`) | Rule occurrences in specific files | Same as global, but only for matching paths |

### 5.5 Tool Management

#### 5.5.1 Automatic Installation

LucidShark downloads only its **managed** tools, the first time they are needed: Trivy, OpenGrep, Checkov, gosec, PMD, Checkstyle, SpotBugs, ktlint, detekt and Duplo (logged as e.g. `Downloading Trivy v0.76.2...`).

All other tools (ruff, mypy, pyright, ESLint, Biome, Prettier, tsc, pytest, Jest, golangci-lint, Clippy, ...) are **not** installed by LucidShark. They must already be available in the project's virtualenv, `node_modules/.bin`, or on `PATH`. If a configured tool is missing, `lucidshark scan` stops before scanning with exit code 3.

#### 5.5.2 Version Pinning

LucidShark pins versions for tools it downloads directly (security scanners and duplication detection). Versions are defined in `pyproject.toml` under `[tool.lucidshark.tools]`:

```toml
# pyproject.toml
[tool.lucidshark.tools]
# Security scanners
trivy = "0.76.2"
opengrep = "1.33.1"
checkov = "3.3.20"
gosec = "2.30.0"
# Java tools
pmd = "7.29.0"
checkstyle = "14.4.0"
spotbugs = "4.10.5"
# Kotlin tools
ktlint = "1.8.0"
detekt = "1.23.8"
# Duplication detection
duplo = "0.2.0"
```

**Language-specific tools** (ruff, eslint, biome, mypy, pyright, etc.) are **not** version-pinned by LucidShark. Install these via your package manager (pip, npm, cargo) to ensure compatibility with your project. PMD, Checkstyle, SpotBugs, ktlint and detekt are exceptions  -  they are managed (auto-downloaded) like security tools, since they are distributed as cross-platform JARs/zips.

When installed as a package, LucidShark uses hardcoded fallback versions from `src/lucidshark/bootstrap/versions.py`.

#### 5.5.3 Binary Cache

Binaries are cached in `{project_root}/.lucidshark/` by default. The `LUCIDSHARK_HOME` environment variable can override this for global installations:

```
{project}/.lucidshark/
├── bin/
│   ├── trivy/{version}/trivy
│   ├── opengrep/{version}/opengrep
│   ├── checkov/{version}/checkov
│   ├── gosec/{version}/gosec
│   ├── pmd/{version}/pmd-bin-{version}/
│   ├── checkstyle/{version}/checkstyle-{version}-all.jar
│   ├── spotbugs/{version}/spotbugs-{version}/
│   ├── ktlint/{version}/ktlint-{version}.jar
│   ├── detekt/{version}/detekt-cli-{version}-all.jar
│   └── duplo/{version}/lucidshark-duplo
├── cache/
│   └── trivy/          # Vulnerability database
├── config/             # Configuration files
└── logs/               # Debug/diagnostic logs
```

---

## 6. System Architecture

### 6.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        LucidShark CLI                            │
├─────────────────────────────────────────────────────────────────┤
│  Commands                                                       │
│  ├── init           → Configure AI tool integration               │
│  ├── scan           → Pipeline execution                        │
│  ├── serve          → MCP server / file watcher                 │
│  ├── status         → Show version, platform and tool status    │
│  ├── validate       → Validate lucidshark.yml                   │
│  ├── doctor         → Health check for setup and environment    │
│  ├── help           → LLM-friendly documentation                │
│  └── overview       → Generate QUALITY.md quality overview      │
├─────────────────────────────────────────────────────────────────┤
│  Pipeline Orchestrator                                          │
│  ├── DomainRunner   (tool-domain execution: lint, typecheck...) │
│  ├── PipelineExecutor (security scanner orchestration)          │
│  ├── ParallelScannerExecutor (ThreadPool-based parallelism)     │
│  ├── Enricher pipeline (sequential post-processing)             │
│  └── Threshold evaluation (per-domain fail_on)                  │
├─────────────────────────────────────────────────────────────────┤
│  Tool Plugins                                                   │
│  ├── Linting:     RuffLinter, ESLintLinter, BiomeLinter,        │
│  │                ClippyLinter, CheckstyleLinter, PmdLinter,    │
│  │                KtlintLinter, GoLangCILintLinter,             │
│  │                DotnetFormatLinter, ClangTidyLinter,          │
│  │                ScalafixLinter, SwiftLintLinter,              │
│  │                RubocopLinter, PhpcsLinter                    │
│  ├── TypeCheck:   MypyChecker, PyrightChecker,                  │
│  │                TypeScriptChecker, SpotBugsChecker,           │
│  │                DetektChecker, CargoCheckChecker,              │
│  │                GoVetChecker, DotnetBuildChecker,              │
│  │                CppcheckChecker, ScalaCompileChecker,          │
│  │                SwiftCompilerChecker, SorbetChecker,           │
│  │                PhpstanChecker                                │
│  ├── Security:    TrivyScanner, OpenGrepScanner,                │
│  │                CheckovScanner, GosecScanner                  │
│  ├── Testing:     PytestRunner, JestRunner, VitestRunner,       │
│  │                MochaRunner, KarmaRunner, PlaywrightRunner,   │
│  │                MavenTestRunner, CargoTestRunner,              │
│  │                GoTestRunner, DotnetTestRunner,               │
│  │                CTestRunner, SbtTestRunner,                   │
│  │                SwiftTestRunner, RspecRunner,                  │
│  │                PhpunitRunner                                 │
│  ├── Coverage:    CoveragePyPlugin, IstanbulPlugin,             │
│  │                VitestCoveragePlugin, JaCoCoPlugin,            │
│  │                TarpaulinPlugin, GoCoverPlugin,               │
│  │                DotnetCoveragePlugin, GcovPlugin,             │
│  │                LcovPlugin, ScoveragePlugin,                  │
│  │                SwiftCoveragePlugin, SimpleCovPlugin,          │
│  │                PhpunitCoveragePlugin                         │
│  ├── Formatting:  RuffFormatter, PrettierFormatter,             │
│  │                RustfmtFormatter, GofmtFormatter,             │
│  │                KtlintFormatter, DotnetFormatFormatter,       │
│  │                ClangFormatFormatter, ScalafmtFormatter,      │
│  │                SwiftFormatFormatter, RubocopFormatter,       │
│  │                PhpCsFixerFormatter                           │
│  ├── Duplication: DuploPlugin                                   │
│  └── Enrichers:   (post-processing pipeline)                    │
├─────────────────────────────────────────────────────────────────┤
│  Output Layer                                                   │
│  ├── Reporters:   JSON, Table, SARIF, Summary                   │
│  └── AI Format:   Structured instructions for AI agents         │
├─────────────────────────────────────────────────────────────────┤
│  AI Integration Layer                                           │
│  ├── MCP Server:  8 tools for AI agents to invoke               │
│  ├── File Watcher: Real-time checking via watchdog              │
│  └── Instruction Formatter: Issue → actionable fix guidance     │
├─────────────────────────────────────────────────────────────────┤
│  Detection & Bootstrap                                          │
│  ├── Detection:  Languages, frameworks, tools, test frameworks  │
│  └── Bootstrap:  Binary download, version management, paths     │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Plugin Interfaces

Each domain has its own abstract base class. All plugins share common properties (`name`, `domain`, `get_version()`, `ensure_binary()`) but have domain-specific execution methods.

#### 6.2.1 LinterPlugin (`plugins/linters/base.py`)

```python
class LinterPlugin(ABC):
    def __init__(self, project_root: Optional[Path] = None, **kwargs) -> None: ...

    @property
    @abstractmethod
    def name(self) -> str: ...           # e.g., 'ruff', 'eslint'

    @property
    @abstractmethod
    def languages(self) -> List[str]: ...  # e.g., ['python']

    @property
    def domain(self) -> ToolDomain: ...  # Always ToolDomain.LINTING

    @property
    def supports_fix(self) -> bool: ...  # Default: False

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def lint(self, context: ScanContext) -> List[UnifiedIssue]: ...

    def fix(self, context: ScanContext) -> FixResult:
        """Override if linter supports auto-fix."""
```

#### 6.2.2 TypeCheckerPlugin (`plugins/type_checkers/base.py`)

```python
class TypeCheckerPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def languages(self) -> List[str]: ...
    @property
    def domain(self) -> ToolDomain: ...       # Always ToolDomain.TYPE_CHECKING
    @property
    def supports_strict_mode(self) -> bool: ...  # Default: False

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def check(self, context: ScanContext) -> List[UnifiedIssue]: ...
```

#### 6.2.3 ScannerPlugin (`plugins/scanners/base.py`)

```python
class ScannerPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...           # e.g., 'trivy', 'opengrep'
    @property
    @abstractmethod
    def domains(self) -> List[ScanDomain]: ...  # SCA, SAST, IAC, CONTAINER

    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def scan(self, context: ScanContext) -> List[UnifiedIssue]: ...
```

#### 6.2.4 TestRunnerPlugin (`plugins/test_runners/base.py`)

```python
class TestRunnerPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def languages(self) -> List[str]: ...
    @property
    def domain(self) -> ToolDomain: ...  # Always ToolDomain.TESTING

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def run_tests(self, context: ScanContext) -> TestResult: ...
```

#### 6.2.5 CoveragePlugin (`plugins/coverage/base.py`)

```python
class CoveragePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def languages(self) -> List[str]: ...
    @property
    def domain(self) -> ToolDomain: ...  # Always ToolDomain.COVERAGE

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def measure_coverage(
        self, context: ScanContext, threshold: float = 80.0,
    ) -> CoverageResult: ...
```

#### 6.2.6 DuplicationPlugin (`plugins/duplication/base.py`)

```python
class DuplicationPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    @property
    @abstractmethod
    def languages(self) -> List[str]: ...
    @property
    def domain(self) -> ToolDomain: ...  # Always ToolDomain.DUPLICATION

    @abstractmethod
    def get_version(self) -> str: ...
    @abstractmethod
    def ensure_binary(self) -> Path: ...
    @abstractmethod
    def detect_duplication(
        self, context: ScanContext, threshold: float = 10.0,
        min_lines: int = 4, min_chars: int = 3,
        exclude_patterns: Optional[List[str]] = None,
    ) -> DuplicationResult: ...
```

#### 6.2.7 EnricherPlugin (`plugins/enrichers/base.py`)

Enrichers post-process issues after scanning, adding metadata or filtering results:

```python
class EnricherPlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...  # e.g., 'dedup', 'epss', 'kev'

    @abstractmethod
    def enrich(
        self, issues: List[UnifiedIssue], context: ScanContext,
    ) -> List[UnifiedIssue]: ...
```

Enricher constraints:
- MUST NOT modify severity levels set by scanners
- MUST NOT affect exit codes
- MAY filter, augment, or reorder issues
- Run sequentially in configured order

### 6.3 Codebase Detector

The codebase detector identifies project characteristics (`detection/detector.py`):

```python
@dataclass
class LanguageInfo:
    name: str                          # Language name (lowercase)
    version: Optional[str] = None      # Detected version
    file_count: int = 0                # Number of files

@dataclass
class ToolConfig:
    tool: str                          # Tool name (e.g., 'ruff')
    config_file: Optional[Path]        # Path to config file
    config_location: Optional[str]     # 'file', 'pyproject.toml', 'package.json'

@dataclass
class ProjectContext:
    root: Path
    languages: list[LanguageInfo]         # Detected languages with metadata
    package_managers: list[str]           # ["pip", "npm", "maven"]
    frameworks: list[str]                 # ["fastapi", "react", "spring-boot"]
    existing_tools: dict[str, ToolConfig] # {"ruff": ToolConfig(...)}
    test_frameworks: list[str]            # ["pytest", "jest", "junit5"]
```

Detection modules:
- `detection/languages.py` - Detects languages via file extensions and marker files. Supports: Python, JavaScript, TypeScript, Go, Rust, Java, Kotlin, Scala, Ruby, PHP, C#, Swift, C, C++.
- `detection/frameworks.py` - Detects frameworks and test frameworks from dependency files. Supports Python (FastAPI, Django, Flask, etc.), JS/TS (React, Vue, Angular, Next, Express, etc.), Java (Spring Boot, Quarkus, Micronaut, etc.).
- `detection/tools.py` - Detects existing tool configurations (ruff, eslint, biome, mypy, pyright, prettier, trivy, jest, karma, playwright, etc.).

Detection strategy:
1. Scan for marker files (package.json, pyproject.toml, go.mod, pom.xml, etc.)
2. Count files by extension to determine primary language
3. Parse dependency files to detect frameworks and test frameworks
4. Check for existing tool configurations in config files, pyproject.toml sections, and package.json keys

### 6.4 MCP Server

The MCP server (`mcp/server.py`) exposes tools for AI agents via stdio. By default, scans only changed files (uncommitted changes).

**MCP Tools:**

| Tool | Description |
|------|-------------|
| `scan` | Run quality checks. Params: `domains` (default `["all"]`), `files`, `all_files`, `fix`, `base_branch`, `coverage_threshold_scope`, `linting_threshold_scope`, `type_checking_threshold_scope`, `duplication_threshold_scope` |
| `check_file` | Check a single file (auto-detects language and runs relevant checks) |
| `get_fix_instructions` | Get detailed fix instructions for a specific issue by ID |
| `apply_fix` | Apply auto-fix for a fixable issue (Ruff/Python linting only): runs `ruff check --select <rule> --fix <file>`, which fixes every occurrence of that rule in the file |
| `get_status` | Returns `project_root`, `available_tools`, `enabled_domains` (security domains only) and `cached_issues` |
| `get_help` | Get LucidShark documentation in markdown format |
| `autoconfigure` | Get instructions for AI-driven project configuration |
| `validate_config` | Validate a lucidshark.yml configuration file |

```python
class MCPToolExecutor:
    """Executes LucidShark operations for MCP tools."""

    async def scan(
        self,
        domains: List[str],              # ["all"], ["linting", "sast"], etc.
        files: Optional[List[str]],      # Specific files to scan
        all_files: bool = False,         # Full project scan
        fix: bool = False,               # Apply auto-fixes
        base_branch: Optional[str] = None,                   # Filter results to files changed since branch
        coverage_threshold_scope: Optional[str] = None,      # "changed" (default), "project", "both"
        linting_threshold_scope: Optional[str] = None,       # Accepted, currently no effect
        type_checking_threshold_scope: Optional[str] = None, # Accepted, currently no effect
        duplication_threshold_scope: Optional[str] = None,   # "both" (default), "changed", "project"
        on_progress: Optional[...],      # Async progress callback
    ) -> Dict[str, Any]: ...

    async def check_file(self, file_path: str) -> Dict[str, Any]: ...
    async def get_fix_instructions(self, issue_id: str) -> Dict[str, Any]: ...
    async def apply_fix(self, issue_id: str) -> Dict[str, Any]: ...
    async def get_status(self) -> Dict[str, Any]: ...
    async def get_help(self) -> Dict[str, Any]: ...
    async def autoconfigure(self) -> Dict[str, Any]: ...
    async def validate_config(self, config_path: Optional[str] = None) -> Dict[str, Any]: ...
```

The MCP server sends progress notifications during scans, reporting domain start/completion events to the AI client.

MCP `scan` caveats: the `*_threshold_scope` params only matter together with `base_branch`; `linting_threshold_scope` and `type_checking_threshold_scope` are accepted but currently have no effect; the coverage/duplication scope defaults are hardcoded and do not read `threshold_scope` from `lucidshark.yml`. MCP `scan` does not apply `fail_on`; its response reports `blocking` (true when any critical/high issue is present) instead.

**Partial Scanning Support (Default Behavior):**

| Domain | Partial Scan | Notes |
|--------|--------------|-------|
| Linting | ⚠️ Partial | Ruff/ESLint/Biome/Checkstyle/PMD/ktlint/clang-tidy/Scalafix/RuboCop/phpcs support file args; Clippy, golangci-lint (`./...`), dotnet format and SwiftLint are project-wide |
| Formatting | ⚠️ Partial | Ruff Format/Prettier/ktlint/rustfmt/gofmt/clang-format/Scalafmt/SwiftFormat/RuboCop Format/PHP-CS-Fixer support file args; dotnet format is project-wide |
| Type Checking | ⚠️ Partial | mypy/pyright/cppcheck/detekt support file args; tsc/SpotBugs/cargo check/dotnet build/scala compile/swift compiler/Sorbet/PHPStan always full; go vet runs package-wide (`./...`) |
| SAST | ❌ No | OpenGrep scans the project root and gosec scans `./...`; results are narrowed to changed files only with `--base-branch` |
| SCA | ❌ No | Trivy dependency scan always project-wide |
| IaC | ❌ No | Checkov always project-wide |
| Testing | ⚠️ Partial | Jest/Vitest/Mocha/Playwright support file args; pytest (always the full suite)/Karma/Maven/cargo test/dotnet test/CTest/sbt/swift test/RSpec/PHPUnit project-wide; go test runs package-wide (`./...`) |
| Coverage | ⚠️ Partial | Parses existing data, filter output; Tarpaulin/JaCoCo/dotnet coverage/Scoverage/swift coverage always project-wide; go cover parses project-wide coverprofile |
| Duplication | ❌ No | Duplo always scans project-wide for cross-file duplicates |

### 6.5 Unified Issue Schema

All tools normalize to this schema (`core/models.py`):

```python
class ScanDomain(str, Enum):
    """Security-focused scanning domains."""
    SCA = "sca"
    CONTAINER = "container"
    IAC = "iac"
    SAST = "sast"

class ToolDomain(str, Enum):
    """Quality pipeline tool domains."""
    LINTING = "linting"
    TYPE_CHECKING = "type_checking"
    SECURITY = "security"      # Generic (used in config, not in issues)
    TESTING = "testing"
    COVERAGE = "coverage"
    DUPLICATION = "duplication"
    FORMATTING = "formatting"

# Issues use either ScanDomain or ToolDomain
DomainType = Union[ScanDomain, ToolDomain]

class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

@dataclass
class UnifiedIssue:
    # Core identification
    id: str                        # Unique identifier
    domain: DomainType             # ScanDomain or ToolDomain
    source_tool: str               # "ruff", "trivy", "mypy", etc.
    severity: Severity             # CRITICAL, HIGH, MEDIUM, LOW, INFO

    # Content
    rule_id: str                   # Rule identifier (E501, CVE-2024-1234, CKV_AWS_1)
    title: str                     # Short issue title
    description: str               # Detailed description
    recommendation: str | None     # How to fix
    documentation_url: str | None  # Link to rule documentation

    # Location
    file_path: Path | None         # File containing the issue
    line_start: int | None         # Starting line number
    line_end: int | None           # Ending line number
    column_start: int | None       # Starting column
    column_end: int | None         # Ending column
    code_snippet: str | None       # Relevant code

    # Fix information
    fixable: bool                  # Whether auto-fix is available
    suggested_fix: str | None      # Suggested code fix

    # Domain-specific fields
    dependency: str | None         # For SCA (e.g., "lodash@4.17.20")
    iac_resource: str | None       # For IaC (e.g., "aws_s3_bucket.public")

    # Ignore status
    ignored: bool                  # Whether this issue is ignored via ignore_issues config
    ignore_reason: str | None      # Reason from the ignore_issues entry

    # Extensibility
    metadata: dict[str, Any]       # Tool-specific data
```

---

## 7. AI Integration Specification

### 7.1 Integration Modes

LucidShark supports multiple integration modes with AI coding tools:

#### 7.1.1 MCP Server Mode (Recommended)

LucidShark runs as an MCP server that AI tools connect to:

```bash
./lucidshark serve --mcp
```

**For Claude Code** (project `.mcp.json`, written by `lucidshark init`):
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

`command` is `./lucidshark` when a project-local binary exists; otherwise `init` uses `lucidshark` (pip install) or an absolute path. `init` also adds `"enabledMcpjsonServers": ["lucidshark"]` to the project `.claude/settings.json`. For Windsurf, `init --windsurf` only prints an MCP snippet (with absolute paths) to paste into `~/.codeium/windsurf/mcp_config.json` or `.devin/mcp_config.json`; it writes neither file.

#### 7.1.2 Hooks Mode

`lucidshark init` adds a Claude Code hook to the project `.claude/settings.json`. It does not run a scan; it only echoes a reminder after each edit:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write|NotebookEdit",
        "hooks": [
          {
            "type": "command",
            "command": "echo '[LucidShark] Code modified — scan before completing task (mcp__lucidshark__scan or lucidshark scan --linting --type-checking --formatting --fix --format ai)'"
          }
        ]
      }
    ]
  },
  "enabledMcpjsonServers": ["lucidshark"]
}
```

#### 7.1.3 File Watcher Mode

For editors without MCP/hooks support:

```bash
./lucidshark serve --watch > /tmp/lucidshark-issues.json
```

Each debounced batch of changes is scanned and the result is printed to stdout as JSON; editor plugins can read that output and display issues.

### 7.2 AI Instruction Format

When providing feedback to AI agents, the MCP `scan` response (`mcp/formatter.py`) has these top-level keys: `total_issues`, `ignored_issues`, `blocking`, `summary`, `severity_counts`, `domain_status`, `issues_by_domain`, `instructions`, `recommended_action`, plus `ignored_issues_by_domain`, `coverage_summary`, `duplication_summary` and `incremental_scan` when relevant. Each entry in `instructions` is a flat `FixInstruction` (see 5.3.3), sorted by priority (critical 1 … info 5):

```json
{
  "total_issues": 1,
  "ignored_issues": 0,
  "blocking": true,
  "summary": "1 issues found: 1 high",
  "severity_counts": { "high": 1 },
  "domain_status": {
    "type_checking": { "status": "fail", "display": "1 issues", "issue_count": 1, "fixable_count": 0 },
    "sast": { "status": "pass", "display": "Pass", "issue_count": 0, "fixable_count": 0 }
  },
  "issues_by_domain": {
    "type_checking": [
      { "id": "mypy-a1b2c3", "location": "src/utils.py:45", "severity": "high",
        "title": "[arg-type] Argument 1 has incompatible type \"str\"; expected \"list[str]\"", "fixable": false }
    ]
  },
  "instructions": [
    {
      "priority": 2,
      "action": "FIX_TYPE_ERROR",
      "summary": "[arg-type] Argument 1 has incompatible type \"str\"; expected \"list[str]\" in utils.py:45",
      "file": "src/utils.py",
      "line": 45,
      "column": 19,
      "problem": "Argument 1 has incompatible type \"str\"; expected \"list[str]\"",
      "fix_steps": ["Pass a list instead of a string, or change the function signature"],
      "suggested_fix": null,
      "current_code": null,
      "documentation_url": null,
      "related_issues": [],
      "issue_id": "mypy-a1b2c3"
    }
  ],
  "recommended_action": "Address 1 high-severity issue(s) before committing."
}
```

### 7.3 Feedback Loop

The AI integration creates an automated feedback loop with partial scanning for speed:

```
1. AI writes/modifies code
2. LucidShark runs partial scan on changed files (via MCP files parameter)
3. Issues are formatted as instructions
4. AI receives instructions and applies fixes
5. LucidShark re-checks (partial scan on fixed files)
6. Repeat until clean
7. Before commit: run full scan for comprehensive check
```

The feedback loop is driven by instructions provided to the AI tool via `lucidshark init`, which creates:
- `.claude/CLAUDE.md` for Claude Code with scan workflow instructions

These instruct the AI to:
- Run **default scans** (changed files only) after code changes for fast feedback
- Run **full scans** (with `all_files=true`) before commits for comprehensive checking

### 7.4 Partial Scanning for AI Agents (Default Behavior)

LucidShark scans only changed files by default, enabling fast feedback loops:

| Scenario | Scan Type | Example |
|----------|-----------|---------|
| After editing files | Default (changed files) | `scan(domains=["linting", "type_checking"])` |
| Single file check | Partial | `check_file(file_path="src/main.py")` |
| Specific files | Partial | `scan(domains=["linting"], files=["src/a.py", "src/b.py"])` |
| Before commit | Full | `scan(domains=["all"], all_files=true)` |
| Security audit | Full | `scan(domains=["sca", "sast", "iac"], all_files=true)` |

**Tool-Level Partial Scan Support:**

| Tool Category | Tools | Partial Scan Support |
|---------------|-------|---------------------|
| **Linting** | Ruff, ESLint, Biome, Checkstyle, PMD, ktlint, clang-tidy, Scalafix, RuboCop, phpcs | ✅ All support file args |
| **Linting** | Clippy, dotnet format, SwiftLint | ❌ Project-wide only |
| **Linting** | golangci-lint | ❌ No (always runs workspace-wide `./...`) |
| **Formatting** | Ruff Format, Prettier, ktlint, rustfmt, gofmt, clang-format, Scalafmt, SwiftFormat, RuboCop Format, PHP-CS-Fixer | ✅ Support file args |
| **Formatting** | dotnet format | ❌ Project-wide only |
| **Type Checking** | mypy, pyright, cppcheck, detekt | ✅ Support file args |
| **Type Checking** | TypeScript (tsc), SpotBugs, cargo check, dotnet build, scala compile, swift compiler, Sorbet, PHPStan | ❌ Project-wide only |
| **Type Checking** | go vet | ❌ No (package-wide) |
| **SAST** | OpenGrep, gosec | ❌ Project-wide (filtered only with `--base-branch`) |
| **SCA** | Trivy | ❌ Project-wide by design |
| **IaC** | Checkov | ❌ Project-wide by design |
| **Testing** | Jest, Vitest, Mocha, Playwright | ✅ Support file args |
| **Testing** | pytest, Karma, Maven/Gradle, cargo test, dotnet test, CTest, sbt, swift test, RSpec, PHPUnit | ❌ Config-based / project-wide |
| **Testing** | go test | ❌ No (package-wide) |
| **Coverage** | coverage.py, Istanbul, Vitest coverage, SimpleCov, PHPUnit Clover | ⚠️ Parse data, filter output |
| **Coverage** | JaCoCo, Tarpaulin, dotnet coverage, Scoverage, swift coverage | ❌ Project-wide |
| **Coverage** | go cover | ❌ No (project-wide coverprofile) |
| **Duplication** | Duplo | ❌ Project-wide by design |

---

## 8. CLI Specification

### 8.1 Global Options

```
lucidshark [OPTIONS] COMMAND [ARGS]

Global Options (must come before the subcommand, e.g. `lucidshark --debug scan`):
  --verbose, -v        Verbose output
  --quiet, -q          Minimal output
  --debug              Debug mode with full traces
  --version            Show version
  --help, -h           Show help
```

### 8.2 Commands

#### 8.2.1 `init`

```
./lucidshark init [OPTIONS]

Configure AI tool integration and generate lucidshark.yml.

AI tools (default: Claude Code only; flags combine):
  --claude-code        Configure Claude Code
  --cursor             Configure Cursor (.cursor/mcp.json, .cursor/rules/lucidshark.mdc)
  --windsurf           Configure Windsurf (.windsurf/rules/lucidshark.md, prints MCP snippet)
  --aider              Configure Aider (.aider.conf.yml lint-cmd, CONVENTIONS.md)
  --all-tools          Configure all supported tools

Options:
  --dry-run            Show changes without applying
  --force              Overwrite existing configuration (selected tools and lucidshark.yml)
  --remove             Remove LucidShark from the selected tools' configuration
  --no-config          Skip lucidshark.yml generation (only configure AI tool integration)

Examples:
  ./lucidshark init                    # Full setup: Claude Code + config generation
  ./lucidshark init --cursor --aider   # Cursor and Aider instead of Claude Code
  ./lucidshark init --all-tools        # Every supported AI tool
  ./lucidshark init --no-config        # Only configure Claude Code
  ./lucidshark init --force            # Regenerate everything
```

#### 8.2.2 `scan`

```
./lucidshark scan [OPTIONS] [PATH]

Run the quality pipeline. By default, scans only changed files (uncommitted changes).
Without a domain flag, only the security domains (sca/sast/iac/container) enabled in
lucidshark.yml run; other domains need their flag or --all.

Scan Domains:
  --sca                Scan dependencies for known vulnerabilities (Trivy)
  --sast               Static application security testing (OpenGrep)
  --iac                Scan Infrastructure-as-Code (Checkov)
  --container          Scan container images (use with --image)
  --linting            Run linting checks
  --type-checking      Run type checking
  --formatting         Run formatting checks
  --testing            Run test suite
  --coverage           Run coverage analysis (requires --testing)
  --duplication        Run code duplication detection
  --all                Enable all configured domains

Targets:
  PATH                 Path to scan (default: current directory)
  --files FILE...      Specific files to scan
  --all-files          Scan entire project instead of just changed files
  --image IMAGE        Container image to scan (repeatable)
  --base-branch BRANCH Filter results (issues, coverage, duplication) to files changed
                       since BRANCH (e.g. origin/main); full analysis still runs

Output:
  --format FORMAT      Output format: ai, json, table, sarif, summary (default: json)

Configuration:
  --fail-on LEVEL      Fail on any non-ignored issue at or above LEVEL (critical, high,
                       medium, low) in every domain; overrides fail_on in config
  --coverage-threshold N  Coverage percentage threshold (default: 80)
  --duplication-threshold N  Max duplication percentage (default: 10)
  --min-lines N        Min lines for duplicate block (default: 4)
  --coverage-threshold-scope {changed,project,both}       With --base-branch (default: changed)
  --linting-threshold-scope {changed,project,both}        With --base-branch (default: changed)
  --type-checking-threshold-scope {changed,project,both}  With --base-branch (default: changed)
  --duplication-threshold-scope {changed,project,both}    With --base-branch (default: both when a duplication section is configured)
  --config PATH        Path to config file

Execution:
  --fix                Apply auto-fixes where possible (linting and formatting)
  --stream             Stream tool output in real-time
  --sequential         Disable parallel scanner execution
  --dry-run            Show what would be scanned without executing

Examples:
  ./lucidshark scan --linting          # Lint changed files (default)
  ./lucidshark scan --all --all-files  # Full project scan
  ./lucidshark scan --files src/a.py   # Scan specific files
  ./lucidshark scan --linting --fix    # Auto-fix linting issues
  ./lucidshark scan --stream           # See live output
  ./lucidshark scan --format json      # JSON output
```

#### 8.2.4 `serve`

```
./lucidshark serve [OPTIONS] [PATH]

Run LucidShark as a server for AI integration.

Options:
  --mcp                Run as MCP server (for Claude Code); the default when
                       neither --mcp nor --watch is given
  --watch              Watch files and run incremental checks on changes;
                       results are printed to stdout as JSON
  --debounce MS        Debounce delay for file watcher (default: 1000ms)
  PATH                 Project directory to serve (default: current directory)

Examples:
  ./lucidshark serve --mcp             # MCP server for Claude Code
  ./lucidshark serve --watch           # File watcher mode
```

On binary installs, `serve --mcp` self-updates before serving unless `settings.auto_update: false`. Other commands check for and download a new release in the background; a downloaded update is applied the next time LucidShark starts.

#### 8.2.5 `status`

```
lucidshark status

Show LucidShark version, platform, cached tools and available plugins.

Examples:
  lucidshark status                  # Overview
```

#### 8.2.6 `validate`

```
./lucidshark validate [OPTIONS]

Validate a lucidshark.yml configuration file and report errors/warnings.

Options:
  --config PATH        Path to config file (default: find in current directory)

Examples:
  ./lucidshark validate                    # Validate default config
  ./lucidshark validate --config my.yml    # Validate specific file
```

#### 8.2.7 `doctor`

```
./lucidshark doctor

Run diagnostic checks on your LucidShark installation.

Checks:
  - Configuration: lucidshark.yml presence and validity
  - Tools: Scanner plugin availability and versions
  - Environment: Python version, platform, git repository
  - Integrations: Claude Code MCP configuration

Examples:
  ./lucidshark doctor                  # Run all health checks
```

#### 8.2.8 `help`

```
lucidshark help

Display comprehensive LLM-friendly documentation including CLI commands,
MCP tools, and configuration reference.
```

#### 8.2.9 `overview`

```
./lucidshark overview [OPTIONS] [PATH]

Generate a quality overview report (QUALITY.md) from scan results.
Provides a git-committed quality dashboard without server or SaaS.

IMPORTANT: Requires a full project scan (--all-files). Partial/incremental
scans are rejected because overview represents the entire repo's quality state.

Options:
  --show               Display overview to stdout (default)
  --preview            Preview what would be written without saving
  --update             Write QUALITY.md and update history file
  --scan               Run a scan first if no cached results exist

Examples:
  ./lucidshark scan --all --all-files    # Required: full project scan first
  ./lucidshark overview                  # Display current overview
  ./lucidshark overview --preview        # Preview without saving
  ./lucidshark overview --update         # Save QUALITY.md and history
```

**How it works:**
1. Reads cached scan results from `.lucidshark/last-scan.json`
2. Validates the scan was a full project scan (rejects partial scans)
3. Calculates health score (0-10) based on issues, coverage, duplication
4. Generates markdown with domain status, trends, top files
5. Optionally saves to QUALITY.md and appends to history

**CI Integration:**
```yaml
# GitHub Actions - auto-commit on merge to main
- name: Update Quality Overview
  if: github.ref == 'refs/heads/main'
  run: |
    ./lucidshark scan --all --all-files  # Must use --all-files for overview
    ./lucidshark overview --update
    git add QUALITY.md .lucidshark/quality-history.json
    git diff --staged --quiet || git commit -m "chore: update quality overview"
    git push
```

### 8.3 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success: no blocking issues |
| 1 | A `fail_on` rule failed (including coverage `below_threshold` and duplication `above_threshold`), an issue is at or above `--fail-on`, or a mandatory tool was skipped/failed. Without `fail_on` or `--fail-on`, issues and threshold misses are reported but don't change the exit code |
| 2 | Tool/scanner execution error, or invalid command-line arguments (argparse usage error) |
| 3 | Config file not found or not parseable, scan path not found, configured tool not installed, or `--coverage` without `--testing` |

---

## 9. Supported Tools

### 9.1 Linting

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| Ruff | Python | pip / binary | ✅ Yes |
| ESLint | JavaScript, TypeScript | npm | ✅ Yes |
| Biome | JavaScript, TypeScript, JSON | npm / binary | ✅ Yes |
| Checkstyle | Java | managed (auto-download) | ✅ Yes |
| PMD | Java | managed (auto-download) | ✅ Yes |
| ktlint | Kotlin | managed (auto-download) | ✅ Yes |
| Clippy | Rust | system (rustup) | ❌ No (Cargo workspace) |
| golangci-lint | Go | go install | ❌ No (workspace-wide `./...`) |
| dotnet format | C# | system (.NET SDK) | ❌ No (project-wide) |
| clang-tidy | C, C++ | system (LLVM) | ✅ Yes |
| Scalafix | Scala | cs install (CLI on PATH) | ✅ Yes |
| SwiftLint | Swift | brew / system | ❌ No (project-wide) |
| RuboCop | Ruby | gem | ✅ Yes |
| phpcs | PHP | composer | ✅ Yes |

All linting tools support partial scanning via the `files` parameter, except Clippy (full Cargo workspace), golangci-lint (always `./...`), dotnet format and SwiftLint.

### 9.2 Formatting

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| Ruff Format | Python | pip / binary | ✅ Yes |
| Prettier | JavaScript, TypeScript, CSS, JSON, Markdown | npm | ✅ Yes |
| ktlint (format) | Kotlin | managed (auto-download) | ✅ Yes |
| rustfmt | Rust | system (rustup) | ✅ Yes |
| gofmt | Go | system (ships with Go) | ✅ Yes |
| dotnet format whitespace | C# | system (.NET SDK) | ❌ No (project-wide) |
| clang-format | C, C++ | system (LLVM) | ✅ Yes |
| Scalafmt | Scala | cs install (CLI on PATH) | ✅ Yes |
| SwiftFormat | Swift | brew / system | ✅ Yes |
| RuboCop Format | Ruby | gem | ✅ Yes |
| PHP-CS-Fixer | PHP | composer | ✅ Yes |

Formatting tools check code style and whitespace conventions. All formatters support partial scanning via the `files` parameter except dotnet format, which runs on the whole project.

### 9.3 Type Checking

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| mypy | Python | pip | ✅ Yes |
| Pyright | Python | pip / npm / binary | ✅ Yes |
| TypeScript (tsc) | TypeScript | npm | ❌ No |
| SpotBugs | Java | managed (auto-download) | ❌ No |
| detekt | Kotlin | managed (auto-download) | ✅ Yes |
| cargo check | Rust | system (rustup) | ❌ No (Cargo workspace) |
| go vet | Go | system (ships with Go) | ❌ No (package-wide) |
| dotnet build | C# | system (.NET SDK) | ❌ No |
| cppcheck | C, C++ | system | ✅ Yes |
| scala compile | Scala | sbt / mvn / gradle | ❌ No |
| Swift compiler | Swift | system (Xcode / swift.org) | ❌ No |
| Sorbet | Ruby | gem | ❌ No (project-wide) |
| PHPStan | PHP | composer | ❌ No (project-wide) |

**Note:** TypeScript (tsc) does not support file-level CLI arguments - it uses `tsconfig.json` to determine what to check. SpotBugs requires compiled Java classes (run `mvn compile` or `gradle build` first). cargo check operates on the full Cargo workspace. go vet operates on Go packages. dotnet build, scala compile, Swift compiler, Sorbet and PHPStan operate on full projects/packages.

### 9.4 Security

| Tool | Domains | Install Method | Partial Scan |
|------|---------|----------------|--------------|
| Trivy | SCA, Container | managed (auto-download) | ❌ No |
| OpenGrep | SAST | managed (auto-download) | ❌ No (project-wide) |
| gosec | SAST (Go) | managed (auto-download) | ❌ No (scans `./...`) |
| Checkov | IaC | managed (auto-download) | ❌ No |

**Note:** All security scanners scan the entire project. With `--base-branch`, their results are filtered to changed files.

### 9.5 Testing

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| pytest | Python | pip | ❌ No (always the full suite) |
| Jest | JavaScript, TypeScript | npm | ✅ Yes |
| Vitest | JavaScript, TypeScript | npm | ✅ Yes |
| Mocha | JavaScript, TypeScript | npm | ✅ Yes |
| Karma | JavaScript, TypeScript (Angular) | npm | ❌ No |
| Playwright | JavaScript, TypeScript (E2E) | npm | ✅ Yes |
| Maven/Gradle | Java, Kotlin (JUnit/TestNG) | system | ❌ No |
| cargo test | Rust | system (rustup) | ❌ No (Cargo workspace) |
| go test | Go | system (ships with Go) | ❌ No (package-wide) |
| dotnet test | C# | system (.NET SDK) | ❌ No |
| CTest | C, C++ | system (CMake) | ❌ No |
| sbt test | Scala | system / cs install | ❌ No |
| swift test | Swift | system (Xcode / swift.org) | ❌ No |
| RSpec | Ruby | gem | ❌ No (project-wide) |
| PHPUnit | PHP | composer | ❌ No (project-wide) |

**Note:** Jest, Vitest, Mocha and Playwright can run specific test files; running the full test suite is recommended before commits to catch regressions. pytest, Maven, Gradle, dotnet test, CTest, sbt, swift test, RSpec and PHPUnit always run the full test suite. cargo test runs all unit tests, integration tests, and doc tests in the Cargo workspace. go test runs all tests in the specified packages.

### 9.6 Coverage

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| coverage.py | Python | pip | ⚠️ Partial (filter output) |
| Istanbul/nyc | JavaScript, TypeScript | npm | ⚠️ Partial (filter output) |
| Vitest coverage | JavaScript, TypeScript | npm | ⚠️ Partial (filter output) |
| JaCoCo | Java, Kotlin | Maven/Gradle plugin | ❌ No (project-wide) |
| Tarpaulin | Rust | cargo install | ❌ No (Cargo workspace) |
| go cover | Go | system (ships with Go) | ❌ No (project-wide) |
| dotnet coverage | C# | system (.NET SDK) | ❌ No (project-wide) |
| gcov | C | system (GCC) | ❌ No (project-wide) |
| lcov | C++ | system | ❌ No (project-wide) |
| Scoverage | Scala | sbt / Maven plugin | ❌ No (project-wide) |
| swift coverage (llvm-cov) | Swift | system (Xcode / swift.org) | ❌ No (project-wide) |
| SimpleCov | Ruby | gem | ⚠️ Partial (filter output) |
| PHPUnit Clover | PHP | composer | ⚠️ Partial (filter output) |

**Note:** Coverage plugins only parse existing coverage data files  -  they never run tests. Most test runners (pytest, jest, vitest, mocha, maven, go test, dotnet test, swift test) include coverage instrumentation automatically; the cargo test runner switches to `cargo tarpaulin` when coverage is enabled and tarpaulin is installed. Others (karma, playwright) require separate coverage tools or config. If no coverage data is found, a `no_coverage_data` error is returned. For partial scanning, coverage output can be filtered to show only changed files.

**Java Coverage (JaCoCo):** JaCoCo reads the report produced by the Maven/Gradle test run, so testing must be enabled too:
```yaml
pipeline:
  testing:
    enabled: true
    tools: [maven]
  coverage:
    enabled: true
    tools: [jacoco]
    threshold: 80
```

`coverage.extra_args` is accepted by the config validator but currently ignored; skip integration tests that need Docker or external services in your build configuration instead.

### 9.7 Duplication Detection

| Tool | Languages | Install Method | Partial Scan |
|------|-----------|----------------|--------------|
| Duplo | Python, Rust, Java, Kotlin, JavaScript, TypeScript, C, C++, C#, Go, Scala, Swift, Ruby, PHP, Erlang, VB, HTML, CSS | managed (auto-download) | ❌ No |

**Note:** Duplication detection always scans the entire project to find cross-file duplicates. Use the `pipeline.duplication.exclude` configuration or the global `exclude` list to skip generated or vendor files (e.g., `htmlcov/**`, `generated/**`).

---

## 10. Development Phases

### Phase 1: Foundation ✅ COMPLETE

**Goal**: Core pipeline with `init` and `scan` commands

- [x] Codebase detector (languages, frameworks, existing tools)
- [x] Configuration generator (`lucidshark init`)
- [x] Pipeline orchestrator
- [x] Initial tool plugins:
  - [x] Ruff (Python linting)
  - [x] ESLint (JS/TS linting)
  - [x] mypy (Python type checking)
  - [x] Trivy (SCA, container security)
  - [x] OpenGrep (SAST)
  - [x] pytest (Python testing)
- [x] Reporters: Table, JSON, SARIF

**Milestone**: `lucidshark init && lucidshark scan` works end-to-end

### Phase 2: Expanded Coverage ✅ COMPLETE

**Goal**: More tools

- [x] Additional tool plugins:
  - [x] Biome (JS/TS)
  - [x] Checkov (IaC)
  - [x] Checkstyle (Java linting)
  - [x] PMD (Java static analysis - managed)
  - [x] ktlint (Kotlin linting - managed)
  - [x] detekt (Kotlin static analysis - managed)
  - [x] dotnet format (C# linting/formatting)
  - [x] dotnet build (C# type checking)
  - [x] dotnet test (C# testing)
  - [x] dotnet coverage (C# coverage)
  - [x] clang-tidy (C/C++ linting)
  - [x] clang-format (C/C++ formatting)
  - [x] cppcheck (C/C++ type checking)
  - [x] CTest (C/C++ testing)
  - [x] gcov/lcov (C/C++ coverage)
  - [x] Scalafix (Scala linting)
  - [x] Scalafmt (Scala formatting)
  - [x] scala compile (Scala type checking)
  - [x] sbt test (Scala testing)
  - [x] Scoverage (Scala coverage)
  - [x] SwiftLint (Swift linting)
  - [x] SwiftFormat (Swift formatting)
  - [x] swift compiler (Swift type checking)
  - [x] swift test (Swift testing)
  - [x] swift coverage (Swift coverage)
  - [x] RuboCop (Ruby linting/formatting)
  - [x] Sorbet (Ruby type checking)
  - [x] RSpec (Ruby testing)
  - [x] SimpleCov (Ruby coverage)
  - [x] phpcs (PHP linting)
  - [x] PHP-CS-Fixer (PHP formatting)
  - [x] PHPStan (PHP type checking)
  - [x] PHPUnit (PHP testing)
  - [x] PHPUnit Clover (PHP coverage)
  - [x] Jest (JS/TS testing)
  - [x] Karma (Angular testing)
  - [x] Playwright (E2E testing)
  - [x] Vitest (JS/TS testing)
  - [x] coverage.py (Python coverage)
  - [x] Istanbul (JS/TS coverage)
  - [x] Vitest coverage (JS/TS coverage)
  - [x] pyright (Python type checking)
  - [x] TypeScript (tsc)
  - [x] Duplo (duplication detection)
- [x] Auto-fix mode (`--fix`)

**Milestone**: Support for Python, JavaScript/TypeScript, Java projects

### Phase 3: AI Integration ✅ COMPLETE

**Goal**: MCP server and AI feedback loop

- [x] MCP server implementation (`lucidshark serve --mcp`) with 8 tools
- [x] AI instruction formatter
- [x] File watcher mode
- [x] Claude Code integration (`lucidshark init`)
- [x] Feedback loop configuration
- [x] MCP autoconfigure tool (AI-driven project setup)
- [x] MCP validate_config tool
- [x] MCP progress notifications

**Milestone**: AI agents can invoke LucidShark and receive fix instructions

### Phase 3.5: Developer Experience ✅ COMPLETE

**Goal**: CLI polish and diagnostics

- [x] `lucidshark validate` command
- [x] `lucidshark doctor` command (health checks)
- [x] `lucidshark help` command (LLM-friendly docs)
- [x] `--dry-run` for scan command
- [x] `--stream` for real-time output
- [x] SpotBugs (Java type checking)
- [x] JaCoCo (Java coverage)
- [x] Maven test runner

**Milestone**: Complete developer experience with diagnostics

### Phase 4: Polish (In Progress)

**Goal**: Production readiness

- [x] Comprehensive documentation (README, spec, LLM help, exclude patterns, roadmap)
- [ ] Plugin SDK for third-party tools
- [ ] Performance optimization (caching, incremental checks)
- [ ] Error handling hardening

**Milestone**: v1.0 release

---

## 11. Module Structure

```
src/lucidshark/
├── cli/                    # Command-line interface
│   ├── __main__.py         # Entry point
│   ├── arguments.py        # Argument parser
│   ├── runner.py           # Command dispatch
│   ├── exit_codes.py       # Exit code constants
│   ├── config_bridge.py    # Config → CLI bridge
│   └── commands/           # Command implementations
│       ├── init.py         # lucidshark init
│       ├── scan.py         # lucidshark scan
│       ├── serve.py        # lucidshark serve
│       ├── status.py       # lucidshark status
│       ├── validate.py     # lucidshark validate
│       ├── doctor.py       # lucidshark doctor
│       ├── help.py         # lucidshark help
│       ├── overview.py     # lucidshark overview
│       └── list_scanners.py # list-scanners (internal)
├── config/                 # Configuration handling
│   ├── models.py           # Config dataclasses
│   ├── loader.py           # YAML loading and merging
│   ├── validation.py       # Config validation
│   └── ignore.py           # Ignore pattern handling
├── core/                   # Core abstractions
│   ├── models.py           # UnifiedIssue, ScanContext, etc.
│   ├── domain_runner.py    # Tool-domain execution
│   ├── git.py              # Git operations
│   ├── paths.py            # Path determination
│   ├── streaming.py        # Real-time output streaming
│   ├── subprocess_runner.py # Subprocess management
│   └── logging.py          # Logging setup
├── detection/              # Project detection
│   ├── detector.py         # CodebaseDetector orchestrator
│   ├── languages.py        # Language detection
│   ├── frameworks.py       # Framework detection
│   └── tools.py            # Tool config detection
├── generation/             # Config generation
│   ├── config_generator.py # lucidshark.yml generation
│   └── package_installer.py # Package installation (not called by any command)
├── pipeline/               # Scan pipeline
│   ├── executor.py         # PipelineExecutor
│   └── parallel.py         # ParallelScannerExecutor
├── plugins/                # All tool plugins
│   ├── discovery.py        # Plugin discovery via entry points
│   ├── utils.py            # Shared plugin utilities
│   ├── linters/            # LinterPlugin implementations
│   ├── type_checkers/      # TypeCheckerPlugin implementations
│   ├── formatters/         # FormatterPlugin implementations
│   ├── scanners/           # ScannerPlugin implementations
│   ├── test_runners/       # TestRunnerPlugin implementations
│   ├── coverage/           # CoveragePlugin implementations
│   ├── duplication/        # DuplicationPlugin implementations
│   ├── enrichers/          # EnricherPlugin implementations
│   └── reporters/          # Reporter implementations
├── mcp/                    # MCP server
│   ├── server.py           # LucidSharkMCPServer
│   ├── tools.py            # MCPToolExecutor
│   ├── formatter.py        # InstructionFormatter
│   └── watcher.py          # File watcher
├── bootstrap/              # Tool management
│   ├── download.py         # Binary downloading
│   ├── paths.py            # .lucidshark/ directory management
│   ├── platform.py         # Platform detection
│   ├── versions.py         # Version management
│   └── validation.py       # Binary validation
```

---

## 13. Appendix

### A. Glossary

| Term | Definition |
|------|------------|
| **Domain** | Category of checks: linting, type checking, security, testing, coverage, duplication |
| **ToolDomain** | Enum for quality pipeline domains (LINTING, TYPE_CHECKING, FORMATTING, SECURITY, TESTING, COVERAGE, DUPLICATION) |
| **ScanDomain** | Enum for security scanning domains (SCA, SAST, IAC, CONTAINER) |
| **Tool** | Underlying program (Ruff, Trivy, pytest) |
| **Plugin** | LucidShark adapter for a tool |
| **Enricher** | Post-processing plugin that augments or filters issues after scanning |
| **Pipeline** | Sequence of domains to execute |
| **Issue** | Single finding from any tool, normalized to UnifiedIssue schema |
| **MCP** | Model Context Protocol, standard for AI tool integration |

### B. Configuration Schema

There is no published JSON Schema. `lucidshark validate` (or the `validate_config` MCP tool) checks `lucidshark.yml` against the keys and values defined in `config/validation.py`; section 5.4.1 documents the schema.

### C. Environment Variables

| Variable | Purpose |
|----------|---------|
| `LUCIDSHARK_HOME` | Override tool storage directory (default: `{project}/.lucidshark`). Also locates the optional global config `$LUCIDSHARK_HOME/config/config.yml` (fallback `<cwd>/.lucidshark/config/config.yml`), which is deep-merged under the project or `--config` file (dicts merge, lists replace, project wins) |
