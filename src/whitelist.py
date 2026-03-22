# src/whitelist.py

# 1. 算子分类定义（供 Coder 节点参考，增强 AI 逻辑能力）
ARITHMETIC_OPS = [
    "abs", "add", "densify", "divide", "inverse", "log", "max", "min", 
    "multiply", "power", "reverse", "sign", "signed_power", "sqrt", "subtract"
]

LOGICAL_OPS = [
    "and", "if_else", "is_nan", "not", "or"
]

TIME_SERIES_OPS = [
    "days_from_last_change", "hump", "kth_element", "last_diff_value",
    "ts_arg_max", "ts_arg_min", "ts_av_diff", "ts_backfill", "ts_corr",
    "ts_count_nans", "ts_covariance", "ts_decay_linear", "ts_delay",
    "ts_delta", "ts_mean", "ts_product", "ts_quantile", "ts_rank",
    "ts_regression", "ts_scale", "ts_std_dev", "ts_step", "ts_sum", "ts_zscore"
]

CROSS_SECTIONAL_OPS = [
    "normalize", "quantile", "rank", "scale", "winsorize", "zscore"
]

GROUP_OPS = [
    "group_backfill", "group_mean", "group_neutralize", 
    "group_rank", "group_scale", "group_zscore"
]

TRANSFORMATIONAL_OPS = [
    "bucket", "trade_when"
]

VECTOR_OPS = [
    "vec_avg", "vec_sum"
]

# 2. 基础数据集（根据你之前的运行情况，确保这些是可用的）
ALLOWED_DATASETS = [
    "close", "open", "high", "low", "volume", "vwap", "returns"
]

# 3. 允许使用的分组变量
ALLOWED_GROUPS = [
    "sector", "industry", "subindustry", "market", "group"
]

# 4. 汇总白名单（供 Syntax 节点静态检查使用）
# 包含所有算子、数据集和群组关键字
WQ_WHITELIST = set(
    ARITHMETIC_OPS + 
    LOGICAL_OPS + 
    TIME_SERIES_OPS + 
    CROSS_SECTIONAL_OPS + 
    GROUP_OPS + 
    TRANSFORMATIONAL_OPS + 
    VECTOR_OPS + 
    ALLOWED_DATASETS + 
    ALLOWED_GROUPS
)

# 5. 导出给 Coder 节点使用的纯算子列表字符串
ALLOWED_OPERATORS = ", ".join(
    ARITHMETIC_OPS + LOGICAL_OPS + TIME_SERIES_OPS + 
    CROSS_SECTIONAL_OPS + GROUP_OPS + TRANSFORMATIONAL_OPS + VECTOR_OPS
)