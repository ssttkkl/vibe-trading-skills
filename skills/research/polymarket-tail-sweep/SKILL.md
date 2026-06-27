---
name: polymarket-tail-sweep
description: 扫尾盘 — 扫描 Polymarket 即将到期的事件，按到期日排序，AI 筛选低风险高回报的送钱盘
version: 1.6.0
author: Hermes Agent
tags: [polymarket, prediction-markets, tail-sweep, 送钱盘]
---

# Polymarket 尾盘扫描（Tail Sweep）

扫描 Polymarket 即将到期的事件，按到期日排序，AI 判断哪些是低风险高回报的送钱盘。

## 本技能 vs polymarket-arb-scanner

| | 扫尾盘（本技能） | 子盘套利扫描器 |
|:--|:---------------|:-------------|
| 定位 | 快速索引发掘 | 深度执行分析 |
| 粒度 | 事件级 | 子市场级 |
| 价差 | 无 | 有（bestBid/Ask） |
| CLOB/AMM | 无 | 有 |
| 决策 | 人工 | AI过滤+调研+推荐 |

先用扫尾盘发现候选，再用子盘扫描器做深度分析。

## 参考文件

本技能附带以下参考文件（`references/` 目录）：

- `references/gamma-api-query-patterns.md` — Gamma API 查询模式和常见坑
- `references/strait-of-hormuz-traffic-analysis.md` — 霍尔木兹海峡通行量送钱盘分析（跨到期日价格推理）
- `references/warships-hormuz-assessment.md` — 军舰通过霍尔木兹概率评估
- `references/gold-settlement-arb-pattern.md` — 黄金GC六月结算价套利案例（2026-06-27）
- `references/middle-east-market-clusters.md` — 中东市场族系与联动关系
- `references/strait-of-hormuz-june-analysis.md` — 霍尔木兹6/30到期分析

- `references/volatility-price-range-analysis.md` — 结算范围盘波动率感知分析（黄金/BTC/ETH等价格盘必备，详见第4h节）
- `scripts/volatility_dashboard.py` — 实时行情+30d波动率数据采集（供 cron 流水线使用）
## 前置条件

- 无需 API Key，全公开接口
- 依赖 `~/.hermes/skills/research/polymarket/scripts/polymarket.py`（查询盘口详情）
- Python3 标准库（json, urllib, datetime）

## 核心逻辑

### 第零步：流动性门槛（铁律）

**送钱盘推荐最低标准 — 必须在推荐前用 Gamma API 独立核实：**

| 等级 | 量 | 可操作性 | 
|:----|:--:|:--------|
| ✅ **可推荐** | **>$1M** | CLOB订单簿，零滑点，价格可执行 |
| ⚠️ 仅小资金 | $1K-$1M | AMM盘，$400以内可玩但需标注滑点风险 |
| ❌ 不推荐 | <$1K | AMM极薄盘，价格不靠谱，API数据与显示严重不一致 |

**核实方法：**
```bash
curl -s 'https://gamma-api.polymarket.com/events/{event_id}' | python3 -c "
import json,sys; e=json.load(sys.stdin)
for m in e.get('markets',[]):
    vol = float(m.get('volume',0))
    tok = m.get('token_id','')
    print(f'真实量: \${vol:,.0f} | CLOB: {\"✅\" if tok else \"❌ AMM\"} | 价格: {m.get(\"outcomePrices\",\"?\")}')"
```

**经验教训（2026-06-27）：** 扫尾盘脚本显示韩国军舰量 $1.1M，API核实仅 $446，相差 2500 倍。**永远不要相信脚本显示的 volume，必须以 API 返回值为准。**

### 第一步：扫数据

用 Gamma API 按交易量降序拉取活跃事件：

```
GET gamma-api.polymarket.com/events?closed=false&limit=100&offset={N}&order=volume&ascending=false
```

参数：
- `limit=100`（单页上限）
- `offset` 翻页，默认扫 **3页 = 300事件**（更多页收益递减，且包含大量零量垃圾盘）
- 只保留 **N天内到期**（默认14天）

```python
def scan_raw(max_days=14, pages=3):
    """输出所有即将到期的事件+盘口原始数据"""
    ...
```

⚠️ **快速脚本 (`polymarket_tail_sweep.py`) 已知数据问题：**

