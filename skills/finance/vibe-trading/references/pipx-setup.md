# Pipx Installation Setup Guide

## Current State (2026-06)

`vibe-trading` is installed via **pipx** at:
```
which vibe-trading  →  ~/.local/pipx/venvs/vibe-trading-ai/bin/vibe-trading
```

The pipx version (0.1.5) may differ from the source version (0.1.9 in your local `Vibe-Trading` project directory).

## Preflight Check

When `vibe-trading serve` starts, it runs a preflight:
```
Preflight Check
 OK   │ LLM (deepseek)     │ deepseek-v4-pro via https://api.deepseek.com/v1
 OK   │ OKX API            │ reachable
 OK   │ yfinance           │ reachable
 OK   │ Tushare            │ token configured
 OK   │ akshare            │ installed
 OK   │ ccxt               │ installed

6/6 services ready
```

If Tushare shows `N/A` with "TUSHARE_TOKEN not set", A-share data is unavailable but HK/US/crypto still work.

## .env File Location

The server loads `.env` from the **same directory as `api_server.py`**. The search order is:

1. `~/.vibe-trading/.env` (user-level config — preferred for pipx)
2. `AGENT_DIR/.env` where AGENT_DIR = package root
3. `$CWD/.env` (current working directory)

For pipx, the package root is:
```
~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/
```

So the .env must be at:
```
~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/.env
```

Or better, create `~/.vibe-trading/.env` which is the first search path.

### Copy command
```bash
# Option A: user-level config (preferred)
mkdir -p ~/.vibe-trading
cp your-local-vibe-trading/agent/.env ~/.vibe-trading/.env

# Option B: pipx site-packages
cp your-local-vibe-trading/agent/.env ~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/.env
```

## Frontend Build

The server warns:
```
[warn] No frontend build found at .../frontend/dist
```

Fix:
```bash
# Build from source
cd your-local-vibe-trading/frontend
npm install && npm run build

# Copy to pipx path
mkdir -p ~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/frontend/
cp -r your-local-vibe-trading/frontend/dist ~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/frontend/dist
```

After fixing, the log shows `[prod] Frontend served from ...` instead of the warning.

## Switching to Source (editable) Install

```bash
# Remove pipx version
pipx uninstall vibe-trading-ai

# Install source in editable mode
cd your-local-vibe-trading
pip install -e .

# Verify
readlink -f $(which vibe-trading)
# Should point to: your-local-vibe-trading/... not pipx
```

## Running the Server

```bash
vibe-trading serve --port 8888
```

Server starts on `http://0.0.0.0:8888`. Keeps running until CTRL+C.

For background: use a separate terminal tab/window. `terminal(background=true)` with Hermes causes silent exits for long-lived processes.
