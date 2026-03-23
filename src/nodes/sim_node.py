# src/nodes/sim_node.py
import json
import time
import os
import sys
import re
from typing import Any, List, Optional

from playwright.sync_api import sync_playwright
from src.state import AlphaState
from src.logger import logger

COOKIE_PATH = "wq_cookies.json"
RESPONSE_URL_HINTS = ("sim", "alpha", "backtest", "result", "submit", "check")
ERROR_PAYLOAD_KEYS = ("error", "errors", "message", "detail", "reason", "title")
SUCCESS_SELECTORS = [
    "text='IS Summary'",
    "button:has-text('Show test period')",
]
NEW_SIMULATION_TAB_SELECTORS = [
    "#root > div > div.editor > div.editor-tabs > div.editor-tabs__new-tab-element > div > div",
    ".editor-tabs__new-tab-element",
]
TEST_PERIOD_BUTTON_SELECTORS = [
    "#root > div > div.editor > div.editor-instance > div.editor-panels > div > div.SplitPane2 > div > div > div.editor-bottom-bar-right.editor-bottom-bar-right--has-results > div.editor-bottom-bar__bottom-buttons > button.button.button--primary",
    "#root > div > div.editor > div.editor-instance > div.editor-panels > div > div.SplitPane2 > div > div > div.editor-bottom-bar-right.editor-bottom-bar-right--has-results > div.editor-bottom-bar__bottom-buttons > button.button.button--primary > span",
    "button:has-text('Show test period')",
]
PREFERRED_ERROR_SELECTORS = [
    ".editor-code__flash-message .flash-messages__content li div",
    ".editor-code__flash-message .flash-messages__content li",
    ".editor-code__flash-message [role='alert']",
]
UI_FEEDBACK_SELECTORS = [
    "[role='alert']",
    "[aria-live='assertive']",
    "[class*='toast']",
    "[class*='Toast']",
    "[class*='snackbar']",
    "[class*='notification']",
    "[class*='alert']",
    "[data-testid*='alert']",
    "[data-testid*='error']",
]
IGNORED_UI_TEXT_PATTERNS = [
    r"^Select/add tags$",
    r"^Description$",
    r"^Currently 'anonymous'$",
    r"^None$",
    r"^Simulate an alpha to view the results here\.$",
]
ERROR_KEYWORD_FALLBACKS = [
    "Incompatible unit",
    "Attempted to use",
    "Unexpected character",
    "Error",
    "Syntax",
    "Invalid",
]


def normalize_message(text: str, limit: int = 300) -> str:
    normalized = " ".join((text or "").split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3] + "..."


def should_ignore_ui_message(text: str) -> bool:
    normalized = normalize_message(text)
    if not normalized:
        return True
    return any(re.fullmatch(pattern, normalized, re.IGNORECASE) for pattern in IGNORED_UI_TEXT_PATTERNS)


def extract_error_message_from_payload(payload: Any) -> Optional[str]:
    if isinstance(payload, dict):
        for key in ERROR_PAYLOAD_KEYS:
            if key in payload:
                message = extract_error_message_from_payload(payload[key])
                if message:
                    return message
        for value in payload.values():
            message = extract_error_message_from_payload(value)
            if message:
                return message
        return None

    if isinstance(payload, list):
        for item in payload:
            message = extract_error_message_from_payload(item)
            if message:
                return message
        return None

    if isinstance(payload, str):
        message = normalize_message(re.sub(r"<[^>]+>", " ", payload))
        return message or None

    return None


def payload_indicates_error(payload: Any) -> bool:
    if isinstance(payload, dict):
        lowered_keys = {str(key).lower() for key in payload.keys()}
        if lowered_keys.intersection({"error", "errors", "detail", "reason"}):
            return True
        status_value = str(payload.get("status", "")).lower()
        if status_value in {"error", "failed", "invalid"}:
            return True
        success_value = payload.get("success")
        if success_value is False:
            return True
        return any(payload_indicates_error(value) for value in payload.values())

    if isinstance(payload, list):
        return any(payload_indicates_error(item) for item in payload)

    return False


