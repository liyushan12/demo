"""
跨境电商选品分析助手 - Streamlit 主界面 (Agent 架构版)
支持两种模式：URL 爬取分析 / Demo 品类分析
UI 风格：Glassmorphism + Lucide Icons + WCAG AA
"""
import streamlit as st
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.data_loader import (
    get_categories, get_reviews_by_category, get_negative_reviews
)
from core.agents import OrchestratorAgent
from core.agents.metrics_agent import MetricsCollectorAgent, MetricsStore, SalesEstimator
from core.llm_client import QwenClient, get_client
from config import CATEGORIES

# 便捷函数 - 复用原版 API
def fetch_and_store_product_metrics(url, keepa_api_key=""):
    """获取商品数据并存储（Agent 版）"""
    orchestrator = OrchestratorAgent(llm_client=get_client(), data_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    return orchestrator.get_metrics(url, keepa_api_key)

def get_all_trends(product_id):
    """获取所有趋势数据"""
    store = MetricsStore(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    return store.get_trends(product_id)

def format_number(num):
    return SalesEstimator.format_number(num)

def format_rate(rate):
    return SalesEstimator.format_rate(rate)

def check_keepa_status(api_key):
    """检查 Keepa API 状态"""
    from core.agents.metrics_agent import KeepaSourceAgent
    agent = KeepaSourceAgent()
    # 简单检查
    if not api_key:
        return {"valid": False, "error": "未配置 API Key"}
    return {"valid": True, "tokens_left": "unknown", "error": None}

st.set_page_config(
    page_title="跨境电商选品分析",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== SVG 图标 (Lucide) ====================
ICONS = {
    "search": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "link": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>',
    "spider": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 2v4"/><path d="M12 18v4"/><path d="m4.93 4.93 2.83 2.83"/><path d="m16.24 16.24 2.83 2.83"/><path d="M2 12h4"/><path d="M18 12h4"/><path d="m4.93 19.07 2.83-2.83"/><path d="m16.24 7.76 2.83-2.83"/></svg>',
    "brain": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/></svg>',
    "file-text": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
    "bar-chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="20" y2="10"/><line x1="18" x2="18" y1="20" y2="4"/><line x1="6" x2="6" y1="20" y2="16"/></svg>',
    "trending-up": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "trending-down": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 17 13.5 8.5 8.5 13.5 2 7"/><polyline points="16 17 22 17 22 11"/></svg>',
    "minus": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14"/></svg>',
    "flame": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>',
    "clipboard-list": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/></svg>',
    "lightbulb": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/></svg>',
    "target": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "package": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7.5 4.27 9 5.15"/><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/></svg>',
    "database": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></svg>',
    "star": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "star-empty": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "message-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/></svg>',
    "dollar-sign": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "shield-check": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/></svg>',
    "check-circle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/></svg>',
    "alert-triangle": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>',
    "zap": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 14a1 1 0 0 1-.78-1.63l9.9-10.2a.5.5 0 0 1 .86.46l-1.92 6.02A1 1 0 0 0 13 10h7a1 1 0 0 1 .78 1.63l-9.9 10.2a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14z"/></svg>',
    "key": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m15.5 7.5 2.3 2.3a1 1 0 0 0 1.4 0l2.1-2.1a1 1 0 0 0 0-1.4L19 4"/><path d="m21 2-9.6 9.6"/><circle cx="7.5" cy="15.5" r="5.5"/></svg>',
    "settings": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>',
    "play": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>',
    "thumbs-up": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2h0a3.13 3.13 0 0 1 3 3.88Z"/></svg>',
    "calendar": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 2v4"/><path d="M16 2v4"/><rect width="18" height="18" x="3" y="4" rx="2"/><path d="M3 10h18"/></svg>',
    "external-link": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></svg>',
    "wifi": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/></svg>',
    "wifi-off": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M2 2 22 22"/></svg>',
    "shopping-cart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>',
    "award": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>',
    "pie-chart": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    "activity": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-2.48a2 2 0 0 0-1.93 1.46l-2.35 8.36a.25.25 0 0 1-.48 0L9.24 2.18a.25.25 0 0 0-.48 0l-2.35 8.36A2 2 0 0 1 4.49 12H2"/></svg>',
    "tag": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.43 2.43 0 0 0 3.42 0l6.58-6.58a2.43 2.43 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5" fill="currentColor"/></svg>',
    "hash": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="9" y2="9"/><line x1="4" x2="20" y1="15" y2="15"/><line x1="10" x2="8" y1="3" y2="21"/><line x1="16" x2="14" y1="3" y2="21"/></svg>',
    "percent": '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" x2="5" y1="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>',
}


def icon(name: str, size: int = 20) -> str:
    """返回 SVG 图标 HTML，带固定尺寸防止布局偏移"""
    svg = ICONS.get(name, "")
    if not svg:
        return ""
    # 替换 width/height 为指定尺寸
    svg = svg.replace(f'width="20"', f'width="{size}"').replace(f'height="20"', f'height="{size}"')
    return f'<span class="icon" style="display:inline-flex;align-items:center;justify-content:center;width:{size}px;height:{size}px;flex-shrink:0;">{svg}</span>'

# ==================== 关键词翻译映射 ====================
KEYWORD_TRANSLATIONS = {
    # 正面
    "quality": "质量好", "comfortable": "舒适", "value": "性价比高", "easy": "易用",
    "great": "很棒", "good": "好", "excellent": "优秀", "perfect": "完美",
    "love": "喜欢", "best": "最好", "nice": "不错", "amazing": "惊艳",
    "wonderful": "很棒", "fantastic": "极好", "awesome": "太棒了", "sturdy": "结实",
    "durable": "耐用", "lightweight": "轻便", "portable": "便携", "reliable": "可靠",
    "fast": "快速", "smooth": "流畅", "clear": "清晰", "powerful": "强大",
    "soft": "柔软", "convenient": "方便", "effective": "有效", "solid": "扎实",
    "compact": "紧凑", "stylish": "时尚", "beautiful": "漂亮", "elegant": "优雅",
    "quiet": "安静", "accurate": "精准", "bright": "明亮", "clean": "干净",
    "comfort": "舒适", "premium": "高端", "intuitive": "直观", "responsive": "响应快",
    "versatile": "多功能", "impressive": "令人印象深刻", "satisfactory": "满意",
    "functional": "功能性强", "practical": "实用", "efficient": "高效",
    # 负面
    "broke": "坏了", "cheap": "廉价", "uncomfortable": "不舒服", "disappointing": "令人失望",
    "defective": "有缺陷", "flimsy": "脆弱", "difficult": "困难", "loud": "噪音大",
    "heavy": "沉重", "slow": "慢", "poor": "差", "terrible": "糟糕", "worst": "最差",
    "broken": "破损", "faulty": "故障", "leak": "漏水", "noise": "噪音",
    "expensive": "太贵", "overpriced": "价格过高", "useless": "没用", "waste": "浪费",
    "fragile": "易碎", "unreliable": "不可靠", "complicated": "复杂", "confusing": "令人困惑",
    "itchy": "发痒", "tight": "太紧", "loose": "太松", "smell": "有异味",
    "sticky": "粘手", "sharp": "太锋利", "thin": "太薄", "weak": "太弱",
    "hot": "发烫", "cold": "太冷", "rough": "粗糙", "hard": "太硬",
    "ugly": "难看", "misleading": "误导", "scam": "骗局", "garbage": "垃圾",
    "horrible": "恐怖", "frustrating": "令人沮丧", "annoying": "烦人",
    "uncomfortably": "不舒服地", "damaged": "损坏", "returned": "退货",
}


def translate_keyword(kw: str) -> str:
    """翻译关键词，返回 'keyword（中文）' 格式。
    如果关键词已包含中文括号翻译，则直接返回。"""
    # 如果已经包含中文括号翻译，直接返回
    if '（' in kw and '）' in kw:
        return kw
    lower = kw.lower().strip()
    cn = KEYWORD_TRANSLATIONS.get(lower, "")
    if cn:
        return f"{kw}（{cn}）"
    return kw


# ==================== 全局样式 ====================
st.markdown("""
<style>
/* Google Fonts 导入 - 独特字体搭配 */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,800;0,900;1,400&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ============================================================
   Design Tokens — Luxury Editorial Aesthetic
   主色 Primary:   Deep Midnight #0a0e27 → Gold Accent #d4a574
   辅助色 Secondary: Warm Rose #c9727d / Cool Sage #7d9b8c
   中性色 Neutral:  Warm Grays with depth
   ============================================================ */
:root {
    /* Primary - Deep Luxe */
    --p-50:  #f7f5f0;  --p-100: #ede8dc;  --p-200: #ddd3be;
    --p-300: #c9b896;  --p-400: #b89b6e;  --p-500: #d4a574;
    --p-600: #c49462;  --p-700: #a67c4a;  --p-800: #8a6640;
    --p-900: #6e5235;
    /* Secondary - Rose */
    --s-50:  #fdf2f3;  --s-100: #fce4e7;  --s-200: #facdd3;
    --s-300: #f5a3ae;  --s-400: #ed6d80;  --s-500: #c9727d;
    --s-600: #b55a66;  --s-700: #994955;  --s-800: #803e49;
    /* Tertiary - Sage */
    --t-50:  #f3f7f5;  --t-100: #e0ebe5;  --t-200: #c3d7cc;
    --t-300: #9dbbaa;  --t-400: #7d9b8c;  --t-500: #5f8070;
    --t-600: #4b6759;  --t-700: #3d5349;  --t-800: #33443d;
    /* Neutral - Warm Slate */
    --n-50:  #faf9f7;  --n-100: #f4f2ee;  --n-200: #e8e4dc;
    --n-300: #d4cec2;  --n-400: #a8a192;  --n-500: #7d7768;
    --n-600: #5c574a;  --n-700: #3d3a33;  --n-800: #1f1d1a;
    --n-900: #0a0908;
    /* Semantic */
    --success: #5f8070;  --warning: #c9a55a;  --danger: #c9727d;
    /* Surface - Dark Luxury */
    --bg:       #0a0e27;
    --bg-sub:   #0f1333;
    --surface:  #141836;
    --surface-2: #1a1f45;
    --border:   rgba(212,165,116,0.15);
    --border-hover: rgba(212,165,116,0.3);
    /* Gold Accents */
    --gold: #d4a574;
    --gold-glow: rgba(212,165,116,0.2);
    --gold-gradient: linear-gradient(135deg, #d4a574 0%, #e8c9a0 50%, #d4a574 100%);
    /* Shadow - Deep & Dramatic */
    --shadow-sm:  0 2px 8px rgba(0,0,0,0.3);
    --shadow-md:  0 8px 24px rgba(0,0,0,0.4);
    --shadow-lg:  0 16px 48px rgba(0,0,0,0.5);
    --shadow-xl:  0 24px 64px rgba(0,0,0,0.6);
    --shadow-glow: 0 0 40px rgba(212,165,116,0.15);
    --shadow-ring: 0 0 0 2px rgba(212,165,116,0.3);
    /* Radius */
    --r-sm: 6px;  --r-md: 10px;  --r-lg: 14px;  --r-xl: 20px;  --r-2xl: 28px;
    /* Spacing (8px grid) */
    --sp-1: 4px;  --sp-2: 8px;  --sp-3: 12px;  --sp-4: 16px;
    --sp-5: 20px; --sp-6: 24px; --sp-7: 28px;  --sp-8: 32px;
    /* Typography - Distinctive */
    --font-display: 'Playfair Display', Georgia, 'Times New Roman', serif;
    --font-body: 'DM Sans', -apple-system, 'Segoe UI', sans-serif;
    --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
    --font: var(--font-body);
    --lh: 1.65;
}

/* ---- 亮色模式 (Luxury Light) ---- */
@media (prefers-color-scheme: light) {
    :root {
        --bg:       #faf9f7;
        --bg-sub:   #f4f2ee;
        --surface:  #ffffff;
        --surface-2: #f7f5f0;
        --border:   rgba(10,9,8,0.1);
        --border-hover: rgba(10,9,8,0.2);
        --n-50:  #faf9f7;  --n-100: #f4f2ee;  --n-200: #e8e4dc;
        --n-300: #d4cec2;  --n-400: #a8a192;  --n-500: #7d7768;
        --n-600: #5c574a;  --n-700: #3d3a33;  --n-800: #1f1d1a;
        --n-900: #0a0908;
        --shadow-sm:  0 2px 8px rgba(0,0,0,0.06);
        --shadow-md:  0 8px 24px rgba(0,0,0,0.08);
        --shadow-lg:  0 16px 48px rgba(0,0,0,0.1);
        --shadow-xl:  0 24px 64px rgba(0,0,0,0.12);
        --shadow-glow: 0 0 40px rgba(164,124,74,0.1);
    }
}

/* ---- 全局重置 ---- */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}
html {
    font-size: 16px;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}
body, .stApp {
    font-family: var(--font-body);
    line-height: var(--lh);
    color: var(--n-800);
    background: var(--bg);
    overflow-x: hidden;
}

/* ---- 全局背景纹理 ---- */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        radial-gradient(ellipse at 20% 50%, rgba(212,165,116,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 80% 20%, rgba(125,155,140,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 80%, rgba(201,114,125,0.05) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
}

/* ---- 入场动画 ---- */
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
}
@keyframes slideInLeft {
    from { opacity: 0; transform: translateX(-20px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes slideInRight {
    from { opacity: 0; transform: translateX(20px); }
    to   { opacity: 1; transform: translateX(0); }
}
@keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}
@keyframes pulse-ring {
    0% { box-shadow: 0 0 0 0 rgba(212,165,116,0.4); }
    70% { box-shadow: 0 0 0 8px rgba(212,165,116,0); }
    100% { box-shadow: 0 0 0 0 rgba(212,165,116,0); }
}
@keyframes float {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-6px); }
}
@keyframes gold-shimmer {
    0% { background-position: -100% 0; }
    100% { background-position: 200% 0; }
}
@keyframes glow-pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
}
.anim-fade-up { animation: fadeInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) both; }
.anim-fade { animation: fadeIn 0.5s ease-out both; }
.anim-slide-left { animation: slideInLeft 0.5s cubic-bezier(0.23, 1, 0.32, 1) both; }
.anim-slide-right { animation: slideInRight 0.5s cubic-bezier(0.23, 1, 0.32, 1) both; }
.anim-d1 { animation-delay: 0.08s; }
.anim-d2 { animation-delay: 0.16s; }
.anim-d3 { animation-delay: 0.24s; }
.anim-d4 { animation-delay: 0.32s; }
.anim-d5 { animation-delay: 0.4s; }
.anim-d6 { animation-delay: 0.48s; }

/* -- 尊重用户减少动效偏好 -- */
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
    }
}

/* -- 全局 cursor-pointer for interactive elements -- */
.stButton button, .stRadio label, .stSelectbox,
.stTabs [data-baseweb="tab"], a, .hero-tag, .tag,
.m-card, .feat-c, .pain-c, .dem-row, .rev-c {
    cursor: pointer;
}

#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; }

/* ---- 主内容区 ---- */
.block-container {
    padding: var(--sp-8) var(--sp-8) var(--sp-4) !important;
    max-width: 1280px !important;
    margin: 0 auto;
    position: relative;
    z-index: 1;
}

/* ---- 侧边栏 ---- */
section[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
}
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: var(--gold) !important;
    font-family: var(--font-display) !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase;
    margin-bottom: var(--sp-3) !important;
}
section[data-testid="stSidebar"] label {
    color: var(--n-400) !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.02em;
}
section[data-testid="stSidebar"] .stTextInput input {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    color: var(--n-800) !important;
    padding: var(--sp-3) var(--sp-4) !important;
    font-size: 0.88rem !important;
    font-family: var(--font-body) !important;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: var(--gold) !important;
    box-shadow: 0 0 0 3px var(--gold-glow), var(--shadow-sm) !important;
    outline: none !important;
}
section[data-testid="stSidebar"] .stRadio > div { gap: var(--sp-2); }
section[data-testid="stSidebar"] .stRadio label {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    padding: var(--sp-4) var(--sp-5) !important;
    color: var(--n-500) !important;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    box-shadow: none !important;
    cursor: pointer !important;
}
section[data-testid="stSidebar"] .stRadio label:hover {
    border-color: var(--gold) !important;
    background: rgba(212,165,116,0.05) !important;
    color: var(--n-700) !important;
}
section[data-testid="stSidebar"] [data-baseweb="radio"] div[aria-checked="true"] + label {
    background: rgba(212,165,116,0.1) !important;
    border-color: var(--gold) !important;
    color: var(--gold) !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--surface-2) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--r-md) !important;
    color: var(--n-800) !important;
    box-shadow: none !important;
}
section[data-testid="stSidebar"] .stSlider > div > div > div { color: var(--gold) !important; }
section[data-testid="stSidebar"] hr { border-color: var(--border) !important; margin: var(--sp-5) 0 !important; }
section[data-testid="stSidebar"] .stCaption, section[data-testid="stSidebar"] small {
    color: var(--n-400) !important;
    font-size: 0.78rem !important;
}
section[data-testid="stSidebar"] button[kind="primary"] {
    background: var(--gold-gradient) !important;
    background-size: 200% 100% !important;
    border: none !important;
    border-radius: var(--r-md) !important;
    padding: var(--sp-4) var(--sp-6) !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    font-family: var(--font-body) !important;
    color: var(--bg) !important;
    letter-spacing: 0.04em;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    box-shadow: 0 4px 16px rgba(212,165,116,0.3) !important;
    cursor: pointer !important;
}
section[data-testid="stSidebar"] button[kind="primary"]:hover {
    background-position: 100% 0 !important;
    box-shadow: 0 6px 24px rgba(212,165,116,0.4) !important;
    transform: translateY(-1px);
}
section[data-testid="stSidebar"] button[kind="primary"]:active {
    transform: translateY(0);
    box-shadow: 0 2px 8px rgba(212,165,116,0.3) !important;
}

/* ==================== 组件 ==================== */

/* -- Icon -- */
.icon svg {
    display: block;
    flex-shrink: 0;
}

/* -- Hero -- */
.hero {
    text-align: center;
    padding: 72px var(--sp-8) 56px;
    margin-bottom: var(--sp-8);
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-2xl);
    box-shadow: var(--shadow-lg), var(--shadow-glow);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    animation: fadeInUp 0.8s cubic-bezier(0.23, 1, 0.32, 1) both;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background:
        radial-gradient(ellipse at 30% 20%, rgba(212,165,116,0.12) 0%, transparent 50%),
        radial-gradient(ellipse at 70% 80%, rgba(125,155,140,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(201,114,125,0.06) 0%, transparent 60%);
    animation: hero-glow 12s ease-in-out infinite alternate;
}
.hero::after {
    content: '';
    position: absolute;
    top: 0; left: -100%;
    width: 300%; height: 100%;
    background: linear-gradient(90deg, transparent 0%, rgba(212,165,116,0.06) 50%, transparent 100%);
    animation: shimmer 10s ease-in-out infinite;
}
@keyframes hero-glow {
    0%   { transform: translate(0,0) rotate(0deg); }
    100% { transform: translate(-2%,2%) rotate(0.5deg); }
}
.hero-title {
    position: relative;
    font-family: var(--font-display);
    font-size: 3.2rem;
    font-weight: 700;
    background: linear-gradient(135deg, var(--gold) 0%, #e8c9a0 30%, var(--gold) 60%, #c49462 100%);
    background-size: 200% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gold-shimmer 4s ease-in-out infinite, fadeInUp 0.8s cubic-bezier(0.23, 1, 0.32, 1) 0.1s both;
    letter-spacing: -0.02em;
    line-height: 1.15;
    margin-bottom: var(--sp-5);
}
.hero-sub {
    position: relative;
    color: var(--n-400);
    font-size: 1.05rem;
    font-weight: 400;
    line-height: var(--lh);
    letter-spacing: 0.04em;
    animation: fadeInUp 0.8s cubic-bezier(0.23, 1, 0.32, 1) 0.2s both;
}
.hero-tags {
    position: relative;
    display: flex;
    justify-content: center;
    gap: var(--sp-3);
    margin-top: var(--sp-6);
    flex-wrap: wrap;
    animation: fadeInUp 0.8s cubic-bezier(0.23, 1, 0.32, 1) 0.35s both;
}
.hero-tag {
    background: rgba(212,165,116,0.08);
    border: 1px solid rgba(212,165,116,0.2);
    color: var(--gold);
    padding: var(--sp-2) var(--sp-5);
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
    letter-spacing: 0.04em;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    cursor: pointer;
}
.hero-tag:hover {
    background: rgba(212,165,116,0.15);
    border-color: var(--gold);
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(212,165,116,0.2);
}

/* -- 指标卡片 -- */
.metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: var(--sp-4);
    margin: var(--sp-6) 0;
}
.m-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-6) var(--sp-4);
    text-align: center;
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    animation: fadeInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) both;
}
.m-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gold-gradient);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.m-card::after {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle, rgba(212,165,116,0.06) 0%, transparent 60%);
    opacity: 0;
    transition: opacity 0.4s ease;
}
.m-card.c-gold::before    { background: linear-gradient(90deg, #c9a55a, #e8d5a0); }
.m-card.c-indigo::before  { background: var(--gold-gradient); }
.m-card.c-emerald::before { background: linear-gradient(90deg, #5f8070, #7d9b8c); }
.m-card.c-rose::before    { background: linear-gradient(90deg, #c9727d, #e8a0aa); }
.m-card.c-amber::before   { background: linear-gradient(90deg, #c9a55a, #e8d5a0); }
.m-card:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md), var(--shadow-glow);
    transform: translateY(-6px);
}
.m-card:hover::before { opacity: 1; }
.m-card:hover::after { opacity: 1; }
.m-card:hover .m-val {
    background: var(--gold-gradient);
    background-size: 200% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gold-shimmer 2s ease-in-out infinite;
}
.m-icon {
    margin-bottom: var(--sp-3);
    display: flex;
    justify-content: center;
}
.m-icon .icon svg { stroke: var(--gold); }
.m-val {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 700;
    color: var(--n-800);
    letter-spacing: -0.02em;
    line-height: 1.1;
    position: relative;
    z-index: 1;
}
.m-lbl {
    font-size: 0.7rem;
    color: var(--n-400);
    font-weight: 500;
    margin-top: var(--sp-3);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    position: relative;
    z-index: 1;
}

/* -- 商品标题 -- */
.prod-title {
    font-family: var(--font-display);
    font-size: 1.4rem;
    font-weight: 600;
    color: var(--n-800);
    letter-spacing: -0.01em;
    line-height: var(--lh);
    margin-bottom: var(--sp-5);
    padding: 0 var(--sp-1);
}

/* -- Tab -- */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: 5px;
    gap: 3px;
    box-shadow: var(--shadow-sm);
    animation: fadeIn 0.5s ease-out both;
}
.stTabs [data-baseweb="tab"] {
    border-radius: var(--r-md) !important;
    padding: var(--sp-3) var(--sp-6) !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--n-400) !important;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1) !important;
    position: relative;
    letter-spacing: 0.02em;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(212,165,116,0.05) !important;
    color: var(--n-600) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(212,165,116,0.1) !important;
    color: var(--gold) !important;
    font-weight: 600 !important;
    border: 1px solid rgba(212,165,116,0.2) !important;
}
.stTabs [data-baseweb="tab-border"],
.stTabs [data-baseweb="tab-highlight"] { display: none; }

/* -- 区块标题 -- */
.sec-hd {
    font-family: var(--font-display);
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--n-800);
    letter-spacing: -0.01em;
    margin-bottom: var(--sp-6);
    display: flex;
    align-items: center;
    gap: var(--sp-3);
    line-height: var(--lh);
    padding-bottom: var(--sp-3);
    border-bottom: 1px solid var(--border);
}
.sec-hd .icon svg { stroke: var(--gold); }

/* -- 情感分布条 -- */
.sent-bar-wrap {
    display: flex;
    gap: 4px;
    margin: var(--sp-6) 0;
    border-radius: var(--r-lg);
    overflow: hidden;
    height: 48px;
    box-shadow: var(--shadow-sm);
}
.sent-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 0.82rem;
    letter-spacing: 0.04em;
    transition: flex 0.8s cubic-bezier(0.23, 1, 0.32, 1);
}
.sent-bar.pos { background: linear-gradient(135deg, #5f8070, #7d9b8c); }
.sent-bar.neu { background: linear-gradient(135deg, #c9a55a, #e8d5a0); }
.sent-bar.neg { background: linear-gradient(135deg, #c9727d, #e8a0aa); }

/* -- 标签 -- */
.tag {
    display: inline-block;
    padding: var(--sp-1) var(--sp-4);
    border-radius: 100px;
    font-size: 0.78rem;
    font-weight: 500;
    margin: var(--sp-1) var(--sp-1) var(--sp-1) 0;
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    line-height: 1.6;
    letter-spacing: 0.02em;
}
.tag:hover { transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.tag.pos { background: rgba(95,128,112,0.15); border: 1px solid rgba(95,128,112,0.3); color: #7d9b8c; }
.tag.neg { background: rgba(201,114,125,0.15); border: 1px solid rgba(201,114,125,0.3); color: #e8a0aa; }
.tag.pri-h { background: rgba(201,114,125,0.15); color: #e8a0aa; border: 1px solid rgba(201,114,125,0.3); }
.tag.pri-m { background: rgba(201,165,90,0.15); color: #e8d5a0; border: 1px solid rgba(201,165,90,0.3); }
.tag.pri-l { background: rgba(95,128,112,0.15); color: #7d9b8c; border: 1px solid rgba(95,128,112,0.3); }
.tag.gap-y { background: rgba(212,165,116,0.1); color: var(--gold); border: 1px solid rgba(212,165,116,0.25); }
.tag.gap-n { background: var(--surface-2); color: var(--n-400); border: 1px solid var(--border); }

/* -- 玻璃卡片 -- */
.glass {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-7);
    box-shadow: var(--shadow-sm);
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
}
.glass:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md), var(--shadow-glow);
}
.glass-title {
    font-family: var(--font-display);
    font-size: 0.82rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: var(--sp-4);
    line-height: var(--lh);
    display: flex;
    align-items: center;
    gap: var(--sp-2);
}

/* -- 痛点卡片 -- */
.pain-c {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-6) var(--sp-6) var(--sp-6) var(--sp-7);
    margin-bottom: var(--sp-4);
    position: relative;
    overflow: hidden;
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    animation: slideInLeft 0.5s cubic-bezier(0.23, 1, 0.32, 1) both;
}
.pain-c::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    border-radius: var(--r-xl) 0 0 var(--r-xl);
}
.pain-c.lv-h::before { background: linear-gradient(180deg, #c9727d, #e8a0aa); }
.pain-c.lv-m::before { background: linear-gradient(180deg, #c9a55a, #e8d5a0); }
.pain-c.lv-l::before { background: linear-gradient(180deg, #5f8070, #7d9b8c); }
.pain-c:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
    transform: translateX(6px);
}
.pain-c:hover .pain-hd {
    color: var(--gold);
}
.pain-hd {
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--n-800);
    margin-bottom: var(--sp-3);
    display: flex;
    align-items: center;
    gap: var(--sp-2);
    line-height: var(--lh);
}
.pain-meta {
    display: flex;
    gap: var(--sp-5);
    margin-bottom: var(--sp-4);
    font-size: 0.8rem;
    color: var(--n-400);
    line-height: var(--lh);
}
.pain-quote {
    background: var(--surface-2);
    border-left: 3px solid rgba(212,165,116,0.3);
    padding: var(--sp-4) var(--sp-5);
    border-radius: 0 var(--r-md) var(--r-md) 0;
    font-size: 0.88rem;
    color: var(--n-500);
    font-style: italic;
    line-height: 1.75;
    font-family: var(--font-display);
}

/* -- 需求行 -- */
.dem-row {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: var(--sp-5) var(--sp-6);
    margin-bottom: var(--sp-3);
    display: flex;
    align-items: center;
    gap: var(--sp-4);
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.5s cubic-bezier(0.23, 1, 0.32, 1) both;
}
.dem-row:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
    transform: translateX(6px);
}
.dem-row:hover .dem-num {
    background: var(--gold);
    color: var(--bg);
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(212,165,116,0.3);
}
.dem-num {
    width: 40px; height: 40px;
    border-radius: var(--r-md);
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--font-display);
    font-weight: 700;
    font-size: 0.9rem;
    flex-shrink: 0;
    background: rgba(212,165,116,0.1);
    color: var(--gold);
    transition: all 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}
.dem-body { flex: 1; }
.dem-name { font-weight: 600; color: var(--n-800); font-size: 0.92rem; margin-bottom: var(--sp-2); line-height: var(--lh); }
.dem-tags { display: flex; gap: var(--sp-2); align-items: center; }

/* -- 评论卡片 -- */
.rev-c {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-lg);
    padding: var(--sp-6);
    margin-bottom: var(--sp-3);
    transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.5s cubic-bezier(0.23, 1, 0.32, 1) both;
}
.rev-c:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
    transform: translateY(-3px);
}
.rev-c:hover .rev-stars {
    transform: scale(1.1);
    display: inline-block;
}
.rev-hd { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.rev-stars { color: var(--gold); font-size: 0.9rem; letter-spacing: 3px; }
.rev-ttl { font-weight: 600; color: var(--n-800); font-size: 0.95rem; line-height: var(--lh); }
.rev-meta { font-size: 0.75rem; color: var(--n-400); margin-bottom: var(--sp-3); display: flex; gap: var(--sp-4); align-items: center; }
.rev-body { font-size: 0.88rem; color: var(--n-500); line-height: 1.8; }
.rev-badge {
    display: inline-block;
    background: rgba(95,128,112,0.15);
    border: 1px solid rgba(95,128,112,0.3);
    color: #7d9b8c;
    padding: 3px var(--sp-3);
    border-radius: var(--r-sm);
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.04em;
}

/* -- 评分分布 -- */
.rbar-row { display: flex; align-items: center; gap: var(--sp-3); margin-bottom: var(--sp-3); }
.rbar-lbl { width: 24px; text-align: right; font-size: 0.85rem; color: var(--n-400); font-weight: 600; }
.rbar-track { flex: 1; height: 8px; background: var(--surface-2); border-radius: 100px; overflow: hidden; }
.rbar-fill { height: 100%; border-radius: 100px; background: var(--gold-gradient); background-size: 200% 100%; animation: gold-shimmer 3s ease-in-out infinite; transition: width 0.8s cubic-bezier(0.23, 1, 0.32, 1); }
.rbar-cnt { width: 32px; font-size: 0.8rem; color: var(--n-400); font-weight: 600; }

/* -- 功能卡片 -- */
.feat-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--sp-5);
    margin: var(--sp-8) 0;
}
.feat-c {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-8) var(--sp-5);
    text-align: center;
    transition: all 0.5s cubic-bezier(0.23, 1, 0.32, 1);
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    animation: fadeInUp 0.6s cubic-bezier(0.23, 1, 0.32, 1) both;
    position: relative;
    overflow: hidden;
}
.feat-c::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: var(--gold-gradient);
    transform: scaleX(0);
    transition: transform 0.4s ease;
}
.feat-c:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-lg), var(--shadow-glow);
    transform: translateY(-8px);
}
.feat-c:hover::before { transform: scaleX(1); }
.feat-c:hover .feat-icon .icon svg {
    stroke: var(--gold);
    transform: scale(1.15);
    transition: all 0.3s ease;
}
.feat-icon {
    margin-bottom: var(--sp-4);
    display: flex;
    justify-content: center;
}
.feat-icon .icon svg { stroke: var(--n-400); transition: all 0.3s ease; }
.feat-ttl { font-family: var(--font-display); font-weight: 600; color: var(--n-800); font-size: 0.95rem; margin-bottom: var(--sp-2); line-height: var(--lh); }
.feat-desc { font-size: 0.8rem; color: var(--n-400); line-height: 1.6; letter-spacing: 0.02em; }

/* -- 报告容器 -- */
.rpt {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-8);
    line-height: 1.9;
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    animation: fadeIn 0.6s ease-out both;
}
.rpt h1, .rpt h2, .rpt h3 {
    font-family: var(--font-display) !important;
    color: var(--n-800) !important;
    margin-top: 1.8em;
    font-weight: 600;
}
.rpt h1 { font-size: 1.5rem; }
.rpt h2 { font-size: 1.25rem; border-bottom: 1px solid var(--border); padding-bottom: var(--sp-3); }
.rpt h3 { font-size: 1.1rem; }
.rpt p, .rpt li { color: var(--n-500) !important; line-height: 1.9; }
.rpt table { width: 100%; border-collapse: collapse; margin: var(--sp-5) 0; }
.rpt th {
    background: rgba(212,165,116,0.08);
    color: var(--gold);
    padding: var(--sp-3) var(--sp-4);
    text-align: left;
    font-weight: 600;
    font-size: 0.82rem;
    border-bottom: 2px solid rgba(212,165,116,0.2);
    letter-spacing: 0.04em;
}
.rpt td {
    padding: var(--sp-3) var(--sp-4);
    color: var(--n-500);
    border-bottom: 1px solid var(--border);
    font-size: 0.88rem;
}
.rpt tr:hover td { background: rgba(212,165,116,0.03); }
.rpt strong { color: var(--n-800) !important; font-weight: 600; }
.rpt blockquote {
    border-left: 3px solid var(--gold);
    padding: var(--sp-4) var(--sp-6);
    background: rgba(212,165,116,0.05);
    border-radius: 0 var(--r-md) var(--r-md) 0;
    margin: var(--sp-5) 0;
    font-family: var(--font-display);
    font-style: italic;
}
.rpt code {
    background: rgba(212,165,116,0.08);
    color: var(--gold);
    padding: 3px 8px;
    border-radius: var(--r-sm);
    font-size: 0.84em;
    font-family: var(--font-mono);
}

/* -- 分隔线 -- */
hr {
    border: none;
    border-top: 1px solid var(--border);
    margin: var(--sp-6) 0;
}

/* -- Alert 样式 -- */
.stAlert > div {
    border-radius: var(--r-lg) !important;
    border: 1px solid var(--border) !important;
    box-shadow: var(--shadow-sm) !important;
}

/* -- 响应式 -- */
@media (max-width: 768px) {
    .hero-title { font-size: 2.2rem; }
    .hero { padding: 40px var(--sp-5) 32px; }
    .metrics { grid-template-columns: repeat(2, 1fr); }
    .feat-grid { grid-template-columns: 1fr 1fr; }
    .block-container { padding: var(--sp-4) !important; }
    .pain-c:hover { transform: none; }
    .dem-row:hover { transform: none; }
}
@media (max-width: 480px) {
    .hero-title { font-size: 1.8rem; }
    .metrics { grid-template-columns: 1fr; }
    .feat-grid { grid-template-columns: 1fr; }
    .hero-tags { gap: var(--sp-2); }
}

/* -- 图表容器 -- */
.chart-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--r-xl);
    padding: var(--sp-6);
    margin-bottom: var(--sp-4);
    box-shadow: var(--shadow-sm);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    animation: fadeIn 0.5s ease-out both;
}
.chart-container:hover {
    border-color: var(--border-hover);
    box-shadow: var(--shadow-md);
}
.chart-title {
    font-family: var(--font-display);
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--n-800);
    margin-bottom: var(--sp-5);
    display: flex;
    align-items: center;
    gap: var(--sp-3);
}
.chart-title .icon svg { stroke: var(--gold); }

/* -- 数据表格 -- */
.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
}
.data-table th {
    background: rgba(212,165,116,0.08);
    color: var(--gold);
    padding: var(--sp-3) var(--sp-4);
    text-align: left;
    font-weight: 600;
    font-size: 0.78rem;
    border-bottom: 2px solid rgba(212,165,116,0.2);
    white-space: nowrap;
    letter-spacing: 0.04em;
}
.data-table td {
    padding: var(--sp-3) var(--sp-4);
    color: var(--n-500);
    border-bottom: 1px solid var(--border);
    font-size: 0.84rem;
}
.data-table tr:hover td { background: rgba(212,165,116,0.03); }
.data-table .num { text-align: right; font-variant-numeric: tabular-nums; }

/* -- 滚动条美化 -- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--surface); }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(212,165,116,0.3), rgba(212,165,116,0.15));
    border-radius: 100px;
    border: 2px solid var(--surface);
}
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, rgba(212,165,116,0.5), rgba(212,165,116,0.3)); }

/* -- 页脚 -- */
.footer-bar {
    text-align: center;
    padding: var(--sp-8) var(--sp-4);
    margin-top: var(--sp-8);
    border-top: 1px solid var(--border);
    background: var(--surface);
}
.footer-bar span {
    font-size: 0.78rem;
    color: var(--n-400);
    letter-spacing: 0.08em;
    font-family: var(--font-display);
}
.footer-bar .heart {
    color: var(--s-400);
    display: inline-block;
    animation: float 2s ease-in-out infinite;
}

/* -- 分析状态指示器 -- */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    animation: pulse-ring 2s infinite;
}
.status-dot.active { background: var(--success); }
.status-dot.inactive { background: var(--warning); animation: none; }

/* -- 加载骨架屏 -- */
.skeleton {
    background: linear-gradient(90deg, var(--surface-2) 25%, var(--surface) 50%, var(--surface-2) 75%);
    background-size: 200% 100%;
    animation: shimmer 1.5s infinite;
    border-radius: var(--r-md);
}

/* -- 工具提示增强 -- */
.stTooltip {
    font-size: 0.82rem !important;
    border-radius: var(--r-md) !important;
    backdrop-filter: blur(12px) !important;
}

/* -- 进度条美化 -- */
.stProgress > div > div {
    background: var(--gold-gradient) !important;
    background-size: 200% 100% !important;
    animation: gold-shimmer 2s ease-in-out infinite !important;
    border-radius: 100px !important;
}

/* -- 分隔线美化 -- */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--gold), transparent);
    background-size: 200% 100%;
    animation: gold-shimmer 4s ease-in-out infinite;
    margin: var(--sp-6) 0;
    opacity: 0.3;
}

/* -- 侧边栏 logo 区域 -- */
.sidebar-brand {
    text-align: center;
    padding: var(--sp-5) 0 var(--sp-3);
    margin-bottom: var(--sp-4);
    border-bottom: 1px solid var(--border);
}
.sidebar-brand-title {
    font-family: var(--font-display);
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--n-800);
    letter-spacing: 0.02em;
}
.sidebar-brand-sub {
    font-size: 0.72rem;
    color: var(--n-400);
    margin-top: 4px;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)


# ==================== 组件函数 ====================

def render_header():
    st.markdown("""
    <div class="hero">
        <div class="hero-title">跨境电商选品分析</div>
        <div class="hero-sub">AI 驱动的智能选品工具 &mdash; 爬取评论 &middot; 深度分析 &middot; 辅助决策</div>
        <div class="hero-tags">
            <span class="hero-tag">{icon_trending} 情感分析</span>
            <span class="hero-tag">{icon_flame} 痛点提取</span>
            <span class="hero-tag">{icon_target} 需求洞察</span>
            <span class="hero-tag">{icon_file} 智能报告</span>
            <span class="hero-tag">{icon_activity} 商品数据</span>
        </div>
    </div>
    """.format(
        icon_trending=icon("trending-up", 15),
        icon_flame=icon("flame", 15),
        icon_target=icon("target", 15),
        icon_file=icon("file-text", 15),
        icon_activity=icon("activity", 15),
    ), unsafe_allow_html=True)


def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">{icon_search} 选品分析</div>
            <div class="sidebar-brand-sub">Cross-border E-commerce Analyzer</div>
        </div>
        """.format(icon_search=icon("search", 20)), unsafe_allow_html=True)
        st.markdown("### 基础配置")
        api_key = st.text_input(
            "通义千问 API Key",
            type="password",
            placeholder="选填，不填则使用内置分析",
            help="填入后将调用真实大模型进行分析",
        )

        keepa_api_key = st.text_input(
            "Keepa API Key",
            type="password",
            placeholder="选填，用于获取历史数据",
            help="注册 keepa.com 获取 API Key，免费额度每月 100 次",
        )

        st.markdown("---")
        st.markdown("### 数据来源")
        mode = st.radio("分析模式", options=["商品链接分析", "Demo 品类分析"], label_visibility="collapsed")
        url = None
        selected_id = None
        max_pages = 5

        if mode == "商品链接分析":
            url = st.text_input("亚马逊商品链接", placeholder="https://www.amazon.com/dp/B0xxxxxx", help="粘贴商品主页或评论页链接")
            max_pages = st.slider("爬取评论页数", 1, 10, 3, help="每页约 10 条，越多越全面但越慢")
        else:
            categories = get_categories()
            category_options = {f"{c['name']}（{c['name_en']}）": c['id'] for c in categories}
            selected = st.selectbox("选择品类", options=list(category_options.keys()))
            selected_id = category_options[selected]
            cat_data = get_reviews_by_category(selected_id)
            if cat_data:
                st.markdown("---")
                st.markdown("### 品类概览")
                c1, c2 = st.columns(2)
                c1.metric("评分", f"{cat_data['avg_rating']}/5.0")
                c2.metric("评论数", f"{cat_data['review_count']}条")
                st.metric("价格区间", cat_data["price_range"])

        # ---- API 状态指示 ----
        st.markdown("---")
        st.markdown("### 模式状态")
        if api_key:
            st.markdown("""
            <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:12px;">
                {icon_check}
                <div>
                    <div style="font-weight:600;color:#7d9b8c;font-size:0.88rem;">API 模式</div>
                    <div style="font-size:0.75rem;color:var(--n-400,#a8a192);margin-top:2px;">已填入 Key，将调用通义千问大模型</div>
                </div>
            </div>
            """.format(icon_check=icon("check-circle", 22)), unsafe_allow_html=True)

            # 测试 API 按钮
            if st.button("测试 API 连接", use_container_width=True):
                with st.spinner("正在测试..."):
                    try:
                        from core.llm_client import QwenClient
                        test_client = QwenClient(api_key=api_key)
                        result = test_client.chat("你好", "请回复OK两个字母", temperature=0)
                        if test_client.using_api:
                            st.success(f"API 连接成功！模型返回：{result[:50]}")
                        else:
                            st.error(f"API 调用失败：{test_client.last_error}")
                    except Exception as e:
                        st.error(f"连接异常：{e}")
        else:
            st.markdown("""
            <div style="background:rgba(201,165,90,0.1);border:1px solid rgba(201,165,90,0.25);border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:12px;">
                {icon_alert}
                <div>
                    <div style="font-weight:600;color:#c9a55a;font-size:0.88rem;">Demo 模式</div>
                    <div style="font-size:0.75rem;color:var(--n-400,#a8a192);margin-top:2px;">未填 Key，使用内置模拟数据</div>
                </div>
            </div>
            """.format(icon_alert=icon("alert-triangle", 22)), unsafe_allow_html=True)

    return mode, url if mode == "商品链接分析" else None, selected_id, api_key, keepa_api_key, max_pages


def _metrics(items):
    cards = ""
    for i, (icon, val, lbl, cls) in enumerate(items):
        delay_cls = f"anim-d{i+1}" if i < 6 else ""
        cards += f"""
        <div class="m-card {cls} {delay_cls}">
            <div class="m-icon">{icon}</div>
            <div class="m-val">{val}</div>
            <div class="m-lbl">{lbl}</div>
        </div>"""
    st.markdown(f'<div class="metrics">{cards}</div>', unsafe_allow_html=True)


def _keyword_tags(keywords, css_class):
    """渲染关键词标签，带中文翻译"""
    if not keywords:
        return '<span style="color:#94a3b8;font-size:0.85rem;">暂无数据</span>'
    tags = ""
    for kw in keywords:
        display = translate_keyword(kw)
        tags += f'<span class="tag {css_class}">{display}</span>'
    return tags


def render_sentiment(r):
    st.markdown(f'<div class="sec-hd">{icon("trending-up")} 情感分析</div>', unsafe_allow_html=True)

    pos = r.get('positive_ratio', 0)
    neu = r.get('neutral_ratio', 0)
    neg = r.get('negative_ratio', 0)

    _metrics([
        (icon("trending-up", 24), f"{pos*100:.0f}%", "正面", "c-emerald"),
        (icon("minus", 24), f"{neu*100:.0f}%", "中性", "c-amber"),
        (icon("trending-down", 24), f"{neg*100:.0f}%", "负面", "c-rose"),
    ])

    if pos + neu + neg > 0:
        st.markdown(f"""
        <div class="sent-bar-wrap">
            <div class="sent-bar pos" style="flex:{max(pos,0.01)}">正面 {pos*100:.0f}%</div>
            <div class="sent-bar neu" style="flex:{max(neu,0.01)}">中性 {neu*100:.0f}%</div>
            <div class="sent-bar neg" style="flex:{max(neg,0.01)}">负面 {neg*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**正面关键词**")
        st.markdown(_keyword_tags(r.get('positive_keywords', []), "pos"), unsafe_allow_html=True)
    with c2:
        st.markdown("**负面关键词**")
        st.markdown(_keyword_tags(r.get('negative_keywords', []), "neg"), unsafe_allow_html=True)

    summary = r.get('summary', '')
    if summary:
        st.markdown(f"""
        <div class="glass" style="margin-top:20px;">
            <div class="glass-title" style="color:var(--gold,#d4a574);">{icon("brain", 16)} 分析总结</div>
            <div style="color:var(--n-600,#5c574a);font-size:0.92rem;line-height:1.8;">{summary}</div>
        </div>
        """, unsafe_allow_html=True)


def render_pain_points(r):
    st.markdown(f'<div class="sec-hd">{icon("flame")} 核心痛点</div>', unsafe_allow_html=True)
    points = r.get('pain_points', [])
    if not points:
        st.warning("暂无痛点数据")
        return

    lv_map = {'high': ('lv-h', '高'), 'medium': ('lv-m', '中'), 'low': ('lv-l', '低')}
    for i, p in enumerate(points, 1):
        sev = p.get('severity', 'medium')
        cls, lbl = lv_map.get(sev, ('lv-m', '未知'))
        st.markdown(f"""
        <div class="pain-c {cls}">
            <div class="pain-hd">#{i} {p.get('issue', '未知问题')}</div>
            <div class="pain-meta">
                <span>严重程度：<span class="tag pri-{sev[0]}">{lbl}</span></span>
                <span>出现频次：<span style="color:#1e293b;font-weight:700;">{p.get('frequency', 0)} 次</span></span>
            </div>
            <div class="pain-quote">"{p.get('example', '无')}"</div>
        </div>
        """, unsafe_allow_html=True)

    rec = r.get('recommendation', '')
    if rec:
        st.markdown(f"""
        <div class="glass" style="margin-top:8px;">
            <div class="glass-title" style="color:#7d9b8c;">{icon("lightbulb", 16)} 改进建议</div>
            <div style="color:var(--n-600,#5c574a);font-size:0.92rem;line-height:1.8;">{rec}</div>
        </div>
        """, unsafe_allow_html=True)


def render_demands(r):
    st.markdown(f'<div class="sec-hd">{icon("clipboard-list")} 需求洞察</div>', unsafe_allow_html=True)
    dlist = r.get('demands', [])
    if not dlist:
        st.warning("暂无需求数据")
        return

    pri_cls = {'high': 'pri-h', 'medium': 'pri-m', 'low': 'pri-l'}
    pri_lbl = {'high': '高', 'medium': '中', 'low': '低'}
    for i, d in enumerate(dlist, 1):
        pri = d.get('priority', 'medium')
        gap = d.get('market_gap', False)
        st.markdown(f"""
        <div class="dem-row">
            <div class="dem-num">{i}</div>
            <div class="dem-body">
                <div class="dem-name">{d.get('demand', '未知需求')}</div>
                <div class="dem-tags">
                    <span class="tag {pri_cls.get(pri, 'pri-m')}">优先级：{pri_lbl.get(pri, '中')}</span>
                    <span class="tag {'gap-y' if gap else 'gap-n'}">{'存在缺口' if gap else '已满足'}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    unmet = r.get('unmet_needs', '')
    if unmet:
        st.markdown(f"""
        <div class="glass" style="margin-top:8px;">
            <div class="glass-title" style="color:var(--gold,#d4a574);">{icon("target", 16)} 市场机会</div>
            <div style="color:var(--n-600,#5c574a);font-size:0.92rem;line-height:1.8;">{unmet}</div>
        </div>
        """, unsafe_allow_html=True)


def render_report(report):
    st.markdown(f'<div class="sec-hd">{icon("file-text")} 选品报告</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="rpt">{report}</div>', unsafe_allow_html=True)


def render_raw_data(cat_data):
    st.markdown(f'<div class="sec-hd">{icon("bar-chart")} 原始评论数据</div>', unsafe_allow_html=True)
    reviews = cat_data.get("reviews", [])
    if not reviews:
        st.warning("暂无评论数据")
        return

    ratings = [r.get('rating', 0) for r in reviews]
    max_cnt = max([ratings.count(i) for i in range(1, 6)] + [1])

    st.markdown("**评分分布**")
    for star in range(5, 0, -1):
        cnt = ratings.count(star)
        pct = (cnt / max_cnt * 100) if max_cnt > 0 else 0
        st.markdown(f"""
        <div class="rbar-row">
            <div class="rbar-lbl">{star}★</div>
            <div class="rbar-track"><div class="rbar-fill" style="width:{pct}%"></div></div>
            <div class="rbar-cnt">{cnt}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(f'<div style="margin-top:24px;font-weight:700;color:var(--n-800,#1e293b);">评论列表（共 {len(reviews)} 条）</div>', unsafe_allow_html=True)
    for rv in reviews:
        stars = "★" * int(rv.get('rating', 0)) + "☆" * (5 - int(rv.get('rating', 0)))
        badge = f'<span class="rev-badge">{icon("shield-check", 12)} 已验证购买</span>' if rv.get('verified') else ''
        st.markdown(f"""
        <div class="rev-c">
            <div class="rev-hd">
                <span class="rev-stars">{stars}</span>
                <span class="rev-ttl">{rv.get('title', '无标题')}</span>
                {badge}
            </div>
            <div class="rev-meta">
                <span>{rv.get('date', 'N/A')}</span>
                <span>有帮助：{rv.get('helpful_votes', 0)}</span>
            </div>
            <div class="rev-body">{rv.get('content', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)


def render_product_metrics_from_url(url: str, keepa_api_key: str = ""):
    """从亚马逊 URL 获取并渲染商品数据可视化面板"""
    import plotly.graph_objects as go
    import pandas as pd

    st.markdown(f'<div class="sec-hd">{icon("activity")} 商品数据面板</div>', unsafe_allow_html=True)

    # 获取商品指标数据
    data_source = "Keepa API" if keepa_api_key else "爬虫"
    with st.spinner(f"正在通过 {data_source} 获取商品数据..."):
        metrics = fetch_and_store_product_metrics(url, keepa_api_key)

    if metrics.get("error"):
        st.error(f"获取数据失败: {metrics['error']}")
        return

    product_id = metrics.get("product_id", "")
    bsr_level = metrics.get("bsr_level", {})
    data_source = metrics.get("data_source", "scraper")

    # ---- 指标概览卡片 ----
    _metrics([
        (icon("shopping-cart", 24), format_number(metrics.get("estimated_monthly_sales", 0)), "月销量(估)", "c-indigo"),
        (icon("trending-up", 24), format_number(metrics.get("estimated_daily_sales", 0)), "日销量(估)", "c-emerald"),
        (icon("award", 24), f"#{metrics.get('bsr_rank', 0):,}", f"BSR {bsr_level.get('label', '')}", "c-gold"),
        (icon("dollar-sign", 24), f"${metrics.get('price', 0):.2f}", "当前价格", "c-amber"),
        (icon("star", 24), f"{metrics.get('avg_rating', 0):.1f}", "评分", "c-rose"),
        (icon("percent", 24), format_rate(metrics.get("review_rate", 0)), "留评率(估)", "c-indigo"),
    ])

    # 显示数据来源说明
    if data_source == "keepa":
        st.markdown(f"""
        <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;font-size:0.84rem;color:#7d9b8c;">
            {icon("check-circle", 16)} <strong>数据来源：Keepa API</strong> - 价格、BSR、评分、评论数为历史真实数据，销量为基于 BSR 的估算值。
        </div>
        """, unsafe_allow_html=True)
    elif data_source in ["playwright", "amazon_api"]:
        st.markdown(f"""
        <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;font-size:0.84rem;color:#7d9b8c;">
            {icon("check-circle", 16)} <strong>数据来源：亚马逊实时数据</strong> - 价格、BSR、评分、评论数为真实数据，销量为基于 BSR 的估算值。
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background:rgba(201,165,90,0.1);border:1px solid rgba(201,165,90,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;font-size:0.84rem;color:#c9a55a;">
            {icon("info", 16)} <strong>数据来源：亚马逊爬取</strong> - 评分和评论数为真实数据，价格和BSR为估算值。
        </div>
        """, unsafe_allow_html=True)

    # ---- 获取历史趋势数据 ----
    # 如果是 Keepa 数据，直接使用返回的历史数据；否则从本地存储获取
    if data_source == "keepa":
        bsr_trend = metrics.get("bsr_history", [])
        daily_sales = metrics.get("daily_sales_history", [])
        price_trend = metrics.get("price_history", [])
        rating_trend = metrics.get("rating_history", [])
        review_rate_trend = []
    else:
        trends = get_all_trends(product_id)
        bsr_trend = trends.get("bsr_trend", [])
        daily_sales = trends.get("daily_sales", [])
        price_trend = trends.get("price_trend", [])
        rating_trend = trends.get("rating_trend", [])
        review_rate_trend = trends.get("review_rate_trend", [])

    # ---- BSR 排名趋势 ----
    if len(bsr_trend) > 1:
        st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("award", 16)} BSR 排名趋势</div>', unsafe_allow_html=True)

        df_bsr = pd.DataFrame(bsr_trend)
        fig_bsr = go.Figure()
        fig_bsr.add_trace(go.Scatter(
            x=df_bsr['date'],
            y=df_bsr['rank'],
            mode='lines+markers',
            name='BSR 排名',
            line=dict(color='#0d9488', width=2),
            marker=dict(size=6),
            fill='tozeroy',
            fillcolor='rgba(13,148,136,0.1)'
        ))
        fig_bsr.update_layout(
            xaxis_title='日期',
            yaxis_title='BSR 排名',
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)', autorange='reversed'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_bsr, use_container_width=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 销量趋势 ----
    if len(daily_sales) > 1:
        st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("trending-up", 16)} 日销量趋势（估算）</div>', unsafe_allow_html=True)

        df_daily = pd.DataFrame(daily_sales)
        fig_daily = go.Figure()
        fig_daily.add_trace(go.Scatter(
            x=df_daily['date'],
            y=df_daily['sales'],
            mode='lines+markers',
            name='日销量',
            line=dict(color='#6366f1', width=2),
            marker=dict(size=5),
            fill='tozeroy',
            fillcolor='rgba(99,102,241,0.1)'
        ))
        fig_daily.update_layout(
            xaxis_title='日期',
            yaxis_title='销量（件）',
            height=350,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_daily, use_container_width=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 价格 + 评分 + 留评率趋势（三列布局）----
    if len(price_trend) > 1 or len(rating_trend) > 1 or len(review_rate_trend) > 1:
        col1, col2, col3 = st.columns(3)

        with col1:
            if len(price_trend) > 1:
                st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("dollar-sign", 16)} 价格趋势</div>', unsafe_allow_html=True)

                df_price = pd.DataFrame(price_trend)
                fig_price = go.Figure()
                fig_price.add_trace(go.Scatter(
                    x=df_price['date'],
                    y=df_price['price'],
                    mode='lines+markers',
                    name='价格',
                    line=dict(color='#f59e0b', width=2),
                    marker=dict(size=5)
                ))
                fig_price.update_layout(
                    xaxis_title='日期',
                    yaxis_title='价格 ($)',
                    height=300,
                    margin=dict(l=20, r=20, t=10, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                    yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_price, use_container_width=True)

                # 显示价格统计（如果有 CamelCamelCamel 数据）
                price_stats = metrics.get("price_stats", {})
                if price_stats:
                    st.markdown(f"""
                    <div style="background:var(--surface-2,#1a1f45);border:1px solid var(--border,rgba(212,165,116,0.15));border-radius:var(--r-md,10px);padding:14px 18px;margin-top:12px;font-size:0.8rem;">
                        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                            <span style="color:var(--n-400,#a8a192);">历史最低</span>
                            <span style="color:#7d9b8c;font-weight:600;">${price_stats.get('lowest', 0):.2f}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                            <span style="color:var(--n-400,#a8a192);">历史最高</span>
                            <span style="color:#e8a0aa;font-weight:600;">${price_stats.get('highest', 0):.2f}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:6px;">
                            <span style="color:var(--n-400,#a8a192);">平均价格</span>
                            <span style="color:var(--n-600,#5c574a);font-weight:600;">${price_stats.get('average', 0):.2f}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;">
                            <span style="color:var(--n-400,#a8a192);">当前价格</span>
                            <span style="color:var(--n-700,#3d3a33);font-weight:600;">${price_stats.get('current', 0):.2f}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if price_stats.get("is_good_deal"):
                        st.markdown(f"""
                        <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:var(--r-md,10px);padding:10px 16px;margin-top:12px;font-size:0.8rem;color:#7d9b8c;">
                            {icon("check-circle", 15)} <strong>好价!</strong> 当前价格低于历史平均价 10% 以上
                        </div>
                        """, unsafe_allow_html=True)
                    elif price_stats.get("is_at_lowest"):
                        st.markdown(f"""
                        <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:var(--r-md,10px);padding:10px 16px;margin-top:12px;font-size:0.8rem;color:#7d9b8c;">
                            {icon("check-circle", 15)} <strong>历史最低价!</strong>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

        with col2:
            if len(rating_trend) > 1:
                st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("star", 16)} 评分趋势</div>', unsafe_allow_html=True)

                df_rating = pd.DataFrame(rating_trend)
                fig_rating = go.Figure()
                fig_rating.add_trace(go.Scatter(
                    x=df_rating['date'],
                    y=df_rating['rating'],
                    mode='lines+markers',
                    name='评分',
                    line=dict(color='#e11d48', width=2),
                    marker=dict(size=6)
                ))
                fig_rating.update_layout(
                    xaxis_title='日期',
                    yaxis_title='评分',
                    height=300,
                    margin=dict(l=20, r=20, t=10, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                    yaxis=dict(gridcolor='rgba(0,0,0,0.05)', range=[2.5, 5.0]),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_rating, use_container_width=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

        with col3:
            if len(review_rate_trend) > 1:
                st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("percent", 16)} 留评率趋势</div>', unsafe_allow_html=True)

                df_rate = pd.DataFrame(review_rate_trend)
                fig_rate = go.Figure()
                fig_rate.add_trace(go.Scatter(
                    x=df_rate['date'],
                    y=[r * 100 for r in df_rate['rate']],
                    mode='lines+markers',
                    name='留评率',
                    line=dict(color='#8b5cf6', width=2),
                    marker=dict(size=6),
                    fill='tozeroy',
                    fillcolor='rgba(139,92,246,0.1)'
                ))
                fig_rate.update_layout(
                    xaxis_title='日期',
                    yaxis_title='留评率 (%)',
                    height=300,
                    margin=dict(l=20, r=20, t=10, b=20),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                    yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
                    hovermode='x unified'
                )
                st.plotly_chart(fig_rate, use_container_width=True)

                st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 历史数据明细表 ----
    if len(bsr_trend) > 1:
        st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("database", 16)} 历史数据明细</div>', unsafe_allow_html=True)

        # 构建完整的历史数据表格
        history_data = []
        for i, bsr in enumerate(bsr_trend):
            row = {"日期": bsr["date"], "BSR": bsr["rank"]}
            if i < len(daily_sales):
                row["日销量(估)"] = daily_sales[i]["sales"]
            if i < len(price_trend):
                row["价格"] = f"${price_trend[i]['price']:.2f}"
            if i < len(rating_trend):
                row["评分"] = f"{rating_trend[i]['rating']:.1f}"
            if i < len(review_rate_trend):
                row["留评率"] = f"{review_rate_trend[i]['rate']*100:.1f}%"
            history_data.append(row)

        if history_data:
            # 构建表格 HTML
            headers = list(history_data[0].keys())
            table_html = '<table class="data-table"><thead><tr>'
            for h in headers:
                align = 'class="num"' if h != '日期' else ''
                table_html += f'<th {align}>{h}</th>'
            table_html += '</tr></thead><tbody>'

            for row in history_data:
                table_html += '<tr>'
                for h in headers:
                    align = 'class="num"' if h != '日期' else ''
                    table_html += f'<td {align}>{row[h]}</td>'
                table_html += '</tr>'
            table_html += '</tbody></table>'
            st.markdown(table_html, unsafe_allow_html=True)

        st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 无历史数据提示 ----
    if len(bsr_trend) <= 1:
        st.markdown(f"""
        <div class="glass" style="margin-top:16px;">
            <div class="glass-title" style="color:var(--gold,#d4a574);">{icon("info", 16)} 趋势数据说明</div>
            <div style="color:var(--n-600,#5c574a);font-size:0.92rem;line-height:1.8;">
                当前为首次分析该商品，仅显示当前数据点。<br>
                趋势图表将在多次分析同一商品后自动显示，帮助您追踪 BSR、价格、评分等指标的变化趋势。<br>
                <strong>建议</strong>：每天或每周分析一次同一商品，积累数据以获得更准确的趋势分析。
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_demo_product_metrics(selected_id: str):
    """Demo 模式下的商品数据面板（模拟数据）"""
    import plotly.graph_objects as go
    import pandas as pd
    from datetime import datetime, timedelta

    st.markdown(f'<div class="sec-hd">{icon("activity")} 商品数据面板</div>', unsafe_allow_html=True)

    # ---- 品类专属模拟数据 ----
    DEMO_METRICS = {
        "wireless_earbuds": {
            "monthly_sales": 3200, "daily_sales": 107, "bsr_rank": 1856,
            "price": 28.99, "avg_rating": 3.8, "review_rate": 0.032,
            "bsr_label": "Electronics > Earbuds",
            "trend_base_bsr": 2200, "trend_base_price": 29.99,
            "trend_base_rating": 3.7, "trend_base_sales": 90,
        },
        "portable_blender": {
            "monthly_sales": 1800, "daily_sales": 60, "bsr_rank": 3421,
            "price": 32.99, "avg_rating": 3.5, "review_rate": 0.028,
            "bsr_label": "Home & Kitchen > Blenders",
            "trend_base_bsr": 4000, "trend_base_price": 34.99,
            "trend_base_rating": 3.4, "trend_base_sales": 45,
        },
        "led_strip_lights": {
            "monthly_sales": 5600, "daily_sales": 187, "bsr_rank": 876,
            "price": 15.99, "avg_rating": 4.2, "review_rate": 0.041,
            "bsr_label": "Home & Kitchen > Lighting",
            "trend_base_bsr": 1100, "trend_base_price": 17.99,
            "trend_base_rating": 4.1, "trend_base_sales": 150,
        },
        "yoga_mat": {
            "monthly_sales": 2400, "daily_sales": 80, "bsr_rank": 2134,
            "price": 24.99, "avg_rating": 4.0, "review_rate": 0.035,
            "bsr_label": "Sports & Outdoors > Yoga",
            "trend_base_bsr": 2500, "trend_base_price": 26.99,
            "trend_base_rating": 3.9, "trend_base_sales": 65,
        },
        "phone_stand": {
            "monthly_sales": 4100, "daily_sales": 137, "bsr_rank": 1245,
            "price": 12.99, "avg_rating": 4.3, "review_rate": 0.038,
            "bsr_label": "Electronics > Accessories",
            "trend_base_bsr": 1500, "trend_base_price": 14.99,
            "trend_base_rating": 4.2, "trend_base_sales": 110,
        },
    }

    m = DEMO_METRICS.get(selected_id, DEMO_METRICS["wireless_earbuds"])

    # ---- 指标概览卡片 ----
    _metrics([
        (icon("shopping-cart", 24), format_number(m["monthly_sales"]), "月销量(估)", "c-indigo"),
        (icon("trending-up", 24), format_number(m["daily_sales"]), "日销量(估)", "c-emerald"),
        (icon("award", 24), f"#{m['bsr_rank']:,}", m["bsr_label"].split(" > ")[-1], "c-gold"),
        (icon("dollar-sign", 24), f"${m['price']:.2f}", "当前价格", "c-amber"),
        (icon("star", 24), f"{m['avg_rating']:.1f}", "评分", "c-rose"),
        (icon("percent", 24), format_rate(m["review_rate"]), "留评率(估)", "c-indigo"),
    ])

    st.markdown(f"""
    <div style="background:rgba(201,165,90,0.1);border:1px solid rgba(201,165,90,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;font-size:0.84rem;color:#c9a55a;">
        {icon("info", 16)} <strong>数据来源：Demo 模拟数据</strong> - 以下数据为基于品类特征生成的模拟趋势，仅供展示效果。
    </div>
    """, unsafe_allow_html=True)

    # ---- 生成30天模拟趋势数据 ----
    import random
    random.seed(hash(selected_id))  # 同品类每次生成相同数据
    today = datetime(2025, 1, 15)
    dates = [(today - timedelta(days=29 - i)).strftime("%Y-%m-%d") for i in range(30)]

    bsr_trend = []
    daily_sales = []
    price_trend = []
    rating_trend = []

    for i, d in enumerate(dates):
        noise = random.uniform(-0.15, 0.15)
        progress = i / 29.0

        # BSR 逐渐改善（下降）
        bsr = int(m["trend_base_bsr"] * (1 - progress * 0.3 + noise * 0.5))
        bsr_trend.append({"date": d, "rank": max(100, bsr)})

        # 销量逐渐上升
        sales = int(m["trend_base_sales"] * (1 + progress * 0.4 + noise * 0.3))
        daily_sales.append({"date": d, "sales": max(10, sales)})

        # 价格小幅波动
        price = round(m["trend_base_price"] + random.uniform(-2, 1), 2)
        price_trend.append({"date": d, "price": max(5, price)})

        # 评分缓慢上升
        rating = round(min(5.0, m["trend_base_rating"] + progress * 0.15 + noise * 0.05), 1)
        rating_trend.append({"date": d, "rating": max(1.0, rating)})

    # ---- BSR 排名趋势 ----
    st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("award", 16)} BSR 排名趋势</div>', unsafe_allow_html=True)
    df_bsr = pd.DataFrame(bsr_trend)
    fig_bsr = go.Figure()
    fig_bsr.add_trace(go.Scatter(
        x=df_bsr['date'], y=df_bsr['rank'], mode='lines+markers', name='BSR 排名',
        line=dict(color='#0d9488', width=2), marker=dict(size=5),
        fill='tozeroy', fillcolor='rgba(13,148,136,0.1)'
    ))
    fig_bsr.update_layout(
        xaxis_title='日期', yaxis_title='BSR 排名', height=350,
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)', autorange='reversed'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_bsr, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 销量趋势 ----
    st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("trending-up", 16)} 日销量趋势（估算）</div>', unsafe_allow_html=True)
    df_daily = pd.DataFrame(daily_sales)
    fig_daily = go.Figure()
    fig_daily.add_trace(go.Scatter(
        x=df_daily['date'], y=df_daily['sales'], mode='lines+markers', name='日销量',
        line=dict(color='#6366f1', width=2), marker=dict(size=5),
        fill='tozeroy', fillcolor='rgba(99,102,241,0.1)'
    ))
    fig_daily.update_layout(
        xaxis_title='日期', yaxis_title='销量（件）', height=350,
        margin=dict(l=20, r=20, t=10, b=20),
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
        hovermode='x unified'
    )
    st.plotly_chart(fig_daily, use_container_width=True)
    st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 价格 + 评分趋势（两列）----
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("dollar-sign", 16)} 价格趋势</div>', unsafe_allow_html=True)
        df_price = pd.DataFrame(price_trend)
        fig_price = go.Figure()
        fig_price.add_trace(go.Scatter(
            x=df_price['date'], y=df_price['price'], mode='lines+markers', name='价格',
            line=dict(color='#f59e0b', width=2), marker=dict(size=5)
        ))
        fig_price.update_layout(
            xaxis_title='日期', yaxis_title='价格 ($)', height=300,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            hovermode='x unified'
        )
        st.plotly_chart(fig_price, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("star", 16)} 评分趋势</div>', unsafe_allow_html=True)
        df_rating = pd.DataFrame(rating_trend)
        fig_rating = go.Figure()
        fig_rating.add_trace(go.Scatter(
            x=df_rating['date'], y=df_rating['rating'], mode='lines+markers', name='评分',
            line=dict(color='#e11d48', width=2), marker=dict(size=6)
        ))
        fig_rating.update_layout(
            xaxis_title='日期', yaxis_title='评分', height=300,
            margin=dict(l=20, r=20, t=10, b=20),
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(gridcolor='rgba(0,0,0,0.05)'),
            yaxis=dict(gridcolor='rgba(0,0,0,0.05)', range=[2.5, 5.0]),
            hovermode='x unified'
        )
        st.plotly_chart(fig_rating, use_container_width=True)
        st.markdown('</div></div>', unsafe_allow_html=True)

    # ---- 历史数据明细表 ----
    st.markdown(f'<div class="chart-container"><div class="chart-title">{icon("database", 16)} 历史数据明细</div>', unsafe_allow_html=True)
    history_data = []
    for i, bsr in enumerate(bsr_trend):
        row = {"日期": bsr["date"], "BSR": bsr["rank"]}
        if i < len(daily_sales):
            row["日销量(估)"] = daily_sales[i]["sales"]
        if i < len(price_trend):
            row["价格"] = f"${price_trend[i]['price']:.2f}"
        if i < len(rating_trend):
            row["评分"] = f"{rating_trend[i]['rating']:.1f}"
        history_data.append(row)

    headers = list(history_data[0].keys())
    table_html = '<table class="data-table"><thead><tr>'
    for h in headers:
        align = 'class="num"' if h != '日期' else ''
        table_html += f'<th {align}>{h}</th>'
    table_html += '</tr></thead><tbody>'
    for row in history_data:
        table_html += '<tr>'
        for h in headers:
            align = 'class="num"' if h != '日期' else ''
            table_html += f'<td {align}>{row[h]}</td>'
        table_html += '</tr>'
    table_html += '</tbody></table>'
    st.markdown(table_html, unsafe_allow_html=True)
    st.markdown('</div></div>', unsafe_allow_html=True)


def render_welcome(mode):
    if mode == "url":
        items = [
            ("link", "粘贴链接", "粘贴亚马逊商品链接即可开始"),
            ("spider", "自动爬取", "自动抓取商品页面的用户评论"),
            ("brain", "AI 分析", "情感分析 · 痛点提取 · 需求洞察"),
            ("file-text", "智能报告", "一键生成结构化选品分析报告"),
        ]
    else:
        items = [
            ("package", "选择品类", "从预设品类中选择分析目标"),
            ("database", "示例数据", "内置评论数据，无需网络"),
            ("brain", "完整流程", "体验完整的分析流程"),
            ("file-text", "生成报告", "查看完整的选品分析报告"),
        ]

    cards = ""
    for i, (icon_name, ttl, desc) in enumerate(items):
        delay_cls = f"anim-d{i+1}"
        cards += f"""
        <div class="feat-c {delay_cls}">
            <div class="feat-icon">{icon(icon_name, 32)}</div>
            <div class="feat-ttl">{ttl}</div>
            <div class="feat-desc">{desc}</div>
        </div>"""

    st.markdown(f"""
    <div style="text-align:center;padding:24px 0 8px;" class="anim-fade-up">
        <div style="font-family:var(--font-display,'Playfair Display',Georgia,serif);font-size:1.5rem;font-weight:600;color:var(--n-800,#1f1d1a);letter-spacing:-0.01em;">开始使用</div>
        <div style="color:var(--n-400,#a8a192);margin-top:10px;font-size:0.92rem;letter-spacing:0.04em;">粘贴商品链接或使用示例数据体验</div>
    </div>
    <div class="feat-grid">{cards}</div>
    """, unsafe_allow_html=True)


# ==================== 主函数 ====================

def _render_api_status(using_api=False, last_error=''):
    """分析完成后显示实际 API 使用状态"""

    if using_api:
        st.markdown("""
        <div style="background:rgba(95,128,112,0.1);border:1px solid rgba(95,128,112,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;backdrop-filter:blur(12px);">
            {icon_check}
            <div>
                <div style="font-weight:600;color:#7d9b8c;font-size:0.88rem;">本次分析使用了通义千问 API</div>
                <div style="font-size:0.75rem;color:var(--n-400,#a8a192);margin-top:2px;">分析结果由大语言模型实时生成</div>
            </div>
        </div>
        """.format(icon_check=icon("check-circle", 22)), unsafe_allow_html=True)
    else:
        reason = f"（{last_error}）" if last_error else ""
        st.markdown(f"""
        <div style="background:rgba(201,165,90,0.1);border:1px solid rgba(201,165,90,0.25);border-radius:var(--r-md,10px);padding:14px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;backdrop-filter:blur(12px);">
            {icon("alert-triangle", 22)}
            <div>
                <div style="font-weight:600;color:#c9a55a;font-size:0.88rem;">本次分析使用了内置模拟数据 {reason}</div>
                <div style="font-size:0.75rem;color:var(--n-400,#a8a192);margin-top:2px;">填入有效的 API Key 可获得大模型实时分析结果</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def main():
    render_header()
    mode, url, selected_id, api_key, keepa_api_key, max_pages = render_sidebar()

    # 使用 Agent 架构 - OrchestratorAgent 统一调度
    llm_client = QwenClient(api_key=api_key) if api_key else get_client()
    data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
    orchestrator = OrchestratorAgent(llm_client=llm_client, data_dir=data_dir)

    st.sidebar.markdown("---")
    btn = st.sidebar.button("开始分析", type="primary", use_container_width=True)

    # ===== URL 模式 =====
    if mode == "商品链接分析":
        if btn:
            if not url:
                st.error("请输入亚马逊商品链接")
            else:
                with st.spinner("正在爬取评论并分析，请稍候（约 20~30 秒）..."):
                    result = orchestrator.analyze_from_url(url, max_pages=max_pages)
                    st.session_state['url_result'] = result
                    st.session_state['api_status'] = {
                        'using_api': getattr(llm_client, 'using_api', False),
                        'last_error': getattr(llm_client, 'last_error', ''),
                    }

        if 'url_result' in st.session_state:
            result = st.session_state['url_result']
            if result.get("error"):
                st.error(result['error'])

            info = result.get("product_info", {})
            st.markdown(f'<div class="prod-title">{info.get("name", "未知商品")}</div>', unsafe_allow_html=True)

            _metrics([
                (icon("star", 24), f"{info.get('avg_rating', 0)}", "平均评分", "c-gold"),
                (icon("message-circle", 24), f"{info.get('review_count', 0):,}", "评论总数", "c-indigo"),
                (icon("dollar-sign", 24), info.get('price_range', 'N/A'), "价格", "c-emerald"),
            ])

            if result.get("sentiment"):
                api_status = st.session_state.get('api_status', {})
                _render_api_status(
                    using_api=api_status.get('using_api', False),
                    last_error=api_status.get('last_error', '')
                )

                t1, t2, t3, t4, t5, t6 = st.tabs(["情感分析", "痛点提取", "需求洞察", "选品报告", "原始数据", "商品数据"])
                with t1: render_sentiment(result["sentiment"])
                with t2: render_pain_points(result["pain_points"])
                with t3: render_demands(result["demands"])
                with t4:
                    if st.button("生成完整报告"):
                        with st.spinner("报告生成中..."):
                            report = orchestrator.generate_report({
                                "category_data": info,
                                "sentiment": result["sentiment"],
                                "pain_points": result["pain_points"],
                                "demands": result["demands"],
                            })
                            st.session_state['url_report'] = report
                    if 'url_report' in st.session_state:
                        render_report(st.session_state['url_report'])
                with t5:
                    render_raw_data(info)
                with t6:
                    render_product_metrics_from_url(url, keepa_api_key)
        else:
            render_welcome("url")

    # ===== Demo 模式 =====
    else:
        if btn:
            with st.spinner("分析中..."):
                demo_result = orchestrator.analyze_demo(selected_id)
                st.session_state['sentiment'] = demo_result.get("sentiment", {})
                st.session_state['pain_points'] = demo_result.get("pain_points", {})
                st.session_state['demands'] = demo_result.get("demands", {})
                st.session_state['analyzed'] = True
                st.session_state['api_status'] = {
                    'using_api': getattr(llm_client, 'using_api', False),
                    'last_error': getattr(llm_client, 'last_error', ''),
                }

        if st.session_state.get('analyzed'):
            api_status = st.session_state.get('api_status', {})
            _render_api_status(
                using_api=api_status.get('using_api', False),
                last_error=api_status.get('last_error', '')
            )

            t1, t2, t3, t4, t5, t6 = st.tabs(["情感分析", "痛点提取", "需求洞察", "选品报告", "原始数据", "商品数据"])
            with t1: render_sentiment(st.session_state['sentiment'])
            with t2: render_pain_points(st.session_state['pain_points'])
            with t3: render_demands(st.session_state['demands'])
            with t4:
                if st.button("生成完整报告"):
                    with st.spinner("报告生成中..."):
                        cat_data = get_reviews_by_category(selected_id)
                        st.session_state['report'] = orchestrator.generate_report({
                            "category_data": cat_data,
                            "sentiment": st.session_state['sentiment'],
                            "pain_points": st.session_state['pain_points'],
                            "demands": st.session_state['demands'],
                        })
                if 'report' in st.session_state:
                    render_report(st.session_state['report'])
            with t5:
                cat_data = get_reviews_by_category(selected_id)
                if cat_data:
                    render_raw_data(cat_data)
            with t6:
                render_demo_product_metrics(selected_id)
        else:
            render_welcome("demo")

    # ---- 页脚 ----
    render_footer()


def render_footer():
    st.markdown("""
    <div class="footer-bar">
        <span>Crafted with <span class="heart">♥</span> by AI Product Analyzer &middot; 跨境电商选品分析助手 v1.0</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
