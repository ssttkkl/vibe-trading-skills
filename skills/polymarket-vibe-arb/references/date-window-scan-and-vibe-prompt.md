# Polymarket date-window scan + compact vibe prompt

Use this note when the user asks for a specific expiry window, e.g. “after 6/30, before 7/15”.

## Gamma scan pattern

Prefer `/markets` date filters over event-page `--days` approximation:

```python
params = dict(
    closed='false',
    active='true',
    limit='100',
    offset=str(offset),
    end_date_min='2026-07-01T00:00:00Z',  # > 6/30
    end_date_max='2026-07-15T00:00:00Z',  # < 7/15
    volume_num_min='10000',
)
```

Loop `offset += 100` until a page returns `< limit`. Deduplicate by `conditionId`/`id`/`slug`.

Filter locally:

- strict `endDate >= start_utc and endDate < end_utc`
- Yes/No price in the user’s target band, default 85–99.5¢ for tail arb
- `volumeNum >= min_volume`
- `spread <= max_spread`
- calculate executable buy estimate:
  - Yes: use `bestAsk` when available
  - No: use `1 - bestBid` when available

## Window-edge pitfall

Markets titled “by June 30” can have `endDate` on July 1 due to settlement timezone. If the user says “after 6/30” in the sense of event window, down-rank or exclude these and report the count; do not silently mix them into core candidates.

## Compact prompt for vibe-trading

The session message endpoint can reject `content` longer than ~5000 chars. For batch scans:

1. Keep the scan boundary and aggregate stats.
2. Include at most 8–12 diversified candidates.
3. Family-dedupe repeat markets (e.g. Iran shipping daily markets) and keep representatives.
4. Per candidate include only:
   - question, slug
   - side to check
   - Y/N prices
   - executable buy estimate + ROI
   - bid/ask/spread
   - volume/liquidity
   - endDate
   - first 100–200 chars of rules
5. Ask vibe to research/verify news and rules itself.

## Retrieval fallback

After sending a session message, if `poll_session.py` shows connection errors or times out, first check:

```bash
curl -sS http://127.0.0.1:8000/sessions/$SESSION_ID/messages
```

The assistant reply may already be completed even if polling failed. Do not restart/kill `vibe-trading serve` without asking the user.
