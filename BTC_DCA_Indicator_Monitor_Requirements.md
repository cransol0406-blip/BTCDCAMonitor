# BTC_DCA_Indicator_Monitor 项目需求文档（最终版）

## 1. 项目目标

项目名称：`BTC_DCA_Indicator_Monitor`

本项目用于通过 GitHub Actions 每 5 分钟自动运行一次 Python 脚本，获取 BTC 价格和四个定投/低估判断指标，并通过 Telegram Bot 推送固定格式的中文监控消息。

本项目要求一次性实现最终版效果，不采用 MVP、第一版、第二版等渐进路线。

必须实现的监控内容：

1. BTC 当前价格
2. AHR999 指数
3. MVRV Z-Score
4. MVRV
5. 200 周均线

推送标题固定为：

```text
btc定投指标监控
```

项目用途：

```text
用于 BTC 长期定投监控、低估区判断、加仓强度辅助决策。
```

重要声明：

```text
本项目只用于个人投资监控和辅助判断，不构成投资建议。
```

---

## 2. 核心运行要求

### 2.1 运行平台

使用 GitHub Actions 定时运行。

必须支持：

```yaml
on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:
```

说明：

- GitHub Actions 的 schedule 使用 UTC。
- GitHub Actions 官方最短 schedule 间隔为 5 分钟。
- 实际触发可能存在延迟，因此本项目不能作为严格实时系统。
- 本项目用于定投监控，不用于高频交易。

### 2.2 运行频率

要求：

```text
每 5 分钟运行一次。
```

每次运行应完成：

```text
获取数据
↓
计算指标
↓
判断指标状态
↓
生成 Telegram 消息
↓
发送 Telegram 推送
```

### 2.3 Python 版本

建议使用：

```text
Python 3.11
```

---

## 3. 必须实现的指标

## 3.1 BTC 当前价格

### 指标说明

获取 BTC/USD 当前价格。

### 推荐数据源

优先级建议：

1. Binance API
2. CoinGecko API
3. Coinbase API

第一优先建议使用 Binance：

```text
https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT
```

如果 Binance 失败，可 fallback 到 CoinGecko 或 Coinbase。

### 输出格式

```text
BTC价格：$68,500.00
```

格式要求：

- 使用美元符号 `$`
- 保留 2 位小数
- 使用千分位
- 若获取失败，显示 `获取失败`

---

## 3.2 AHR999 指数

### 指标说明

AHR999 是 BTC 长周期定投估值指标，常用于判断 BTC 是否处于定投区或低估区。

常见公式：

```text
AHR999 = BTC价格 / 200日定投成本 × BTC价格 / 指数增长估值
```

也可近似表示为：

```text
AHR999 = price / GMA200 × price / estimated_price
```

其中：

- `price`：BTC 当前价格
- `GMA200`：200 日几何均价或 200 日定投成本
- `estimated_price`：基于长期指数增长模型得到的估值价格

### 实现要求

必须实现 AHR999 获取或计算。

实现优先级：

1. 优先使用稳定 API 或公开数据源直接获取 AHR999。
2. 如果无法直接获取，则实现 AHR999-like 近似计算。
3. 如果采用近似计算，必须在代码注释和 README 中说明口径。
4. 不允许因为 AHR999 获取失败导致整个程序退出。
5. 若接口失败且有缓存，则使用缓存值，并在日志中说明。
6. 若接口失败且无缓存，消息中显示 `获取失败`。

### 输出格式

```text
AHR999指数：0.92
```

格式要求：

- 保留 2 位小数
- 若使用缓存，建议显示为：

```text
AHR999指数：0.92（使用缓存）
```

---

## 3.3 MVRV Z-Score

### 指标说明

MVRV Z-Score 用于衡量 BTC 市值相对于已实现市值的偏离程度。

常见公式：

```text
MVRV Z-Score = (Market Cap - Realized Cap) / Std(Market Cap)
```

其中：

- `Market Cap`：BTC 当前市值
- `Realized Cap`：BTC 已实现市值
- `Std(Market Cap)`：历史市值标准差

### 实现要求

必须实现 MVRV Z-Score 获取或计算。

实现优先级：

