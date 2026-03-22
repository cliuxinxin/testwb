from src.state import AlphaState
from src.logger import logger


def submit_alpha(state: AlphaState) -> dict:
    expression = state.get("expression")
    logger.info(f"🚀 [Node: Submitter] 正在提交达标因子到 WorldQuant Brain...")
    logger.debug(f"Submitter: 尝试点击 Submit 按钮 (Mocking...): {expression}")

    # 这里未来写入保存到本地 SQLite 或 CSV 的逻辑
    logger.info(f"🚀 [Node: Submitter] 🎉 因子提交成功！")
    # 同步返回关键信息，便于前端记录历史
    return {
        "status": "submitted",
        "idea": state.get("idea"),
        "expression": state.get("expression"),
    }