| 问题 | 表现 | 影响 |
|:----|:----|:-----|
| **交易量严重夸大** | 脚本报告的 $1.1M，实际 API 原始数据仅 $446 | 低量盘被误判为可操作 |
| **到期日错误** | 12月到期的盘显示 "2d 15h" | 过期判断失真 |
| **盘口创建** | 脚本显示的"盘口"可能查不到对应事件/市场 | 无法验证规则 |
| **价格偏差** | 脚本显示 No @ 92.5¢，实际 92.1¢ | ROI 计算有出入 |

**❗ 铁律：脚本输出只是候选索引，决策前必须用 Gamma API 独立验证每个候选盘的实际量和价格。**

### 第一步半：独立验证候选盘

对脚本显示的量 ≥ $50K 的候选，用 Gamma API 逐条验证：

```bash
# 用 offset 翻页查低量事件（title/tag 搜索不可靠）
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset={OFFSET}&order=volume&ascending=false' \
  | python3 -c "
import json,sys
data = json.load(sys.stdin)
for e in data:
    for m in e.get('markets',[]):
        q = m.get('question','')
        if '关键词' in q:
            print(f'Event: {e.get(\"title\",\"?\")}')
            print(f'Q: {q}')
            print(f'真实量: \${float(m.get(\"volume\",0)):,.0f}')
            print(f'真实价格: {m.get(\"outcomePrices\",\"?\")}')
            print(f'规则: {e.get(\"description\",\"\")[:400]}')
"
```

经验值：脚本报告的 6位数量 → 实际可能只有 3位数量，**不要以脚本显示的量为准**。

### 第二步：按到期日排序

```python
near = [m for m in data if 0 <= m['days'] <= max_days]
near.sort(key=lambda x: x['days'])
```

不要按 APY/ROI/交易量排序——尾盘的意义是按 **到期急迫性** 排列。

### 第三步：AI 筛选

逐条看 No 价格，分四档判断：

| No价格 | 类型 | ROI参考 | 典型年化 | 判断逻辑 |
|:------:|:----|:-------:|:--------:|:---------|
| **98-100¢** | 🟢 确定性尾盘 | 0.1-2% | **15-100%** | 几乎必中的短期赌注 |
| **85-99¢** | 🟡 送钱盘 | 1-18% | 变化大 | 核心关注区间，用 `--no-min/--no-max` 灵活调整 |
| **80-89¢** | 🟠 价值盘 | 12-25% | 变化大 | 弹性大，适合淘金 |
| **<80¢** | 🔴 投机盘 | >25% | 虚高 | APY看着高但风险匹配 |

> ⚠️ **送钱盘价格范围可配置**：脚本的 `--no-min`（默认0.90）和 `--no-max`（默认0.97）参数允许灵活调整。例如 `--no-min 0.85 --no-max 0.99` 可看到更多候选。调低下界会增加ROI但也增加false positive风险。

**AI 判断送钱盘 checklist：**

- [ ] No 价格（越高越确定）
- [ ] 到期天数（越近越确定）
- [ ] 规则是否客观可量化（Portwatch/IMF数据 > 主观判断）
- [ ] 是否有过期的子市场全部判 No（历史验证）
- [ ] 排除体育赛事（比分/输赢不可预测）
- [ ] 深度/交易量是否够大（>$1M 可交易）
- [ ] 尾部风险（会不会突然触发）

### 第四步：深度分析（Deep Dive）

对送钱盘候选，按 ROI 排序后做系统性深度分析，最终只推荐**一个**。

#### 4a. 查找事件规则

`polymarket.py` 需要精确 slug，经常找不到。用 Gamma API 替代：

```bash
# 方法1：按关键词搜事件列表（title 参数不可靠，本地 grep 替代）
curl -s "https://gamma-api.polymarket.com/events?closed=false&limit=200&order=volume&ascending=false" \
  | python3 -c "import json,sys; [print(f'{e.get(\"title\",\"?\")} | id: {e.get(\"id\",\"?\")}') for e in json.load(sys.stdin) if '关键词' in e.get('title','').lower()]"

# 方法2：拿到 event_id 后查完整规则
curl -s "https://gamma-api.polymarket.com/events/{event_id}" \
  | python3 -c "import json,sys; e=json.load(sys.stdin); print(e.get('description',''))"
```

