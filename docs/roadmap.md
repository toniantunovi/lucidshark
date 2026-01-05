# LucidScan Roadmap

> **Vision**: The trust layer for AI-assisted development

LucidScan unifies code quality tools (linting, type checking, security, testing, coverage) into a single pipeline that auto-configures for any project and integrates with AI coding tools like Claude Code and Cursor.

---

## Roadmap Overview

```
         v0.1.x                v0.2                v0.3                v0.4                v0.5               v1.0
           │                    │                   │                   │                   │                   │
    ───────●────────────────────●───────────────────●───────────────────●───────────────────●───────────────────●───────
           │                    │                   │                   │                   │                   │
     Current State         Foundation          Code Quality          Full Pipeline       AI Integration      Production
                                                                                                               Ready
    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │ Security     │    │ init command │    │ Linting      │    │ Testing      │    │ MCP server   │    │ Docs         │
    │ scanning     │    │ Codebase     │    │ Type checking│    │ Coverage     │    │ File watcher │    │ Performance  │
    │ (Trivy,      │    │ detection    │    │ Auto-fix     │    │ Full pipeline│    │ AI instruct  │    │ Stability    │
    │ OpenGrep,    │    │ CI generation│    │              │    │              │    │ format       │    │              │
    │ Checkov)     │    │              │    │              │    │              │    │              │    │              │
    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## Current State (v0.1.x)

LucidScan has a working security scanning foundation:

| Component | Status |
|-----------|--------|
| CLI framework | ✅ Complete |
| Plugin system (entry points) | ✅ Complete |
| Pipeline orchestrator | ✅ Complete |
| Configuration system | ✅ Complete |
| Security scanners | ✅ Trivy, OpenGrep, Checkov |
| Reporters | ✅ JSON, Table, SARIF, Summary |
| AI enricher | ✅ OpenAI, Anthropic, Ollama |

**What works today:**
```bash
lucidscan scan --sca --sast --iac    # Security scanning
lucidscan scan --format sarif        # SARIF output for GitHub
lucidscan scan --ai                  # AI-powered explanations
```

---

## v0.2 — Foundation

**Theme**: Smart initialization and expanded architecture

### Key Deliverables

| Feature | Description |
|---------|-------------|
| **`lucidscan init`** | Interactive project setup that detects your stack and generates config |
| **Codebase detection** | Auto-detect languages, frameworks, existing tools, CI systems |
| **CI config generation** | Generate GitHub Actions, GitLab CI, Bitbucket Pipelines configs |
| **Plugin restructure** | Generalize scanner plugins to support all tool types |

### User Experience

```bash
$ lucidscan init

Analyzing project...

Detected:
  Languages:    Python 3.11
  Frameworks:   FastAPI
  Tools:        pytest, ruff (pyproject.toml)
  CI:           GitHub Actions

? Linter         [Ruff] ✓
? Type checker   [mypy]
? Security       [Trivy + OpenGrep]
? CI platform    [GitHub Actions] ✓

Generated:
  ✓ lucidscan.yml
  ✓ .github/workflows/lucidscan.yml
```

### Success Criteria

- [ ] `lucidscan init` works for Python and JavaScript projects
- [ ] CI config generation for GitHub, GitLab, Bitbucket
- [ ] Existing security scanning continues to work

---

## v0.3 — Code Quality

**Theme**: Linting and type checking

### Key Deliverables

| Feature | Description |
|---------|-------------|
| **Linting plugins** | Ruff (Python), ESLint (JS/TS), Biome (JS/TS) |
| **Type checking plugins** | mypy (Python), TypeScript, Pyright |
| **Auto-fix mode** | `lucidscan scan --fix` applies automatic fixes |
| **Unified output** | Lint and type errors in same format as security issues |

### User Experience

```bash
$ lucidscan scan

Linting ━━━━━━━━━━━━━━━━━━━━ 100%
Type Checking ━━━━━━━━━━━━━━ 100%
Security ━━━━━━━━━━━━━━━━━━━ 100%

┌─────────────────────────────────────────────────────────┐
│ Summary                                                 │
├─────────────────────────────────────────────────────────┤
│ Linting:       3 errors, 12 warnings (8 fixable)        │
│ Type Checking: 1 error                                  │
│ Security:      0 critical, 2 high, 5 medium             │
└─────────────────────────────────────────────────────────┘

$ lucidscan scan --fix

