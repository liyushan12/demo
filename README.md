# 跨境电商选品分析助手 - Agent 架构版

基于多 Agent 协作的跨境电商选品分析工具，支持亚马逊商品评论爬取、情感分析、痛点提取、需求洞察和选品报告生成。

---

## 架构设计

```
+---------------------------------------------------+
|              OrchestratorAgent                     |
|            (总控 / 调度 / 状态管理)                  |
+----------+----------+-----------+-----------------+
| Scraper  | Analyst  | Reporter  | MetricsCollector |
| Agent    | Agent    | Agent     | Agent            |
|(数据采集) |(分析引擎) |(报告生成)  |(指标采集+存储)    |
+----------+----------+-----------+-----------------+
|              BaseAgent (基类)                       |
|     共享: LLM调用 / 日志 / 错误处理 / 重试           |
+---------------------------------------------------+
```

### Agent 职责

| Agent                 | 职责                           | 输入       | 输出            |
| --------------------- | ------------------------------ | ---------- | --------------- |
| OrchestratorAgent     | 调度所有子 Agent，管理全局状态 | 用户请求   | 完整分析结果    |
| ScraperAgent          | 从亚马逊爬取评论数据           | URL / ASIN | 标准化评论数据  |
| AnalystAgent          | 情感分析 / 痛点提取 / 需求洞察 | 评论数据   | 分析结果 JSON   |
| ReporterAgent         | 生成结构化选品报告             | 分析结果   | Markdown 报告   |
| MetricsCollectorAgent | 采集商品指标 (BSR/价格/评分)   | URL / ASIN | 指标数据 + 趋势 |

### 数据源 Agent

| Agent            | 数据源          | 说明                     |
| ---------------- | --------------- | ------------------------ |
| KeepaSourceAgent | Keepa API       | 历史价格/BSR/评分 (付费) |
| CamelSourceAgent | CamelCamelCamel | 历史价格 (免费)          |
| ScraperAgent     | 亚马逊页面爬虫  | 当前数据 (免费)          |

---

## 项目结构

```
product-analyzer-agent/
├── app.py                           # Streamlit 主界面 (启动入口)
├── config.py                        # 配置文件 (API Key / 分析参数 / 爬虫参数)
├── requirements.txt                 # 依赖清单
├── README.md                        # 项目说明
├── core/
│   ├── __init__.py
│   ├── llm_client.py                # 通义千问 LLM 客户端 (含 Mock 模式)
│   ├── data_loader.py               # 本地 JSON 数据加载
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py            # Agent 基类 (日志/重试/消息传递)
│   │   ├── scraper_agent.py         # 数据采集 Agent (亚马逊爬虫)
│   │   ├── analyst_agent.py         # 分析 Agent (情感/痛点/需求)
│   │   ├── reporter_agent.py        # 报告生成 Agent
│   │   ├── metrics_agent.py         # 指标采集 Agent + 数据源 Agent + 存储
│   │   └── orchestrator_agent.py    # 总控 Agent (调度工作流)
│   └── sources/
│       ├── __init__.py
│       └── amazon_page.py           # 亚马逊页面解析工具函数
├── templates/
│   ├── __init__.py
│   └── prompts.py                   # LLM Prompt 模板
└── data/
    ├── sample_reviews.json          # 示例评论数据 (5 个品类)
    └── product_metrics_history.json # 指标历史快照 (自动生成)
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key（可选）

在环境变量中设置通义千问 API Key（未配置时使用 Mock 数据进行 Demo）：

```bash
# Windows
set DASHSCOPE_API_KEY=your-api-key

# Linux/Mac
export DASHSCOPE_API_KEY="your-api-key"
```

### 3. 启动项目

```bash
streamlit run app.py
```

启动后浏览器会自动打开 `http://localhost:8501`，在侧边栏中选择分析模式：

- **商品链接分析**：粘贴亚马逊商品链接，自动爬取评论并分析
- **Demo 品类分析**：选择预设品类，使用本地示例数据体验完整流程

> 未配置 API Key 时自动使用内置 Mock 数据，无需网络即可体验。

### 4. 代码调用（API 方式）

也可以在 Python 代码中直接调用：

```python
from core.agents import OrchestratorAgent
from core.llm_client import get_client

# 初始化
client = get_client()
orchestrator = OrchestratorAgent(llm_client=client)

# Demo 模式 - 使用本地示例数据
result = orchestrator.analyze_demo("wireless_earbuds")

# URL 模式 - 爬取亚马逊商品评论
result = orchestrator.analyze_from_url("https://amazon.com/dp/B0xxx")

# 采集商品指标
metrics = orchestrator.get_metrics("https://amazon.com/dp/B0xxx")

# 单独生成报告（需自行准备数据，键名须为 category_data / sentiment / pain_points / demands）
report = orchestrator.generate_report({
    "category_data": result["product_info"],
    "sentiment": result["sentiment"],
    "pain_points": result["pain_points"],
    "demands": result["demands"],
})
```

---

## 工作流

| 工作流          | 说明                                |
| --------------- | ----------------------------------- |
| analyze_url     | 爬取亚马逊评论 → 翻译 → 分析 → 汇总 |
| analyze_demo    | 使用本地示例数据进行分析            |
| get_metrics     | 采集商品 BSR/价格/评分等指标        |
| generate_report | 生成 Markdown 选品报告              |

### URL 分析流程详解

