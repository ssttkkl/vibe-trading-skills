# 2026-06-27 扫尾盘实战：关键发现

## 1. GPT-5.6 Resolution Rules

**盘口**: "GPT-5.6 released by June 30?" → No @ 98.4¢

**关键发现**: vibe-trading 查到了 Polymarket 的 Resolution Rules 原文：
> *"A qualifying model must be launched and publicly accessible, including via open beta or open rolling waitlist signups. A closed beta or any form of private access will not suffice."*

6/26 OpenAI 发布 GPT-5.6 是 limited preview（仅面向 trusted partners），符合 "private access" 定义 → 不算 released。

## 2. SpaceX 估值：NPM ≠ 公开市值

**盘口**: SpaceX valuation $1.35T/$1.45T/$1.5T → No @ ~98¢

**关键发现**: Polymarket 规则引用 Nasdaq Private Market (NPM) 私募估值，**不是公开 SPCX 市值**。SPCX 公开交易后市值 $2.02T，但 NPM 最后数据远低于阈值。这三个盘口不是千倍错价，No 定价正确。

## 3. US 6/26 军事打击伊朗

vibe-trading 通过 web_search 发现了 US Central Command 6/26 对伊朗的军事打击（回应霍尔木兹海峡商船攻击），这个新闻被扫描脚本完全遗漏，说明 vibe-trading 的全权调研能力。

## 4. 期权链概率验证

| 盘口 | 工具 | 发现 |
|------|------|------|
| WTI $80 (No @ 95.8¢) | OVX=46.96 | 2.69σ → 真实概率~0.4%，市场定价4.2%（高估10倍） |
| 黄金 $3,900 (No @ 91.7¢) | GVZ=18.5% | 1.85σ → 真实概率~3.2%，市场定价8.3%（高估2.6倍） |
| BTC $55K (No @ 95.0¢) | BVIV=53% | 1.56σ → 真实概率~5.9%，市场定价5.0%（略偏乐观） |

## 5. 价格盘的三段判断法

1. **用期权隐含波动率**（OVX/GVZ/BVIV）算 z-score 和真实概率
2. **对比市场定价**（1 - No价格）看高估/低估
3. **结合宏观面**判断厚尾风险（地缘升级、趋势动量）

不应只看当前价格在范围内就判断。
