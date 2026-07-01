---
name: polymarket-vibe-arb
description: Polymarket 尾盘扫描与批量并列调研：筛盘、传原始候选、让 vibe-trading 做全权深度分析并输出结论。
version: 1.2.2
tags: [polymarket, vibe-trading, 套利, 送钱盘]
---

# Polymarket Vibe-Arb

用扫描器找候选盘，再把**原始候选数据**交给 vibe-trading 做并列深度调研。核心目标：找到**尾盘套利**里最值得下注的盘——优先看事件确定概率、可执行性、尾部风险和剩余套利空间，而不是讨论市场定价是否“合理”。

## 核心原则

- **只喂原始数据，让 vibe-trading 自己调研。** 不预填结论，不假设工具，不代查新闻。
- **重点是尾盘套利最大化。** 市场定价是否“合理”不是终点，关键是事件确定概率下的剩余套利空间。
- **批量扫描必须并列看待候选盘。** 不写成“主盘 + 补充盘”。
- **主筛区看对称区间。** 优先看 `Yes/No 85–99.5¢` 的盘；`Yes 100¢` 这类饱和盘默认降权，只在“是否已经没空间”时作为排除/确认项。
- **只保留可复用内容。** 案例、误判长文、一次性分析不要长期留在 `references/`。

## 工作流

```text
单盘：Gamma/页面抓规则与盘口 → 填单盘模板 → 发 vibe-trading → 轮询 → 报告
批量：扫描子盘数据 → AI 原则过滤 → 原始候选数据 → vibe-trading session → 轮询 → 报告 → QQ
```

- 单盘分析直接用 `references/polymarket-deep-research-prompt.md` 的单盘版。
- 批量扫描默认用并列版，不要写成主盘 + 附属盘。
- 如果用户只要求“先扫一轮 / 先看候选”，先返回候选清单，不要主动发 vibe-trading。

- 多到期日/同规则事件要**并列看待**，不要写成“主盘 + 补充盘”。
- 先找事件页/slug，再拉 Gamma；不要依赖标题模糊搜索去猜事件，容易命中无关盘。

### 扫描

```bash
cd ~/.hermes/skills/finance/polymarket-vibe-arb/scripts
python3 polymarket_arb_scanner.py --days 7 --price-min 0.80 --price-max 0.99 --min-vol 10000 --event-pages 5 --top 100 --max-spread 15
python3 volatility_dashboard.py
```

> 说明：脚本输出只是初筛。量、价差、流动性最后仍以 Gamma API / 实盘可交易性为准。

#### 指定到期窗口扫描（不要只用 `--days` 近似）

当用户给出明确日期窗口（例如“不包含 6/30，7/15 之前到期”）时，优先按 Gamma `/markets` 的 `end_date_min` / `end_date_max` 做窗口分页，而不是只扫事件页再按 `--days` 近似。建议口径：

- 用 `end_date_min=YYYY-MM-DDT00:00:00Z` 与 `end_date_max=YYYY-MM-DDT00:00:00Z`；结束日按 `< end_date_max` 理解。
- 配合 `volume_num_min=10000`、`closed=false`、`active=true`、`limit=100`、`offset += 100` 分页；不要相信单页结果就是全量。
- 仍按 Yes/No 85–99.5¢、最大 spread、成交量/流动性过滤。
- 初筛时把体育、名人/meme、标题实际属于窗口外（如“by June 30”但因结算 endDate 落到 7/1）的盘降权/排除；但保留统计，方便用户核验漏筛。

### 发到 vibe-trading

```bash
SESSION_ID=$(curl -sf -X POST "http://127.0.0.1:8000/sessions" \
  -H "Content-Type: application/json" \
  -d '{"title": "Polymarket Arb $(date +%m-%d_%H:%M)"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin)['session_id'])")

CONTENT=$(cat /tmp/vibe_prompt.md | python3 -c "import json,sys; print(json.dumps({'content': sys.stdin.read()}))")
curl -sf -X POST "http://127.0.0.1:8000/sessions/$SESSION_ID/messages" \
  -H "Content-Type: application/json" -d "$CONTENT"

python3 poll_session.py "$SESSION_ID" --timeout 900
```

- 轮询前先确认 session 消息接口可读；必要时直接读 `GET /sessions/{session_id}/messages` 兜底。
- vibe-trading 的 message `content` 可能有 5000 字符上限。批量扫描不要把 20+ 个盘的完整规则原文全塞进去；先用脚本压缩：保留扫描口径、统计、slug、方向、Y/N、可执行买价、bid/ask/spread、volume/liquidity、endDate、规则前 100–200 字。候选按家族去重（如同一 Iran shipping 系列保留 2–3 个代表），目标控制在 4–5k 字内。
- 若 `poll_session.py` 期间出现短暂 connection refused，不要立即重启/kill 服务；先用 `GET /sessions/{session_id}/messages` 查看是否已有 assistant 完整回复，再决定是否继续等。

### 调研模板

- 单盘版 / 批量并列版：`references/polymarket-deep-research-prompt.md`
- Gamma 拉盘与字段映射说明：`references/polymarket-gamma-prompt-build.md`
- ISW StoryMap / ArcGIS 图层核验：`references/isw-arcgis-resolution-check.md`
- 批量扫描时默认使用**并列版**，不要写成单盘主市场。

## 送钱盘口径

只有同时满足下面四条，才考虑叫“送钱盘”：

- 规则客观可量化
- 价格明显偏离真实概率
- 流动性足够可执行
- 尾部风险可控

简化判断：

- `Yes/No 85-99.5¢`：核心筛选区，优先看确定性和可执行性
- `接近 100¢`：先判断是否已经到“几乎没空间”的尾盘，再决定是否排除
- `80-84¢`：价值盘
- `<80¢`：投机盘，APY 可能虚高

## 参考文件

- `references/polymarket-deep-research-prompt.md` — 直接复制给 vibe-trading 的 prompt 模板
- `references/polymarket-gamma-prompt-build.md` — Gamma API 拉盘与字段拼装笔记；优先 slug，再落到具体 market 字段
- `references/date-window-scan-and-vibe-prompt.md` — 明确到期窗口扫描、窗口边界坑、<5k 紧凑 vibe prompt 与 session 消息兜底
- `references/session-reply-forwarding.md` — 当用户要求转发 session 最新/最后一条回复时，先读完整消息流再取最新 assistant 消息

## 前置条件

- `vibe-trading serve`（localhost:8000）
- 本地 Jina Reader Docker（端口 3000，防 451 阻断）
- `scripts/poll_session.py`

## 常见坑

1. **批量盘写成主盘 + 候选盘。** 这会把分析重心带歪；批量必须并列比较。
2. **把脚本初筛当最终结论。** 初筛只负责过滤，最终判断交给 vibe-trading。
3. **vibe-trading 的外部实时价可能错。** 尤其 BTC/ETH 这类阈值盘，最终答复前必须用结算源/主流 API（如 Binance ticker）独立核验当前价；若与 vibe 报告差异会显著改变缓冲、概率或排序，把修正价发回同一个 session 要求重算，再交付修正版。详见 `references/realtime-price-correction.md`。
4. **留太多一次性案例。** `references/` 只放模板、工具型说明、可复用规则。
5. **忘了规则客观性。** 主观裁决盘优先降权，不要硬凑 alpha。
6. **直接按标题模糊匹配 Gamma 事件。** 同名/近名事件会误匹配，优先用 slug 或事件页上下文确认。

## 验证

- `references/` 里只留可复用模板/说明
- 脚本全部在 `scripts/` 下
- 批量扫描默认走并列版 prompt
- 送钱盘定义与模板口径一致
