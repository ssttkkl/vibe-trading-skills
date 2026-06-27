---
name: polymarket-vibe-arb
description: Polymarket 尾盘扫描 → vibe-trading 分析。扫子盘级数据 → AI 原则过滤 → 原始候选数据发到 vibe-trading API 全权调研（不预填数据不假设工具）→ 输出完整分析报告
version: 1.2.0
tags: [polymarket, vibe-trading, 套利, 送钱盘]
---

# Polymarket Vibe-Arb

联动扫描器 + vibe-trading 做深度分析。包含方法论（找送钱盘的原则、规则分析技巧、波动率感知分析）和自动化流水线（扫描→过滤→vibe-trading 全权调研）。

## 核心原则

**只喂原始数据，让 vibe-trading 全权调研。** 不加行情、不假设工具有什么、不预先上网查新闻。

实测（2026-06-27）：直接发候选表，vibe-trading 自己拉了 yfinance 实时价、OVX/BVIV 期权链隐含波动率、搜到 US 6/26 打击伊朗新闻，报告质量优于预调研。

## 自动化流水线

```
① run_arb_scan.sh → 扫描数据
② AI 原则过滤（排除体育/名人/meme/垃圾流动性）
③ 原始候选数据 → vibe-trading API session
④ vibe-trading 全权调研
⑤ 轮询 → 报告 → QQ
```

### Step 1：扫数据

```bash
cd ~/.hermes/scripts
python3 polymarket_arb_scanner.py \
  --days 7 --price-min 0.80 --price-max 0.99 \
  --min-vol 10000 --event-pages 5 --top 100 --max-spread 15
python3 volatility_dashboard.py
```

### Step 2：AI 过滤原则（不要关键词硬编码）

| 排除 | 保留 |
|------|------|
| ✅ 体育结果（足球小组赛、比分、出线） | 价格/结算范围盘（黄金/WTI/BTC/ETH） |
| ✅ 名人行为/meme（马斯克推文数） | 地缘政治盘（伊朗/以色列/霍尔木兹/俄罗斯） |
| ✅ 主观裁决盘（定义模糊争议大） | 科技估值/产品盘（OpenAI/SpaceX/GPT） |
| ✅ 价差>10% 且 量<$50K 的垃圾盘 | — |

只保留原始数据（盘口名、方向、价格、ROI、到期日、量）传给 vibe-trading。

### Step 3：发到 vibe-trading

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

- **背景说明**：Polymarket 二元期权（买 No @ 90¢ = 到期判 No 赚 11.1%）
- **候选盘按类型分组**，只附原始数据（名称、方向、价格、ROI、到期日、量）
- **一次性完成全部调研，不留未完成项：**

**1. 实时行情**
- 拉所有价格相关资产（黄金、WTI、BTC、ETH、SPCX）的实时价
- 拉期权隐含波动率（WTI→OVX, 黄金→GVZ, BTC→BVIV/DVOL）
- 拉近期 K 线

**2. 规则确认**
- 找到每个盘口的 Resolution Rules 原文
- 检查时间窗陷阱（规则写的年份和到期日是否一致）
- 确认裁决来源（哪家机构/媒体判定结果）
- 科技估值盘确认估值来源（NPM、公开市值还是融资轮）
- 评估规则客观性：数据驱动 > 物理事实 > 主观判断

**3. 概率计算**
- 价格盘：用期权 IV 算 z-score 和真实概率，对比市场定价
- 地缘盘：按最新新闻和物理限制判断
- 如果同一事件有多个到期日，对比价格差反推当前状态
- 考虑尾部风险（地缘升级、黑天鹅）
- 如果有历史过期子市场，去查它们为什么判 No——基本面原因现在是否仍然成立

**4. 基本面调研**
- 价格盘：宏观新闻（Fed、CPI、地缘、供需）
- 地缘盘：每个事件的最新具体新闻
- 科技盘：融资/估值/产品发布动态

**5. 价差评估**
- 对比你的概率和市场概率，差距是否足够大？
- 标注方向不明确的盘（Yes 代表什么？）
- 薄盘标注滑点风险

- **输出格式**：每个盘口的完整分析（实时价、波动率、期权概率、规则验证、基本面、价差评估）。**不分优先级、不给分配建议**——只呈现事实。

### Step 4：输出

vibe-trading 返回什么就发什么。超时说下次再试。

---

## 方法论：找送钱盘的原则

### 流动性门槛（铁律）

| 等级 | 量 | 可操作性 |
|:----|:--:|:--------|
| ✅ **可推荐** | **>$1M** | CLOB 订单簿，零滑点，价格可执行 |
| ⚠️ 仅小资金 | $1K-$1M | AMM盘，$400 以内可玩但需标注滑点 |
| ❌ 不推荐 | <$1K | AMM 极薄盘，价格不靠谱 |

**脚本显示的量不可信** — 扫尾盘脚本曾显示 $1.1M，API 核实仅 $446。**永远以 API 返回值（Gamma API）为准。**

### 价格分档

