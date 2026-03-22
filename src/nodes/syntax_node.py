# src/nodes/syntax_node.py
import re
from src.state import AlphaState
from src.logger import logger
from src.whitelist import WQ_WHITELIST

def check_syntax(state: AlphaState) -> dict:
    expression = state.get("expression", "")
    iteration = state.get("iteration_count", 0)
    logger.info(f"🔎 [Node: Syntax] 本地静态查错中...")
    error_msgs = []

    if '[' in expression or ']' in expression or '{' in expression or '}' in expression:
        error_msgs.append("绝对禁止使用中括号 [] 或大括号 {}，WQ 表达式仅支持小括号 ()。")
    
    if expression.count('(') != expression.count(')'):
        error_msgs.append("括号不匹配 (Unbalanced parentheses)。")
        
    if re.search(r'\d[eE][+-]?\d', expression):
        error_msgs.append("绝对禁止使用科学计数法 (如 1e-5)，请使用完整小数。")
        
    if re.search(r'\b(and|or|if|else)\b', expression, re.IGNORECASE):
        error_msgs.append("绝对禁止使用 'and', 'or', 'if' 等Python关键字。")
        
    if re.search(r',\s*[A-Za-z]\s*\)', expression):
        error_msgs.append("周期参数不能是抽象字母（如 N, M），必须是具体整数。")

    words = re.findall(r'[a-zA-Z_]\w*', expression)
    invalid_words = [w for w in words if w.lower() not in WQ_WHITELIST]
    if invalid_words:
        error_msgs.append(f"使用了未授权的算子/数据集: {', '.join(set(invalid_words))}。请严格从白名单中选取。")

    if error_msgs:
        full_error = " ".join(error_msgs)
        logger.warning(f"🔎[Node: Syntax] 拦截到致命错误: {full_error}")
        # 【修改重点】返回 feedback 让 AI 知道怎么改，并且累加 iteration_count
        return {
            "status": "syntax_error", 
            "error_msg": full_error,
            "feedback": f"本地语法检查报错: {full_error} 请修正。",
            "iteration_count": iteration + 1
        }
    
    logger.info("🔎[Node: Syntax] ✅ 本地语法检查完美通过。")
    return {"status": "syntax_passed", "error_msg": None}