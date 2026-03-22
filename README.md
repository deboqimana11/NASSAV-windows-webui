# NASSAV

NASSAV 是一个在 Windows 本机运行的多源视频下载、刮削和本地 Web UI 浏览工具。

这份 README 的目标很直接：

- 第一次打开仓库就知道怎么启动
- 第一次下载就知道该点哪里
- 出问题时知道先查什么

如果你只想最快用起来，直接看下面的 `3 分钟上手`。

---

## 1. 当前这份仓库能做什么

当前仓库已经针对 Windows 做了可用性改造，支持：

- 输入车牌号下载视频
- 自动生成 `mp4 / nfo / poster / fanart / metadata.json`
- 遇到 MissAV Cloudflare 时自动走 Playwright 浏览器模式回退
- 启动本地 Web UI 浏览视频列表
- 在 Web UI 详情页直接播放本地视频
- 首页自动轮询刷新下载状态和最新列表

已经在 Windows 下实际跑通过的例子包括：

- `VEC-769`
- `IPZZ-776`
- `SSIS-001`
- `ADN-707`
- `JUR-447`

---

## 2. 先记住这几个文件

最常用的入口就这几个：

- `run_all.bat`
  用资源管理器双击，最省事
- `run_all.ps1`
  在一个 PowerShell 窗口里同时启动前后端
- `main.py`
  命令行下载单个视频
- `metadata.py`
  重新补刮削已有视频
- `queue_runner.py`
  消费下载队列
- `cfg/configs.json`
  本机真实配置文件
- `cfg/configs.json.example`
  配置模板，应该提交到 GitHub 的是它

---

## 3. 3 分钟上手

### 3.1 克隆项目

```powershell
git clone https://github.com/Satoing/NASSAV.git
cd NASSAV
```

### 3.2 安装依赖

```powershell
pip install -r requirements.txt
npm install
npx playwright install chromium
```

说明：

- `npm install` 是在项目根目录执行，不是在 `frontend` 目录
- Playwright 是 MissAV 浏览器回退必须依赖

### 3.3 复制配置模板

```powershell
Copy-Item cfg\configs.json.example cfg\configs.json
```

然后打开 `cfg/configs.json`，至少检查这几个字段：

```json
{
  "SavePath": "./videos",
  "DBPath": "./db/downloaded.db",
  "QueuePath": "./db/download_queue.txt",
  "Proxy": "http://127.0.0.1:7897",
  "BrowserFallbackEnabled": true,
  "BrowserProfilePath": "./.browser-profile/missav"
}
```

关键字段解释：

- `Proxy`
  你自己的本地代理地址
- `BrowserFallbackEnabled`
  必须开，Cloudflare 拦截时靠它过站
- `BrowserProfilePath`
  浏览器模式的用户目录
- `SavePath`
  视频输出目录

### 3.4 启动 Web UI

最简单：

```bat
run_all.bat
```

启动后打开：

- 前端：`http://127.0.0.1:5173`
- 后端：`http://127.0.0.1:31471`

### 3.5 在 Web UI 里下载

1. 打开首页
2. 顶部输入车牌号，例如 `IPZZ-776`
3. 点击“添加下载”
4. 首页会显示：
   - 当前下载中的是哪个车牌
   - 队列里还有没有等待任务
   - 下载完成后视频会自动出现在列表
5. 点击封面进入详情页，可以直接播放本地视频

---

## 4. 如果你不用 Web UI，只想命令行下载

### 下载单个视频

```powershell
python main.py IPZZ-776
```

### 强制重新执行

```powershell
python main.py IPZZ-776 -f
```

### 下载成功后目录长这样

```text
videos/
└── IPZZ-776/
    ├── IPZZ-776.mp4
    ├── IPZZ-776.html
    ├── IPZZ-776.nfo
    ├── IPZZ-776-poster.jpg
    ├── IPZZ-776-fanart-1.jpg
    ├── IPZZ-776-fanart-2.jpg
    ├── ...
    └── metadata.json
```

字段含义：

- `mp4`
  视频文件
- `html`
  本地详情页快照
- `nfo`
  媒体库刮削文件
- `poster`
  竖版海报
- `fanart-*`
  横版样图 / 预览图
- `metadata.json`
  结构化元数据

---

## 5. 目录结构

```text
NASSAV/
├── backend/            # Go 后端服务
├── cfg/                # 配置文件
├── db/                 # sqlite 和下载队列
├── frontend/           # Vue Web UI
├── src/                # Python 主逻辑
├── tools/              # 浏览器抓取脚本 / ffmpeg / 下载器
├── videos/             # 视频输出目录
├── main.py             # 单个资源下载入口
├── metadata.py         # 补刮削入口
├── queue_runner.py     # 队列消费入口
├── run_all.bat         # Windows 双击启动入口
├── run_all.ps1         # 单窗口启动前后端
├── start_all.ps1       # 双窗口启动前后端
├── start_backend.ps1   # 只启动后端
└── start_frontend.ps1  # 只启动前端
```

---

