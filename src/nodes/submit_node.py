from src.db import save_alpha, save_attempt
from src.state import AlphaState
from src.logger import logger


def submit_alpha(state: AlphaState) -> dict:
    expression = state.get("expression")
    idea = state.get("idea")
    metrics = state.get("simulation_results", {})

    if expression and idea:
        save_alpha(
            expression=expression,
            idea=idea,
            sharpe=metrics.get("sharpe", 0.0),
            turnover=metrics.get("turnover", 0.0),
            fitness=metrics.get("fitness", 0.0),
            status="passed",
        )
        save_attempt(
            stage="submit",
            status="passed",
            idea=idea,
            expression=expression,
            sharpe=metrics.get("sharpe", 0.0),
            turnover=metrics.get("turnover", 0.0),
            fitness=metrics.get("fitness", 0.0),
            feedback="达标因子已保存到本地基因库。",
        )

    logger.info("🚀 [Node: Submitter] 已将达标因子归档到本地基因库。")
    return {
        "status": "stored",
        "feedback": "达标因子已保存到本地基因库；真实平台提交流程尚未实现。",
        "idea": idea,
        "expression": expression,
    }
