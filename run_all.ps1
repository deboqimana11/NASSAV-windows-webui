param(
  [int]$ApiPort = 31471,
  [int]$WebPort = 5173
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$backendExe = Join-Path $PSScriptRoot 'backend\main.exe'
if (-not (Test-Path $backendExe)) {
  Write-Host 'backend\main.exe 不存在，先执行 go build -o main.exe'
  exit 1
}

$env:NASSAV_SERVER_PORT = "$ApiPort"
$backendJob = Start-Job -ScriptBlock {
  param($projectRoot, $port)
  Set-Location $projectRoot
  $env:NASSAV_SERVER_PORT = "$port"
  & (Join-Path $projectRoot 'backend\main.exe')
} -ArgumentList $PSScriptRoot, $ApiPort

try {
  Start-Sleep -Seconds 2
  Set-Location (Join-Path $PSScriptRoot 'frontend')
  if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
  }
  Write-Host "后端: http://127.0.0.1:$ApiPort"
  Write-Host "前端: http://127.0.0.1:$WebPort"
  npm run dev -- --host 127.0.0.1 --port $WebPort
}
finally {
  if ($backendJob) {
    Stop-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue | Out-Null
  }
}