**⚠ 坑：** Gamma API 的 `?title=` 参数搜索不工作（传关键词照样返回世界杯等无关事件）。必须本地 grep 过滤。**不要**用 `?tag=` 参数，也同样不可靠。

**🔍 技巧：搜索低量事件需要加大 offset**

扫描脚本只覆盖前 3-5 页（300-500 事件），但有价值的薄盘往往在更深的位置：

```bash
# 在 offset=200 附近找军舰/地缘政治等 niche 市场
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset=200&order=volume&ascending=false' \
  | python3 -c "
import json,sys
data = json.load(sys.stdin)
for e in data:
    for m in e.get('markets',[]):
        q = m.get('question','')
        if '关键词' in q:
            vol = float(m.get('volume',0))
            print(f'{q[:60]} | Vol: \${vol:,.0f} | {m.get(\"outcomePrices\",\"?\")}')
"
```

注意事件名可以包含多个子市场（如 "Which countries will send warships through X" 事件下有 20+ 子市场），每个子市场独立定价。`?title=` 搜不到这些事件——**必须用 offset 扫描 + 本地文本匹配**。

#### 4b. 检视历史子市场验证

看所有子市场（含已过期/已结算的）确认历史模式：

```python
# 在 4a 的 curl 输出中，markets[] 包含所有子市场
# 已过期子市场 prices=["0","1"] 或 ["1","0"] 表示已结算
# 
# 送钱盘关键信号：同一个系列多个月全部判 No
# 例：Pahlavi 1月No、2月No、3月No...当前月No价格≈93¢
# 连续N个月全No = 极强的模式验证
```

#### 4c. 评估规则客观性

| 规则类型 | 风险等级 | 说明 |
|:---------|:--------:|:-----|
| 数据驱动（IMF/Portwatch 等） | 🟢 低 | 完全客观，无争议风险 |
| 物理事实（入境/辞职/公告等） | 🟡 中 | 事实可验证，但有解释空间 |
| 主观判断（"侮辱"/"成功"/"最好"等） | 🔴 高 | 争议风险大，规避 |

**⚠ 规则时间窗陷阱（2026-06-27实战发现）：**

有的盘口子市场名称写着"XX by June 30?"，但事件级规则实际上限定了一个完全不同的时间窗。例如以色列议会解散盘：

- 市场标题：Israeli parliament dissolved by June 30?
- 事件规则：Knesset dissolved between September 3 and October 31, 2025 → Yes
- 注意是2025年，不是2026年！

规则时间窗已过，但市场仍在交易（Yes @ 6%）。这种盘不碰——要么定价混乱，要么规则更新了但没同步到事件描述。

排查方法：
```
curl -s 'https://gamma-api.polymarket.com/events/{event_id}' | python3 -c "
import json,sys; e=json.load(sys.stdin)
desc = e.get('description','')
import re
years = set(re.findall(r'20\d{2}', desc))
print('规则中提及的年份:', sorted(years))
print('描述片段:', desc[:200])
"
```

#### 4e. 薄盘与小资金分析（< $50K 量）

当用户资金量小（如 $400）时，**薄盘反而是优势**：

| 资金量 | 薄盘策略 | 厚盘策略 |
|:------|:---------|:---------|
| < $1K | ✅ 可用。可能吃到价格偏离的利润 | ✅ 零滑点但价差小 |
| $1-10K | ⚠️ 滑点开始显著 | ✅ 推荐 |
| > $10K | ❌ 基本买穿整个池子 | ✅ 唯一选择 |

**薄盘执行注意：**

1. **CLOB vs AMM** — 检查 token_id/condition_id是否为空：
   - 有值 = CLOB（订单簿交易，可以看深度）
   - 空 = AMM（自动做市商池，滑点取决于池子大小）

2. **AMM 滑点估算**：买入量超过总 Volume 的 10% 时，滑点可能吃掉 30-50% 的预期利润

3. **价格波动**：薄盘 API 返回的价格可能在几分钟内变化 3-5¢，显示价不一定能成交

4. **验证脚本数据**：脚本可能将 $446 显示为 $1.1M——**永远用 API 二次验证量**

