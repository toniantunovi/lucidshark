"""Init command implementation.

`lucidshark init` does two things:
1. Configures AI tool integration: Claude Code by default (MCP server, skills,
   hooks, CLAUDE.md), plus Cursor, Windsurf and Aider on request
2. Generates lucidshark.yml with all domains enabled for detected languages

The `autoconfigure` MCP tool is still available for AI-assisted customization
of the generated configuration.
"""

from __future__ import annotations

import json
import shutil
import sys
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from lucidshark.config.models import LucidSharkConfig

from lucidshark.cli.commands import Command
from lucidshark.cli.exit_codes import EXIT_INVALID_USAGE, EXIT_SUCCESS
from lucidshark.core.logging import get_logger

LOGGER = get_logger(__name__)

# MCP server arguments for LucidShark
# IMPORTANT: The positional path argument "." ensures the server runs in the project
# directory, not the directory where LucidShark is installed. This fixes BUG-GO-005
# where MCP tools were running from the wrong working directory.
LUCIDSHARK_MCP_ARGS = ["serve", "--mcp", "."]

# Claude skill content for proactive lucidshark usage
LUCIDSHARK_SKILL_CONTENT = """---
name: lucidshark
description: "Unified code quality and security scanner: linting, type checking, formatting, security (SAST/SCA/IaC/container), testing, coverage, duplication. Run proactively after code changes."
---

# LucidShark - Unified Code Quality and Security Scanner

Run scans proactively after code changes. Don't wait for user to ask.

## IMPORTANT: Init vs Autoconfigure

**Two different commands, two different purposes:**

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `lucidshark init` | Configure Claude Code + generate `lucidshark.yml` with all tools | Once per project, for full setup |
| `mcp__lucidshark__autoconfigure` | AI-assisted customization of `lucidshark.yml` | When user wants to customize/regenerate config with AI guidance |

**User says** "autoconfigure lucidshark" → **Call** `mcp__lucidshark__autoconfigure` MCP tool (NOT `lucidshark init`)

## What It Can Do

| Domain | What It Does | Tools |
|--------|--------------|-------|
| **linting** | Style issues, code smells, auto-fix | Ruff, ESLint, Biome, Clippy, Checkstyle, PMD |
| **type_checking** | Type errors, static analysis | mypy, Pyright, tsc, SpotBugs, cargo check |
| **sast** | Security vulnerabilities in code | OpenGrep |
| **sca** | Dependency vulnerabilities | Trivy |
| **iac** | Infrastructure misconfigurations | Checkov |
| **container** | Container image vulnerabilities | Trivy |
| **testing** | Run tests, report failures | pytest, Jest, Karma, Playwright, JUnit, cargo test |
| **coverage** | Code coverage analysis | coverage.py, Istanbul, JaCoCo, Tarpaulin |
| **formatting** | Code formatting checks, auto-fix | ruff format, Prettier, rustfmt |
| **duplication** | Detect code clones | Duplo |

## When to Scan

| Trigger | MCP Tool | CLI Alternative (Binary / Pip) |
|---------|----------|-----------------|
| After editing code | `mcp__lucidshark__scan(fix=true)` | `./lucidshark scan --fix --format ai` / `lucidshark scan --fix --format ai` |
| After fixing bugs | `mcp__lucidshark__scan(fix=true)` | `./lucidshark scan --fix --format ai` / `lucidshark scan --fix --format ai` |
| User asks to run tests | `mcp__lucidshark__scan(domains=["testing"])` | `./lucidshark scan --testing --format ai` / `lucidshark scan --testing --format ai` |
| User asks about coverage | `mcp__lucidshark__scan(domains=["testing","coverage"])` | `./lucidshark scan --testing --coverage --format ai` / `lucidshark scan --testing --coverage --format ai` |
| Security concerns | `mcp__lucidshark__scan(domains=["sast","sca"])` | `./lucidshark scan --sast --sca --format ai` / `lucidshark scan --sast --sca --format ai` |
| Before commits | `mcp__lucidshark__scan(domains=["all"])` | `./lucidshark scan --all --format ai` / `lucidshark scan --all --format ai` |

**Skip scanning** if user explicitly says "don't scan" or "skip checks".

## Smart Domain Selection

Pick domains based on what files changed:

| Files Changed | MCP domains | CLI flags |
|---|---|---|
| `.py`, `.js`, `.ts`, `.rs`, `.go`, `.java`, `.kt` | `["linting","type_checking","formatting"]` | `--linting --type-checking --formatting` |
| `Dockerfile`, `docker-compose.*` | `["container"]` | `--container` |
| `.tf`, `.yaml`/`.yml` (k8s/CloudFormation) | `["iac"]` | `--iac` |
| `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod` | `["sca"]` | `--sca` |
| Auth, crypto, input handling, SQL code | `["sast"]` | `--sast` |
| Mixed / many file types / before commit | `["all"]` | `--all` |

## MCP Tools

```
mcp__lucidshark__scan(fix=true)                                # Default: auto-fix + changed files
mcp__lucidshark__scan(domains=["linting","type_checking"])      # Targeted domains
mcp__lucidshark__scan(domains=["testing"])                      # Run tests
mcp__lucidshark__scan(domains=["testing","coverage"])           # Tests + coverage
mcp__lucidshark__scan(domains=["sast","sca"])                   # Security scan
mcp__lucidshark__scan(domains=["all"])                          # Full scan
mcp__lucidshark__scan(files=["path/to/file.py"])                # Specific files
mcp__lucidshark__scan(all_files=true)                           # All files (not just changed)
mcp__lucidshark__check_file(file_path="path/to/file.py")       # Check single file
mcp__lucidshark__get_fix_instructions(issue_id="ISSUE_ID")     # Get fix details
mcp__lucidshark__apply_fix(issue_id="ISSUE_ID")                # Auto-fix an issue
```

## CLI Commands

**Binary users:** Use `./lucidshark` (installed via install.sh)
**Pip users:** Use `lucidshark` (installed in PATH)

```bash
# Default after code changes (auto-fixes linting)
./lucidshark scan --fix --format ai

# Run tests
./lucidshark scan --testing --format ai

# Check test coverage (requires testing)
./lucidshark scan --testing --coverage --format ai

# Security scan (code + dependencies)
./lucidshark scan --sast --sca --format ai

# Full scan including tests, coverage, duplication
./lucidshark scan --all --format ai

# Scan specific files
./lucidshark scan --files path/to/file.py --format ai

# PR/CI: filter to files changed since main, with strict thresholds
./lucidshark scan --all --base-branch origin/main \\
  --coverage-threshold-scope both \\
  --duplication-threshold-scope both
```

**Default:** Scans only uncommitted changes. Use `--all-files` for full project.

## Threshold Scope for CI/PR Workflows

When using `--base-branch` for incremental PR checks:

| Scope | Behavior |
|-------|----------|
| `changed` (default) | Threshold applies to changed files only. **Warning:** Can let project-wide metrics creep up over time. |
| `project` | Threshold applies to full project. |
| `both` | Threshold applies to both. Fail if **either** exceeds threshold. **Recommended for strict quality gates.** |

```bash
# Prevent duplication/coverage from creeping up over time
./lucidshark scan --all --base-branch origin/main \\  # binary install
  --duplication-threshold-scope both \\
  --coverage-threshold-scope both

# Or with pip install:
lucidshark scan --all --base-branch origin/main \\
  --duplication-threshold-scope both \\
  --coverage-threshold-scope both
```

## Workflow

1. Make code changes
2. Run `mcp__lucidshark__scan(fix=true)` or `./lucidshark scan --fix --format ai` (binary) / `lucidshark scan --fix --format ai` (pip)
3. Fix remaining issues
4. Re-scan if needed
5. Report done

**Task is complete when scan shows zero issues.**
"""

