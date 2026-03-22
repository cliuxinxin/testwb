# src/whitelist.py

# 确保这些是你当前账号真正解锁了的算子
ALLOWED_OPERATORS =[
    "rank", 
    "ts_mean", 
    "ts_corr", 
    "ts_rank", 
    "abs", 
    "log", 
    "sign",
    "group_neutralize"
]

# 确保这些是你当前账号可用的数据字段
ALLOWED_DATASETS =[
    "close", 
    "open", 
    "high", 
    "low", 
    "volume", 
    "vwap"
]

# 🚀 新增：允许使用的分类/群组数据（用于行业中性化）
ALLOWED_GROUPS =[
    "sector",
    "industry",
    "subindustry",
    "market",
    "group"   # ⬅️ 新增：放行关键字 group，防止被本地静态正则误杀

]

# 组装成一个全集，供本地语法检查器使用
WQ_WHITELIST = set(ALLOWED_OPERATORS + ALLOWED_DATASETS + ALLOWED_GROUPS)