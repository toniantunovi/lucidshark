# Ignore Patterns in LucidScan

LucidScan supports multiple ways to exclude files and findings from your quality pipeline.

## File-Level Ignores

### .lucidscanignore File

Create a `.lucidscanignore` file in your project root with gitignore-style patterns:

```gitignore
# Dependencies
node_modules/
.venv/
vendor/

# Build output
dist/
build/
*.pyc
__pycache__/

# Test fixtures (but not tests themselves)
**/__fixtures__/
**/testdata/

# Generated files
*.generated.ts
*.min.js

# But keep important config
!vendor/config.yml
```

**Supported syntax:**

| Pattern | Description | Example |
|---------|-------------|---------|
| `*` | Match any characters except `/` | `*.log` matches `debug.log` |
| `**` | Match any directory depth | `**/test_*.py` matches files at any depth |
| `/` (trailing) | Match directories only | `vendor/` matches the vendor directory |
| `!` | Negate a pattern (re-include) | `!important.log` keeps the file |
| `#` | Comment line | `# This is ignored` |

### Config File Ignores

Add patterns to `lucidscan.yml`:

```yaml
ignore:
  - "**/node_modules/**"
  - "**/.venv/**"
  - "**/dist/**"
  - "*.md"
```

**Note:** Patterns from both `.lucidscanignore` and `lucidscan.yml` are merged.

## How Ignore Patterns Work

LucidScan passes ignore patterns to each tool using their native exclude mechanisms:

| Domain | Tool | CLI Flag Used |
|--------|------|---------------|
| Linting | Ruff | `--exclude` |
| Linting | ESLint | `--ignore-pattern` |
| Type Checking | mypy | `--exclude` |
| Security | Trivy | `--skip-dirs`, `--skip-files` |
| Security | OpenGrep | `--exclude` |
| Security | Checkov | `--skip-path` |
| Testing | pytest | `--ignore` |

This ensures tools efficiently skip ignored paths during their internal file discovery.

## Inline Ignores (Per-Finding)

Inline ignores suppress specific findings at the code level. These are handled natively by each tool.

### Linting

#### Ruff (Python)

Suppress a specific rule:

```python
x = 1  # noqa: E501
```

Suppress all rules on a line:

```python
x = 1  # noqa
```

Suppress for entire file (at top):

```python
# ruff: noqa: E501
```

#### ESLint (JavaScript/TypeScript)

Suppress next line:

```javascript
// eslint-disable-next-line no-console
console.log("debug");
```

Suppress specific rule:

```javascript
console.log("debug"); // eslint-disable-line no-console
```

Suppress for block:

```javascript
/* eslint-disable no-console */
console.log("debug");
/* eslint-enable no-console */
```

### Type Checking

#### mypy (Python)

Suppress on line:

```python
x: int = "hello"  # type: ignore
```

Suppress specific error:

```python
x: int = "hello"  # type: ignore[assignment]
```

#### TypeScript

Suppress next line:

```typescript
// @ts-ignore
const x: number = "hello";
```

Suppress with reason (TS 3.9+):

```typescript
// @ts-expect-error: Legacy API returns string
const x: number = legacyApi();
```

### Security

#### OpenGrep / Semgrep (SAST)

Suppress a specific rule:

```python
password = "hardcoded"  # nosemgrep: hardcoded-password
```

Suppress all rules on a line:

```python
eval(user_input)  # nosemgrep
```

#### Checkov (IaC)

Suppress with reason:

```hcl
resource "aws_s3_bucket" "example" {
  # checkov:skip=CKV_AWS_18:Access logging not required for this bucket
  bucket = "my-bucket"
}
```

Suppress multiple checks:

```yaml
# checkov:skip=CKV_K8S_1,CKV_K8S_2:Known issues to be fixed later
apiVersion: v1
kind: Pod
```

#### Trivy (SCA)

Trivy does not support inline ignores. Use a `.trivyignore` file:

```
# .trivyignore - List CVEs to ignore
CVE-2021-1234
CVE-2021-5678
```

### Testing

#### pytest (Python)

Skip a test:

```python
import pytest

@pytest.mark.skip(reason="Not implemented yet")
def test_feature():
    pass
```

