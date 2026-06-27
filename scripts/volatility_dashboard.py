#!/usr/bin/env python3
"""Fetch real-time prices + 30d volatility data for use by cron job AI."""
import json, urllib.request, sys

def api(url, timeout=10):
    try:
        r = urllib.request.urlopen(url, timeout=timeout)
        return json.loads(r.read())
    except Exception as e:
        return None

print("📊 实时行情 + 近期波动率（供AI调研参考）")
print("─" * 50)

# --- Crypto spot + 24h ---
crypto = api("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true")
if crypto:
    for coin, label in [('bitcoin','BTC'),('ethereum','ETH'),('solana','SOL')]:
        info = crypto.get(coin, {})
        p = info.get('usd', 0)
        chg = info.get('usd_24hr_change', 0)
        print(f"  {label}: ${p:,.0f} ({chg:+.1f}%)")

# --- Crypto 30d range ---
for coin, label in [('bitcoin','BTC'),('ethereum','ETH'),('solana','SOL')]:
    chart = api(f"https://api.coingecko.com/api/v3/coins/{coin}/market_chart?vs_currency=usd&days=30")
    if chart:
        prices = [p[1] for p in chart.get('prices', [])]
        if prices:
            low = min(prices); high = max(prices)
            first = prices[0]; last = prices[-1]
            chg = (last-first)/first*100
            print(f"  {label:>4} 30d范围: ${low:,.0f} - ${high:,.0f}  (30d变化: {chg:+.1f}%)")

# --- Gold ---
gold = api("https://api.gold-api.com/price/XAU")
if gold:
    p = gold.get('price', 0)
    chg = gold.get('changePercent', 0)
    print(f"  XAU/USD: ${p:,.0f} ({chg:+.2f}%)")
print("  ⚠️ 黄金近期波动率极高（本月振幅 $3800-$5000，约24%）")
print("  ⚠️ 高波动率意味着结算范围盘风险极大，不可仅以当前价格判断")

print()
print("🛢️  WTI Crude Oil: $75-$80（建议上网查EIA最新数据）")
print()
print("─" * 50)
print("💡 波动率使用说明：")
print("  - 30d范围反映资产近一个月的波动幅度")
print("  - 24h变化反映短期动量")
print("  - 对于结算范围盘（如Gold $3800-$4200），高波动率=高风险范围内到期")
print("  - AI分析时必须结合波动率判断，不能只看当前价格")
print("─" * 50)
