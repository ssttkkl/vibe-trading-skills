# Polymarket Gamma → prompt 拼装笔记

这份笔记用于手工或脚本化把 Gamma market 字段拼装进 vibe-trading prompt；脚本应放在技能目录 `scripts/` 下，避免依赖全局临时脚本。

## 适用场景

- 已知 Polymarket market slug，需要直接生成 vibe-trading 深度调研 prompt
- 需要把盘面字段和规则原文自动塞入 `references/polymarket-deep-research-prompt.md`
- 不想手工复制 Yes/No 价格、成交量、bestBid/bestAsk、spread、clobTokenIds

## 可靠取数方式

1. 先查 market：
   - `GET /markets?slug={slug}`
2. 取首条 market 作为目标盘：
   - `question` / `title`
   - `slug`
   - `conditionId` 或 `id`
   - `outcomes`
   - `outcomePrices`
   - `volume`
   - `liquidity`
   - `bestBid`
   - `bestAsk`
   - `spread`
   - `lastTradePrice`
   - `endDate`
   - `description`（作为规则原文）
   - `clobTokenIds`
3. 解析时把 `outcomes` 和 `clobTokenIds` 当字符串数组处理，不要按数值数组解析。

## 生成 prompt 的字段映射

- `{{market_title}}` ← market question/title
- `{{slug_or_event_id}}` ← `slug / conditionId`
- `{{yes_price}}` ← outcomePrices[0]
- `{{no_price}}` ← outcomePrices[1]
- `{{volume}}` ← volume
- `{{orderbook_summary}}` ← `bestBid / bestAsk / spread / liquidity`
- `{{resolution_rules}}` ← description
- `{{similar_markets}}` ← 保守的相似盘摘要
- `{{candidate_list}}` ← 单盘时填 `Single market only`

## 实践要点

- Gamma 接口在终端里最好带 `User-Agent: Mozilla/5.0`。
- 单盘分析时，先拿到真实 slug，再拉 market 详情，最后再拼 prompt。
- 如果只想把 prompt 发给 vibe-trading，不需要先做额外猜测，直接把原始字段喂进去即可。
