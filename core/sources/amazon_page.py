"""
亚马逊页面解析工具函数
供各 Agent 共享使用
"""
import re
from typing import Optional


def extract_asin(url: str) -> Optional[str]:
    """从亚马逊 URL 中提取 ASIN"""
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/gp/product/([A-Z0-9]{10})',
        r'/ASIN/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def get_base_url(url: str) -> str:
    """提取域名基础 URL"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def detect_amazon_domain(url: str) -> str:
    """检测亚马逊域名"""
    url_lower = url.lower()
    domains = [
        "amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
        "amazon.co.jp", "amazon.ca", "amazon.it", "amazon.es",
        "amazon.in", "amazon.com.mx",
    ]
    for domain in domains:
        if domain in url_lower:
            return domain
    return "amazon.com"
