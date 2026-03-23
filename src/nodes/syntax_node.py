# src/nodes/syntax_node.py
import re
from typing import List, Optional, Tuple

from src.state import AlphaState
from src.logger import logger
from src.db import save_attempt
from src.whitelist import (
    ALLOWED_GROUPS,
    BOOLEAN_NAMED_ARG_RULES,
    ENUM_NAMED_ARG_RULES,
    GROUP_ARG_RULES,
    INTEGER_ARG_RULES,
    INTEGER_NAMED_ARG_RULES,
    NAMED_ONLY_ARG_RULES,
    NUMERIC_NAMED_ARG_RULES,
    OPERATOR_SIGNATURES,
    REQUIRED_NAMED_ARG_RULES,
    WQ_WHITELIST,
)


def split_top_level_args(arg_text: str) -> List[str]:
    if not arg_text.strip():
        return []

    args = []
    current = []
    depth = 0
    quote_char = None

    for char in arg_text:
        if quote_char:
            current.append(char)
            if char == quote_char:
                quote_char = None
            continue

        if char in {"'", '"'}:
            quote_char = char
            current.append(char)
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        elif char == "," and depth == 0:
            args.append("".join(current).strip())
            current = []
            continue

        current.append(char)

    tail = "".join(current).strip()
    if tail:
        args.append(tail)
    return args


def find_matching_paren(text: str, open_index: int) -> int:
    depth = 0
    quote_char = None

    for idx in range(open_index, len(text)):
        char = text[idx]
        if quote_char:
            if char == quote_char:
                quote_char = None
            continue

        if char in {"'", '"'}:
            quote_char = char
            continue

        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return idx

    return -1


def extract_function_calls(text: str) -> List[Tuple[str, List[str]]]:
    calls = []
    idx = 0

    while idx < len(text):
        if text[idx].isalpha() or text[idx] == "_":
            start = idx
            while idx < len(text) and (text[idx].isalnum() or text[idx] == "_"):
                idx += 1
            name = text[start:idx]

            look_ahead = idx
            while look_ahead < len(text) and text[look_ahead].isspace():
                look_ahead += 1

            if look_ahead < len(text) and text[look_ahead] == "(":
                close_idx = find_matching_paren(text, look_ahead)
                if close_idx == -1:
                    return calls

                inner = text[look_ahead + 1:close_idx]
                args = split_top_level_args(inner)
                calls.append((name, args))
                for arg in args:
                    calls.extend(extract_function_calls(arg))
                idx = close_idx + 1
                continue

        idx += 1

    return calls


def extract_named_arg(arg: str) -> Optional[Tuple[str, str]]:
    match = re.match(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+)$", arg)
    if not match:
        return None
    return match.group(1).lower(), match.group(2).strip()


