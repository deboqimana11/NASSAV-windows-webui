<div align="center">
<img style="max-width:50%;" src="pic/logo.png" alt="NASSAV" />
<br>
</div>

<div align="center">
  <img src="https://img.shields.io/github/stars/Satoing/NASSAV?style=for-the-badge&color=FF69B4" alt="Stars">
  <img src="https://img.shields.io/github/forks/Satoing/NASSAV?style=for-the-badge&color=FF69B4" alt="Forks">
  <img src="https://img.shields.io/github/issues/Satoing/NASSAV?style=for-the-badge&color=FF69B4" alt="Issues">
  <img src="https://img.shields.io/github/license/Satoing/NASSAV?style=for-the-badge&color=FF69B4" alt="License">
</div>

## 项目简介

NASSAV 是一个基于 Python 的多源影片下载与刮削工具。

这份仓库已经补齐 Windows 可用所需的关键兼容改造，当前在 `D:\22\NASSAV` 下已经实际跑通过：
- `VEC-769`
- `IPZZ-776`

当前这套 Windows 方案的核心不是“纯 HTTP 抓站”，而是：
- 常规请求能拿到页面时，直接解析下载
- MissAV 遇到 Cloudflare 时，自动切换到 Playwright 浏览器模式获取真实详情页
- 元数据优先从本地保存的 MissAV 页面解析，不再强依赖 JavBus
- 下载完成后自动生成 `metadata.json`、`.nfo`、封面和预览图

## 当前已完成的 Windows 兼容改造

- Python 下载链路改成跨平台调用，不再依赖 Unix `rm` 和 shell 拼接
- `main.py` 支持 Windows 下直接传入车牌号参数
- Go 后端不再写死 Linux 路径，改为读取 `cfg/configs.json`
- 前端 API 地址和 API Key 改为 Vite 环境变量
- 新增 `queue_runner.py` 作为跨平台批量任务入口
- 新增 MissAV 浏览器回退脚本：`tools/missav_browser_fetch.mjs`
- 新增浏览器配置项：`BrowserFallbackEnabled`、`BrowserProfilePath`、`SiteCookies`、`SiteHeaders`

## 目录结构

```text
NASSAV/
├── backend/            # Go HTTP 服务
├── cfg/                # 配置文件
├── db/                 # sqlite 和下载队列
├── frontend/           # Vue 前端
├── src/                # Python 主逻辑
├── tools/              # 辅助工具和浏览器抓取脚本
├── videos/             # 下载输出目录
├── main.py             # 单个下载入口
├── metadata.py         # 批量补刮削入口
├── queue_runner.py     # 跨平台队列执行器
└── package.json        # Playwright 依赖
```

## 环境要求

- Python 3.11+
- Node.js 18+
- Go 1.22+
- 可用代理
- Windows 10/11

说明：
- 仓库已优先支持 Windows 本地运行。
- `backend` 使用 `github.com/mattn/go-sqlite3`，在 Windows 上编译时可能需要 MinGW / MSYS2 / GCC。
- 仓库内如存在 `tools/ffmpeg.exe`、`tools/m3u8-Downloader-Go.exe`，会优先使用本地工具；否则也可走系统 PATH。

## 快速开始

### 1. 克隆项目

```powershell
git clone https://github.com/Satoing/NASSAV.git
cd NASSAV
```

### 2. 安装 Python 依赖

```powershell
pip install -r requirements.txt
```

### 3. 安装 Node 依赖和浏览器

根目录需要安装 Playwright：

```powershell
npm install
npx playwright install chromium
```

说明：
- 这里不是在 `frontend` 目录安装，而是在项目根目录安装。
- MissAV 被 Cloudflare 拦截时，程序会调用这个 Chromium 做浏览器回退。

### 4. 配置 `cfg/configs.json`

如果还没有配置文件：

```powershell
Copy-Item cfg\configs.json.example cfg\configs.json
```

建议重点关注这些字段：

```json
{
  "LogPath": "./logs",
  "SavePath": "./videos",
  "DBPath": "./db/downloaded.db",
  "QueuePath": "./db/download_queue.txt",
  "Proxy": "http://127.0.0.1:7897",
  "IsNeedVideoProxy": false,
  "BrowserFallbackEnabled": true,
  "BrowserFetchTimeoutSec": 180,
  "BrowserProfilePath": "./.browser-profile/missav"
}
```

