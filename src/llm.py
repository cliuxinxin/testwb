import os
from langchain_openai import ChatOpenAI
from src.logger import logger


def get_llm(temperature=0.7) -> ChatOpenAI:
    # 动态从环境变量中获取（配合 Streamlit/外部控制面板）
    api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("LLM_MODEL", "gpt-4o")

    logger.debug(f"初始化 LLM 客户端: Model={model}, Base={api_base}")
    return ChatOpenAI(
        api_key=api_key, base_url=api_base, model=model, temperature=temperature
    )
