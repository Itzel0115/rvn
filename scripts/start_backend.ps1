$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$script = Join-Path $repo "demo_web.py"
$venvPython = Join-Path $repo ".venv\Scripts\python.exe"

Set-Location $repo

$uv = Get-Command uv -ErrorAction SilentlyContinue
if ($uv) {
    & $uv.Path run python $script
    exit $LASTEXITCODE
}

if (Test-Path $venvPython) {
    & $venvPython $script
    exit $LASTEXITCODE
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    throw "Python was not found. Install Python 3.12 or create .venv before starting the backend."
}

& $python.Path $script
exit $LASTEXITCODE