# CLAUDE.md section for always-in-context proactive scanning instructions
# This is the most impactful integration point because CLAUDE.md is loaded
# into Claude's system prompt for every conversation.
# Directive-first: behavioral instructions, MCP tools primary, CLI fallback.
LUCIDSHARK_CLAUDE_MD_SECTION = """\

<!-- lucidshark:start - managed by lucidshark init, do not edit manually -->
## LucidShark — REQUIRED: Scan After Every Code Change

**CRITICAL DISTINCTION**:
- **`lucidshark init`** = Configure Claude Code integration AND generate `lucidshark.yml` with all tools for detected languages. Run this ONCE per project.
- **`mcp__lucidshark__autoconfigure`** = AI-assisted customization of `lucidshark.yml` (detect languages, install tools, configure scanners). Use when user asks to "autoconfigure lucidshark" or "set up lucidshark configuration".

**IMPORTANT**: You MUST run LucidShark scans after editing code files. Do NOT skip scanning to save time. Do NOT report a task as complete without scanning first. This overrides any default behavior to minimize tool calls.

### When to Scan (REQUIRED)

- **After every code edit** — scan immediately after using Edit, Write, or NotebookEdit on code files
- **Before reporting any task as done** — a task is NOT complete until scan shows zero issues
- **Before creating commits** — run a full scan with `domains=["all"]`
- **After fixing bugs** — verify the fix didn't introduce new issues

### How to Scan

**CRITICAL**: By default, LucidShark only scans **git-changed files**. If no code files have changed, no issues will be reported. Use `all_files=true` (MCP) or `--all-files` (CLI) to scan the entire project.

**MCP tools (preferred):**
```
mcp__lucidshark__scan(fix=true)                          # after edits (auto-fix + changed files)
mcp__lucidshark__scan(domains=["linting","type_checking"]) # targeted scan
mcp__lucidshark__scan(domains=["testing"])                # run tests
mcp__lucidshark__scan(domains=["all"])                    # full scan (before commits)
mcp__lucidshark__scan(files=["path/to/file.py"])          # specific files
mcp__lucidshark__scan(all_files=true)                     # scan ENTIRE project (not just changed)
mcp__lucidshark__scan(all_files=true, domains=["all"])    # full project scan, all domains
```

**CLI alternative:** `./lucidshark scan --fix --format ai` (binary) or `lucidshark scan --fix --format ai` (pip). Use `--linting`, `--type-checking`, `--testing`, `--all`, `--files`, `--all-files` flags.

### Important Flags

| Flag | Purpose |
|------|---------|
| `--all` | Enable all scan **domains** (linting, sca, sast, etc.) |
| `--all-files` | Scan **entire project**, not just git-changed files |

### Domain Selection

- **`.py` `.js` `.ts` `.rs` `.go` `.java` `.kt`** → `["linting", "type_checking", "formatting"]`
- **Dockerfile / docker-compose** → `["container"]`
- **Terraform / K8s / IaC YAML** → `["iac"]`
- **`package.json` `requirements.txt` `Cargo.toml`** → `["sca"]`
- **Auth, crypto, SQL code** → `["sast"]`
- **Before commit or mixed changes** → `["all"]`

### When NOT to Scan

- User explicitly says "don't scan", "skip checks", or "no linting"
- You only read/explored code without making any changes
- You only edited non-code files (markdown, docs, comments-only)
<!-- lucidshark:end -->
"""

# Claude Code hooks configuration for .claude/settings.json
# PostToolUse hook on Edit/Write/NotebookEdit echoes a scan reminder
# after every code edit, providing a persistent nudge in context.
LUCIDSHARK_HOOKS_CONFIG: Dict[str, Any] = {
    "hooks": {
        "PostToolUse": [
            {
                "matcher": "Edit|Write|NotebookEdit",
                "hooks": [
                    {
                        "type": "command",
                        "command": (
                            "echo '[LucidShark] Code modified — scan before completing"
                            " task (mcp__lucidshark__scan or lucidshark scan"
                            " --fix --format ai)'"
                        ),
                    }
                ],
            }
        ]
    }
}

