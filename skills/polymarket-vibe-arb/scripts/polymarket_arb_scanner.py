#!/usr/bin/env python3
"""
Polymarket 子盘级套利扫描器 v2
- 直接扫到子市场级别，不依赖事件级汇总
- 利用 market 内置的 bestBid/bestAsk/spread/liquidityClob 字段
- 计算有效ROI：考虑价差后的真实可执行回报
- 支持 Yes 和 No 两个方向
"""

import json, urllib.request, sys
from datetime import datetime, timezone, date

NOW = datetime.now(timezone.utc)
TODAY = date.today()

def api_get(url, timeout=10):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
        return json.loads(resp.read())
    except Exception as e:
        return None

def fmt_vol(vol):
    if vol >= 1e6: return f"${vol/1e6:.1f}M"
    if vol >= 1e3: return f"${vol/1e3:.0f}K"
    return f"${vol:.0f}"

def calc_roi(buy_price):
    if buy_price <= 0 or buy_price >= 1: return 0
    return (1/buy_price - 1) * 100

def parse_date(s):
    """各种日期格式转date对象"""
    if not s: return None
    s = str(s)[:10]
    try:
        return datetime.strptime(s, '%Y-%m-%d').date()
    except:
        pass
    try:
        return datetime.strptime(s, '%Y-%m-%dT%H:%M:%S').date()
    except:
        pass
    return None

