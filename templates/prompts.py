"""
跨境电商选品分析 - Prompt 模板
"""

SYSTEM_ROLE = """你是一位资深的跨境电商数据分析专家，擅长从用户评论中提取有价值的信息。
请用中文回复，分析要专业、具体、有数据支撑。"""

# 情感分析 Prompt
SENTIMENT_ANALYSIS = {
    "system": SYSTEM_ROLE,
    "user": """请分析以下商品评论的情感倾向。

商品品类：{category}
评论数量：{count}
评论内容：
{reviews}

请按以下 JSON 格式返回分析结果：
{{
    "overall_sentiment": "positive/negative/mixed",
    "positive_ratio": 0.0-1.0,
    "negative_ratio": 0.0-1.0,
    "neutral_ratio": 0.0-1.0,
    "positive_keywords": ["英文关键词1（中文翻译）", "英文关键词2（中文翻译）"],
    "negative_keywords": ["英文关键词1（中文翻译）", "英文关键词2（中文翻译）"],
    "summary": "一句话总结情感分析结果"
}}

注意：关键词请用英文原文，后面括号内附中文翻译，格式为 "keyword（中文）"。"""
}

# 痛点提取 Prompt
PAIN_POINT_EXTRACTION = {
    "system": SYSTEM_ROLE,
    "user": """请从以下负面评论中提取用户的核心痛点问题。

商品品类：{category}
负面评论内容：
{reviews}

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
1. 提取最核心的 {top_n} 个痛点
2. 按严重程度排序
3. 每个痛点要有具体的用户原话作为佐证"""
}

# 需求分析 Prompt
DEMAND_ANALYSIS = {
    "system": SYSTEM_ROLE,
    "user": """请分析以下评论中体现的用户需求和市场机会。

商品品类：{category}
评论内容（含评分）：
{reviews}

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
}

# 选品报告 Prompt
PRODUCT_REPORT = {
    "system": SYSTEM_ROLE,
    "user": """请根据以下分析数据，生成一份完整的跨境电商选品分析报告。

商品品类：{category}
价格区间：{price_range}
平均评分：{avg_rating}
评论数量：{review_count}

情感分析结果：
{sentiment_result}

痛点分析结果：
{pain_point_result}

需求分析结果：
{demand_result}

请生成一份结构清晰的 Markdown 格式报告，包含：
1. 市场概况
2. 用户情感分析
3. 核心痛点
4. 未满足需求
5. 选品建议（是否推荐进入、差异化方向、定价策略、风险提示）"""
}