1. 优先使用 Coin Metrics、Glassnode 或其他可靠数据源直接获取。
2. 若无法直接获取，则使用 Market Cap、Realized Cap 和历史 Market Cap 自行计算。
3. 若自行计算，应缓存历史 Market Cap 数据。
4. 若采用自算口径，应在 README 中说明可能与第三方网站存在口径差异。
5. 不允许因为 MVRV Z-Score 获取失败导致整个程序退出。
6. 若接口失败且有缓存，则使用缓存值。
7. 若接口失败且无缓存，消息中显示 `获取失败`。

### 输出格式

```text
MVRV Z-Score：1.15
```

格式要求：

- 保留 2 位小数
- 允许负数
- 若使用缓存，建议显示为：

```text
MVRV Z-Score：1.15（使用缓存）
```

---

## 3.4 MVRV

### 指标说明

MVRV 用于比较 BTC 当前市值与已实现市值。

公式：

```text
MVRV = Market Cap / Realized Cap
```

也可近似理解为：

```text
MVRV ≈ BTC 当前价格 / Realized Price
```

其中：

- `Market Cap`：当前市场市值
- `Realized Cap`：按每枚 BTC 最后一次链上移动价格计价后的总市值
- `Realized Price`：全网平均链上成本价

### 实现要求

必须实现 MVRV 获取或计算。

实现优先级：

1. 优先直接获取 MVRV 指标。
2. 如果无法直接获取，则通过 `Market Cap / Realized Cap` 计算。
3. 如果无法获取 Realized Cap，但能获取 Realized Price，则通过 `BTC Price / Realized Price` 近似计算。
4. 若采用近似值，应在 README 中说明。
5. 不允许因为 MVRV 获取失败导致整个程序退出。
6. 若接口失败且有缓存，则使用缓存值。
7. 若接口失败且无缓存，消息中显示 `获取失败`。

### 输出格式

```text
MVRV：1.82
```

格式要求：

- 保留 2 位小数
- 若使用缓存，建议显示为：

```text
MVRV：1.82（使用缓存）
```

---

## 3.5 200 周均线

### 指标说明

200 周均线用于判断 BTC 是否接近历史长期低估区。

### 计算方式

使用 BTC 最近 1400 个日线收盘价计算简单平均值：

```text
200周均线 ≈ 最近 1400 个日线收盘价的简单平均值
```

原因：

```text
200周 × 7天 = 1400天
```

### 实现要求

1. 必须获取足够长的 BTC 日线历史数据。
2. 必须自行计算 200 周均线。
3. 历史价格数据应缓存，避免每 5 分钟重复拉取完整数据。
4. 200 周均线可以每天更新一次。
5. 若历史价格接口失败且有缓存，则使用缓存。
6. 若接口失败且无缓存，消息中显示 `获取失败`。

### 输出格式

```text
200周均线：$43,200.00
```

格式要求：

- 使用美元符号 `$`
- 保留 2 位小数
- 使用千分位
- 若使用缓存，建议显示为：

```text
200周均线：$43,200.00（使用缓存）
```

---

# 4. 指标状态判断规则

## 4.1 AHR999 状态

判断规则：

```python
if ahr999 < 0.45:
    status = "低估区（< 0.45）"
elif 0.45 <= ahr999 <= 1.2:
    status = "定投区（0.45 - 1.2）"
else:
    status = "偏高区（> 1.2）"
```

输出示例：

```text
AHR999：定投区（0.45 - 1.2）
```

---

## 4.2 MVRV Z-Score 状态

判断规则：

```python
if mvrv_z < 0:
    status = "低估区（< 0）"
elif 0 <= mvrv_z < 1.5:
    status = "中性偏低（0 - 1.5）"
elif 1.5 <= mvrv_z < 4:
    status = "中性偏高（1.5 - 4）"
else:
    status = "高估区（>= 4）"
```

输出示例：

```text
MVRV Z-Score：中性偏低（0 - 1.5）
```

---

## 4.3 MVRV 状态

判断规则：

```python
if mvrv < 1:
    status = "低估区（< 1）"
elif 1 <= mvrv < 1.5:
    status = "偏低估区（1 - 1.5）"
elif 1.5 <= mvrv < 3:
    status = "中性区（1.5 - 3）"
else:
    status = "偏高区（>= 3）"
```

输出示例：

```text
MVRV：中性区（1.5 - 3）
```

---

## 4.4 200 周均线状态

判断规则：

