# doc: 定义下载类的基础操作
from abc import ABC, abstractmethod
import json
from loguru import logger
import os
import subprocess
import time
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
from urllib.parse import urljoin
from ..comm import *
from curl_cffi import requests


@dataclass
class AVDownloadInfo:
    m3u8: str = ""
    title: str = ""
    avid: str = ""
    estimated_bytes: int = 0

    def __str__(self):
        return (
            f"=== 元数据详情 ===\n"
            f"番号: {self.avid or '未知'}\n"
            f"标题: {self.title or '未知'}\n"
            f"M3U8: {self.m3u8 or '无'}"
        )

    def to_json(self, file_path: str, indent: int = 2) -> bool:
        try:
            path = Path(file_path) if isinstance(file_path, str) else file_path
            path.parent.mkdir(parents=True, exist_ok=True)

            with path.open('w', encoding='utf-8') as f:
                json.dump(asdict(self), f, ensure_ascii=False, indent=indent)
            return True
        except (IOError, TypeError) as e:
            logger.error(f"JSON序列化失败: {str(e)}")
            return False


class Downloader(ABC):
    def __init__(self, path: str, proxy=None, timeout=15):
        self.path = path
        self.proxy = proxy
        self.proxies = {
            'http': proxy,
            'https': proxy
        } if proxy else None
        self.timeout = timeout
        self.domain = ""

    def setDomain(self, domain: str) -> bool:
        if domain:
            self.domain = domain
            return True
        return False

    def build_headers(self, referer: str = "") -> dict:
        return build_site_headers(self.domain, referer)

    @abstractmethod
    def getDownloaderName(self) -> str:
        pass

    @abstractmethod
    def getHTML(self, avid: str) -> Optional[str]:
        pass

    @abstractmethod
    def parseHTML(self, html: str) -> Optional[AVDownloadInfo]:
        pass

    def downloadInfo(self, avid: str) -> Optional[AVDownloadInfo]:
        avid = avid.upper()
        os.makedirs(os.path.join(self.path, avid), exist_ok=True)
        html = self.getHTML(avid)
        if not html:
            logger.error("获取html失败")
            return None
        with open(os.path.join(self.path, avid, avid + ".html"), "w+", encoding='utf-8') as f:
            f.write(html)

        info = self.parseHTML(html)
        if info is None:
            logger.error("解析元数据失败")
            return None

        info.avid = info.avid.upper()
        if not info.estimated_bytes and info.m3u8:
            info.estimated_bytes = self._estimate_total_bytes(info.m3u8)
        info.to_json(os.path.join(self.path, avid, "download_info.json"))
        logger.info("已保存到 download_info.json")

        return info

    def downloadM3u8(self, url: str, avid: str) -> bool:
        output_dir = Path(self.path) / avid
        output_dir.mkdir(parents=True, exist_ok=True)
        ts_path = output_dir / f"{avid}.ts"
        mp4_path = output_dir / f"{avid}.mp4"
        progress_path = output_dir / 'download_progress.json'
        estimated_bytes = self._read_cached_estimated_bytes(output_dir) or self._estimate_total_bytes(url)

        def write_progress(phase: str, downloaded_bytes: int = 0, speed_bytes_per_sec: float = 0.0, progress_percent: float = 0.0) -> None:
            payload = {
                'phase': phase,
                'downloadedBytes': max(int(downloaded_bytes), 0),
                'estimatedBytes': max(int(estimated_bytes), 0),
                'speedBytesPerSec': max(float(speed_bytes_per_sec), 0.0),
                'progressPercent': max(0.0, min(float(progress_percent), 100.0)),
                'updatedAt': int(time.time())
            }
            try:
                progress_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
            except OSError as e:
                logger.debug(f"写入下载进度失败: {e}")

        def read_size(path: Path) -> int:
            try:
                return path.stat().st_size
            except OSError:
                return 0

        def calc_progress(downloaded_bytes: int) -> float:
            if estimated_bytes <= 0:
                return 0.0
            return min(96.0, downloaded_bytes / estimated_bytes * 100)

        def run_downloader(use_proxy: bool) -> bool:
            command = [download_tool, '-u', url, '-o', str(ts_path), '-H', f'Referer:http://{self.domain}']
            if use_proxy and self.proxy:
                command.extend(['-p', self.proxy])
                logger.info('使用代理')
            else:
                logger.info('不使用代理')
            logger.debug(command)

            write_progress('starting', read_size(ts_path), 0.0, 0.0)
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, text=True)
            last_bytes = read_size(ts_path)
            last_time = time.monotonic()

            while process.poll() is None:
                time.sleep(1)
                current_bytes = read_size(ts_path)
                now = time.monotonic()
                elapsed = max(now - last_time, 0.001)
                speed = max(current_bytes - last_bytes, 0) / elapsed
                write_progress('downloading', current_bytes, speed, calc_progress(current_bytes))
                last_bytes = current_bytes
                last_time = now

            process.wait()
            final_bytes = read_size(ts_path)
            write_progress('downloading', final_bytes, 0.0, calc_progress(final_bytes))
            if process.returncode != 0:
                logger.error(f'下载器退出码异常: {process.returncode}')
                write_progress('failed', final_bytes, 0.0, calc_progress(final_bytes))
                return False
            return True

        try:
            first_attempt_with_proxy = bool(isNeedVideoProxy and self.proxy)
            if not run_downloader(first_attempt_with_proxy):
                retry_with_proxy = bool((not first_attempt_with_proxy) and self.proxy)
                if retry_with_proxy == first_attempt_with_proxy:
                    return False
                logger.info('首次下载失败，切换网络策略重试')
                if not run_downloader(retry_with_proxy):
                    return False

            write_progress('finalizing', read_size(ts_path), 0.0, 98.0)
            convert = [ffmpeg_tool, '-y', '-i', str(ts_path), '-c', 'copy', '-f', 'mp4', str(mp4_path)]
            logger.debug(convert)
            completed = subprocess.run(convert, capture_output=True, text=True)
            if completed.returncode != 0:
                logger.error(completed.stdout)
                logger.error(completed.stderr)
                write_progress('failed', read_size(ts_path), 0.0, 98.0)
                return False

            write_progress('completed', read_size(mp4_path), 0.0, 100.0)
            if ts_path.exists():
                ts_path.unlink()
            if progress_path.exists():
                progress_path.unlink()
            return True
        except FileNotFoundError as e:
            logger.error(f"工具不存在: {e}")
            write_progress('failed', read_size(ts_path), 0.0, 0.0)
            return False
        except Exception as e:
            logger.error(f"下载失败: {e}")
            write_progress('failed', read_size(ts_path), 0.0, 0.0)
            return False

    def _fetch_html(self, url: str, referer: str = "") -> Optional[str]:
        logger.debug(f"fetch url: {url}")
        try:
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=self.build_headers(referer),
                timeout=self.timeout,
                impersonate="chrome110",
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败: {str(e)}")
            return None

    def _read_cached_estimated_bytes(self, output_dir: Path) -> int:
        info_path = output_dir / 'download_info.json'
        if not info_path.exists():
            return 0
        try:
            payload = json.loads(info_path.read_text(encoding='utf-8'))
            return max(int(payload.get('estimated_bytes') or 0), 0)
        except Exception:
            return 0

    def _estimate_total_bytes(self, m3u8_url: str) -> int:
        try:
            response = requests.get(
                m3u8_url,
                proxies=self.proxies,
                headers=self.build_headers(f'https://{self.domain}/'),
                timeout=self.timeout,
                impersonate="chrome110",
            )
            response.raise_for_status()
            lines = [line.strip() for line in response.text.splitlines() if line.strip()]
            segments = [urljoin(m3u8_url, line) for line in lines if not line.startswith('#')]
            if not segments:
                return 0

            sample_count = min(len(segments), 8)
            sample_sizes = []
            for segment_url in segments[:sample_count]:
                try:
                    head = requests.head(
                        segment_url,
                        proxies=self.proxies,
                        headers=self.build_headers(f'https://{self.domain}/'),
                        timeout=self.timeout,
                        impersonate="chrome110",
                        allow_redirects=True,
                    )
                    head.raise_for_status()
                    content_length = head.headers.get('Content-Length') or head.headers.get('content-length')
                    if content_length:
                        sample_sizes.append(int(content_length))
                        continue
                except Exception:
                    pass

                try:
                    get_resp = requests.get(
                        segment_url,
                        proxies=self.proxies,
                        headers=self.build_headers(f'https://{self.domain}/'),
                        timeout=self.timeout,
                        impersonate="chrome110",
                    )
                    get_resp.raise_for_status()
                    content_length = get_resp.headers.get('Content-Length') or get_resp.headers.get('content-length')
                    if content_length:
                        sample_sizes.append(int(content_length))
                    else:
                        sample_sizes.append(len(get_resp.content))
                except Exception:
                    continue

            if not sample_sizes:
                return 0

            average_size = sum(sample_sizes) / len(sample_sizes)
            return int(average_size * len(segments))
        except Exception as e:
            logger.debug(f"估算总大小失败: {e}")
            return 0
