"""
分析 Agent
负责情感分析、痛点提取、需求洞察
将 LLM 分析逻辑封装为 Agent 模式
"""
import json
from typing import Any, Dict, List

from .base_agent import BaseAgent


class AnalystAgent(BaseAgent):
    """
    分析 Agent

    职责:
    - 情感分析 (sentiment)
    - 痛点提取 (pain_points)
    - 需求洞察 (demands)

    输入: {"task": "sentiment"|"pain_points"|"demands"|"all", "category_data": {...}}
    输出: 分析结果字典
    """

    def __init__(self, llm_client=None):
        super().__init__(name="AnalystAgent", llm_client=llm_client)

    def execute(self, input_data: Any, context: Dict = None) -> Dict:
        task = input_data.get("task", "all") if isinstance(input_data, dict) else "all"
        cat_data = input_data.get("category_data", {}) if isinstance(input_data, dict) else {}

        if not cat_data:
            return {"error": "未提供品类数据"}

        if task == "all":
            return {
                "sentiment": self.analyze_sentiment(cat_data),
                "pain_points": self.analyze_pain_points(cat_data),
                "demands": self.analyze_demands(cat_data),
            }
        elif task == "sentiment":
            return self.analyze_sentiment(cat_data)
        elif task == "pain_points":
            return self.analyze_pain_points(cat_data)
        elif task == "demands":
            return self.analyze_demands(cat_data)
        else:
            return {"error": f"未知任务: {task}"}

    # ---- 情感分析 ----

    def analyze_sentiment(self, cat_data: Dict) -> Dict:
        reviews = cat_data.get("reviews", [])
        total = len(reviews)

        if total > 0:
            positive = sum(1 for r in reviews if r.get("rating", 0) >= 4)
            negative = sum(1 for r in reviews if r.get("rating", 0) <= 2)
            neutral = total - positive - negative
            pos_ratio = round(positive / total, 2)
            neg_ratio = round(negative / total, 2)
            neu_ratio = round(neutral / total, 2)
        else:
            pos_ratio, neg_ratio, neu_ratio = 0, 0, 0

        reviews_text = self._format_reviews(reviews)
        category = cat_data.get("name", "未知品类")

        system_prompt = "你是一位资深的跨境电商数据分析专家，擅长从用户评论中提取有价值的信息。请用中文回复。"

        user_prompt = f"""请分析以下商品评论的情感倾向。

商品品类：{category}
评论数量：{total}
评论内容：
{reviews_text}

请按以下 JSON 格式返回分析结果：
{{
    "overall_sentiment": "positive/negative/mixed",
    "positive_keywords": ["英文关键词1（中文翻译）", "英文关键词2（中文翻译）"],
    "negative_keywords": ["英文关键词1（中文翻译）", "英文关键词2（中文翻译）"],
    "summary": "一句话总结情感分析结果"
}}"""

        result = self.call_llm_json(system_prompt, user_prompt)
        result["positive_ratio"] = pos_ratio
        result["negative_ratio"] = neg_ratio
        result["neutral_ratio"] = neu_ratio

        if pos_ratio >= 0.6:
            result["overall_sentiment"] = "positive"
        elif neg_ratio >= 0.4:
            result["overall_sentiment"] = "negative"
        else:
            result["overall_sentiment"] = "mixed"

        return result

    # ---- 痛点提取 ----

    def analyze_pain_points(self, cat_data: Dict) -> Dict:
        negative = [r for r in cat_data.get("reviews", []) if r.get("rating", 0) <= 2]
        if not negative:
            return {"pain_points": [], "recommendation": "暂无负面评论，无法分析痛点。"}

        reviews_text = self._format_reviews(negative)
        category = cat_data.get("name", "未知品类")

        system_prompt = "你是一位资深的跨境电商数据分析专家，擅长从用户评论中提取有价值的信息。请用中文回复。"

        user_prompt = f"""请从以下负面评论中提取用户的核心痛点问题。

商品品类：{category}
负面评论内容：
{reviews_text}

请按以下 JSON 格式返回分析结果：
{{
    "pain_points": [
        {{
            "issue": "痛点描述",
            "severity": "high/medium/low",
            "frequency": 出现次数,
            "example": "典型用户原话摘录"
        }}
    ],
    "recommendation": "针对这些痛点的产品改进建议"
}}

要求：
1. 提取最核心的 5 个痛点
2. 按严重程度排序
3. 每个痛点要有具体的用户原话作为佐证"""

        return self.call_llm_json(system_prompt, user_prompt)

    # ---- 需求洞察 ----

    def analyze_demands(self, cat_data: Dict) -> Dict:
        reviews = cat_data.get("reviews", [])
        reviews_with_rating = []
        for r in reviews:
            reviews_with_rating.append(
                f"[评分: {r.get('rating', 0)}/5] {r.get('title', '')} - {r.get('content', '')}"
            )
        reviews_text = "\n\n".join(reviews_with_rating)
        category = cat_data.get("name", "未知品类")

        system_prompt = "你是一位资深的跨境电商数据分析专家，擅长从用户评论中提取有价值的信息。请用中文回复。"

        user_prompt = f"""请分析以下评论中体现的用户需求和市场机会。

商品品类：{category}
评论内容（含评分）：
{reviews_text}

请按以下 JSON 格式返回分析结果：
{{
    "demands": [
        {{
            "demand": "需求描述",
            "priority": "high/medium/low",
            "market_gap": true/false
        }}
    ],
    "unmet_needs": "总结未被满足的市场需求和机会点"
}}

要求：
1. 区分已满足和未满足的需求
2. 重点识别市场缺口（竞品做得不好的地方）
3. 给出优先级排序"""

        return self.call_llm_json(system_prompt, user_prompt)

    # ---- 工具方法 ----

    def _format_reviews(self, reviews: List[Dict], max_count: int = 50) -> str:
        formatted = []
        for i, r in enumerate(reviews[:max_count], 1):
            formatted.append(
                f"[{i}] 评分: {r.get('rating', 0)}/5 | 标题: {r.get('title', '')}\n"
                f"   内容: {r.get('content', '')}"
            )
        return "\n\n".join(formatted)
