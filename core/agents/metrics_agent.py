"""
指标采集 Agent
负责采集商品的 BSR、价格、评分等指标数据
整合 Keepa / CamelCamelCamel / 爬虫等多数据源
"""
import re
import time
import random
from typing import Any, Dict, List, Optional

import requests

from .base_agent import BaseAgent


# ---- 数据源 Agent ----

class KeepaSourceAgent(BaseAgent):
    """Keepa API 数据源 Agent"""

    KEEPA_API_BASE = "https://api.keepa.com"
    DOMAIN_MAP = {
        "amazon.com": 1, "amazon.co.uk": 2, "amazon.de": 3,
        "amazon.fr": 4, "amazon.co.jp": 5, "amazon.ca": 6,
        "amazon.it": 8, "amazon.es": 9, "amazon.in": 10, "amazon.com.mx": 11,
    }

    def __init__(self, llm_client=None):
        super().__init__(name="KeepaSourceAgent", llm_client=llm_client)

    def execute(self, input_data: Any, context: Dict = None) -> Dict:
        asin = input_data.get("asin", "")
        api_key = input_data.get("api_key", "")
        domain = input_data.get("domain", "amazon.com")

        if not api_key:
            return {"error": "未配置 Keepa API Key"}

        domain_id = self.DOMAIN_MAP.get(domain, 1)
        url = f"{self.KEEPA_API_BASE}/product"
        params = {
            "key": api_key, "domain": domain_id, "asin": asin,
            "stats": 180, "history": 1, "offers": 0,
        }

        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 429:
                return {"error": "Keepa API 请求频率限制"}
            if resp.status_code != 200:
                return {"error": f"Keepa API 返回 HTTP {resp.status_code}"}

            data = resp.json()
            if "products" not in data or not data["products"]:
                return {"error": f"未找到商品 {asin} 的数据"}

            product = data["products"][0]
            csv = product.get("csv", [])

            price_history = self._parse_price_history(csv[0] if len(csv) > 0 else [], 90)
            bsr_history = self._parse_bsr_history(csv[3] if len(csv) > 3 else [], 90)
            rating_history = self._parse_rating_history(csv[5] if len(csv) > 5 else [], 180)
            review_history = self._parse_review_count_history(csv[6] if len(csv) > 6 else [], 180)

            current_price = price_history[-1]["price"] if price_history else 0
            current_bsr = bsr_history[-1]["rank"] if bsr_history else 0
            current_rating = rating_history[-1]["rating"] if rating_history else 0
            current_review_count = review_history[-1]["review_count"] if review_history else 0

            stats = product.get("stats", {})
            estimated_monthly_sales = 0
            if stats:
                ems = stats.get("estimatedMonthlySales", [0, 0, 0])
                estimated_monthly_sales = ems[0] if isinstance(ems, list) and ems else 0

            return {
                "asin": asin, "title": product.get("title", "未知商品"),
                "current_price": current_price, "current_bsr": current_bsr,
                "current_rating": current_rating, "current_review_count": current_review_count,
                "estimated_monthly_sales": estimated_monthly_sales,
                "price_history": price_history, "bsr_history": bsr_history,
                "rating_history": rating_history, "review_count_history": review_history,
                "data_source": "keepa", "error": None,
            }
        except requests.exceptions.Timeout:
            return {"error": "Keepa API 请求超时"}
        except Exception as e:
            return {"error": f"Keepa API 请求失败: {str(e)}"}

    def _keepa_timestamp_to_datetime(self, ts):
        from datetime import datetime, timezone
        if ts <= 0 or ts == -1:
            return None
        unix_ts = ts * 60 + 1356998400
        return datetime.fromtimestamp(unix_ts, tz=timezone.utc)

    def _parse_price_history(self, csv_data, days=90):
        from datetime import datetime, timedelta
        if not csv_data or len(csv_data) < 2: return []
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = []
        for i in range(0, len(csv_data) - 1, 2):
            ts, price_cents = csv_data[i], csv_data[i + 1]
            if ts <= 0 or price_cents <= 0 or price_cents == -1: continue
            dt = self._keepa_timestamp_to_datetime(ts)
            if dt is None or dt < cutoff: continue
            result.append({"date": dt.strftime("%Y-%m-%d"), "price": round(price_cents / 100, 2)})
        return result

    def _parse_bsr_history(self, csv_data, days=90):
        from datetime import datetime, timedelta
        if not csv_data or len(csv_data) < 2: return []
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = []
        for i in range(0, len(csv_data) - 1, 2):
            ts, rank = csv_data[i], csv_data[i + 1]
            if ts <= 0 or rank <= 0 or rank == -1: continue
            dt = self._keepa_timestamp_to_datetime(ts)
            if dt is None or dt < cutoff: continue
            result.append({"date": dt.strftime("%Y-%m-%d"), "rank": rank})
        return result

    def _parse_rating_history(self, csv_data, days=180):
        from datetime import datetime, timedelta
        if not csv_data or len(csv_data) < 2: return []
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = []
        for i in range(0, len(csv_data) - 1, 2):
            ts, rating_x10 = csv_data[i], csv_data[i + 1]
            if ts <= 0 or rating_x10 <= 0 or rating_x10 == -1: continue
            dt = self._keepa_timestamp_to_datetime(ts)
            if dt is None or dt < cutoff: continue
            result.append({"date": dt.strftime("%Y-%m-%d"), "rating": round(rating_x10 / 10, 1)})
        return result

    def _parse_review_count_history(self, csv_data, days=180):
        from datetime import datetime, timedelta
        if not csv_data or len(csv_data) < 2: return []
        cutoff = datetime.utcnow() - timedelta(days=days)
        result = []
        for i in range(0, len(csv_data) - 1, 2):
            ts, count = csv_data[i], csv_data[i + 1]
            if ts <= 0 or count < 0 or count == -1: continue
            dt = self._keepa_timestamp_to_datetime(ts)
            if dt is None or dt < cutoff: continue
            result.append({"date": dt.strftime("%Y-%m-%d"), "review_count": count})
        return result