def scan_markets(max_days=7, pages=5, min_price=0.80, max_price=0.99, min_vol=10000):
    """扫所有事件展平到子市场，各自计算"""
    print(f"🔄 扫描 {pages*100} 事件...", file=sys.stderr)
    
    all_events = []
    for page in range(pages):
        offset = page * 100
        url = f"https://gamma-api.polymarket.com/events?closed=false&limit=100&offset={offset}&order=volume&ascending=false"
        data = api_get(url)
        if not data or len(data) == 0:
            break
        all_events.extend(data)
    
    print(f"   共 {len(all_events)} 事件", file=sys.stderr)
    
    results = []
    total_markets = 0
    
    for e in all_events:
        etitle = e.get('title', '?')
        erules = e.get('description', '')
        for m in e.get('markets', []):
            total_markets += 1
            
            # 价格检查
            prices_str = m.get('outcomePrices')
            if not prices_str: continue
            try:
                prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str
                yes_price = float(prices[0])
                no_price = float(prices[1])
            except:
                continue
            
            # 到期日期检查
            expiry = parse_date(m.get('endDateIso') or m.get('endDate', ''))
            if expiry:
                delta = (expiry - TODAY).days
                if delta < 0 or delta > max_days:
                    continue
                days_left = delta
            else:
                continue  # 没到期日的不处理
            
            # 量检查
            vol = float(m.get('volume', 0))
            if vol < min_vol: continue
            
            # 流动性/价差检查
            token_ids = m.get('clobTokenIds', [])
            is_clob = bool(token_ids and len(token_ids) >= 2)
            
            # 判断两个方向
            sides_to_check = []
            if min_price <= yes_price <= max_price:
                sides_to_check.append(('Yes', yes_price))
            if min_price <= no_price <= max_price:
                sides_to_check.append(('No', no_price))
            
            for side, market_price in sides_to_check:
                # 跳过已基本结算的
                if market_price > 0.995: continue
                
                roi = calc_roi(market_price)
                
                # 计算有效买入价（考虑价差）
                if is_clob:
                    # CLOB盘 - 用 bestBid/bestAsk
                    if side == 'Yes':
                        # 买Yes要看 No的bid/ask，或者直接看Yes的ask
                        best_ask = float(m.get('bestAsk', 0))  # Yes的ask
                        if best_ask > 0 and best_ask < 1:
                            eff_buy = best_ask
                        else:
                            eff_buy = market_price * 1.02  # 保底2%滑点
                    else:  # No
                        # 买No = 1 - Yes的bestBid
                        best_bid = float(m.get('bestBid', 0))  # Yes的bid
                        if best_bid > 0 and best_bid < 1:
                            eff_buy = 1 - best_bid
                        else:
                            eff_buy = market_price * 1.02
                    
                    # 计算价差
                    bid = float(m.get('bestBid', 0))
                    ask = float(m.get('bestAsk', 0))
                    if bid > 0 and ask > 0:
                        spread_pct = (ask - bid) / ((ask + bid) / 2) * 100
                    else:
                        spread_pct = 2.0  # 默认
                    
                    mtype = 'CLOB'
                    liquidity = float(m.get('liquidityClob', 0))
                else:
                    # AMM盘 - 按volume估算滑点
                    if vol < 50000:
                        est = 0.10
                    elif vol < 200000:
                        est = 0.05
                    elif vol < 1000000:
                        est = 0.02
                    else:
                        est = 0.01
                    
                    eff_buy = market_price * (1 + est)
                    spread_pct = est * 100
                    mtype = 'AMM'
                    liquidity = vol
                
                effective_roi = calc_roi(eff_buy)
                
                results.append({
                    'question': m.get('question', '?'),
                    'event_title': etitle,
                    'expiry': str(expiry),
                    'days_left': days_left,
                    'side': side,
                    'price': market_price,
                    'eff_buy': eff_buy,
                    'roi': roi,
                    'eff_roi': effective_roi,
                    'spread_pct': spread_pct,
                    'type': mtype,
                    'volume': vol,
                    'liquidity': liquidity,
                    'token_ids': bool(token_ids),
                    'slug': m.get('slug', ''),
                })
    
    print(f"   展平 {total_markets} 子市场 → {len(results)} 符合条件", file=sys.stderr)
    return results

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Polymarket 子盘套利扫描器 v2')
    parser.add_argument('--days', type=int, default=7)
    parser.add_argument('--event-pages', type=int, default=5)
    parser.add_argument('--min-vol', type=float, default=10000)
    parser.add_argument('--price-min', type=float, default=0.80)
    parser.add_argument('--price-max', type=float, default=0.99)
    parser.add_argument('--top', type=int, default=20)
    parser.add_argument('--max-spread', type=float, default=15.0)
    args = parser.parse_args()
    
    results = scan_markets(
        max_days=args.days,
        pages=args.event_pages,
        min_price=args.price_min,
        max_price=args.price_max,
        min_vol=args.min_vol,
    )
    
    # 过滤价差
    results = [r for r in results if r['spread_pct'] <= args.max_spread]
    
    # 按有效ROI排序
    results.sort(key=lambda x: x['eff_roi'], reverse=True)
    
    if not results:
        print("\n⚠️  无符合条件的套利机会")
        return
    
    print(f"\n{'='*135}")
    print(f"🏁  Polymarket 子盘套利机会（{args.days}天内到期 / 量>${args.min_vol/1000:.0f}K）")
    print(f"   价格范围: {args.price_min*100:.0f}-{args.price_max*100:.0f}¢ | 价差容忍: <{args.max_spread}%")
    print(f"{'='*135}")
    
    header = f"{'#':>3} | {'子盘（事件）':<60} | {'到期':>5} | {'方向':>3} | {'中间价':>6} | {'买入价':>7} | {'名义ROI':>8} | {'实得ROI':>8} | {'价差':>5} | {'类型':>5} | {'量':>9}"
    
    print(f"\n{'─'*135}")
    print(header)
    print(f"{'─'*135}")
    
    for i, r in enumerate(results[:args.top], 1):
        label = f"{r['question'][:45]}"
        event_short = f"({r['event_title'][:12]})"
        q_str = f"{label} {event_short}"[:58]
        
        side = "📗Y" if r['side'] == 'Yes' else "🔴N"
        mid = r['price'] * 100
        eff = r['eff_buy'] * 100
        roi = r['roi']
        eff_roi = r['eff_roi']
        
        roi_str = f"+{roi:.1f}%" if roi < 999 else "∞"
        eff_str = f"+{eff_roi:.1f}%" if eff_roi < 999 else "∞"
        
        sp_str = f"{r['spread_pct']:.1f}%"
        mtype = r['type']
        vol_str = fmt_vol(r['volume'])
        days_str = f"{r['days_left']}d"
        
        print(f"{i:>3} | {q_str:<58} | {days_str:>5} | {side:>3} | {mid:>5.1f}¢ | {eff:>5.1f}¢ | {roi_str:>8} | {eff_str:>8} | {sp_str:>5} | {mtype:>5} | {vol_str:>9}")
    
    print(f"\n{'─'*135}")
    print(f"💡 买入价 = CLOB的ask价 / AMM的估算价（含滑点）")
    print(f"💡 实得ROI = 按买入价算的实际回报（扣除价差后）")
    print(f"💡 CLOB=订单簿可交易 | AMM=自动做市池（滑点估算）")
    print(f"\n参数: --days N --price-min M --price-max N --min-vol V --max-spread S")

if __name__ == '__main__':
    main()
