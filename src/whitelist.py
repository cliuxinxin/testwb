# src/whitelist.py
from typing import List

ARITHMETIC_OPS = [
    "abs", "add", "densify", "divide", "inverse", "log", "max", "min",
    "multiply", "power", "reverse", "sign", "signed_power", "sqrt", "subtract",
]

LOGICAL_OPS = [
    "and", "if_else", "is_nan", "not", "or",
]

TIME_SERIES_OPS = [
    "days_from_last_change", "hump", "kth_element", "last_diff_value",
    "ts_arg_max", "ts_arg_min", "ts_av_diff", "ts_backfill", "ts_corr",
    "ts_count_nans", "ts_covariance", "ts_decay_linear", "ts_delay",
    "ts_delta", "ts_mean", "ts_product", "ts_quantile", "ts_rank",
    "ts_regression", "ts_scale", "ts_std_dev", "ts_step", "ts_sum", "ts_zscore",
]

CROSS_SECTIONAL_OPS = [
    "normalize", "quantile", "rank", "scale", "winsorize", "zscore",
]

VECTOR_OPS = [
    "vec_avg", "vec_sum",
]

TRANSFORMATIONAL_OPS = [
    "bucket", "trade_when",
]

GROUP_OPS = [
    "group_backfill", "group_mean", "group_neutralize",
    "group_rank", "group_scale", "group_zscore",
]

ALLOWED_DATASETS = [
    "close", "open", "high", "low", "volume", "vwap", "returns",
]

ALLOWED_GROUPS = [
    "sector", "industry", "subindustry", "market", "group",
]

ALLOWED_COMPARATORS = ["<", "<=", "==", ">", ">=", "!="]

ALLOWED_OPTION_KEYWORDS = [
    "filter", "false", "true", "ignore", "nan", "lookback", "k",
    "dense", "driver", "gaussian", "cauchy", "uniform", "constant",
    "lag", "rettype", "usestd", "limit", "sigma", "rate", "scale",
    "longscale", "shortscale", "std", "range", "buckets", "skipboth",
    "nangroup", "hump",
]

ALLOWED_OPERATORS = (
    ARITHMETIC_OPS
    + LOGICAL_OPS
    + TIME_SERIES_OPS
    + CROSS_SECTIONAL_OPS
    + VECTOR_OPS
    + TRANSFORMATIONAL_OPS
    + GROUP_OPS
)

OPERATOR_SIGNATURES = {
    "abs": {"min_args": 1, "max_args": 1},
    "add": {"min_args": 2, "max_args": None, "named_args": {"filter"}},
    "densify": {"min_args": 1, "max_args": 1},
    "divide": {"min_args": 2, "max_args": 2},
    "inverse": {"min_args": 1, "max_args": 1},
    "log": {"min_args": 1, "max_args": 1},
    "max": {"min_args": 2, "max_args": None},
    "min": {"min_args": 2, "max_args": None},
    "multiply": {"min_args": 2, "max_args": None, "named_args": {"filter"}},
    "power": {"min_args": 2, "max_args": 2},
    "reverse": {"min_args": 1, "max_args": 1},
    "sign": {"min_args": 1, "max_args": 1},
    "signed_power": {"min_args": 2, "max_args": 2},
    "sqrt": {"min_args": 1, "max_args": 1},
    "subtract": {"min_args": 2, "max_args": None, "named_args": {"filter"}},
    "and": {"min_args": 2, "max_args": 2},
    "if_else": {"min_args": 3, "max_args": 3},
    "is_nan": {"min_args": 1, "max_args": 1},
    "not": {"min_args": 1, "max_args": 1},
    "or": {"min_args": 2, "max_args": 2},
    "days_from_last_change": {"min_args": 1, "max_args": 1},
    "hump": {"min_args": 1, "max_args": 2, "named_args": {"hump"}},
    "kth_element": {"min_args": 3, "max_args": 4, "named_args": {"ignore"}},
    "last_diff_value": {"min_args": 2, "max_args": 2},
    "ts_arg_max": {"min_args": 2, "max_args": 2},
    "ts_arg_min": {"min_args": 2, "max_args": 2},
    "ts_av_diff": {"min_args": 2, "max_args": 2},
    "ts_backfill": {"min_args": 2, "max_args": 3, "named_args": {"lookback", "k"}},
    "ts_corr": {"min_args": 3, "max_args": 3},
    "ts_count_nans": {"min_args": 2, "max_args": 2},
    "ts_covariance": {"min_args": 3, "max_args": 3},
    "ts_decay_linear": {"min_args": 2, "max_args": 3, "named_args": {"dense"}},
    "ts_delay": {"min_args": 2, "max_args": 2},
    "ts_delta": {"min_args": 2, "max_args": 2},
    "ts_mean": {"min_args": 2, "max_args": 2},
    "ts_product": {"min_args": 2, "max_args": 2},
    "ts_quantile": {"min_args": 2, "max_args": 3, "named_args": {"driver"}},
    "ts_rank": {"min_args": 2, "max_args": 3, "named_args": {"constant"}},
    "ts_regression": {"min_args": 3, "max_args": 5, "named_args": {"lag", "rettype"}},
    "ts_scale": {"min_args": 2, "max_args": 3, "named_args": {"constant"}},
    "ts_std_dev": {"min_args": 2, "max_args": 2},
    "ts_step": {"min_args": 1, "max_args": 1},
    "ts_sum": {"min_args": 2, "max_args": 2},
    "ts_zscore": {"min_args": 2, "max_args": 2},
    "normalize": {"min_args": 1, "max_args": 3, "named_args": {"usestd", "limit"}},
    "quantile": {"min_args": 1, "max_args": 3, "named_args": {"driver", "sigma"}},
    "rank": {"min_args": 1, "max_args": 2, "named_args": {"rate"}},
    "scale": {"min_args": 1, "max_args": 4, "named_args": {"scale", "longscale", "shortscale"}},
    "winsorize": {"min_args": 1, "max_args": 2, "named_args": {"std"}},
    "zscore": {"min_args": 1, "max_args": 1},
    "vec_avg": {"min_args": 1, "max_args": 1},
    "vec_sum": {"min_args": 1, "max_args": 1},
    "bucket": {"min_args": 2, "max_args": 4, "named_args": {"range", "buckets", "skipboth", "nangroup"}},
    "trade_when": {"min_args": 3, "max_args": 3},
    "group_backfill": {"min_args": 3, "max_args": 4, "named_args": {"std"}},
    "group_mean": {"min_args": 3, "max_args": 3},
    "group_neutralize": {"min_args": 2, "max_args": 2},
    "group_rank": {"min_args": 2, "max_args": 2},
    "group_scale": {"min_args": 2, "max_args": 2},
    "group_zscore": {"min_args": 2, "max_args": 2},
}

