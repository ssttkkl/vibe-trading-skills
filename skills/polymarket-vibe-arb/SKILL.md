---
name: polymarket-vibe-arb
description: Polymarket 尾盘扫描 → vibe-trading 分析。扫子盘级数据 → AI 原则过滤 → 原始候选数据发到 vibe-trading API 全权调研（不预填数据不假设工具）→ 输出 P0/P1 分级报告
version: 1.1.0
tags: [polymarket, vibe-trading, 套利, 送钱盘]
---

# Polymarket Vibe-Arb

联动扫描器 + vibe-trading 做深度分析。

## 核心原则

**只喂原始数据，让 vibe-trading 全权调研。** 不预填行情、不假设工具有什么、不预先上网查新闻。实测原始候选表直接发给 vibe-trading，它自己拉 yfinance 实时价、查期权链隐含波动率、搜最新新闻，报告质量比自己预调研更好。

## 架构

```
① run_arb_scan.sh → 扫描数据（子盘表 + 波动率看板供AI过滤参考）
② AI 原则过滤（排除体育/名人/meme/垃圾流动性）
③ 原始候选数据 → vibe-trading API session
④ vibe-trading 全权调研（工具自选）
⑤ 轮询 → 报告 → QQ
```

## 触发

```bash
cd ~/.hermes/scripts && bash run_arb_scan.sh
```

AI 读取输出 → 过滤 → 发 vibe-trading

## Step 1：扫数据

```bash
cd ~/.hermes/scripts
python3 polymarket_arb_scanner.py \
  --days 7 --price-min 0.80 --price-max 0.99 \
  --min-vol 10000 --event-pages 5 --top 100 --max-spread 15
python3 volatility_dashboard.py
```

输出供 AI 过滤使用（不传给 vibe-trading）：
- 子盘扫描表（价格80-99¢、7天到期、量>$10K、价差<15%）
- 波动率看板（AI 判断参考，不传入下方 prompt）

## Step 2：AI 过滤原则（不要关键词硬编码）

| 排除 | 保留 |
|------|------|
| ✅ 体育结果（足球小组赛、比分、出线） | 价格/结算范围盘（黄金/WTI/BTC/ETH） |
| ✅ 名人行为/meme（马斯克推文数） | 地缘政治盘（伊朗/以色列/霍尔木兹/俄罗斯） |
| ✅ 主观裁决盘（定义模糊争议大） | 科技估值/产品盘（OpenAI/SpaceX/GPT） |
| ✅ 价差>10% 且 量<$50K 的垃圾盘 | — |

过滤后只有原始数据（盘口名、方向、价格、ROI、到期日、量）——**不加行情、不加波动率、不注明 vibe-trading 用什么工具**。

## Step 3：发到 vibe-trading

```bash
SESSION_ID=$(curl -sf -X POST "http://127.0.0.1:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "Polymarket Arb $(date +%m-%d_%H:%M)"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

CONTENT=$(cat /tmp/vibe_prompt.md | python3 -c "import json,sys; print(json.dumps({'content': sys.stdin.read()}))")
curl -sf -X POST "http://127.0.0.1:8000/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" -d "$CONTENT"

python3 ~/.hermes/skills/finance/vibe-trading/scripts/poll_session.py "$SESSION_ID" --timeout 900
```

### prompt 模板

- **背景说明**：Polymarket 二元期权机制（买 No @ 90¢ = 到期判 No 赚 11.1%）
- **候选盘按类型分组**（价格/地缘/科技），只附原始数据（名称、方向、价格、ROI、到期日、量）
- **调研指令（关键）**：
  - **价格/结算范围盘**（黄金、WTI、BTC、ETH）：拉实时价格、近期K线、**期权链数据**判断。用期权隐含波动率验证概率
  - **地缘盘**：查最新局势新闻
  - **科技盘**：查融资/产品发布动态。SpaceX 查 SPCX 市值，GPT-5.6 查 Resolution Rules 定义
- **输出格式**：P0 确定性 / P1 价值 / 排除 + $100 分配建议
- **不加**：行情数据、波动率、工具假设、任何预处理

### 实测 prompt（2026-06-27）

发给 vibe-trading 的内容就是候选表 + 指令，干净简洁。vibe-trading 自行决定用 web_search / get_market_data / 期权链数据，结果报告发现了 US 6/26 打击伊朗的新闻（我们都没注意到），并正确使用正态近似+期权隐含波动率验证了所有价格盘概率。

## Step 4：输出

vibe-trading 返回什么就发什么。超时说"下次再试"。

## 前置条件

- `vibe-trading serve`（localhost:8000）
- 本地 Jina Reader Docker（端口 3000）
- `~/.hermes/scripts/` 下有 `polymarket_arb_scanner.py`、`volatility_dashboard.py`、`run_arb_scan.sh`
- `poll_session.py` 在 `~/.hermes/skills/finance/vibe-trading/scripts/poll_session.py`

## 参考

- `polymarket-tail-sweep` — 手动筛选方法论、规则分析技巧
- `vibe-trading` — HTTP API 调用方式
