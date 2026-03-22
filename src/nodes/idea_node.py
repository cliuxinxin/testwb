from src.state import AlphaState
from src.llm import get_llm
from src.logger import logger
from src.db import get_random_near_miss


def generate_idea(state: AlphaState) -> dict:
    logger.info("💡 [Node: Idea] 正在生成因子灵感...")
    llm = get_llm(temperature=0.8)  # 灵感阶段温度稍高
    # 尝试从基因库中提取优秀基因进行变异；若无则新生成
    near_miss = get_random_near_miss()
    if near_miss:
        logger.info(
            f"🧬 发现优秀历史基因 (Sharpe: {near_miss['sharpe']})，开始进行交叉变异..."
        )
        prompt = f"""
        你是一个顶级量化研究员。请对以下未及格但有潜力的因子逻辑进行【变异】或【进化】。
        【原逻辑】: {near_miss["idea"]}
        【原表达式】: {near_miss["expression"]}
        请输出全新的变异思路，说明为什么新思路能提高夏普率。限制在100字以内。
        """
    else:
        prompt = """你是一个顶级量化研究员。请构思一个新的量化因子逻辑，例如基于价量背离、均值回归。限制在100字以内。"""
    response = llm.invoke(prompt)
    content = getattr(response, "content", "")
    if isinstance(content, str):
        idea = content.strip()
    elif isinstance(content, list):
        idea = " ".join([str(p) for p in content]).strip()
    else:
        idea = str(content).strip()
    logger.debug(f"生成的灵感: {idea}")
    return {
        "idea": idea,
        "iteration_count": 0,
        "status": "new",
        "error_msg": None,
        "feedback": "",
    }
