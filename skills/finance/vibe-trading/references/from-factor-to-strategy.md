# From Factor to Strategy: The Missing Pipeline

Having a set of factors (like Alpha158's 158 factors) is just the raw ingredients.
Between "I have factors" and "I have a profitable strategy" there are 6 steps:

## 1. Factor Synthesis (信号合成)

Multiple factors must be combined into a single predictive score:

| Method | Description | When to Use |
|--------|-------------|-------------|
| **Equal-weight rank** | `score = avg(rank(f1), rank(f2), ...)` | Simple baseline; noise factors dilute signal |
| **IC-weighted** | `score = Σ(IC_i × factor_i)` | Factors have unequal predictability; needs stable IC |
| **ML model** | `score = LightGBM.predict(features)` | Qlib default. Model learns non-linear interactions. **Start here.** |
| **Factor orthogonalization** | Remove multicollinearity before combining | When factors are highly correlated; avoids double-counting |

**Qlib does this**: you pick `model=LightGBM` and it learns the synthesis weights automatically.

## 2. Stock Selection (选股)

Score → which stocks to hold:

| Method | Logic | Pros/Cons |
|--------|-------|-----------|
| **Top-K** | Pick top N by score daily | Simple; ignores spacing |
| **Quantile truncation** | Long top 20%, short bottom 20% | Qlib default. Market-neutral style. |
| **Threshold cutoff** | Score > 0.5 buy, < -0.3 sell | Intuitive; threshold tuning needed |
| **Rank-and-rotate** | Sort by score, hold top decile, rotate when rank drops | Lower turnover |

**Qlib default**: daily long-short (top 30% long, bottom 30% short).

## 3. Portfolio Weighting (权重分配)

How much of each selected stock:

| Method | Description |
|--------|-------------|
| **Equal weight** | 1/N. Simplest. Good starting point. |
| **Market-cap weight** | Large caps get more weight. Risk: over-concentration. |
| **Inverse-vol weight** | Lower volatility stocks get higher weight. Risk-parity light. |
| **Risk parity** | Each stock contributes equal risk to portfolio. Needs vol estimation. |
| **Mean-variance (Markowitz)** | Max Sharpe ratio. Sensitive to input estimates. |

**Qlib default**: equal weight within selected pool.

## 4. Risk Control (风控)

**The difference between a backtest and a live strategy. Most beginners skip this and lose money.**

| Constraint | Purpose | Typical Value |
|------------|---------|---------------|
| **Industry neutrality** | Don't bet on one sector | Match benchmark industry weights |
| **Market-cap neutrality** | Don't bet on size factor | Match size distribution |
| **Single-stock cap** | Limit concentration | Max 10% per stock |
| **Volatility target** | Keep portfolio vol predictable | 15-20% annualized |
| **Max drawdown stop** | Emergency stop | -20% triggers risk review |
| **Turnover limit** | Control trading costs | Max 20% daily turnover |

**Real cost of ignoring risk control**: A backtest might show 20% ARR, but live trading with the same signals could lose 30% in one sector rotation event.

## 5. Trading Execution (交易执行)

**Backtests assume fair price execution. Reality disagrees.**

| Factor | Backtest Assumption | Reality |
|--------|-------------------|---------|
| **Slippage** | Market price at signal time | Price moves while order routes (0.1-0.5% for liquid stocks) |
| **Impact cost** | None | Large orders move the price (0.2-2% for illiquid small caps) |
| **Execution delay** | Instant | 1-30 seconds latency in practice |
| **Minimum lot** | Any fraction | A-shares: 100 shares minimum |
| **T+1** | Same-day round trip | A-shares: must hold overnight before selling |
| **Circuit breakers** | None | Stocks can halt 10% limit up/down in A-shares |

**Practical rule**: Apply minimum 0.1-0.3% slippage in backtests; for small-cap A-shares, use 0.5%.

## 6. Rebalancing Schedule (再平衡频率)

| Frequency | Turnover | Signal Decay | Best For |
|-----------|----------|-------------|----------|
| **Daily** | High | Low signal decay | High-frequency factors (alpha decay < 1 day) |
| **Weekly** | Medium | Some decay | Standard ML factors (Alpha158/LightGBM) |
| **Monthly** | Low | Significant decay | Fundamental factors (PE, PB, ROE) |
| **Event-driven** | Variable | Reacts to changes | Only when signal crosses threshold |

**Qlib default**: daily rebalance with long-short strategy.

---

## Putting It Together: A Complete Qlib Strategy Config

```python
config = {
    # Data
    "data": "csi300",
    "start_time": "2008-01-01",
    "end_time": "2020-08-01",

    # Factor (Step 1-2)
    "factors": "Alpha158",        # Use built-in 158 factors
    "model": "LightGBM",           # ML model learns synthesis weights

    # Stock selection (Step 3)
    "topk": 50,                    # Top 50 stocks daily
    "n_drop": 50,                  # Drop bottom 50

    # Weighting (Step 3)
    "weight_method": "equal",

    # Risk control (Step 4)
    "industry_neutral": True,
    "max_position": 0.1,           # 10% per stock max

    # Trading cost (Step 5)
    "slippage": 0.001,
    "cost": 0.0003,

    # Rebalancing (Step 6)
    "rebalance": "daily",

    # Output
    "report_path": "results/summary.html"
}
```

---

## Recommended Beginner Progression

1. **Run Qlib's `work_by_code.py`** — see what a full pipeline looks like
2. **Swap models** — try LightGBM → LSTM → Transformer, compare IC/ARR/MDD
3. **Swap factors** — try Alpha158 → Alpha360, see if more factors help
4. **Tune risk** — add industry neutral, increase slippage, see how returns change
5. **Build your own factor** — write one simple factor, add it to the pipeline
6. **Interpret** — use Qlib's model interpreter to see which factors the model relies on most
