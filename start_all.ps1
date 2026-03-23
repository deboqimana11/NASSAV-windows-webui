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

Write-Host "已启动后端 http://127.0.0.1:$ApiPort 和前端 http://127.0.0.1:$WebPort"
Write-Host '如果 cfg\configs.json 不存在，后端窗口会自动从示例文件生成。'
