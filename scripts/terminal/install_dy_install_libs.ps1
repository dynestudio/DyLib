# dy Library Manager - Shelf Installer
# Usage: irm https://raw.githubusercontent.com/cdordelly/dyLib/dev/install.ps1 | iex

$ShelfUrl    = "https://raw.githubusercontent.com/cdordelly/dyLib/dev/toolbar/dy_install_libs.shelf"
$ShelfName   = "dy_install_libs.shelf"
$ErrorCount  = 0
$Installed   = @()
$Skipped     = @()

Write-Host ""
Write-Host "  dy Library Manager - Shelf Installer" -ForegroundColor Cyan
Write-Host "  ======================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------
# Download shelf file content
# -----------------------------------------------------------------------

Write-Host "  Downloading $ShelfName..." -ForegroundColor Gray
try {
    $ShelfContent = Invoke-RestMethod -Uri $ShelfUrl -UseBasicParsing
} catch {
    Write-Host "  ERROR: Failed to download shelf file." -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    Write-Host ""
    exit 1
}
Write-Host "  Download OK." -ForegroundColor Green
Write-Host ""

# -----------------------------------------------------------------------
# Find Houdini directories in Documents
# -----------------------------------------------------------------------

$DocsPath = [Environment]::GetFolderPath("MyDocuments")
$HoudiniDirs = Get-ChildItem -Path $DocsPath -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -match "^houdini\d+\.\d+$" }

if (-not $HoudiniDirs) {
    Write-Host "  No Houdini directories found in:" -ForegroundColor Yellow
    Write-Host "  $DocsPath" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Expected folders like: houdini20.5, houdini21.0" -ForegroundColor Gray
    Write-Host ""
    exit 0
}

Write-Host "  Found Houdini directories:" -ForegroundColor Gray
foreach ($Dir in $HoudiniDirs) {
    Write-Host "    $($Dir.Name)" -ForegroundColor Gray
}
Write-Host ""

# -----------------------------------------------------------------------
# Deploy to each Houdini directory
# -----------------------------------------------------------------------

foreach ($Dir in $HoudiniDirs) {
    $ToolbarDir  = Join-Path $Dir.FullName "toolbar"
    $DestFile    = Join-Path $ToolbarDir $ShelfName

    # Create toolbar folder if it doesn't exist
    if (-not (Test-Path $ToolbarDir)) {
        New-Item -ItemType Directory -Path $ToolbarDir -Force | Out-Null
    }

    # Write shelf file
    try {
        Set-Content -Path $DestFile -Value $ShelfContent -Encoding UTF8 -NoNewline
        $Installed += $Dir.Name
        Write-Host "  [OK] $($Dir.Name)\toolbar\$ShelfName" -ForegroundColor Green
    } catch {
        $ErrorCount++
        $Skipped += $Dir.Name
        Write-Host "  [FAIL] $($Dir.Name): $_" -ForegroundColor Red
    }
}

# -----------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------

Write-Host ""
Write-Host "  ======================================" -ForegroundColor Cyan
if ($Installed.Count -gt 0) {
    Write-Host "  Installed to $($Installed.Count) Houdini version(s): $($Installed -join ', ')" -ForegroundColor Green
}
if ($Skipped.Count -gt 0) {
    Write-Host "  Failed for $($Skipped.Count) version(s): $($Skipped -join ', ')" -ForegroundColor Red
}
Write-Host ""
Write-Host "  Restart Houdini and look for the 'Dy Install Libs' shelf tab." -ForegroundColor Cyan
Write-Host ""
