"""CLI 入口：命令行方式与代码审查 Agent 对话。"""
import sys

from factory import create_agent


def main():
    print("=" * 60)
    print("  代码审查 Agent (Code Review Agent) - CLI 模式")
    print("  输入代码文件路径或直接粘贴代码，Agent 将进行审查")
    print("  命令: /clear 清空会话 | /quit 退出")
    print("=" * 60)

    try:
        agent = create_agent()
    except ValueError as e:
        print(f"\n初始化失败: {e}")
        sys.exit(1)

    while True:
        try:
            user_input = input("\n你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not user_input:
            continue
        if user_input == "/quit":
            print("再见！")
            break
        if user_input == "/clear":
            agent.reset()
            print("会话已清空。")
            continue

        print("\nAgent 思考中...\n")
        try:
            answer = agent.run(user_input)
            print(answer)
        except RuntimeError as e:
            print(f"[错误] {e}")


if __name__ == "__main__":
    main()
