param(
  [int]$Port = 5173,
  [string]$BindHost = '0.0.0.0'
)

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot 'frontend')

if (-not (Test-Path '.env')) {
  Copy-Item '.env.example' '.env'
}

$lanIps = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
  Where-Object { $_.IPAddress -match '^192\.168\.|^10\.|^172\.(1[6-9]|2[0-9]|3[0-1])\.' } |
  Select-Object -ExpandProperty IPAddress -Unique)

if (-not $lanIps -or $lanIps.Count -eq 0) {
  $lanIps = @('127.0.0.1')
}

foreach ($ip in $lanIps) {
  Write-Host ("Frontend: http://{0}:{1}" -f $ip, $Port)
}
Write-Host 'Use the Frontend URL above on a phone connected to the same Wi-Fi.'

npm run dev -- --host $BindHost --port $Port
