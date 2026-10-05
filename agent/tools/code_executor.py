"""代码执行工具：在子进程沙箱中运行 Python 代码，验证 Bug 是否真实存在。"""
import subprocess
import sys
import tempfile
import os

from .base import Tool

TIMEOUT_SECONDS = 15
MAX_OUTPUT = 5000  # 输出截断上限，防止撑爆上下文


class RunPythonTool(Tool):
    """执行 Python 代码片段并返回 stdout/stderr。"""

    name = "run_python_code"
    description = (
        "在独立子进程中执行一段 Python 代码，返回标准输出与错误信息。"
        "用途：验证审查中发现的 Bug 是否真实存在（如运行报错、复现除零等），"
        "或运行小的测试脚本验证推断。每次执行是独立的，变量不会保留。"
        "注意：不要执行有副作用的代码（删除文件、网络请求等）。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "要执行的 Python 代码"},
        },
        "required": ["code"],
    }

    def execute(self, code: str) -> str:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, tmp_path],
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
                encoding="utf-8",
                errors="replace",
            )
            output = result.stdout or ""
            if result.stderr:
                output += "\n[stderr]\n" + result.stderr
            output += f"\n[退出码] {result.returncode}"
        except subprocess.TimeoutExpired:
            output = f"错误：代码执行超时（>{TIMEOUT_SECONDS}s），已终止"
        finally:
            os.unlink(tmp_path)

        if len(output) > MAX_OUTPUT:
            output = output[:MAX_OUTPUT] + f"\n...(输出过长，已截断，共 {len(output)} 字符)"
        return output or "（无输出）"