# Tool-neutral scan guidance shared by the Cursor and Windsurf rule files.
# These IDEs expose MCP tools by their plain name, so the text refers to
# "the lucidshark `scan` MCP tool" instead of Claude's mcp__server__tool form.
LUCIDSHARK_AGENT_RULES_BODY = """\
# LucidShark: Scan After Every Code Change

LucidShark is the project's code quality and security scanner (linting, type
checking, formatting, SAST, SCA, IaC, container, testing, coverage, duplication).
It runs as the `lucidshark` MCP server.

You MUST run a LucidShark scan after editing code files. Do not report a task
as complete until the scan shows zero issues.

## When to Scan

- After every code edit: scan the changed files with auto-fix enabled
- After fixing bugs: verify the fix did not introduce new issues
- Before reporting a task as done
- Before creating commits: run a full scan with all domains

## How to Scan

Preferred: call the lucidshark `scan` MCP tool.

| Situation | `scan` tool arguments |
|---|---|
| After edits (auto-fix, changed files) | `fix: true` |
| Targeted domains | `domains: ["linting", "type_checking"]` |
| Run tests | `domains: ["testing"]` |
| Security | `domains: ["sast", "sca"]` |
| Before commits | `domains: ["all"]` |
| Specific files | `files: ["path/to/file.py"]` |
| Entire project, not just changed files | `all_files: true` |

Other lucidshark MCP tools: `check_file` (single file), `get_fix_instructions`
and `apply_fix` (per issue), `autoconfigure` (AI-assisted `lucidshark.yml` setup).

CLI fallback if the MCP server is unavailable (`./lucidshark` for the binary
install, `lucidshark` for pip):

```bash
./lucidshark scan --fix --format ai           # after edits
./lucidshark scan --all --format ai           # before commits
./lucidshark scan --files path/to/file.py --format ai
```

By default LucidShark scans only git-changed files. Use `all_files: true`
(MCP) or `--all-files` (CLI) to scan the whole project.

## Domain Selection

- `.py` `.js` `.ts` `.rs` `.go` `.java` `.kt`: `["linting", "type_checking", "formatting"]`
- Dockerfile / docker-compose: `["container"]`
- Terraform / K8s / IaC YAML: `["iac"]`
- `package.json` `requirements.txt` `Cargo.toml`: `["sca"]`
- Auth, crypto, SQL code: `["sast"]`
- Before commit or mixed changes: `["all"]`

## When NOT to Scan

- The user explicitly says "don't scan" or "skip checks"
- You only read code without changing it
- You only edited non-code files (markdown, docs)
"""

# Cursor project rule (.cursor/rules/lucidshark.mdc). alwaysApply: true puts
# the rule in context for every request.
LUCIDSHARK_CURSOR_RULE_CONTENT = (
    "---\n"
    "description: Run LucidShark quality and security scans after every code change\n"
    "alwaysApply: true\n"
    "---\n\n" + LUCIDSHARK_AGENT_RULES_BODY
)

# Windsurf workspace rule (.windsurf/rules/lucidshark.md).
LUCIDSHARK_WINDSURF_RULE_CONTENT = (
    "---\ntrigger: always_on\n---\n\n" + LUCIDSHARK_AGENT_RULES_BODY
)

# Windsurf (renamed Devin Desktop) reads MCP servers from a global per-user
# file, and newer releases also from a project .devin/mcp_config.json. init
# does not write either; it prints a snippet with absolute paths that works
# in both locations.
WINDSURF_GLOBAL_MCP_CONFIG = "~/.codeium/windsurf/mcp_config.json"
WINDSURF_PROJECT_MCP_CONFIG = ".devin/mcp_config.json"

# Aider has no MCP support. It runs lint-cmd after each edit with the edited
# file names appended, and treats a non-zero exit code as lint failure, so
# --files must come last and --fail-on low guarantees a non-zero exit when
# any issue is found.
AIDER_LINT_ARGS = "scan --linting --type-checking --fail-on low --format ai --files"

# Markers for the managed block in .aider.conf.yml (YAML comments).
AIDER_CONF_START_MARKER = "# lucidshark:start"
AIDER_CONF_END_MARKER = "# lucidshark:end"

# Managed section appended to CONVENTIONS.md, which init adds to aider's
# read-only context via the `read` key in .aider.conf.yml.
LUCIDSHARK_CONVENTIONS_SECTION = """\

<!-- lucidshark:start - managed by lucidshark init, do not edit manually -->
## LucidShark: Code Quality Gate

This project uses LucidShark for linting, type checking, formatting, security
and test checks. Aider runs LucidShark automatically as the lint command after
each edit (`lint-cmd` in `.aider.conf.yml`). When it reports issues, fix them
before moving on.

- Treat every LucidShark issue as a required fix, not a suggestion.
- Do not consider a task done while LucidShark reports issues.
- Before committing, ask the user to run the full scan, or run it with
  `/run ./lucidshark scan --all --format ai` (binary install) or
  `/run lucidshark scan --all --format ai` (pip install).
- Use `--all-files` to scan the whole project instead of only changed files.
<!-- lucidshark:end -->
"""

# Valid tool selectors for `lucidshark init`, in setup order.
INIT_TOOLS = ("claude_code", "cursor", "windsurf", "aider")


