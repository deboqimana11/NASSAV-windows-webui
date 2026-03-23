# doc: 使用本地 MissAV / Jable 页面或 JavBus 刮削元数据
import json
from io import BytesIO
from loguru import logger
import os
from dataclasses import dataclass, asdict, field
from typing import Optional
from pathlib import Path
from .comm import *
from curl_cffi import requests
from PIL import Image
from datetime import datetime
from urllib.parse import urlparse
import re
from xml.etree import ElementTree as ET
from xml.dom import minidom


def is_complete_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


@dataclass
class AVMetadata:
    title: str = ""
    cover: str = ""
    avid: str = ""
    actress: dict = field(default_factory=dict)
    description: str = ""
    duration: str = ""
    release_date: str = ""
    keywords: list[str] = field(default_factory=list)
    fanarts: list[str] = field(default_factory=list)
    source: str = ""
    sprite_vtt: str = ""
    sprite_image: str = ""

    def __str__(self):
        actress_str = "\n    ".join(
            [f"{name} ({avatar})" for name, avatar in self.actress.items()]
        ) if self.actress else "无"
        keywords_str = ", ".join(self.keywords) if self.keywords else "无"
        fanart_str = ", ".join(self.fanarts[:5]) if self.fanarts else "无"

        return (
            "=== 元数据详情 ===\n"
            f"番号: {self.avid or '未知'}\n"
            f"标题: {self.title or '未知'}\n"
            f"发行日期: {self.release_date or '未知'}\n"
            f"时长: {self.duration or '未知'}\n"
            f"演员及头像:\n    {actress_str}\n"
            f"关键词: {keywords_str}\n"
            f"描述: {self.description or '无'}\n"
            f"封面URL: {self.cover or '无'}\n"
            f"样品图像: {fanart_str}\n"
            "================="
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


headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": f"https://{scraperDomain}/",
    "Sec-Fetch-Mode": "navigate"
}