INTEGER_ARG_RULES = {
    "kth_element": {1, 2},
    "last_diff_value": {1},
    "ts_arg_max": {1},
    "ts_arg_min": {1},
    "ts_av_diff": {1},
    "ts_backfill": {1},
    "ts_corr": {2},
    "ts_count_nans": {1},
    "ts_covariance": {2},
    "ts_decay_linear": {1},
    "ts_delay": {1},
    "ts_delta": {1},
    "ts_mean": {1},
    "ts_product": {1},
    "ts_quantile": {1},
    "ts_rank": {1},
    "ts_regression": {2},
    "ts_scale": {1},
    "ts_std_dev": {1},
    "ts_step": {0},
    "ts_sum": {1},
    "ts_zscore": {1},
    "group_backfill": {2},
}

INTEGER_NAMED_ARG_RULES = {
    "ts_backfill": {"lookback", "k"},
    "ts_rank": {"constant"},
    "ts_scale": {"constant"},
    "ts_regression": {"lag", "rettype"},
}

NUMERIC_NAMED_ARG_RULES = {
    "add": {"filter"},
    "multiply": {"filter"},
    "subtract": {"filter"},
    "hump": {"hump"},
    "ts_decay_linear": {"dense"},
    "normalize": {"limit"},
    "quantile": {"sigma"},
    "rank": {"rate"},
    "scale": {"scale", "longscale", "shortscale"},
    "winsorize": {"std"},
    "group_backfill": {"std"},
}

BOOLEAN_NAMED_ARG_RULES = {
    "add": {"filter"},
    "multiply": {"filter"},
    "subtract": {"filter"},
    "ts_decay_linear": {"dense"},
    "normalize": {"usestd"},
    "bucket": {"skipboth", "nangroup"},
}

ENUM_NAMED_ARG_RULES = {
    "kth_element": {"ignore": {"nan"}},
    "ts_quantile": {"driver": {"gaussian", "cauchy", "uniform"}},
    "quantile": {"driver": {"gaussian", "cauchy", "uniform"}},
}

GROUP_ARG_RULES = {
    "group_backfill": {1},
    "group_mean": {2},
    "group_neutralize": {1},
    "group_rank": {1},
    "group_scale": {1},
    "group_zscore": {1},
}

REQUIRED_NAMED_ARG_RULES = {
    "bucket": {"range", "buckets"},
}

NAMED_ONLY_ARG_RULES = {
    "hump": {1},
}

