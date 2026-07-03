"""
数据采集 Agent
负责从亚马逊商品页面爬取评论数据
将原始爬虫逻辑封装为 Agent 模式，增加协调接口
"""
import re
import time
import random
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import cloudscraper
from bs4 import BeautifulSoup

from .base_agent import BaseAgent
from ..sources.amazon_page import extract_asin, get_base_url


class ScraperAgent(BaseAgent):
    """
    数据采集 Agent

    职责:
    - 从亚马逊商品 URL 爬取评论
    - 提取商品基本信息 (标题/价格/评分/BSR)
    - 支持多页爬取
    - 返回标准化数据格式

    输入: {"url": "https://amazon.com/dp/B0xxx", "max_pages": 5}
    输出: {"id": "ASIN", "name": "...", "reviews": [...], ...}
    """

    def __init__(self, llm_client=None):
        super().__init__(name="ScraperAgent", llm_client=llm_client)

    def execute(self, input_data: Any, context: Dict = None) -> Dict:
        url = input_data.get("url", "") if isinstance(input_data, dict) else str(input_data)
        max_pages = input_data.get("max_pages", 5) if isinstance(input_data, dict) else 5

        if not url:
            return {"error": "未提供 URL", "reviews": []}

        return self._scrape_with_fallback(url, max_pages)

    # ---- 爬取逻辑 ----

    def _create_scraper(self):
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False},
            delay=5,
        )
        scraper.headers.update({
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        })
        return scraper

    def _extract_asin(self, url: str) -> Optional[str]:
        """从 URL 提取 ASIN（委托给共享工具函数）"""
        return extract_asin(url)

    def _get_base_url(self, url: str) -> str:
        """提取域名基础 URL（委托给共享工具函数）"""
        return get_base_url(url)

    def _parse_product_page(self, soup: BeautifulSoup) -> Dict:
        """解析商品主页，获取基本信息"""
        title = ""
        for sel in ["#productTitle", "h1.a-size-large span"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break

        # 提取价格
        price = ""
        for sel in [
            "#corePriceDisplay_desktop_feature_div .a-offscreen",
            "#apex_offerDisplay_desktop .a-offscreen",
            ".a-price .a-offscreen",
            "#priceblock_ourprice", "#priceblock_dealprice",
            ".priceToPay .a-offscreen", "#apex_desktop .a-offscreen",
            ".a-price-whole",
        ]:
            el = soup.select_one(sel)
            if el:
                txt = el.get_text(strip=True)
                if any(c in txt for c in ['$', '€', '£', '¥']) or re.search(r'\d+\.\d{2}', txt):
                    price = txt
                    break

        if not price:
            html_text = str(soup)
            for pattern in [r'"priceAmount":\s*"?([\d.]+)"?', r'\$(\d+\.\d{2})']:
                matches = re.findall(pattern, html_text)
                if matches:
                    for m in matches:
                        try:
                            p = float(m)
                            if 5 < p < 10000:
                                price = f"${p:.2f}"
                                break
                        except (ValueError, TypeError):
                            pass
                if price: break

        # 提取评分
        avg_rating = 0.0
        for sel in ["#acrPopover .a-icon-alt", "#averageCustomerReviews .a-icon-alt",
                     "[data-hook='rating-out-of-text']"]:
            el = soup.select_one(sel)
            if el:
                match = re.search(r'([\d.]+)', el.get_text())
                if match:
                    avg_rating = float(match.group(1))
                    break

        if avg_rating == 0:
            for pattern in [r'"rating":\s*"?(\d+\.?\d*)"?', r'(\d+\.?\d*)\s+out\s+of\s+5']:
                match = re.search(pattern, str(soup))
                if match:
                    try:
                        r = float(match.group(1))
                        if 1 <= r <= 5:
                            avg_rating = r
                            break
                    except (ValueError, TypeError):
                        pass

        # 提取评论数
        review_count = 0
        for sel in ["#acrCustomerReviewText", "[data-hook='total-review-count']"]:
            el = soup.select_one(sel)
            if el:
                match = re.search(r'([\d,]+)', el.get_text())
                if match:
                    review_count = int(match.group(1).replace(",", ""))
                    break

        if review_count == 0:
            for pattern in [r'"reviewCount":\s*"?(\d+)"?', r'(\d+)\s+(?:global\s+)?ratings?']:
                match = re.search(pattern, str(soup))
                if match:
                    try:
                        count = int(match.group(1).replace(',', ''))
                        if count > 0:
                            review_count = count
                            break
                    except: pass

        # 提取 BSR
        bsr_rank, bsr_category = self._extract_bsr(soup)

        return {
            "title": title, "price": price, "avg_rating": avg_rating,
            "review_count": review_count, "bsr_rank": bsr_rank, "bsr_category": bsr_category,
        }

    def _extract_bsr(self, soup: BeautifulSoup) -> tuple:
        page_text = soup.get_text()
        bsr_patterns = [
            r'Best\s+Sellers?\s+Rank[:\s]*#?([\d,]+)\s+in\s+([^\n(]+)',
            r'#([\d,]+)\s+in\s+([^\n(#]+)',
        ]
        for pattern in bsr_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                try:
                    rank = int(match.group(1).replace(",", ""))
                    category = re.sub(r'\s*\(.*$', '', match.group(2).strip()).strip()
                    return rank, category
                except ValueError:
                    continue
        return 0, ""

    def _parse_reviews_from_product_page(self, soup: BeautifulSoup) -> List[Dict]:
        reviews = []
        for el in soup.select('[data-hook="review"]'):
            review = {}
            rating_el = el.select_one('[data-hook="review-star-rating"] .a-icon-alt')
            if rating_el:
                match = re.search(r'([\d.]+)', rating_el.get("alt", "") or rating_el.get_text())
                review["rating"] = float(match.group(1)) if match else 0
            else:
                review["rating"] = 0

            title_el = el.select_one('[data-hook="reviewTitle"], [data-hook="review-title"]')
            if title_el:
                span = title_el.select_one("span")
                review["title"] = span.get_text(strip=True) if span else title_el.get_text(strip=True)
            else:
                review["title"] = ""

            date_el = el.select_one('[data-hook="review-date"]')
            review["date"] = date_el.get_text(strip=True) if date_el else ""

            body_el = el.select_one('[data-hook="reviewRichContentContainer"]') or \
                      el.select_one('[data-hook="review-body"]')
            review["content"] = body_el.get_text(strip=True) if body_el else ""

            helpful_el = el.select_one('[data-hook="helpful-vote-statement"]')
            if helpful_el:
                match = re.search(r'([\d,]+)', helpful_el.get_text())
                review["helpful_votes"] = int(match.group(1).replace(",", "")) if match else 0
            else:
                review["helpful_votes"] = 0

            badges = el.select_one('[data-hook="review-badges"]')
            review["verified"] = "Verified Purchase" in badges.get_text() if badges else False

            if review["title"] or review["content"]:
                reviews.append(review)
        return reviews

    def _parse_reviews_from_page(self, soup: BeautifulSoup) -> List[Dict]:
        reviews = []
        for el in soup.select('[data-hook="review"]'):
            review = {}
            rating_el = el.select_one('[data-hook="review-star-rating"] .a-icon-alt, '
                                       '[data-hook="cmps-review-star-rating"] .a-icon-alt')
            if rating_el:
                match = re.search(r'([\d.]+)', rating_el.get_text())
                review["rating"] = float(match.group(1)) if match else 0
            else:
                review["rating"] = 0

            title_el = el.select_one('[data-hook="review-title"]')
            if title_el:
                span = title_el.select_one("span")
                review["title"] = span.get_text(strip=True) if span else title_el.get_text(strip=True)
            else:
                review["title"] = ""

            review["date"] = (el.select_one('[data-hook="review-date"]') or type('', (), {"get_text": lambda s=False: ""})()).get_text(strip=True)
            body_el = el.select_one('[data-hook="reviewRichContentContainer"], [data-hook="review-body"]')
            review["content"] = body_el.get_text(strip=True) if body_el else ""

            helpful_el = el.select_one('[data-hook="helpful-vote-statement"]')
            if helpful_el:
                match = re.search(r'([\d,]+)', helpful_el.get_text())
                review["helpful_votes"] = int(match.group(1).replace(",", "")) if match else 0
            else:
                review["helpful_votes"] = 0

            badges = el.select_one('[data-hook="review-badges"]')
            review["verified"] = "Verified Purchase" in badges.get_text() if badges else False

            if review["title"] or review["content"]:
                reviews.append(review)
        return reviews

    def scrape_amazon_reviews(self, url: str, max_pages: int = 5) -> Dict:
        asin = self._extract_asin(url)
        if not asin:
            raise ValueError(f"无法从链接中提取 ASIN: {url}")

        base_url = self._get_base_url(url)
        scraper = self._create_scraper()

        product_url = f"{base_url}/dp/{asin}"
        resp = scraper.get(product_url, timeout=30)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")
        if soup.select_one("form[action*='validateCaptcha']"):
            raise RuntimeError("遇到亚马逊验证码，请稍后重试")

        product_info = self._parse_product_page(soup)
        self.log(f"商品信息: {product_info['title'][:50]}...")

        all_reviews = self._parse_reviews_from_product_page(soup)

        if len(all_reviews) < 10 and max_pages > 1:
            time.sleep(random.uniform(2, 4))
            for page in range(2, max_pages + 1):
                review_url = f"{base_url}/product-reviews/{asin}/?pageNumber={page}&sortBy=recent"
                try:
                    resp = scraper.get(review_url, timeout=30)
                    if resp.status_code != 200:
                        break
                    soup = BeautifulSoup(resp.text, "lxml")
                    if soup.select_one("form[action*='validateCaptcha']"):
                        break
                    reviews = self._parse_reviews_from_page(soup)
                    if not reviews:
                        break
                    all_reviews.extend(reviews)
                    time.sleep(random.uniform(2, 4))
                except Exception:
                    break

        return {
            "id": asin,
            "name": product_info.get("title", "未知商品"),
            "name_en": product_info.get("title", "Unknown Product"),
            "price_range": product_info.get("price", "N/A"),
            "avg_rating": product_info.get("avg_rating", 0),
            "review_count": product_info.get("review_count", len(all_reviews)),
            "bsr_rank": product_info.get("bsr_rank", 0),
            "bsr_category": product_info.get("bsr_category", ""),
            "reviews": all_reviews,
        }

    def _scrape_with_fallback(self, url: str, max_pages: int = 5) -> Dict:
        try:
            return self._retry(lambda: self.scrape_amazon_reviews(url, max_pages))
        except Exception as e:
            return {
                "id": "unknown", "name": f"爬取失败: {str(e)}",
                "name_en": f"Scrape failed: {str(e)}",
                "price_range": "N/A", "avg_rating": 0, "review_count": 0,
                "bsr_rank": 0, "bsr_category": "", "reviews": [],
                "error": str(e),
            }