def capture_ui_feedback_messages(page) -> List[str]:
    messages = []

    for selector in PREFERRED_ERROR_SELECTORS:
        try:
            locator = page.locator(selector)
            count = min(locator.count(), 5)
            for idx in range(count):
                candidate = normalize_message(locator.nth(idx).inner_text())
                if candidate and not should_ignore_ui_message(candidate):
                    messages.append(candidate)
        except Exception as exc:
            logger.debug(f"读取首选错误 selector 失败 ({selector}): {exc}")

    if messages:
        deduped = []
        seen = set()
        for message in messages:
            if message in seen:
                continue
            deduped.append(message)
            seen.add(message)
        return deduped[:5]

    try:
        messages = page.evaluate(
            """selectors => {
                const unique = new Map();

                const parseRgb = (value) => {
                    const match = value && value.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)/i);
                    if (!match) {
                        return null;
                    }
                    return { r: Number(match[1]), g: Number(match[2]), b: Number(match[3]) };
                };

                const isVisible = (element) => {
                    if (!element) {
                        return false;
                    }
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    return (
                        style.display !== "none" &&
                        style.visibility !== "hidden" &&
                        Number(style.opacity || 1) > 0 &&
                        rect.width > 0 &&
                        rect.height > 0
                    );
                };

                const scoreElement = (element, text) => {
                    const style = window.getComputedStyle(element);
                    const rect = element.getBoundingClientRect();
                    const className = (typeof element.className === "string" ? element.className : "").toLowerCase();
                    const role = (element.getAttribute("role") || "").toLowerCase();
                    const live = (element.getAttribute("aria-live") || "").toLowerCase();
                    let score = 0;

                    if (role === "alert") score += 40;
                    if (live === "assertive") score += 20;
                    if (/toast|snackbar|notification|alert/.test(className)) score += 25;
                    if (style.position === "fixed" || style.position === "sticky") score += 15;
                    if (rect.top > window.innerHeight * 0.55) score += 8;

                    const bg = parseRgb(style.backgroundColor || "");
                    const fg = parseRgb(style.color || "");
                    if (bg && bg.r > bg.g + 25 && bg.r > bg.b + 25) score += 20;
                    if (fg && fg.r > fg.g + 25 && fg.r > fg.b + 25) score += 8;

                    if (text.length >= 8 && text.length <= 280) score += 10;
                    return score;
                };

                for (const selector of selectors) {
                    for (const element of document.querySelectorAll(selector)) {
                        if (!isVisible(element)) continue;
                        const text = (element.innerText || element.textContent || "").replace(/\\s+/g, " ").trim();
                        if (text.length < 5) continue;
                        const score = scoreElement(element, text);
                        const previous = unique.get(text);
                        if (!previous || score > previous.score) {
                            unique.set(text, { text, score });
                        }
                    }
                }

                return Array.from(unique.values())
                    .sort((a, b) => b.score - a.score)
                    .slice(0, 5)
                    .map((item) => item.text);
            }""",
            UI_FEEDBACK_SELECTORS,
        )
    except Exception as exc:
        logger.debug(f"结构化读取 UI 反馈失败: {exc}")
        return []

    results = []
    for message in messages:
        normalized = normalize_message(message)
        if normalized and not should_ignore_ui_message(normalized):
            results.append(normalized)
    return results


def get_new_ui_error(page, baseline_messages: Optional[List[str]] = None) -> Optional[str]:
    baseline = set(baseline_messages or [])
    for message in capture_ui_feedback_messages(page):
        if message not in baseline:
            return message
    return None


def extract_keyword_fallback_error(page) -> Optional[str]:
    for keyword in ERROR_KEYWORD_FALLBACKS:
        try:
            err_loc = page.locator(f"text='{keyword}'").first
            if err_loc.is_visible():
                return normalize_message(err_loc.inner_text())
        except Exception:
            continue
    return None


