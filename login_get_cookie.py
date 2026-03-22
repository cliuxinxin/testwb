from playwright.sync_api import sync_playwright
import time


def login_and_save_cookie():
    print("启动浏览器，请在弹出的窗口中手动登录 WorldQuant Brain...")
    with sync_playwright() as p:
        # 必须是 headless=False，让你自己输入账号密码或二次验证
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto("https://platform.worldquantbrain.com/sign-in")

        print("等待登录完成 (等待 URL 变成主页，你有 120 秒时间)...")
        # 登录成功，保存全部 Cookie 等会话状态
        page.wait_for_url("**/simulate**", timeout=120000)

        context.storage_state(path="wq_cookies.json")
        print(
            "✅ 成功提取 Cookie！已保存为 wq_cookies.json。你现在可以启动自动化系统了。"
        )
        browser.close()


if __name__ == "__main__":
    login_and_save_cookie()