Fixed 8 linting issues in 4 files.
```

### Success Criteria

- [ ] Ruff and ESLint plugins working
- [ ] mypy and TypeScript plugins working
- [ ] `--fix` mode applies auto-fixes
- [ ] Unified issue format across all tools

---

## v0.4 — Full Pipeline

**Theme**: Testing and coverage

### Key Deliverables

| Feature | Description |
|---------|-------------|
| **Testing plugins** | pytest (Python), Jest (JS/TS), Go test |
| **Coverage plugins** | coverage.py (Python), Istanbul (JS/TS) |
| **Coverage thresholds** | Fail CI if coverage drops below threshold |
| **Complete pipeline** | All five domains in one command |

### User Experience

```bash
$ lucidscan scan

Linting ━━━━━━━━━━━━━━━━━━━━ 100%
Type Checking ━━━━━━━━━━━━━━ 100%
Security ━━━━━━━━━━━━━━━━━━━ 100%
Testing ━━━━━━━━━━━━━━━━━━━━ 100%
Coverage ━━━━━━━━━━━━━━━━━━━ 100%

┌─────────────────────────────────────────────────────────┐
│ Summary                                                 │
├─────────────────────────────────────────────────────────┤
│ Linting:       ✓ passed                                 │
│ Type Checking: ✓ passed                                 │
│ Security:      2 high (blocking)                        │
│ Testing:       42 passed, 0 failed                      │
│ Coverage:      87% (threshold: 80%) ✓                   │
└─────────────────────────────────────────────────────────┘
```

### Success Criteria

- [ ] pytest and Jest plugins working
- [ ] Coverage threshold enforcement
- [ ] Complete pipeline execution
- [ ] Python and JavaScript projects fully supported

---

## v0.5 — AI Integration

**Theme**: MCP server and AI feedback loop

### Key Deliverables

| Feature | Description |
|---------|-------------|
| **MCP server** | `lucidscan serve --mcp` for Claude Code and Cursor |
| **File watcher** | `lucidscan serve --watch` for real-time checking |
| **AI instruction format** | Structured fix instructions for AI agents |
| **Feedback loop** | AI writes → LucidScan checks → AI fixes |

### User Experience

**Claude Code / Cursor integration:**

```json
{
  "mcpServers": {
    "lucidscan": {
      "command": "lucidscan",
      "args": ["serve", "--mcp"]
    }
  }
}
```

**AI receives structured instructions:**

```json
{
  "instructions": [
    {
      "priority": 1,
      "action": "FIX_SECURITY_VULNERABILITY",
      "file": "src/auth.py",
      "line": 23,
      "problem": "Hardcoded password detected",
      "fix_steps": [
        "Import os module",
        "Replace with os.environ.get('DB_PASSWORD')"
      ]
    }
  ]
}
```

### Success Criteria

- [ ] MCP server works with Claude Code
- [ ] MCP server works with Cursor
- [ ] File watcher mode functional
- [ ] AI agents can receive and act on fix instructions

---

## v1.0 — Production Ready

**Theme**: Polish and stability

### Key Deliverables

| Feature | Description |
|---------|-------------|
| **Documentation** | Comprehensive user and developer guides |
| **Performance** | Incremental checking, caching, parallel execution |
| **Error handling** | Graceful degradation, clear error messages |
| **Distribution** | Updated PyPI package, Docker image, Homebrew |

### Success Criteria

- [ ] Complete documentation
- [ ] Performance optimized for large codebases
- [ ] Stable API (no breaking changes in 1.x)
- [ ] Production use by early adopters

---

## Future Considerations

Beyond v1.0, potential directions include:

| Direction | Description |
|-----------|-------------|
| **More languages** | Go, Rust, Java, C# support |
| **VS Code extension** | Native IDE integration |
| **Team features** | Shared configurations, policy enforcement |
| **Custom rules** | User-defined linting and security rules |
| **Dashboard** | Optional web UI for visibility |

These are not committed — they depend on user feedback and adoption.

---

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-01 | v0.1.x | Security scanning foundation complete |
| — | v0.2 | Foundation (planned) |
| — | v0.3 | Code Quality (planned) |
| — | v0.4 | Full Pipeline (planned) |
| — | v0.5 | AI Integration (planned) |
| — | v1.0 | Production Ready (planned) |

---

## Contributing

See the [full specification](main.md) for detailed technical requirements.

To contribute:
1. Pick an item from the current milestone
2. Open an issue to discuss approach
3. Submit a PR

We welcome contributions for:
- New tool plugins
- Documentation improvements
- Bug fixes and testing
