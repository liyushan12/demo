# 跨境电商选品分析助手 - Agent 架构版

基于多 Agent 协作的跨境电商选品分析工具，支持亚马逊商品评论爬取、情感分析、痛点提取、需求洞察和选品报告生成。

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

| Agent              | 职责                           | 输入                    | 输出             |
|--------------------|-------------------------------|------------------------|-----------------|
| OrchestratorAgent  | 调度所有子 Agent，管理全局状态    | 用户请求                | 完整分析结果      |
| ScraperAgent       | 从亚马逊爬取评论数据             | URL / ASIN             | 标准化评论数据    |
| AnalystAgent       | 情感分析 / 痛点提取 / 需求洞察   | 评论数据                | 分析结果 JSON    |
| ReporterAgent      | 生成结构化选品报告               | 分析结果                | Markdown 报告   |
| MetricsCollectorAgent | 采集商品指标 (BSR/价格/评分)  | URL / ASIN             | 指标数据 + 趋势  |

### 数据源 Agent

| Agent            | 数据源              | 说明                   |
|------------------|--------------------|-----------------------|
| KeepaSourceAgent | Keepa API          | 历史价格/BSR/评分 (付费) |
| CamelSourceAgent | CamelCamelCamel    | 历史价格 (免费)         |
| ScraperAgent     | 亚马逊页面爬虫       | 当前数据 (免费)         |

## 与原版的对比

| 维度     | 原版 (product-analyzer)      | Agent 版 (product-analyzer-agent) |
|----------|------------------------------|----------------------------------|
| 架构     | 单体类 ProductAnalyzer       | 多 Agent 协作                     |
| 职责     | 分析器承担所有逻辑            | 每个 Agent 职责单一                |
| 扩展性   | 添加新数据源需修改分析器       | 新增 SourceAgent 即可              |
| 可测试性 | 需要 mock 整个分析器          | 可单独测试每个 Agent               |
| 错误隔离 | 一个模块失败影响整体          | Agent 独立，错误不会扩散            |
| 复用性   | 逻辑耦合在一个类中            | Agent 可独立复用                   |

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

### 3. 使用方式

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

# 生成选品报告
report = orchestrator.generate_report({
    "category_data": result["product_info"],
    "sentiment": result["sentiment"],
    "pain_points": result["pain_points"],
    "demands": result["demands"],
})
```

## 工作流

| 工作流           | 说明                              |
|-----------------|----------------------------------|
| analyze_url     | 爬取亚马逊评论 → 翻译 → 分析 → 汇总 |
| analyze_demo    | 使用本地示例数据进行分析              |
| get_metrics     | 采集商品 BSR/价格/评分等指标         |
| generate_report | 生成 Markdown 选品报告            |

## 项目结构

```
product-analyzer-agent/
├── config.py                    # 配置文件 (API Key / 分析参数 / 爬虫参数)
├── requirements.txt             # 依赖清单
├── README.md                    # 项目说明
├── core/
│   ├── __init__.py
│   ├── llm_client.py            # 通义千问 LLM 客户端 (含 Mock 模式)
│   ├── data_loader.py           # 本地 JSON 数据加载
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py        # Agent 基类 (日志/重试/消息传递)
│   │   ├── scraper_agent.py     # 数据采集 Agent (亚马逊爬虫)
│   │   ├── analyst_agent.py     # 分析 Agent (情感/痛点/需求)
│   │   ├── reporter_agent.py    # 报告生成 Agent
│   │   ├── metrics_agent.py     # 指标采集 Agent + 数据源 Agent + 存储
│   │   └── orchestrator_agent.py # 总控 Agent (调度工作流)
│   └── sources/
│       ├── __init__.py
│       └── amazon_page.py       # 亚马逊页面解析工具函数
├── templates/
│   ├── __init__.py
│   └── prompts.py               # LLM Prompt 模板
└── data/
    ├── sample_reviews.json      # 示例评论数据 (5 个品类)
    └── product_metrics_history.json  # 指标历史快照 (自动生成)
```

## 支持的品类 (Demo 模式)

| 品类 ID | 中文名称 | 英文名称 | 平均评分 | 评论数 | 价格区间 |
|---------|---------|---------|---------|-------|---------|
| wireless_earbuds | 无线蓝牙耳机 | Wireless Bluetooth Earbuds | 3.8 | 25 | $15-45 |
| portable_blender | 便携式榨汁机 | Portable Blender | 3.5 | 20 | $20-40 |
| led_strip_lights | LED 灯带 | LED Strip Lights | 4.2 | 20 | $10-25 |
| yoga_mat | 瑜伽垫 | Yoga Mat | 4.0 | 20 | $18-35 |
| phone_stand | 手机支架 | Phone Stand | 4.3 | 15 | $8-20 |

## 核心功能

### 情感分析
- 正面/负面/中性评价比例统计
- 正面和负面关键词提取
- 整体情感倾向判断

### 痛点提取
- 从负面评论中识别核心痛点
- 按严重程度排序 (高/中/低)
- 提供典型用户原话佐证

### 需求洞察
- 识别已满足和未满足的市场需求
- 发现市场缺口和机会点
- 按优先级排序

### 指标采集
- BSR (Best Sellers Rank) 追踪
- 价格历史趋势
- 销量估算 (基于 BSR)
- 留评率计算

## 技术栈

- **Python 3.8+**
- **LLM**: 通义千问 (qwen-turbo)
- **爬虫**: cloudscraper + BeautifulSoup4
- **数据源**: Keepa API / CamelCamelCamel / 亚马逊页面爬取

## 许可证

MIT License
