param(
  [int]$ApiPort = 31471,
  [int]$WebPort = 5173
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

$backendScript = Join-Path $PSScriptRoot 'start_backend.ps1'
$frontendScript = Join-Path $PSScriptRoot 'start_frontend.ps1'

Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File', $backendScript, '-Port', $ApiPort) -WorkingDirectory $PSScriptRoot | Out-Null
Start-Sleep -Seconds 2
Start-Process -FilePath 'powershell.exe' -ArgumentList @('-NoExit','-ExecutionPolicy','Bypass','-File', $frontendScript, '-Port', $WebPort) -WorkingDirectory $PSScriptRoot | Out-Null

Write-Host "Started backend http://127.0.0.1:$ApiPort and frontend http://127.0.0.1:$WebPort"
Write-Host 'If cfg\configs.json does not exist, the backend window will create it from the example file automatically.'
