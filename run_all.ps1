param(
  [int]$ApiPort = 31471,
  [int]$WebPort = 5173,
  [string]$BindHost = '0.0.0.0'
)

$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot

function Ensure-Config {
  $configPath = Join-Path $PSScriptRoot 'cfg\configs.json'
  $examplePath = Join-Path $PSScriptRoot 'cfg\configs.json.example'

  if (-not (Test-Path $configPath)) {
    if (-not (Test-Path $examplePath)) {
      throw '缺少 cfg\configs.json.example，无法自动生成配置文件。'
    }

    Copy-Item $examplePath $configPath
    Write-Host '已自动创建 cfg\configs.json，请按需检查代理等配置。'
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
    Write-Host '检测到 backend\main，已自动复制为 backend\main.exe。'
    return $exePath
  }

  $goCmd = Get-Command go -ErrorAction SilentlyContinue
  if ($goCmd) {
    Write-Host '未找到 backend\main.exe，正在自动编译 Go 后端...'
    Push-Location (Join-Path $PSScriptRoot 'backend')
    try {
      & $goCmd.Source build -o main.exe
    }
    finally {
      Pop-Location
    }

    if (Test-Path $exePath) {
      Write-Host 'Go 后端编译完成。'
      return $exePath
    }
  }

  throw '后端可执行文件不存在，且自动修复失败。请确认 backend\main.exe 已随仓库提供，或本机已安装 Go。'
}

Ensure-Config
$backendExe = Resolve-BackendExe
$env:NASSAV_SERVER_PORT = "$ApiPort"

$playwrightModule = Join-Path $PSScriptRoot 'node_modules\playwright'
if (-not (Test-Path $playwrightModule)) {
  Write-Host 'Playwright not found, installing dependencies...'
  Set-Location $PSScriptRoot
  npm install
  npx playwright install chromium
}

$backendJob = Start-Job -ScriptBlock {
  param($projectRoot, $port, $backendExePath)
  Set-Location $projectRoot
  $env:NASSAV_SERVER_PORT = "$port"
  & $backendExePath
} -ArgumentList $PSScriptRoot, $ApiPort, $backendExe

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
    Write-Host '已自动创建 frontend\.env。'
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