```python
price_to_200wma = btc_price / ma_200w

if price_to_200wma < 1:
    status = "价格低于200周均线，进入长期低估观察区"
elif 1 <= price_to_200wma < 1.2:
    status = "价格接近200周均线，处于低位观察区"
else:
    status = "价格高于200周均线，未进入极端低估区"
```

输出示例：

```text
200周均线：价格高于200周均线，未进入极端低估区
```

---

# 5. 操作建议生成规则

操作建议必须根据多个指标综合判断，不允许只依赖单一指标。

## 5.1 极端低估 / 战略加仓区

满足以下条件中的 3 个或以上：

```text
AHR999 < 0.45
MVRV Z-Score < 0
MVRV < 1
BTC价格 <= 200周均线
```

输出：

```text
多个低估信号同时触发，可进入战略加仓区，适合分批提高定投金额，但不建议一次性满仓。
```

---

## 5.2 增强定投区

满足以下条件中的 2 个：

```text
AHR999 处于定投区或低估区
MVRV Z-Score 处于低估区或中性偏低
MVRV < 1.5
BTC价格 / 200周均线 < 1.2
```

输出：

```text
部分低估信号出现，可适当提高定投金额，建议继续分批执行。
```

---

## 5.3 普通定投区

条件：

```text
未触发极端低估或增强定投，但 AHR999 处于定投区，或其他指标整体中性。
```

输出：

```text
普通定投，不触发加倍；等待 AHR999 < 0.45、MVRV < 1 或价格接近200周均线时再提高定投金额。
```

---

## 5.4 偏高 / 观察区

条件：

```text
AHR999 > 1.2
且 MVRV >= 3 或 MVRV Z-Score >= 4
且价格明显高于 200周均线
```

输出：

```text
当前未出现低估信号，可降低定投强度或仅观察，不建议追高加仓。
```

---

## 5.5 数据不完整时的建议

如果四个指标中有两个或以上获取失败：

```text
部分关键指标获取失败，暂不调整定投策略，建议等待下一次监控结果。
```

如果 BTC 价格获取失败：

```text
BTC价格获取失败，本次不生成操作建议，请检查数据源或等待下一次运行。
```

---

# 6. Telegram 推送格式

推送格式必须固定。

## 6.1 标准格式

```text
btc定投指标监控

监控时间：2026-06-04 18:30:00
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

## 6.2 低估状态示例

```text
btc定投指标监控

监控时间：2026-06-04 18:30:00
BTC价格：$39,800.00
AHR999指数：0.42
MVRV Z-Score：-0.15
MVRV：0.96
200周均线：$40,500.00

指标状态：
AHR999：低估区（< 0.45）
MVRV Z-Score：低估区（< 0）
MVRV：低估区（< 1）
200周均线：价格低于200周均线，进入长期低估观察区

操作建议：
多个低估信号同时触发，可进入战略加仓区，适合分批提高定投金额，但不建议一次性满仓。
```

## 6.3 获取失败示例

```text
btc定投指标监控

监控时间：2026-06-04 18:30:00
BTC价格：$68,500.00
AHR999指数：获取失败
MVRV Z-Score：1.15（使用缓存）
MVRV：1.82
200周均线：$43,200.00（使用缓存）

指标状态：
AHR999：无法判断
MVRV Z-Score：中性偏低（0 - 1.5）
MVRV：中性区（1.5 - 3）
200周均线：价格高于200周均线，未进入极端低估区

