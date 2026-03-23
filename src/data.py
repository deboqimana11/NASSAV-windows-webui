import sqlite3
from typing import List
from .comm import *


def initialize_db(db_path: str, table_name: str):
    logger.debug(f"db_path: {db_path}, table_name: {table_name}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        bvid TEXT PRIMARY KEY
    )
    ''')
    conn.commit()
    conn.close()


def batch_insert_bvids(bvid_list: list[str], db_path: str, table_name: str):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        cursor.executemany(
            f'INSERT OR IGNORE INTO {table_name} (bvid) VALUES (?)',
            [(bvid,) for bvid in bvid_list]
        )
        conn.commit()
        logger.info(f"成功插入 {cursor.rowcount}")
    except sqlite3.Error as e:
        logger.error(f"插入BVID时出错: {e}")
        conn.rollback()
    finally:
        conn.close()


def find_in_db(bvid: str, db_path: str, table_name: str) -> bool:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT 1 FROM {table_name} WHERE bvid = ? LIMIT 1"
        cursor.execute(query, (bvid,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result is not None
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
        return False
    except Exception as e:
        print(f"发生错误: {e}")
        return False


def delete_from_db(bvid: str, db_path: str, table_name: str) -> bool:
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table_name} WHERE bvid = ?', (bvid,))
        conn.commit()
        deleted = cursor.rowcount > 0
        cursor.close()
        conn.close()
        if deleted:
            logger.warning(f"已删除脏数据库记录: {bvid}")
        return deleted
    except sqlite3.Error as e:
        logger.error(f"删除BVID时出错: {e}")
        return False
