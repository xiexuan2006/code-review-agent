"""演示视频素材采集：Playwright 驱动本机 Edge，实录 Web 界面完整审查流程并逐步截图。

前置: web 服务已运行在 http://127.0.0.1:7860
输出: video_frames/step1..step6 截图
"""
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "video_frames"
FRAMES.mkdir(exist_ok=True)
PROFILE = BASE / ".edge_profile"
CACHE = BASE / ".edge_cache"

DEMO_TEXT = """请审查这段代码：
def divide(a, b):
    return a / b

result = divide(10, 0)
print(result)"""


def shot(page, name):
    page.screenshot(path=str(FRAMES / f"{name}.png"))
    print(f"已截图: {name}.png", flush=True)


def scroll_chat(page, ratio):
    """把聊天区滚动容器滚到指定比例位置 (0=顶部, 1=底部)。"""
    page.evaluate(
        """(ratio) => {
            const divs = [...document.querySelectorAll('div')];
            const holder = divs.find(e =>
                e.scrollHeight > e.clientHeight + 100 &&
                e.textContent.includes('总体评价'));
            if (holder) holder.scrollTop = (holder.scrollHeight - holder.clientHeight) * ratio;
        }""",
        ratio,
    )
    page.wait_for_timeout(600)


def wait_reply_stable(page, timeout_s=240):
    """等待 Agent 回复完成：出现'总体评价'且页面文本连续两次采样不再变化。"""
    page.wait_for_selector("text=总体评价", timeout=timeout_s * 1000)
    prev = ""
    for _ in range(timeout_s):
        page.wait_for_timeout(3000)
        cur = page.evaluate("() => document.body.innerText")
        if cur == prev:
            return
        prev = cur
    raise TimeoutError("回复文本长期不稳定")


with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE),
        channel="msedge",
        headless=True,
        args=["--no-first-run", "--disable-gpu"],
        viewport={"width": 1440, "height": 900},
        device_scale_factor=2,
    )
    page = browser.new_page()

    # step1: 首页
    page.goto("http://127.0.0.1:7860", timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)
    shot(page, "step1_home")

    # step2: 填入待审查代码
    box = page.locator('textarea[placeholder*="粘贴代码"]')
    box.fill(DEMO_TEXT)
    page.wait_for_timeout(800)
    shot(page, "step2_filled")

    # 发送并等待审查报告生成
    page.get_by_role("button", name="发送").click()
    print("已发送，等待 Agent 审查完成（最长 4 分钟）...", flush=True)
    wait_reply_stable(page)
    page.wait_for_timeout(2000)  # 等 Markdown 渲染稳定

    # step3/4/5: 回复不同区域（先滚顶、再中、再底）
    scroll_chat(page, 0.0)
    shot(page, "step3_reply_top")
    scroll_chat(page, 0.45)
    shot(page, "step4_report")
    scroll_chat(page, 1.0)
    shot(page, "step5_fix")

    # step6: 清空会话
    page.get_by_role("button", name="清空会话").click()
    page.wait_for_timeout(2000)
    shot(page, "step6_cleared")

    browser.close()

print("\n素材采集完成 ✔ 共 6 帧")
