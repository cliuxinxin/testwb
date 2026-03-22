import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

# 读取配置，提供默认值防止崩溃
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o")
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", 4))
