# Real-time price correction for Polymarket tail scans

When vibe-trading analyzes crypto threshold markets, do a final independent price sanity check before delivering the report. A small realtime-price error can flip the ranking because tail-scan EV depends on the remaining buffer to the threshold.

## Pattern

1. Run the Gamma/window scan and send compact candidates to vibe-trading.
2. When the report comes back, identify markets whose thesis depends on a live external price (BTC/ETH thresholds, equity IPO market cap, weather, sports scores).
3. Independently query the settlement source or closest primary source. For crypto threshold markets, Binance ticker is a fast sanity check:

```bash
python3 - <<'PY'
import urllib.request, json
for sym in ['BTCUSDT','ETHUSDT']:
    url=f'https://api.binance.com/api/v3/ticker/price?symbol={sym}'
    data=json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=10).read())
    print(sym, data['price'])
PY
```

4. Compare the live price with vibe-trading's assumed price. Recompute rough buffer:

```text
buffer = (spot - threshold) / spot     # for Yes-above-threshold
buffer = (threshold - spot) / spot     # for No-below-threshold / inverse cases
```

5. If the buffer/probability/ranking materially changes, send a follow-up in the **same vibe session** with the corrected price and ask for revised probabilities, EV, ranking, and sizing. Do not deliver the stale first report as final.

## Example lesson

A 7-day Polymarket scan initially ranked `BTC > $56,000 on July 2` as the top “送钱盘” assuming BTC ≈ $60,200 (≈7% buffer). A Binance check showed BTC ≈ $58,390, reducing buffer to ≈4.1%. The same-session follow-up downgraded it from top pick to “do not open unless price <= 0.855”, and promoted `ETH > $1,500` / `BTC > $54,000` instead.

## Delivery rule

Final answer should explicitly mention that a realtime correction was performed when it changes the conclusion. This preserves trust and avoids giving the user an obsolete ranking.