class CamelSourceAgent(BaseAgent):
    """CamelCamelCamel 数据源 Agent"""

    CAMEL_DOMAINS = {
        "amazon.com": "camelcamelcamel.com",
        "amazon.co.uk": "uk.camelcamelcamel.com",
        "amazon.de": "de.camelcamelcamel.com",
        "amazon.fr": "fr.camelcamelcamel.com",
        "amazon.co.jp": "jp.camelcamelcamel.com",
        "amazon.ca": "ca.camelcamelcamel.com",
    }

    def __init__(self, llm_client=None):
        super().__init__(name="CamelSourceAgent", llm_client=llm_client)

    def execute(self, input_data: Any, context: Dict = None) -> Dict:
        asin = input_data.get("asin", "")
        amazon_url = input_data.get("amazon_url", "")
        days = input_data.get("days", 90)

        if not asin:
            return {"error": "未提供 ASIN"}

        camel_domain = "camelcamelcamel.com"
        url_lower = amazon_url.lower()
        for amazon_d, camel_d in self.CAMEL_DOMAINS.items():
            if amazon_d in url_lower:
                camel_domain = camel_d
                break

        camel_url = f"https://{camel_domain}/product/{asin}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }

        try:
            from bs4 import BeautifulSoup
            resp = requests.get(camel_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                return {"error": f"CamelCamelCamel 返回 HTTP {resp.status_code}"}

            html = resp.text
            soup = BeautifulSoup(html, "lxml")

            title = ""
            title_el = soup.select_one("h2.title, .product-title, h1")
            if title_el:
                title = title_el.get_text(strip=True)

            price_history = self._extract_chart_data(html, days)
            amazon_prices = [p["amazon"] for p in price_history if p.get("amazon", 0) > 0]

            return {
                "asin": asin, "title": title, "data_source": "camel",
                "price_history": price_history,
                "lowest_price": round(min(amazon_prices), 2) if amazon_prices else 0,
                "highest_price": round(max(amazon_prices), 2) if amazon_prices else 0,
                "average_price": round(sum(amazon_prices) / len(amazon_prices), 2) if amazon_prices else 0,
                "error": None,
            }
        except Exception as e:
            return {"error": f"CamelCamelCamel 请求失败: {str(e)}"}

    def _extract_chart_data(self, html, days=90):
        import json
        price_history = []
        for pattern in [r'var\s+chartData\s*=\s*({.*?});', r'"prices"\s*:\s*(\[{.*?}\])']:
            matches = re.findall(pattern, html, re.DOTALL)
            for match in matches:
                try:
                    data = json.loads(match)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                date = item.get("date", item.get("timestamp", ""))
                                price = item.get("price", item.get("amazon", 0))
                                if date and price:
                                    price_history.append({"date": str(date)[:10], "amazon": float(price)})
                        if price_history:
                            return price_history[-days:]
                except (json.JSONDecodeError, ValueError, KeyError):
                    continue

        google_patterns = [r"addRows\(\[([\s\S]*?)\]\)"]
        for pattern in google_patterns:
            match = re.search(pattern, html)
            if match:
                row_pattern = r'new\s+Date\((\d+),(\d+),(\d+)\),\s*([\d.]+)'
                rows = re.findall(row_pattern, match.group(1))
                for year, month, day, price in rows:
                    try:
                        price_history.append({
                            "date": f"{year}-{int(month)+1:02d}-{int(day):02d}",
                            "amazon": float(price),
                        })
                    except (ValueError, TypeError):
                        continue
                if price_history:
                    return price_history[-days:]
        return []


# ---- 销量估算 ----

class SalesEstimator:
    """基于 BSR 的销量估算器"""

    @staticmethod
    def estimate_daily_sales(bsr_rank: int, category: str = "") -> int:
        if bsr_rank <= 0: return 0
        if bsr_rank <= 100: base, exponent = 5000, 0.45
        elif bsr_rank <= 500: base, exponent = 1500, 0.50
        elif bsr_rank <= 2000: base, exponent = 800, 0.55
        elif bsr_rank <= 10000: base, exponent = 400, 0.60
        elif bsr_rank <= 50000: base, exponent = 150, 0.65
        else: base, exponent = 50, 0.70

        multiplier = SalesEstimator._get_category_multiplier(category)
        estimated = base * (bsr_rank ** (-exponent)) * multiplier
        return max(1, int(estimated))

    @staticmethod
    def estimate_monthly_sales(bsr_rank: int, category: str = "") -> int:
        return SalesEstimator.estimate_daily_sales(bsr_rank, category) * 30

    @staticmethod
    def calculate_review_rate(review_count: int, monthly_sales: int) -> float:
        if monthly_sales <= 0: return 0.0
        rate = review_count / (monthly_sales * 6)
        return min(max(rate, 0.001), 0.10)

    @staticmethod
    def get_bsr_level(bsr_rank: int) -> Dict:
        if bsr_rank <= 0: return {"level": "unknown", "label": "未知", "color": "#94a3b8"}
        elif bsr_rank <= 100: return {"level": "hot", "label": "爆款", "color": "#dc2626"}
        elif bsr_rank <= 500: return {"level": "hot", "label": "热销", "color": "#f59e0b"}
        elif bsr_rank <= 2000: return {"level": "warm", "label": "良好", "color": "#10b981"}
        elif bsr_rank <= 10000: return {"level": "cool", "label": "一般", "color": "#6366f1"}
        else: return {"level": "cold", "label": "冷门", "color": "#94a3b8"}

    @staticmethod
    def _get_category_multiplier(category: str) -> float:
        cat_lower = category.lower() if category else ""
        for kw in ["electronics", "phone", "earbuds", "headphone", "light", "led"]:
            if kw in cat_lower: return 1.3
        for kw in ["home", "kitchen", "toy", "clothing", "bag"]:
            if kw in cat_lower: return 1.0
        for kw in ["industrial", "tool", "automotive", "office"]:
            if kw in cat_lower: return 0.7
        return 1.0

    @staticmethod
    def format_number(num: int) -> str:
        if num >= 10000: return f"{num/10000:.1f}万"
        return f"{num:,}"

    @staticmethod
    def format_rate(rate: float) -> str:
        return f"{rate * 100:.1f}%"


# ---- 指标存储 ----

class MetricsStore:
    """本地 JSON 存储，用于保存指标历史快照"""

    def __init__(self, data_dir: str = "data"):
        import os
        self.data_dir = data_dir
        self.metrics_file = os.path.join(data_dir, "product_metrics_history.json")
        os.makedirs(data_dir, exist_ok=True)

    def _load(self) -> Dict:
        import json, os
        if not os.path.exists(self.metrics_file): return {}
        try:
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError, IOError) as e:
            return {}

    def _save(self, data: Dict):
        import json
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_snapshot(self, product_id: str, metrics: Dict):
        from datetime import datetime, timedelta
        history = self._load()
        if product_id not in history:
            history[product_id] = {"snapshots": [], "first_seen": datetime.now().isoformat()}

        today = datetime.now().strftime("%Y-%m-%d")
        snapshot = {
            "timestamp": datetime.now().isoformat(), "date": today,
            "bsr_rank": metrics.get("bsr_rank", 0), "price": metrics.get("price", 0),
            "avg_rating": metrics.get("avg_rating", 0), "review_count": metrics.get("review_count", 0),
            "estimated_daily_sales": metrics.get("estimated_daily_sales", 0),
            "estimated_monthly_sales": metrics.get("estimated_monthly_sales", 0),
            "review_rate": metrics.get("review_rate", 0),
        }

        existing_dates = [s["date"] for s in history[product_id]["snapshots"]]
        if today in existing_dates:
            for i, s in enumerate(history[product_id]["snapshots"]):
                if s["date"] == today:
                    history[product_id]["snapshots"][i] = snapshot
                    break
        else:
            history[product_id]["snapshots"].append(snapshot)

        cutoff = (datetime.now() - timedelta(days=180)).strftime("%Y-%m-%d")
        history[product_id]["snapshots"] = [s for s in history[product_id]["snapshots"] if s["date"] >= cutoff]
        history[product_id]["last_updated"] = datetime.now().isoformat()
        self._save(history)

    def get_trends(self, product_id: str) -> Dict:
        history = self._load()
        data = history.get(product_id)
        if not data: return {}
        snapshots = data.get("snapshots", [])
        return {
            "bsr_trend": [{"date": s["date"], "rank": s.get("bsr_rank", 0)} for s in snapshots],
            "price_trend": [{"date": s["date"], "price": s.get("price", 0)} for s in snapshots],
            "rating_trend": [{"date": s["date"], "rating": s.get("avg_rating", 0)} for s in snapshots],
            "daily_sales": [{"date": s["date"], "sales": s.get("estimated_daily_sales", 0)} for s in snapshots],
            "review_rate_trend": [{"date": s["date"], "rate": s.get("review_rate", 0)} for s in snapshots],
        }

    def get_current(self, product_id: str) -> Optional[Dict]:
        history = self._load()
        data = history.get(product_id)
        if not data or not data.get("snapshots"): return None
        return data["snapshots"][-1]


