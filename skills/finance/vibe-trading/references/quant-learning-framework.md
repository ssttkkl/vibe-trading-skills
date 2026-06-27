# Quant Trading Learning Framework: Three Paradigms

A consolidated reference bridging vibe-trading, Qlib, Backtrader, FinRL, and FinGPT — organized by the three quant paradigms.

## The Three Paradigms

| Paradigm | Approach | Typical Tools | Data |
|----------|----------|-------------|------|
| **📐 传统因子量化** | Human proposes hypothesis, data validates | Qlib, Backtrader, JoinQuant, Alphalens | Price, fundamentals |
| **🤖 AI-传统ML** | Algorithm discovers patterns from data | Qlib model zoo, FinRL, XGBoost, Scikit-learn | Price + factor matrix |
| **🧠 AI-LLM** | LLM processes unstructured text | vibe-trading, FinGPT, RD-Agent | News, earnings transcripts, social media |

## Qlib vs Vibe-Trading: Layer Clarification

**They are NOT competitors. They are different layers of the same stack:**

```
                    Qlib                          Vibe-Trading
               ┌──────────────┐            ┌────────────────────────┐
               │  Data Pipeline │            │ Alpha Zoo (452 factors) │
               │  Factor Engine │            │ 77 Finance Skills       │
               │  Model Training│            │ 29 Swarm Teams          │
               │  Backtest Engine│           │ Shadow Account          │
               └──────┬───────┘            │ MCP/CLI/HTTP API        │
                      │                    └────────────────────────┘
                      │                            │
          R&D-Agent(Q)│                            │
       ┌──────────────┴────────┐                  │
       │ LLM layer on top      │                  │
       │ of Qlib infrastructure│                  │
       └──────────────────────┘                  │
                                                  │
                    ┌─────────────────────────────┴─────────────┐
                    │ Backtest Engines: ChinaA / GlobalEquity /  │
                    │ Crypto / Futures / Forex / Options        │
                    └───────────────────────────────────────────┘
```

| Aspect | Qlib | Vibe-Trading |
|--------|------|-------------|
| **What you do** | Write Python code to call its API | `pip install` then CLI/MCP tools |
| **Data setup** | Download 5GB HDF5, configure calendar | Auto-fetch from yfinance/AKShare/OKX |
| **Markets** | Primarily A-share (CSI300/500) | A/HK/US/Crypto/Futures/FX/Options |
| **Factors** | Write or import Alpha158 | Built-in 452, `vibe-trading alpha bench` one-liner |
| **Backtest** | Qlib's own engine | 7 engines (ChinaA built Qlib-like) |
| **Time to first result** | Hours | Minutes |

**Vibe-Trading's ChinaA engine** is conceptually similar to Qlib's pipeline (factor → model → backtest), but:
- No HDF5 data download required
- No Docker setup
- Auto-falls back to AKShare when Tushare token missing
- The Alpha Zoo ships qlib158 as static pandas code, not requiring Qlib runtime

## Qlib Beginner: Getting Started Path

Prerequisites: Minimum 16GB RAM, 5GB free disk.

### Step 1: Install + Download Data

```bash
# Install
pip install qlib

# Download CSI300 data (~5GB)
python scripts/get_data.py qlib_data \
  --target_dir ~/.qlib/qlib_data/cn_data \
  --region cn
```

### Step 2: Run the Official Tutorial

```bash
cd examples/tutorial/
python work_by_code.py
```

This runs LightGBM + Alpha158 full pipeline. Verify it works before changing anything.

### Step 3: Run the Model Zoo

```bash
# Individual models
cd examples/benchmarks/LightGBM && python run_model.py
cd examples/benchmarks/LSTM && python run_model.py
cd examples/benchmarks/Transformer && python run_model.py

# Or all at once
python examples/run_all_model.py
```

Available models in `examples/benchmarks/`:

| Model | Complexity | Notes |
|-------|-----------|-------|
| Linear | ⭐ | Baseline. If this beats your fancy model, you have a problem. |
| LightGBM | ⭐ | **Best starting point.** Fast, robust, good with Alpha158. |
| GRU/LSTM | ⭐⭐ | Classic RNN sequence models. |
| ALSTM | ⭐⭐ | LSTM + Attention. |
| Transformer | ⭐⭐⭐ | Pure attention. Needs more data. |
| GATs | ⭐⭐⭐ | Graph attention. Captures stock-stock relationships. |
| DoubleEnsemble | ⭐⭐ | Ensemble. Robust. |
| HIST | ⭐⭐⭐ | Graph + temporal. Most complex. |

