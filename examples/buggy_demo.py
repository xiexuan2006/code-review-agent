"""演示用示例代码：包含多种典型 Bug，供 Agent 审查演示。

故意保留以下问题：
1. 除零错误（未检查 b 是否为 0）
2. 文件资源泄漏（open 后未关闭）
3. 硬编码密码（安全隐患）
4. 可变默认参数（Python 经典陷阱）
5. 裸 except（吞掉所有异常）
"""


def find_user(users: list, user_id):
    for user in users:
        if user["id"] == user_id:
            return user
    return None


def get_email(users: list, user_id):
    user = find_user(users, user_id)
    return user["email"]  # user 可能为 None，会抛 TypeError


def average(numbers=[]):  # 可变默认参数陷阱
    numbers.append(0)
    return sum(numbers) / len(numbers)  # numbers 为空时除零


def load_data(path):
    try:
        with open(path) as f:
            return f.read()
    except:  # 裸 except，吞掉所有异常包括 KeyboardInterrupt
        return ""


PASSWORD = "admin_123456"  # 硬编码密码


def check_password(input_pwd):
    return input_pwd == PASSWORD
