---
name: vibe-portfolio-analysis
version: 5.3.1
description: 持仓分析 prompt，调用 vibe-trading 执行。架构：单 prompt 指定内置 swarm/skill（工具导向，不扮演角色）。4 步：equity_research_team → technical-basic + read_url → investment_committee × 1（一轮全部标的）→ 综合。API session 模式优先。
---

# Vibe Portfolio Analysis

持仓分析 prompt，调用 vibe-trading 执行。工具导向（不角色扮演），API session 模式优先。

## 触发条件

"分析持仓" / "跑一次分析" / "vibe-trading 跑一下"

## 前置条件

- **持仓数据来源**：`ft stock list`（finance-tracker，需 `HTTP_PROXY` 代理拉取 yfinance 实时价）
- `~/.vibe-trading/.env` — 配置了 LLM API key
- vibe-trading serve 运行中（tmux 启动，非 screen）

## 数据来源

持仓数据通过 `ft stock list` 查询（finance-tracker 统一管理）。旧 `~/.hermes/portfolio.json` 已停用（备份为 `portfolio.json.bak`）。

实时价格查询（当 ft stock list 的 yfinance 拉取失败时回退）：
```bash
curl -s --proxy http://127.0.0.1:7890 "https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?interval=1d&range=5d" -H "User-Agent: Mozilla/5.0"
```

港股/中概不需要 proxy。

## 用户偏好

- **语言**：中文
- **风格**：完整解释分析过程和证据链——含 TA 指标数值、多空论据、每一步用到的工具和数据来源
- **模式**：API session 模式（建 session → 直接发消息，不设 goal）
- **输出结构**：P&L 一览 → 逐个多空决策（含TA评分±5 + 多空辩论）→ 组合健康 → 追溯表
- **报告交付**：vibe-trading 返回完整报告后，保存至 `/tmp/vibe_report_<topic>_<date>.md`，以 `MEDIA:` 附件形式发送原始全量报告。用户要看完整版，不提炼摘要代替
- **SPCX 类型**：是 SpaceX 正股（非追踪股、非ETF）。`generate_vibe_prompt.py` 中 `ptype` 回退默认 `"股票"`（仅 QLD→杠杆、SMH/SGOV→ETF 有特殊映射）。名称由 yfinance `longName` 自动取为 `"Space Exploration Technologies Corp."`

## 持仓更新流程（portfolio.json）

用户会随时通知持仓变动。成本计算使用**平均成本法（均摊成本）**，非 FIFO。

### 更新规则

- **加仓**：shares 增加，total_cost 按新增成本加总
- **减仓**：shares 减少，total_cost = 原 total_cost - 卖出实收（price × shares - commission）。均价随之变化（卖亏↑卖赚↓）
- **清仓**：删掉该 position 条目
- **现金变化**：USD/CNY/HKD 直接改数值
- **负成本**：`total_cost` 可为负数（如 MRVL 3 股，total_cost: -44.59），代表已收回本金后的免费仓位
- **改完告知**：通知用户当前持仓数和现金余额

### 平均成本法计算示例

详见 `references/average-cost-method.md`。

```
原来: 8股 × $954.75 = $7,638.02
买入: 3股@$900 → 总成本 = $7,638 + $2,700 = $10,338（相加摊均价）
卖出: 2股@$969 → 回收 $1,938，总成本 = $10,338 - $1,938 = $8,400（卖赚了，均价↓）
卖出: 2股@$900 → 回收 $1,800，总成本 = $8,400 - $1,800 = $6,600（卖亏了，均价↑）
```

**核心规则：** 买入总成本相加，卖出总成本减去实收（price×shares-commission），不是按均摊成本扣减。卖亏均价上升，卖赚均价下降。

### 典型陷阱

| 陷阱 | 处理 |
|------|------|
| 平均成本法≠固定均价法 | 卖出后 total_cost = 原 total_cost - 实收（price×shares-commission），不是"均价×剩余股数"。卖亏均涨卖赚均降 |
| 浮点精度 | total_cost 保留2位小数，不要出现 5845.0199999999995 |
| 重复/取消订单混在记录里 | 只确认成交的交易 |
| 负成本仓位 | 成本视为已收回本金，均价 = total_cost / shares |

## 轻量研究模式（含个股多空辩论）

不是每次都要跑 4 步全流程。用户也可以直接问一个具体问题，比如"我现在仓位全是半导体，推荐一些分散板块"。

