#!/usr/bin/env python3
"""Poll a vibe-trading session, waiting for an assistant response.

Usage:
  python3 poll_session.py <session_id> [--port 8000] [--interval 30] [--timeout 7200]

Defaults: port=8000, interval=30s, timeout=2h (7200s)

The correct API endpoint is GET /sessions/{id}/messages?limit=100
NOT ?before=30&after=10 (those params don't apply to this API).
"""
import json
import sys
import time
import urllib.request


def poll(session_id: str, port: int = 8000, interval: int = 30, timeout: int = 7200):
    base = f"http://127.0.0.1:{port}"
    url = f"{base}/sessions/{session_id}/messages?limit=100"
    start = time.time()
    deadline = start + timeout
    last_progress = 0
    known_count = 0

    # First pass: count existing assistant messages so we only wait for NEW ones
    # This makes the script work for follow-up questions, not just first message
    try:
        resp = urllib.request.urlopen(url, timeout=10)
        msgs = json.loads(resp.read().decode())
        known_count = sum(1 for m in msgs if m.get("role") == "assistant" and m.get("content"))
    except Exception:
        pass

    while time.time() < deadline:
        try:
            resp = urllib.request.urlopen(url, timeout=10)
            msgs = json.loads(resp.read().decode())
            current_count = sum(1 for m in msgs if m.get("role") == "assistant" and m.get("content"))
            if current_count > known_count:
                elapsed = int(time.time() - start)
                new_msgs = [m for m in reversed(msgs) if m.get("role") == "assistant" and m.get("content")]
                if new_msgs:
                    print(f"\n=== Response received ({elapsed // 60}m {elapsed % 60}s) ===\n")
                    print(new_msgs[0]["content"])
                    return True
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Query failed: {e}", file=sys.stderr)

        elapsed = int(time.time() - start)
        if elapsed - last_progress >= 300:
            remaining = int(deadline - time.time())
            print(f"[{time.strftime('%H:%M:%S')}] Waited {elapsed // 60}m, {remaining // 60}m remaining...")
            last_progress = elapsed
        time.sleep(interval)

    print(f"\nTimeout after {(time.time() - start) // 60:.0f} minutes, no response")
    return False


if __name__ == "__main__":
    args = sys.argv[1:]
    sid = args[0] if args else None
    port = 8000
    interval = 30
    timeout = 7200

    for i, a in enumerate(args[1:], 1):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
        elif a == "--interval" and i + 1 < len(args):
            interval = int(args[i + 1])
        elif a == "--timeout" and i + 1 < len(args):
            timeout = int(args[i + 1])

    if not sid:
        print("Usage: poll_session.py <session_id> [--port 8000] [--interval 30] [--timeout 7200]", file=sys.stderr)
        sys.exit(1)

    ok = poll(sid, port=port, interval=interval, timeout=timeout)
    sys.exit(0 if ok else 1)
