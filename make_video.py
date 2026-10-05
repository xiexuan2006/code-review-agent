"""将截图素材合成为演示视频：1920x1080 MP4，含标题卡、步骤字幕、结尾卡。

输出: 演示视频.mp4（约 58 秒）
"""
import io
import sys
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont

BASE = Path(__file__).resolve().parent
FRAMES = BASE / "video_frames"
OUT = BASE / "演示视频.mp4"

W, H = 1920, 1080
FPS = 10
BAR_H = 130
DARK = (26, 35, 50)
ACCENT = (255, 122, 0)

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"


def font(size, bold=True):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REG, size)


def text_center(draw, y, text, f, fill=(255, 255, 255)):
    w = draw.textlength(text, font=f)
    draw.text(((W - w) / 2, y), text, font=f, fill=fill)


def card(lines):
    """生成标题卡/结尾卡（深蓝底 + 多行文字）。"""
    img = Image.new("RGB", (W, H), DARK)
    d = ImageDraw.Draw(img)
    d.rectangle([0, H - 14, W, H], fill=ACCENT)
    n = len(lines)
    y = H / 2 - n * 60
    for text, size, bold in lines:
        f = font(size, bold)
        if bold:
            text_center(d, y - 8, text, f)
        else:
            text_center(d, y - 8, text, f, fill=(180, 195, 210))
        y += size + 34
    return img


def frame_with_caption(png_name, caption, sub=None):
    """截图 + 底部字幕条，铺满画布。"""
    img = Image.new("RGB", (W, H), (240, 242, 245))
    d = ImageDraw.Draw(img)
    shot = Image.open(FRAMES / png_name).convert("RGB")
    # 截图区域：字幕条上方全部利用，保持宽高比
    avail_w, avail_h = W - 80, H - BAR_H - 50
    scale = min(avail_w / shot.width, avail_h / shot.height)
    shot = shot.resize((int(shot.width * scale), int(shot.height * scale)))
    x = (W - shot.width) // 2
    y = (H - BAR_H - shot.height) // 2 - 10
    d.rectangle([x - 2, y - 2, x + shot.width + 2, y + shot.height + 2],
                outline=(200, 205, 212), width=2)
    img.paste(shot, (x, y))
    # 字幕条
    d.rectangle([0, H - BAR_H, W, H], fill=DARK)
    text_center(d, H - BAR_H + (BAR_H - 52) // 2 - 6, caption, font(44))
    if sub:
        text_center(d, H - BAR_H + 74, sub, font(26, bold=False), fill=(170, 182, 198))
    return img


TITLE = card([
    ("代码审查 Agent", 92, True),
    ("基于通义千问的手写 ReAct Agent", 44, False),
    ("输入 → 推理 → 工具调用 → 输出", 36, False),
])
END = card([
    ("核心实现", 60, True),
    ("手写 ReAct Agent 循环 · 3 种工具 · 上下文记忆", 38, False),
    ("错误重试 · 子进程沙箱 · Gradio / CLI 双入口", 38, False),
    ("技术栈：Python + 通义千问 + Gradio", 32, False),
])

STEPS = [
    ("step1_home.png", "Gradio 交互界面", "支持粘贴代码片段或指定文件路径进行审查", 6),
    ("step2_filled.png", "填入待审查代码", "示例代码包含除零错误等典型问题", 7),
    ("step3_reply_top.png", "Agent 自主推理与工具调用", "调用 run_python_code 实际执行代码，验证 Bug 真实存在", 10),
    ("step4_report.png", "输出结构化审查报告", "严重程度 · 位置行号 · 修复建议 · 验证状态", 12),
    ("step5_fix.png", "给出修复后的代码片段", "针对每个严重问题提供可落地的改进方案", 9),
    ("step6_cleared.png", "支持多轮会话与上下文记忆", "可针对同一代码继续追问，随时清空开启新会话", 6),
]

writer = imageio.get_writer(str(OUT), fps=FPS, codec="libx264",
                            macro_block_size=1, pixelformat="yuv420p",
                            quality=8)


def append(img, seconds):
    arr = np.asarray(img)
    for _ in range(int(seconds * FPS)):
        writer.append_data(arr)


append(TITLE, 4)
for name, cap, sub, sec in STEPS:
    append(frame_with_caption(name, cap, sub), sec)
append(END, 6)
writer.close()

size_mb = OUT.stat().st_size / 1024 / 1024
total = 4 + sum(s[3] for s in STEPS) + 6
print(f"视频生成完成: {OUT.name}  时长 {total}s  大小 {size_mb:.1f}MB")
