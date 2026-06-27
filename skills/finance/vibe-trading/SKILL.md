---
name: vibe-trading
version: 0.1.9
description: Professional finance research toolkit — backtesting (7 engines + benchmark comparison panel), factor analysis, Alpha Zoo (452 pre-built alphas across qlib158/alpha101/gtja191/academic), options pricing, 77 finance skills, 29 multi-agent swarm teams, Trade Journal analyzer, and Shadow Account (extract → backtest → render) across 7 data sources (tushare, yfinance, okx, akshare, mootdx, ccxt, futu).
dependencies:
  python: ">=3.11"
  pip:
    - vibe-trading-ai
env:
  - name: TUSHARE_TOKEN
    description: "Tushare API token for China A-share data (optional — HK/US/crypto work without any key)"
    required: false
  - name: OPENAI_API_KEY
    description: "OpenAI-compatible API key — only needed for run_swarm (multi-agent teams). All other tools work without it."
    required: false
  - name: LANGCHAIN_MODEL_NAME
    description: "LLM model name for run_swarm (e.g. deepseek/deepseek-v4-pro). Only needed if using run_swarm."
    required: false
  - name: API_AUTH_KEY
    description: "Bearer token for the FastAPI HTTP server. When set, all API endpoints require Authorization: Bearer <token>. When unset, only loopback (127.0.0.1/localhost) requests are allowed — non-local requests get 403."
    required: false
  - name: DEEPSEEK_API_KEY
    description: "DeepSeek API key for LLM provider. Used with LANGCHAIN_PROVIDER=deepseek and DEEPSEEK_BASE_URL."
    required: false
mcp:
  command: vibe-trading-mcp
  args: []
---

# Vibe-Trading

Professional finance research toolkit with AI-powered backtesting (7 engines), multi-agent teams, 77 specialized skills, the **Alpha Zoo** (452 pre-built quantitative alphas across qlib158 / alpha101 / gtja191 / academic with one-line CLI benchmarking), and the Shadow Account loop — extract your implicit trading rules from a journal, backtest them across A股/港股/美股/crypto, then see where they would have served you better.

## Setup

```bash
pip install vibe-trading-ai
```

> **Package name vs commands:** The PyPI package is `vibe-trading-ai`. Once installed, you get:
>
> | Command | Purpose |
> |---------|---------|
> | `vibe-trading` | Interactive CLI / TUI |
> | `vibe-trading serve` | Launch FastAPI web server |
> | `vibe-trading-mcp` | Start MCP server (for Claude Desktop, OpenClaw, Cursor, etc.) |

### Frontend Build (required for Web UI)

The Web UI (`vibe-trading serve`) requires a frontend build. After `pip install`, the frontend is NOT pre-built. You must:

```bash
# Find the package location
python -c "import vibe_trading_ai; import pathlib; print(pathlib.Path(vibe_trading_ai.__file__).parent.parent)"

# Build frontend
cd <package_location>/frontend
npm install && npm run build
```

> **Pitfall:** If installed via `pipx`, the `vibe-trading` command resolves to the pipx venv. The server looks for `frontend/dist` relative to the installed package, NOT the source directory. You must build or copy `frontend/dist/` into the pipx venv's package path (e.g. `~/.local/pipx/venvs/vibe-trading-ai/lib/python3.X/frontend/dist`).

> **Pitfall:** If using `pip install -e .` (editable/source install) but `which vibe-trading` still points to a pipx venv, the pipx version takes precedence. Either uninstall the pipx version (`pipx uninstall vibe-trading-ai`) or copy the frontend build to the pipx path.

> **Pitfall:** Do NOT use `screen` to run `vibe-trading serve`. Screen-launched processes have an asyncio `create_task` scheduling bug with uvicorn in Python 3.14 — sessions are created and messages accepted, but `_run_attempt` never starts. The session stays `active` forever. Always use **tmux** instead (see Server Startup below).

Add to your agent's MCP config:

```json
{
  "mcpServers": {
    "vibe-trading": {
      "command": "vibe-trading-mcp"
    }
  }
}
```

### API Key Requirements

Core research MCP tools work with zero API keys for HK/US/crypto. After `pip install`, backtesting, market data, factor analysis, options pricing, chart patterns, web search, document reading, trade journal analysis, shadow-account extraction/backtest/report, the Alpha Zoo (452 pre-built alphas), and all 77 skills are ready to use. IBKR tools require a local TWS / IB Gateway session; `run_swarm` requires an LLM key.

| Feature | Key needed | When |
|---------|-----------|------|
| HK/US equities & crypto | None | Always free (yfinance + OKX) |
| China A-share data | `TUSHARE_TOKEN` | Only if you query A-share symbols |
| Multi-agent swarm (`run_swarm`) | `OPENAI_API_KEY` + `LANGCHAIN_MODEL_NAME` | Swarm spawns internal LLM workers |

## What You Can Do

