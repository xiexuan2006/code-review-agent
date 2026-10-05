"""Gradio Web 界面：与代码审查 Agent 聊天，展示工具调用过程。"""
import sys
from pathlib import Path

import gradio as gr

# 直接运行本文件时，把项目根目录加入模块搜索路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from factory import create_agent

# 演示用的示例代码（含典型 Bug），可一键填入
SAMPLE_CODE = '''import os

def get_user_data(user_id):
    users = {"1": "Alice", "2": "Bob"}
    return users[user_id]

def divide(a, b):
    return a / b

def read_config(path):
    f = open(path)
    data = f.read()
    return data

password = "admin123"
print(divide(10, 0))
'''

TITLE = "🔍 代码审查 Agent"
DESCRIPTION = (
    "基于通义千问 + 手写 ReAct Agent 循环的代码审查助手。"
    "支持：粘贴代码 / 指定文件路径审查，自动调用工具读取文件、"
    "执行 Python 代码验证 Bug，输出结构化审查报告。"
)


def build_ui():
    agent = create_agent()

    def chat_fn(message, history):
        """Gradio 流式回调：Agent 每次工具调用实时追加到聊天。"""
        history = history or []
        steps = []

        def on_step(stage, detail):
            if stage == "tool_call":
                steps.append(f"🔧 **工具调用** {detail}")

        answer = agent.run(message, on_step=on_step)
        if steps:
            process = "\n\n".join(steps)
            return f"{process}\n\n---\n\n{answer}"
        return answer

    with gr.Blocks(title=TITLE) as demo:
        gr.Markdown(f"# {TITLE}\n{DESCRIPTION}")
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(height=520, label="对话")
                msg = gr.Textbox(placeholder="粘贴代码或输入文件路径，例如：审查 examples/buggy_demo.py",
                                 label="输入", show_label=False)
                with gr.Row():
                    send_btn = gr.Button("发送", variant="primary")
                    clear_btn = gr.Button("清空会话")
            with gr.Column(scale=1):
                gr.Markdown("### 使用说明\n"
                            "1. 直接粘贴代码片段\n"
                            "2. 或输入项目内文件路径\n"
                            "3. Agent 会自动调用工具分析验证")
                fill_btn = gr.Button("填入示例代码")
                sample_box = gr.Textbox(label="示例代码", value=SAMPLE_CODE,
                                        lines=12, interactive=True)

        def user_send(message, history):
            return "", history + [{"role": "user", "content": message}]

        def bot_reply(history):
            message = history[-1]["content"]
            reply = chat_fn(message, history[:-1])
            history = history + [{"role": "assistant", "content": reply}]
            return history

        send_btn.click(user_send, [msg, chatbot], [msg, chatbot]) \
                .then(bot_reply, chatbot, chatbot)
        msg.submit(user_send, [msg, chatbot], [msg, chatbot]) \
           .then(bot_reply, chatbot, chatbot)
        clear_btn.click(lambda: agent.reset(), None, None) \
                 .then(lambda: [], None, chatbot)
        fill_btn.click(lambda s: s, sample_box, msg)

    return demo


if __name__ == "__main__":
    build_ui().launch(server_name="127.0.0.1", server_port=7860, inbrowser=True)
