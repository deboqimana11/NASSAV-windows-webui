param(
  [int]$Port = 31471
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Ensure-Config {
  $configPath = Join-Path $PSScriptRoot 'cfg\configs.json'
  $examplePath = Join-Path $PSScriptRoot 'cfg\configs.json.example'

  if (-not (Test-Path $configPath)) {
    if (-not (Test-Path $examplePath)) {
      throw 'Missing cfg\configs.json.example. Cannot create cfg\configs.json automatically.'
    }

    Copy-Item $examplePath $configPath
    Write-Host 'Created cfg\configs.json automatically. Please review proxy and related settings if needed.'
  }
}

function Resolve-BackendExe {
  $exePath = Join-Path $PSScriptRoot 'backend\main.exe'
  $legacyPath = Join-Path $PSScriptRoot 'backend\main'

  if (Test-Path $exePath) {
    return $exePath
  }

  if (Test-Path $legacyPath) {
    Copy-Item $legacyPath $exePath -Force
    Write-Host 'Found backend\main and copied it to backend\main.exe.'
    return $exePath
  }

  $goCmd = Get-Command go -ErrorAction SilentlyContinue
  if ($goCmd) {
    Write-Host 'backend\main.exe not found. Building Go backend automatically...'
    Push-Location (Join-Path $PSScriptRoot 'backend')
    try {
      & $goCmd.Source build -o main.exe
    }
    finally {
      Pop-Location
    }

    if (Test-Path $exePath) {
      Write-Host 'Go backend build completed.'
      return $exePath
    }
  }

  throw 'Backend executable is missing and automatic recovery failed. Provide backend\main.exe or install Go.'
}

Ensure-Config
$env:NASSAV_SERVER_PORT = "$Port"
$backendExe = Resolve-BackendExe

Write-Host "Backend: http://127.0.0.1:$Port"
& $backendExe
