param(
  [int]$ApiPort = 31471,
  [int]$WebPort = 5173,
  [string]$BindHost = '0.0.0.0'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$backendExe = Join-Path $PSScriptRoot 'backend\main.exe'
if (-not (Test-Path $backendExe)) {
  Write-Host 'backend\main.exe not found, build it first with go build -o main.exe'
  exit 1
}

$env:NASSAV_SERVER_PORT = "$ApiPort"

$playwrightModule = Join-Path $PSScriptRoot 'node_modules\playwright'
if (-not (Test-Path $playwrightModule)) {
  Write-Host 'Playwright not found, installing dependencies...'
  Set-Location $PSScriptRoot
  npm install
  npx playwright install chromium
}

$backendJob = Start-Job -ScriptBlock {
  param($projectRoot, $port)
  Set-Location $projectRoot
  $env:NASSAV_SERVER_PORT = "$port"
  & (Join-Path $projectRoot 'backend\main.exe')
} -ArgumentList $PSScriptRoot, $ApiPort

try {
  Start-Sleep -Seconds 2

  $lanIps = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -match '^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\.' } |
    Select-Object -ExpandProperty IPAddress -Unique)

  if (-not $lanIps -or $lanIps.Count -eq 0) {
    $lanIps = @('127.0.0.1')
  }

  Set-Location (Join-Path $PSScriptRoot 'frontend')
  if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
  }

  foreach ($ip in $lanIps) {
    Write-Host ("Backend: http://{0}:{1}" -f $ip, $ApiPort)
    Write-Host ("Frontend: http://{0}:{1}" -f $ip, $WebPort)
  }
  Write-Host 'Use the Frontend URL above on a phone connected to the same Wi-Fi.'

  npm run dev -- --host $BindHost --port $WebPort
}
finally {
  if ($backendJob) {
    Stop-Job $backendJob -ErrorAction SilentlyContinue | Out-Null
    Remove-Job $backendJob -Force -ErrorAction SilentlyContinue | Out-Null
  }
}
