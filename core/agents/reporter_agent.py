"""
报告生成 Agent
负责将分析结果转化为结构化选品报告
"""
import json
from typing import Any, Dict

from .base_agent import BaseAgent


class ReporterAgent(BaseAgent):
    """
    报告生成 Agent

    职责:
    - 接收情感分析、痛点提取、需求洞察的结果
    - 生成 Markdown 格式的选品分析报告

    输入: {
        "category_data": {...},
        "sentiment": {...},
        "pain_points": {...},
        "demands": {...}
    }
    输出: Markdown 格式报告字符串
    """

    def __init__(self, llm_client=None):
        super().__init__(name="ReporterAgent", llm_client=llm_client)

    def execute(self, input_data: Any, context: Dict = None) -> str:
        cat_data = input_data.get("category_data", {})
        sentiment = input_data.get("sentiment", {})
        pain_points = input_data.get("pain_points", {})
        demands = input_data.get("demands", {})

        category = cat_data.get("name", "未知品类")
        price_range = cat_data.get("price_range", "N/A")
        avg_rating = cat_data.get("avg_rating", 0)
        review_count = cat_data.get("review_count", 0)

        system_prompt = (
            "你是一位资深的跨境电商数据分析专家，"
            "擅长从用户评论中提取有价值的信息。请用中文回复，"
            "报告要专业、具体、有数据支撑。"
        )

        user_prompt = f"""请根据以下分析数据，生成一份完整的跨境电商选品分析报告。

商品品类：{category}
价格区间：{price_range}
平均评分：{avg_rating}
评论数量：{review_count}

情感分析结果：
{json.dumps(sentiment, ensure_ascii=False, indent=2)}

痛点分析结果：
{json.dumps(pain_points, ensure_ascii=False, indent=2)}

需求分析结果：
{json.dumps(demands, ensure_ascii=False, indent=2)}

请生成一份结构清晰的 Markdown 格式报告，包含：
1. 市场概况
2. 用户情感分析
3. 核心痛点
4. 未满足需求
5. 选品建议（是否推荐进入、差异化方向、定价策略、风险提示）"""

        return self.call_llm(system_prompt, user_prompt, temperature=0.5)
