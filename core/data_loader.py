"""
数据加载模块
支持本地 JSON 和在线爬取两种数据源
"""
import json
import os
from typing import Dict, List, Optional


def _data_path() -> str:
    # 向上两级到达项目根目录，然后进入 data 目录
    core_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(core_dir)
    return os.path.join(project_root, "data", "sample_reviews.json")


def load_reviews() -> Dict:
    """加载评论数据"""
    with open(_data_path(), "r", encoding="utf-8") as f:
        return json.load(f)


def get_categories() -> List[Dict]:
    """获取所有品类列表"""
    data = load_reviews()
    return [
        {
            "id": cat["id"], "name": cat["name"], "name_en": cat["name_en"],
            "avg_rating": cat["avg_rating"], "review_count": cat["review_count"],
            "price_range": cat["price_range"],
        }
        for cat in data["categories"]
    ]


def get_reviews_by_category(category_id: str) -> Optional[Dict]:
    """获取指定品类的评论数据"""
    data = load_reviews()
    for cat in data["categories"]:
        if cat["id"] == category_id:
            return cat
    return None


def get_negative_reviews(category_id: str) -> List[Dict]:
    """获取指定品类的负面评论（评分 <= 2）"""
    cat = get_reviews_by_category(category_id)
    if not cat:
        return []
    return [r for r in cat["reviews"] if r["rating"] <= 2]


def get_positive_reviews(category_id: str) -> List[Dict]:
    """获取指定品类的正面评论（评分 >= 4）"""
    cat = get_reviews_by_category(category_id)
    if not cat:
        return []
    return [r for r in cat["reviews"] if r["rating"] >= 4]


def format_reviews_for_prompt(reviews: List[Dict], max_count: int = 50) -> str:
    """将评论格式化为适合 Prompt 的文本"""
    formatted = []
    for i, r in enumerate(reviews[:max_count], 1):
        formatted.append(
            f"[{i}] 评分: {r['rating']}/5 | 标题: {r['title']}\n"
            f"   内容: {r['content']}"
        )
    return "\n\n".join(formatted)


def get_negative_reviews_from_data(cat_data: Dict) -> List[Dict]:
    """从数据中获取负面评论"""
    return [r for r in cat_data.get("reviews", []) if r.get("rating", 0) <= 2]


def get_positive_reviews_from_data(cat_data: Dict) -> List[Dict]:
    """从数据中获取正面评论"""
    return [r for r in cat_data.get("reviews", []) if r.get("rating", 0) >= 4]
