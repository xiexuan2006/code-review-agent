"""冒烟测试：验证工具系统与记忆模块（不依赖 API Key）。

运行: .venv/Scripts/python.exe test_smoke.py
"""
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import py_compile
import pathlib

# 1. 语法检查所有模块
for f in pathlib.Path(".").rglob("*.py"):
    if ".venv" not in str(f):
        py_compile.compile(str(f), doraise=True)
print("[通过] 语法检查")

# 2. 工具注册表
from agent.tools.file_reader import ListFilesTool, ReadFileTool
from agent.tools.code_executor import RunPythonTool
from agent.tools.base import ToolRegistry

reg = ToolRegistry()
reg.register(ListFilesTool())
reg.register(ReadFileTool())
reg.register(RunPythonTool())
names = [t["function"]["name"] for t in reg.schemas()]
assert names == ["list_files", "read_file", "run_python_code"], names
print(f"[通过] 工具注册: {names}")

# 3. list_files
r1 = reg.execute("list_files", '{"directory": "."}')
assert "agent" in r1 and "main.py" in r1
print("[通过] list_files")

# 4. read_file（带行号）
r2 = reg.execute("read_file", '{"path": "examples/buggy_demo.py"}')
assert "   1 |" in r2
print("[通过] read_file")

# 5. read_file 异常路径
r2b = reg.execute("read_file", '{"path": "不存在.py"}')
assert r2b.startswith("错误")
print("[通过] read_file 错误处理")

# 6. 代码执行：正常输出
r3 = reg.execute("run_python_code", '{"code": "print(21*2)"}')
assert "42" in r3 and "退出码] 0" in r3
print("[通过] run_python_code 正常执行")

# 7. 代码执行：除零错误复现（验证 Bug 场景）
r4 = reg.execute("run_python_code", '{"code": "print(1/0)"}')
assert "ZeroDivisionError" in r4
print("[通过] run_python_code 捕获异常")

# 8. 工具 JSON 参数解析失败
r5 = reg.execute("run_python_code", "{bad json}")
assert "解析失败" in r5
print("[通过] 工具参数容错")

# 9. Memory 裁剪逻辑
from agent.memory import Memory

m = Memory(system_prompt="sys", max_messages=4)
for i in range(6):
    m.add({"role": "user", "content": f"msg{i}"})
msgs = m.get_messages()
assert msgs[0]["role"] == "system" and len(msgs) == 5
assert msgs[1]["content"] == "msg2"
print("[通过] Memory 裁剪")

# 10. Memory 裁剪后首条不能是 tool 消息
m2 = Memory(system_prompt="sys", max_messages=3)
m2.add({"role": "user", "content": "q1"})
m2.add({"role": "assistant", "content": "", "tool_calls": [{"id": "1", "type": "function", "function": {"name": "x", "arguments": "{}"}}]})
m2.add({"role": "tool", "tool_call_id": "1", "content": "r1"})
m2.add({"role": "tool", "tool_call_id": "2", "content": "r2"})
m2.add({"role": "assistant", "content": "done"})
msgs2 = m2.get_messages()
assert msgs2[1]["role"] != "tool"
print("[通过] Memory 裁剪协议安全")

# 11. Agent 循环防死（mock LLM，不调真实 API）
from agent.agent import CodeReviewAgent


class MockLLM:
    def chat(self, messages, tools=None, temperature=0.2):
        class M:
            role = "assistant"
            content = "最终回答"
            tool_calls = None

        return M()


agent = CodeReviewAgent(llm=MockLLM(), memory=Memory(system_prompt="s"), tool_registry=reg)
assert agent.run("测试") == "最终回答"
agent.reset()
print("[通过] Agent 循环（Mock LLM）")

print("\n全部 11 项冒烟测试通过 ✔")
