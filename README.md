# Vibe-Trading Skills

A collection of [Hermes Agent](https://hermes-agent.nousresearch.com) skills for Polymarket arbitrage analysis and portfolio research, powered by [Vibe-Trading](https://github.com/ssttkkl/Vibe-Trading).

## Dependency

This project provides **skills** (workflow instructions + helper scripts) for the Hermes Agent ecosystem. It **does not** include the Vibe-Trading analysis engine itself.

**Required upstream:** [Vibe-Trading](https://github.com/ssttkkl/Vibe-Trading) must be installed and running (`vibe-trading serve`) for any skill that submits prompts to its HTTP API (default `localhost:8000`).

## Included Skills

| Skill | Category | Description |
|-------|----------|-------------|
| `vibe-trading` | finance | MCP integration with Vibe-Trading's 35+ research tools (backtesting, options, web search, multi-agent swarms) |
| `vibe-portfolio-analysis` | finance | Daily portfolio analysis workflow — reads `snapshot.yaml`, generates analysis prompts, submits to Vibe-Trading API |
| `polymarket-tail-sweep` | research | Polymarket prediction market scanner — finds expiring markets with favorable No prices, identifies "free money" opportunities |
| `polymarket-vibe-arb` | research | Combined Polymarket scanner + Vibe-Trading analysis pipeline — scan, filter (AI principle-based), submit to Vibe-Trading for deep research |

## Helper Scripts

- `scripts/poll_session.py` — Polls a Vibe-Trading API session for assistant responses
- `scripts/generate_vibe_prompt.py` — Generates portfolio analysis prompts from `snapshot.yaml`
- `scripts/volatility_dashboard.py` — Fetches real-time prices + 30d volatility ranges for BTC/ETH/SOL/Gold
- `scripts/polymarket_arb_scanner.py` — Sub-market level Polymarket scanner with CLOB spread analysis
- `scripts/run_arb_scan.sh` — Wrapper that runs scanner + volatility dashboard in sequence

## Usage

### 1. Install upstream

```bash
pip install vibe-trading-ai
vibe-trading serve
```

### 2. Copy skills into Hermes

```bash
cp -r skills/* ~/.hermes/skills/
cp -r scripts/* ~/.hermes/scripts/
```

### 3. Run

In a Hermes Agent session, load a skill:

```
skill_view(name='vibe-portfolio-analysis')
```

Then follow the instructions in the skill's SKILL.md.

## License

MIT