class Sracper:
    def __init__(self, path: str, proxy=None, timeout=15):
        self.path = path
        self.proxy = proxy
        self.proxies = {
            'http': proxy,
            'https': proxy
        } if proxy else None
        self.timeout = timeout
        self.domain = scraperDomain

    def scrape(self, avid: str) -> Optional[AVMetadata]:
        avid = avid.upper()
        local_html = Path(self.path) / avid / f"{avid}.html"
        metadata = None
        source = 'javbus'

        if local_html.exists():
            html = local_html.read_text(encoding='utf-8', errors='ignore')
            source = self._detect_local_source(html)
            logger.info(f'使用本地页面刮削: {local_html} ({source})')

            if source == 'missav':
                metadata = self._extract_missav(html, avid)
            elif source == 'jable':
                metadata = self._extract_jable_local(html, avid)
            else:
                metadata = self._extract_javbus(html)

            if metadata:
                if source == 'jable':
                    self._enrich_jable_metadata(metadata)

                if not metadata.release_date:
                    metadata.release_date = self._resolve_release_date(metadata.avid, html, source)
            else:
                logger.warning(f'本地页面解析失败，改为远程补抓: {avid}')

        if not metadata:
            metadata = self._fetch_javbus_metadata(avid)
            if not metadata:
                return None

        logger.info(f"parse metadata succ: \n{metadata}")

        if not self.downloadIMG(metadata):
            return None
        logger.info("download img succ")

        metadata.to_json(os.path.join(self.path, metadata.avid, 'metadata.json'))
        self.genNFO(metadata)
        logger.info("gennfo succ")
        return metadata

    def _detect_local_source(self, html: str) -> str:
        lowered = html.lower()
        if 'missav' in lowered or 'nineyu.com' in lowered or 'og:video:actor' in lowered:
            return 'missav'
        if 'jable.tv' in lowered or 'pagecontext' in lowered or 'var hlsurl =' in lowered:
            return 'jable'
        return 'javbus'

    def _extract_javbus(self, html: str) -> Optional[AVMetadata]:
        try:
            metadata = AVMetadata(source='javbus')
            avid = re.search(r'<title>((\d|[A-Z])+-\d+)', html).group(1)
            title = re.search(r'<title>(.*?) - JavBus</title>', html).group(1)
            cover = re.search(r'<a class="bigImage" href="([^"]+)"><img src="([^"]+)"', html).group(1)
            desc = re.search(r'<meta name="description" content="([^"]+)">', html).group(1)
            keywords = re.search(r'<meta name="keywords" content="([^"]+)">', html).group(1).split(',')
            date = re.search(r'<span class="header">發行日期:</span> ([^<]+)', html).group(1).strip()
            duration = re.search(r'<span class="header">長度:</span> ([^<]+)', html).group(1).strip()
            actresses = re.findall(r'<a class="avatar-box" href="[^"]+">\s*<div class="photo-frame">\s*<img src="([^"]+)"[^>]+>\s*</div>\s*<span>([^<]+)</span>', html)
            fanarts = re.findall(r'<a class="sample-box" href="(.*?\.jpg)">', html) or []

            metadata.avid = avid
            metadata.title = title
            metadata.cover = cover if is_complete_url(cover) else f"https://{self.domain}{cover}"
            metadata.description = desc
            metadata.keywords = keywords
            metadata.release_date = date
            metadata.duration = duration
            for img, name in actresses:
                metadata.actress[name] = img if is_complete_url(img) else f"https://{self.domain}{img}"
            metadata.fanarts = fanarts
            return metadata
        except Exception as e:
            logger.error(f"JavBus 解析失败: {e}")
            return None

    def _extract_missav(self, html: str, fallback_avid: str) -> Optional[AVMetadata]:
        try:
            metadata = AVMetadata(source='missav')

            og_title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            desc_match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
            keyword_match = re.search(r'<meta name="keywords" content="([^"]+)"', html)
            release_match = re.search(r'<meta property="og:video:release_date" content="([^"]+)"', html)
            duration_match = re.search(r'<meta property="og:video:duration" content="([^"]+)"', html)
            actor_matches = re.findall(r'<meta property="og:video:actor" content="([^"]+)"', html)
            seek_matches = re.findall(r'https?:\\/\\/nineyu\.com\\/[^"\']+?\.jpg', html)

            raw_title = og_title_match.group(1).strip() if og_title_match else fallback_avid
            avid_match = re.search(r'([A-Z]+(?:-[A-Z]+)*-\d+)', raw_title)
            metadata.avid = avid_match.group(1).upper() if avid_match else fallback_avid
            metadata.title = raw_title
            metadata.cover = og_image_match.group(1).strip() if og_image_match else ''
            metadata.description = (desc_match.group(1).strip() if desc_match else '') or raw_title
            metadata.keywords = [item.strip() for item in (keyword_match.group(1).split(',') if keyword_match else []) if item.strip()]
            metadata.release_date = release_match.group(1).strip() if release_match else ''

            if duration_match:
                try:
                    total_seconds = int(duration_match.group(1))
                    metadata.duration = str(max(1, total_seconds // 60)) + '分鐘'
                except ValueError:
                    metadata.duration = duration_match.group(1).strip()

            for actor in actor_matches:
                metadata.actress[actor.strip()] = ''

            fanarts = []
            for item in seek_matches:
                normalized = item.replace('\\/', '/')
                if normalized not in fanarts:
                    fanarts.append(normalized)
            metadata.fanarts = fanarts[:20]

            if not metadata.cover or not metadata.avid:
                return None
            return metadata
        except Exception as e:
            logger.error(f"MissAV 解析失败: {e}")
            return None

    def _extract_jable_local(self, html: str, fallback_avid: str) -> Optional[AVMetadata]:
        try:
            metadata = AVMetadata(source='jable')
            og_title_match = re.search(r'<meta property="og:title" content="([^"]+)"', html)
            og_image_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
            desc_match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
            video_id_match = re.search(r"videoId:\s*'([^']+)'", html)
            hls_url_match = re.search(r"var hlsUrl = '([^']+)'", html)
            vtt_url_match = re.search(r"var vttUrl = '([^']+)'", html)
            actress_matches = re.findall(r'/models/[^"\']+[^>]*>([^<]+)</a>', html)

            raw_title = og_title_match.group(1).strip() if og_title_match else fallback_avid
            avid_match = re.search(r'([A-Z]+(?:-[A-Z]+)*-\d+)', raw_title)
            metadata.avid = avid_match.group(1).upper() if avid_match else fallback_avid
            metadata.title = raw_title
            metadata.cover = og_image_match.group(1).strip() if og_image_match else ''
            metadata.description = (desc_match.group(1).strip() if desc_match else '') or raw_title
            metadata.keywords = ['Jable']
            metadata.release_date = self._extract_release_date_from_text(html)

            if video_id_match:
                metadata.keywords.append(f'videoId:{video_id_match.group(1)}')
            if hls_url_match:
                metadata.keywords.append('stream:hls')
            if vtt_url_match:
                metadata.sprite_vtt = vtt_url_match.group(1).strip()
                metadata.sprite_image = metadata.sprite_vtt.replace('thumbvtt.ts', 'thumb.ts')

            for actress in actress_matches:
                name = actress.strip()
                if name and name not in metadata.actress:
                    metadata.actress[name] = ''

            if not metadata.cover or not metadata.avid:
                return None
            return metadata
        except Exception as e:
            logger.error(f"Jable 本地页面解析失败: {e}")
            return None

    def _fetch_javbus_metadata(self, avid: str) -> Optional[AVMetadata]:
        candidate_domains = []
        for domain in [self.domain, *scraper_domains]:
            if domain and domain not in candidate_domains:
                candidate_domains.append(domain)

        for domain in candidate_domains:
            html = self._fetch_html(f'https://{domain}/{avid}', referer=f'https://{domain}/')
            if not html:
                continue
            metadata = self._extract_javbus(html)
            if metadata:
                logger.info(f'通过 {domain} 获取 JavBus 大图剧照: {avid} ({len(metadata.fanarts)} 张)')
                return metadata
        return None

    def _enrich_jable_metadata(self, metadata: AVMetadata) -> None:
        if metadata.source != 'jable':
            return
        if metadata.release_date and metadata.fanarts:
            return

        fallback = self._fetch_javbus_metadata(metadata.avid)
        if not fallback:
            return

        if not metadata.release_date and fallback.release_date:
            metadata.release_date = fallback.release_date
        if fallback.fanarts:
            metadata.fanarts = fallback.fanarts
        if not metadata.description and fallback.description:
            metadata.description = fallback.description
        if not metadata.keywords and fallback.keywords:
            metadata.keywords = fallback.keywords
    def _extract_release_date_from_text(self, text: str) -> str:
        patterns = [
            r'<meta property="og:video:release_date" content="([^\"]+)"',
            r'日期[^0-9]{0,20}(20\d{2}-\d{2}-\d{2})',
            r'日期[^0-9]{0,20}(20\d{2}/\d{2}/\d{2})',
            r'公開日[^0-9]{0,20}(20\d{2}-\d{2}-\d{2})',
            r'發行日期[^0-9]{0,20}(20\d{2}-\d{2}-\d{2})',
            r'发行日期[^0-9]{0,20}(20\d{2}-\d{2}-\d{2})',
            r'(20\d{2}-\d{2}-\d{2})'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).strip().replace('/', '-')
            if re.match(r'^20\d{2}-\d{2}-\d{2}$', value):
                return value
        return ''

    def _resolve_release_date(self, avid: str, html: str, source: str) -> str:
        local_date = self._extract_release_date_from_text(html)
        if local_date:
            return local_date

        candidate_domains = []
        for domain in [self.domain, *scraper_domains]:
            if domain and domain not in candidate_domains:
                candidate_domains.append(domain)

        for domain in candidate_domains:
            fallback_url = f'https://{domain}/{avid}'
            fallback_html = self._fetch_html(fallback_url, referer=f'https://{domain}/')
            if not fallback_html:
                continue
            bus_date = self._extract_release_date_from_text(fallback_html)
            if bus_date:
                logger.info(f'通过 {domain} 回填发行日期: {avid} -> {bus_date}')
                return bus_date
        return ''

    def _cleanup_existing_fanarts(self, metadata: AVMetadata) -> None:
        video_dir = Path(self.path) / metadata.avid
        pattern = re.compile(rf'^{re.escape(metadata.avid)}-fanart-\d+\.jpg$')
        for file in video_dir.iterdir():
            if not file.is_file() or not pattern.match(file.name):
                continue
            try:
                file.unlink()
            except Exception as e:
                logger.warning(f'删除旧 fanart 失败: {file} {e}')
    def downloadIMG(self, metadata: AVMetadata) -> bool:
        prefix = metadata.avid + '-'
        fanart_count = 1
        self._cleanup_existing_fanarts(metadata)
        referer = f'https://missav.ws/cn/{metadata.avid.lower()}' if metadata.source == 'missav' else f'https://jable.tv/videos/{metadata.avid.lower()}/'
        remaining_fanarts = list(metadata.fanarts or [])

        cover_targets = []
        if metadata.cover:
            cover_targets.append(metadata.cover)
        if remaining_fanarts:
            cover_targets.append(remaining_fanarts[0])

        cover_downloaded = False
        for index, image_url in enumerate(cover_targets):
            if not image_url:
                continue
            if self._download_file(image_url, metadata.avid + '/' + prefix + f'fanart-{fanart_count}.jpg', referer=referer):
                self._crop_img(metadata.avid + '/' + prefix + f'fanart-{fanart_count}.jpg', metadata.avid + '/' + prefix + 'poster.jpg')
                cover_downloaded = True
                if index > 0 and remaining_fanarts:
                    remaining_fanarts = remaining_fanarts[1:]
                    logger.warning(f'封面下载失败，已使用首张样品图兜底: {metadata.avid}')
                break

        if not cover_downloaded:
            logger.error(f"封面下载失败：{metadata.cover}")
            return False

        if metadata.source == 'jable' and metadata.sprite_vtt and metadata.sprite_image and not remaining_fanarts:
            extracted = self._download_jable_sprite_fanarts(metadata)
            logger.info(f'Jable 缩略图切出 fanart: {extracted}')
        else:
            for fanart in remaining_fanarts:
                fanart_count += 1
                self._download_file(fanart, metadata.avid + '/' + prefix + f'fanart-{fanart_count}.jpg', referer=referer)

        thumb_dir = os.path.join(self.path, 'thumb')
        os.makedirs(thumb_dir, exist_ok=True)
        for av, url in metadata.actress.items():
            if not url:
                continue
            if os.path.exists(os.path.join(thumb_dir, av + '.jpg')):
                logger.info(f"av {av} already exist")
                continue
            self._download_file(url, os.path.join('thumb', av + '.jpg'), referer=referer)
        return True

    def _download_jable_sprite_fanarts(self, metadata: AVMetadata, limit: int = 20) -> int:
        try:
            vtt_text = self._fetch_text(metadata.sprite_vtt, referer=f'https://jable.tv/videos/{metadata.avid.lower()}/')
            if not vtt_text:
                return 0

            coords = re.findall(r'thumb\.ts#xywh=(\d+),(\d+),(\d+),(\d+)', vtt_text)
            if not coords:
                return 0

            sprite_bytes = self._fetch_bytes(metadata.sprite_image, referer=f'https://jable.tv/videos/{metadata.avid.lower()}/')
            if not sprite_bytes:
                return 0

            sprite = Image.open(BytesIO(sprite_bytes)).convert('RGB')
            unique_coords = []
            seen = set()
            for coord in coords:
                key = tuple(int(v) for v in coord)
                if key in seen:
                    continue
                seen.add(key)
                unique_coords.append(key)

            output_count = 1
            prefix = metadata.avid + '-'
            for x, y, w, h in unique_coords[:limit]:
                output_count += 1
                cropped = sprite.crop((x, y, x + w, y + h))
                output_path = os.path.join(self.path, metadata.avid, prefix + f'fanart-{output_count}.jpg')
                cropped.save(output_path, quality=92)

            return max(0, output_count - 1)
        except Exception as e:
            logger.error(f'Jable 缩略图切图失败: {e}')
            return 0

    def genNFO(self, metadata: AVMetadata) -> bool:
        prefix = metadata.avid + '-'
        root = ET.Element('movie')
        ET.SubElement(root, 'title').text = metadata.title
        ET.SubElement(root, 'plot').text = metadata.description
        ET.SubElement(root, 'outline').text = metadata.description[:100] + ('...' if len(metadata.description) > 100 else '')

        try:
            release_date = datetime.strptime(metadata.release_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            ET.SubElement(root, 'premiered').text = release_date
            ET.SubElement(root, 'releasedate').text = release_date
        except ValueError:
            pass

        if '分鐘' in metadata.duration:
            mins = metadata.duration.replace('分鐘', '').strip()
            ET.SubElement(root, 'runtime').text = mins

        art = ET.SubElement(root, 'art')
        if metadata.cover:
            ET.SubElement(art, 'poster').text = prefix + 'poster.jpg'

        fanart_files = sorted(
            [file.name for file in Path(self.path, metadata.avid).glob(prefix + 'fanart-*.jpg')],
            key=lambda name: int(re.search(r'fanart-(\d+)\.jpg$', name).group(1)) if re.search(r'fanart-(\d+)\.jpg$', name) else 9999
        )
        for fanart_name in fanart_files:
            ET.SubElement(art, 'fanart').text = fanart_name

        for name in metadata.actress.keys():
            actor = ET.SubElement(root, 'actor')
            ET.SubElement(actor, 'name').text = name
            thumb_path = f'thumb/{name}.jpg'
            if os.path.exists(os.path.join(self.path, thumb_path)):
                ET.SubElement(actor, 'thumb').text = thumb_path

        for genre in metadata.keywords[:8]:
            ET.SubElement(root, 'genre').text = genre

        xml_str = ET.tostring(root, encoding='utf-8')
        dom = minidom.parseString(xml_str)
        with open(os.path.join(self.path, metadata.avid, metadata.avid + '.nfo'), 'w', encoding='utf-8') as f:
            dom.writexml(f, indent='  ', addindent='  ', newl='\n', encoding='utf-8')
        return True

    def _download_file(self, url: str, filename: str, referer: str = '') -> bool:
        target_path = os.path.join(self.path, filename)
        logger.debug(f'download {url} to {target_path}')
        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            new_header = headers.copy()
            if referer:
                new_header['Referer'] = referer
            response = requests.get(
                url,
                stream=True,
                impersonate='chrome110',
                proxies=self.proxies,
                headers=new_header,
                timeout=self.timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            logger.error(f'下载失败: {e}')
            return False

    def _fetch_text(self, url: str, referer: str = '') -> str:
        try:
            new_header = headers.copy()
            if referer:
                new_header['Referer'] = referer
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=new_header,
                timeout=self.timeout,
                impersonate='chrome110',
                allow_redirects=True
            )
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f'文本请求失败: {e}')
            return ''

    def _fetch_bytes(self, url: str, referer: str = '') -> bytes:
        try:
            new_header = headers.copy()
            if referer:
                new_header['Referer'] = referer
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=new_header,
                timeout=self.timeout,
                impersonate='chrome110',
                allow_redirects=True
            )
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f'二进制请求失败: {e}')
            return b''

    def _fetch_html(self, url: str, referer: str = '') -> Optional[str]:
        try:
            new_header = headers.copy()
            if referer:
                new_header['Referer'] = referer
            response = requests.get(
                url,
                proxies=self.proxies,
                headers=new_header,
                timeout=self.timeout,
                impersonate='chrome110',
                allow_redirects=False
            )
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f'请求失败: {str(e)}')
            return None

    def _crop_img(self, srcname, optname):
        img = Image.open(os.path.join(self.path, srcname))
        width, height = img.size
        if height > width:
            return
        target_width = int(height * 565 / 800)
        left = width - target_width
        right = width
        top = 0
        bottom = height
        cropped_img = img.crop((left, top, right, bottom))
        cropped_img.save(os.path.join(self.path, optname))
        logger.debug(f'裁剪完成，尺寸: {cropped_img.size}')