操作建议：
部分关键指标获取失败，暂不调整定投策略，建议等待下一次监控结果。
```

---

# 7. 配置项

所有敏感信息必须使用 GitHub Secrets，不允许写死在代码中。

## 7.1 必须配置

```text
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
```

## 7.2 可选配置

```text
COINGECKO_API_KEY
COINMETRICS_API_KEY
GLASSNODE_API_KEY
TIMEZONE
```

默认时区：

```text
Asia/Shanghai
```

也可以配置为：

```text
America/Los_Angeles
```

---

# 8. 推荐项目结构

```text
BTC_DCA_Indicator_Monitor/
├── .github/
│   └── workflows/
│       └── btc_indicator_monitor.yml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── data_sources.py
│   ├── indicators.py
│   ├── status.py
│   ├── message.py
│   ├── telegram.py
│   ├── cache.py
│   └── utils.py
├── data/
│   └── cache.json
├── tests/
│   ├── test_status.py
│   ├── test_message.py
│   ├── test_indicators.py
│   └── test_cache.py
├── requirements.txt
├── README.md
├── .gitignore
└── .env.example
```

---

# 9. 模块职责

## 9.1 `config.py`

职责：

```text
读取环境变量
校验必要配置
提供全局配置
```

必须读取：

```python
TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID
COINGECKO_API_KEY
COINMETRICS_API_KEY
GLASSNODE_API_KEY
TIMEZONE
```

要求：

- 缺少 Telegram 配置时，程序应退出。
- API key 可选。
- TIMEZONE 缺失时默认使用 `Asia/Shanghai`。

---

## 9.2 `data_sources.py`

职责：

```text
请求外部 API
实现多数据源 fallback
返回标准化数据
```

建议函数：

```python
get_btc_price_usd()
get_btc_daily_history()
get_ahr999()
get_mvrv()
get_mvrv_zscore()
get_market_cap_history()
get_realized_cap()
get_realized_price()
```

要求：

- 所有 requests 请求必须设置 timeout。
- 所有 API 调用必须有异常处理。
- API 失败时返回明确错误信息。
- 不允许静默失败。
- 单个指标失败不能影响其他指标。

---

## 9.3 `indicators.py`

职责：

```text
计算指标
处理数值格式
处理近似计算
```

建议函数：

```python
calculate_200wma(daily_prices)
calculate_mvrv(market_cap, realized_cap)
calculate_mvrv_from_realized_price(price, realized_price)
calculate_mvrv_zscore(market_caps, realized_cap)
calculate_ahr999(price, gma200, estimated_price)
calculate_gma200(daily_prices)
```

要求：

- 输入为空时抛出明确异常。
- 不允许返回误导性的 0。
- 对历史数据长度不足要报错。
- 200WMA 至少需要 1400 个日线收盘价。

---

## 9.4 `status.py`

职责：

```text
判断每个指标状态
生成综合操作建议
```

建议函数：

```python
get_ahr999_status(value)
get_mvrv_zscore_status(value)
get_mvrv_status(value)
get_200wma_status(price, ma_200w)
get_action_suggestion(data, statuses)
```

要求：

- 指标为 None 或获取失败时返回 `无法判断`。
- 综合建议要考虑数据完整性。
- 阈值集中管理，便于修改。

---

## 9.5 `message.py`

职责：

```text
生成 Telegram 推送文本
```

建议函数：

```python
build_message(data, statuses, suggestion)
```

要求：

- 消息格式必须完全符合第 6 节。
- 不使用 Markdown，以免 Telegram 特殊字符转义失败。
- 中文内容使用 UTF-8。
- 数字格式统一。

数字格式：

```text
BTC价格：$68,500.00
AHR999指数：0.92
MVRV Z-Score：1.15
MVRV：1.82
200周均线：$43,200.00
```

---

## 9.6 `telegram.py`

职责：

```text
发送 Telegram 消息
```

建议函数：

```python
send_telegram_message(text)
```

调用方式：

```text
POST https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage
```

请求体：

```json
{
  "chat_id": "TELEGRAM_CHAT_ID",
  "text": "消息内容"
}
```

要求：

- 设置 timeout。
- 发送失败时抛出异常。
- 不使用 Markdown parse_mode。
- 打印发送结果日志，但不要打印 bot token。

---

## 9.7 `cache.py`

职责：

```text
读写缓存
减少 API 请求
在接口失败时 fallback
```

缓存文件：

```text
data/cache.json
```

建议缓存字段：

```json
{
  "btc_daily_prices": {
    "updated_at": "2026-06-04T00:00:00+08:00",
    "data": []
  },
  "ma_200w": {
    "updated_at": "2026-06-04T00:00:00+08:00",
    "value": 43200.0
  },
  "ahr999": {
    "updated_at": "2026-06-04T00:00:00+08:00",
    "value": 0.92
  },
  "mvrv_zscore": {
    "updated_at": "2026-06-04T00:00:00+08:00",
    "value": 1.15
  },
  "mvrv": {
    "updated_at": "2026-06-04T00:00:00+08:00",
    "value": 1.82
  }
}
```

缓存策略：

```text
BTC 当前价格：每次实时获取，不强依赖缓存。
历史日线价格：每天更新一次。
200周均线：每天更新一次。
AHR999：每小时或每天更新一次，若依赖当前价格计算则每次刷新。
MVRV Z-Score：每小时或每天更新一次。
MVRV：每小时或每天更新一次。
```

注意：

- GitHub Actions 每次运行环境是临时的。
- 如果希望缓存跨 workflow 运行保留，需要使用 actions/cache 或将缓存提交到仓库。
- 更推荐使用 GitHub Actions cache。
- 如果不实现跨运行缓存，则每次都要从外部 API 拉取，容易触发限流。

---

# 10. GitHub Actions 工作流要求

工作流文件：

```text
.github/workflows/btc_indicator_monitor.yml
```

示例：

```yaml
name: BTC_DCA_Indicator_Monitor