```
用户输入 URL
    │
    ▼
ScraperAgent 爬取评论
    │
    ▼
OrchestratorAgent 批量翻译 (英→中)
    │
    ▼
AnalystAgent 并行分析
    ├── 情感分析 (sentiment)
    ├── 痛点提取 (pain_points)
    └── 需求洞察 (demands)
    │
    ▼
返回结构化结果
```

### 指标采集流程详解

```
用户输入 URL
    │
    ▼
MetricsCollectorAgent
    ├── 检测 ASIN 和域名
    ├── 优先尝试 Keepa API
    │   └── 成功 → 解析历史数据
    └── 回退到 ScraperAgent
        └── 爬取当前 BSR/价格/评分
    │
    ▼
SalesEstimator 估算销量
    │
    ▼
MetricsStore 存储快照 (JSON)
    │
    ▼
返回指标数据 + 趋势
```

---

## 核心功能

### 情感分析

- 正面/负面/中性评价比例统计
- 正面和负面关键词提取（英文+中文翻译）
- 整体情感倾向判断 (positive/negative/mixed)

### 痛点提取

- 从负面评论中识别核心痛点
- 按严重程度排序 (high/medium/low)
- 提供典型用户原话佐证
- 给出产品改进建议

### 需求洞察

- 识别已满足和未满足的市场需求
- 发现市场缺口和机会点 (market_gap)
- 按优先级排序 (high/medium/low)

### 指标采集

- BSR (Best Sellers Rank) 追踪
- 价格历史趋势
- 销量估算（基于 BSR 公式）
- 留评率计算
- 本地 JSON 快照存储（保留 180 天）

### 报告生成

- Markdown 格式结构化报告
- 包含：市场概况、情感分析、核心痛点、未满足需求、选品建议
- 推荐指数、差异化方向、定价策略、风险提示

---

## 支持的品类 (Demo 模式)

| 品类 ID          | 中文名称     | 英文名称                   | 平均评分 | 评论数 | 价格区间 |
| ---------------- | ------------ | -------------------------- | -------- | ------ | -------- |
| wireless_earbuds | 无线蓝牙耳机 | Wireless Bluetooth Earbuds | 3.8      | 25     | $15-45   |
| portable_blender | 便携式榨汁机 | Portable Blender           | 3.5      | 20     | $20-40   |
| led_strip_lights | LED 灯带     | LED Strip Lights           | 4.2      | 20     | $10-25   |
| yoga_mat         | 瑜伽垫       | Yoga Mat                   | 4.0      | 20     | $18-35   |
| phone_stand      | 手机支架     | Phone Stand                | 4.3      | 15     | $8-20    |

---

## 配置说明

在 `config.py` 中可调整以下参数：

| 配置项                     | 默认值       | 说明               |
| -------------------------- | ------------ | ------------------ |
| `DASHSCOPE_API_KEY`        | 环境变量     | 通义千问 API Key   |
| `QWEN_MODEL`               | `qwen-turbo` | 使用的模型         |
| `MAX_REVIEWS_PER_ANALYSIS` | 200          | 单次分析最大评论数 |
| `TOP_PAIN_POINTS`          | 5            | 提取的痛点数量     |
| `TOP_DEMANDS`              | 5            | 提取的需求数量     |
| `SCRAPER_MAX_PAGES`        | 15           | 爬虫最大翻页数     |
| `SCRAPER_REQUEST_TIMEOUT`  | 30s          | 请求超时时间       |
| `SCRAPER_MIN_DELAY`        | 2s           | 请求最小间隔       |
| `SCRAPER_MAX_DELAY`        | 5s           | 请求最大间隔       |

---

## 技术栈

| 技术                      | 用途                 |
| ------------------------- | -------------------- |
| **Python 3.8+**           | 运行环境             |
| **通义千问 (qwen-turbo)** | LLM 分析引擎         |
| **dashscope**             | 通义千问 API SDK     |
| **Streamlit**             | Web 交互界面         |
| **Plotly**                | 数据可视化图表       |
| **Pandas**                | 数据处理             |
| **cloudscraper**          | 绕过 Cloudflare 反爬 |
| **BeautifulSoup4 + lxml** | HTML 解析            |
| **requests**              | HTTP 请求            |

---

## LLM Mock 模式

当未配置 API Key 或未安装 dashscope 时，系统自动切换到 Mock 模式：

- 返回预置的品类分析数据（5 个品类各有独立数据）
- 情感分析、痛点提取、需求洞察、报告生成均有对应 Mock 数据
- 适合快速体验和开发调试
- `QwenClient.using_api` 属性标记是否使用了真实 API
- `QwenClient.last_error` 记录最后一次错误信息

---

## Agent 基类能力

所有 Agent 继承 `BaseAgent`，共享以下能力：

| 方法                                    | 说明                     |
| --------------------------------------- | ------------------------ |
| `execute(input_data, context)`          | 核心执行方法（子类实现） |
| `run(input_data, context)`              | 带生命周期钩子的执行入口 |
| `call_llm(system, user, temp)`          | 调用 LLM                 |
| `call_llm_json(system, user, temp)`     | 调用 LLM 并解析 JSON     |
| `log(msg)`                              | 统一日志输出             |
| `send_message(receiver, type, payload)` | 构造 Agent 间消息        |

生命周期钩子：

- `on_start(context)` — Agent 启动时
- `on_finish(result)` — Agent 完成时
- `on_error(error)` — Agent 出错时

---

## 许可证

MIT License
