"""
跨境电商选品分析助手 - 配置文件 (Agent 版)
"""
import os

# 通义千问 API 配置
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")
QWEN_MODEL = "qwen-turbo"

# 分析配置
MAX_REVIEWS_PER_ANALYSIS = 200
TOP_PAIN_POINTS = 5
TOP_DEMANDS = 5

# 爬虫配置
SCRAPER_MAX_PAGES = 15
SCRAPER_REQUEST_TIMEOUT = 30
SCRAPER_MIN_DELAY = 2
SCRAPER_MAX_DELAY = 5

# 商品指标数据配置
METRICS_DAILY_DAYS = 30
METRICS_MONTHLY_MONTHS = 6

# 支持的品类列表
CATEGORIES = {
    "wireless_earbuds": "无线蓝牙耳机",
    "portable_blender": "便携式榨汁机",
    "led_strip_lights": "LED 灯带",
    "yoga_mat": "瑜伽垫",
    "phone_stand": "手机支架",
}
