#!/usr/bin/env python3
"""轮询 session messages，直到最后一条是 assistant 回复。
用法: python3 poll_session.py <session_id>

测试（已完成session，应立即返回）：
  python3 poll_session.py 37319840798b

等待中的session：
  python3 poll_session.py 0c767eda8be8
"""
import json, sys, time, urllib.request

SESSION = sys.argv[1]
BASE = "http://127.0.0.1:8888"
POLL = 20       # 每20秒查一次
MAX_WAIT = 1800  # 最多等30分钟

start = time.time()
while time.time() - start < MAX_WAIT:
    try:
        resp = urllib.request.urlopen(f"{BASE}/sessions/{SESSION}/messages", timeout=10)
        msgs = json.loads(resp.read())
        total = len(msgs)
        
        if total > 0 and msgs[-1]["role"] == "assistant":
            elapsed = int(time.time() - start)
            print(f"\n=== 分析完成（{elapsed}s, 共{total}条消息）===", flush=True)
            print(msgs[-1]["content"], flush=True)
            sys.exit(0)
        
        # 还没完成，打印进度
        elapsed = int(time.time() - start)
        if total > 0:
            last_role = msgs[-1]["role"]
            print(f"  [{elapsed}s] 共{total}条, 最后一条={last_role}", flush=True)
        else:
            print(f"  [{elapsed}s] 尚无消息", flush=True)
            
    except Exception as e:
        print(f"  [{int(time.time()-start)}s] 请求错误: {e}", flush=True)
    
    time.sleep(POLL)

print(f"超时: {MAX_WAIT}s 内未收到 assistant 回复", flush=True)
sys.exit(1)
