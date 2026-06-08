$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$frontend = Join-Path $repo "frontend"
$nodeModules = Join-Path $frontend "node_modules"

$env:PYTHON_API_BASE = "http://127.0.0.1:8765"
Set-Location $frontend

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "npm was not found. Install Node.js LTS before starting the mobile route."
}

if (-not (Test-Path $nodeModules)) {
    & $npm.Path install
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Write-Host "Starting unified frontend. Open http://127.0.0.1:3000/mobile for the mobile experience."
& $npm.Path run dev -- --hostname 127.0.0.1
exit $LASTEXITCODE
