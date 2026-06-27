#!/usr/bin/env python3
"""从 ~/.ft/snapshot.yaml 生成 vibe-trading 分析 prompt（含实时价+盘后价，≤5000字符）"""
import yaml, os, sys
from pathlib import Path
import yfinance as yf

# 设置代理
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

SNAPSHOT = Path.home() / ".ft" / "snapshot.yaml"
OUTPUT = Path("/tmp") / "vibe_cron_daily.md"

with open(SNAPSHOT) as f:
    snap = yaml.safe_load(f)

# === 获取实时汇率 ===
FX_RATE = 7.0  # fallback
try:
    fx_info = yf.Ticker("CNY=X").info
    fx_price = fx_info.get("regularMarketPrice")
    if fx_price:
        FX_RATE = fx_price
        print(f"📊 USD/CNY = {FX_RATE:.4f}", file=sys.stderr)
except Exception:
    print(f"⚠️ 汇率获取失败，使用 fallback {FX_RATE}", file=sys.stderr)

def to_usd(amount, currency):
    if currency == "USD":
        return amount
    return amount / FX_RATE

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
            "type": ptype, "note": note, "cname": display,  # 初始cname=代码，后面拉实时价时同步更新
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
        print(f"  {p['ticker']:7s} → {price:>8.2f}  {p['cname']:10s}  P&L={p['pnl']:>8.2f}", file=sys.stderr)
        # 盘后/盘前标记
        if data.get("market_state"):
            p["market_state"] = data["market_state"]
            p["post_chg"] = data.get("post_chg", 0)
    else:
        p["price"] = 0
        p["pnl"] = 0
        print(f"  {p['ticker']:7s} → ❌ 未获取到", file=sys.stderr)

# === 按市值(USD)降序排序 ===
for p in all_positions:
    price = p.get("price", 0) or 0
    p["mkt_val"] = price * p["shares"]
    p["mkt_val_usd"] = to_usd(p["mkt_val"], p["currency"])
all_positions.sort(key=lambda p: p["mkt_val_usd"], reverse=True)

# === 生成持仓表（含现价和P&L）===
rows = []
total_pnl = 0
total_usd = 0
for p in all_positions:
    price = p["price"]
    pnl = p["pnl"]
    total_pnl += pnl
    mkt_val = p["mkt_val"]
    mkt_usd = p["mkt_val_usd"]
    total_usd += mkt_usd
    price_s = f"{p['currency']}{price:.2f}" if price else "N/A"
    pnl_s = f"{p['currency']}{pnl:+.0f}" if price else "-"
    pnl_usd = to_usd(abs(pnl), p["currency"])
    pnl_usd_sign = "+" if pnl >= 0 else "-"
    state_flag = ""
    if p.get("market_state") in ("POSTPOST", "POST"):
        chg = p.get("post_chg", 0)
        state_flag = "🌙"
        price_s = f"{p['currency']}{price:.2f}({chg:+.1f}%)"
    elif p.get("market_state") in ("PREPRE", "PRE"):
        chg = p.get("post_chg", 0)
        state_flag = "🌅"
        price_s = f"{p['currency']}{price:.2f}({chg:+.1f}%)"
    mkt_s = f"${mkt_usd:,.0f}"
    rows.append(f"| {p['ticker']:7s}|{p['cname']:35s}|{p['shares']:>6}|{p['currency']}{p['total_cost']:>9.0f}|{price_s:>18}|{pnl_s:>11}|{mkt_s:>10}|{p['type']:4s}{state_flag}|")
cash_rows = [f"| 现金     |{ccy:10s}|      |{ccy}{amt:>9.0f}|                  |           |          |{ccy:4s}|" for ccy, amt in sorted(cash_by_ccy.items()) if amt > 0]
portfolio = "\n".join(rows + cash_rows)

holdings_csv = ", ".join(p["ticker"] for p in all_positions)
cash_list = [f"{ccy}={amt:.0f}" for ccy, amt in cash_by_ccy.items()]
cash_str = "，".join(cash_list)

prompt = f"""语言：中文 | 风格：完整解释分析过程和证据链

## 持仓（USD换算，🌙=盘后价 🌅=盘前价 | 汇率 USD/CNY = {FX_RATE:.4f}）
|标的|名称|股数|总成本|现价(盘后涨跌)|P&L|市值USD|类型|
|----|----|----|------|----|---|--|--|
|{portfolio}

成本计算方式：均摊法（平均成本法）——卖出时总成本减去回收资金，剩余股数均价重算。示例：30股成本$4,500，卖15股收$3,225，则剩余15股成本$1,275（均价$85）。P&L基于此计算，不是FIFO。

已含实时价+汇率换算，无需再查价格。整体P&L约{total_pnl:+.0f}，总市值约${total_usd:,.0f} USD。

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
