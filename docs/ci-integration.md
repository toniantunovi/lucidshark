# CI Integration Guide

LucidScan integrates seamlessly with all major CI/CD platforms. This guide covers setup, common patterns, and best practices.

## Quick Start

### GitHub Actions

```yaml
- uses: voldeq/lucidscan/.github/actions/scan@main
  with:
    scan-types: all
    fail-on: high
```

### GitLab CI

```yaml
lucidscan:
  image: ghcr.io/voldeq/lucidscan:latest
  script:
    - lucidscan --all --fail-on high
```

### Bitbucket Pipelines

```yaml
- step:
    name: Security Scan
    image: ghcr.io/voldeq/lucidscan:latest
    script:
      - lucidscan --all --fail-on high
```

---

## GitHub Actions

### Using the Composite Action

The recommended way to use LucidScan in GitHub Actions:

```yaml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: voldeq/lucidscan/.github/actions/scan@main
        with:
          scan-types: all
          fail-on: high
```

### Action Inputs

| Input | Description | Default |
|-------|-------------|---------|
| `scan-types` | Comma-separated: `sca`, `sast`, `iac`, `container`, or `all` | `all` |
| `fail-on` | Fail threshold: `critical`, `high`, `medium`, `low` | (none) |
| `format` | Output format: `table`, `json`, `summary`, `sarif` | `table` |
| `image` | Container image to scan | (none) |
| `config` | Path to `.lucidscan.yml` | (none) |
| `working-directory` | Directory to scan | `.` |
| `version` | LucidScan version | `latest` |
| `sarif-file` | Path for SARIF output (enables Code Scanning) | (none) |

### Action Outputs

| Output | Description |
|--------|-------------|
| `exit-code` | LucidScan exit code |
| `issues-found` | `true` if issues were found |

### GitHub Code Scanning Integration

Generate SARIF output to integrate with GitHub's Code Scanning:

```yaml
- uses: voldeq/lucidscan/.github/actions/scan@main
  with:
    scan-types: all
    sarif-file: lucidscan-results.sarif
```

The action automatically uploads SARIF results to GitHub Code Scanning.

### Using Docker Image Directly

For more control, use the Docker image directly:

```yaml
jobs:
  security:
    runs-on: ubuntu-latest
    container:
      image: ghcr.io/voldeq/lucidscan:latest
    steps:
      - uses: actions/checkout@v4
      - run: lucidscan --all --fail-on high
```

---

## GitLab CI

### Basic Setup

Add to your `.gitlab-ci.yml`:

```yaml
lucidscan:
  image: ghcr.io/voldeq/lucidscan:latest
  stage: test
  script:
    - lucidscan --all
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Using the Template

Include the LucidScan template for pre-configured jobs:

```yaml
include:
  - remote: 'https://raw.githubusercontent.com/voldeq/lucidscan/main/ci-templates/gitlab-ci.yml'

variables:
  LUCIDSCAN_FAIL_ON: "high"
```

### Parallel Scanning

Run scan types in parallel for faster feedback:

```yaml
stages:
  - test

lucidscan-sca:
  image: ghcr.io/voldeq/lucidscan:latest
  stage: test
  script:
    - lucidscan --sca

lucidscan-sast:
  image: ghcr.io/voldeq/lucidscan:latest
  stage: test
  script:
    - lucidscan --sast

lucidscan-iac:
  image: ghcr.io/voldeq/lucidscan:latest
  stage: test
  script:
    - lucidscan --iac
```

### Container Scanning

Scan images built in your pipeline:

```yaml
build:
  stage: build
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

scan-container:
  image: ghcr.io/voldeq/lucidscan:latest
  stage: test
  script:
    - lucidscan --container --image $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  needs:
    - build
```

---

## Bitbucket Pipelines

### Basic Setup

Add to your `bitbucket-pipelines.yml`:

```yaml
image: ghcr.io/voldeq/lucidscan:latest

