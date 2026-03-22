import time
from src.logger import logger
from src.graph import build_graph


def main():
    logger.info("=" * 50)
    logger.info("🤖 WorldQuant Brain 自动化因子挖掘系统启动")
    logger.info("=" * 50)

    app = build_graph()

    initial_state = {"iteration_count": 0, "status": "new"}

    logger.info("▶️ 开始单次挖掘任务流...")
    start_time = time.time()

    try:
        for output in app.stream(initial_state):
            for node_name, state_update in output.items():
                logger.debug(f"--- 节点 [{node_name}] 执行完毕 ---")
    except Exception as e:
        logger.error(f"工作流执行中发生致命错误: {str(e)}", exc_info=True)

    elapsed = time.time() - start_time
    logger.info(f"⏹️ 任务流结束。总耗时: {elapsed:.2f} 秒。")


if __name__ == "__main__":
    main()
