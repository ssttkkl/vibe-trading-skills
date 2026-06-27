#!/usr/bin/env bash
# Wrapper: scan + volatility data
cd ~/.hermes/scripts
python3 polymarket_arb_scanner.py --days 7 --price-min 0.80 --price-max 0.99 --min-vol 10000 --event-pages 5 --top 100 --max-spread 15 2>/dev/null
echo ""
python3 volatility_dashboard.py
