from typing import Optional

from langchain_openai import ChatOpenAI
from src.config import Settings, get_settings
from src.logger import logger


def get_llm(temperature=0.7, settings: Optional[Settings] = None) -> ChatOpenAI:
    current_settings = settings or get_settings()

    logger.debug(
        f"初始化 LLM 客户端: Model={current_settings.model}, Base={current_settings.api_base}"
    )
    return ChatOpenAI(
        api_key=current_settings.api_key,
        base_url=current_settings.api_base,
        model=current_settings.model,
        temperature=temperature,
    )
