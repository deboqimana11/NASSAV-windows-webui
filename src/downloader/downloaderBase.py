# doc: 定义下载类的基础操作
from abc import ABC, abstractmethod
import json
from loguru import logger
import os
import subprocess
from dataclasses import dataclass, asdict
from typing import Optional
from pathlib import Path
from ..comm import *
from curl_cffi import requests


@dataclass
class AVDownloadInfo:
    m3u8: str = ""
    title: str = ""
    avid: str = ""

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
        info.to_json(os.path.join(self.path, avid, "download_info.json"))
        logger.info("已保存到 download_info.json")

        return info

    def downloadM3u8(self, url: str, avid: str) -> bool:
        output_dir = Path(self.path) / avid
        output_dir.mkdir(parents=True, exist_ok=True)
        ts_path = output_dir / f"{avid}.ts"
        mp4_path = output_dir / f"{avid}.mp4"

        def run_downloader(use_proxy: bool) -> bool:
            command = [download_tool, '-u', url, '-o', str(ts_path), '-H', f'Referer:http://{self.domain}']
            if use_proxy and self.proxy:
                command.extend(['-p', self.proxy])
                logger.info('使用代理')
            else:
                logger.info('不使用代理')
            logger.debug(command)
            completed = subprocess.run(command, capture_output=True, text=True)
            if completed.returncode != 0:
                logger.error(completed.stdout)
                logger.error(completed.stderr)
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

            convert = [ffmpeg_tool, '-y', '-i', str(ts_path), '-c', 'copy', '-f', 'mp4', str(mp4_path)]
            logger.debug(convert)
            completed = subprocess.run(convert, capture_output=True, text=True)
            if completed.returncode != 0:
                logger.error(completed.stdout)
                logger.error(completed.stderr)
                return False

            if ts_path.exists():
                ts_path.unlink()
            return True
        except FileNotFoundError as e:
            logger.error(f"工具不存在: {e}")
            return False
        except Exception as e:
            logger.error(f"下载失败: {e}")
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