此时：
- 建 session → 发简洁问题（一段话即可，不用生成提示词文件）
- 告诉 agent "不用跑swarm，直接分析"
- 这类问题通常 3-5 分钟出结果

### 个股多空辩论黄金法则：prompt 极简，不给预处理数据

当用户问"多空辩论一下宁德时代"或"分析下Lumentum"时：

**正确做法：**
```
语言：中文 | 宁德时代多空辩论
```
一句话即可。不要预拉价格数据、不要预排多空论点、不要写分析框架。让 vibe-trading AI 自行通过 web_search / get_market_data 做研究。

**错误做法（用户明确禁止）：**
预排多空论点（"看多方面：..."看空方面："..."）→ 限制了AI自己的推理能力。用户说过"你的请求应该简洁，只有'宁德时代多空辩论'这一句话就够了，剩余的信息让他自行补充"。

### 个股分析流程
1. 建 session（不设 goal）
2. 发消息：只发"标的名称 + 多空辩论"附带语言偏好
3. 所有基本面/价格数据让 vibe-trading 自行获取
4. 等结果。session active 时不要催、不要发"继续处理"、不要开新 session 替代

## 分析架构：4 步工具导向（v5.1）

不是角色扮演。每步告诉 agent 具体用什么工具/swarm：

| 步骤 | 工具 | 说明 |
|------|------|------|
| 1 | `run_swarm(equity_research_team)` | 宏观 + 行业 + 选股扫描，三合一 |
| 2 | `load_skill("technical-basic")` + `read_url` | 逐个 TA 分析持仓 |
| 3 | `run_swarm(investment_committee)` | **一次性**分析全部标的。全部标的+TA数据一起丢给一个 run_swarm，不要写「逐一轮」或「× N」 |
| 4 | 综合 | 组合健康 + 调仓建议 |

#### ⚠️ 分析 Agent 仍可能覆盖 prompt 提供的正确数据

即使 prompt 已通过 yfinance longName 提供了正确的标的身份（如 SPCX = "Space Exploration Technologies Corp."），vibe-trading 分析 agent 仍可能**根据其训练知识覆盖 prompt 数据**，将 SPCX 错误归类为"SPAC ETF"。

**根因**：分析 agent 对 ticker SPCX 的 training-time 知识（SPAC & New Issue ETF）强于 prompt 中的显式数据。这不是 prompt 质量问题，而是 LLM 的知识优先于上下文注入的竞价问题。

**已知受影响标的**：
- **SPCX**：训练数据中其代码是已清盘的 SPAC ETF，但 2026-06 IPO 后现为 SpaceX。这是典型的重名 ticker 问题
- **SATS**（EchoStar）：可能被误认为卫星运营商对照物

**改正流程（不重新建 session）**：
1. 发 follow-up 消息到同一 session，仅聚焦纠正点（如"SXCX 是 SpaceX，不是 SPAC ETF，请重新评估"）
2. 用 `poll_session.py` 等新回复
3. 收到确认后，再发一条要求系统性修正完整报告（"基于纠正重新输出完整报告"）
4. 再次轮询获取修正版

不要开新 session — 原有 session 的上下文（持仓表、TA 数据、宏观分析）都可以保留，只需替换被纠正标的的分析结论。

## ⚠️ 价格数据可靠性：预拉优于 AI 自搜

vibe-trading AI 通过 web_search 获取的实时价格有时大幅偏差（如 SPCX 实际 ~$161 被报成 $96），导致后续分析结论完全反方向。

**修复：** `generate_vibe_prompt.py` 已改为发送 prompt 前通过 Yahoo Finance v8 API 预拉实时价，直接写入持仓表的「现价」和「P&L」列，并注明"已含实时价，无需再查价格"。

价格拉取逻辑：
- **美股**：`https://query1.finance.yahoo.com/v8/finance/chart/{TICKER}?interval=1d&range=5d`（需 `--proxy`）
- **港股**：yfinance 格式为 `0700.HK`（4位数字+.HK），raw ticker `00700.hk` 需 `int(parts[0])` 后 `f"{ticker_num:04d}.HK"`
- **A股**：直接使用 `.sz` / `.sh` 后缀（如 `159740.SZ`）
- **失败处理：** 拉取失败显示 `N/A`，仍允许 AI 自行补充
- **中文名称来源**：prompt 持仓表添加「名称」列。名称通过 yfinance v8 API 的 `longName` 字段自动获取（不截断），无需任何手动兜底。新增标的无需改代码

### ⚠️ 数据时效性陷阱：历史事件 ≠ 当前状态