OPERATOR_MANUAL = {
    "Arithmetic": [
        ("abs(x)", "取绝对值。"),
        ("add(x, y, filter=false)", "逐元素相加；filter=true 时把 NaN 当 0。"),
        ("densify(x)", "压缩分组桶，常用于分组字段。"),
        ("divide(x, y)", "逐元素相除。"),
        ("inverse(x)", "返回 1/x。"),
        ("log(x)", "自然对数；输入应为正。"),
        ("max(x, y, ...)", "返回多个输入中的最大值，至少 2 个参数。"),
        ("min(x, y, ...)", "返回多个输入中的最小值，至少 2 个参数。"),
        ("multiply(x, y, ..., filter=false)", "逐元素相乘；filter=true 时把 NaN 当 0。"),
        ("power(x, y)", "x 的 y 次幂。"),
        ("reverse(x)", "返回 -x。"),
        ("sign(x)", "返回符号位：正为 1，负为 -1，0 为 0。"),
        ("signed_power(x, y)", "保留 x 符号的幂运算。"),
        ("sqrt(x)", "非负平方根；有符号开方用 signed_power(x, 0.5)。"),
        ("subtract(x, y, ..., filter=false)", "从左到右依次相减；filter=true 时把 NaN 当 0。"),
    ],
    "Logical": [
        ("and(a, b)", "两者都为真时返回 1；必须用函数形式。"),
        ("if_else(cond, a, b)", "条件为真返回 a，否则返回 b。"),
        ("a < b / a <= b / a == b / a > b / a >= b / a != b", "比较结果返回 1/0。"),
        ("is_nan(x)", "x 为 NaN 时返回 1，否则返回 0。"),
        ("not(x)", "逻辑取反。"),
        ("or(a, b)", "任一为真时返回 1；必须用函数形式。"),
    ],
    "Time Series": [
        ("days_from_last_change(x)", "距离上次变化过去了多少天。"),
        ("hump(x, hump=0.01)", "限制变化幅度，常用于降换手。"),
        ("kth_element(x, d, k, ignore=\"NaN\")", "回看 d 天取第 k 个值，常用于回填。"),
        ("last_diff_value(x, d)", "返回过去 d 天中最近一次与当前不同的值。"),
        ("ts_arg_max(x, d)", "过去 d 天最大值距今天数。"),
        ("ts_arg_min(x, d)", "过去 d 天最小值距今天数。"),
        ("ts_av_diff(x, d)", "x 与 ts_mean(x, d) 的差，忽略均值中的 NaN。"),
        ("ts_backfill(x, lookback=d, k=1)", "用最近有效值回填 NaN。"),
        ("ts_corr(x, y, d)", "过去 d 天的皮尔逊相关。"),
        ("ts_count_nans(x, d)", "过去 d 天 NaN 的个数。"),
        ("ts_covariance(y, x, d)", "过去 d 天协方差。"),
        ("ts_decay_linear(x, d, dense=false)", "线性衰减平滑。"),
        ("ts_delay(x, d)", "取 d 天前的值。"),
        ("ts_delta(x, d)", "x 与 d 天前值的差。"),
        ("ts_mean(x, d)", "过去 d 天均值。"),
        ("ts_product(x, d)", "过去 d 天连乘。"),
        ("ts_quantile(x, d, driver=\"gaussian\")", "滚动 rank 后再做分布变换。"),
        ("ts_rank(x, d, constant=0)", "时间序列排名。"),
        ("ts_regression(y, x, d, lag=0, rettype=0)", "回归相关参数；顺序是 y, x, d。"),
        ("ts_scale(x, d, constant=0)", "把时间序列缩放到 0 到 1。"),
        ("ts_std_dev(x, d)", "过去 d 天标准差。"),
        ("ts_step(1)", "天数计数器，只写 1。"),
        ("ts_sum(x, d)", "过去 d 天求和。"),
        ("ts_zscore(x, d)", "过去 d 天 Z-score。"),
    ],
    "Cross Sectional": [
        ("normalize(x, useStd=false, limit=0.0)", "横截面去均值，可选除标准差并裁剪。"),
        ("quantile(x, driver=gaussian, sigma=1.0)", "横截面 rank 后做分布变换。"),
        ("rank(x, rate=2)", "横截面排名到 0 到 1。"),
        ("scale(x, scale=1, longscale=1, shortscale=1)", "缩放多空头寸规模。"),
        ("winsorize(x, std=4)", "按标准差裁剪极值。"),
        ("zscore(x)", "横截面 Z-score。"),
    ],
    "Vector": [
        ("vec_avg(x)", "向量字段取均值。"),
        ("vec_sum(x)", "向量字段求和。"),
    ],
    "Transformational": [
        ("bucket(rank(x), range=\"0,1,0.1\", skipBoth=False, NaNGroup=False)", "按区间分桶。"),
        ("bucket(rank(x), buckets=\"2,5,6,7,10\", skipBoth=False, NaNGroup=False)", "按自定义桶分组。"),
        ("trade_when(x, y, z)", "开仓条件满足时更新为 y，未满足保持历史值，z 满足时平仓为 NaN。"),
    ],
    "Group": [
        ("group_backfill(x, group, d, std=4.0)", "组内 winsorized mean 回填。"),
        ("group_mean(x, weight, group)", "第二个参数是 weight，第三个参数才是 group。"),
        ("group_neutralize(x, group)", "对组内均值做中性化。"),
        ("group_rank(x, group)", "组内排名。"),
        ("group_scale(x, group)", "组内缩放。"),
        ("group_zscore(x, group)", "组内 Z-score。"),
    ],
}

