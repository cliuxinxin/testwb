import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_base: str
    api_key: str
    model: str
    max_iterations: int


def _read_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name, str(default))
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def get_settings() -> Settings:
    return Settings(
        api_base=os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("LLM_MODEL", "gpt-4o"),
        max_iterations=max(1, _read_int_env("MAX_ITERATIONS", 4)),
    )
