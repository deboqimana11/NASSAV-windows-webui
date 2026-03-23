from src import downloaderMgr
from src.comm import *
from src import data
import sys
import os
import subprocess
import argparse
from pathlib import Path
from metadata import *


def append_if_not_duplicate(filename, new_content):
    new_content = new_content.strip()
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            existing_lines = [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        existing_lines = []

    if new_content not in existing_lines:
        with open(filename, 'a', encoding='utf-8') as file:
            file.write(new_content + '\n')
        return True
    return False


def has_pending_queue_items(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return any(line.strip() for line in file.readlines())
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('target', nargs='?', help='指定车牌号')
    parser.add_argument('-f', '--force', action='store_true', help='跳过DB检查，强制执行')
    args = parser.parse_args()

    if args.target is None:
        logger.error("需要提供车牌号")
        sys.exit(1)

    logger.info(f"Force: {args.force}")
    logger.info(f"Target: {args.target}")

    data.initialize_db(downloaded_path, "MissAV")

    avid = args.target.upper()
    work_path = str((project_root / 'work').resolve())
    Path(work_path).touch(exist_ok=True)

    if not args.force and data.find_in_db(avid, downloaded_path, "MissAV"):
        video_dir = Path(save_path) / avid
        has_local_artifacts = (video_dir / f"{avid}.mp4").exists() or (video_dir / f"{avid}.nfo").exists()
        if has_local_artifacts:
            logger.info(f"{avid} 已在小姐姐数据库中，且本地文件存在")
            sys.exit(0)
        data.delete_from_db(avid, downloaded_path, "MissAV")
        logger.warning(f"{avid} 数据库中存在，但本地文件缺失，已清理脏记录并继续重新下载")

    logger.info(f"开始执行 车牌号: {avid}")

    with open(work_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()
    if content and content != "0":
        logger.info(f"A download task is running, save {avid} to download queue")
        with open(queue_path, 'a', encoding='utf-8') as f:
            f.write(f'{avid}\n')
        sys.exit(0)

    with open(work_path, 'w', encoding='utf-8') as f:
        f.write(avid)

    mgr = downloaderMgr.DownloaderMgr()
    try:
        if len(sorted_downloaders) == 0:
            raise ValueError(f"cfg没有配置下载器：{sorted_downloaders}")

        count = 0
        for it in sorted_downloaders:
            count += 1
            downloader = mgr.GetDownloader(it["downloaderName"])
            if downloader is None:
                logger.error(f"下载器 {it['downloaderName']} 没有找到")
                if count >= len(sorted_downloaders):
                    raise ValueError(f"下载器 {it['downloaderName']} 没有找到")
                continue
            if not downloader.setDomain(it["domain"]):
                logger.error(f"下载器 {downloader.getDownloaderName()} 的域名没有配置")
                continue
            logger.info(f"尝试使用Downloader: {downloader.getDownloaderName()} 下载")

            info = downloader.downloadInfo(avid)
            if not info:
                logger.error(f"{avid} 下载元数据失败")
                if count >= len(sorted_downloaders):
                    raise ValueError(f"{avid} 下载元数据失败")
                continue
            logger.info(info)
            if not downloader.downloadM3u8(info.m3u8, avid):
                logger.error(f"{info.m3u8} 下载视频失败")
                if count >= len(sorted_downloaders):
                    raise ValueError(f"{info.m3u8} 下载视频失败")
                continue
            break

        gen_nfo()

    except ValueError as e:
        logger.error(e)
        if append_if_not_duplicate(queue_path, avid):
            logger.info(f"'{avid}' 已成功添加到下载队列。")
        else:
            logger.info(f"'{avid}' 已存在下载队列中。")

    finally:
        with open(work_path, 'w', encoding='utf-8') as f:
            f.write("0")

        if os.getenv('NASSAV_QUEUE_RUNNER') != '1' and has_pending_queue_items(queue_path):
            logger.info("检测到待处理队列，开始自动执行下一项")
            subprocess.Popen([sys.executable, 'queue_runner.py'], cwd=project_root)



