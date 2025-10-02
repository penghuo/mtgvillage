<#
    Run backend smoke test and serve the frontend for local development on Windows.
#>
param(
    [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $RepoRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error 'Python 3.9 or newer is required on PATH.'
}

Write-Host 'Installing backend dependencies...' -ForegroundColor Cyan
python -m pip install -r requirements.txt

Write-Host 'Running backend smoke test...' -ForegroundColor Cyan
python -c 'import sys; from pathlib import Path; sys.path.insert(0, str(Path.cwd() / "scripts")); from mtg_price_checker import MTGPriceChecker; checker = MTGPriceChecker(); stores = ", ".join(checker.stores.keys()) or "none"; print(f"Configured stores: {stores}")'

Write-Host ("Starting static site server at http://127.0.0.1:{0}" -f $Port) -ForegroundColor Cyan
Write-Host 'Press Ctrl+C to stop the server when you are done testing.' -ForegroundColor Yellow
python -m http.server $Port
