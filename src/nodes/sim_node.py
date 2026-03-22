# src/nodes/sim_node.py
import time
import os
import sys
import re
from playwright.sync_api import sync_playwright
from src.state import AlphaState
from src.logger import logger

COOKIE_PATH = "wq_cookies.json"

# ==========================================================
# 💡 全局单例：浏览器管家 (实现浏览器复用，不重复开关)
# ==========================================================
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def get_page(self):
        if self.page is None:
            logger.info("🚀 首次启动常驻浏览器...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False, args=["--start-maximized"])
            self.context = self.browser.new_context(
                storage_state=COOKIE_PATH, viewport={"width": 1920, "height": 1080}
            )
            self.page = self.context.new_page()
            
            logger.debug("正在打开 WQ 模拟页...")
            self.page.goto("https://platform.worldquantbrain.com/simulate", timeout=60000)
            self.page.wait_for_load_state("networkidle")
            time.sleep(3)
        return self.page

browser_manager = BrowserManager()

def close_annoying_popups(page):
    selectors =[
        "text='Accept All'", "text='Skip'", "text='Got it'", 
        "text='Close'", ".introjs-skipbutton", ".modal-close-button"
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.is_visible(timeout=500):
                loc.click()
                time.sleep(0.5)
        except:
            pass

def run_simulation(state: AlphaState) -> dict:
    expression = state.get("expression")
    logger.info(f"⚙️ [Node: Simulator] 准备在常驻浏览器中执行回测...")

    if not os.path.exists(COOKIE_PATH):
        return {"status": "error", "error_msg": "Missing wq_cookies.json", "simulation_results": {}}

    try:
        page = browser_manager.get_page()

        # ==========================================
        # 🚀 第一重防御：页面状态强制重置 (清除幽灵任务)
        # ==========================================
        # 如果当前页面正在跑上一个卡住的任务（出现 Cancel 按钮），强制刷新！
        if page.locator("button:has-text('Cancel')").first.is_visible(timeout=1000):
            logger.warning("⚙️ 发现残留的运行任务导致 UI 锁定，正在强制刷新页面重置状态...")
            page.reload()
            page.wait_for_load_state("networkidle")
            time.sleep(3)

        close_annoying_popups(page)

        # 点击输入框确保激活
        try:
            page.click(".monaco-editor", timeout=3000)
        except:
            page.mouse.click(500, 300)

        # 填入代码，并使用防冻结空格技巧
        page.keyboard.press("Meta+A" if os.name == "posix" and sys.platform == "darwin" else "Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5) 
        page.keyboard.insert_text(expression)
        
        # ==========================================
        # 🚀 第二重防御：强制触发 WQ 前端验证器
        # ==========================================
        page.keyboard.press("Escape")  # 关掉弹出的代码提示框
        page.mouse.click(10, 10)       # 点击网页左上角空白处，强行失去焦点
        time.sleep(4)                  # 必须耐心等待！复杂的公式 WQ 后台要算好几秒才能点亮按钮

        # ==========================================
        # 🚀 第三重防御：安全点击与状态穿透
        # ==========================================
        simulate_btn = page.locator("button:has-text('Simulate'), button:has-text('SIMULATE')").first
        cancel_btn = page.locator("button:has-text('Cancel')").first
        
        # 检查按钮是否依然被禁用
        if simulate_btn.is_visible() and not simulate_btn.is_enabled():
            logger.warning("⚙️ Simulate 按钮为灰色不可点状态！正在搜寻网页红条报错...")
            err_loc = page.locator("text=/Incompatible unit|Attempted to use|Unexpected character|Error|Syntax|Invalid/i").first
            if err_loc.is_visible():
                return {"error_msg": err_loc.inner_text(), "status": "error", "simulation_results": {}}
            return {"error_msg": "表达式存在严重语法错误，WQ 的 Simulate 按钮一直处于禁用状态。", "status": "error", "simulation_results": {}}

        try:
            # 🚀 致命修复：no_wait_after=True 告诉 Playwright 点完瞬间撒手，不要去验证网页有没有加载，防止引发假报错！
            simulate_btn.click(force=True, no_wait_after=True)
            time.sleep(1.5) # 给网页 1.5 秒的反应时间把按钮变成 Cancel
        except Exception as e:
            # 如果依然点出了异常，我们去检查屏幕上是不是已经出现了 Cancel 按钮
            if not cancel_btn.is_visible():
                return {"error_msg": f"点击回测按钮时发生未知异常: {str(e)}", "status": "error", "simulation_results": {}}
            # 如果 Cancel 出现了，说明其实点成功了！吃掉这个报错，继续往下走

        logger.info("⚙️ 开启智能监控 (等待进度条)...")
        time.sleep(3) 
        
        # 轮询监控报错或完成标志
        max_wait_seconds = 300
        poll_interval = 2
        for i in range(max_wait_seconds // poll_interval):
            # 1. 🚀 暴力抓报错红条/黄条：不再用长串正则，直接检查包含这些关键字的任意文本
            error_keywords = ["Incompatible unit", "Attempted to use", "Unexpected character", "Error", "Syntax", "Invalid"]
            for keyword in error_keywords:
                # Playwright 的 "text='xxx'" 表示包含该子串即可匹配，速度极快且稳定
                err_loc = page.locator(f"text='{keyword}'").first
                if err_loc.is_visible():
                    error_text = err_loc.inner_text()
                    logger.warning(f"⚙️ 抓取到网页红条报错: {error_text}")
                    return {"error_msg": f"平台运行错误: {error_text}", "status": "error", "simulation_results": {}}
            
            # 2. 抓真正的成功标志：出现 IS Summary，或者 Show test period 按钮
            success_locator = page.locator("text='IS Summary'").first
            hidden_btn = page.locator("button:has-text('Show test period')").first
            
            if success_locator.is_visible() or hidden_btn.is_visible():
                logger.info("⚙️ 侦测到回测完成标志，跳出等待！")
                break 
                
            time.sleep(poll_interval)
        else:
            logger.error(f"⚙️ 等待回测结果超时（已等待 {max_wait_seconds} 秒）！")
            return {"error_msg": "等待回测结果超时（可能是公式过于复杂，服务器计算缓慢）", "status": "error", "simulation_results": {}}

        # ==========================================================
        # 💡 解开折叠与数据盲抓
        # ==========================================================
        hidden_btn = page.locator("button:has-text('Show test period')").first
        if hidden_btn.is_visible():
            logger.info("🔍 发现数据被隐藏，正在自动点击展开...")
            hidden_btn.click(force=True)
            page.wait_for_timeout(2000)

        results = {"sharpe": 0.0, "turnover": 0.0, "fitness": 0.0, "fail_reasons": []}
        try:
            # 1. 提取核心指标 (依然使用上次极度成功的严格正则)
            page_text = page.inner_text("body")
            
            def extract_metric(metric_name, text):
                pattern = rf'{metric_name}\s+([+-]?\d+\.\d+)'
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    val = float(match.group(1))
                    end_idx = match.end()
                    if end_idx < len(text) and text[end_idx] == '%':
                        val = val / 100.0
                    return round(val, 4)
                return 0.0

            results["sharpe"] = extract_metric("Sharpe", page_text)
            results["turnover"] = extract_metric("Turnover", page_text)
            results["fitness"] = extract_metric("Fitness", page_text)
            
            # 2. 🚀 结构化解析 "IS Testing Status" 区域！
            fail_reasons = []
            try:
                # 找到包含所有 PASS/FAIL 的大框框，并抓取带有换行符的原始文字
                status_block = page.locator("text='IS Testing Status'").locator("..").inner_text(timeout=3000)
                
                # 状态机机制：只在读取到 X FAIL 下方的文字时才收录
                in_fail_section = False
                for line in status_block.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # 遇到 PASS, WARNING, PENDING 区域，关闭收集
                    if re.match(r'^\d+\s+(PASS|WARNING|PENDING)', line):
                        in_fail_section = False
                    # 遇到 FAIL 区域，开启收集
                    elif re.match(r'^\d+\s+FAIL', line):
                        in_fail_section = True
                    # 如果当前在 FAIL 区域内，且句子包含 cutoff
                    elif in_fail_section and 'cutoff' in line:
                        fail_reasons.append(line)
            except Exception as e:
                logger.debug(f"结构化读取状态栏失败: {e}")

            results["fail_reasons"] = list(set(fail_reasons))
            
            logger.info(f"⚙️ 抓取成功: 夏普={results['sharpe']}, 拒签原因数={len(results['fail_reasons'])}")
            if len(results['fail_reasons']) > 0:
                logger.debug(f"⚙️ 抓取到的真正拒签原因: {results['fail_reasons']}")
                
        except Exception as e:
            logger.warning(f"无法精准抓取指标数值: {str(e)}")
        # 绝对不关闭浏览器！直接返回！
        return {"simulation_results": results, "error_msg": None, "status": "simulated"}

    except Exception as e:
        logger.error(f"⚙️ Playwright 执行时出错: {str(e)}")
        # 只有真正崩溃时才考虑记录错误
        return {"error_msg": "页面崩溃或超时", "status": "error", "simulation_results": {}}