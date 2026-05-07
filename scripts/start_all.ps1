$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "start_backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "start_frontend.ps1"
$mobileScript = Join-Path $PSScriptRoot "start_mobile.ps1"

function Start-DetachedProcess {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ScriptPath
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = "powershell.exe"
    $psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    $psi.UseShellExecute = $true
    $psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Minimized
    [System.Diagnostics.Process]::Start($psi) | Out-Null
}

Start-DetachedProcess -ScriptPath $backendScript
Start-Sleep -Seconds 6
Start-DetachedProcess -ScriptPath $frontendScript
Start-Sleep -Seconds 2
Start-DetachedProcess -ScriptPath $mobileScript

Write-Host ""
Write-Host "All services started." -ForegroundColor Green
Write-Host "API:       http://127.0.0.1:8765" -ForegroundColor Cyan
Write-Host "Web UI:    http://127.0.0.1:3000" -ForegroundColor Cyan
Write-Host "Mobile UI: http://127.0.0.1:3001" -ForegroundColor Cyan
Write-Host ""
Write-Host "Use 8765 for API calls, 3000 for desktop UI, and 3001 for mobile UI." -ForegroundColor Yellow