Skip conditionally:

```python
@pytest.mark.skipif(sys.version_info < (3, 10), reason="Requires Python 3.10+")
def test_new_feature():
    pass
```

Expected failure:

```python
@pytest.mark.xfail(reason="Known bug #123")
def test_buggy_feature():
    pass
```

#### Jest (JavaScript/TypeScript)

Skip a test:

```javascript
test.skip('not implemented', () => {
  // ...
});
```

Skip describe block:

```javascript
describe.skip('feature', () => {
  // ...
});
```

## Domain-Specific Configuration

### Disable Entire Domains

```yaml
pipeline:
  linting:
    enabled: false  # Skip linting entirely
  type_checking:
    enabled: true
  security:
    enabled: true
  testing:
    enabled: true
  coverage:
    enabled: false  # Skip coverage checks
```

### Tool-Specific Ignores

Some tools have their own ignore files that LucidScan respects:

| Tool | Ignore File |
|------|-------------|
| Ruff | `.ruff.toml` (exclude section), `pyproject.toml` |
| ESLint | `.eslintignore`, `eslint.config.js` |
| mypy | `pyproject.toml` (exclude section) |
| Trivy | `.trivyignore` |
| Checkov | `.checkov.yml` |
| pytest | `pytest.ini`, `pyproject.toml` |

LucidScan doesn't override these — they work alongside `.lucidscanignore`.

## Best Practices

### Do Ignore

- **Dependencies**: `node_modules/`, `.venv/`, `vendor/`
- **Build output**: `dist/`, `build/`, `*.pyc`
- **Generated code**: `*.generated.ts`, `*.pb.go`
- **Test fixtures**: `**/__fixtures__/`, `**/testdata/`
- **IDE/editor files**: `.idea/`, `.vscode/` (usually in `.gitignore` already)

### Don't Ignore

- **Your application code** — fix issues instead of ignoring
- **Configuration files** — security issues here are real
- **Test files** — keep `tests/` scanned for security issues
- **CI/CD files** — `.github/`, `.gitlab-ci.yml` should be checked

### Inline Ignore Guidelines

1. **Always document the reason** when using inline ignores
2. **Prefer specific rule IDs** over blanket ignores
3. **Review inline ignores periodically** — they may no longer be needed
4. **Use inline ignores sparingly** — they're exceptions, not the norm

## Examples

### Python Project

`.lucidscanignore`:

```gitignore
# Virtual environments
.venv/
venv/
env/

# Build artifacts
dist/
build/
*.egg-info/
*.pyc
__pycache__/

# Test fixtures
tests/fixtures/
**/conftest.py  # if you don't want conftest scanned

# Generated
*.pyi  # if generated
```

### JavaScript/TypeScript Project

`.lucidscanignore`:

```gitignore
# Dependencies
node_modules/

# Build output
dist/
build/
.next/
out/

# Generated
*.d.ts  # if generated
coverage/

# Test fixtures
**/__mocks__/
**/__fixtures__/
```

### Infrastructure Project

`.lucidscanignore`:

```gitignore
# Example configurations
examples/
samples/

# Local development overrides
*.local.tf
*.tfvars  # if contains secrets (should be in .gitignore)

# Test fixtures
**/testdata/

# Generated
.terraform/
*.tfstate*
```

### Monorepo

`.lucidscanignore`:

```gitignore
# Shared dependencies
node_modules/
**/node_modules/

# Build outputs
**/dist/
**/build/

# Per-package ignores can also be in each package's directory
```

## Troubleshooting

### Pattern Not Working

1. Check the pattern syntax — use `**` for recursive matching
2. Verify the path is relative to project root
3. Run with `--debug` to see which files are being scanned
4. Check if the tool has its own ignore file overriding

### Too Many Files Ignored

1. Check for overly broad patterns like `*` or `**/*`
2. Use `!` negation to re-include important files
3. Be specific: `tests/fixtures/` instead of `tests/`

### Inline Ignore Not Working

1. Verify the exact comment syntax for the tool
2. Check if the rule ID is correct
3. Some tools require the ignore on the same line, others on the line before
