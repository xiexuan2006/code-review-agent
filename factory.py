"""应用工厂：组装 LLM、记忆、工具与 Agent，供 CLI 和 Web 复用。"""
import os

from dotenv import load_dotenv

from agent.agent import CodeReviewAgent
from agent.llm import LLMClient
from agent.memory import Memory
from agent.tools.base import ToolRegistry
from agent.tools.code_executor import RunPythonTool
from agent.tools.file_reader import ListFilesTool, ReadFileTool
from prompts.system import SYSTEM_PROMPT


def create_agent() -> CodeReviewAgent:
    """创建配置完整的代码审查 Agent 实例。"""
    load_dotenv()  # 从 .env 读取配置

    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    model = os.getenv("LLM_MODEL", "qwen-plus")
    base_url = os.getenv(
        "LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    llm = LLMClient(api_key=api_key, model=model, base_url=base_url)
    memory = Memory(system_prompt=SYSTEM_PROMPT, max_messages=40)

    tool_registry = ToolRegistry()
    tool_registry.register(ListFilesTool())
    tool_registry.register(ReadFileTool())
    tool_registry.register(RunPythonTool())

    return CodeReviewAgent(llm=llm, memory=memory, tool_registry=tool_registry)
