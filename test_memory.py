"""验证多轮上下文记忆：第一轮让 LLM 记住信息，第二轮检验是否记得。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from factory import create_agent

agent = create_agent()

print("=== 第 1 轮：让 Agent 记住信息 ===")
a1 = agent.run("请记住：这个项目的秘密代号是 PANDA-42。先简单回复收到即可。")
print(a1[:200])

print("\n=== 第 2 轮：换话题后提问，检验记忆 ===")
a2 = agent.run("我刚才告诉你的秘密代号是什么？只回答代号本身。")
print(a2[:200])
assert "PANDA-42" in a2, f"记忆失败，回答: {a2}"

print("\n=== 第 3 轮：验证 reset 后记忆清空 ===")
agent.reset()
a3 = agent.run("我之前告诉过你一个秘密代号吗？如果对话里没有，请回答'没有'。")
print(a3[:150])
assert "PANDA-42" not in a3, "reset 后记忆未清空"

print("\n多轮记忆与重置验证通过 ✔")
