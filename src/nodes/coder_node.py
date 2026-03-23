# src/nodes/coder_node.py
from typing import Optional

from src.config import Settings
from src.state import AlphaState
from src.llm import get_llm
from src.logger import logger
from src.db import format_history_snapshot, get_history_snapshot
from src.whitelist import (
    ALLOWED_COMPARATORS,
    ALLOWED_DATASETS,
    ALLOWED_GROUPS,
    ALLOWED_OPERATORS,
    CODER_METHOD_RULES_TEXT,
    OPERATOR_MANUAL_TEXT,
)


def write_expression(state: AlphaState, settings: Optional[Settings] = None) -> dict:
    iteration = state.get('iteration_count', 0)
    logger.info(f"💻 [Node: Coder] 正在编写/修复 WQ 表达式 (迭代: {iteration})...")
    
    llm = get_llm(temperature=0.1, settings=settings)
    idea = state.get("idea", "")
    feedback = state.get("feedback", "")
    history_text = format_history_snapshot(get_history_snapshot())
    attempted_expressions = state.get("attempted_expressions", [])
    
    ops_str = ", ".join(ALLOWED_OPERATORS)
    data_str = ", ".join(ALLOWED_DATASETS)
    groups_str = ", ".join(ALLOWED_GROUPS)
    comparators_str = " ".join(ALLOWED_COMPARATORS)
    attempted_expression_text = " || ".join(attempted_expressions[-5:]) if attempted_expressions else "无"
    
    prompt = f"""将以下因子逻辑写成 WorldQuant Brain 的单行表达式。
【因子逻辑】: {idea}

【允许的基础数据】: {data_str}
【允许的分组字段】: {groups_str}
【允许的比较运算符】: {comparators_str}
【允许的算子】: {ops_str}

【历史经验与失败记录】:
{history_text}

【本轮已经尝试过的表达式（绝对禁止重复）】:
{attempted_expression_text}

【算子签名与使用手册】:
{OPERATOR_MANUAL_TEXT}

【强制写作规则】:
{CODER_METHOD_RULES_TEXT}

【最后输出要求】:
1. 只输出一行纯净表达式。
2. 不要输出解释、不要输出 Markdown、不要输出多行。
3. 在输出前先自行检查每个算子的参数个数、参数顺序、group 参数和命名参数是否符合手册。
4. 如果历史里有高频错误或最近失败样本，优先规避这些错误，不要重复犯错。
5. 输出必须与本轮已尝试表达式结构明显不同，不能只改一个参数或换一个 group 字段后原样重写。
"""
    if feedback:
        prompt += f"\n\n【前期测试反馈与报错】: \n{feedback}\n请仔细分析报错原因，严格遵守约束条件，修复此错误！"

    response = llm.invoke(prompt)
    expression = str(response.content).strip().replace("`", "")
    
    logger.info(f"💻[Node: Coder] 生成表达式: {expression}")
    return {"expression": expression}