vibe-trading 的 `web_search` 和 `read_url` 可能搜到数天到数周前的旧新闻（如6月5日半导体暴跌$1.3T），并将其作为利空依据。到分析日（如6月23日）时，标的可能已部分或全部修复。

**不查验的后果：** 把「历史事件」当作「当前利空」，结论失准。

**正确流程：** 分析中任何基于「特定日期事件」的论据，必须同步核查两者：
1. 事件本身（发生了什么）
2. 当前各标的收盘价（该事件是否已被价格消化/修复）

区分方式：用 yfinance v8 API 拉各标的当前价，判断「事件冲击→修复程度」链条是否成立。未修复的继续作利空，已修复的标记为历史事件、不再影响当下判断。也可在 prompt 末尾追加一句提醒，要求 vibe-trading 在引用历史事件时同步确认当前价格状态。

### ⚠️ 失败处理：vibe-trading 不可用时的降级方案

当以下情况出现时：
- API session 超过 10 分钟无回复（agent 仍在 `active` 但不推进）
- swarm run 1-2 分钟内快速 `failed`（通常是 worker 缺少 web_search/read_url 工具）
- HTTP 451 导致 read_url 反复重试卡死 session

**降级方案（手动分析）**：

1. **实时拉价**：通过 `yfinance` 库（需 `HTTP_PROXY=http://127.0.0.1:7890`）获取所有标的现价。美股直接用 ticker（NVDA 而非 NVDA.US），港股用 `0700.HK`，A 股用 `159740.SZ`
2. **计算持仓表**：成本根据 snapshot.yaml 读取，市值=股数×现价，盈亏=市值-成本。按市值占比排序
3. **分析框架**：
   - 逐个标的：趋势判断（vs 成本价/MA50）、行业背景、多空论点
   - 组合整体：集中度风险、现金占比、币种分散
   - 给出优先级行动清单（按🔴🟡🟢排）
4. **报告输出**：保存为 MD 文件，发送 MEDIA 附件

**要告诉用户**：说明 vibe-trading 不可用并解释原因（session 超时 / swarm 工具缺失 / 451 阻断），再把手动分析结果发给用户。不要悄悄替代而假装是 vibe-trading 输出的。

部分 swarm preset 的 worker agent 缺少 `web_search` 工具（如 `investment_committee` 的 bull_advocate/bear_advocate 只有 `bash/read_file/write_file/load_skill/factor_analysis`）。这导致以下场景失败：
- **私有公司/追踪股研究**（如 SPCX/SpaceX）：web_search 是唯一能获取非公开信息的工具
- **小众/新上市标的**：get_market_data/read_url 可能被 451 或缺少数据源阻挡

**影响**：swarm worker 在这些情况下会返回空结果或快速失败（status=failed within 1-2 min）。

**应对**：
1. 优先 API session 模式（session agent 工具齐全，可自行 web_search/read_url）
2. 如必须用 swarm，考虑用 `equity_research_team`（tools 更丰富）替代 `investment_committee`
3. 预拉实时价和基本数据写入 prompt，减少 worker 对外部工具的依赖

### ⚠️ 分析完成后的报告交付

vibe-trading 分析可能耗时 10-30 分钟。返回的 raw assistant 回复可达 8K-14K 字符。

**交付流程**：

```python
# 1. 从 session 获取完整 assistant 回复
curl -s "http://127.0.0.1:8000/sessions/{SID}/messages?limit=100" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
for m in msgs:
    if m.get('role') == 'assistant':
        print(m.get('content', ''))
" > /tmp/vibe_report_<topic>_$(date +%m%d).md

# 2. 发送为 MEDIA 附件（完整原始报告，不提炼摘要代替）
# 回复中包含: MEDIA:/tmp/vibe_report_<topic>_<date>.md

# 3. 可在附件后附简要摘要（3-5行关键结论），但绝不替代原始报告
```

⚠️ **绝对不提炼摘要代替原始报告**。用户要求完整分析过程和证据链，原始报告含 TA 指标数值（MA/RSI/MACD/布林带）、多空论据、追溯表——这些都是摘要无法覆盖的。vibe-trading 的 assistant 回复可能长达 13K+ 字符，全量发给用户。

⚠️ **平台交付坑：QQ 不支持 MEDIA 文件附件。** `send_message` 的 MEDIA 附件只在 telegram/discord/matrix/weixin/signal/yuanbao/feishu 上生效。当用户通过 QQ 使用时 MEDIA 文件会被静默丢弃。必须改为在消息正文中直接粘贴完整报告内容，或分多条消息发出。不要在 QQ 上尝试 MEDIA 附件后问"收到了吗"——它们已经在发送端被丢弃了。