```bash
# 验证薄盘的实际量和价格
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset=200&order=volume&ascending=false' \
  | python3 -c "
import json,sys
data = json.load(sys.stdin)
for e in data:
    for m in e.get('markets',[]):
        q = m.get('question','')
        if 'south korea' in q.lower() and 'warship' in q.lower():
            prices = m.get('outcomePrices','?')
            vol = float(m.get('volume',0))
            tok = m.get('token_id','')
            cond = m.get('condition_id','')
            print(f'真实量: \${vol:,.0f}')
            print(f'真实价格: {prices}')
            print(f'CLOB(token_id): {\"有\" if tok else \"无 → AMM盘\"}')
            print(f'Condition ID: {\"有\" if cond else \"无\"}')
"
```

#### 4f. 跨到期日价格对比（推断当前数据）

对同一事件不同到期日的子市场，对比其价格可以反推当前实际状态：

**技巧：同一事件，两个到期日，价格差 = 时间价值**

```
例：Strait of Hormuz 通行恢复正常
├── 6/30到期: Yes @  4.75¢（市场认为2.5天内恢复概率=5%）
└── 7/31到期: Yes @ 49.5¢（市场认为33天内恢复概率=50%）

推理：如果当前通行量已经接近60阈值，
      6/30价格不会只有4.75¢
      → 当前7日均线大概率远低于60（估30-40艘/天）
      → 2.5天内翻倍恢复到60+几乎不可能
      → 6/30 No @ 95.25¢ 是安全送钱盘
```

**适用场景：** 任何有多个到期日子市场系列（月度/季度到期子市场）

**不适用场景：** 不同到期日对应不同规则/条件的事件

#### 4g. No价格 vs 真实概率（价差套利分析）

**核心洞察（来自用户纠正）：** 送钱盘 No 价格 ≠ 真实概率。市场定价和真实概率之间的差价就是套利空间。

```
中国市场定价 No @ 88¢ → 隐含 Yes 概率 = 12%
真实概率：2.5天派军舰 ≈ 0.1%（真实No ≈ 99.9¢）
                            ↓
                    差价 11.9¢ = 套利空间
```

**发现价差的方法：**

1. **基本面分析** — 基于物理限制判断真实概率（韩国2.5天派军舰过霍尔木兹≈不可能）
2. **历史模式验证** — 连续多月子市场全No（如Pahlavi 1-6月全部No）
3. **规则逻辑推理** — 阈值在2-3天内无法达到（如Portwatch 7日均线翻倍所需时间）

**价差与流动性的权衡：**

| 盘口类型 | 价差空间 | 流动性 | 说明 |
|:---------|:--------:|:------:|:-----|
| 厚盘（>$1M） | 2-5¢ | ✅ 零滑点 | 价差小但可重仓 |
| 薄盘（<$1K） | 10-15¢ | ⚠️ 滑点大 | 小资金可以吃价差 |
| 中盘（$1K-$50K） | 5-10¢ | 🟡 有滑点 | 需评估执行成本 |

**⚠️ 关键陷阱：** 薄盘的高ROI只是名义值。如果买入量超过总Volume的10%，AMM滑点会大幅缩小实际价差。**最终实得ROI = 名义ROI - 滑点损耗。**

多候选对比后推荐**一个**，按以下优先级：

1. **规则客观性** → 数据驱动 > 物理事实 > 主观判断
2. **历史验证强度** → 连续多月全 No 最强
3. **流动性** → >$1M 可操作
4. **到期时间** → 2-3天最佳（时间越短尾部风险越低）
5. **ROI** → 5-10% 为合理送钱盘范围，>10% 需额外谨慎（时间窗口长或规则有隐患）

```bash
# 举例：最终推荐输出格式
🥇 最终推荐: Reza Pahlavi 进入伊朗 — No @ 93.5¢
   理由: 规则客观(物理入境) + 连续6个月全No + 量$1.9M + 2.5天到期
   风险: 美伊核谈重大突破 → Pahlavi受邀回国
```

#### 4h. 波动率感知分析（价格范围盘专用）

> 针对 Gold $3800-$4200、BTC >$60K、ETH dip to $1,400 等价格范围盘。
> 详细方法论见 `references/volatility-price-range-analysis.md`。

**铁律：当前价格在范围内 ≠ 到期时也在范围内。**

分析步骤：

1. **获取波动率数据** — 用 `scripts/volatility_dashboard.py` 自动输出30d范围+24h变化

