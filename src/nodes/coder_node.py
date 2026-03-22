# src/nodes/coder_node.py
from src.state import AlphaState
from src.llm import get_llm
from src.logger import logger
from src.whitelist import ALLOWED_OPERATORS, ALLOWED_DATASETS

def write_expression(state: AlphaState) -> dict:
    iteration = state.get('iteration_count', 0)
    logger.info(f"💻 [Node: Coder] 正在编写/修复 WQ 表达式 (迭代: {iteration})...")
    
    llm = get_llm(temperature=0.1)
    idea = state.get("idea", "")
    feedback = state.get("feedback", "")
    
    # 动态将列表转为字符串
    ops_str = ", ".join(ALLOWED_OPERATORS)
    data_str = ", ".join(ALLOWED_DATASETS)
    
    prompt = f"""将以下因子逻辑写成 WorldQuant Brain 的单行表达式。
【因子逻辑】: {idea}

【极度严格的约束（违反任何一条直接淘汰）】:
1. 只能使用以下基础数据: {data_str}
2. 只能使用以下算子: {ops_str}
3. 【绝对禁止】使用 Python 的 `and`, `or`, `if` 等关键字！如果需要多条件叠加，请用加减乘除。
4. 【绝对禁止】使用抽象变量名（如 N, M, d）！计算周期必须是具体整数（如 5, 10, 20）。
5. 【绝对禁止】使用科学计数法（如 1e-5），必须直接写完整小数（如 0.00001）。
6. 不要加 Markdown 标记，直接输出一行纯净的代码。
7. 【用法警告】如果使用 group_neutralize，第二个参数必须直接写分类数据（如 sector 或 industry）。正确示范：group_neutralize(rank(close), sector)。绝对禁止用数字1或[]，也绝对禁止写成 group=sector 这种 Python 传参格式！
8. 【量纲一致性铁律】绝对禁止把常数（如 0.00001, 1）直接加减到带有量纲的原始数据（如 close, volume, vwap）上！例如 volume+0.00001 会直接导致 Incompatible unit 报错。"""
    if feedback:
        prompt += f"\n\n【前期测试反馈与报错】: \n{feedback}\n请仔细分析报错原因，严格遵守约束条件，修复此错误！"

    response = llm.invoke(prompt)
    expression = response.content.strip().replace("`", "")
    
    logger.info(f"💻[Node: Coder] 生成表达式: {expression}")
    return {"expression": expression}