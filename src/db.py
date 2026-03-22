import sqlite3
import os
from src.logger import logger

DB_PATH = "alphas.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # 创建基因库表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alpha_memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expression TEXT UNIQUE,
            idea TEXT,
            sharpe REAL,
            turnover REAL,
            fitness REAL,
            status TEXT,       -- 'passed' 或 'near_miss'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.debug("本地 SQLite 基因库初始化完成。")


def save_alpha(expression, idea, sharpe, turnover, fitness, status):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR IGNORE INTO alpha_memory (expression, idea, sharpe, turnover, fitness, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (expression, idea, sharpe, turnover, fitness, status),
        )
        conn.commit()
        conn.close()
        logger.debug(f"成功将因子存入基因库: {expression} | 状态: {status}")
    except Exception as e:
        logger.error(f"存入数据库失败: {e}")


def get_random_near_miss():
    """随机获取一个表现尚可的因子用于变异"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT expression, idea, sharpe FROM alpha_memory WHERE status='near_miss' ORDER BY RANDOM() LIMIT 1"
    )
    row = cursor.fetchone()
    conn.close()
    if row:
        return {"expression": row[0], "idea": row[1], "sharpe": row[2]}
    return None


# 初始化调用
init_db()