pipelines:
  default:
    - step:
        name: Security Scan
        script:
          - lucidscan --all

  pull-requests:
    '**':
      - step:
          name: Security Scan
          script:
            - lucidscan --all --fail-on high
```

### Parallel Scanning

```yaml
pipelines:
  default:
    - parallel:
        - step:
            name: SCA Scan
            script:
              - lucidscan --sca
        - step:
            name: SAST Scan
            script:
              - lucidscan --sast
        - step:
            name: IaC Scan
            script:
              - lucidscan --iac
```

---

## Exit Codes

LucidScan uses exit codes to communicate results:

| Code | Meaning | CI Behavior |
|------|---------|-------------|
| `0` | Scan completed, no issues (or below threshold) | Pass |
| `1` | Issues found at or above threshold | Fail |
| `2` | Scanner error | Fail |
| `3` | Invalid usage | Fail |
| `4` | Bootstrap failure | Fail |

---

## The `--fail-on` Flag

The `--fail-on` flag controls when LucidScan returns exit code 1:

```bash
# Fail only on critical issues
lucidscan --all --fail-on critical

# Fail on high or critical issues
lucidscan --all --fail-on high

# Fail on medium, high, or critical issues
lucidscan --all --fail-on medium

# Fail on any issue
lucidscan --all --fail-on low
```

### Recommended Policies

| Environment | Recommended `--fail-on` |
|-------------|-------------------------|
| Pull Requests | `high` - Block critical/high issues |
| Main Branch | `high` - Enforce quality gate |
| Release Tags | `medium` - Stricter for releases |
| Development | (none) - Informational only |

### Example: Tiered Policy

```yaml
# GitHub Actions example
jobs:
  pr-scan:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: voldeq/lucidscan/.github/actions/scan@main
        with:
          fail-on: high

  release-scan:
    if: startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: voldeq/lucidscan/.github/actions/scan@main
        with:
          fail-on: medium
```

---

## Configuration File

Use `.lucidscan.yml` for consistent configuration across environments:

```yaml
# .lucidscan.yml
scanners:
  sca: true
  sast: true
  iac: true
  container: false

fail_on: high

ignore:
  - "vendor/"
  - "node_modules/"
  - "**/*.test.js"
```

Then in CI, just run:

```bash
lucidscan
```

---

## Docker Image Tags

Available tags for `ghcr.io/voldeq/lucidscan`:

| Tag | Description |
|-----|-------------|
| `latest` | Latest stable release |
| `X.Y.Z` | Specific version (e.g., `0.2.0`) |

The Docker image includes:
- Pre-downloaded scanner binaries (Trivy, OpenGrep, Checkov)
- Pre-warmed Trivy vulnerability database
- Ready for immediate scanning with no bootstrap time

---

## Caching (Optional)

For pip-based installation, cache the scanner binaries:

### GitHub Actions

```yaml
- uses: actions/cache@v4
  with:
    path: ~/.lucidscan
    key: lucidscan-${{ runner.os }}-${{ hashFiles('.lucidscan.yml') }}
```

### GitLab CI

```yaml
lucidscan:
  cache:
    key: lucidscan-$CI_RUNNER_EXECUTABLE_ARCH
    paths:
      - ~/.lucidscan/
```

> Note: When using the Docker image, caching is unnecessary as binaries are pre-installed.

---

## Troubleshooting

### Scanner Download Failures

If scanners fail to download in CI:

1. Check network connectivity
2. Verify GitHub/external URLs are not blocked
3. Use the Docker image (pre-downloaded binaries)

### Permission Errors

The Docker image runs as root by default. If you need non-root:

```yaml
container:
  image: ghcr.io/voldeq/lucidscan:latest
  options: --user 1000:1000
```

### Timeout Issues

For large repositories, increase timeout:

```yaml
# GitLab
lucidscan:
  timeout: 30 minutes
  script:
    - lucidscan --all

# GitHub Actions (per-step timeout)
- uses: voldeq/lucidscan/.github/actions/scan@main
  timeout-minutes: 30
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
lucidscan --all --debug
```
