"""端到端验证：Agent 真实调用 LLM + 工具，审查示例代码。运行一次约消耗几千 token。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from factory import create_agent

agent = create_agent()
steps = []


def on_step(stage, detail):
    if stage == "tool_call":
        print(f"\n>>> [工具调用] {detail[:150]}")
    steps.append((stage, detail))


answer = agent.run("请审查 examples/buggy_demo.py 这个文件，输出完整审查报告", on_step=on_step)

print("\n" + "=" * 60)
print("最终审查报告:")
print("=" * 60)
print(answer)

tool_calls = [s for s in steps if s[0] == "tool_call"]
print(f"\n[统计] 共发生 {len(tool_calls)} 次工具调用: "
      f"{[s[1].split('(')[0] for s in tool_calls]}")
assert len(tool_calls) >= 1, "Agent 未调用任何工具，循环可能异常"
assert len(answer) > 200, "最终回答过短"
print("\n端到端验证通过 ✔")