on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: btc-dca-indicator-monitor
  cancel-in-progress: true

jobs:
  monitor:
    runs-on: ubuntu-latest
    timeout-minutes: 3

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Restore cache
        uses: actions/cache@v4
        with:
          path: data/cache.json
          key: btc-indicator-cache-${{ github.run_id }}
          restore-keys: |
            btc-indicator-cache-

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run BTC indicator monitor
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
          COINGECKO_API_KEY: ${{ secrets.COINGECKO_API_KEY }}
          COINMETRICS_API_KEY: ${{ secrets.COINMETRICS_API_KEY }}
          GLASSNODE_API_KEY: ${{ secrets.GLASSNODE_API_KEY }}
          TIMEZONE: Asia/Shanghai
        run: |
          python -m src.main
```

要求：

- `timeout-minutes` 建议设置为 3，避免异常卡住消耗过多 Actions 分钟。
- 使用 `concurrency` 避免上一次任务未结束时新任务堆积。
- 不要在日志中输出任何 token。
- 依赖安装应尽量简单，避免每次运行耗时过长。

---

# 11. `requirements.txt`

建议：

```text
requests>=2.31.0
pandas>=2.0.0
numpy>=1.24.0
python-dotenv>=1.0.0
```

如果不使用 pandas，也可只使用 requests 和 numpy。

---

# 12. 错误处理要求

程序必须处理以下异常：

1. BTC 价格接口失败。
2. AHR999 接口失败。
3. MVRV 接口失败。
4. MVRV Z-Score 接口失败。
5. 历史价格接口失败。
6. Telegram 发送失败。
7. API 限流。
8. 缓存文件不存在。
9. 缓存文件损坏。
10. 指标数据为空。
11. 指标数据格式错误。
12. GitHub Secrets 未配置。
13. 历史数据长度不足。
14. 当前价格为 0 或 None。
15. Realized Cap 为 0 或 None。

处理原则：

```text
单个指标失败，不影响其他指标。
BTC价格失败，本次仍发送错误提示消息。
Telegram配置缺失，程序直接退出。
外部API失败时优先使用缓存。
无缓存时显示“获取失败”。
不得返回误导性默认值，例如 0。
```

---

# 13. 日志要求

程序应输出运行日志，便于在 GitHub Actions 中排查问题。

日志应包括：

```text
开始运行时间
数据源调用情况
各指标获取成功或失败
是否使用缓存
Telegram 是否发送成功
程序结束时间
```

日志不得包括：

```text
Telegram Bot Token
API Key
完整 Secrets
```

---

# 14. 测试要求

必须编写单元测试。

## 14.1 状态判断测试

文件：

```text
tests/test_status.py
```

覆盖：

```text
AHR999 < 0.45
AHR999 = 0.45
AHR999 = 1.2
AHR999 > 1.2

MVRV Z-Score < 0
MVRV Z-Score = 0
MVRV Z-Score = 1.5
MVRV Z-Score = 4

MVRV < 1
MVRV = 1
MVRV = 1.5
MVRV = 3