vibe-trading API 消息体限制 **5000 字符**。`generate_vibe_prompt.py` 生成的 prompt 原为 ~6168 字符，超出限制导致消息被裁。

**修复（2026-06-15）：** 双重修复。
1. **脚本精简**：`generate_vibe_prompt.py` 重写为精简版（~1000 字符），去掉啰嗦的分析步骤说明，保留核心指令
2. **根因修复**：`stock.py repair_security()` 在重建 snapshot 时跳过 shares=0 的标的。此前清仓操作只把股数归零不删条目，导致 snapshot 积累 30+ 零股废标。零股被带到 prompt 中，既占字符又干扰 vibe-trading AI 判断
3. **生成脚本**也做了一层防御性过滤（shares==0 跳过）

**维护提醒：** 如果持仓数量大幅增加导致 prompt 再次超标，优先精简分析流程描述（第 1-4 步说明）而不是裁剪持仓表。持仓表目前每行 ~50 字符，11 个标的大约占 550 字符。
如果 Prompt 生成后发现字符数超标或持仓表有 0 股/负股异常条目，先检查 snapshot.yaml 中 `accounts.security` 下各账户的 positions 是否有零股残存，然后 `ft verify --fix` 重建。如果重建后仍残留，说明 `_replay_security_csv` 中证券 CSV 记录的重播逻辑存在 bug——清仓卖出的 SELL 行可能导致 shares=0 而非完全省略该 position key。

## Prompt 生成脚本

`~/.hermes/scripts/generate_vibe_prompt.py` 生成分析 prompt 发往 vibe-trading API。

#### 重要特性（v7）
1. **实时价预拉** — Yahoo Finance v8 API（需 `--proxy http://127.0.0.1:7890`）逐个拉取持仓现价和 P&L。美股直取、港股 `int+04d.HK`、A 股用 `.sz`/`.sh` 后缀
2. **名称自动获取** — 从 chart API meta 的 `longName` 字段直接获取，不截断、无兜底映射、无硬编码 name_map。chart API 本身就返回 `longName`（含 SPCX→"Space Exploration Technologies Corp."、159740→"DaCheng Hang Seng Technology ETF(QDII)" 等，无需额外 API 调用）。新增标的零代码维护
3. **零股/负股过滤** — `shares <= 0` 的行不写入 prompt
4. **≤5000 字符** — 当前 ~1200 字符，远低于 API 限制
5. **成本计算说明** — prompt 末尾附带均摊法说明（卖出时总成本减回收资金），避免 AI 对负成本/变均价持仓产生误解
6. **输出格式提示** — prompt 末尾注明"已含实时价，无需再查价格"，避免 AI 二次搜价出错

### 运行方式（API session 模式首选）

```bash
# 0. 生成精简分析 prompt（从 snapshot.yaml → /tmp/vibe_cron_daily.md）
#    脚本已设为 #!/usr/bin/env python3，直接运行即可
~/.hermes/scripts/generate_vibe_prompt.py
# 或 chmod +x 后直接 ./generate_vibe_prompt.py
# 输出约 1400 字符，如持仓变化可检查字符数 wc -c /tmp/vibe_cron_daily.md

# 1. 建 session（不设 goal）
SESSION_ID=$(curl -s -X POST http://127.0.0.1:8000/sessions \
  -H "Content-Type: application/json" -d '{}' | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" )

# 2. 直接发消息（不设 goal）— 一次发完或分条追问均可
curl -s -X POST "http://127.0.0.1:8000/sessions/${SESSION_ID}/messages" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c "import json; print(json.dumps({'content': open('/tmp/vibe_cron_daily.md').read()}))")"

# 3. 轮询（最长 2 小时）— 注意：session status 永远是 "active"（无 processing/done 区分），需要用消息内容判断
LAST_COUNT=$(curl -s "http://127.0.0.1:8000/sessions/${SESSION_ID}/messages?limit=100" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
while true; do
  sleep 30
  NEW_COUNT=$(curl -s "http://127.0.0.1:8000/sessions/${SESSION_ID}/messages?limit=100" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
  [ "$NEW_COUNT" -gt "$LAST_COUNT" ] && break
done
curl -s "http://127.0.0.1:8000/sessions/${SESSION_ID}/messages?limit=100" | python3 -c "
import sys, json
msgs = json.load(sys.stdin)
for m in reversed(msgs):
    if m['role'] == 'assistant' and m.get('content'):
        print(m['content'])
        break
"
```