### Step 4: Compare Results

Output format (from Qlib's evaluation):

```
Model     IC      ICIR    Rank IC  Ann.Return  MaxDD
LightGBM  0.0277  0.2211  0.0386   3.97%       -8.55%
LSTM      0.0318  0.2367  0.0435   3.81%       -12.07%
Transformer 0.0317 0.2538  0.0434  2.93%       -9.87%
```

### Step 5: Iterate

1. Swap factors (Alpha158 → Alpha360)
2. Add industry neutrality
3. Change rebalance frequency
4. Adjust slippage assumptions
5. Interpret which factors matter most (Qlib model interpreter)

### Step 6: Vibe-Trading Alternative (5-minute setup)

```bash
pip install vibe-trading-ai

# Same analysis, no data download
vibe-trading alpha bench --zoo alpha158 --universe csi300 --period 2018-2025
vibe-trading backtest --model lgb --factors alpha158 --universe csi300
```

## Three LLM Quant Frameworks: When to Use What

Three major LLM-powered frameworks cover different use cases — understanding their boundaries is critical:

| Framework | Core Loop | Key Strength | Key Weakness | Best For |
|-----------|-----------|-------------|-------------|----------|
| **TradingAgents** (83k⭐) | Analyst team → Bull/bear debate → Trader → Risk → PM → **buy/sell/hold** | Out-of-box: give ticker+date, get decision; fixed quality floor | No backtesting, no factor mining, no joint optimization; LLM tokens every run | Quick single-ticker buy/sell signal (just run `tradingagents`) |
| **Vibe-Trading** | 35 MCP tools + 77 skills + 29 swarm teams → **analysis result** | Full quant toolkit: backtesting, factors, options, shadow account; no API key for HK/US/crypto | Not a self-contained trading pipeline; requires prompt engineering and orchestration | Research, backtesting, portfolio analysis, factor studies |
| **R&D-Agent(Q)** (NeurIPS 2025, MSRA) | Spec → Synthesis → Co-STEER codegen → Qlib backtest → Bandit → **generated factors + models** | Automates factor mining + model selection; only ~$10/run; 2× ARR with 70% fewer factors | Needs Qlib + data setup; output is factor library, not trading signals | Quant strategy R&D — let LLM discover new factors and models iteratively |

### Architecture of R&D-Agent(Q)

```
Research Phase:
  [Specification Unit]  → Define data interface, output format, constraints
  [Synthesis Unit]      → Grow a "knowledge forest" from past experiments
                           produce next hypothesis (factor or model)

Development Phase:
  [Implementation Unit] → Co-STEER agent: DAG-based task scheduling,
                           knowledge graph of (task, code, feedback) triples,
                           code generation + iterative repair
  [Validation Unit]     → Backtest on Qlib, IC > 0.99 dedup, update SOTA
  [Analysis Unit]       → Multi-dimensional evaluation, then context-bandit
                           (Thompson sampling on 8-dim state vector)
                           decides: optimize factor or model next?
```

### Key R&D-Agent(Q) code architecture (RD-Agent repo)

```
rdagent/scenarios/qlib/          ← The Qlib quant scenario
├── developer/                    ← Co-STEER codegen (factor_coder, model_coder, runners)
├── experiment/                   ← Experiment scenarios (factor, model, quant/joint)
├── proposal/                     ← Hypothesis generation (factor_proposal, model_proposal, quant_proposal)
├── docker/                       ← Qlib data Docker environment
└── prompts.yaml                  ← LLM prompt templates

rdagent/app/qlib_rd_loop/
├── conf.py                       ← Config: 4 setting classes:
│   ├── FactorBasePropSetting       → rdagent fin_factor (factor-only optimization)
│   ├── ModelBasePropSetting        → rdagent fin_model (model-only optimization)
│   ├── QuantBasePropSetting        → rdagent fin_quant (joint: bandit scheduler, model+factor coders/runners)
│   └── FactorFromReportPropSetting → rdagent fin_factor_report (extract factors from financial reports)
├── factor.py                     → CLI entry: factor-only loop
├── model.py                      → CLI entry: model-only loop
├── quant.py                      → CLI entry: joint optimization loop
└── factor_from_report.py         → CLI entry: factors from financial reports

CLI commands:
  rdagent fin_quant        → Joint factor+model optimization (the full R&D-Agent(Q))
  rdagent fin_factor       → Factor-only optimization
  rdagent fin_model        → Model-only optimization
  rdagent fin_factor_report  → Extract factors from PDF reports
```

### When to use which

- "Tell me buy/sell for NVDA" → **TradingAgents**: `tradingagents` → pick ticker → done
- "Backtest my strategy" / "Analyze my portfolio" → **Vibe-Trading**: `pip install vibe-trading-ai`
- "Discover new factors for my A-share model" → **R&D-Agent(Q)**: `pip install rdagent` + Qlib data

R&D-Agent(Q) treats Qlib as its **execution engine** — it generates Qlib-compatible factor/model Python code, runs them through Qlib's backtest pipeline, and uses the metrics to drive the next iteration. This is fundamentally different from Vibe-Trading's Alpha Zoo, which ships pre-built Qlib formulas (qlib158) as static pandas expressions without requiring Qlib runtime.

## Practical Project Entry Points (Difficulty)

1. [gpt4-stock-trading](https://github.com/skywalker0803r/gpt4-stock-trading) — One notebook: GPT-4 sentiment → signal → backtest. Easiest start.
2. [JoinQuant multi-factor tutorial](https://github.com/JoinQuant/multi-factor-tutorial) — Traditional factor quant with IC analysis.
3. [FinGPT](https://github.com/AI4Finance-Foundation/FinGPT) (18k⭐) — Full LLM pipeline: data → LoRA fine-tuning → sentiment → signal.
4. [FinRL](https://github.com/AI4Finance-Foundation/FinRL) (10k⭐) — Deep RL trading with optional LLM embeddings.
5. [Qlib](https://github.com/microsoft/qlib) (44k⭐) — Microsoft's complete AI quant platform. Alpha158, model zoo, RD-Agent for LLM factor mining.

## LLM Quant Pitfalls

| Pitfall | Description | Mitigation |
|---------|-------------|------------|
| Look-ahead bias | LLM may "know" future events from training data | Timestamp-aligned historical news only; cache by date |
| Hallucination | LLM invents tickers, cites fake news | Fact-checking agent; require citations; LLM as auxiliary only |
| API cost | GPT-4 $0.10-0.50/call | DeepSeek for screening ($3-6/mo); expensive model only for high-conviction |
| HTTP 451 blocks | Yahoo/Reuters/Investopedia block shared IPs | Use v8 chart API (query1.yahoo.com); pull prices yourself |
| Refusal to answer | LLMs refuse trading advice | System prompt: "financial data research assistant" |

## LLM-Specific Backtesting

1. Time alignment — only feed news dated ≤ backtest date
2. Caching — cache results by (date, content_hash) → disk for reproducibility
3. Cost estimation — DeepSeek $3-6/mo vs GPT-4 $60-120/mo (100 stocks × 20 days)
4. Framework — Use [llm-backtest-toolkit](https://github.com/llm-quant/llm-backtest-toolkit)
5. Ensemble — LLM as one factor weighted ≤ 20%, never alone

## Data Sources by Type

| Type | US/Global | China |
|------|-----------|-------|
| Price (free) | yfinance | AKShare, baostock |
| Price (pro) | Polygon.io | Tushare (token) |
| News | NewsAPI (free 500/day), Finnhub | Tushare news |
| Earnings transcripts | Finnhub, HuggingFace | — |
| SEC filings | SEC EDGAR API (free) | — |
| Social sentiment | Reddit (Pushshift) | Xueqiu API |

## Key Papers (2024-2025)

- "LLMFactor: Extracting Financial Factors from Text with LLMs" — HKUST, 2024
- "Can GPT models be Financial Analysts?" — empirical study, 2024
- "TradingGPT: A Multi-Agent System for Financial Trading" — 2024
- "LLMs for Financial Market Analysis: A Survey" — 2025
- "R&D-Agent-Quant" (NeurIPS 2025, arXiv:2505.15155) — Microsoft: multi-agent auto factor+model optimization on Qlib, <$10/run, 2× ARR vs Alpha158/360. Code: github.com/microsoft/RD-Agent
- "R&D-Agent: An LLM-Agent Framework Towards Autonomous Data Science" (arXiv:2505.14738) — Overall RD-Agent framework. Top performer on MLE-bench.
- "TradingAgents" (arXiv:2412.20138) — TauricResearch: multi-agent trading pipeline (analyst→debate→trader→risk→PM), LangGraph, 83k⭐
