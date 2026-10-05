"""Agent 核心循环（ReAct 模式）：

    输入 → LLM 推理 → 工具调用 → 观察结果 → 再推理 → ... → 最终输出
"""
from .llm import LLMClient
from .memory import Memory
from .tools.base import ToolRegistry

MAX_ITERATIONS = 10  # 单次提问最多允许的工具调用轮数，防止死循环


class CodeReviewAgent:
    """代码审查 Agent：组合 LLM、记忆与工具，驱动推理-行动循环。"""

    def __init__(self, llm: LLMClient, memory: Memory, tool_registry: ToolRegistry):
        self.llm = llm
        self.memory = memory
        self.tools = tool_registry

    def run(self, user_input: str, on_step=None) -> str:
        """处理一轮用户输入，返回最终回答。

        Args:
            user_input: 用户消息
            on_step: 可选回调 on_step(stage, detail)，用于 Web 界面展示中间过程

        Returns:
            Agent 的最终文本回答
        """
        self.memory.add({"role": "user", "content": user_input})

        for iteration in range(MAX_ITERATIONS):
            assistant_message = self.llm.chat(
                messages=self.memory.get_messages(),
                tools=self.tools.schemas(),
            )

            # 情况一：LLM 决定调用工具
            if getattr(assistant_message, "tool_calls", None):
                self.memory.add(assistant_message)  # 先记录含 tool_calls 的助手消息
                for tool_call in assistant_message.tool_calls:
                    name = tool_call.function.name
                    arguments = tool_call.function.arguments
                    if on_step:
                        on_step("tool_call", f"调用工具 {name}({arguments})")
                    result = self.tools.execute(name, arguments)
                    if on_step:
                        on_step("tool_result", f"{name} 返回:\n{result[:500]}")
                    # 工具结果以 role=tool 消息回填，供 LLM 下轮观察
                    self.memory.add({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
                continue  # 带着观察结果回到推理步骤

            # 情况二：LLM 给出最终回答，循环结束
            answer = assistant_message.content or ""
            self.memory.add({"role": "assistant", "content": answer})
            return answer

        # 超过最大轮数的保护：避免无限工具调用
        fallback = "抱歉，本次任务的工具调用轮数达到上限，已中止。请尝试更具体的问题。"
        self.memory.add({"role": "assistant", "content": fallback})
        return fallback

    def reset(self):
        """清空记忆，开启新会话。"""
        self.memory.clear()
