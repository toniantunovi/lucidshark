# Build script for lucidscan tool bundles (Windows)
# Creates a self-contained bundle with Trivy, Semgrep, and Checkov

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Read version from pyproject.toml
function Read-Version {
    param([string]$Key)
    python -c "import tomllib; print(tomllib.load(open('$ProjectRoot/pyproject.toml','rb'))['tool']['lucidscan']['scanners']['$Key'])"
}

function Read-LucidscanVersion {
    python -c "import tomllib; print(tomllib.load(open('$ProjectRoot/pyproject.toml','rb'))['project']['version'])"
}

# Main build function
function Main {
    $Platform = "windows-amd64"
    $Os = "windows"
    $Arch = "amd64"

    Write-Host "Building bundle for platform: $Platform"
    Write-Host "OS: $Os, Arch: $Arch"

    # Read versions from pyproject.toml
    $TrivyVersion = Read-Version "trivy"
    $SemgrepVersion = Read-Version "semgrep"
    $CheckovVersion = Read-Version "checkov"
    $LucidscanVersion = Read-LucidscanVersion

    Write-Host "Scanner versions:"
    Write-Host "  Trivy:    $TrivyVersion"
    Write-Host "  Semgrep:  $SemgrepVersion"
    Write-Host "  Checkov:  $CheckovVersion"
    Write-Host "  Lucidscan: $LucidscanVersion"

    # Create bundle directory structure
    $BundleDir = Join-Path $ProjectRoot "dist\bundle"
    if (Test-Path $BundleDir) {
        Remove-Item -Recurse -Force $BundleDir
    }
    New-Item -ItemType Directory -Path "$BundleDir\bin" -Force | Out-Null
    New-Item -ItemType Directory -Path "$BundleDir\config" -Force | Out-Null

    # Step 1: Create Python virtual environment
    Write-Host "Creating Python virtual environment..."
    python -m venv "$BundleDir\venv"

    # Step 2: Install Semgrep
    Write-Host "Installing Semgrep $SemgrepVersion..."
    & "$BundleDir\venv\Scripts\pip.exe" install --quiet --upgrade pip
    & "$BundleDir\venv\Scripts\pip.exe" install --quiet "semgrep==$SemgrepVersion"

    # Step 3: Install Checkov
    Write-Host "Installing Checkov $CheckovVersion..."
    & "$BundleDir\venv\Scripts\pip.exe" install --quiet "checkov==$CheckovVersion"

    # Step 4: Download Trivy binary
    Write-Host "Downloading Trivy $TrivyVersion..."
    $TrivyUrl = "https://get.trivy.dev/trivy?type=zip&version=$TrivyVersion&os=$Os&arch=$Arch"
    $TrivyZip = Join-Path $BundleDir "trivy.zip"
    Invoke-WebRequest -Uri $TrivyUrl -OutFile $TrivyZip
    Expand-Archive -Path $TrivyZip -DestinationPath "$BundleDir\bin" -Force
    Remove-Item $TrivyZip

    # Step 5: Generate versions.json
    Write-Host "Generating versions.json..."
    $BundleDate = (Get-Date -Format "yyyy.MM.dd")
    $VersionsJson = @{
        lucidscan = $LucidscanVersion
        trivy = $TrivyVersion
        semgrep = $SemgrepVersion
        checkov = $CheckovVersion
        python = "3.11"
        platform = $Platform
        bundleVersion = $BundleDate
    } | ConvertTo-Json -Depth 10
    Set-Content -Path "$BundleDir\config\versions.json" -Value $VersionsJson

    # Step 6: Verify installation
    Write-Host "Verifying installation..."
    & "$BundleDir\bin\trivy.exe" --version
    & "$BundleDir\venv\Scripts\semgrep.exe" --version
    & "$BundleDir\venv\Scripts\checkov.exe" --version

    # Step 7: Create archive
    $ArchiveName = "lucidscan-bundle-$Platform.zip"
    $ArchivePath = Join-Path $ProjectRoot "dist\$ArchiveName"
    Write-Host "Creating archive: $ArchiveName"
    Compress-Archive -Path "$BundleDir\*" -DestinationPath $ArchivePath -Force

    # Generate checksum
    Write-Host "Generating checksum..."
    $Checksum = Get-FileHash -Path $ArchivePath -Algorithm SHA256
    "$($Checksum.Hash.ToLower())  $ArchiveName" | Out-File -Append -FilePath (Join-Path $ProjectRoot "dist\SHA256SUMS") -Encoding utf8

    Write-Host ""
    Write-Host "Bundle created successfully: dist\$ArchiveName"
    $Size = (Get-Item $ArchivePath).Length / 1MB
    Write-Host "Bundle size: $([math]::Round($Size, 2)) MB"
}

Main
