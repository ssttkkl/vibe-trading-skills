# AI Trading Frameworks Comparison

Three LLM-powered trading frameworks compared: **TradingAgents**, **Vibe-Trading**, **R&D-Agent-Quant**.

---

## TradingAgents (TauricResearch)

⭐ 83.4k stars | [arXiv:2412.20138](https://arxiv.org/abs/2412.20138)

**定位**: 让 LLM 模拟一家真实交易公司，给定 ticker+日期 → 输出买卖建议。

**架构**: LangGraph 固定流水线，7 个角色 agent：
- Analyst Team: 基本面、情绪、新闻、技术 4 个分析师
- Researcher Team: 多/空研究员辩论
- Trader: 下单决策
- Risk Management + Portfolio Manager: 风控 + 最终审批

**特点**:
- 每次决策跑满全套流程，质量可预期
- Decision Log: 同 ticker 自动反思之前决策
- LangGraph Checkpoint: 断点续跑
- 支持 10+ LLM 提供商
- **不能定制流程，不能做因子分析、回测验证**

**适合**: 想要"对 ticker 一键出买卖建议"的研究者，不关心因子挖掘和量化验证。

---

## Vibe-Trading

**定位**: 可编程的量化研究实验室 — 工具/知识/agent 团队自由组合。

**架构**: MCP 工具集 (35 个) + 77 金融技能 + 29 个 swarm 团队，无固定流水线。

**核心能力**:
- **回测**: 7 引擎 (A股/全球/Crypto/期货/外汇/期权)
- **因子**: Alpha Zoo 452 个预置公开因子，支持 IC/IR 基准测试
- **Shadow Account**: 从交易日志提取隐式规则 → 跨市场回测 → 信号
- **Swarm**: 29 个专注团队 (Investment Committee/Crypto Desk/Macro Desk 等)
- **数据**: 7 个数据源，HK/US/Crypto 零 API key
- **HTTP API** 优先使用

**适合**: 需要做量化研究、回测策略、分析组合、从交易日志中发现模式的交易者。

---

## R&D-Agent-Quant (Microsoft Research)

NeurIPS 2025 | [arXiv:2505.15155](https://arxiv.org/abs/2505.15155) | [github.com/microsoft/RD-Agent](https://github.com/microsoft/RD-Agent)

**定位**: 用 LLM 多智能体自动做量化因子挖掘 + 模型选型，联合迭代优化。

**架构**: 5 模块闭环 (Specification → Synthesis → Implementation → Validation → Analysis)：
- Co-STEER: 带知识图的代码生成器，记录 (任务, 代码, 反馈) 三元组，新任务先查历史
- Bandit 调度器: Contextual Thompson Sampling 决定"下轮挖因子还是换模型"

**实验结果** (CSI300, 2008-2020):
- R&D-Factor: IC 0.0497, ARR 14.61% (用 22% 的因子数量达到 Alpha 158 水平)
- R&D-Agent(Q) 联合优化: IC 0.0532, ARR 14.21%, IR 1.74
- 成本不到 $10
- 在 CSI500 / NASDAQ 100 上做了 out-of-sample 验证

**关键局限性**:
- **最终生成的具体因子公式没有公布** — 论文证明了流程可行性，但 8 个 SOTA 因子是黑箱
- 强依赖 Qlib 运行时环境 (Docker + 数据 + API key)
- 每轮实验需要 LLM API 调用
- 本质上只是把"提出因子 → 训练 → 回测"这套流程搬到了 LLM 上
- **非量化研究员用不上** — 不如 Vibe-Trading 开箱即用

**适合**: 量化研究员，想自动化因子挖掘 + 模型选型流程的人。

---

## 对比总表

| 维度 | TradingAgents | Vibe-Trading | R&D-Agent(Q) |
|------|--------------|-------------|--------------|
| **类型定位** | 交易决策流水线 | 量化研究工具包 | 量化 R&D 自动化框架 |
| **架构** | LangGraph 固定流水线 | MCP 工具集 + 可插拔 Agent | 5 模块闭环 + Bandit 调度 |
| **自动化程度** | 单次决策 (全自动) | 半自动 (需写 prompt) | **全自动迭代** |
| **因子挖掘** | ❌ | ✅ Alpha Zoo 452 个 (预置) | ✅ **LLM 动态生成** |
| **回测验证** | 有日期对齐但非核心 | ✅ 7 引擎 | ✅ 基于 Qlib |
| **模型选型** | ❌ 固定流程 | ❌ 需手动 | ✅ LLM 自动 + Bandit 调度 |
| **联合优化** | ❌ | ❌ | ✅ |
| **生成因子可见** | N/A | ✅ 全部公开 | ❌ **未公布** |
| **跑一次的成本** | 7+ agent，token 大 | 可零成本 (不跑 swarm) | <$10 (论文值) |
| **启动成本** | pip install + API key | pip install 零 key | Docker + Qlib + API key |
| **适合谁** | 要快速买卖建议的人 | 要做量化研究的人 | 要自动挖因子的研究员 |

---

## 一句话说清楚

> **TradingAgents** = 输入 ticker → 出买卖建议（交易公司模拟器）  
> **Vibe-Trading** = 给交易者的一套量化工具（自己动手分析）  
> **R&D-Agent(Q)** = 让 LLM 代替你挖因子+选模型（量化 R&D 自动化）

三者定位完全不重叠。TradingAgents 给你答案，Vibe-Trading 给你做答案的工具，R&D-Agent(Q) 帮你自动化做答案的过程。

## Hermes-Side Reproduction of R&D-Agent(Q)

The paper's core loop is replicable with Hermes tools without Qlib:

```python
# Pseudocode for the R&D loop
while rounds < max_rounds:
    # [Synthesis] Read history, propose new factor/model
    hypothesis = llm(
        f"Current best: IC={sota_ic}, ARR={sota_arr}. "
        f"Fact store has {n_trials} past attempts. "
        f"Propose a new {'factor' if bandit=='factor' else 'model'}."
    )

    # [Implementation] Write code
    factor_code = llm_with_fact_store(hypothesis, fact_store)
    write_file(f"factors/round_{i}.py", factor_code)

    # [Validation] Run backtest
    result = terminal(f"python backtest.py --factors factors/round_{i}.py")

    # [Analysis] Evaluate + decide next direction
    sota, feedback = evaluate(result, sota)
    direction = bandit(metrics)  # factor or model?

    # Persist
    fact_store(action="add",
        content=f"Round {i}: hypothesis='{hypothesis}' → IC={ic}, ARR={arr}")
```

### Required Infrastructure

```
~/.hermes/quant/
├── data/
│   ├── csi300_features.h5     # Pre-computed features
│   └── csi300_labels.h5       # Forward returns labels
├── factors/
│   ├── alpha_20.py             # Initial factor set
│   ├── round_01_factor.py      # Each new factor
│   └── sota_factors/           # Current best factor library
├── models/
│   ├── baseline_lgb.py         # Starting model
│   └── sota_model.pkl          # Current best model
├── backtest.py                 # Backtest harness
└── config.yaml                 # Loop config
```

### Gap vs RD-Agent

| Component | RD-Agent | Hermes equivalent |
|-----------|----------|-------------------|
| Backtest engine | Qlib (professional) | Custom backtest.py or Qlib API |
| Sandbox isolation | Docker | terminal() directly |
| Co-STEER knowledge graph | SQLite (task,code,feedback) | fact_store / memory |
| Code gen fault tolerance | Auto-retry + DAG scheduling | Manual retry logic |
| Automation | Fully automatic 36 rounds | Needs user kickoff (cronjob) |
| Qlib integration | Deep coupling | Optional—use yfinance instead |

For practical reproduction, `pip install rdagent` is faster. The Hermes approach is valuable when you want to integrate R&D-Agent-style factor iteration with Vibe-Trading's existing data sources and backtest engines, or when you want to work with US/HK/crypto markets (RD-Agent is A-share focused).
