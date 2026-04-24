$ErrorActionPreference = "Stop"

param(
    [string]$Python = "python"
)

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvDir = Join-Path $projectRoot ".venv-build"
$appName = "Abipha-DMS-Reporter"
$zipName = "Abipha-DMS-Reporter-windows-x64.zip"
$iconPath = Join-Path $projectRoot "assets\\abipha-dms-reporter.ico"
$packageDir = Join-Path $projectRoot "dist\\windows-package"
$exeName = "$appName.exe"

Set-Location $projectRoot

if (-not (Test-Path $venvDir)) {
    & $Python -m venv $venvDir
}

$pythonExe = Join-Path $venvDir "Scripts\\python.exe"

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install pyinstaller
& $pythonExe -m pip install .

if (-not (Test-Path $iconPath)) {
    & $pythonExe (Join-Path $projectRoot "scripts\\generate_app_icon.py")
}

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}

& $pythonExe -m PyInstaller `
    --noconfirm `
    --clean `
    --onefile `
    --distpath $packageDir `
    --workpath (Join-Path $projectRoot "build\\pyinstaller") `
    --specpath (Join-Path $projectRoot "build\\spec") `
    --icon $iconPath `
    --name $appName `
    main.py

Copy-Item `
    -Path (Join-Path $projectRoot "modules") `
    -Destination (Join-Path $packageDir "modules") `
    -Recurse `
    -Force

$zipPath = Join-Path $projectRoot "dist\\$zipName"
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}
Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath

Write-Host "Windows package ready:"
Write-Host "  EXE: $packageDir\\$exeName"
Write-Host "  ZIP: $zipPath"
