"""
总控 Agent (Orchestrator)
负责调度所有子 Agent，管理全局状态和数据流转
这是整个系统的"大脑"
"""
import json
from typing import Any, Dict, Optional

from .base_agent import BaseAgent
from .scraper_agent import ScraperAgent
from .analyst_agent import AnalystAgent
from .reporter_agent import ReporterAgent
from .metrics_agent import MetricsCollectorAgent


class OrchestratorAgent(BaseAgent):
    """
    总控 Agent

    职责:
    - 接收用户请求，分解为子任务
    - 按依赖关系调度子 Agent
    - 管理全局上下文 (context)
    - 汇总结果返回给用户

    工作流:
    1. URL 模式: ScraperAgent -> AnalystAgent -> ReporterAgent
    2. Demo 模式: AnalystAgent -> ReporterAgent
    3. 指标采集: MetricsCollectorAgent
    """

    def __init__(self, llm_client=None, data_dir: str = "data"):
        super().__init__(name="OrchestratorAgent", llm_client=llm_client)
        self.data_dir = data_dir

        # 初始化子 Agent（共享 LLM 客户端）
        self.scraper = ScraperAgent(llm_client)
        self.analyst = AnalystAgent(llm_client)
        self.reporter = ReporterAgent(llm_client)
        self.metrics_collector = MetricsCollectorAgent(llm_client, data_dir)

        # 全局上下文
        self._context: Dict[str, Any] = {}

    @property
    def context(self) -> Dict:
        return self._context.copy()

    def execute(self, input_data: Any, context: Dict = None) -> Any:
        """根据输入分发到不同的工作流"""
        task = input_data.get("task", "") if isinstance(input_data, dict) else ""
        self._context = context or {}

        if task == "analyze_url":
            return self._workflow_url(input_data)
        elif task == "analyze_demo":
            return self._workflow_demo(input_data)
        elif task == "get_metrics":
            return self._workflow_metrics(input_data)
        elif task == "generate_report":
            return self._workflow_report(input_data)
        else:
            return {"error": f"未知任务: {task}"}

    # ---- URL 分析工作流 ----

    def _workflow_url(self, input_data: Dict) -> Dict:
        """
        URL 分析全流程:
        1. ScraperAgent 爬取评论
        2. AnalystAgent 分析情感/痛点/需求
        3. 结果汇总
        """
        url = input_data.get("url", "")
        max_pages = input_data.get("max_pages", 5)

        if not url:
            return {"error": "请输入亚马逊商品链接"}

        # Step 1: 爬取
        self.log("Step 1/3: 爬取评论数据...")
        cat_data = self.scraper.execute({"url": url, "max_pages": max_pages}, self._context)

        if cat_data.get("error"):
            return {
                "product_info": cat_data, "sentiment": {},
                "pain_points": {}, "demands": {}, "error": cat_data["error"],
            }

        if not cat_data.get("reviews"):
            return {
                "product_info": cat_data, "sentiment": {},
                "pain_points": {}, "demands": {}, "error": "未爬取到任何评论数据",
            }

        # Step 2: 翻译评论
        self.log("Step 2/3: 翻译评论...")
        cat_data = self._translate_reviews(cat_data)

        # Step 3: 分析
        self.log("Step 3/3: 执行分析...")
        analysis = self.analyst.execute({"task": "all", "category_data": cat_data}, self._context)

        return {
            "product_info": cat_data,
            "sentiment": analysis.get("sentiment", {}),
            "pain_points": analysis.get("pain_points", {}),
            "demands": analysis.get("demands", {}),
        }

    # ---- Demo 分析工作流 ----

    def _workflow_demo(self, input_data: Dict) -> Dict:
        """Demo 模式: 使用本地示例数据"""
        from ..data_loader import load_reviews, get_reviews_by_category

        category_id = input_data.get("category_id", "")
        if not category_id:
            return {"error": "请选择品类"}

        cat_data = get_reviews_by_category(category_id)
        if not cat_data:
            return {"error": f"品类不存在: {category_id}"}

        self.log(f"分析品类: {cat_data.get('name', category_id)}")

        # 执行分析
        sentiment = self.analyst.analyze_sentiment(cat_data)
        pain_points = self.analyst.analyze_pain_points(cat_data)
        demands = self.analyst.analyze_demands(cat_data)

        return {
            "product_info": cat_data,
            "sentiment": sentiment,
            "pain_points": pain_points,
            "demands": demands,
        }

    # ---- 指标采集工作流 ----

    def _workflow_metrics(self, input_data: Dict) -> Dict:
        """采集商品指标数据"""
        url = input_data.get("url", "")
        keepa_api_key = input_data.get("keepa_api_key", "")

        self.log("采集商品指标...")
        return self.metrics_collector.execute({
            "url": url, "keepa_api_key": keepa_api_key,
        }, self._context)

    # ---- 报告生成工作流 ----

    def _workflow_report(self, input_data: Dict) -> str:
        """生成选品报告"""
        self.log("生成选品报告...")
        return self.reporter.execute(input_data, self._context)

    # ---- 评论翻译 ----

    def _translate_reviews(self, cat_data: Dict) -> Dict:
        """批量翻译评论标题和内容为中文"""
        import re
        reviews = cat_data.get("reviews", [])
        if not reviews:
            return cat_data

        batch_size = 10
        for i in range(0, len(reviews), batch_size):
            batch = reviews[i:i + batch_size]
            items = []
            for j, r in enumerate(batch):
                items.append(f"[{j}] 标题: {r.get('title', '')}\n内容: {r.get('content', '')}")

            prompt = f"""请将以下英文评论翻译成中文，保持原意。每条评论返回一行，格式为：
[序号] 标题翻译 ||| 内容翻译

只返回翻译结果，不要添加其他说明。

评论：
{"".join([chr(10) + item for item in items])}"""

            result = self.call_llm(
                "你是一位专业的英中翻译，擅长电商评论翻译。请准确翻译，保持原文语气。",
                prompt, temperature=0.3
            )

            translations = {}
            for line in result.strip().split("\n"):
                line = line.strip()
                if not line: continue
                m = re.match(r'\[(\d+)\]\s*(.+?)\s*\|\|\|\s*(.+)', line)
                if m:
                    translations[int(m.group(1))] = (m.group(2).strip(), m.group(3).strip())

            for j, r in enumerate(batch):
                if j in translations:
                    title_cn, content_cn = translations[j]
                    orig_title = r.get('title', '')
                    orig_content = r.get('content', '')
                    if title_cn and orig_title:
                        r['title'] = f"{orig_title}（{title_cn}）"
                    if content_cn and orig_content:
                        r['content'] = f"{orig_content}（{content_cn}）"

        return cat_data

    # ---- 便捷方法 ----

    def analyze_from_url(self, url: str, max_pages: int = 5) -> Dict:
        """从 URL 执行完整分析（便捷入口）"""
        return self.run({"task": "analyze_url", "url": url, "max_pages": max_pages})

    def analyze_demo(self, category_id: str) -> Dict:
        """Demo 模式分析（便捷入口）"""
        return self.run({"task": "analyze_demo", "category_id": category_id})

    def get_metrics(self, url: str, keepa_api_key: str = "") -> Dict:
        """采集指标（便捷入口）"""
        return self.run({"task": "get_metrics", "url": url, "keepa_api_key": keepa_api_key})

    def generate_report(self, input_data: Dict) -> str:
        """生成报告（便捷入口）"""
        return self.run({"task": "generate_report", **input_data})
