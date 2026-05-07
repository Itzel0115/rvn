$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$mobile = Join-Path $repo "mobile-demo"
$nodeModules = Join-Path $mobile "node_modules"

$env:PYTHON_API_BASE = "http://127.0.0.1:8765"
Set-Location $mobile

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    throw "npm was not found. Install Node.js LTS before starting the mobile demo."
}

if (-not (Test-Path $nodeModules)) {
    & $npm.Path install
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

& $npm.Path run dev -- --hostname 127.0.0.1
exit $LASTEXITCODE
