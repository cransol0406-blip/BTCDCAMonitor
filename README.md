# BTC_DCA_Indicator_Monitor

用于 BTC 长期定投指标监控和个人辅助判断。项目通过 GitHub Actions 每 5 分钟运行一次 Python 脚本，获取 BTC 价格、AHR999-like、MVRV Z-Score、MVRV、200 周均线，并通过 Telegram Bot 推送固定中文消息。

本项目不构成投资建议。

## 推送示例

```text
【BTC定投指标监控】

时间：2026-06-04 18:30:00
BTC价格：$68,500.00
AHR999指数：0.92
MVRV Z-Score：1.15
MVRV：1.82
200周均线：$43,200.00

指标状态：
AHR999：定投区（0.45 - 1.2）
MVRV Z-Score：中性偏低（0 - 1.5）
MVRV：中性区（1.5 - 3）
200周均线：价格高于200周均线，未进入极端低估区

操作建议：
普通定投，不触发加倍；等待 AHR999 < 0.45、MVRV < 1 或价格接近200周均线时再提高定投金额。
```

## 指标与口径

- BTC 价格：优先 Binance `BTCUSDT`，失败后 fallback 到 CoinGecko、Coinbase。
- 200 周均线：使用最近 1400 个 BTC 日线收盘价计算简单平均值。
- MVRV：优先使用 Coin Metrics 社区 API 的 `CapMVRVCur`。
- MVRV Z-Score：使用 Coin Metrics 社区 API 的 `CapMrktCurUSD` 和 `CapMVRVCur`，由 `market_cap / mvrv` 反推 realized cap，再计算 `(market_cap - realized_cap) / std(market_cap)`。
- AHR999：采用 AHR999-like 近似计算：`price / GMA200 * price / estimated_price`。其中 `GMA200` 为近 200 日几何均价，`estimated_price` 使用常见 BTC 长期幂律估值近似公式计算。该值不是官方 AHR999 数据源，可能与第三方网站存在差异。

## 阈值规则

- AHR999：`< 0.45` 为低估区，`0.45 - 1.2` 为定投区，`> 1.2` 为偏高区。
- MVRV Z-Score：`< 0` 为低估区，`0 - 1.5` 为中性偏低，`1.5 - 4` 为中性偏高，`>= 4` 为高估区。
- MVRV：`< 1` 为低估区，`1 - 1.5` 为偏低估区，`1.5 - 3` 为中性区，`>= 3` 为偏高区。
- 200 周均线：价格低于均线为长期低估观察区，价格/均线 `< 1.2` 为低位观察区。

## 配置

所有敏感信息必须放入 GitHub Secrets 或本地 `.env`，不要写入代码或 README。

必填：

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

可选：

```text
COINGECKO_API_KEY
COINMETRICS_API_KEY
GLASSNODE_API_KEY
TIMEZONE
```

默认时区为 `Asia/Shanghai`。

## 本地运行

```bash
pip install -r requirements.txt
python -m src.main
```

本地测试：

```bash
pip install -r requirements-dev.txt
python -m pytest tests -q
```

## GitHub Actions

工作流位于 `.github/workflows/btc_indicator_monitor.yml`，支持：

```yaml
on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:
```

GitHub Actions 的 schedule 可能延迟，不适合高频交易或严格实时风控。public 仓库使用标准 GitHub-hosted runner 时通常不消耗免费分钟额度；如果改为 private 仓库，应重新评估 Actions 分钟消耗。

## 缓存

缓存文件为 `data/cache.json`。GitHub Actions 使用 `actions/cache` 在运行之间恢复缓存，减少重复拉取历史日线和链上指标数据。接口失败时，程序优先使用已有缓存并在消息中标注“使用缓存”。

## 常见排查

- Telegram 配置缺失：程序会直接退出，请检查 GitHub Secrets 或本地 `.env`。
- 单个指标获取失败：消息中显示“获取失败”，其他指标继续运行。
- 多个指标失败：操作建议会提示暂不调整定投策略。
- API 限流或网络失败：等待下次运行，或配置可选 API key 提升稳定性。

## 风险提示

本项目仅用于 BTC 定投指标监控和个人辅助决策，不构成投资建议。

链上指标存在口径差异，历史有效不代表未来有效。

GitHub Actions 定时任务可能延迟，不适合高频交易或实时风控。

AHR999、MVRV、MVRV Z-Score 等指标可能因数据源不同而出现差异。
