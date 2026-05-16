$ErrorActionPreference = "Stop"

param(
    [string]$Python = "python",
    [switch]$SkipTests
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $projectRoot ".venv-build"
$distDir = Join-Path $projectRoot "dist"
$packageDir = Join-Path $distDir "windows-package"
$workDir = Join-Path $projectRoot "build\pyinstaller-windows"
$specDir = Join-Path $projectRoot "build\spec-windows"
$zipPath = Join-Path $distDir "dms-reporting-windows-x64.zip"
$appName = "DMS Reporting"
$exePath = Join-Path $packageDir "$appName.exe"

Set-Location $projectRoot

if (-not (Test-Path $venvDir)) {
    & $Python -m venv $venvDir
}

$pythonExe = Join-Path $venvDir "Scripts\python.exe"

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install ".[dev]" pyinstaller

if (-not $SkipTests) {
    & $pythonExe -m pytest -q
}

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
if (Test-Path $workDir) {
    Remove-Item $workDir -Recurse -Force
}
if (Test-Path $specDir) {
    Remove-Item $specDir -Recurse -Force
}

& $pythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --windowed `
    --distpath $packageDir `
    --workpath $workDir `
    --specpath $specDir `
    --name $appName `
    main_windows.py

Copy-Item `
    -Path (Join-Path $projectRoot "modules") `
    -Destination (Join-Path $packageDir "modules") `
    -Recurse `
    -Force

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath

Write-Host "Windows app package ready:"
Write-Host "  EXE: $exePath"
Write-Host "  ZIP: $zipPath"