# ==========================================================
# 💡 全局单例：浏览器管家 (实现浏览器复用，不重复开关)
# ==========================================================
class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.recent_api_errors = []

    def reset(self):
        for resource_name in ("page", "context", "browser"):
            resource = getattr(self, resource_name)
            if resource is None:
                continue
            try:
                resource.close()
            except Exception as exc:
                logger.debug(f"关闭 {resource_name} 时失败: {exc}")

        if self.playwright is not None:
            try:
                self.playwright.stop()
            except Exception as exc:
                logger.debug(f"停止 Playwright 时失败: {exc}")

        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.recent_api_errors = []

    def _is_page_healthy(self):
        if not all([self.playwright, self.browser, self.context, self.page]):
            return False
        try:
            return not self.page.is_closed()
        except Exception:
            return False

    def clear_runtime_events(self):
        self.recent_api_errors = []

    def pop_recent_api_error(self) -> Optional[str]:
        if not self.recent_api_errors:
            return None
        return self.recent_api_errors.pop()

    def _remember_api_error(self, message: str) -> None:
        normalized = normalize_message(message)
        if not normalized:
            return
        if self.recent_api_errors and self.recent_api_errors[-1] == normalized:
            return
        self.recent_api_errors.append(normalized)
        self.recent_api_errors = self.recent_api_errors[-5:]

    def _handle_response(self, response) -> None:
        try:
            if response.request.resource_type not in {"xhr", "fetch"}:
                return

            url = response.url.lower()
            if not any(hint in url for hint in RESPONSE_URL_HINTS):
                return

            status = response.status
            headers = response.headers or {}
            content_type = headers.get("content-type", "").lower()
            message = None

            if "json" in content_type:
                try:
                    payload = response.json()
                    if status >= 400 or payload_indicates_error(payload):
                        message = extract_error_message_from_payload(payload)
                except Exception:
                    body = response.text()
                    try:
                        payload = json.loads(body)
                        if status >= 400 or payload_indicates_error(payload):
                            message = extract_error_message_from_payload(payload)
                    except Exception:
                        if status >= 400:
                            message = normalize_message(body)
            elif status >= 400 or "text" in content_type:
                message = normalize_message(response.text())

            if status >= 400 or message:
                final_message = message or f"平台接口返回异常，HTTP {status}"
                self._remember_api_error(final_message)
        except Exception as exc:
            logger.debug(f"解析平台接口响应失败: {exc}")

    def _launch(self):
        logger.info("🚀 启动新的浏览器会话...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False, args=["--start-maximized"]
        )
        self.context = self.browser.new_context(
            storage_state=COOKIE_PATH, viewport={"width": 1920, "height": 1080}
        )
        self.page = self.context.new_page()
        self.page.on("response", self._handle_response)

    def get_page(self):
        if not self._is_page_healthy():
            if any([self.playwright, self.browser, self.context, self.page]):
                logger.warning("⚙️ 检测到浏览器上下文失效，正在重建...")
            self.reset()
            self._launch()

        try:
            if "/simulate" not in self.page.url:
                logger.debug("正在打开 WQ 模拟页...")
                self.page.goto(
                    "https://platform.worldquantbrain.com/simulate", timeout=60000
                )
                self.page.wait_for_load_state("networkidle")
                time.sleep(3)
        except Exception:
            logger.warning("⚙️ 浏览器页面健康检查失败，正在重建会话...", exc_info=True)
            self.reset()
            self._launch()
            self.page.goto(
                "https://platform.worldquantbrain.com/simulate", timeout=60000
            )
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


def read_runtime_error(page, baseline_ui_messages: Optional[List[str]] = None) -> Optional[str]:
    api_error = browser_manager.pop_recent_api_error()
    if api_error:
        return api_error

    ui_error = get_new_ui_error(page, baseline_ui_messages)
    if ui_error:
        return ui_error

    return extract_keyword_fallback_error(page)


def is_any_selector_visible(page, selectors: List[str]) -> bool:
    for selector in selectors:
        try:
            if page.locator(selector).first.is_visible():
                return True
        except Exception:
            continue
    return False


def click_test_period_button(page) -> bool:
    for selector in TEST_PERIOD_BUTTON_SELECTORS:
        try:
            locator = page.locator(selector).first
            if not locator.is_visible():
                continue
            logger.info(f"🔍 点击 Show test period 按钮: {selector}")
            locator.click(force=True)
            page.wait_for_timeout(2000)
            return True
        except Exception as exc:
            logger.debug(f"点击 Show test period 失败 ({selector}): {exc}")
    return False