关键说明：
- `Proxy`：本地代理地址，当前 Windows 环境下已实际使用 `127.0.0.1:7897`
- `BrowserFallbackEnabled`：开启 MissAV 浏览器模式回退
- `BrowserProfilePath`：Playwright 浏览器用户目录，首次运行后会自动生成
- `SiteCookies`：可给指定站点注入 Cookie，用于提高站点可访问率
- `SiteHeaders`：可给指定站点附加请求头

## 单个资源下载

Windows PowerShell：

```powershell
python main.py VEC-769
python main.py IPZZ-776
```

强制重新下载：

```powershell
python main.py IPZZ-776 -f
```

下载成功后，输出目录类似：

```text
videos/
└── IPZZ-776/
    ├── IPZZ-776.mp4
    ├── IPZZ-776.html
    ├── IPZZ-776.nfo
    ├── IPZZ-776-poster.jpg
    ├── IPZZ-776-fanart-1.jpg
    ├── ...
    └── metadata.json
```

## 浏览器回退机制

这是当前 Windows 能跑通 MissAV 的关键。

程序流程如下：
1. 先按普通 HTTP 请求 MissAV 页面。
2. 如果被 Cloudflare 拦住，自动调用 `tools/missav_browser_fetch.mjs`。
3. Playwright 打开目标页面或搜索车牌号。
4. 把真实详情页 HTML 保存到影片目录。
5. 后续从这个本地 HTML 解析 m3u8、标题、封面和预览图。

因此你看到站内请求可能不是传统页面接口，而是媒体流、推荐接口或 Cloudflare 校验流量，这都是正常的。真正关键的是浏览器最终能否落到影片详情页。

## Windows 一键启动

已经提供 4 个 PowerShell 脚本：

```powershell
.\start_backend.ps1
.\start_frontend.ps1
.\start_all.ps1
.\run_all.ps1
```

说明：
- `start_backend.ps1`：启动 Go 后端
- `start_frontend.ps1`：启动 Vue 前端开发服务器
- `start_all.ps1`：分别打开两个 PowerShell 窗口，同时启动前后端
- `run_all.ps1`：在同一个 PowerShell 窗口内启动整套服务，适合直接盯日志

默认地址：
- 后端：`http://127.0.0.1:31471`
- 前端：`http://127.0.0.1:5173`

## 批量队列执行

向 `db/download_queue.txt` 中追加车牌号后执行：

```powershell
python queue_runner.py
```

Windows 下建议直接用“任务计划程序”定时运行：

```powershell
python D:\path\to\NASSAV\queue_runner.py
```

## 补刮削已有资源

已有视频文件后，可以重新补齐元数据：

```powershell
python metadata.py
```

当前逻辑会优先读取本地 `<AVID>.html`，其次再尝试其它来源，因此比旧版更适合 MissAV 当前环境。

## 后端 API

启动 Go 后端：

```powershell
cd backend
go build -o main.exe
.\main.exe
```

默认端口：`31471`

可用环境变量：
- `NASSAV_PROJECT_ROOT`
- `NASSAV_MEDIA_PATH`
- `NASSAV_DB_PATH`
- `NASSAV_SERVER_PORT`
- `NASSAV_API_KEY`
- `NASSAV_PYTHON`
- `NASSAV_FFMPEG`
- `NASSAV_M3U8_DOWNLOADER`

示例接口：

```text
GET /api/videos
GET /api/videos/{id}
GET /api/addvideo/{id}
```

PowerShell 调用示例：

```powershell
$headers = @{ Authorization = 'Bearer IBHUSDBWQHJEJOBDSW' }
Invoke-RestMethod -Uri 'http://127.0.0.1:31471/api/addvideo/IPZZ-776' -Headers $headers
```

## 前端预览

先复制环境文件：

```powershell
Copy-Item frontend\.env.example frontend\.env
```

`frontend/.env` 示例：

```env
VITE_API_BASE=http://127.0.0.1:31471
VITE_API_KEY=IBHUSDBWQHJEJOBDSW
```

启动前端：

```powershell
cd frontend
npm install
npm run dev
```

打包：

```powershell
npm run build
```

## 已知事项

- MissAV、Jable 这类站点会频繁换规则，失效时优先检查域名、代理和 Cookie。
- 光靠 `cf_clearance` 不一定足够，很多情况下还是要靠浏览器模式真正通过 Cloudflare。
- 下载频率太高容易触发风控。
- Dockerfile 仍更偏向 Linux 容器，不是当前这套 Windows 原生方案的重点入口。

## Reference

1. [m3u8-Downloader-Go](https://github.com/Greyh4t/m3u8-Downloader-Go)
2. [mrjet](https://github.com/cailurus/mrjet)

## 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。



