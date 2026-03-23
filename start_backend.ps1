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
$env:NASSAV_SERVER_PORT = "$Port"
$backendExe = Resolve-BackendExe

Write-Host "启动后端: http://127.0.0.1:$Port"
& $backendExe
