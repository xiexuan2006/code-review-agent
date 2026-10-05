"""文件读取工具：读取文件内容、列出目录结构，供 Agent 审查项目代码。"""
import os

from .base import Tool

MAX_FILE_SIZE = 200 * 1024  # 单文件读取上限 200KB，防止撑爆上下文
MAX_LIST_ENTRIES = 100

TEXT_SUFFIXES = {
    ".py", ".js", ".ts", ".java", ".go", ".c", ".cpp", ".h", ".rs",
    ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".html", ".css",
}


class ListFilesTool(Tool):
    """列出目录下的文件与子目录。"""

    name = "list_files"
    description = (
        "列出指定目录下的文件和子目录（不递归）。用于了解项目结构，"
        "再配合 read_file 阅读具体文件。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "directory": {
                "type": "string",
                "description": "目录路径，'.' 表示当前目录",
            }
        },
        "required": ["directory"],
    }

    def execute(self, directory: str = ".") -> str:
        directory = os.path.abspath(directory)
        if not os.path.isdir(directory):
            return f"错误：目录不存在: {directory}"
        entries = sorted(os.listdir(directory))
        if len(entries) > MAX_LIST_ENTRIES:
            entries = entries[:MAX_LIST_ENTRIES] + [f"...(共 {MAX_LIST_ENTRIES} 条已截断)"]
        lines = []
        for name in entries:
            full = os.path.join(directory, name)
            tag = "[目录]" if os.path.isdir(full) else "[文件]"
            lines.append(f"{tag} {name}")
        return "\n".join(lines) or "（空目录）"


class ReadFileTool(Tool):
    """读取单个文本文件的全部内容。"""

    name = "read_file"
    description = (
        "读取指定文件的内容（仅支持文本文件，如 .py/.js/.md 等）。"
        "审查代码前先用本工具获取源码。"
    )
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件相对或绝对路径"}
        },
        "required": ["path"],
    }

    def execute(self, path: str) -> str:
        path = os.path.abspath(path)
        if not os.path.isfile(path):
            return f"错误：文件不存在: {path}"
        suffix = os.path.splitext(path)[1].lower()
        if suffix not in TEXT_SUFFIXES:
            return f"错误：不支持的文件类型 '{suffix}'（仅支持文本文件）"
        size = os.path.getsize(path)
        if size > MAX_FILE_SIZE:
            return f"错误：文件过大（{size} 字节 > {MAX_FILE_SIZE}），请拆分后审查"
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        # 附带行号，方便 LLM 在审查意见中引用行号
        numbered = "\n".join(
            f"{i:>4} | {line}" for i, line in enumerate(content.splitlines(), 1)
        )
        return f"文件 {path}（{size} 字节）内容如下：\n{numbered}"
