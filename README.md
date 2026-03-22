WQ Alpha 自动化挖掘系统 - 使用指南
===================================


1) 概要
- 目的：通过模块化的 LangGraph 工作流，实现“生成因子灵感 → 写出表达式 → 回测 → 评估 → 迭代”的闭环。
- 可视化：前端使用 Streamlit，方便观察状态机流转、LLM 生成的因子文本、回测指标和日志。


2) 依赖与环境需求
- Python 3.8+ (推荐 3.9+)
- 依赖安装：`pip install -r requirements.txt`
- (可选) Streamlit: 通过 `pip install streamlit` 安装
- 大模型后端：可以使用官方 OpenAI 接口，也可以配置 DeepSeek、 Ollama 本地等 OpenAI 兼容接口


3) 配置与环境变量
- 核心变量（请优先使用 .env.sample 的模板来创建实际的 .env）：
  - OPENAI_API_BASE: OpenAI 兼容接口的基地址，如 https://api.openai.com/v1
  - OPENAI_API_KEY: 对应的 API Key
  - LLM_MODEL: 模型名称，如 gpt-4o、deepseek-chat、qwen2.5 等，取决于所用后端
  - MAX_ITERATIONS: 最大迭代轮次（整数）
- 如何设置
  - 将 .env.sample 复制为 .env，然后填入你的数据：
    cp .env.sample .env
    编辑 .env，填入 OPENAI_API_BASE、OPENAI_API_KEY、LLM_MODEL、MAX_ITERATIONS
  - 如果暂时不需要一个环境文件，可以直接在运行阶段通过环境变量覆盖，例如在 Linux/macOS：
    export OPENAI_API_BASE=https://api.openai.com/v1
    export OPENAI_API_KEY=your-key
    export LLM_MODEL=gpt-4o
    export MAX_ITERATIONS=4


4) 快速上手

4.1 使用 Streamlit 前端 UI
- 安装依赖
  - python -m venv venv
  - source venv/bin/activate  # macOS/Linux
  - pip install -r requirements.txt
  - pip install streamlit
- 启动 UI
  - streamlit run webui.py
- 浏览器访问 http://localhost:8501

4.2 使用 CLI 入口运行（不依赖 UI 时的简易验证）
- python main.py

5) 后端切换与测试建议
- 使用 OpenAI 官方接口（默认）
  - OPENAI_API_BASE=https://api.openai.com/v1
  - LLM_MODEL=gpt-4o
- 使用 DeepSeek
  - OPENAI_API_BASE=https://api.deepseek.com/v1
  - OPENAI_API_KEY=your-deepseek-key
  - LLM_MODEL=deepseek-chat
- 本地 Ollama / qwen2.5
  - OPENAI_API_BASE=http://localhost:11434/v1
  - OPENAI_API_KEY=ollama
  - LLM_MODEL=qwen2.5

6) 日志与排错
- 日志位置：logs/wq_bot_YYYY-MM-DD.log
- UI 提供的实时监控与日志输出，便于快速定位问题
- 常见问题：
  - 如果 UI 提示无法连接到后端：检查 OPENAI_API_BASE、OPENAI_API_KEY、LLM_MODEL 是否正确，并确保网络连通性
  - 本地模型不可用：确保 Ollama 或本地服务正在运行，端口与模型名与 .env 配置一致

7) 文件结构要点（与现有实现对齐）
- .env.sample 用于演示应配置的环境变量
- webui.py 提供 Streamlit 界面，可跨平台运行
- src/ 目录下维护了核心逻辑（Graph、Nodes、LLM 调用、日志等），前端仅消费并展示数据流

8) 下一步（可选）
- 将 alpha_history 持久化到 SQLite/CSV，便于离线分析
- 增强前端图表，展示更多指标（如迭代时间、每步耗时、失败原因统计等）
- 增加错误处理策略与重试机制
- 针对不同后端添加单元测试与端到端测试用例

如果你愿意，我可以：
- 直接把上述两份文件打包成一个 Git 补丁（patch），你只需粘贴进你的仓库即可
- 根据你的具体后端（OpenAI、DeepSeek、 Ollama）的实际地址，给出一个即用的 .env 带注释的版本
- 进一步扩展 README，包含常见问题的快速排错清单和一个“快速上手演示视频”的准备指南

需要我把这两份文件以 patch 的形式直接给你吗？或者你想让我再把 README 扩展成包含一个“快速演示视频脚本/命令清单”版本？
