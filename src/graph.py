from functools import partial
from typing import Optional

from langgraph.graph import StateGraph, END
from src.config import Settings, get_settings
from src.state import AlphaState
from src.logger import logger
from src.nodes.idea_node import generate_idea
from src.nodes.coder_node import write_expression
from src.nodes.syntax_node import check_syntax     # ⬅️ 1. 导入 Syntax 节点
from src.nodes.sim_node import run_simulation
from src.nodes.eval_node import evaluate_results
from src.nodes.submit_node import submit_alpha

def build_graph(settings: Optional[Settings] = None):
    current_settings = settings or get_settings()
    logger.debug("正在编排 LangGraph 工作流拓扑结构...")
    workflow = StateGraph(AlphaState)

    # 1. 注册节点
    workflow.add_node("idea", partial(generate_idea, settings=current_settings))
    workflow.add_node("coder", partial(write_expression, settings=current_settings))
    workflow.add_node("syntax", check_syntax)      # ⬅️ 2. 注册 Syntax 节点
    workflow.add_node("simulator", run_simulation)
    workflow.add_node("evaluator", evaluate_results)
    workflow.add_node("submitter", submit_alpha)

    # 2. 定义条件路由函数
    def evaluate_router(state: AlphaState) -> str:
        current_iter = state.get("iteration_count", 0)
        status = state.get("status")

        logger.debug(
            f"[Router] 当前状态: {status}, 迭代次数: {current_iter}/{current_settings.max_iterations}"
        )

        if current_iter >= current_settings.max_iterations:
            logger.warning(
                f"[Router] 达到最大迭代次数 {current_settings.max_iterations}，放弃此因子的抢救，流程结束。"
            )
            return "end"

        if status == "need_new_idea":
            return "idea"

        if status in ["error", "failed"]:
            return "coder"  # 回去改代码

        if status == "passed":
            return "submitter"  # 去提交

        return "end"

    # ⬅️ 3. 增加 Syntax 的路由判断
    def syntax_router(state: AlphaState) -> str:
        current_iter = state.get("iteration_count", 0)
        if current_iter >= current_settings.max_iterations:
            logger.warning(
                f"[Router] Syntax 拦截达到最大迭代次数 {current_settings.max_iterations}，流程结束。"
            )
            return "end"

        if state.get("status") == "need_new_idea":
            return "idea"

        if state.get("status") == "syntax_error":
            return "coder"      # 语法错误，打回给 Coder 重新写
        return "simulator"      # 语法通过，去浏览器跑回测

    # 4. 连接边拓扑结构
    workflow.set_entry_point("idea")
    workflow.add_edge("idea", "coder")
    workflow.add_edge("coder", "syntax")    # ⬅️ 4. Coder 生成后先跑 Syntax 节点

    # ⬅️ 5. 根据 Syntax 结果分流
    workflow.add_conditional_edges(
        "syntax",
        syntax_router,
        {"idea": "idea", "coder": "coder", "simulator": "simulator", "end": END},
    )

    workflow.add_edge("simulator", "evaluator")
    
    workflow.add_conditional_edges(
        "evaluator",
        evaluate_router,
        {"idea": "idea", "coder": "coder", "submitter": "submitter", "end": END},
    )
    workflow.add_edge("submitter", END)

    logger.debug("LangGraph 编译完成。")
    return workflow.compile()
