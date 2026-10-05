"""构建提交包：将项目源码打包为 zip，排除虚拟环境、API Key 等敏感与无关内容。

输出: ../学号姓名_code-review-agent.zip
"""
import io
import sys
import zipfile
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

BASE = Path(__file__).resolve().parent
OUT = BASE.parent / "学号姓名_code-review-agent.zip"

EXCLUDE_DIRS = {".venv", ".edge_profile", ".edge_cache", "video_frames",
                "__pycache__", ".git", "打包暂存"}
EXCLUDE_FILES = {".env"}  # 含 API Key，严禁打包
EXCLUDE_SUFFIX = {".log"}

count = 0
with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
    for path in sorted(BASE.rglob("*")):
        rel = path.relative_to(BASE)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if path.is_file():
            if path.name in EXCLUDE_FILES or path.suffix in EXCLUDE_SUFFIX:
                continue
            zf.write(path, arcname=str(Path("code-review-agent") / rel))
            count += 1

size_mb = OUT.stat().st_size / 1024 / 1024
print(f"打包完成: {OUT}")
print(f"文件数: {count}  大小: {size_mb:.1f} MB")

# 校验：确认包内无敏感文件
with zipfile.ZipFile(OUT) as zf:
    names = zf.namelist()
    assert not any(n.endswith("/.env") for n in names), "危险: .env 被打包!"
    assert not any(".venv/" in n for n in names), "危险: .venv 被打包!"
    key_files = [n for n in names if n.endswith((".py", ".md", ".txt", ".bat",
                                                 ".mp4", ".gitignore",
                                                 ".env.example"))]
    print(f"校验通过: 无 .env / .venv  泄露; 关键文件 {len(key_files)} 个")
