#!/bin/bash
set -euo pipefail

# Build script for lucidscan tool bundles
# Creates a self-contained bundle with Trivy, Semgrep, and Checkov

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Detect platform
detect_platform() {
    local os arch

    case "$(uname -s)" in
        Linux*)  os="linux" ;;
        Darwin*) os="macos" ;;
        *)       echo "Unsupported OS: $(uname -s)" >&2; exit 1 ;;
    esac

    case "$(uname -m)" in
        x86_64)  arch="amd64" ;;
        aarch64) arch="arm64" ;;
        arm64)   arch="arm64" ;;
        *)       echo "Unsupported architecture: $(uname -m)" >&2; exit 1 ;;
    esac

    echo "${os}-${arch}"
}

# Read version from pyproject.toml
read_version() {
    local key="$1"
    python3 -c "import tomllib; print(tomllib.load(open('${PROJECT_ROOT}/pyproject.toml','rb'))['tool']['lucidscan']['scanners']['${key}'])"
}

read_lucidscan_version() {
    python3 -c "import tomllib; print(tomllib.load(open('${PROJECT_ROOT}/pyproject.toml','rb'))['project']['version'])"
}

# Main build function
main() {
    local platform="${1:-$(detect_platform)}"
    local os="${platform%-*}"
    local arch="${platform#*-}"

    echo "Building bundle for platform: ${platform}"
    echo "OS: ${os}, Arch: ${arch}"

    # Read versions from pyproject.toml
    TRIVY_VERSION=$(read_version "trivy")
    SEMGREP_VERSION=$(read_version "semgrep")
    CHECKOV_VERSION=$(read_version "checkov")
    LUCIDSCAN_VERSION=$(read_lucidscan_version)

    echo "Scanner versions:"
    echo "  Trivy:    ${TRIVY_VERSION}"
    echo "  Semgrep:  ${SEMGREP_VERSION}"
    echo "  Checkov:  ${CHECKOV_VERSION}"
    echo "  Lucidscan: ${LUCIDSCAN_VERSION}"

    # Create bundle directory structure
    BUNDLE_DIR="${PROJECT_ROOT}/dist/bundle"
    rm -rf "${BUNDLE_DIR}"
    mkdir -p "${BUNDLE_DIR}/bin"
    mkdir -p "${BUNDLE_DIR}/config"

    # Step 1: Create Python virtual environment
    echo "Creating Python virtual environment..."
    python3 -m venv "${BUNDLE_DIR}/venv"

    # Step 2: Install Semgrep
    echo "Installing Semgrep ${SEMGREP_VERSION}..."
    "${BUNDLE_DIR}/venv/bin/pip" install --quiet --upgrade pip
    "${BUNDLE_DIR}/venv/bin/pip" install --quiet "semgrep==${SEMGREP_VERSION}"

    # Step 3: Install Checkov
    echo "Installing Checkov ${CHECKOV_VERSION}..."
    "${BUNDLE_DIR}/venv/bin/pip" install --quiet "checkov==${CHECKOV_VERSION}"

    # Step 4: Download Trivy binary
    echo "Downloading Trivy ${TRIVY_VERSION}..."
    TRIVY_URL="https://get.trivy.dev/trivy?type=tar.gz&version=${TRIVY_VERSION}&os=${os}&arch=${arch}"
    curl -sfL "${TRIVY_URL}" | tar xzf - -C "${BUNDLE_DIR}/bin"
    chmod +x "${BUNDLE_DIR}/bin/trivy"

    # Step 5: Generate versions.json
    echo "Generating versions.json..."
    BUNDLE_DATE=$(date -u +"%Y.%m.%d")
    cat > "${BUNDLE_DIR}/config/versions.json" <<EOF
{
  "lucidscan": "${LUCIDSCAN_VERSION}",
  "trivy": "${TRIVY_VERSION}",
  "semgrep": "${SEMGREP_VERSION}",
  "checkov": "${CHECKOV_VERSION}",
  "python": "3.11",
  "platform": "${platform}",
  "bundleVersion": "${BUNDLE_DATE}"
}
EOF

    # Step 6: Verify installation
    echo "Verifying installation..."
    "${BUNDLE_DIR}/bin/trivy" --version
    "${BUNDLE_DIR}/venv/bin/semgrep" --version
    "${BUNDLE_DIR}/venv/bin/checkov" --version

    # Step 7: Create archive
    ARCHIVE_NAME="lucidscan-bundle-${platform}.tar.gz"
    echo "Creating archive: ${ARCHIVE_NAME}"
    tar -czvf "${PROJECT_ROOT}/dist/${ARCHIVE_NAME}" -C "${BUNDLE_DIR}" .

    # Generate checksum
    echo "Generating checksum..."
    cd "${PROJECT_ROOT}/dist"
    sha256sum "${ARCHIVE_NAME}" >> SHA256SUMS

    echo ""
    echo "Bundle created successfully: dist/${ARCHIVE_NAME}"
    echo "Bundle size: $(du -h "${PROJECT_ROOT}/dist/${ARCHIVE_NAME}" | cut -f1)"
}

main "$@"
