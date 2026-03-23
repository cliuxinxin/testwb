# src/nodes/eval_node.py
from src.db import save_alpha, save_attempt
from src.state import AlphaState
from src.logger import logger


NEAR_MISS_SHARPE_THRESHOLD = 0.8


def persist_near_miss(state: AlphaState, res: dict) -> None:
    expression = state.get("expression")
    idea = state.get("idea")
    sharpe = res.get("sharpe", 0.0)

    if not expression or not idea or sharpe < NEAR_MISS_SHARPE_THRESHOLD:
        return

    save_alpha(
        expression=expression,
        idea=idea,
        sharpe=sharpe,
        turnover=res.get("turnover", 0.0),
        fitness=res.get("fitness", 0.0),
        status="near_miss",
    )


def evaluate_results(state: AlphaState) -> dict:
    logger.info("⚖️ [Node: Evaluator] 正在根据 WQ 官方反馈评估结果...")
    iteration = state.get("iteration_count", 0) + 1
    
    # 1. 致命错误：代码根本没跑通
    if state.get("status") == "error":
        real_error = state.get('error_msg', '未知错误')
        feedback_msg = f"平台直接拒绝了代码！报错内容：【{real_error}】。请仔细阅读，如果是 operator unknown，说明没权限使用该算子，请用其他公式替代！"
        next_status = "error"
        next_repeat_error_count = state.get("repeat_error_count", 0)
        if state.get("feedback") and real_error and real_error in state.get("feedback", ""):
            next_repeat_error_count += 1
        else:
            next_repeat_error_count = 1
        if next_repeat_error_count >= 2:
            feedback_msg += " 同类错误已经连续重复出现，请放弃当前公式，改用新的因子思路。"
            next_status = "need_new_idea"
        save_attempt(
            stage="evaluation",
            status=next_status,
            idea=state.get("idea", ""),
            expression=state.get("expression", ""),
            sharpe=state.get("simulation_results", {}).get("sharpe", 0.0),
            turnover=state.get("simulation_results", {}).get("turnover", 0.0),
            fitness=state.get("simulation_results", {}).get("fitness", 0.0),
            error_msg=real_error,
            feedback=feedback_msg,
        )
        logger.warning(f"⚖️ 打回原因: {feedback_msg}")
        return {
            "status": next_status,
            "iteration_count": iteration,
            "feedback": feedback_msg,
            "repeat_error_count": next_repeat_error_count,
        }

    # 读取刚才扒下来的数据
    res = state.get("simulation_results", {})
    sharpe = res.get("sharpe", 0.0)
    fail_reasons = res.get("fail_reasons", [])
    
    # 2. 如果没有任何明确的 FAIL 理由
    if not fail_reasons:
        if sharpe >= 1.25:
            logger.info("⚖️ ✅ 官方 0 FAIL！指标全部达标，准备提交！")
            return {
                "status": "passed",
                "iteration_count": iteration,
                "feedback": "表现极佳，完美通过 WQ 官方所有测试！",
                "repeat_error_count": 0,
            }
        else:
            # 🚀 新增逻辑：抓不到 FAIL，但夏普率低于及格线 (比如只有 0.6)
            feedback_msg = f"代码跑通了！但夏普率(Sharpe)仅为 {sharpe}，远低于平台及格线 1.25。虽然没有严重报错，但因子表现太平庸。请从根本上优化逻辑，比如更换信号源或加入更多的交叉因子！"
            persist_near_miss(state, res)
            save_attempt(
                stage="evaluation",
                status="failed",
                idea=state.get("idea", ""),
                expression=state.get("expression", ""),
                sharpe=res.get("sharpe", 0.0),
                turnover=res.get("turnover", 0.0),
                fitness=res.get("fitness", 0.0),
                feedback=feedback_msg,
            )
            logger.info(f"⚖️ 🔄 官方未报错，但夏普太低 ({sharpe})，打回重做。")
            return {
                "status": "failed",
                "iteration_count": iteration,
                "feedback": feedback_msg,
                "repeat_error_count": 0,
            }

    # 3. 官方拒签：抓取到了具体的 FAIL 理由
    feedback_parts =[
        f"回测完成，当前夏普率: {sharpe}。但未通过 WQ 官方测试！以下是官方的【FAIL 拒签理由】(请仔细阅读)：",
        *["- " + reason for reason in fail_reasons],
        "\n【量化专家修改建议】:"
    ]
    
    # 针对官方的不同报错，给 AI 补充具体的修改方向
    added_advice = False
    for reason in fail_reasons:
        if "Sharpe" in reason and "below cutoff" in reason:
            feedback_parts.append("👉 夏普率太低: 尝试增加横向截面 rank() 操作，或者结合不同逻辑的数据。")
            added_advice = True
        elif "Turnover" in reason and "above cutoff" in reason:
            feedback_parts.append("👉 换手率超标: 请务必在表达式最外层使用 ts_mean(..., 5) 或者 ts_rank 进行平滑，降低交易频率！")
            added_advice = True
        elif "Fitness" in reason:
            feedback_parts.append("👉 Fitness不达标: 因子表现不够稳定，尝试改变计算周期（例如 5 改 20）。")
            added_advice = True
        elif "Invalid number of inputs" in reason:
            feedback_parts.append("👉 参数个数错误: 优先检查可选参数是否必须写成命名参数。典型例子是把 `hump(x, 0.01)` 改成 `hump(x, hump=0.01)`，以及 `bucket(...)` 需要显式写 `range=` 或 `buckets=`。")
            added_advice = True
            
    if not added_advice:
         feedback_parts.append("👉 请根据上述英文报错，重新调整数学表达式。")

    feedback_msg = "\n".join(feedback_parts)
    current_fail_signature = " | ".join(fail_reasons)
    next_status = "failed"
    next_repeat_error_count = state.get("repeat_error_count", 0)
    previous_feedback = state.get("feedback", "")
    if current_fail_signature and current_fail_signature in previous_feedback:
        next_repeat_error_count += 1
    else:
        next_repeat_error_count = 1
    if next_repeat_error_count >= 2:
        next_status = "need_new_idea"
        feedback_msg += "\n👉 同类失败已经连续重复出现，不要继续微调当前表达式，请重新生成一个新的因子思路。"
    
    persist_near_miss(state, res)
    save_attempt(
        stage="evaluation",
        status=next_status,
        idea=state.get("idea", ""),
        expression=state.get("expression", ""),
        sharpe=res.get("sharpe", 0.0),
        turnover=res.get("turnover", 0.0),
        fitness=res.get("fitness", 0.0),
        error_msg=current_fail_signature,
        feedback=feedback_msg,
    )
    logger.info(f"⚖️ 🔄 官方拒签，打回重做。发现 {len(fail_reasons)} 个未达标项。")
    logger.debug(f"传给 Coder 的反馈: \n{feedback_msg}")
    
    return {
        "status": next_status,
        "iteration_count": iteration,
        "feedback": feedback_msg,
        "repeat_error_count": next_repeat_error_count,
    }
