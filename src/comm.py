import json
import random
import shutil
from loguru import logger
import os
import platform
from pathlib import Path

current_file_path = Path(__file__).resolve()
project_root = current_file_path.parent.parent

config_path = project_root / 'cfg' / 'configs.json'
with config_path.open('r', encoding='utf-8') as file:
    configs = json.load(file)


def resolve_project_path(raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = project_root / path
    return path.resolve()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def resolve_binary(env_name: str, candidates: list[str]) -> str:
    override = os.getenv(env_name)
    if override:
        return override

    for candidate in candidates:
        candidate_path = Path(candidate)
        if candidate_path.is_absolute() and candidate_path.exists():
            return str(candidate_path)

        local_candidate = project_root / candidate
        if local_candidate.exists():
            return str(local_candidate.resolve())

        discovered = shutil.which(candidate)
        if discovered:
            return discovered

    return candidates[0]


def get_site_config_value(mapping: dict, domain: str, default=None):
    if not isinstance(mapping, dict):
        return default
    return mapping.get(domain, mapping.get(domain.lower(), default))


def build_site_headers(domain: str = '', referer: str = '') -> dict:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    configured_headers = get_site_config_value(site_headers, domain, {})
    if isinstance(configured_headers, dict):
        headers.update(configured_headers)

    cookie_value = get_site_config_value(site_cookies, domain, '')
    if cookie_value:
        headers['Cookie'] = cookie_value

    if referer:
        headers['Referer'] = referer
    elif domain and 'Referer' not in headers:
        headers['Referer'] = f'https://{domain}/'

    return headers


log_path = resolve_project_path(configs.get('LogPath', './logs'))
save_path = str(resolve_project_path(configs.get('SavePath', './videos')))
downloaded_path = str(resolve_project_path(configs.get('DBPath', './db/downloaded.db')))
queue_path = str(resolve_project_path(configs.get('QueuePath', './db/download_queue.txt')))
myproxy = configs.get('Proxy', '') or None
isNeedVideoProxy = configs.get('IsNeedVideoProxy', False)
site_cookies = configs.get('SiteCookies', {})
site_headers = configs.get('SiteHeaders', {})
scraper_domains = configs.get('ScraperDomain') or [
    'www.javbus.com',
    'www.busdmm.ink',
    'www.dmmsee.bond'
]
browser_fallback_enabled = configs.get('BrowserFallbackEnabled', True)
browser_fetch_timeout_sec = int(configs.get('BrowserFetchTimeoutSec', 180))
browser_profile_path = str(resolve_project_path(configs.get('BrowserProfilePath', './.browser-profile/missav')))

log_path.mkdir(parents=True, exist_ok=True)
Path(save_path).mkdir(parents=True, exist_ok=True)
ensure_parent(Path(downloaded_path))
ensure_parent(Path(queue_path))
Path(downloaded_path).touch(exist_ok=True)
Path(queue_path).touch(exist_ok=True)
Path(browser_profile_path).mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_path / '{time:YYYY-MM-DD}.log'),
    rotation='00:00',
    retention='7 days',
    enqueue=False,
    level='DEBUG',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}'
)

sorted_downloaders = sorted(
    [downloader for downloader in configs.get('Downloader', []) if downloader.get('weight', 0) != 0],
    key=lambda x: x['weight'],
    reverse=True
)
missAVDomain = ''
for downloader in configs.get('Downloader', []):
    if downloader.get('downloaderName') == 'MissAV':
        missAVDomain = downloader.get('domain', '')
        break
logger.info(f'missav domain: {missAVDomain}')

scraperDomain = random.choice(scraper_domains)
logger.info(f'scraper domain: {scraperDomain}')

if platform.system() == 'Windows':
    download_tool = resolve_binary('NASSAV_M3U8_DOWNLOADER', ['tools/m3u8-Downloader-Go.exe', 'm3u8-Downloader-Go.exe'])
    ffmpeg_tool = resolve_binary('NASSAV_FFMPEG', ['tools/ffmpeg.exe', 'ffmpeg.exe', 'ffmpeg'])
else:
    download_tool = resolve_binary('NASSAV_M3U8_DOWNLOADER', ['tools/m3u8-Downloader-Go', 'm3u8-Downloader-Go'])
    ffmpeg_tool = resolve_binary('NASSAV_FFMPEG', ['ffmpeg'])

node_tool = resolve_binary('NASSAV_NODE', ['node'])
