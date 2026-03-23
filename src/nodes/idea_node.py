from typing import Optional

from src.config import Settings
from src.state import AlphaState
from src.llm import get_llm
from src.logger import logger
from src.db import format_history_snapshot, get_history_snapshot
from src.whitelist import (
    ALLOWED_DATASETS,
    ALLOWED_GROUPS,
    IDEA_METHOD_RULES_TEXT,
    OPERATOR_CATEGORY_TEXT,
)


def generate_idea(state: AlphaState, settings: Optional[Settings] = None) -> dict:
    logger.info("💡 [Node: Idea] 正在生成因子灵感...")
    llm = get_llm(temperature=0.8, settings=settings)  # 灵感阶段温度稍高
    datasets_text = ", ".join(ALLOWED_DATASETS)
    groups_text = ", ".join(ALLOWED_GROUPS)
    history_snapshot = get_history_snapshot()
    history_text = format_history_snapshot(history_snapshot)
    has_history = any(history_snapshot.values())
    attempted_ideas = state.get("attempted_ideas", [])
    attempted_expressions = state.get("attempted_expressions", [])

    recent_attempt_block = ""
    if attempted_ideas or attempted_expressions:
        recent_attempt_block = (
            "\n【本轮已经尝试过的内容（不要重复）】:\n"
            f"- 已尝试思路: {' || '.join(attempted_ideas[-3:]) if attempted_ideas else '无'}\n"
            f"- 已尝试表达式: {' || '.join(attempted_expressions[-3:]) if attempted_expressions else '无'}\n"
        )

    if has_history:
        logger.info("🧠 已加载历史结果和失败反馈，用于驱动新想法生成...")
        prompt = f"""
你是一个顶级量化研究员。你这次不是从零开始，而是必须基于历史结果、失败反馈和已有样本来提出新的思路。

【允许的基础数据】: {datasets_text}
【允许的分组字段】: {groups_text}
【允许的算子分类】:
{OPERATOR_CATEGORY_TEXT}

【历史经验】:
{history_text}
{recent_attempt_block}

【构思约束】:
{IDEA_METHOD_RULES_TEXT}

请输出一个全新的中文因子思路，限制在120字以内，并同时满足：
1. 明确点出核心数据来源。
2. 明确点出至少一个时间序列处理或横截面/分组处理。
3. 需要显式说明是在复用什么成功经验，或者在规避什么历史失败模式。
4. 如果历史里反复出现某类错误，这次要主动绕开。
5. 如果逻辑容易高换手，要在思路里说明会怎样控换手。
6. 不要直接输出公式，不要输出 Markdown。
7. 不允许复用本轮已经尝试过的思路或仅做同义改写。
        """
    else:
        prompt = f"""
你是一个顶级量化研究员。请构思一个新的量化因子逻辑，例如价量背离、均值回归、波动收敛、趋势反转。

【允许的基础数据】: {datasets_text}
【允许的分组字段】: {groups_text}
【允许的算子分类】:
{OPERATOR_CATEGORY_TEXT}
{recent_attempt_block}

【构思约束】:
{IDEA_METHOD_RULES_TEXT}

请输出一个中文因子思路，限制在120字以内，并同时满足：
1. 明确点出核心数据来源。
2. 明确点出至少一个时间序列处理或横截面/分组处理。
3. 如果逻辑容易高换手，要在思路里说明会怎样控换手。
4. 不要直接输出公式，不要输出 Markdown。
5. 不允许复用本轮已经尝试过的思路或仅做同义改写。
"""
    response = llm.invoke(prompt)
    content = getattr(response, "content", "")
    if isinstance(content, str):
        idea = content.strip()
    elif isinstance(content, list):
        idea = " ".join([str(p) for p in content]).strip()
    else:
        idea = str(content).strip()
    logger.debug(f"生成的灵感: {idea}")
    updated_attempted_ideas = attempted_ideas + [idea]
    return {
        "idea": idea,
        "attempted_ideas": updated_attempted_ideas[-5:],
        "repeat_error_count": 0,
        "status": "new",
        "error_msg": None,
        "feedback": "",
    }
