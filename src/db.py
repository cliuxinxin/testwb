import sqlite3
from typing import Any, Dict, List

from src.logger import logger

DB_PATH = "alphas.db"


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        cursor = conn.cursor()
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alpha_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage TEXT,
                status TEXT,
                idea TEXT,
                expression TEXT,
                sharpe REAL,
                turnover REAL,
                fitness REAL,
                error_msg TEXT,
                feedback TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    logger.debug("本地 SQLite 基因库初始化完成。")


def save_alpha(expression, idea, sharpe, turnover, fitness, status):
    try:
        with _connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alpha_memory (expression, idea, sharpe, turnover, fitness, status)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(expression) DO UPDATE SET
                    idea = excluded.idea,
                    sharpe = CASE
                        WHEN alpha_memory.status = 'passed' AND excluded.status != 'passed'
                        THEN alpha_memory.sharpe
                        ELSE excluded.sharpe
                    END,
                    turnover = CASE
                        WHEN alpha_memory.status = 'passed' AND excluded.status != 'passed'
                        THEN alpha_memory.turnover
                        ELSE excluded.turnover
                    END,
                    fitness = CASE
                        WHEN alpha_memory.status = 'passed' AND excluded.status != 'passed'
                        THEN alpha_memory.fitness
                        ELSE excluded.fitness
                    END,
                    status = CASE
                        WHEN alpha_memory.status = 'passed' AND excluded.status != 'passed'
                        THEN alpha_memory.status
                        ELSE excluded.status
                    END
            """,
                (expression, idea, sharpe, turnover, fitness, status),
            )
        logger.debug(f"成功将因子存入基因库: {expression} | 状态: {status}")
    except Exception as e:
        logger.error(f"存入数据库失败: {e}")


def save_attempt(
    stage: str,
    status: str,
    idea: str = "",
    expression: str = "",
    sharpe: float = 0.0,
    turnover: float = 0.0,
    fitness: float = 0.0,
    error_msg: str = "",
    feedback: str = "",
) -> None:
    try:
        with _connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO alpha_attempts (
                    stage, status, idea, expression, sharpe, turnover, fitness, error_msg, feedback
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stage,
                    status,
                    idea,
                    expression,
                    sharpe,
                    turnover,
                    fitness,
                    error_msg,
                    feedback,
                ),
            )
        logger.debug(f"成功记录历史尝试: stage={stage}, status={status}")
    except Exception as e:
        logger.error(f"记录历史尝试失败: {e}")


def _rows_to_dicts(rows: List[sqlite3.Row]) -> List[Dict[str, Any]]:
    return [dict(row) for row in rows]


def _shorten(text: str, limit: int = 160) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def get_history_snapshot(
    top_passed_limit: int = 2,
    near_miss_limit: int = 3,
    recent_attempt_limit: int = 5,
    recurring_issue_limit: int = 3,
) -> Dict[str, List[Dict[str, Any]]]:
    with _connect() as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT idea, expression, sharpe, turnover, fitness, status, created_at
            FROM alpha_memory
            WHERE status = 'passed'
            ORDER BY sharpe DESC, id DESC
            LIMIT ?
            """,
            (top_passed_limit,),
        )
        top_passed = _rows_to_dicts(cursor.fetchall())

        cursor.execute(
            """
            SELECT idea, expression, sharpe, turnover, fitness, status, created_at
            FROM alpha_memory
            WHERE status = 'near_miss'
            ORDER BY sharpe DESC, id DESC
            LIMIT ?
            """,
            (near_miss_limit,),
        )
        near_misses = _rows_to_dicts(cursor.fetchall())

        cursor.execute(
            """
            SELECT stage, status, idea, expression, sharpe, turnover, fitness, error_msg, feedback, created_at
            FROM alpha_attempts
            ORDER BY id DESC
            LIMIT ?
            """,
            (recent_attempt_limit,),
        )
        recent_attempts = _rows_to_dicts(cursor.fetchall())

        cursor.execute(
            """
            SELECT issue, count(*) AS hit_count, max(created_at) AS last_seen
            FROM (
                SELECT trim(COALESCE(NULLIF(error_msg, ''), NULLIF(feedback, ''))) AS issue, created_at
                FROM alpha_attempts
                WHERE status IN ('syntax_error', 'error', 'failed')
            )
            WHERE issue IS NOT NULL AND issue != ''
            GROUP BY issue
            ORDER BY hit_count DESC, last_seen DESC
            LIMIT ?
            """,
            (recurring_issue_limit,),
        )
        recurring_issues = _rows_to_dicts(cursor.fetchall())

    return {
        "top_passed": top_passed,
        "near_misses": near_misses,
        "recent_attempts": recent_attempts,
        "recurring_issues": recurring_issues,
    }


def format_history_snapshot(snapshot: Dict[str, List[Dict[str, Any]]]) -> str:
    sections = []

    top_passed = snapshot.get("top_passed", [])
    if top_passed:
        lines = ["历史成功样本:"]
        for item in top_passed:
            lines.append(
                f"- passed | Sharpe={item.get('sharpe', 0):.4f} | Idea={_shorten(item.get('idea', ''))} | Expr={_shorten(item.get('expression', ''))}"
            )
        sections.append("\n".join(lines))

    near_misses = snapshot.get("near_misses", [])
    if near_misses:
        lines = ["历史接近通过样本:"]
        for item in near_misses:
            lines.append(
                f"- near_miss | Sharpe={item.get('sharpe', 0):.4f} | Idea={_shorten(item.get('idea', ''))} | Expr={_shorten(item.get('expression', ''))}"
            )
        sections.append("\n".join(lines))

    recurring_issues = snapshot.get("recurring_issues", [])
    if recurring_issues:
        lines = ["高频失败模式:"]
        for item in recurring_issues:
            lines.append(
                f"- {item.get('hit_count', 0)} 次: {_shorten(item.get('issue', ''), 220)}"
            )
        sections.append("\n".join(lines))

    recent_attempts = snapshot.get("recent_attempts", [])
    if recent_attempts:
        lines = ["最近尝试与反馈:"]
        for item in recent_attempts:
            issue = item.get("error_msg") or item.get("feedback") or ""
            lines.append(
                f"- [{item.get('stage', '')}/{item.get('status', '')}] Idea={_shorten(item.get('idea', ''), 80)} | Expr={_shorten(item.get('expression', ''), 100)} | Sharpe={item.get('sharpe', 0):.4f} | Note={_shorten(issue, 180)}"
            )
        sections.append("\n".join(lines))

    if not sections:
        return "暂无历史结果、失败反馈或可复用样本。"

    return "\n\n".join(sections)


# 初始化调用
init_db()