BTC价格 < 200WMA
BTC价格 = 200WMA
BTC价格 / 200WMA = 1.2
BTC价格明显高于200WMA
```

## 14.2 消息格式测试

文件：

```text
tests/test_message.py
```

检查：

```text
标题是否为 btc定投指标监控
是否包含监控时间
是否包含 BTC价格
是否包含 AHR999指数
是否包含 MVRV Z-Score
是否包含 MVRV
是否包含 200周均线
是否包含 指标状态
是否包含 操作建议
低估状态文案是否正确
获取失败文案是否正确
```

## 14.3 指标计算测试

文件：

```text
tests/test_indicators.py
```

覆盖：

```text
200WMA计算
GMA200计算
MVRV计算
MVRV Z-Score计算
AHR999计算
历史数据不足时报错
Realized Cap为0时报错
输入为空时报错
```

## 14.4 缓存测试

文件：

```text
tests/test_cache.py
```

覆盖：

```text
缓存文件不存在
缓存文件损坏
缓存读取成功
缓存写入成功
缓存过期判断
缓存 fallback
```

---

# 15. README 要求

README.md 必须包括以下内容：

1. 项目简介
2. 推送效果截图或示例
3. 指标说明
4. 指标阈值说明
5. 数据源说明
6. AHR999 口径说明
7. MVRV 和 MVRV Z-Score 口径说明
8. 200周均线计算说明
9. Telegram Bot 配置方法
10. GitHub Secrets 配置方法
11. GitHub Actions 启用方法
12. public 仓库使用说明
13. 本地运行方法
13. 常见错误排查
14. 风险提示

风险提示必须包含：

```text
本项目仅用于 BTC 定投指标监控和个人辅助决策，不构成投资建议。
链上指标存在口径差异，历史有效不代表未来有效。
GitHub Actions 定时任务可能延迟，不适合高频交易或实时风控。
AHR999、MVRV、MVRV Z-Score 等指标可能因数据源不同而出现差异。
```

---

# 16. 本地运行要求

必须支持本地运行：

```bash
pip install -r requirements.txt
python -m src.main
```

必须提供 `.env.example`：

```text
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
COINGECKO_API_KEY=
COINMETRICS_API_KEY=
GLASSNODE_API_KEY=
TIMEZONE=Asia/Shanghai
```

本地运行时可使用 python-dotenv 读取 `.env`。

---

# 17. GitHub 仓库与免费额度说明

本项目明确采用：

```text
public GitHub repository
```

推荐仓库名称：

```text
BTC_DCA_Indicator_Monitor
```

本项目每 5 分钟运行一次：

```text
每小时 12 次
每天 288 次
每月约 8640 次
```

由于本项目使用 public 仓库，标准 GitHub-hosted runner 通常不消耗 GitHub Actions 免费分钟额度。因此，本项目按 public 仓库运行时，一般不会因为每 5 分钟执行一次而耗尽免费分钟。

如果用户已有另一个 SPY/QQQ 监控项目也在 public 仓库中运行，并且同样使用标准 GitHub-hosted runner，两个项目同时运行通常也不会消耗免费分钟额度。

两个项目合计运行频率约为：

```text
每小时 24 次
每天 576 次
每月约 17280 次
```

使用 public 仓库时，该频率通常仍不计入免费分钟。

注意事项：

1. 不要把任何密钥、token、API key 写入代码或 README。
2. 即使仓库是 public，GitHub Secrets 仍然可以安全保存敏感信息。
3. Telegram Bot Token、Telegram Chat ID、API Key 必须全部放入 GitHub Secrets。
4. 如果未来将仓库改为 private，则每 5 分钟运行一次可能明显消耗 GitHub Actions 分钟额度。
5. 为避免异常任务堆积，应设置 `timeout-minutes: 3` 和 `concurrency`。
6. 使用缓存和数据源 fallback，减少 API 限流风险。
7. public 仓库会公开代码和配置文件，但不会公开 GitHub Secrets 的具体值。

---

# 18. 最终验收标准

项目完成后必须满足：

```text
1. GitHub Actions 每 5 分钟触发一次。
2. 能获取 BTC 当前价格。
3. 能获取或计算 AHR999。
4. 能获取或计算 MVRV Z-Score。
5. 能获取或计算 MVRV。
6. 能计算 200周均线。
7. 能判断四个指标状态。
8. 能生成固定中文推送格式。
9. 能通过 Telegram Bot 发送消息。
10. 单个指标失败不导致整个程序崩溃。
11. 支持缓存和 fallback。
12. 支持本地运行。
13. 不泄露任何 token 或 API key。
14. 有基本单元测试。
```

---

# 19. 最终推送示例

```text
btc定投指标监控

监控时间：2026-06-04 18:30:00
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
