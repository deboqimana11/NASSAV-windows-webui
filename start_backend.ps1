param(
  [int]$Port = 31471
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$env:NASSAV_SERVER_PORT = "$Port"
$backendExe = Join-Path $PSScriptRoot 'backend\main.exe'

if (-not (Test-Path $backendExe)) {
  Write-Host 'backend\main.exe 不存在，先执行 go build -o main.exe'
  exit 1
}

Write-Host "启动后端: http://127.0.0.1:$Port"
& $backendExe
