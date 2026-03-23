import streamlit as st
import time
from src.config import Settings, get_settings
from src.graph import build_graph

# ==========================================
# 1. 页面配置与状态初始化
# ==========================================
st.set_page_config(page_title="WQ Alpha 自动化挖掘系统", page_icon="📈", layout="wide")
initial_settings = get_settings()

if "alpha_history" not in st.session_state:
    st.session_state.alpha_history = []
if "is_running" not in st.session_state:
    st.session_state.is_running = False

# ==========================================
# 2. 侧边栏：环境配置 (支持 UI 动态修改)
# ==========================================
with st.sidebar:
    st.title("⚙️ 系统配置")

    api_base = st.text_input(
        "API Base URL", value=initial_settings.api_base
    )
    api_key = st.text_input(
        "API Key", value=initial_settings.api_key, type="password"
    )
    model = st.text_input("LLM Model", value=initial_settings.model)
    max_iter = st.number_input(
        "最大迭代次数",
        min_value=1,
        max_value=10,
        value=initial_settings.max_iterations,
    )

    current_settings = Settings(
        api_base=api_base,
        api_key=api_key,
        model=model,
        max_iterations=int(max_iter),
    )

    st.markdown("---")
    st.markdown("### 🛠️ 调试面板")
    start_btn = st.button(
        "🚀 启动单次因子挖掘", use_container_width=True, type="primary"
    )

# ==========================================
# 3. 主界面布局
# ==========================================
st.title("🤖 WorldQuant Brain 自动化因子挖掘")
st.markdown("基于 LangGraph 编排的 `生成 -> 回测 -> 评估 -> 迭代` 闭环系统。")

# 创建 Tab 页面
tab_monitor, tab_history = st.tabs(["👁️ 实时监控面板", "📚 成功因子库"])

with tab_monitor:
    # 占位符定义，用于流式更新内容
    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("💡 因子逻辑 (Idea)")
        idea_placeholder = st.empty()
        st.subheader("💻 当前表达式 (Expression)")
        code_placeholder = st.empty()
        st.subheader("🔄 迭代状态")
        status_placeholder = st.empty()
    with col2:
        st.subheader("📊 回测指标 (Simulation)")
        metrics_placeholder = st.empty()
        st.subheader("⚖️ 评估建议 (Feedback)")
        feedback_placeholder = st.empty()
    st.markdown("---")
    st.subheader("📜 节点流转日志 (LangGraph Trace)")
    log_placeholder = st.empty()

# ==========================================
# 4. 核心逻辑：触发与流式渲染
# ==========================================
if start_btn:
    if not current_settings.api_key:
        st.error("请在左侧栏输入 API Key！")
        st.stop()

    # 清空占位符并重置状态
    idea_placeholder.info("等待生成...")
    code_placeholder.code("# 等待生成...")
    metrics_placeholder.info("等待回测...")
    feedback_placeholder.info("等待评估...")
    log_text = ""
    log_placeholder.code("系统启动...\n", language="text")

    # 编译 LangGraph
    app = build_graph(current_settings)
    initial_state = {"iteration_count": 0, "status": "new"}

    st.session_state.is_running = True

    # 使用 Streamlit 的进度 Spinner 罩住整个运行过程
    with st.spinner("🤖 自动化因子挖掘流水线运行中..."):
        try:
            # LangGraph 流式执行
            for output in app.stream(initial_state):
                for node_name, state_update in output.items():
                    # 1. 记录日志
                    log_text += (
                        f"[{time.strftime('%H:%M:%S')}] 节点 [{node_name}] 执行完毕。\n"
                    )
                    log_placeholder.code(log_text, language="text")

                    # 2. 实时更新 UI 状态
                    if "idea" in state_update:
                        idea_placeholder.success(state_update["idea"])

                    if "expression" in state_update:
                        code_placeholder.code(
                            state_update["expression"], language="python"
                        )

                    if "iteration_count" in state_update:
                        status_placeholder.metric(
                            "当前迭代次数", state_update["iteration_count"]
                        )

                    if (
                        "simulation_results" in state_update
                        and state_update["simulation_results"]
                    ):
                        res = state_update["simulation_results"]
                        m1, m2, m3 = metrics_placeholder.columns(3)
                        m1.metric("Sharpe", res.get("sharpe", 0))
                        m2.metric("Turnover", res.get("turnover", 0))
                        m3.metric("Fitness", res.get("fitness", 0))
                    elif node_name == "simulator" and state_update.get("error_msg"):
                        metrics_placeholder.error(
                            f"❌ 平台报错: {state_update['error_msg']}"
                        )

                    if "feedback" in state_update and state_update["feedback"]:
                        if state_update.get("status") in {"passed", "stored"}:
                            feedback_placeholder.success(state_update["feedback"])
                        elif state_update.get("status") == "error":
                            feedback_placeholder.error(state_update["feedback"])
                        else:
                            feedback_placeholder.warning(state_update["feedback"])

                    # 3. 提交成功，写入历史库
                    if node_name == "submitter":
                        st.session_state.alpha_history.append(
                            {
                                "idea": state_update.get("idea", "未知逻辑"),
                                "expression": state_update.get("expression", ""),
                                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                            }
                        )
                        st.balloons()  # 放气球庆祝

                    time.sleep(0.5)  # 给 UI 一点渲染的缓冲时间

        except Exception as e:
            st.error(f"运行发生异常: {str(e)}")

    st.session_state.is_running = False

# ==========================================
# 5. 渲染历史提交页面
# ==========================================
with tab_history:
    st.subheader("🏆 成功提交的 Alpha 记录")
    if not st.session_state.alpha_history:
        st.info("暂无成功提交的因子。快去挖掘吧！")
    else:
        for idx, item in enumerate(reversed(st.session_state.alpha_history)):
            with st.expander(
                f"Alpha #{len(st.session_state.alpha_history) - idx} | {item['time']}"
            ):
                st.markdown(f"**逻辑**: {item['idea']}")
                st.code(item["expression"], language="python")
