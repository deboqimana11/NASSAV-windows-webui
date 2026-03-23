from src.comm import *
from src import data
from src.scraper import Sracper, AVMetadata
import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont


def ensure_video_folder(avid: str) -> Path:
    folder = Path(save_path) / avid
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def read_local_nfo(avid: str) -> tuple[str, str]:
    nfo_path = Path(save_path) / avid / f'{avid}.nfo'
    if not nfo_path.exists():
        return avid, ''

    try:
        root = ET.parse(nfo_path).getroot()
        title = (root.findtext('title') or avid).strip()
        release_date = (root.findtext('releasedate') or root.findtext('premiered') or '').strip()
        return title or avid, release_date
    except Exception as exc:
        logger.error(f'读取本地NFO失败: {exc}')
        return avid, ''


def create_placeholder_poster(avid: str, title: str) -> None:
    video_dir = Path(save_path) / avid
    poster_path = video_dir / f'{avid}-poster.jpg'
    fanart_path = video_dir / f'{avid}-fanart-1.jpg'
    if poster_path.exists() and fanart_path.exists():
        return

    image = Image.new('RGB', (800, 1200), '#f3d5da')
    draw = ImageDraw.Draw(image)
    try:
        title_font = ImageFont.truetype('arial.ttf', 42)
        sub_font = ImageFont.truetype('arial.ttf', 24)
    except Exception:
        title_font = ImageFont.load_default()
        sub_font = ImageFont.load_default()

    draw.rounded_rectangle((48, 72, 752, 1128), radius=36, fill='#fff7f8', outline='#d78695', width=4)
    draw.text((90, 150), avid, fill='#8a2037', font=title_font)

    wrapped = []
    text = title.strip() or avid
    chunk = ''
    for char in text:
        trial = chunk + char
        if len(trial) >= 18:
            wrapped.append(trial)
            chunk = ''
        else:
            chunk = trial
    if chunk:
        wrapped.append(chunk)
    wrapped = wrapped[:8]

    y = 270
    for line in wrapped:
        draw.text((90, y), line, fill='#4b2730', font=sub_font)
        y += 48

    draw.text((90, 1040), 'LOCAL LIBRARY RECOVERED ITEM', fill='#b8606d', font=sub_font)
    image.save(fanart_path, quality=92)

    poster = image.crop((270, 72, 752, 1128))
    poster.save(poster_path, quality=92)


def write_fallback_metadata(avid: str) -> None:
    title, release_date = read_local_nfo(avid)
    metadata = AVMetadata(
        title=title,
        avid=avid,
        description=title,
        release_date=release_date,
        source='local-recovery',
        fanarts=[f'{avid}-fanart-1.jpg']
    )
    metadata.to_json(Path(save_path) / avid / 'metadata.json')
    create_placeholder_poster(avid, title)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        logger.error('需要提供车牌号')
        sys.exit(1)

    avid = sys.argv[1].strip().upper()
    if not avid:
        logger.error('车牌号为空')
        sys.exit(1)

    ensure_video_folder(avid)
    data.initialize_db(downloaded_path, 'MissAV')
    data.batch_insert_bvids([avid], downloaded_path, 'MissAV')

    scraper = Sracper(save_path, myproxy)
    result = scraper.scrape(avid)
    if result:
        logger.info(f'{avid} 补全元数据成功')
        sys.exit(0)

    logger.warning(f'{avid} 远程补全失败，改用本地兜底元数据')
    write_fallback_metadata(avid)
    logger.info(f'{avid} 已生成本地兜底元数据')