2. **评估安全边际** — 当前价格在结算范围的什么位置？
   ```
   Gold $3800-$4200, 当前$4,091, 30d范围$3,800-$5,000
   → 距上限仅 $109 (占范围8%)，以24%月波动率，3天内可能突破
   ```

3. **检查到期前宏观事件** — 上网搜索未来N天的重要经济数据/央行决议

4. **综合评分**：

   | 信号 | 判断 |
   |:----|:----|
   | 价格在范围中间 + 低波动 | ✅ 安全 |
   | 价格在范围边界 + 高波动 | ❌ 高风险 |
   | 今天到期 + 当前价在范围内 | ✅ 确定 |

5. **跨到期日反推** — 有多个到期子市场时，对比价格差推断当前状态：
   ```
   霍尔木兹6/30 Yes @ 4.75¢ vs 7/31 Yes @ 49.5¢
   → 4.75¢说明当前通行量远低于正常 → 6/30 No 安全
   ```

**用户纠正（2026-06-27）：** 起初只看了 Gold 当前 $4,091 在 $3800-$4200 范围内就判断"送钱"，忽略了24%月波动率和即将到来的核心PCE数据。必须结合波动率+宏观事件综合判断。

### 与 vibe-trading 协同的架构

当需要深度分析时，可将扫描数据发送到 vibe-trading（通过 HTTP API localhost:8000）进行金融级判断：

```
┌───────────────────────────────────────────────────────────┐
│ Cron AI（12h轮询）                                        │
│                                                           │
│  1. run_arb_scan.sh → 原始扫描数据 + 波动率看板            │
│  2. Cron AI 用 web_search 上网查新闻：                     │
│     → 价格盘：查宏观/波动/宏观事件日历                     │
│     → 地缘盘：查最新局势/谈判进展                          │
│     → 输出"调研证据"（结构化，附来源）                     │
│  3. 调研证据 + 扫描数据 → vibe-trading API session：      │
│     → vibe-trading 不用再上网（避免 Jina Reader 451）     │
│     → 只用 load_skill/backtest 做金融分析判断              │
│  4. 输出最终报告                                         │
└───────────────────────────────────────────────────────────┘
```

**⚠️ Jina Reader HTTP 451 陷阱（2026-06-27实测）：**
vibe-trading 的 `read_url` 走 Jina Reader 共享 IP，金融网站（Reuters/Yahoo Finance）频繁返回 451 阻断，导致 session 卡在 active 状态 20+ 分钟无输出。
**修复方法：** 部署本地 Jina Reader Docker (`ghcr.io/jina-ai/reader:oss`)，或让 Cron AI 完成所有网络调研后再发给 vibe-trading 做纯分析。

**vibe-trading prompt 模板（调研证据+分析指令）：**

```markdown
## 任务：审查 Polymarket 候选盘

以下是扫描数据和已完成的调研证据（互联网查证完毕），
请你用金融分析能力做最终判断，不需要再上网。

### 调研证据摘要

**#1 Gold $3,800-$4,200（3天到期）**
- 当前 $4,091 | 30d范围 $3,800-$5,000 | 波动率24%
- 6/29有核心PCE数据
- 结论：价格在范围内但靠近上限，高波动有突破风险

**#5 BTC >$60K（今天到期）**
- 当前 $60,369，今天到期
- 结论：已超$60K，Yes @ 90.5¢ 送钱

### 你的任务
1. 用 load_skill(technical-basic) 等技术分析参考
2. 综合证据，输出P0/P1/排除分级
3. 给出$100分配建议
```

### 第五步：输出格式

按到期日分组：

```
==========================================================================
📋 尾盘送钱候选 — 按到期日排序
==========================================================================

━━━ 6/30到期（2.5天后）━━━

🥇 盘口: Will Apple be the largest company in the world by June 30?
   No @ 99.8¢ | ROI +0.3% | 年化≈44% | 量 $23.9M
   ✅ Apple已经是全球市值最大，剩2天不会变

🥇 盘口: Will the Iranian regime fall by June 30?
   No @ 99.9¢ | ROI +0.2% | 年化≈29% | 量 $64.8M
   ✅ 2.5天内政权倒台概率无限接近0

🥈 盘口: Strait of Hormuz returns to normal?
   No @ 94.9¢ | ROI +5.4% | 量 $38.0M
   ⚠️ 规则客观(IMF)，地缘风险中等

━━━ 7月1日到期（4天后）━━━
...
```