def open_new_simulation_tab(page) -> bool:
    for selector in NEW_SIMULATION_TAB_SELECTORS:
        try:
            locator = page.locator(selector).first
            if not locator.is_visible():
                continue
            logger.info(f"🗂️ 新建 simulation 页签: {selector}")
            locator.click(force=True)
            page.wait_for_timeout(1500)
            return True
        except Exception as exc:
            logger.debug(f"点击新建页签失败 ({selector}): {exc}")
    return False


def expand_test_period_results(page) -> None:
    if not is_any_selector_visible(page, TEST_PERIOD_BUTTON_SELECTORS):
        return

    logger.info("⏳ 回测完成，等待结果区稳定后再展开 test period...")
    page.wait_for_timeout(3000)

    if not click_test_period_button(page):
        return

    for _ in range(10):
        if is_any_selector_visible(page, ["text='IS Summary'", "text='IS Testing Status'"]):
            return
        page.wait_for_timeout(500)

def run_simulation(state: AlphaState) -> dict:
    expression = state.get("expression")
    logger.info(f"⚙️ [Node: Simulator] 准备在常驻浏览器中执行回测...")

    if not os.path.exists(COOKIE_PATH):
        return {"status": "error", "error_msg": "Missing wq_cookies.json", "simulation_results": {}}

    try:
        page = browser_manager.get_page()
        open_new_simulation_tab(page)
        close_annoying_popups(page)
        page.wait_for_timeout(1000)

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
        browser_manager.clear_runtime_events()
        baseline_ui_messages = capture_ui_feedback_messages(page)

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
            runtime_error = read_runtime_error(page, baseline_ui_messages)
            if runtime_error:
                return {"error_msg": runtime_error, "status": "error", "simulation_results": {}}
            return {"error_msg": "表达式存在严重语法错误，WQ 的 Simulate 按钮一直处于禁用状态。", "status": "error", "simulation_results": {}}

        try:
            # 🚀 致命修复：no_wait_after=True 告诉 Playwright 点完瞬间撒手，不要去验证网页有没有加载，防止引发假报错！
            simulate_btn.click(force=True, no_wait_after=True)
            time.sleep(1.5) # 给网页 1.5 秒的反应时间把按钮变成 Cancel
        except Exception as e:
            # 如果依然点出了异常，我们去检查屏幕上是不是已经出现了 Cancel 按钮
            if not cancel_btn.is_visible():
                runtime_error = read_runtime_error(page, baseline_ui_messages)
                if runtime_error:
                    return {"error_msg": runtime_error, "status": "error", "simulation_results": {}}
                return {"error_msg": f"点击回测按钮时发生未知异常: {str(e)}", "status": "error", "simulation_results": {}}
            # 如果 Cancel 出现了，说明其实点成功了！吃掉这个报错，继续往下走

        logger.info("⚙️ 开启智能监控 (等待进度条)...")
        time.sleep(3) 
        
        # 轮询监控报错或完成标志
        max_wait_seconds = 300
        poll_interval = 2
        for i in range(max_wait_seconds // poll_interval):
            runtime_error = read_runtime_error(page, baseline_ui_messages)
            if runtime_error:
                logger.warning(f"⚙️ 抓取到平台结构化报错: {runtime_error}")
                return {"error_msg": f"平台运行错误: {runtime_error}", "status": "error", "simulation_results": {}}

            success_detected = is_any_selector_visible(page, SUCCESS_SELECTORS)

            if success_detected:
                logger.info("⚙️ 侦测到回测完成标志，跳出等待！")
                break 
                
            time.sleep(poll_interval)
        else:
            logger.error(f"⚙️ 等待回测结果超时（已等待 {max_wait_seconds} 秒）！")
            return {"error_msg": "等待回测结果超时（可能是公式过于复杂，服务器计算缓慢）", "status": "error", "simulation_results": {}}

        # ==========================================================
        # 💡 解开折叠与数据盲抓
        # ==========================================================
        expand_test_period_results(page)

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
        browser_manager.reset()
        # 只有真正崩溃时才考虑记录错误
        return {"error_msg": "页面崩溃或超时", "status": "error", "simulation_results": {}}