class InitCommand(Command):
    """Configure AI tool integration and generate lucidshark.yml.

    By default this sets up .mcp.json, .claude/skills/, .claude/CLAUDE.md, and
    .claude/settings.json so Claude Code can use LucidShark's MCP tools.
    --cursor, --windsurf, --aider and --all-tools configure other tools.

    It also detects project languages and generates a lucidshark.yml configuration
    with all domains enabled and all supported tools for the detected languages.
    Use --no-config to skip config generation.
    """

    def __init__(self, version: str):
        """Initialize InitCommand.

        Args:
            version: Current lucidshark version string.
        """
        self._version = version

    @property
    def name(self) -> str:
        """Command identifier."""
        return "init"

    def execute(self, args: Namespace, config: "LucidSharkConfig | None" = None) -> int:
        """Execute the init command.

        Args:
            args: Parsed command-line arguments.
            config: Optional LucidShark configuration (unused).

        Returns:
            Exit code.
        """
        dry_run = getattr(args, "dry_run", False)
        force = getattr(args, "force", False)
        remove = getattr(args, "remove", False)
        no_config = getattr(args, "no_config", False)

        setup_steps = {
            "claude_code": self._setup_claude_code,
            "cursor": self._setup_cursor,
            "windsurf": self._setup_windsurf,
            "aider": self._setup_aider,
        }

        success = True
        for index, tool in enumerate(self._selected_tools(args)):
            if index:
                print()
            if not setup_steps[tool](dry_run, force, remove):
                success = False

        # Generate lucidshark.yml from language templates
        if success and not remove and not no_config:
            try:
                self._generate_config(dry_run, force)
            except Exception as e:
                print(f"\n  Warning: Config generation failed: {e}")
                print("  You can generate config later with: lucidshark init --force")

        if success and not dry_run:
            print("\nRestart your AI tool to apply changes.")

        return EXIT_SUCCESS if success else EXIT_INVALID_USAGE

    @staticmethod
    def _selected_tools(args: Namespace) -> List[str]:
        """Return the AI tools to configure, in setup order.

        With no tool flag, only Claude Code is configured (the historical
        default). --all-tools selects every supported tool.

        Args:
            args: Parsed command-line arguments.

        Returns:
            List of tool identifiers from INIT_TOOLS.
        """
        if getattr(args, "all_tools", False):
            return list(INIT_TOOLS)
        selected = [tool for tool in INIT_TOOLS if getattr(args, tool, False)]
        return selected or ["claude_code"]

    def _setup_claude_code(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Claude Code MCP settings in project .mcp.json.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing config.
            remove: If True, remove LucidShark from config.

        Returns:
            True if successful.
        """
        print("Configuring Claude Code (.mcp.json)...")

        config_path = self._get_claude_code_config_path()
        if config_path is None:
            print("  Could not determine Claude Code config location.")
            return False

        mcp_success = self._configure_mcp_tool(
            tool_name="Claude Code",
            config_path=config_path,
            config_key="mcpServers",
            dry_run=dry_run,
            force=force,
            remove=remove,
            use_portable_path=True,  # .mcp.json is version controlled
        )

        # Configure Claude skill
        skill_success = self._configure_claude_skill(
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

        # Configure CLAUDE.md with proactive scanning instructions
        claude_md_success = self._configure_claude_md(
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

        # Configure Claude Code hooks for scan reminders
        hooks_success = self._configure_claude_hooks(
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

        return mcp_success and skill_success and claude_md_success and hooks_success

    def _generate_config(
        self,
        dry_run: bool = False,
        force: bool = False,
    ) -> bool:
        """Generate lucidshark.yml from detected languages and templates.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing lucidshark.yml.

        Returns:
            True if successful.
        """
        config_path = Path.cwd() / "lucidshark.yml"

        # Check for existing config
        if config_path.exists() and not force:
            print(f"\n  lucidshark.yml already exists at {config_path}")
            print("  Use --force to overwrite.")
            return True

        print("\nGenerating lucidshark.yml...")

        # Detect languages
        from lucidshark.detection.detector import CodebaseDetector

        detector = CodebaseDetector()
        context = detector.detect(Path.cwd())

        if not context.languages:
            print("  No supported languages detected. Skipping config generation.")
            return True

        lang_names = [lang.name for lang in context.languages]
        print(f"  Detected languages: {', '.join(lang_names)}")

        # Compose config from templates
        from lucidshark.generation.template_composer import TemplateComposer

        composer = TemplateComposer()

        if dry_run:
            composer.compose(context)
            print(f"  Would write lucidshark.yml with {len(lang_names)} language(s)")
            return True

        output_path = composer.write(context, config_path)
        print(f"  Generated {output_path}")
        return True

    def _find_lucidshark_path(self, portable: bool = False) -> Optional[str]:
        """Find the lucidshark executable path.

        Searches in order:
        1. Local binary in project root (./lucidshark) - for standalone installs
        2. PATH via shutil.which (only if not portable)
        3. Same directory as current Python interpreter (for venv installs)

        Args:
            portable: If True, return a relative path suitable for version control.

        Returns:
            Path to lucidshark executable, or None if not found.
        """
        cwd = Path.cwd()

        # First check for local binary in project root (standalone install)
        local_binary = cwd / "lucidshark"

        if local_binary.exists() and local_binary.is_file():
            # For local binary, always return relative path
            return "./lucidshark"

        # Then try PATH (only if not looking for portable path)
        if not portable:
            lucidshark_path = shutil.which("lucidshark")
            if lucidshark_path:
                return lucidshark_path

        # Try to find in the same directory as the Python interpreter
        # This handles venv installations where lucidshark isn't in global PATH
        python_dir = Path(sys.executable).parent

        candidates = [
            python_dir / "lucidshark",
        ]

        for candidate in candidates:
            if candidate.exists():
                if portable:
                    # Try to make it relative to cwd for version control
                    try:
                        relative = candidate.relative_to(cwd)
                        return str(relative)
                    except ValueError:
                        # Not relative to cwd, can't use portable path
                        pass
                else:
                    return str(candidate)

        # For portable, fall back to just "lucidshark"
        if portable:
            return None

        return None

    def _build_mcp_config(self, lucidshark_path: Optional[str]) -> dict:
        """Build MCP server configuration.

        Args:
            lucidshark_path: Full path to lucidshark executable, or None.

        Returns:
            MCP server configuration dict.
        """
        command = lucidshark_path if lucidshark_path else "lucidshark"
        return {
            "command": command,
            "args": LUCIDSHARK_MCP_ARGS.copy(),
        }

    def _configure_mcp_tool(
        self,
        tool_name: str,
        config_path: Path,
        config_key: str,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
        use_portable_path: bool = False,
    ) -> bool:
        """Configure an MCP-compatible tool.

        Args:
            tool_name: Name of the tool for display.
            config_path: Path to the config file.
            config_key: Key in the config for MCP servers.
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing config.
            remove: If True, remove LucidShark from config.
            use_portable_path: If True, use relative path for version control.

        Returns:
            True if successful.
        """
        # Find lucidshark executable
        lucidshark_path = self._find_lucidshark_path(portable=use_portable_path)
        if lucidshark_path:
            print(f"  Using lucidshark command: {lucidshark_path}")
        elif not dry_run:
            print("  Warning: 'lucidshark' command not found in PATH or venv.")
            print("  Using 'lucidshark' as command (must be in PATH at runtime).")

        # Read existing config
        config, error = self._read_json_config(config_path)
        if error and not remove:
            # For new config, start fresh
            config = {}

        # Get or create the MCP servers section
        mcp_servers = config.get(config_key, {})

        if remove:
            # Remove LucidShark from config
            if "lucidshark" in mcp_servers:
                if dry_run:
                    print(f"  Would remove lucidshark from {config_path}")
                else:
                    del mcp_servers["lucidshark"]
                    config[config_key] = mcp_servers
                    if not mcp_servers:
                        del config[config_key]
                    self._write_json_config(config_path, config)
                    print(f"  Removed lucidshark from {config_path}")
            else:
                print(f"  lucidshark not found in {config_path}")
            return True

        # Check if LucidShark is already configured
        if "lucidshark" in mcp_servers and not force:
            print(f"  LucidShark already configured in {config_path}")
            print("  Use --force to overwrite.")
            return True

        # Add LucidShark config with found path
        mcp_config = self._build_mcp_config(lucidshark_path)
        mcp_servers["lucidshark"] = mcp_config
        config[config_key] = mcp_servers

        if dry_run:
            print(f"  Would write to {config_path}:")
            print(f"    {json.dumps(config, indent=2)}")
            return True

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write config
        success = self._write_json_config(config_path, config)
        if success:
            print(f"  Added lucidshark to {config_path}")
            self._print_available_tools()
        return success

    def _configure_claude_skill(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Claude skill for lucidshark.

        Creates a skill file at .claude/skills/lucidshark/SKILL.md

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing skill.
            remove: If True, remove lucidshark skill.

        Returns:
            True if successful.
        """
        print("Configuring Claude skill...")
        skill_file = Path.cwd() / ".claude" / "skills" / "lucidshark" / "SKILL.md"
        return self._configure_owned_file(
            skill_file,
            LUCIDSHARK_SKILL_CONTENT.lstrip(),
            label="lucidshark skill",
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

    def _configure_owned_file(
        self,
        path: Path,
        content: str,
        label: str,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Create, overwrite or remove a file owned entirely by LucidShark.

        Used for files that only LucidShark writes (skills, IDE rule files).
        On removal, the parent directory is removed too if it is left empty.

        Args:
            path: File to manage.
            content: Full file content to write.
            label: Human readable name used in messages.
            dry_run: If True, only show what would be done.
            force: If True, overwrite an existing file.
            remove: If True, remove the file.

        Returns:
            True if successful.
        """
        if remove:
            if not path.exists():
                print(f"  {label[0].upper()}{label[1:]} not found")
                return True
            if dry_run:
                print(f"  Would remove {path}")
                return True
            try:
                path.unlink()
                if path.parent.exists() and not any(path.parent.iterdir()):
                    path.parent.rmdir()
                print(f"  Removed {label}")
                return True
            except Exception as e:
                print(f"  Error removing {label}: {e}")
                return False

        if path.exists() and not force:
            print(f"  {label[0].upper()}{label[1:]} already exists at {path}")
            print("  Use --force to overwrite.")
            return True

        if dry_run:
            print(f"  Would create {label} at {path}")
            return True

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            print(f"  Created {label} at {path}")
            return True
        except Exception as e:
            print(f"  Error creating {label}: {e}")
            return False

    def _configure_claude_md(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure CLAUDE.md with LucidShark proactive scanning instructions.

        CLAUDE.md is loaded into Claude's system prompt for every conversation,
        making it the most reliable way to ensure proactive scanning behavior.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing LucidShark section.
            remove: If True, remove LucidShark section from CLAUDE.md.

        Returns:
            True if successful.
        """
        print("Configuring .claude/CLAUDE.md...")
        return self._configure_markdown_section(
            Path.cwd() / ".claude" / "CLAUDE.md",
            LUCIDSHARK_CLAUDE_MD_SECTION,
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

    def _configure_markdown_section(
        self,
        md_path: Path,
        section: str,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Add, update or remove the LucidShark managed section of a markdown file.

        Uses HTML comment markers to manage the LucidShark section so it can
        be updated or removed without affecting user content. The file is
        deleted on removal only if nothing but whitespace remains.

        Args:
            md_path: Markdown file to manage.
            section: Managed section content, including markers.
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing LucidShark section.
            remove: If True, remove the LucidShark section.

        Returns:
            True if successful.
        """
        start_marker = "<!-- lucidshark:start"
        end_marker = "<!-- lucidshark:end -->"

        # Read existing content
        existing_content = ""
        if md_path.exists():
            try:
                existing_content = md_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  Error reading {md_path}: {e}")
                return False

        has_section = (
            start_marker in existing_content and end_marker in existing_content
        )

        if remove:
            if not has_section:
                print(f"  LucidShark section not found in {md_path}")
                return True
            if dry_run:
                print(f"  Would remove LucidShark section from {md_path}")
                return True
            new_content = self._remove_managed_section(
                existing_content, start_marker, end_marker
            )
            return self._write_or_delete(
                md_path, new_content, f"Removed LucidShark section from {md_path}"
            )

        if has_section and not force:
            print(f"  LucidShark section already exists in {md_path}")
            print("  Use --force to overwrite.")
            return True

        if dry_run:
            action = "update" if has_section else "create"
            print(f"  Would {action} LucidShark section in {md_path}")
            return True

        if has_section:
            new_content = self._replace_managed_section(
                existing_content, start_marker, end_marker, section
            )
        else:
            # Append to existing content (or create new file)
            new_content = existing_content.rstrip() + "\n" + section

        try:
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(new_content, encoding="utf-8")
            action = "Updated" if has_section else "Added"
            print(f"  {action} LucidShark section in {md_path}")
            return True
        except Exception as e:
            print(f"  Error writing {md_path}: {e}")
            return False

    @staticmethod
    def _write_or_delete(path: Path, content: str, message: str) -> bool:
        """Write content to path, or delete path if content is only whitespace.

        Args:
            path: File to update.
            content: New content.
            message: Message printed after a successful write.

        Returns:
            True if successful.
        """
        try:
            if content.strip():
                path.write_text(content, encoding="utf-8")
                print(f"  {message}")
            else:
                path.unlink()
                print(f"  Removed {path} (was empty after removal)")
            return True
        except Exception as e:
            print(f"  Error updating {path}: {e}")
            return False

    def _setup_cursor(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Cursor: project MCP server and an always-applied rule.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing config.
            remove: If True, remove LucidShark from Cursor config.

        Returns:
            True if successful.
        """
        print("Configuring Cursor (.cursor/mcp.json)...")
        cursor_dir = Path.cwd() / ".cursor"
        mcp_success = self._configure_mcp_tool(
            tool_name="Cursor",
            config_path=cursor_dir / "mcp.json",
            config_key="mcpServers",
            dry_run=dry_run,
            force=force,
            remove=remove,
            use_portable_path=True,  # project config, version controlled
        )

        print("Configuring Cursor rule (.cursor/rules/lucidshark.mdc)...")
        rule_success = self._configure_owned_file(
            cursor_dir / "rules" / "lucidshark.mdc",
            LUCIDSHARK_CURSOR_RULE_CONTENT,
            label="Cursor rule",
            dry_run=dry_run,
            force=force,
            remove=remove,
        )
        return mcp_success and rule_success

    def _setup_windsurf(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Windsurf: workspace rule plus a printed MCP snippet.

        Windsurf reads MCP servers from a global per-user file, which init
        never writes. The snippet and path are printed instead.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing rule.
            remove: If True, remove the LucidShark rule.

        Returns:
            True if successful.
        """
        print("Configuring Windsurf rule (.windsurf/rules/lucidshark.md)...")
        rule_success = self._configure_owned_file(
            Path.cwd() / ".windsurf" / "rules" / "lucidshark.md",
            LUCIDSHARK_WINDSURF_RULE_CONTENT,
            label="Windsurf rule",
            dry_run=dry_run,
            force=force,
            remove=remove,
        )

        if remove:
            print(
                "  Remove the 'lucidshark' entry from "
                f"{WINDSURF_GLOBAL_MCP_CONFIG} or {WINDSURF_PROJECT_MCP_CONFIG} "
                "manually if you added it."
            )
            return rule_success

        snippet = {"mcpServers": {"lucidshark": self._build_windsurf_mcp_config()}}
        print(
            "  init does not write Windsurf MCP config. Merge this into "
            f"{WINDSURF_GLOBAL_MCP_CONFIG} (or {WINDSURF_PROJECT_MCP_CONFIG} "
            "in Devin Desktop):"
        )
        for line in json.dumps(snippet, indent=2).splitlines():
            print(f"    {line}")
        return rule_success

    def _build_windsurf_mcp_config(self) -> Dict[str, Any]:
        """Build an MCP server entry usable from a global (non-project) config.

        A global config has no project working directory, so the command and
        the project path are made absolute.

        Returns:
            MCP server configuration dict.
        """
        cwd = Path.cwd()
        lucidshark_path = self._find_lucidshark_path(portable=False)
        if lucidshark_path and lucidshark_path.startswith("./"):
            lucidshark_path = str(cwd / lucidshark_path[2:])
        config = self._build_mcp_config(lucidshark_path)
        config["args"] = [*LUCIDSHARK_MCP_ARGS[:-1], str(cwd)]
        return config

    def _setup_aider(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Aider: lint-cmd in .aider.conf.yml and CONVENTIONS.md.

        Aider has no MCP support. LucidShark runs as aider's lint command,
        and CONVENTIONS.md (loaded via `read`) carries the guidance.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing LucidShark sections.
            remove: If True, remove LucidShark sections.

        Returns:
            True if successful.
        """
        print("Configuring Aider (.aider.conf.yml)...")
        conf_success = self._configure_aider_conf(dry_run, force, remove)

        print("Configuring Aider conventions (CONVENTIONS.md)...")
        conventions_success = self._configure_markdown_section(
            Path.cwd() / "CONVENTIONS.md",
            LUCIDSHARK_CONVENTIONS_SECTION,
            dry_run=dry_run,
            force=force,
            remove=remove,
        )
        return conf_success and conventions_success

    def _configure_aider_conf(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Add, update or remove the LucidShark managed block in .aider.conf.yml.

        The block is delimited by YAML comment markers and appended as text,
        so user keys and comments are never rewritten. Keys the user already
        sets outside the block are left alone and reported instead.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, rewrite an existing LucidShark block.
            remove: If True, remove the LucidShark block.

        Returns:
            True if successful.
        """
        conf_path = Path.cwd() / ".aider.conf.yml"
        existing_content = ""
        if conf_path.exists():
            try:
                existing_content = conf_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"  Error reading {conf_path}: {e}")
                return False

        has_block = (
            AIDER_CONF_START_MARKER in existing_content
            and AIDER_CONF_END_MARKER in existing_content
        )
        user_content = (
            self._remove_managed_section(
                existing_content, AIDER_CONF_START_MARKER, AIDER_CONF_END_MARKER
            )
            if has_block
            else existing_content
        )

        if remove:
            if not has_block:
                print(f"  LucidShark settings not found in {conf_path}")
                return True
            if dry_run:
                print(f"  Would remove LucidShark settings from {conf_path}")
                return True
            return self._write_or_delete(
                conf_path, user_content, f"Removed LucidShark settings from {conf_path}"
            )

        if has_block and not force:
            print(f"  LucidShark settings already exist in {conf_path}")
            print("  Use --force to overwrite.")
            return True

        user_keys = self._parse_yaml_mapping(user_content, conf_path)
        if user_keys is None:
            return False

        block = self._build_aider_block(user_keys)
        if dry_run:
            action = "update" if has_block else "create"
            print(f"  Would {action} LucidShark settings in {conf_path}:")
            for line in block.splitlines():
                print(f"    {line}")
            return True

        new_content = user_content.rstrip()
        new_content = (new_content + "\n\n" if new_content else "") + block
        try:
            conf_path.write_text(new_content, encoding="utf-8")
            action = "Updated" if has_block else "Added"
            print(f"  {action} LucidShark settings in {conf_path}")
            return True
        except Exception as e:
            print(f"  Error writing {conf_path}: {e}")
            return False

    @staticmethod
    def _parse_yaml_mapping(content: str, path: Path) -> Optional[Dict[str, Any]]:
        """Parse YAML content that must be a mapping (or empty).

        Args:
            content: YAML text.
            path: Source path, for error messages.

        Returns:
            The parsed mapping, or None if the content is invalid.
        """
        import yaml

        try:
            data = yaml.safe_load(content) if content.strip() else {}
        except yaml.YAMLError as e:
            print(f"  Invalid YAML in {path}: {e}")
            return None
        if data is None:
            return {}
        if not isinstance(data, dict):
            print(f"  {path} is not a YAML mapping; not modifying it.")
            return None
        return data

    def _build_aider_block(self, user_keys: Dict[str, Any]) -> str:
        """Build the managed .aider.conf.yml block for keys the user has not set.

        Args:
            user_keys: Keys already set by the user outside the managed block.

        Returns:
            Managed block text including markers.
        """
        import yaml

        lucidshark_cmd = self._find_lucidshark_path(portable=True) or "lucidshark"
        wanted: Dict[str, Any] = {
            "lint-cmd": f"{lucidshark_cmd} {AIDER_LINT_ARGS}",
            "auto-lint": True,
            "read": ["CONVENTIONS.md"],
        }

        settings: Dict[str, Any] = {}
        for key, value in wanted.items():
            if key not in user_keys:
                settings[key] = value
                continue
            if key == "read":
                user_read = user_keys[key]
                listed = user_read if isinstance(user_read, list) else [user_read]
                if "CONVENTIONS.md" not in listed:
                    print(
                        "  Note: 'read' is already set; add CONVENTIONS.md to it "
                        "so aider loads the LucidShark conventions."
                    )
            else:
                print(f"  Note: '{key}' is already set; leaving your value unchanged.")

        lines = [
            f"{AIDER_CONF_START_MARKER} - managed by lucidshark init, do not edit manually"
        ]
        if settings:
            lines.append(
                yaml.safe_dump(
                    settings, sort_keys=False, default_flow_style=False
                ).rstrip()
            )
        lines.append(AIDER_CONF_END_MARKER)
        return "\n".join(lines) + "\n"

    def _configure_claude_hooks(
        self,
        dry_run: bool = False,
        force: bool = False,
        remove: bool = False,
    ) -> bool:
        """Configure Claude Code hooks and enabled MCP servers in .claude/settings.json.

        Adds a PostToolUse hook that echoes a scan reminder after every
        code edit (Edit, Write, NotebookEdit). This provides a persistent
        nudge in Claude's context to run scans.

        Also adds "lucidshark" to the enabledMcpjsonServers array to enable
        the MCP server from .mcp.json.

        Args:
            dry_run: If True, only show what would be done.
            force: If True, overwrite existing hooks.
            remove: If True, remove LucidShark hooks and enabled server entry.

        Returns:
            True if successful.
        """
        settings_path = Path.cwd() / ".claude" / "settings.json"
        hooks_key = "hooks"
        enabled_mcp_key = "enabledMcpjsonServers"

        print("Configuring Claude Code hooks (.claude/settings.json)...")

        # Read existing settings
        existing_settings: Dict[str, Any] = {}
        if settings_path.exists():
            try:
                content = settings_path.read_text(encoding="utf-8").strip()
                if content:
                    existing_settings = json.loads(content)
            except (json.JSONDecodeError, Exception) as e:
                print(f"  Error reading {settings_path}: {e}")
                if not remove:
                    return False

        has_hooks = hooks_key in existing_settings and self._has_lucidshark_hooks(
            existing_settings.get(hooks_key, {})
        )
        has_enabled_server = self._has_lucidshark_in_enabled_servers(
            existing_settings.get(enabled_mcp_key, [])
        )

        if remove:
            changes_made = False
            if has_hooks:
                if dry_run:
                    print(f"  Would remove LucidShark hooks from {settings_path}")
                else:
                    self._remove_lucidshark_hooks(existing_settings)
                    print(f"  Removed LucidShark hooks from {settings_path}")
                    changes_made = True
            else:
                print(f"  LucidShark hooks not found in {settings_path}")

            if has_enabled_server:
                if dry_run:
                    print(
                        f"  Would remove lucidshark from enabledMcpjsonServers in {settings_path}"
                    )
                else:
                    self._remove_from_enabled_mcp_servers(existing_settings)
                    changes_made = True
            else:
                print(
                    f"  lucidshark not found in enabledMcpjsonServers in {settings_path}"
                )

            if changes_made and not dry_run:
                # If settings is now empty (or only has empty structures), clean up
                if not existing_settings or existing_settings == {}:
                    try:
                        settings_path.unlink()
                        print(f"  Removed {settings_path} (was empty after removal)")
                    except Exception as e:
                        print(f"  Error removing {settings_path}: {e}")
                        return False
                else:
                    success = self._write_json_config(settings_path, existing_settings)
                    if success:
                        print(
                            f"  Removed LucidShark configuration from {settings_path}"
                        )
                    return success
            return True

        if has_hooks and has_enabled_server and not force:
            print(f"  LucidShark already configured in {settings_path}")
            print("  Use --force to overwrite.")
            return True

        if dry_run:
            action = "update" if (has_hooks or has_enabled_server) else "create"
            print(f"  Would {action} LucidShark configuration in {settings_path}")
            return True

        # Merge hooks into existing settings, preserving non-LucidShark hooks
        new_settings = dict(existing_settings)

        # Configure hooks
        # Remove any existing LucidShark hooks first so we don't duplicate
        if has_hooks:
            self._remove_lucidshark_hooks(new_settings)
        # Merge: add LucidShark PostToolUse hooks alongside existing hooks
        existing_hooks = new_settings.get(hooks_key, {})
        new_hooks = LUCIDSHARK_HOOKS_CONFIG[hooks_key]
        for event_type, hook_groups in new_hooks.items():
            if event_type in existing_hooks:
                existing_hooks[event_type].extend(hook_groups)
            else:
                existing_hooks[event_type] = list(hook_groups)
        new_settings[hooks_key] = existing_hooks

        # Configure enabledMcpjsonServers
        self._add_to_enabled_mcp_servers(new_settings)

        try:
            settings_path.parent.mkdir(parents=True, exist_ok=True)
            success = self._write_json_config(settings_path, new_settings)
            if success:
                action = "Updated" if (has_hooks or has_enabled_server) else "Added"
                print(f"  {action} LucidShark configuration in {settings_path}")
            return success
        except Exception as e:
            print(f"  Error writing {settings_path}: {e}")
            return False

    @staticmethod
    def _has_lucidshark_hooks(hooks: Dict[str, Any]) -> bool:
        """Check if hooks config contains LucidShark hooks.

        Args:
            hooks: The hooks configuration dict.

        Returns:
            True if LucidShark hooks are present.
        """
        post_tool_use = hooks.get("PostToolUse", [])
        for hook_group in post_tool_use:
            matcher = hook_group.get("matcher", "")
            if "Edit" in matcher and "Write" in matcher and "NotebookEdit" in matcher:
                for hook in hook_group.get("hooks", []):
                    if "LucidShark" in hook.get("command", ""):
                        return True
        return False

    @staticmethod
    def _remove_lucidshark_hooks(settings: Dict[str, Any]) -> None:
        """Remove LucidShark hooks from settings in-place.

        Args:
            settings: The settings dict to modify.
        """
        hooks = settings.get("hooks", {})
        post_tool_use = hooks.get("PostToolUse", [])

        # Filter out LucidShark hook groups
        filtered = []
        for hook_group in post_tool_use:
            matcher = hook_group.get("matcher", "")
            is_lucidshark = (
                "Edit" in matcher
                and "Write" in matcher
                and "NotebookEdit" in matcher
                and any(
                    "LucidShark" in h.get("command", "")
                    for h in hook_group.get("hooks", [])
                )
            )
            if not is_lucidshark:
                filtered.append(hook_group)

        if filtered:
            hooks["PostToolUse"] = filtered
        else:
            hooks.pop("PostToolUse", None)

        if hooks:
            settings["hooks"] = hooks
        else:
            settings.pop("hooks", None)

    @staticmethod
    def _has_lucidshark_in_enabled_servers(enabled_servers: List[str]) -> bool:
        """Check if lucidshark is in the enabledMcpjsonServers list.

        Args:
            enabled_servers: List of enabled MCP server names.

        Returns:
            True if "lucidshark" is present.
        """
        return "lucidshark" in enabled_servers

    @staticmethod
    def _add_to_enabled_mcp_servers(settings: Dict[str, Any]) -> None:
        """Add lucidshark to enabledMcpjsonServers in settings in-place.

        Preserves all other entries in the list.

        Args:
            settings: The settings dict to modify.
        """
        enabled_servers = settings.get("enabledMcpjsonServers", [])
        if "lucidshark" not in enabled_servers:
            enabled_servers.append("lucidshark")
        settings["enabledMcpjsonServers"] = enabled_servers

    @staticmethod
    def _remove_from_enabled_mcp_servers(settings: Dict[str, Any]) -> None:
        """Remove lucidshark from enabledMcpjsonServers in settings in-place.

        Preserves all other entries in the list.

        Args:
            settings: The settings dict to modify.
        """
        enabled_servers = settings.get("enabledMcpjsonServers", [])
        if "lucidshark" in enabled_servers:
            enabled_servers.remove("lucidshark")
        if enabled_servers:
            settings["enabledMcpjsonServers"] = enabled_servers
        else:
            settings.pop("enabledMcpjsonServers", None)

    @staticmethod
    def _process_managed_section(
        content: str,
        start_marker: str,
        end_marker: str,
        replacement: Optional[str] = None,
    ) -> str:
        """Process a managed section delimited by markers.

        Args:
            content: The full file content.
            start_marker: Start of the managed section (prefix match).
            end_marker: End of the managed section (exact line match).
            replacement: If provided, replaces section with this content.
                         If None, section is removed.

        Returns:
            Content with the managed section processed.
        """
        lines = content.split("\n")
        result: List[str] = []
        in_section = False
        replaced = False
        for line in lines:
            if not in_section and start_marker in line:
                in_section = True
                if replacement is not None and not replaced:
                    result.append(replacement.rstrip())
                    replaced = True
            elif in_section and end_marker in line:
                in_section = False
            elif not in_section:
                result.append(line)
        return "\n".join(result)

    @staticmethod
    def _remove_managed_section(
        content: str, start_marker: str, end_marker: str
    ) -> str:
        """Remove a managed section delimited by markers from content."""
        return InitCommand._process_managed_section(content, start_marker, end_marker)

    @staticmethod
    def _replace_managed_section(
        content: str, start_marker: str, end_marker: str, new_section: str
    ) -> str:
        """Replace a managed section with new content."""
        return InitCommand._process_managed_section(
            content, start_marker, end_marker, new_section
        )

    def _get_claude_code_config_path(self) -> Optional[Path]:
        """Get the Claude Code MCP config file path.

        Returns:
            Path to .mcp.json at project root.
        """
        # Claude Code project-scoped MCP servers in .mcp.json
        return Path.cwd() / ".mcp.json"

    def _read_json_config(self, path: Path) -> Tuple[Dict[str, Any], Optional[str]]:
        """Read a JSON config file.

        Args:
            path: Path to the config file.

        Returns:
            Tuple of (config dict, error message or None).
        """
        if not path.exists():
            return {}, f"Config file does not exist: {path}"

        try:
            with open(path, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}, None
                return json.loads(content), None
        except json.JSONDecodeError as e:
            return {}, f"Invalid JSON in {path}: {e}"
        except Exception as e:
            return {}, f"Error reading {path}: {e}"

    def _write_json_config(self, path: Path, config: Dict[str, Any]) -> bool:
        """Write a JSON config file.

        Args:
            path: Path to the config file.
            config: Configuration dictionary.

        Returns:
            True if successful.
        """
        try:
            with open(path, "w") as f:
                json.dump(config, f, indent=2)
                f.write("\n")
            return True
        except Exception as e:
            print(f"  Error writing {path}: {e}")
            return False

    def _print_available_tools(self) -> None:
        """Print available CLI commands."""
        print("\n  Available commands:")
        print("    Binary users (install.sh):  Use ./lucidshark")
        print("    Pip users (pip install):    Use lucidshark")
        print("")
        print("    ./lucidshark scan --format ai   # Run quality checks")
        print("    ./lucidshark scan --fix         # Auto-fix linting issues")
        print("    ./lucidshark scan --all         # Full scan (all domains)")
        print("    ./lucidshark status             # Show configuration")
        print("    ./lucidshark validate           # Validate lucidshark.yml")
        print("    ./lucidshark help               # Show documentation")
        print("\n  MCP server:")
        print("    ./lucidshark serve --mcp        # Run as MCP server")