# ---- 指标采集 Agent ----

class MetricsCollectorAgent(BaseAgent):
    """
    指标采集 Agent

    职责:
    - 从多数据源采集商品指标
    - 估算销量和留评率
    - 存储历史快照

    输入: {"url": "...", "keepa_api_key": "..."}
    输出: 完整的指标数据字典
    """

    def __init__(self, llm_client=None, data_dir: str = "data"):
        super().__init__(name="MetricsCollectorAgent", llm_client=llm_client)
        self.keepa_agent = KeepaSourceAgent(llm_client)
        self.camel_agent = CamelSourceAgent(llm_client)
        self.store = MetricsStore(data_dir)
        self.estimator = SalesEstimator()

    def execute(self, input_data: Any, context: Dict = None) -> Dict:
        from ..sources.amazon_page import extract_asin, detect_amazon_domain

        url = input_data.get("url", "")
        keepa_api_key = input_data.get("keepa_api_key", "")

        asin = extract_asin(url)
        if not asin:
            return {"error": "无法从链接中提取 ASIN"}

        # 优先 Keepa
        if keepa_api_key:
            domain = detect_amazon_domain(url)
            keepa_result = self.keepa_agent.execute({"asin": asin, "api_key": keepa_api_key, "domain": domain})
            if not keepa_result.get("error"):
                return self._process_keepa(keepa_result, asin)

        # 回退到爬虫
        return self._fetch_from_scraper(url, asin)

    def _process_keepa(self, keepa_data: Dict, asin: str) -> Dict:
        current_bsr = keepa_data.get("current_bsr", 0)
        current_price = keepa_data.get("current_price", 0)
        current_rating = keepa_data.get("current_rating", 0)
        current_review_count = keepa_data.get("current_review_count", 0)
        estimated_monthly = keepa_data.get("estimated_monthly_sales", 0)

        if estimated_monthly <= 0 and current_bsr > 0:
            estimated_monthly = self.estimator.estimate_monthly_sales(current_bsr)

        daily_sales = estimated_monthly // 30 if estimated_monthly > 0 else 0
        review_rate = self.estimator.calculate_review_rate(current_review_count, estimated_monthly)

        self.store.save_snapshot(asin, {
            "bsr_rank": current_bsr, "price": current_price,
            "avg_rating": current_rating, "review_count": current_review_count,
            "estimated_daily_sales": daily_sales, "estimated_monthly_sales": estimated_monthly,
            "review_rate": review_rate,
        })

        return {
            "product_id": asin, "name": keepa_data.get("title", "未知商品"),
            "data_source": "keepa", "bsr_rank": current_bsr,
            "price": current_price, "avg_rating": current_rating,
            "review_count": current_review_count,
            "estimated_daily_sales": daily_sales, "estimated_monthly_sales": estimated_monthly,
            "review_rate": review_rate,
            "bsr_level": self.estimator.get_bsr_level(current_bsr),
            "price_history": keepa_data.get("price_history", []),
            "bsr_history": keepa_data.get("bsr_history", []),
            "rating_history": keepa_data.get("rating_history", []),
            "daily_sales_history": self._bsr_to_sales(keepa_data.get("bsr_history", [])),
            "price_stats": {}, "error": None,
        }

    def _fetch_from_scraper(self, url: str, asin: str) -> Dict:
        from .scraper_agent import ScraperAgent
        scraper = ScraperAgent()
        data = scraper.scrape_amazon_reviews(url)

        if data.get("error"):
            return {"product_id": asin, "name": data.get("name", "未知商品"),
                    "data_source": "scraper", "error": data["error"]}

        bsr_rank = data.get("bsr_rank", 0)
        review_count = data.get("review_count", 0)
        price = self._parse_price(data.get("price_range", "0"))

        if price == 0 and review_count > 0:
            price = 99.99 if review_count > 10000 else 49.99 if review_count > 1000 else 29.99 if review_count > 100 else 19.99
        if bsr_rank == 0 and review_count > 0:
            bsr_rank = 500 if review_count > 10000 else 1000 if review_count > 5000 else 3000 if review_count > 1000 else 10000

        daily_sales = self.estimator.estimate_daily_sales(bsr_rank)
        monthly_sales = self.estimator.estimate_monthly_sales(bsr_rank)
        review_rate = self.estimator.calculate_review_rate(review_count, monthly_sales)

        self.store.save_snapshot(asin, {
            "bsr_rank": bsr_rank, "price": price,
            "avg_rating": data.get("avg_rating", 0), "review_count": review_count,
            "estimated_daily_sales": daily_sales, "estimated_monthly_sales": monthly_sales,
            "review_rate": review_rate,
        })

        trends = self.store.get_trends(asin)

        return {
            "product_id": asin, "name": data.get("name", "未知商品"),
            "data_source": "scraper", "bsr_rank": bsr_rank,
            "bsr_category": data.get("bsr_category", ""),
            "price": price, "avg_rating": data.get("avg_rating", 0),
            "review_count": review_count,
            "estimated_daily_sales": daily_sales, "estimated_monthly_sales": monthly_sales,
            "review_rate": review_rate,
            "bsr_level": self.estimator.get_bsr_level(bsr_rank),
            "price_history": trends.get("price_trend", []),
            "bsr_history": trends.get("bsr_trend", []),
            "rating_history": trends.get("rating_trend", []),
            "daily_sales_history": trends.get("daily_sales", []),
            "price_stats": {}, "error": None,
        }

    def _bsr_to_sales(self, bsr_history: List[Dict]) -> List[Dict]:
        return [{"date": p["date"], "sales": self.estimator.estimate_daily_sales(p["rank"])}
                for p in bsr_history]

    def _parse_price(self, price_str: str) -> float:
        if not price_str or price_str == "N/A": return 0.0
        match = re.search(r'[\d,.]+', price_str.replace(',', ''))
        try:
            return float(match.group())
        except (ValueError, AttributeError):
            return 0.0