> **⚠️ 发消息：一次性或 follow-up 均可**
> 一次性发完整需求节省时间，但 follow-up 消息（追问/澄清）也可以正常发送、agent 会响应。需要补充信息时直接在同一 session 追问即可，不用开新 session。

## 实时价格查询（portfolio_pnl.py 已废弃）

`scripts/portfolio_pnl.py` 脚本已移除。用以下命令替代：

```bash
# 拉美股实时价（需 proxy）
curl -s --proxy http://127.0.0.1:7890 \
  "https://query1.finance.yahoo.com/v8/finance/chart/NVDA?interval=1d&range=5d" \
  -H "User-Agent: Mozilla/5.0"

# 拉港股
curl -s "https://query1.finance.yahoo.com/v8/finance/chart/0700.HK?interval=1d&range=5d" \
  -H "User-Agent: Mozilla/5.0"

# 全量查询（finance-tracker 自带价格拉取）
HTTP_PROXY=http://127.0.0.1:7890 ft stock list
```

持仓成本计算规则：平均成本法（见 `references/average-cost-method.md`）。

## 铁律（永不违反）

1. **不得编造数据** — 所有建议必须来自 vibe-trading 实际输出
2. **一任务一跑，不重试** — session active 时绝不开新 session、不切端口、不取消。一次几百万 token，重试浪费钱。如果怀疑卡死，**问用户**，不自己判断
3. **不重启不kill** — 任何重启 server、kill 进程、切端口的操作，必须先问用户
4. **轮询用消息计数而非 session status** — `GET /sessions/{id}` 始终返回 `status="active"`（无 "processing"/"done" 区分）。正确做法：记住发消息前的消息数量，周期查 `GET /sessions/{id}/messages` 看数量是否增加。**zsh 陷阱：** `status` 是 zsh 保留变量，赋值会导致 `read-only variable` 错误。用 `s` 或 `LAST_COUNT` 替代
5. **follow-up 消息有效** — 可以在已有 session 上发追问消息，agent 会正常响应。一次性发完整需求是效率建议（减少等待轮次），非强制约束
6. **开新 session 前问用户** — 即使旧 session 看似卡住或长时间无回复，也要先问用户确认。用户明确说过"别老是把我跑到一半的任务当做卡住了，然后又重新跑一个任务"。session 跑1.5-2小时才正常，不要擅自判断卡死

## 支持文件

| 文件 | 说明 |
|------|------|
| `references/average-cost-method.md` | 平均成本法计算规则和示例 |
| `~/.hermes/scripts/generate_vibe_prompt.py` | **主入口**：从 snapshot.yaml 生成精简分析 prompt。自动拉取实时价→longName 自动取全称→输出 ~1400 字符。v7: 去兜底、去截断，新增标的不改代码 |

### 脚本改进历史

| 版本 | 改进 |
|------|------|
| v1 (原版) | ~6168 字符，超出 API 5000 限制 |
| v2 (2026-06-15) | 精简到 ~1000 字符，移除冗余描述，零股过滤 |
| v3 (2026-06-15) | 增加 yfinance 实时价预拉（curl v8 API + proxy），避免 AI 自搜价偏差 |
| v4 (2026-06-15) | 增加港股 ticker 映射修复（00700→0700.HK），增加中文公司名称列 |
| v5 (2026-06-16) | 修正 SPCX 类型：追踪股→股票，名称：SpaceX追踪股→SpaceX；风格改为"完整解释分析过程和证据链" |
| v7 (2026-06-23) | `longName` → `longName`（chart API meta 直接取），去截断、去兜底 known_names、改为通用 shebang |

> **注意**：持仓数据来源已统一为 `ft stock list`（finance-tracker），旧 `portfolio.json` 已停用。
>
## 已知问题
- **zsh status 冲突**：轮询脚本不要用 `status` 变量名（zsh 只读内置变量），用 `s` 或消息计数替代
- **AI 实时价格不准确**：vibe-trading 通过 web_search 获取的价格有时偏差较大（如 SPCX 实际 ~$161 被报成 $96）。如有怀疑，以 yfinance 或 ft stock list 为准
- **Session status 无区分**：API 的 `GET /sessions/{id}` 始终返回 `status="active"`，无 "processing"/"done" 状态。判断 agent 是否回复了的唯一方式是查 `GET /sessions/{id}/messages` 是否出现了新的 assistant 消息。轮询脚本不应依赖 status 字段
