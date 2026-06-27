# 盘后/盘前行情获取指南

通过 yfinance 获取美股盘后/盘前价格（post-market / pre-market data）。

## 关键字段

yfinance `Ticker.info` 返回的盘后相关字段：

| 字段 | 说明 | 示例 |
|------|------|------|
| `regularMarketPrice` | 常规交易时段收盘价 | 1048.51 |
| `postMarketPrice` | 盘后价 | 1213.96 |
| `postMarketChangePercent` | 盘后涨跌幅% | 15.78 |
| `marketState` | 市场状态 | `REGULAR`, `POSTPOST`, `PREPRE`, `CLOSED` |
| `hasPrePostMarketData` | 是否有盘前盘后数据 | True |

## 市场状态判断

| 状态 | 含义 |
|------|------|
| `REGULAR` | 常规交易时段 |
| `POSTPOST` / `POST` | 盘后交易时段 🌙 |
| `PREPRE` / `PRE` | 盘前交易时段 🌅 |
| `CLOSED` | 已收盘（A股/港股等）|

## 代理要求

从中国大陆访问 yfinance 必须设置代理：

```python
import os
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"
```

## 完整获取示例

```python
import yfinance as yf
info = yf.Ticker("MU").info
rp = info.get("regularMarketPrice")
pp = info.get("postMarketPrice")
pchg = info.get("postMarketChangePercent")
state = info.get("marketState", "")

if pp and state in ("POSTPOST", "POST", "PREPRE", "PRE"):
    display_price = pp        # 盘后价优先
else:
    display_price = rp        # 否则用收盘价
```

## 用户偏好

该用户要求**所有持仓查询优先展示盘后/盘前价**（美股），A股/港股已收盘则展示收盘价并标注"已收盘无夜盘"。
