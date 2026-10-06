# 代码审查 Agent (Code Review Agent)

> **源代码仓库**：https://github.com/xiexuan2006/code-review-agent （公开仓库，含完整提交历史）
>
> **作者**：谢逸轩

基于**通义千问（Qwen）**与**手写 ReAct Agent 循环**的智能代码审查助手。Agent 能够自主推理、调用工具（读取文件、执行 Python 代码验证 Bug），并输出结构化的审查报告。

## 功能特性

- 🤖 **Agent 循环**：手写 ReAct 模式（输入 → 推理 → 工具调用 → 观察 → 输出），不依赖 Agent 框架
- 🔧 **三种工具**：
  - `list_files`：浏览目录结构
  - `read_file`：读取文件源码（带行号，便于定位问题）
  - `run_python_code`：在子进程沙箱中执行代码，**动态验证 Bug 是否真实存在**
- 🧠 **上下文记忆**：支持多轮对话，自动裁剪历史防止 token 超限
- 🔁 **错误重试**：LLM 调用失败时指数退避重试；工具报错不会中断 Agent，而是交还 LLM 自行调整
- 💻 **双交互入口**：命令行 CLI + Gradio Web 界面

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
# 复制配置模板
copy .env.example .env
# 编辑 .env，填入你的阿里云百炼 DashScope API Key（https://bailian.console.aliyun.com/）
```

### 3. 启动 Web 界面（推荐）

```bash
python web/app.py
```

浏览器自动打开 `http://127.0.0.1:7860`，粘贴代码或输入文件路径（如 `examples/buggy_demo.py`）即可审查。界面会实时展示 Agent 的工具调用过程。

### 4. 或使用命令行

```bash
python main.py
```

支持命令：`/clear` 清空会话，`/quit` 退出。

## 使用示例

```
你 > 帮我审查 examples/buggy_demo.py 这个文件

Agent > 🔧 调用工具 read_file({"path": "examples/buggy_demo.py"})
        🔧 调用工具 run_python_code({"code": "..."})   # 验证除零 Bug
        📋 输出结构化审查报告（含严重程度、行号、修复建议、验证状态）
```

## 项目结构

```
code-review-agent/
├── agent/
│   ├── agent.py            # Agent 核心循环（ReAct）
│   ├── llm.py              # LLM 客户端封装（Qwen，含重试）
│   ├── memory.py           # 上下文记忆管理
│   └── tools/
│       ├── base.py         # 工具基类与注册表
│       ├── file_reader.py  # 文件读取/目录浏览工具
│       └── code_executor.py# Python 代码执行沙箱
├── prompts/system.py       # 代码审查系统提示词
├── web/app.py              # Gradio Web 界面
├── main.py                 # CLI 入口
├── factory.py              # 组件组装工厂
├── examples/buggy_demo.py  # 演示用示例代码
├── README.md               # 本文件
└── Design.md               # 架构设计文档
```

## 技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| LLM | 通义千问 qwen-plus | 国内直连、OpenAI 兼容接口、性价比高 |
| Agent 实现 | 原生 API 手写循环 | 完全掌控推理-行动流程，架构清晰可解释 |
| Web 界面 | Gradio | 快速构建聊天界面，原生支持对话历史 |
| 语言 | Python 3.10+ | 生态成熟，与代码执行工具天然契合 |

## 已知限制

- 代码执行沙箱为子进程隔离（非容器级），仅用于本地学习演示，请勿执行不可信代码
- 单次提问最多 10 轮工具调用（防止死循环）
- 文件读取上限 200KB