def is_integer_literal(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?\d+", value.strip()))


def is_numeric_literal(value: str) -> bool:
    return bool(re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", value.strip()))


def is_boolean_literal(value: str) -> bool:
    return value.strip().lower() in {"true", "false"}


def is_group_expression(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        normalized in ALLOWED_GROUPS
        or normalized.startswith("bucket(")
        or normalized.startswith("densify(")
    )


def validate_function_call(name: str, args: List[str]) -> List[str]:
    spec = OPERATOR_SIGNATURES.get(name.lower())
    if not spec:
        return []

    errors = []
    min_args = spec["min_args"]
    max_args = spec["max_args"]
    arg_count = len(args)
    named_args = spec.get("named_args", set())

    if arg_count < min_args:
        errors.append(f"{name} 至少需要 {min_args} 个参数，当前只有 {arg_count} 个。")
    if max_args is not None and arg_count > max_args:
        errors.append(f"{name} 最多允许 {max_args} 个参数，当前写了 {arg_count} 个。")

    seen_named_args = set()
    for index, arg in enumerate(args):
        named = extract_named_arg(arg)
        if not named:
            continue

        key, value = named
        seen_named_args.add(key)

        if key not in named_args:
            errors.append(f"{name} 不支持命名参数 `{key}`。")
            continue

        if key in INTEGER_NAMED_ARG_RULES.get(name.lower(), set()) and not is_integer_literal(value):
            errors.append(f"{name} 的命名参数 `{key}` 必须是整数。")

        if key in NUMERIC_NAMED_ARG_RULES.get(name.lower(), set()) and key not in BOOLEAN_NAMED_ARG_RULES.get(name.lower(), set()):
            if not is_numeric_literal(value):
                errors.append(f"{name} 的命名参数 `{key}` 必须是数值。")

        if key in BOOLEAN_NAMED_ARG_RULES.get(name.lower(), set()) and not is_boolean_literal(value):
            errors.append(f"{name} 的命名参数 `{key}` 必须是 true 或 false。")

        allowed_enum_values = ENUM_NAMED_ARG_RULES.get(name.lower(), {}).get(key)
        if allowed_enum_values and value.strip().strip("'\"").lower() not in allowed_enum_values:
            errors.append(
                f"{name} 的命名参数 `{key}` 只能取 {', '.join(sorted(allowed_enum_values))}。"
            )

    required_named_args = REQUIRED_NAMED_ARG_RULES.get(name.lower())
    if required_named_args and not seen_named_args.intersection(required_named_args):
        errors.append(
            f"{name} 必须显式提供命名参数 {', '.join(sorted(required_named_args))} 之一。"
        )

    for position in INTEGER_ARG_RULES.get(name.lower(), set()):
        if position >= arg_count:
            continue
        named = extract_named_arg(args[position])
        if named:
            continue
        if not is_integer_literal(args[position]):
            errors.append(f"{name} 的第 {position + 1} 个参数必须是整数。")

    for position in GROUP_ARG_RULES.get(name.lower(), set()):
        if position >= arg_count:
            continue
        named = extract_named_arg(args[position])
        if named:
            errors.append(f"{name} 的分组参数必须用位置参数传入，不能写命名参数。")
            continue
        if not is_group_expression(args[position]):
            errors.append(
                f"{name} 的分组参数必须是 {', '.join(ALLOWED_GROUPS)} 或 bucket(...)/densify(...)。"
            )

    for position in NAMED_ONLY_ARG_RULES.get(name.lower(), set()):
        if position >= arg_count:
            continue
        if not extract_named_arg(args[position]):
            errors.append(
                f"{name} 的第 {position + 1} 个参数必须使用命名参数形式。示例: hump(x, hump=0.01)。"
            )

    if name.lower() == "ts_step" and arg_count >= 1 and args[0].strip() != "1":
        errors.append("ts_step 只能写成 ts_step(1)。")

    return errors

def check_syntax(state: AlphaState) -> dict:
    expression = state.get("expression", "")
    iteration = state.get("iteration_count", 0)
    attempted_expressions = state.get("attempted_expressions", [])
    logger.info(f"🔎 [Node: Syntax] 本地静态查错中...")
    error_msgs = []

    if expression in attempted_expressions:
        full_error = f"检测到重复表达式，当前公式已经在本轮尝试过: {expression}"
        logger.warning(f"🔎[Node: Syntax] 命中重复表达式: {expression}")
        save_attempt(
            stage="syntax",
            status="repeat_expression",
            idea=state.get("idea", ""),
            expression=expression,
            error_msg=full_error,
            feedback="本轮已经生成过同一表达式。不要继续微调这个公式，必须换一个新的因子思路和结构。",
        )
        return {
            "status": "need_new_idea",
            "error_msg": full_error,
            "feedback": "本轮已经生成过同一表达式。不要继续微调这个公式，必须换一个新的因子思路和结构。",
            "iteration_count": iteration + 1,
            "repeat_error_count": state.get("repeat_error_count", 0) + 1,
        }

    if '[' in expression or ']' in expression or '{' in expression or '}' in expression:
        error_msgs.append("绝对禁止使用中括号 [] 或大括号 {}，WQ 表达式仅支持小括号 ()。")
    
    if expression.count('(') != expression.count(')'):
        error_msgs.append("括号不匹配 (Unbalanced parentheses)。")
        
    if re.search(r'\d[eE][+-]?\d', expression):
        error_msgs.append("绝对禁止使用科学计数法 (如 1e-5)，请使用完整小数。")
        
        
    if re.search(r',\s*[A-Za-z]\s*\)', expression):
        error_msgs.append("周期参数不能是抽象字母（如 N, M），必须是具体整数。")

    if re.search(r"\b(and|or)\b(?!\s*\()", expression):
        error_msgs.append("逻辑与/或只能使用函数形式 and(a, b) 或 or(a, b)，不能写 Python 中缀语法。")

    if re.search(r"\bif\b.+\belse\b", expression):
        error_msgs.append("绝对禁止使用 Python 三元表达式，请改用 if_else(cond, a, b)。")

    words = re.findall(r'[a-zA-Z_]\w*', expression)
    invalid_words = [w for w in words if w.lower() not in WQ_WHITELIST]
    if invalid_words:
        error_msgs.append(f"使用了未授权的算子/数据集: {', '.join(set(invalid_words))}。请严格从白名单中选取。")

    for func_name, func_args in extract_function_calls(expression):
        error_msgs.extend(validate_function_call(func_name, func_args))

    if error_msgs:
        full_error = " ".join(error_msgs)
        logger.warning(f"🔎[Node: Syntax] 拦截到致命错误: {full_error}")
        save_attempt(
            stage="syntax",
            status="syntax_error",
            idea=state.get("idea", ""),
            expression=expression,
            error_msg=full_error,
            feedback=f"本地语法检查报错: {full_error} 请修正。",
        )
        # 【修改重点】返回 feedback 让 AI 知道怎么改，并且累加 iteration_count
        return {
            "status": "syntax_error", 
            "error_msg": full_error,
            "feedback": f"本地语法检查报错: {full_error} 请修正。",
            "iteration_count": iteration + 1,
            "attempted_expressions": (attempted_expressions + [expression])[-8:],
            "repeat_error_count": state.get("repeat_error_count", 0),
        }
    
    logger.info("🔎[Node: Syntax] ✅ 本地语法检查完美通过。")
    return {
        "status": "syntax_passed",
        "error_msg": None,
        "attempted_expressions": (attempted_expressions + [expression])[-8:],
        "repeat_error_count": state.get("repeat_error_count", 0),
    }
