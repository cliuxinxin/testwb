from typing import TypedDict, Optional, Dict, Any


class AlphaState(TypedDict):
    idea: str  # 因子逻辑思路
    expression: str  # WQ 表达式代码
    simulation_results: Dict[str, Any]  # 回测结果 (Sharpe, Turnover等)
    error_msg: Optional[str]  # WQ 平台报错信息
    iteration_count: int  # 迭代次数
    status: str  # new, simulated, passed, failed, error
    feedback: str  # Evaluator 针对修改给出的建议
