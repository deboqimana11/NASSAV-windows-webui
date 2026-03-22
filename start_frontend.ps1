param(
  [int]$Port = 5173
)

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot 'frontend')

if (-not (Test-Path '.env')) {
  Copy-Item '.env.example' '.env'
}

Write-Host "启动前端: http://127.0.0.1:$Port"
npm run dev -- --host 127.0.0.1 --port $Port
