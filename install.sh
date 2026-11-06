#!/usr/bin/env bash
#
# LucidShark Installer for Linux and macOS
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash
#
# Or with options:
#   curl -fsSL https://raw.githubusercontent.com/toniantunovi/lucidshark/main/install.sh | bash -s -- --version v0.8.5

set -euo pipefail

# Configuration
REPO="toniantunovi/lucidshark"
BINARY_NAME="lucidshark"
SUMS_NAME="SHA256SUMS"
TMP_FILE=""
TMP_SUMS=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${BLUE}$1${NC}"; }
success() { echo -e "${GREEN}$1${NC}"; }
warn() { echo -e "${YELLOW}$1${NC}"; }
error() { echo -e "${RED}Error: $1${NC}" >&2; exit 1; }

# Detect operating system
detect_os() {
    local os
    os="$(uname -s | tr '[:upper:]' '[:lower:]')"
    case "$os" in
        darwin) echo "darwin" ;;
        linux) echo "linux" ;;
        *) error "Unsupported operating system: $os. Only Linux and macOS are supported." ;;
    esac
}

# Detect architecture
detect_arch() {
    local arch
    arch="$(uname -m)"
    case "$arch" in
        x86_64|amd64) echo "amd64" ;;
        arm64|aarch64) echo "arm64" ;;
        *) error "Unsupported architecture: $arch" ;;
    esac
}

# Get latest release version from GitHub
get_latest_version() {
    local url="https://api.github.com/repos/${REPO}/releases/latest"
    if command -v curl &> /dev/null; then
        curl -fsSL "$url" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/'
    elif command -v wget &> /dev/null; then
        wget -qO- "$url" | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/'
    else
        error "Neither curl nor wget found. Please install one of them."
    fi
}

# Download file
download() {
    local url="$1"
    local output="$2"

    if command -v curl &> /dev/null; then
        curl -fsSL "$url" -o "$output"
    elif command -v wget &> /dev/null; then
        wget -q "$url" -O "$output"
    else
        error "Neither curl nor wget found. Please install one of them."
    fi
}

# Print the SHA-256 of a file using whichever tool the system has
sha256_of() {
    local file="$1"
    if command -v sha256sum &> /dev/null; then
        sha256sum "$file" | awk '{print $1}'
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$file" | awk '{print $1}'
    elif command -v openssl &> /dev/null; then
        openssl dgst -sha256 -r "$file" | awk '{print $1}'
    else
        error "No SHA-256 tool found (need sha256sum, shasum or openssl)."
    fi
}

# Verify a downloaded binary against the release's SHA256SUMS file
verify_checksum() {
    local file="$1"
    local sums_file="$2"
    local asset="$3"
    local expected actual

    expected="$(awk -v name="$asset" '{n=$2; sub(/^\*/, "", n)} n == name {print tolower($1); exit}' "$sums_file")"
    if [[ ! "$expected" =~ ^[0-9a-f]{64}$ ]]; then
        error "${SUMS_NAME} has no entry for ${asset}. Refusing to install an unverified binary."
    fi

    actual="$(sha256_of "$file")"
    if [[ "$actual" != "$expected" ]]; then
        error "Checksum mismatch for ${asset}: expected ${expected}, got ${actual}. The download was discarded."
    fi
    success "Checksum verified (SHA-256 ${actual})"
}

# Main installation function
main() {
    local version=""
    local skip_checksum=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --version|-v)
                version="$2"
                shift 2
                ;;
            --insecure-skip-checksum)
                skip_checksum=true
                shift
                ;;
            --help|-h)
                echo "LucidShark Installer"
                echo ""
                echo "Usage: install.sh [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --version, -v              Install specific version (e.g., v0.8.5)"
                echo "  --insecure-skip-checksum   Skip SHA-256 verification (only for releases"
                echo "                             published before SHA256SUMS existed)"
                echo "  --help, -h                 Show this help message"
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done

    echo ""
    echo "=========================================="
    info "       LucidShark Installer"
    echo "=========================================="
    echo ""

    # Detect platform
    local os arch platform
    os="$(detect_os)"
    arch="$(detect_arch)"
    platform="${os}-${arch}"

    info "Detected platform: ${platform}"
    echo ""

    # Get version
    if [[ -z "$version" ]]; then
        info "Fetching latest version..."
        version="$(get_latest_version)"
        if [[ -z "$version" ]]; then
            error "Could not determine latest version. Please specify with --version"
        fi
    fi
    info "Version: ${version}"
    echo ""

    # Install to current project root
    local install_dir="."

    # Create install directory
    mkdir -p "$install_dir"

    # Construct download URL
    local binary_name="${BINARY_NAME}-${platform}"
    local download_url="https://github.com/${REPO}/releases/download/${version}/${binary_name}"
    local install_path="${install_dir}/${BINARY_NAME}"

    info "Downloading ${binary_name}..."

    # Create temp files for download
    TMP_FILE="$(mktemp)"
    TMP_SUMS="$(mktemp)"
    trap 'rm -f "$TMP_FILE" "$TMP_SUMS"' EXIT

    if ! download "$download_url" "$TMP_FILE"; then
        error "Failed to download binary from: $download_url"
    fi

    # Verify integrity before the binary is ever made executable
    if [[ "$skip_checksum" == true ]]; then
        warn "WARNING: --insecure-skip-checksum given, installing WITHOUT integrity verification."
    else
        local sums_url="https://github.com/${REPO}/releases/download/${version}/${SUMS_NAME}"
        info "Verifying checksum..."
        if ! download "$sums_url" "$TMP_SUMS"; then
            error "Could not download ${SUMS_NAME} for ${version}. Releases before checksums were published need --insecure-skip-checksum."
        fi
        verify_checksum "$TMP_FILE" "$TMP_SUMS" "$binary_name"
    fi

    # Install binary
    info "Installing to ${install_path}..."
    mv "$TMP_FILE" "$install_path"
    chmod +x "$install_path"

    echo ""
    success "Installation complete!"
    echo ""

    # Verify installation
    if "$install_path" --version &> /dev/null; then
        local installed_version
        installed_version="$("$install_path" --version 2>/dev/null || echo "unknown")"
        success "Verified: ${installed_version}"
    else
        warn "Binary installed but could not verify version"
    fi

    echo ""
    echo "=========================================="
    success "Installation Complete!"
    echo "=========================================="
    echo ""
    info "Binary installed to: ./lucidshark"
    info "Each project gets its own binary (like Python venv)"
    echo ""
    warn "IMPORTANT: Use ./lucidshark (not lucidshark)"
    echo ""
    echo "Example commands:"
    echo ""
    success "  ./lucidshark init              # Configure Claude Code"
    success "  ./lucidshark scan --format ai  # Run quality checks"
    success "  ./lucidshark scan --fix        # Auto-fix issues"
    success "  ./lucidshark scan --all        # Full project scan"
    echo ""
    info "The './' prefix runs the binary from the current directory."
    info "This ensures you're using the project-specific version."
    echo ""
}

main "$@"
