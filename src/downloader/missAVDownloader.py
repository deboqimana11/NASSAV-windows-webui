from .downloaderBase import *
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple


class MissAVDownloader(Downloader):
    def getDownloaderName(self) -> str:
        return "MissAV"

    def getHTML(self, avid: str) -> Optional[str]:
        candidate_urls = [
            f'https://{self.domain}/cn/{avid}-chinese-subtitle'.lower(),
            f'https://{self.domain}/cn/{avid}-uncensored-leak'.lower(),
            f'https://{self.domain}/cn/{avid}'.lower(),
            f'https://{self.domain}/dm13/cn/{avid}'.lower(),
        ]

        for url in candidate_urls:
            content = self._fetch_html(url)
            if content:
                return content

        if browser_fallback_enabled:
            logger.info('MissAV 常规请求失败，尝试使用浏览器模式获取页面')
            for url in candidate_urls:
                content = self._fetch_html_via_browser(url, avid)
                if content:
                    return content

        return None

    def parseHTML(self, html: str) -> Optional[AVDownloadInfo]:
        missavMetadata = AVDownloadInfo()

        if uuid := self._extract_uuid(html):
            playlist_url = f"https://surrit.com/{uuid}/playlist.m3u8"
            result = self._get_highest_quality_m3u8(playlist_url)
            if result:
                m3u8_url, resolution = result
                logger.debug(f"最高清晰度: {resolution}\nM3U8链接: {m3u8_url}")
                missavMetadata.m3u8 = m3u8_url
            else:
                logger.error("未找到有效视频流")
                return None
        else:
            logger.error("未找到有效uuid")
            return None

        if not self._extract_metadata(html, missavMetadata):
            return None

        return missavMetadata

    def _fetch_html_via_browser(self, url: str, avid: str) -> Optional[str]:
        try:
            temp_dir = Path(self.path) / avid
            temp_dir.mkdir(parents=True, exist_ok=True)
            output_path = temp_dir / 'browser_fetch.html'
            command = [
                node_tool,
                str((project_root / 'tools' / 'missav_browser_fetch.mjs').resolve()),
                '--url', url,
                '--avid', avid,
                '--timeoutMs', str(browser_fetch_timeout_sec * 1000),
                '--userDataDir', browser_profile_path,
                '--output', str(output_path),
            ]
            if self.proxy:
                command.extend(['--proxy', self.proxy])

            logger.debug(command)
            completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8')
            html = ''
            if output_path.exists():
                html = output_path.read_text(encoding='utf-8', errors='ignore')

            if completed.returncode == 0 and html:
                if 'Just a moment' in html:
                    logger.error('浏览器模式仍然停留在 Cloudflare 验证页')
                    return None
                try:
                    output_path.unlink()
                except OSError:
                    pass
                return html

            logger.error(completed.stdout)
            logger.error(completed.stderr)
            if html and 'Just a moment' not in html:
                return html
            return None
        except Exception as e:
            logger.error(f'浏览器模式获取页面失败: {e}')
            return None

    @staticmethod
    def _extract_uuid(html: str) -> Optional[str]:
        try:
            if match := re.search(r"m3u8\|([a-f0-9\|]+)\|com\|surrit\|https\|video", html):
                return "-".join(match.group(1).split("|")[::-1])
            return None
        except Exception as e:
            logger.error(f"UUID提取异常: {str(e)}")
            return None

    @staticmethod
    def _extract_metadata(html: str, metadata: AVDownloadInfo) -> bool:
        try:
            og_title = re.search(r'<meta property="og:title" content="(.*?)"', html)

            if og_title:
                title_content = og_title.group(1)
                if code_match := re.search(r'^([A-Z]+(?:-[A-Z]+)*-\d+)', title_content):
                    metadata.avid = code_match.group(1)
                    metadata.title = title_content.replace(metadata.avid, '').strip()
                else:
                    metadata.title = title_content.strip()

        except Exception as e:
            logger.error(f"元数据解析异常: {str(e)}")
            return False

        return True

    def _get_highest_quality_m3u8(self, playlist_url: str) -> Optional[Tuple[str, str]]:
        try:
            response = requests.get(
                playlist_url,
                timeout=10,
                impersonate="chrome110",
                proxies=self.proxies,
                headers=self.build_headers(f'https://{self.domain}/')
            )
            response.raise_for_status()
            playlist_content = response.text

            streams = []
            pattern = re.compile(
                r'#EXT-X-STREAM-INF:BANDWIDTH=(\d+),.*?RESOLUTION=(\d+x\d+).*?\n(.*)'
            )

            for match in pattern.finditer(playlist_content):
                bandwidth = int(match.group(1))
                resolution = match.group(2)
                url = match.group(3).strip()
                streams.append((bandwidth, resolution, url))

            streams.sort(reverse=True, key=lambda x: x[0])
            logger.debug(streams)

            if streams:
                best_stream = streams[0]
                base_url = playlist_url.rsplit('/', 1)[0]
                full_url = f"{base_url}/{best_stream[2]}" if not best_stream[2].startswith('http') else best_stream[2]
                return full_url, best_stream[1]
            return None

        except Exception as e:
            logger.error(f"获取最高质量流失败: {str(e)}")
            return None