### 子盘级套利扫描器（v2，推荐使用）

脚本保存在 `~/.hermes/scripts/polymarket_arb_scanner.py`：

```bash
# 扫5天内到期、价格80-99¢、最低量$10K
python3 ~/.hermes/scripts/polymarket_arb_scanner.py --days 5 --price-min 0.80 --price-max 0.99 --min-vol 10000

# 收紧参数：3天、85-97¢、$50K量、价差<10%
python3 ~/.hermes/scripts/polymarket_arb_scanner.py --days 3 --price-min 0.85 --price-max 0.97 --min-vol 50000 --max-spread 10
```

**v2 相比 v1 的核心改进：**

| v1（tail_sweep） | v2（arb_scanner） |
|:-----------------|:------------------|
| 事件级聚合 | ✅ **子盘（market）级别**，看到每个子市场独立定价 |
| 脚本显示的量不可信 | ✅ 直接读 API 原始 `volume` 字段 |
| 只看 No 一个方向 | ✅ Yes/No **两个方向都扫** |
| 无价差信息 | ✅ 读 CLOB `bestBid`/`bestAsk` 算真实买卖价差 |
| 名义ROI | ✅ **实得ROI = 扣除价差后的可执行回报** |
| 到期日经常错 | ✅ 读 `endDateIso` 精确到期日 |

**v2 判断标准：**

| 字段 | 值 |
|:----|:---|
| `bestBid` / `bestAsk` | CLOB 真实买单/卖单价格 |
| `clobTokenIds` 非空 | ✅ **CLOB 盘** — 订单簿可交易 |
| `clobTokenIds` 为空 | ❌ **AMM 盘** — 滑点不可控，谨慎 |
| 价差 = `(ask - bid) / mid` | <5% 可操作，>10% 谨慎 |
| 有效买入价 | CLOB=ask价 / AMM=mid*(1+估滑点) |
| 实得ROI | 按有效买入价算的回报 |

### 快速扫描脚本（v1 旧版）

脚本保存在 `~/.hermes/scripts/polymarket_tail_sweep.py`：

⚠️ **v1 已知问题：** volume 严重夸大（韩国军舰显示 $1.1M 实仅 $446），到期日可能错误。**v1 只作候选索引，推荐用 v2。**

**v1 新增参数：**
```bash
--no-min 0.85   # 送钱盘No价格下限（默认0.90=90¢）
--no-max 0.99   # 送钱盘No价格上限（默认0.97=97¢）
```

```bash
python3 ~/.hermes/scripts/polymarket_tail_sweep.py --days 7 --top 20
```

参数：
- `--days` 到期窗口（默认7天）
- `--min-vol` 最低交易量（默认$50K）
- `--top` 显示数量（默认25）
- `--event-pages` 扫描页数（默认3页=300事件）
- `--no-min` 送钱盘No价格下限（默认0.90=90¢）
- `--no-max` 送钱盘No价格上限（默认0.97=97¢）

示例：`--no-min 0.85 --no-max 0.99` → 85-99¢范围，ROI更高但候选更多需仔细筛选

### 典型送钱盘特征

根据历史经验，Polymarket 上最容易出送钱盘的几类：

1. **"XX事件6/30前不会发生"系列** — 大量子市场在每月底到期，前几个月全部判No
   - 例：Pahlavi进入伊朗、Tim Walz辞职、中国入侵台湾
   - 规律：1-2月全No → 3月全No → ... → 当前子盘No价格虚高

2. **"XX公司全球最大"系列** — 几大科技公司互相竞争的子盘口
   - Apple 当前最大，剩下几天不可能被超越
   - 但注意苹果如果股价大跌可能被反超

3. **"XX人在6/30前进入伊朗"系列** — 包含大量不可能选项
   - Trump/Pete Hegseth/Benjamin Netanyahu 进伊朗=概率0
   - 规则分析：可能有人去谈判（美伊核谈），但特定人选不会

4. **地缘政治量化指标盘口** — 规则基于数据而非定性判断
   - 霍尔木兹海峡：IMF Portwatch 7日均值
   - 这类规则客观，争议少
