"""上下文记忆：维护多轮对话历史，超限时裁剪早期轮次以控制 token。"""
import json


class Memory:
    """对话记忆管理。

    保存 system 提示 + 全部对话轮次；当消息条数超过上限时，
    保留 system 提示和最近的消息，并保证首条消息为 user 角色。
    """

    def __init__(self, system_prompt: str, max_messages: int = 40):
        self.system_message = {"role": "system", "content": system_prompt}
        self.max_messages = max_messages
        self.history: list[dict] = []

    def add(self, message: dict):
        """追加一条消息（dict 或 OpenAI Message 对象均可）。"""
        if not isinstance(message, dict):
            message = self._message_to_dict(message)
        self.history.append(message)

    def get_messages(self) -> list[dict]:
        """返回发送给 LLM 的完整消息列表（含裁剪逻辑）。"""
        if len(self.history) <= self.max_messages:
            return [self.system_message] + self.history
        trimmed = self.history[-self.max_messages:]
        # 裁剪后第一条不能是 tool 消息，否则 OpenAI 协议会报错
        while trimmed and trimmed[0]["role"] == "tool":
            trimmed.pop(0)
        return [self.system_message] + trimmed

    def clear(self):
        """清空对话历史，开启新一轮会话。"""
        self.history = []

    @staticmethod
    def _message_to_dict(message) -> dict:
        """将 OpenAI SDK 的 Message 对象转为可序列化 dict。"""
        result = {"role": message.role, "content": message.content or ""}
        if getattr(message, "tool_calls", None):
            result["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ]
        return result

    def dump(self) -> str:
        """导出会话记录（JSON 字符串），便于调试与展示。"""
        return json.dumps([self.system_message] + self.history,
                          ensure_ascii=False, indent=2)
