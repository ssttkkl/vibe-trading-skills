# Vibe-Trading Skills

A collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills for Polymarket arbitrage analysis and portfolio research, powered by [Vibe-Trading](https://github.com/ssttkkl/Vibe-Trading).

## Dependency

**Required upstream:** [Vibe-Trading](https://github.com/ssttkkl/Vibe-Trading) must be installed and running (`vibe-trading serve`) for any skill that submits prompts to its HTTP API (default `localhost:8000`).

## Included Skills

| Skill | Category | Description |
|-------|----------|-------------|
| `vibe-trading` | finance | MCP integration with Vibe-Trading's 35+ research tools |
| `vibe-portfolio-analysis` | finance | Daily portfolio analysis workflow |
| `polymarket-vibe-arb` | research | Polymarket arbitrage — automation pipeline + comprehensive methodology. Scans sub-markets, filters candidates (AI principle-based), submits raw data to Vibe-Trading API for deep research (options chain, volatility analysis, news search). Includes methodology for finding "free money" opportunities. |
| ~~`polymarket-tail-sweep`~~ | — | Merged into `polymarket-vibe-arb` |

## Helper Scripts

- `scripts/poll_session.py` — Polls Vibe-Trading API session for assistant responses
- `scripts/polymarket_arb_scanner.py` — Sub-market level Polymarket scanner with CLOB spread analysis
- `scripts/volatility_dashboard.py` — Fetches real-time prices + 30d volatility ranges
- `scripts/run_arb_scan.sh` — Wrapper: scanner + volatility dashboard
- `scripts/generate_vibe_prompt.py` — Portfolio analysis prompt generator

## Usage

```bash
pip install vibe-trading-ai
vibe-trading serve

cp -r skills/* ~/.hermes/skills/
cp -r scripts/* ~/.hermes/scripts/
```

Then in a Hermes Agent session: `skill_view(name='polymarket-vibe-arb')`

## License

MIT
