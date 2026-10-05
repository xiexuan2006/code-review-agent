"""LLM 客户端封装：基于 OpenAI 兼容接口调用通义千问，带指数退避重试。"""
import time

from openai import OpenAI

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen-plus"


class LLMClient:
    """通义千问 LLM 客户端（OpenAI 兼容模式）。"""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL,
                 base_url: str = DEFAULT_BASE_URL, max_retries: int = 3):
        if not api_key:
            raise ValueError("API Key 不能为空，请在 .env 中配置 DASHSCOPE_API_KEY")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.max_retries = max_retries

    def chat(self, messages: list, tools: list | None = None, temperature: float = 0.2):
        """调用 LLM，失败时按指数退避重试。

        Args:
            messages: OpenAI 格式的消息列表
            tools: 工具的 JSON Schema 定义列表
            temperature: 生成温度，代码审查场景用低温度保证稳定

        Returns:
            助手消息对象（可能包含 content 或 tool_calls）
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                }
                if tools:
                    kwargs["tools"] = tools
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message
            except Exception as e:  # 网络/限流/服务端错误统一重试
                last_error = e
                if attempt < self.max_retries - 1:
                    wait = 2 ** attempt  # 1s, 2s, 4s...
                    print(f"[LLM] 第 {attempt + 1} 次调用失败: {e}，{wait}s 后重试")
                    time.sleep(wait)
        raise RuntimeError(f"LLM 调用在 {self.max_retries} 次重试后仍失败") from last_error