IDEA_METHOD_RULES = [
    "只能构思能用允许数据和允许算子直接落地的思路，禁止虚构自定义字段或外部数据。",
    "思路里要明确数据来源、时间序列变换和横截面/分组处理，不要只说抽象概念。",
    "优先使用 ts_mean、ts_rank、ts_zscore、rank、zscore、group_neutralize、hump、trade_when 这类稳定模式。",
    "如果逻辑容易高换手，必须在思路里主动考虑 hump、ts_mean、ts_decay_linear 或 trade_when 的控换手手段。",
    "如果要做分组，group 参数只能是 sector、industry、subindustry、market、group 或 bucket(...) 的结果。",
    "思路必须简短、可执行，不能输出伪代码、变量名规划或多步算法说明。",
]

CODER_METHOD_RULES = [
    "必须严格按手册签名写算子，参数顺序不能自己发明。",
    "只有手册明确支持时才能写命名参数；例如 bucket 的 range=/buckets=、ts_backfill 的 lookback=/k=。",
    "逻辑判断允许比较运算符和 and(a,b)/or(a,b)/not(x)/if_else(cond,a,b) 的函数形式；禁止写 Python 中缀 `x and y`、`x or y` 或三元表达式。",
    "所有窗口参数都必须是具体整数，不能写 N、M、d 这类抽象变量。",
    "group_* 系列的 group 参数必须是分组字段或 bucket(...)，不能写数字、列表、字典或命名参数。",
    "group_mean(x, weight, group) 的第二个参数是 weight，不是 group。",
    "trade_when(x, y, z) 固定 3 个参数，不要增删参数，也不要把条件写成 Python 语句。",
    "bucket(...) 必须显式给出 range= 或 buckets=，不要只写裸字符串。",
    "ts_regression 的顺序固定为 y, x, d, lag, rettype，不要把 x/y 顺序写反。",
    "ts_step 只能写成 ts_step(1)。",
    "不要把常数直接加减到 close、open、high、low、volume、vwap 这类带量纲原始字段上。",
    "输出必须只有一行纯表达式，不能带 Markdown、解释文字或多余空行。",
]


def _format_operator_categories() -> str:
    sections = [
        ("Arithmetic", ARITHMETIC_OPS),
        ("Logical", LOGICAL_OPS),
        ("Time Series", TIME_SERIES_OPS),
        ("Cross Sectional", CROSS_SECTIONAL_OPS),
        ("Vector", VECTOR_OPS),
        ("Transformational", TRANSFORMATIONAL_OPS),
        ("Group", GROUP_OPS),
    ]
    return "\n".join(
        f"- {category}: {', '.join(operators)}" for category, operators in sections
    )


def _format_manual() -> str:
    lines = []
    for category, entries in OPERATOR_MANUAL.items():
        lines.append(f"{category}:")
        for signature, desc in entries:
            lines.append(f"- {signature}: {desc}")
    return "\n".join(lines)


def _format_rules(rules: List[str]) -> str:
    return "\n".join(f"{idx}. {rule}" for idx, rule in enumerate(rules, start=1))


OPERATOR_CATEGORY_TEXT = _format_operator_categories()
OPERATOR_MANUAL_TEXT = _format_manual()
IDEA_METHOD_RULES_TEXT = _format_rules(IDEA_METHOD_RULES)
CODER_METHOD_RULES_TEXT = _format_rules(CODER_METHOD_RULES)

WQ_WHITELIST = {
    item.lower()
    for item in (
        ALLOWED_OPERATORS
        + ALLOWED_DATASETS
        + ALLOWED_GROUPS
        + ALLOWED_OPTION_KEYWORDS
    )
}
