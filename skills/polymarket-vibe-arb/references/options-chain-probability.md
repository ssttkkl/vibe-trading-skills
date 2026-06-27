# 期权链概率验证方法论

用于 Polymarket 价格/结算范围盘的概率验证。当 vibe-trading 使用期权隐含波动率验证市场定价时，以下是关键指标和使用方法。

## 可用波动率指数

| 指数 | 标的 | 说明 |
|------|------|------|
| GVZ | 黄金 (GC) | CBOE Gold Volatility Index，当前~18.5% |
| OVX | 原油 (WTI/CL) | CBOE Crude Oil Volatility Index，当前~46.96 |
| VIX | S&P 500 | 标普500波动率指数 |
| BVIV | 比特币 | Bitcoin Volatility Index，当前~53% |
| ETH波动率 | 以太坊 | 可通过 Deribit 或类似期权市场获取，通常高于BTC |

## 用法示例

### WTI $80 概率验证

```python
current = 69.23
target = 80.00
days = 4
sigma = 0.029  # 日波动率 2.90%（从 OVX=46.96 换算）
move_pct = (target - current) / current  # 15.6%
move_sigma = move_pct / (sigma * sqrt(days))  # 2.69σ
# 正态分布 → 概率 ~0.4%
```

### 黄金 $3,900 概率验证

```python
current = 4096
target = 3900
days = 4
sigma = 0.185 / sqrt(252)  # GVZ=18.5% 换算日波动率
                          # ≈ 1.17% 日波动率
move_pct = (target - current) / current  # -4.8%
move_sigma = abs(move_pct) / (sigma * sqrt(days))  # 1.17σ
# 正态分布 → 概率 ~12%
```

## 注意事项

- 期权隐含波动率通常 > 历史波动率（含风险溢价）
- 厚尾分布意味着尾部概率 > 正态分布估算
- VIX/GVZ/OVX 越高，正态近似越不准确
- 快到期的短期期权（<7天）的隐含波动率可能受 Gamma 影响放大
- 用 `web_search` 或 `read_url` 获取最新 GVZ/OVX/VIX 数据
