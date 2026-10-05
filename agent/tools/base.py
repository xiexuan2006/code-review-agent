"""工具基类与注册表。

每个工具由三部分组成：
- name / description / parameters：OpenAI function calling 的 JSON Schema
- execute：实际执行函数，返回字符串结果
"""
import json


class Tool:
    """工具基类。"""

    name: str = ""
    description: str = ""
    parameters: dict = {}  # JSON Schema 格式的参数定义

    def execute(self, **kwargs) -> str:
        raise NotImplementedError

    @property
    def schema(self) -> dict:
        """转换为 OpenAI function calling 的工具定义。"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


class ToolRegistry:
    """工具注册表：统一管理工具的注册、查找与执行。"""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"工具重复注册: {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict]:
        """返回所有工具的 JSON Schema 定义，供 LLM 选择调用。"""
        return [tool.schema for tool in self._tools.values()]

    def execute(self, name: str, arguments: str | dict) -> str:
        """按名称执行工具，统一捕获异常避免 Agent 循环崩溃。

        Args:
            name: 工具名
            arguments: LLM 生成的参数（JSON 字符串或 dict）

        Returns:
            工具执行结果（字符串），失败时返回错误信息
        """
        tool = self._tools.get(name)
        if tool is None:
            return f"错误：未找到工具 '{name}'，可用工具: {list(self._tools)}"
        try:
            args = json.loads(arguments) if isinstance(arguments, str) else arguments
        except json.JSONDecodeError as e:
            return f"错误：工具参数 JSON 解析失败: {e}"
        try:
            return tool.execute(**args)
        except TypeError as e:
            return f"错误：工具参数不匹配: {e}"
        except Exception as e:
            # 工具报错不中断 Agent，把错误交给 LLM 自行调整
            return f"工具执行出错: {type(e).__name__}: {e}"
