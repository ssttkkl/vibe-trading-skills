# Gamma API 查询模式

> 用于 Polymarket 尾盘分析时的数据验证

## 基础查询

```bash
# 按交易量降序获取活跃事件（分页）
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset={OFFSET}&order=volume&ascending=false'
```

- `closed=false` — 仅活跃事件
- `limit=100` — 单页上限（硬限制）
- `offset=0,100,200,300...` — 翻页
- `order=volume&ascending=false` — 按交易量降序

## 按 event_id 查详情

```bash
curl -s 'https://gamma-api.polymarket.com/events/{EVENT_ID}' | python3 -c "
import json,sys
e=json.load(sys.stdin)
print(f'Title: {e.get(\"title\")}')
print(f'Desc: {e.get(\"description\")[:500]}')
print(f'Slug: {e.get(\"slug\")}')
for m in e.get('markets',[]):
    print(f'Q: {m.get(\"question\")}')
    print(f'Prices: {m.get(\"outcomePrices\")}')
    print(f'Volume: \${float(m.get(\"volume\",0)):,.0f}')
    print(f'Token ID: {m.get(\"token_id\",\"\")}  ← 空=AMM盘, 有值=CLOB盘')
    print(f'Condition ID: {m.get(\"condition_id\",\"\")}')
"
```

## 按市场 slug 查（通过 polymarket.py 脚本）

```bash
python3 ~/.hermes/skills/research/polymarket/scripts/polymarket.py market {SLUG}
python3 ~/.hermes/skills/research/polymarket/scripts/polymarket.py event {EVENT_SLUG}
```

**坑：** slug 后缀经常带随机数（如 `-943`、`-245-361`），可能找不到。

## 搜索特定事件

```bash
# Gamma API 的 ?title= 参数不可靠（传入关键词也返回无关事件）
# 必须拉全量后用本地 python3 过滤

curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset={OFFSET}&order=volume&ascending=false' \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
for e in data:
    for m in e.get('markets',[]):
        q=m.get('question','')
        if 'pahlavi' in q.lower() or ('iran' in q.lower() and 'enter' in q.lower()):
            print(f'Event: {e.get(\"title\")}')
            print(f'Q: {q}')
            print(f'Prices: {m.get(\"outcomePrices\")}')
            print(f'Volume: \${float(m.get(\"volume\",0)):,.0f}')
            print(f'Rules: {e.get(\"description\",\"\")[:400]}')
"
```

## 事件内多子市场搜索

有些事件名不包含子市场的关键词。例如 `title="Which countries will send warships through the Strait of Hormuz by June 30?"` 包含 20+ 个子市场（各国），但用 `?title=South+Korea` 搜不到。

```bash
# 正确方法：拉全事件后本地遍历 markets[]
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset=200&order=volume&ascending=false' \
  | python3 -c "
import json,sys
data=json.load(sys.stdin)
for e in data:
    for m in e.get('markets',[]):
        q=m.get('question','')
        if 'south korea' in q.lower():
            print(f'EVENT: {e.get(\"title\")}')
            print(f'Q: {q}')
            print(f'Prices: {m.get(\"outcomePrices\")}')
            print(f'Vol: \${float(m.get(\"volume\",0)):,.0f}')
            print(f'Rules: {e.get(\"description\",\"\")[:300]}')
"
```

## 找低交易量事件

扫尾盘的候选往往低于 top-100。用高 offset：

```bash
# offset=200 开始查（跳过 top-200 热门事件）
curl -s 'https://gamma-api.polymarket.com/events?closed=false&limit=100&offset=200&order=volume&ascending=false'
```

## CLOB vs AMM 鉴别

检查 market 的 `token_id` 字段：

| token_id | 类型 | 说明 |
|:---------|:----|:-----|
| 非空字符串 | CLOB | 有订单簿，可查 depth，滑点可控 |
| 空字符串 | AMM | 自动做市商池，滑点随买入量指数级上升 |

薄盘（Volume < $50K）几乎全是 AMM。

## 数据完整性注意事项

| 检查项 | 原因 |
|:-------|:-----|
| 交易量 | 脚本报告的量和API原始量可能差3-4个数量级 |
| 价格 | 脚本显示价格可能偏离API实际中间价0.5-2¢ |
| 到期日 | 脚本可能错误解析到期日（12月→2天） |
| 盘口存在性 | 脚本显示的盘可能在API中查不到 |
| token_id | 空=AMM，薄盘的滑点风险极高 |
