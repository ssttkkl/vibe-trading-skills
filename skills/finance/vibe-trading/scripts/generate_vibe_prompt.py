#!/usr/bin/env python3
"""从 ~/.ft/snapshot.yaml 生成 vibe-trading 分析 prompt（含实时价+盘后价，≤5000字符）

Usage:
    ~/.hermes/scripts/generate_vibe_prompt.py
    → writes to /tmp/vibe_cron_daily.md
    Then: 用 API session 模式提交到 vibe-trading serve

Features:
    • 美股优先展示盘后/盘前价 (postMarketPrice)，带涨跌幅百分比
    • A股/港股已收盘展示 regularMarketPrice
    • 标记: 🌙=盘后价  🌅=盘前价
"""
import yaml, os, sys
from pathlib import Path
import yfinance as yf

# 设置代理（yfinance 读环境变量 HTTP_PROXY）
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

SNAPSHOT = Path.home() / ".ft" / "snapshot.yaml"
OUTPUT = Path("/tmp") / "vibe_cron_daily.md"

with open(SNAPSHOT) as f:
    snap = yaml.safe_load(f)

# === 提取持仓 ===
all_positions = []
cash_by_ccy = {}

def yf_data(raw_ticker):
    """通过 yfinance 获取实时价、盘后价和名称"""
    name = raw_ticker.replace("_", "")
    parts = name.split(".")
    if len(parts) == 2:
        if parts[1] == "us":
            yahoo_ticker = parts[0]
        elif parts[1] == "hk":
            ticker_num = int(parts[0])
            yahoo_ticker = f"{ticker_num:04d}.HK"
        else:
            yahoo_ticker = name
    else:
        yahoo_ticker = name
    try:
        tk = yf.Ticker(yahoo_ticker)
        info = tk.info
        price = info.get("regularMarketPrice")
        post_price = info.get("postMarketPrice")
        post_chg = info.get("postMarketChangePercent")
        state = info.get("marketState", "")
        name_display = info.get("longName", "") or info.get("shortName", "") or raw_ticker.split(".")[0].upper()
        result = {"price": price, "name": name_display}
        # 美股盘后/盘前行情优先展示
        if post_price and state in ("POSTPOST", "POST", "PREPRE", "PRE"):
            result["price"] = post_price
            result["post_price"] = post_price
            result["post_chg"] = post_chg
            result["market_state"] = state
        return result
    except Exception:
        return {"price": None, "name": raw_ticker.split(".")[0].upper()}

for acct_name, acct_data in snap.get("accounts", {}).get("security", {}).items():
    currency = acct_data.get("currency", "USD")
    acct_cash = acct_data.get("cash", 0.0)
    cash_by_ccy[currency] = cash_by_ccy.get(currency, 0.0) + acct_cash

    for ticker, pos in acct_data.get("positions", {}).items():
        shares = pos["shares"]
        if shares <= 0:
            continue
        avg_cost = pos["avg_cost"]
        total_cost = round(shares * avg_cost, 2)
        display = ticker.split(".")[0].upper()
        note = "负成本" if avg_cost == 0 else ""
        ptype = next((t for k, t in {"qld": "杠杆", "smh": "ETF", "sgov": "ETF"}.items() if k in ticker.lower()), "股票")
        all_positions.append({
            "ticker": display, "raw_ticker": ticker,
            "currency": currency, "shares": shares,
            "total_cost": total_cost, "avg_cost": avg_cost,
            "type": ptype, "note": note, "cname": display,
        })

# === 拉实时价 ===
print("⏳ 正在拉取实时价...", file=sys.stderr)
for p in all_positions:
    data = yf_data(p["raw_ticker"])
    price = data["price"]
    p["price"] = price
    if data["name"]:
        p["cname"] = data["name"]
    if price:
        p["pnl"] = round((price - p["avg_cost"]) * p["shares"], 2)
        print(f"  {p['ticker']:7s} → {price:>8.2f}  {p['cname'][:20]:20s}  P&L={p['pnl']:>8.2f}", file=sys.stderr)
        # 盘后/盘前标记
        if data.get("market_state"):
            p["market_state"] = data["market_state"]
            p["post_chg"] = data.get("post_chg", 0)
    else:
        p["price"] = 0
        p["pnl"] = 0
        print(f"  {p['ticker']:7s} → ❌ 未获取到", file=sys.stderr)

# === 生成持仓表（现价优先用盘后/盘前价）===
rows = []
total_pnl = 0
for p in all_positions:
    price = p["price"]
    pnl = p["pnl"]
    total_pnl += pnl
    price_s = f"{p['currency']}{price:.2f}" if price else "N/A"
    pnl_s = f"{p['currency']}{pnl:+.0f}"
    state_flag = ""
    if p.get("market_state") in ("POSTPOST", "POST"):
        chg = p.get("post_chg", 0)
        state_flag = "🌙"
        price_s = f"{p['currency']}{price:.2f}({chg:+.1f}%)"
    elif p.get("market_state") in ("PREPRE", "PRE"):
        chg = p.get("post_chg", 0)
        state_flag = "🌅"
        price_s = f"{p['currency']}{price:.2f}({chg:+.1f}%)"
    rows.append(f"| {p['ticker']:7s}|{p['cname'][:24]:24s}|{p['shares']:>5}|{p['currency']}{p['total_cost']:>8.0f}|{price_s:>18}|{pnl_s:>10}|{p['type']}{state_flag}|")
cash_rows = [f"| 现金     |{'':24s}|      |{ccy}{amt:>8.0f}|                  |          | |" for ccy, amt in sorted(cash_by_ccy.items()) if amt > 0]
portfolio = "\n".join(rows + cash_rows)

prompt = f"""语言：中文 | 风格：完整解释分析过程和证据链

## 持仓（含实时价和盈亏，🌙=盘后价 🌅=盘前价）
|标的|名称|股数|总成本|现价(盘后涨跌)|P&L|类型|
|----|----|----|------|----|---|--|
{portfolio}

已含实时价，美股优先盘后/盘前价，无需再查价格。整体P&L约{total_pnl:+.0f}。

---
## 分析流程
1. **run_swarm(equity_research_team)** — 宏观+行业+选股扫描
2. **load_skill("technical-basic") + read_url** — 逐个TA分析（均线/RSI/MACD/布林）
3. **run_swarm(investment_committee)** — 一轮分析全部{len(all_positions)}个标的
4. **综合** — 组合健康+调仓建议

### 最终输出
1. 市场快照（P&L表，币种分离）
2. 宏观行业扫描结论
3. 逐个持仓：TA评分±5 + 多空辩论 + 最终决策
4. 组合健康评分 + 按优先级行动清单（含股数/金额/币种）
5. 追溯表（步骤/工具/分析内容/结论）
"""
OUTPUT.write_text(prompt)
print(f"\nOutput: {OUTPUT}", file=sys.stderr)
print(f"Prompt: {len(prompt)} chars", file=sys.stderr)
print(f"Holdings: {len(all_positions)} positions, {len(cash_by_ccy)} currencies", file=sys.stderr)
print(prompt)