### Shadow Account — flagship loop

Feed a CSV broker export (同花顺 / 东财 / 富途 / generic), and the agent will:
1. `analyze_trade_journal` — profile your behavior (holding period, win rate, disposition effect, chasing, overtrading, anchoring).
2. `extract_shadow_strategy` — distill 3-5 if-then rules that describe your profitable roundtrips.
3. `run_shadow_backtest` — backtest those rules across A/HK/US/crypto and compute delta-PnL vs your realized trades.
4. `render_shadow_report` — produce an HTML/PDF report (8 sections + charts) with today's matching signals.
5. `scan_shadow_signals` — list today's symbols that match your shadow's entry cadence (research only).

### Backtesting
Create and run quantitative strategies across 7 engines (ChinaA, GlobalEquity, Crypto, ChinaFutures, GlobalFutures, Forex + options) with 7 data sources:
- **HK/US equities** via yfinance (free, no API key)
- **Cryptocurrency** via OKX or CCXT/100+ exchanges (free, no API key)
- **China A-shares** via Tushare (token) or AKShare (free fallback)
- **Futures, forex, macro** via AKShare (free, no API key)
- **HK & A-share equities** via Futu (broker login required, optional)

```

### Multi-Agent Swarm Teams
29 pre-built agent teams for complex research (25 available in v0.1.5; see `references/swarm_presets.md` for full keyword matching reference):
- **Investment Committee**: bull/bear debate → risk review → PM decision
- **Global Equities Desk**: A-share + HK/US + crypto → global strategist
- **Crypto Trading Desk**: funding/basis + liquidation + flow → risk manager
- **Earnings Research Desk**: fundamentals + revisions + options → earnings strategist
- **Macro/Rates/FX Desk**: rates + FX + commodities → macro PM
- **Quant Strategy Desk**: screening → factor research → backtest → risk audit
- **Risk Committee**: drawdown, tail risk, regime analysis
- And 22 more specialized teams

Use `list_swarm_presets()` to see all teams, then `run_swarm()` to execute.

### Alpha Zoo (452 pre-built alphas)
One-line cross-sectional IC / IR / alive-reversed-dead categorisation across four bundled zoos:
- **qlib158** (154 alphas) — Microsoft Qlib's `Alpha158` feature handler, Apache-2.0 with pinned commit SHA.
- **alpha101** (101 alphas) — Kakushadze (2015) "101 Formulaic Alphas" (arXiv:1601.00991), written from the paper appendix.
- **gtja191** (191 alphas) — Guotai Junan 2014 "191 Short-period Trading Alpha Factors" research report.
- **academic** (6 factors) — Fama-French 5 + Carhart momentum (honest price-based proxies).

Each alpha ships with `__alpha_meta__` (formula LaTeX + theme + universe + warmup + columns required), guarded by an AST purity gate + 300-row lookahead sentinel test. Use the `vibe-trading alpha {list,show,bench,compare,export-manifest}` CLI, the `/alpha/*` REST routes (browser at `/alpha-zoo`), or compose multi-factor signals via `ZooSignalEngine.from_zoo(...)`.

### Finance Skills (77)
Comprehensive knowledge base covering:
- Technical analysis (candlestick, Elliott wave, Ichimoku, SMC, harmonic, chanlun)
- Quantitative methods (factor research, ML strategy, pair trading, multi-factor)
- Risk management (VaR/CVaR, stress testing, hedging)
- Options (Black-Scholes, Greeks, multi-leg strategies, payoff diagrams)
- HK/US equities (SEC filings, earnings revisions, ETF flows, ADR/H-share arbitrage)
- Crypto trading desk (funding rates, liquidation heatmaps, stablecoin flows, token unlocks, DeFi yields)
- Behavioral finance, trade journal diagnostics, shadow account
- Macro analysis, credit research, sector rotation, and more

Use `load_skill(name)` to access full methodology docs with code templates.

## Available MCP Tools (35)

| Tool | Description | API Key |
|------|-------------|---------|
| `list_skills` | List all 77 finance skills | None |
| `load_skill` | Load full skill documentation | None |
| `start_research_goal` | Create an auditable research goal | None |
| `get_research_goal` | Read the current research goal | None |
| `add_goal_evidence` | Attach evidence to a research goal | None |
| `update_research_goal_status` | Update goal lifecycle status | None |
| `backtest` | Run vectorized backtest engine | None* |
| `factor_analysis` | IC/IR analysis + layered backtest | None* |
| `analyze_options` | Black-Scholes price + Greeks | None |
| `pattern_recognition` | Detect chart patterns (H&S, double top, etc.) | None |
| `get_market_data` | Fetch OHLCV data across 6 sources (auto-detect + fallback) | None* |
| `web_search` | Search the web via DuckDuckGo | None |
| `read_url` | Fetch web page as Markdown | None |
| `read_document` | Extract text from PDF/DOCX/XLSX/PPTX/images | None |
| `write_file` | Write files (config, strategy code) | None |
| `read_file` | Read file contents | None |
| `analyze_trade_journal` | Parse broker CSV → profile + behavior diagnostics | None |
| `extract_shadow_strategy` | Distill 3-5 if-then rules from profitable roundtrips | None |
| `run_shadow_backtest` | Multi-market backtest + delta-PnL attribution | None* |
| `render_shadow_report` | HTML/PDF shadow report (8 sections + charts) | None |
| `scan_shadow_signals` | Today's symbols matching the shadow's cadence | None |
| `list_swarm_presets` | List multi-agent team presets | None |
| `run_swarm` | Execute a multi-agent research team | LLM key |
| `get_swarm_status` | Poll swarm run status without blocking | None |
| `get_run_result` | Get final report and task summaries | None |
| `list_runs` | List recent swarm runs with metadata | None |
| `reap_stale_runs` | Finalize stale swarm runs | None |
| `trading_connections` | List selectable connector profiles | None |
| `trading_select_connection` | Select the default connector profile | None |
| `trading_check` | Check connector readiness | Connector app/OAuth |
| `trading_account` | Read account summary from selected connector | Connector app/OAuth |
| `trading_positions` | Read positions from selected connector | Connector app/OAuth |
| `trading_orders` | Read open orders from selected connector | Connector app/OAuth |
| `trading_quote` | Read a quote snapshot from selected connector | Connector app/OAuth |
| `trading_history` | Read historical bars from selected connector | Connector app/OAuth |

<sub>*A-share symbols require `TUSHARE_TOKEN`. HK/US/crypto are free. Trading connector rows use the selected connector profile, e.g. IBKR local TWS/Gateway or Robinhood MCP OAuth.</sub>

## Configuration (`.env`)

vibe-trading reads config from `~/.vibe-trading/.env`. Key variables:

| Variable | Purpose |
|----------|---------|
| `DEEPSEEK_API_KEY` | DeepSeek LLM provider key (for run_swarm) |
| `DEEPSEEK_BASE_URL` | DeepSeek API base URL (default `https://api.deepseek.com/v1`) |
| `LANGCHAIN_MODEL_NAME` | LLM model for run_swarm (e.g. `deepseek/deepseek-v4-flash`) |
| `LANGCHAIN_PROVIDER` | LLM provider name (e.g. `deepseek`) |
| `LANGCHAIN_TEMPERATURE` | LLM temperature |
| `OPENAI_API_KEY` | OpenAI-compatible key (alternative to DEEPSEEK_API_KEY) |
| `TUSHARE_TOKEN` | A-share data source token (optional) |
| `API_AUTH_KEY` | Bearer token for HTTP API auth (see below) |
| `TIMEOUT_SECONDS` | Agent iteration timeout |

To change config: edit `~/.vibe-trading/.env` then restart the server.

## API Authentication (built-in)

vibe-trading's FastAPI server has **built-in Bearer token auth** (no code modification needed). All session/run/swarm/alpha endpoints are protected by `Depends(require_auth)`.

**Behaviour:**

| `API_AUTH_KEY` set? | Request from | Result |
|---|---|---|
| No (unset) | localhost/127.0.0.1 | ✅ Allowed (dev mode) |
| No (unset) | Non-loopback IP | ❌ 403 Forbidden |
| Yes | Any IP with wrong/missing token | ❌ 401 Unauthorized |
| Yes | Any IP with valid `Bearer <token>` | ✅ Allowed |

**To enable auth:** add to `~/.vibe-trading/.env`, then restart.

```
API_AUTH_KEY=your-secret-token
```

**Usage:** all requests must include `Authorization: Bearer your-secret-token` header.

```bash
curl -H "Authorization: Bearer your-secret-token" http://127.0.0.1:8000/sessions
```

EventSource/SSE endpoints also accept the API key as a query parameter (`?api_key=...`).

> **Pitfall — don't confuse with DeepSeek API key:** `API_AUTH_KEY` protects the vibe-trading HTTP server itself. `DEEPSEEK_API_KEY` is the LLM provider credential for the internal agent. They are independent.

## Server Startup

Use `tmux` (NOT `screen`) for running `vibe-trading serve` in background:

```bash
# New session with proxy
tmux new-session -d -s vibe-trading \
  bash -c 'export HTTP_PROXY=http://127.0.0.1:7890 HTTPS_PROXY=http://127.0.0.1:7890 && vibe-trading serve'

# Without proxy (DeepSeek is accessible from China)
tmux new-session -d -s vibe-trading 'vibe-trading serve'
```

# Reattach
tmux attach -t vibe-trading

# Kill
tmux kill-session -t vibe-trading
```

Default port is **8000**. Do NOT use 8888 unless you have a specific reason. If you accidentally start a second server on a different port, it won't process sessions — the first server handles the API calls if you hit the wrong port.

### Troubleshooting: session created but no assistant response after 10+ minutes

Most common cause: **you're hitting the wrong server**. Check for multiple vibe-trading processes:

```bash
ps aux | grep vibe-trading | grep -v grep
lsof -iTCP -sTCP:LISTEN -P 2>/dev/null | grep -E "8000|8888"
```

If you find more than one, kill the extras (especially the one not in tmux) and re-create the session on the correct port.

Second most common cause: **screen-launched server** (see pitfall above). Kill it and restart in tmux.

```bash
pip install vibe-trading-ai
```

That's it — no API keys needed for HK/US/crypto markets. Start using `backtest`, `get_market_data`, `analyze_options`, `analyze_trade_journal`, `extract_shadow_strategy`, `web_search`, the **Alpha Zoo** (`vibe-trading alpha bench --zoo gtja191 --universe csi300 --period 2018-2025`), and all 77 skills immediately.

## Local Development / From Source

User has source at a local `Vibe-Trading` project directory. To run from source:

```bash
cd path/to/your/Vibe-Trading
pip install -e .          # editable install
vibe-trading serve --port 8888
```

### Pitfalls

- **Frontend not built:** Server warns `No frontend build found`. Run `cd frontend && npm run build` first, otherwise the web UI won't load.
- **Session API：建 session 后直接发消息**，不设 goal。字段名是 `content`。
- **Session API 优先**：API session 模式是首选。
- **Background mode:** `terminal(background=true)` causes silent exit for `vibe-trading serve`. Always run in foreground with a generous timeout, or use `pty=true` if available.
- **Tushare optional:** Preflight shows `TUSHARE_TOKEN not set` — this is fine for HK/US/crypto, only affects A-share data.
- **LLM key:** The server auto-detects `OPENAI_API_KEY` / compatible env vars for LLM features (e.g. run_swarm). Without it, backtesting and data tools still work.
- **Swarm worker tool gaps:** Some swarm preset workers (e.g. `investment_committee`'s bull_advocate/bear_advocate) are configured with only `bash/read_file/write_file/load_skill/factor_analysis` — no `web_search` or `get_market_data`. This means they cannot research private companies (SPCX/SpaceX) or fetch real-time market data independently. If a swarm run fails quickly (1-2 min), check whether the target needs web research that the workers can't perform. Workaround: include pre-fetched price data and context in the swarm query, or use API session mode where the agent has full tool access.

## Loading Tools from External MCP Servers

The built-in agent can load tools from your own external MCP servers in addition to its local toolset.

> **Note:** This is the *MCP client* path — the opposite of the MCP plugin listed above. The plugin above makes Vibe-Trading's tools available to your agents. This section lets Vibe-Trading's own agent call tools from *your* servers.

### Setup

Create `~/.vibe-trading/agent.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "command": "uvx",
      "args": ["my-mcp-server"],
      "toolTimeout": 30,
      "enabledTools": ["*"]
    }
  }
}
```

Ordinary external MCP tools appear automatically in API session and swarm calls. They are injected after local tools under stable names: `mcp_<server>_<tool>`.

### Official IBKR MCP read-only probe

Add Interactive Brokers' official MCP endpoint as a read-only external server:

```json
{
  "mcpServers": {
    "ibkr": {
      "type": "streamableHttp",
      "url": "https://api.ibkr.com/v1/api/mcp",
      "auth": {
        "type": "oauth",
        "scopes": ["mcp.read"],
        "clientName": "Vibe-Trading",
        "cacheDir": "~/.vibe-trading/live/ibkr/oauth"
      },
      "enabledTools": ["*"]
    }
  }
}
```

### Trading connector profiles

The public trading surface is connector-first. Choose a connector profile, then paper/live is just an attribute under that connector.

```bash
pip install "vibe-trading-ai[ibkr]"
vibe-trading connector list
vibe-trading connector use ibkr-paper-local
vibe-trading connector configure ibkr-paper-local --yes
vibe-trading connector check
vibe-trading connector account
vibe-trading connector positions
vibe-trading connector orders
vibe-trading connector quote AAPL
vibe-trading connector history AAPL --duration "30 D" --bar-size "1 day"
```

Default ports are TWS paper `7497`, IB Gateway paper `4002`, TWS live-readonly `7496`, and IB Gateway live-readonly `4001`.

## Analysis Workflow (for Portfolio Analysis)

当用户要求分析持仓时，加载 `vibe-portfolio-analysis` 技能。架构：
- API session 模式：建 session 后直接发消息，不设 goal（不同版本行为可能不同）
- 4 步：`run_swarm(equity_research_team)` → `load_skill + read_url` → `run_swarm(investment_committee) × 1`（一轮全部标的）→ 综合审查
- **不要角色扮演**（"你是宏观策略师"）— 每步直接指定哪个工具/swarm
- prompt 里**不列 agent 已知工具清单**（agent 自带工具注册表），**不重复持仓列表**（prompt 开头已有持仓表）
- API session 模式：建 session 后直接发消息，不设 goal
- 详见该技能（v5.1 架构）

### load_skill 的行为模式

`load_skill` 在 session agent 和 swarm worker（`POST /swarm/runs`）都可用。SkillsLoader 自动发现 `src/skills/` 下全部 73 个技能，每个技能是 SKILL.md 方法论文档（非代码）。

| 场景 | load_skill | 推荐 |
|------|-----------|------|
| API session agent | 可用，但消耗迭代。基础技能（均线/RSI/MACD/美林时钟）模型本就会，无需加载。不熟悉的领域（ichimoku/谐波/SMC/chanlun）可加载 | 基础分析不调；进阶分析按需调 |
| Swarm Preset (`POST /swarm/runs`) | ✅ 正常工作。每个 worker 的 skills whitelist 控制哪些显示在 Available Skills 区 | 预设自带，YAML 的 `skills` 字段自动过滤 |
| swarm 内的 `{upstream_context}` | 通过 `input_from` → `{upstream_context}` 模板替换传递上游 task 摘要 | DAG 架构，无需手动调 |

### 执行方式选择
API session 模式适合一次性大分析；Swarm preset 适合需要真正多 agent 辩论的深度研究。

#### 73 个可用技能一览

所有技能在 `src/skills/` 目录下，每个含 SKILL.md 方法论文档：

| 类别 | 技能 |
|------|------|
| 宏观/行业 | global-macro, macro-analysis, sector-rotation, asset-allocation, geopolitical-risk, cross-market-strategy |
| 技术面 | technical-basic, candlestick, ichimoku, elliott-wave, harmonic, smc, chanlun, minute-analysis |
| 基本面 | fundamental-filter, financial-statement, valuation-model, earnings-forecast, earnings-revision, dividend-analysis |
| 因子/量化 | factor-research, multi-factor, ml-strategy, pair-trading, quant-statistics, strategy-generate |
| ETF/资金流 | etf-analysis, us-etf-flow, hk-connect-flow, sentiment-analysis, behavioral-finance |
| 风险/期权 | risk-analysis, volatility, hedging-strategy, options-advanced, options-payoff, options-strategy |
| Crypto | onchain-analysis, defi-yield, token-unlock-treasury, stablecoin-flow, perp-funding-basis |
| 数据源 | yfinance, tushare, akshare, okx-market, ccxt, mootdx, edgar-sec-filings |
| 回测/报告 | backtest-diagnose, performance-attribution, report-generate, trade-journal, execution-model |
| 其他 | event-driven, convertible-bond, credit-analysis, commodity-analysis, corporate-events, regulatory-knowledge, seasonal, web-reader, doc-reader, etc. |

在 swarm worker 中，agent_spec.skills whitelist 控制哪些技能出现在 Available Skills 区。agent 用 `load_skill('technical-basic')` 加载完整 SKILL.md。

#### Swarm Runtime 架构速览

```
每个 swarm 是一个 YAML 文件，定义 agents（角色 + system_prompt + tools + skills）+ tasks（DAG，depends_on + input_from）

runtime 执行逻辑：

  1. build_run_from_preset() — 从 YAML 构建 SwarmRun（agents + tasks 对象）
  2. topological_layers(tasks) — 拓扑排序 → 执行层
  3. 逐层执行，层内 ThreadPoolExecutor 并行
  4. 每层完成后 collect summaries → 替换下游 system_prompt 的 {upstream_context}
  5. 每个 task = 一个独立 ReAct 循环 worker

Worker 创建流程：
  SkillsLoader() → 从 src/skills/ 加载所有技能
  _filter_skill_descriptions(loader, agent_spec.skills) → 只保留 whitelist 内的技能
  build_worker_prompt() → system_prompt = role + upstream_context + skill_desc + grounding + data_citation + execution_rules
  run_worker() → for iteration in range(max_iterations): llm.stream_chat(messages, tools)
```

每个 worker 独立（有自己的 tool registry + LLM 实例），不知道其他 worker 存在。数据只通过 `input_from` → `{upstream_context}` 单向传递。

#### 写自定义 Swarm Preset

1. 创建 YAML，放在 `src/swarm/presets/<name>.yaml`
2. agents 定义角色 + system_prompt + tools + skills whitelist
3. tasks 定义 DAG 层序
4. `input_from` 用上游 task_id 映射到下游 `{upstream_context}`

**注意：** preset 目录在 pipx venv 内，升级 `vibe-trading-ai` 会被覆盖。备份到 `~/.hermes/swarm-presets/`。

参考 `portfolio-six-phase` 预设（5 agents, 5 tasks, 4 层 DAG）。

#### 对于 Session 模式的兜底

如果 `load_skill` 达不到预期效果，改为 `run_swarm` 调用内置 swarm preset。详见 `vibe-portfolio-analysis` 技能（v5 架构，4 步工具导向）。

### The 4-part analysis template (use as structure):

```
## 🌍 Macro Position (global-macro)
Dollar cycle, Fed path, Geopolitical, Capital flows

## 📊 Asset Allocation (asset-allocation)
All-weather / Risk parity / Black-Litterman framework

## 🔍 Position Analysis
Per-security: current price vs cost, fundamentals, sector outlook

## 💡 Recommendations
Hold/cut/add actions with $ amounts and reasoning
```

### ⚠️ CRITICAL: 实时价格优先于一切估算

进行任何持仓分析前，**必须先用 yfinance / get_market_data 获取实时价格**。不得使用训练数据中的价格做估值。

**错误案例**：用训练数据价格算出 QLD +83%、MU -78%，用户纠正后发现全错。不是工具问题，是跳过了"先拉实时数据"这一步。

**正确流程**：
1. 第一步永远是拉实时价格（yfinance 一行搞定多个标的）
2. 基于实时价格计算持仓市值、P&L、占比
3. 用户纠正价格时立即重算所有数据，不在旧分析上贴补丁

## 使用 HTTP API（唯一推荐方式）

vibe-trading 的 FastAPI Web 服务运行在 `http://127.0.0.1:8000`（tmux 启动，见 Server Startup），所有功能通过 REST API 调用。

### API 端点一览

| 方法 | 路径 | 用途 |
|------|------|------|
| `POST /sessions` | 创建会话 | `{"title": "可选标题"}` → 返回 `session_id` |
| `POST /sessions/{id}/messages` | 发送分析 prompt | `{"content": "分析指令"}` → 返回 `message_id` |
| `GET /sessions/{id}/messages` | 读取会话全部消息 | `?limit=50` 获取完整对话。返回数组，每条含 role/created_at/content |
| `GET /sessions/{id}` | 查会话状态 | `status: active/processing/done` |
| `POST /sessions/{id}/goal` | 设定分析目标 | `{"objective": "..."}` |
| `POST /swarm/runs` | 直接跑 swarm | 绕过 session |
| `GET /swarm/presets` | 查看 swarm 团队 | 返回所有预设团队 |

### 完整执行流程（Create → Message → Poll → Follow-up → Poll）

建 session 后直接发消息，不设 goal。

```bash
SERVER="http://127.0.0.1:8000"

# Step 1: 服务是否已启动
if ! curl -sf "$SERVER/" > /dev/null 2>&1; then
    echo "❌ 请先运行: vibe-trading serve"
    exit 1
fi

# Step 2: 新建 session
SESSION_ID=$(curl -sf -X POST "$SERVER/sessions" \
  -H "Content-Type: application/json" -d '{}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "✅ 创建 session: $SESSION_ID"

# Step 3: 发消息（不设 goal）
PROMPT="分析 NVDA 的最新走势，给出多空判断"
curl -sf -X POST "$SERVER/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" \
  -d "{\"content\": $(echo "$PROMPT" | python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))")}" > /dev/null
echo "✅ 请求已发送"

# Step 4: 轮询等待（用现有脚本，不自己写轮询逻辑）
python3 ~/.hermes/skills/finance/vibe-trading/scripts/poll_session.py $SESSION_ID
```

> **⚠️ 用户偏好 — 报告交付格式**
> - 必须直接发送 **完整报告内容**，不能给摘要/精简版
> - 支持 **follow-up 追问**：可以发第二条消息追问细节（如质疑数据来源、概率假设等），session agent 会正常响应。不需要一次性发完全部需求。
> - 追问后同样用 `poll_session.py` 等回复，不要写自定义轮询逻辑。

### ⚠️ 轮询注意事项

- 用 `GET /sessions/{id}/messages?limit=100`，**不是** `?before=30&after=10`（后者的参数不适用，会导致轮询一直找不到回复）
- 用已有的 `poll_session.py` 脚本轮询，**不要自己写自定义轮询逻辑**
- 不要频繁手动 curl messages——一次分析跑跑停停是正常的
- 确认 agent 已开始处理的信号：server log 出现 `POST /sessions/{id}/messages`

### poll_session.py 对 follow-up 消息的支持

`poll_session.py` 支持 follow-up 追问：它在启动时先记录已有 assistant 消息数量，然后只在新 assistant 消息出现时才返回。因此同一个 session 可以反复使用该脚本：发消息→跑脚本等回复→再发消息→再跑脚本。

**历史 bug（已修复）：** 旧版 poll_session.py 在消息列表中正向遍历，找到第一条 assistant 消息就返回。对于有多轮对话的 session，这意味着跑 follow-up 时会立即返回旧回复而不是等新的。修复：首次运行时统计已有 assistant 消息数，仅当计数增加时才返回最新一条。

### 读取已有 session 的内容

如果已有 session ID，直接 GET 即可读取完整对话：

```bash
curl -s "http://127.0.0.1:8000/sessions/9241c5d325a4/messages?limit=50" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
for m in msgs:
    print(f'=== {m[\"role\"]} ({m[\"created_at\"][:19]}) ===')
    print(m['content'])
    print()
"
```

也可以只取最新的一条 assistant 回复：

```bash
curl -s "http://127.0.0.1:8000/sessions/9241c5d325a4/messages?limit=50" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
for m in reversed(msgs):
    if m['role'] == 'assistant' and m.get('content'):
        print(m['content'])
        break
"
```

### ⚠️ 注意事项

- `run_swarm` 耗时 10+ 分钟，必须包含在分析中
- API 返回异步结果，需轮询 `GET /sessions/{id}/messages`
- `POST /sessions/{id}/messages` body 字段是 `content`
- 服务地址 `http://127.0.0.1:8000` 由 `vibe-trading serve` 提供（tmux 启动）

### 🛑 Pitfall: HTTP 451 upstream blocks cause the internal agent to hang

The vibe-trading agent's `read_url` tool hits Yahoo Finance, Reuters, Investopedia, Finviz, and other finance domains. These sites **frequently return HTTP 451** (blocked for abuse/DDoS suspicion) from the shared Jina Reader IP (`r.jina.ai`). When this happens:

- The internal agent retries indefinitely and **never produces an assistant response**
- Sessions stay in `active` status forever
- Server logs show `read_url upstream HTTP 451: SecurityCompromiseError`
- Local Clash proxy **does not help** because the request goes Jina → target site, not local → target site

#### ✅ Fix: Deploy Jina Reader locally (solves 451 permanently)

Jina Reader is open-source and runs as a Docker container with a single command:

```bash
docker run -d --name jina-reader --restart unless-stopped -p 3000:8081 ghcr.io/jina-ai/reader:oss
```

Then change `web_reader_tool.py`'s `_JINA_PREFIX`:

```python
# Before (uses Jina's shared cloud IP — gets 451):
_JINA_PREFIX = "https://r.jina.ai/"

# After (uses your local network — goes through your proxy/TUN):
_JINA_PREFIX = "http://127.0.0.1:3000/"
```

The local Reader runs on your machine, so its outbound requests go through your own proxy/TUN, not Jina's shared IP. Target sites see your residential IP and do not block.

**File location (pipx install):** `~/.local/pipx/venvs/vibe-trading-ai/lib/python3.14/site-packages/src/tools/web_reader_tool.py`

After changing the prefix, restart the vibe-trading server for it to take effect.

**Verification:**
```bash
# Check container is running
docker ps --filter name=jina-reader

# Test a site that was previously blocked
curl -s "http://127.0.0.1:3000/https://www.reuters.com/technology/" -H "Accept: text/markdown" | head -5
```

#### ⚠️ Detection (before you've deployed local Reader)

If you send a prompt and polling `GET /sessions/{id}/messages` returns only user messages after 5+ minutes, check the server log for 451 errors:

```bash
# Find the vibe-trading tmux session output
tmux capture-pane -t vibe-trading -p | grep -i "451"
```

#### 🩹 Workaround (alternative if Docker not available)

Fetch prices yourself via Yahoo Finance v8 chart API before sending to vibe-trading:

```bash
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/MU?interval=1d&range=1mo" \
  -H "User-Agent: Mozilla/5.0" | python3 -c "
import sys, json
data = json.load(sys.stdin)
meta = data['chart']['result'][0]['meta']
print(f'Price: \${meta[\"regularMarketPrice\"]}')
print(f'52w High: \${meta[\"fiftyTwoWeekHigh\"]}')
print(f'52w Low: \${meta[\"fiftyTwoWeekLow\"]}')
"
```

### 🔴 铁律一：严禁擅自重试/开新任务（token 很贵）

用户说跑一个任务就只跑一个。如果当前 session 在跑着：
- **不要自己再开一个新 session 重试**
- **不要切端口重试**（8000 ↔ 8888）
- **不要取消当前 session 换方案**
- **耐心等**。一次 portfolio 分析可能跑 30 分钟到 2 小时，run_swarm 每次几百万 token，重试一次就是几十美分起步，不必要

**token 成本意识**：用户用 deepseek-v4-flash 省 token，任何不必要的新 session / 重试 / 额外调用都是在浪费用户的预算。

**正确做法**：如果超时或卡住，先问用户。不要自己判断"死了"。

### 🔴 铁律二：严禁未经用户允许重启/终止服务

任何涉及以下操作，必须先问用户，得到明确许可才能执行：
- **重启 vibe-trading server**（任何端口）
- **kill 任何正在运行的 server 进程**
- **取消/删除 session**（包括看似卡住的 session）
- **切换后端端口**（8000 ↔ 8888）

**原因**：session 可能只是跑得慢（30 分钟+），不是卡死。直接 kill server 会丢失正在进行的分析。用户可能同时在用多个端口做不同测试。

**正确做法**：如果怀疑 session 卡住，先问用户要不要取消或重启，不要自己判断。

### 🔴 铁律三：Server 重启后 session active 但 agent 不会继续处理

vibe-trading serve 重启后，已有 session 的 `status` 显示为 `active`，但 agent 实际上**不会恢复处理**。即使用户发了"继续处理"的消息，agent 也不推进。

**修复**：不是等它恢复，而是：
1. 确认 server 已启动
2. 开**全新 session**
3. 把原 prompt 重新发一次（不要依赖旧 session 的 resume 机制）

轮询脚本 timeout 设为 15-30 分钟（默认 15 分钟），超时后检查是否有部分回复。如果有回复但 session 仍在 `active`，说明可能已产生完整结果——直接取最后一条 assistant 消息即可。

#### 盘后/盘前行情优先展示

美股有盘后/盘前交易数据时，`generate_vibe_prompt.py` 会自动拉取 `postMarketPrice` 替代 `regularMarketPrice` 展示（通过 yfinance + proxy），并加标记：🌙=盘后价 🌅=盘前价。A股/港股已收盘则展示收盘价，无标记。

详细 API 参考见 `references/postmarket-pricing.md`。

## ⚠️ CRITICAL: Transparency when API is slow

When API analysis takes too long or returns empty, **always tell the user explicitly**.

**Correct:** "vibe-trading API 仍在处理中，run_swarm 需要10+分钟"
**Wrong:** silently using yfinance + web_search without mentioning vibe-trading

### 每日持仓分析 prompt 生成

**不要用 `portfolio.json`** — 它不再维护。持仓数据从 `~/.ft/snapshot.yaml` 直接读取。

生成 prompt：

```bash
~/.hermes/scripts/generate_vibe_prompt.py
```

输出到 `/tmp/vibe_cron_daily.md`，然后用 API session 模式提交到 vibe-trading serve。

该脚本自动：
- 从 `~/.ft/snapshot.yaml` 读取持仓
- 通过 **yfinance** 拉实时价（内设代理 `http_proxy=http://127.0.0.1:7890`，无需手动设 env）
- **美股优先拉盘后/盘前价**（`postMarketPrice`），带涨跌幅百分比
- 加标记：🌙=盘后价  🌅=盘前价（A/港股已收盘不标）
- 输出 markdown 持仓表到 `/tmp/vibe_cron_daily.md`

**修改分析风格：** 编辑脚本顶部附近的 `STYLE` 变量（如果已改版则直接改 prompt 模板中的风格描述）。

**⚠️ 用 cron 自动化时的陷阱:** cron 环境默认无 HTTP_PROXY，但脚本已在内部通过 `os.environ` 设置代理（`yfinance` 读 HTTP_PROXY 环境变量），所以 cron 不需要额外设 proxy。但要注意 split into two cron jobs:
- Job A (data-collection): 定时生成 prompt 文件，script 模式推送结果
- Job B (analysis): 读取 prompt 文件并提交到 vibe-trading API session
不要在一个 cron job 里做全部流程——session 可能卡住，cron 超时会丢数据。

Linked files:
- `scripts/vibe_api.py` — reusable CLI client for HTTP API
- `scripts/generate_vibe_prompt.py` — daily analysis prompt generator (swarm vars + legacy prompt)
- `scripts/poll_session.py` — session polling script (uses `?limit=100`, NOT `?before=30&after=10`)
- `references/china-ticker-map.md` — Yahoo Finance 代码映射表
- `references/swarm-architecture.md` — DAG 编排架构详解（runtime + worker + data flow）
| `references/options-learning-resources.md` | curated external options learning resources (web sites, books, learning path) for when the user asks how to learn options trading
| `references/options-practical-sizing.md` | 期权实操：合约规模、盈亏平衡、IV Crush、财报期权风险、Covered Call/Put保护的实际可行性评估（针对小仓位用户） |
- `references/options-practical-analysis.md` — **实操流程**：拉链上数据→算关键指标→检查持仓约束→情景分析→常见陷阱（IV Crush / Theta / 合约规模 mismatch）。用户问"这个期权能买吗"时按此执行
- `references/trading-agent-comparison.md` — three-way comparison of TradingAgents, Vibe-Trading, and R&D-Agent-Quant (Microsoft NeurIPS 2025). Positioning, architecture, capabilities.
- `references/from-factor-to-strategy.md` — The complete pipeline from having price factors to running a live strategy: factor synthesis, stock selection, portfolio weighting, risk control, trade execution, rebalancing frequency. Use when user asks "now that I have factors, what else do I need?"
### 4 步工具导向 prompt 结构

运行时用 `scripts/generate_vibe_prompt.py` 生成 prompt，详见 `vibe-portfolio-analysis` 技能（v5 架构，4 步工具导向，合并 role-playing 为直接工具指定）。