## 6. Windows 启动脚本怎么选

### 最推荐：双击启动

```bat
run_all.bat
```

用途：

- 从资源管理器直接双击
- 自动调用 `run_all.ps1`

### 单窗口看日志

```powershell
.\run_all.ps1
```

用途：

- 同一个 PowerShell 窗口里启动前后端
- 适合看运行日志

### 双窗口分开跑

```powershell
.\start_all.ps1
```

### 分别启动

```powershell
.\start_backend.ps1
.\start_frontend.ps1
```

---

## 7. Web UI 现在有哪些功能

当前 Web UI 支持：

- 首页浏览视频列表
- 自动轮询更新列表
- 自动显示“下载中 / 排队任务”
- 点击封面进入详情页
- 详情页直接播放本地 `mp4`
- 查看 fanart 图集
- 删除本地视频后，页面会自动消失对应条目

---

## 8. 浏览器回退机制为什么重要

当前 Windows 能跑通 MissAV 的关键，不是“纯 HTTP 永远能抓”，而是浏览器模式兜底。

实际流程：

1. 先走普通 HTTP 请求
2. 如果被 Cloudflare 拦住，自动调用 `tools/missav_browser_fetch.mjs`
3. Playwright 打开详情页或根据车牌号搜索
4. 把真实 HTML 保存到本地目录
5. 后续从本地详情页解析 m3u8、标题、封面和 fanart

所以你在浏览器网络面板里经常看到：

- `media-hls...`
- `recombee.com`
- Cloudflare 校验流量
- 各种静态资源请求

这些都正常。关键在于浏览器模式最后能不能落到真实详情页。

---

## 9. 命令行和队列相关

### 补刮削已有视频

```powershell
python metadata.py
```

适用场景：

- 已经有 `mp4`
- 想重新生成 `nfo / poster / fanart / metadata.json`

### 消费下载队列

```powershell
python queue_runner.py
```

队列文件路径：

```text
db/download_queue.txt
```

现在状态接口会自动清理脏队列，所以不会因为历史残留误报“还在排队”。

---

## 10. API 说明

后端默认地址：

```text
http://127.0.0.1:31471
```

常用接口：

```text
GET /api/videos
GET /api/videos/{id}
GET /api/addvideo/{id}
GET /api/status
```

说明：

- `/api/videos`
  获取视频列表
- `/api/videos/{id}`
  获取视频详情
- `/api/addvideo/{id}`
  提交下载任务
- `/api/status`
  获取当前下载状态和队列

PowerShell 示例：

```powershell
$headers = @{ Authorization = 'Bearer IBHUSDBWQHJEJOBDSW' }
Invoke-RestMethod -Uri 'http://127.0.0.1:31471/api/addvideo/IPZZ-776' -Headers $headers
```

---

## 11. 当前配置文件应该怎么管理

真实本机配置是：

```text
cfg/configs.json
```

模板配置是：

```text
cfg/configs.json.example
```

建议规则：

- `cfg/configs.json`
  只留在本机，不要提交 GitHub
- `cfg/configs.json.example`
  提交到仓库，给别人看结构和默认值

原因：

- `cfg/configs.json` 里通常会有你自己的代理、Cookie、站点 header
- 这些属于本机敏感配置，不应该被推上远程仓库

---

## 12. 常见问题

### 为什么 Web UI 里添加下载后，列表不会立即更新？

现在已经修复：首页会自动轮询，后端也会在 `/api/videos` 请求时重扫 `videos` 目录。

### 为什么会显示“排队任务”，但其实没有在下载？

现在已经修复：状态接口会自动清理：

- 已下载完成的车牌
- 重复车牌
- 历史脏队列

### 为什么有些视频只有 1 张 fanart？

旧逻辑会把 `Jable` 本地页面错按 `MissAV` 规则解析。现在已经分开处理：

- `MissAV` 页面按 `nineyu` 规则抓图
- `Jable` 页面按 `thumbvtt.ts / thumb.ts` 规则切图

### 为什么命令行能下，网页里看不到视频？

正常情况下不会了。只要本地目录里生成了 `poster / nfo / mp4`，刷新或者等轮询就会出现。

### 为什么直接请求 MissAV 经常 403？

因为有 Cloudflare 风控。当前方案的关键就是浏览器模式回退，而不是指望纯 HTTP 永远可用。

---

## 13. 已知事项

- MissAV、Jable 等站点经常改规则，失效时优先检查：域名、代理、Cookie、浏览器模式
- 光靠 `cf_clearance` 不一定够，很多时候仍然要靠 Playwright 真正过 Cloudflare
- 下载频率太高容易触发风控
- Dockerfile 仍然更偏 Linux，不是当前这套 Windows 原生流程的重点入口

---

## 14. 参考项目

1. [m3u8-Downloader-Go](https://github.com/Greyh4t/m3u8-Downloader-Go)
2. [mrjet](https://github.com/cailurus/mrjet)

---

## 15. 许可证

本项目采用 MIT 许可证，详见 [LICENSE](LICENSE)。
