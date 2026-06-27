#!/usr/bin/env python3
"""
vibe-trading HTTP API 封装：创建 session → 发送 prompt → 轮询结果

用法：
  python3 vibe_api.py -f /tmp/prompt.txt               # 从文件读 prompt
  python3 vibe_api.py -p "分析 NVDA 基本面"              # 从参数读 prompt
  python3 vibe_api.py -f prompt.txt --poll 20 --wait 60  # 自定义轮询

依赖：无（仅标准库）
服务地址：http://127.0.0.1:8888（可通过 VIBE_API_URL 环境变量覆盖）
"""
import json
import sys
import time
import urllib.request
import urllib.error
import os

API_BASE = os.environ.get("VIBE_API_URL", "http://127.0.0.1:8888")


def api_post(path: str, body: dict) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def api_get(path: str) -> dict | list:
    url = f"{API_BASE}{path}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def create_session(title: str = "") -> str:
    result = api_post("/sessions", {"title": title})
    return result["session_id"]


def send_message(session_id: str, content: str) -> str:
    result = api_post(f"/sessions/{session_id}/messages", {"content": content})
    return result["message_id"]


def poll_result(session_id: str, max_polls: int = 15, wait: int = 60) -> str | None:
    for i in range(1, max_polls + 1):
        time.sleep(wait)
        try:
            msgs = api_get(f"/sessions/{session_id}/messages?limit=5")
            for m in msgs:
                if m.get("role") == "assistant" and m.get("content"):
                    return m["content"]
            print(f"  ⏳ 第{i}次轮询 ({i * wait}s)，仍在处理...", file=sys.stderr)
        except Exception as e:
            print(f"  ⚠️  轮询异常: {e}", file=sys.stderr)
    return None


def main():
    import argparse

    parser = argparse.ArgumentParser(description="vibe-trading HTTP API 客户端")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-f", "--file", help="prompt 文件路径")
    group.add_argument("-p", "--prompt", help="prompt 文本")
    parser.add_argument("--poll", type=int, default=15, help="最大轮询次数 (默认 15)")
    parser.add_argument("--wait", type=int, default=60, help="每次轮询间隔秒数 (默认 60)")
    parser.add_argument("--title", default="", help="会话标题 (可选)")
    parser.add_argument("--raw", action="store_true", help="仅输出结果文本，不打印日志")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            content = f.read()
    else:
        content = args.prompt

    try:
        health = api_get("/health")
    except Exception as e:
        print(f"❌ vibe-trading 服务不可达 ({API_BASE}): {e}", file=sys.stderr)
        sys.exit(1)

    if not args.raw:
        print(f"ℹ️  服务状态: {health}", file=sys.stderr)

    session_id = create_session(args.title)
    if not args.raw:
        print(f"✅ Session: {session_id}", file=sys.stderr)

    send_message(session_id, content)
    if not args.raw:
        print(f"📤 Prompt 已发送 ({len(content)} 字符)", file=sys.stderr)
        print(f"⏳ 开始轮询 (最多 {args.poll} 次, 间隔 {args.wait}s)...", file=sys.stderr)

    result = poll_result(session_id, max_polls=args.poll, wait=args.wait)
    if result:
        print(result)
    else:
        print(f"❌ 超时: {args.poll} 次轮询后未获取结果", file=sys.stderr)
        print(f"   手动检查: curl -s {API_BASE}/sessions/{session_id}/messages?limit=5", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
