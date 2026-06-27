# 29 Swarm Presets — Keyword Matching Reference

> **See also:** `references/run-swarm-behavior.md` (under `vibe-portfolio-analysis` skill) for each swarm's internal architecture — agents, DAG topology, variables, tool/skill assignments, output format, and the critical limitation that swarms cannot chain outputs between separate `run_swarm()` calls.

Each preset has keyword patterns (regex) and a confidence boost score.
When a prompt is submitted to `run_swarm()`, it scores all presets and picks the best match.
Default fallback: `equity_research_team`.

## Strategy / Decision

| Preset | Keywords | Boost |
|--------|----------|:-----:|
| `investment_committee` | 投委会, 投资决策, investment committee | 0.85 |
| `risk_committee` | 风控, VaR, 回撤, 压力测试, risk committee, drawdown | 0.90 |
| `global_allocation_committee` | 全球配置, 多资产, global allocation, cross-asset | 0.90 |
| `portfolio_review_board` | 组合复盘, 业绩归因, portfolio review | 0.85 |
| `macro_strategy_forum` | Fed, CPI, PMI, 货币政策, 宏观, macro | 0.90 |

## Quant / Research

| Preset | Keywords | Boost |
|--------|----------|:-----:|
| `quant_strategy_desk` | 多因子, 回测, 选股, quant strategy, multi-factor | 0.85 |
| `factor_research_committee` | IC/IR, factor, 因子研究, factor research | 0.90 |
| `ml_quant_lab` | ML, LSTM, XGBoost, 机器学习, 深度学习 | 0.90 |
| `statistical_arbitrage_desk` | 统计套利, statistical arbitrage, stat arb | 0.90 |
| `pairs_research_lab` | 配对交易, 协整, pairs trading, cointegration | 0.90 |
| `event_driven_task_force` | M&A, merger, earnings surprise, 事件驱动, 并购, 财报 | 0.90 |
| `equity_research_team` | 研报, 行业分析, equity research, deep dive | 0.85 |
| `fundamental_research_team` | 基本面, 财务, fundamental, deep dive | 0.85 |

## Market / Asset

| Preset | Keywords | Boost |
|--------|----------|:-----:|
| `etf_allocation_desk` | ETF, index fund, 指数基金, ETF配置 | 0.90 |
| `sector_rotation_team` | 板块轮动, 行业轮动, sector rotation | 0.85 |
| `derivatives_strategy_desk` | option, call, put, Greeks, IV, 期权, 衍生品 | 0.90 |
| `convertible_bond_team` | convertible, 可转债, CB | 0.90 |
| `credit_research_team` | credit, bond, YTM, 信用债, 城投, 利差 | 0.90 |
| `commodity_research_team` | commodity, crude, gold, copper, 商品, 原油, 黄金 | 0.90 |
| `fund_selection_panel` | FOF, mutual fund, 基金筛选, 选基 | 0.85 |

## Alternative / Intelligence

| Preset | Keywords | Boost |
|--------|----------|:-----:|
| `crypto_research_lab` | BTC, ETH, SOL, crypto, bitcoin, 加密, 数字货币 | 0.95 |
| `technical_analysis_panel` | RSI, MACD, K线, 技术分析, technical analysis | 0.85 |
| `sentiment_intelligence_team` | sentiment, fear and greed, 情绪, 恐慌 | 0.85 |
| `social_alpha_team` | social media, twitter, reddit, 社媒, 舆情 | 0.85 |
| `geopolitical_war_room` | geopolitical, war, sanction, 地缘, 危机场景 | 0.90 |

## Market labels (auto-extracted)

| Label | Matches |
|-------|---------|
| `A-shares` | A股, a股, 沪深, 上证, 深证, 创业板, 科创板, 中证, CSI |
| `HK` | 港股, 恒生, H股, 港交所, .HK |
| `US` | 美股, 纳斯达克, 标普, 道琼斯, S&P, .US |
| `crypto` | 加密, crypto, BTC, ETH, 币, USDT, 数字货币 |

## Risk tolerance (auto-extracted)

| Level | Matches |
|-------|---------|
| `conservative` | 保守, 低风险, 稳健偏保守 |
| `moderate` | 稳健, 中等风险, balanced |
| `aggressive` | 激进, 高风险, 进取 |