| No价格 | 类型 | ROI | 说明 |
|:------:|:----|:---:|:----|
| 98-100¢ | 🟢 确定性尾盘 | 0.1-2% | 几乎必中 |
| 85-97¢ | 🟡 送钱盘 | 1-18% | 核心关注区 |
| 80-84¢ | 🟠 价值盘 | 12-25% | 弹性大 |
| <80¢ | 🔴 投机盘 | >25% | APY 虚高 |

### 送钱盘 checklist

- [ ] No 价格越高越确定
- [ ] 到期越近越确定
- [ ] 规则客观可量化（数据驱动 > 物理事实 > 主观判断）
- [ ] 历史子市场全部判 No（同系列多个月验证）
- [ ] 排除体育/名人/meme
- [ ] 尾部风险可控

### 规则分析的坑

**Gamma API 搜索不可靠：** `?title=` 和 `?tag=` 参数经常不工作，必须用 offset 翻页 + 本地 grep 过滤。

**规则时间窗陷阱（2026-06-27 发现）：** 某盘口标题写"XX by June 30?"，但事件规则里限定的是 2025 年的窗口，市场仍在交易。排查方法：
```bash
curl -s 'https://gamma-api.polymarket.com/events/{event_id}' | python3 -c "
import json,sys,re; e=json.load(sys.stdin)
desc = e.get('description','')
print('年份:', sorted(set(re.findall(r'20\\d{2}', desc))))
"
```

**规则客观性分级：**

| 类型 | 风险 | 说明 |
|:-----|:---:|:-----|
| 数据驱动（IMF/Portwatch） | 🟢 低 | 完全客观 |
| 物理事实（入境/辞职） | 🟡 中 | 可验证但有解释空间 |
| 主观判断（侮辱/成功/最好） | 🔴 高 | 规避 |

### 跨到期日价格对比

同一事件多个到期日，价格差 = 时间价值。对比可反推当前状态：

```
霍尔木兹 6/30 Yes @ 4.75¢ vs 7/31 Yes @ 49.5¢
→ 4.75¢ 说明当前通行量远低于 60 阈值
→ 2.5 天翻倍到 60+ 不可能 → 6/30 No 安全
```

### No 价格 ≠ 真实概率

市场定价和真实概率的差价就是套利空间：

```
韩国军舰 No @ 88¢ → 隐含 Yes 概率 12%
真实概率：2.5 天派军舰 ≈ 0.1%（真实 No ≈ 99.9¢）
                                   ↓
                           差价 11.9¢ = 套利空间
```

发现价差的方法：
1. **基本面分析** — 基于物理限制（2.5 天派军舰不可能）
2. **历史模式** — 连续多月全 No
3. **规则逻辑** — 阈值在 2-3 天无法达到

### 波动率感知分析（价格盘专用）

**铁律：当前价在范围内 ≠ 到期也在范围内。**

1. 获取波动率数据（`volatility_dashboard.py`）
2. 评估安全边际：当前价在范围的什么位置？
3. 检查到期前宏观事件（Fed、CPI、非农）
4. 用期权链隐含波动率计算概率

### 薄盘与小资金

资金量<$1K 时薄盘反而是优势——可能吃到价格偏离的利润。注意：
- CLOB 盘用 bestBid/Ask 看深度
- AMM 盘买入超总量 10% 时滑点吃掉 30-50% 利润
- 薄盘价格几分钟变动 3-5¢

### 典型送钱盘特征（基本面驱动，非模式重复）

1. **"XX 事件在短期内不可能发生"** — 物理限制决定（某人几天内不可能回国、政府几天内不可能倒台）
2. **"XX 公司全球最大"系列** — 几天内市值不可能被反超
3. **"XX 人在 6/30 前进入伊朗"系列** — 特定人选不可能（Trump/Pete Hegseth/Netanyahu 进伊朗=概率 0）
4. **地缘政治量化指标盘** — IMF Portwatch 等客观数据源，规则清晰无争议

## 参考文件

- `references/gamma-api-query-patterns.md` — Gamma API 查询模式和坑
- `references/strait-of-hormuz-traffic-analysis.md` — 霍尔木兹通行量分析（跨到期日推理）
- `references/warships-hormuz-assessment.md` — 军舰通过霍尔木兹概率
- `references/gold-settlement-arb-pattern.md` — 黄金六月结算价套利案例
- `references/middle-east-market-clusters.md` — 中东市场族系与联动
- `references/strait-of-hormuz-june-analysis.md` — 霍尔木兹 6/30 分析
- `references/volatility-price-range-analysis.md` — 波动率感知分析（价格盘）
- `references/portwatch-api.md` — Portwatch API 数据源
- `references/options-chain-probability.md` — 期权链概率验证方法论
- `references/2026-06-27-analysis-case-study.md` — 实战案例

## 前置条件

- `vibe-trading serve`（localhost:8000）
- 本地 Jina Reader Docker（端口 3000，防 451 阻断）
- `~/.hermes/scripts/` 下有扫描脚本 + `poll_session.py`
