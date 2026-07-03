"""
Agent 基类
所有 Agent 继承此类，共享 LLM 调用、日志、错误处理、重试能力
"""
import json
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

logger = logging.getLogger("agent")


class AgentMessage:
    """Agent 间通信的消息对象"""

    def __init__(self, sender: str, receiver: str, msg_type: str, payload: Any):
        self.sender = sender
        self.receiver = receiver
        self.msg_type = msg_type  # "request" / "response" / "error"
        self.payload = payload
        self.timestamp = time.time()

    def __repr__(self):
        return f"AgentMessage({self.sender} -> {self.receiver}, type={self.msg_type})"


class BaseAgent(ABC):
    """
    Agent 基类

    提供:
    - LLM 调用能力 (通过注入的 llm_client)
    - 统一的日志格式
    - 错误处理与重试
    - Agent 间消息传递接口
    - 生命周期钩子 (on_start / on_finish / on_error)
    """

    def __init__(self, name: str, llm_client=None):
        self.name = name
        self.llm_client = llm_client
        self._state: Dict[str, Any] = {}
        self._errors: list = []

    # ---- 生命周期钩子 ----

    def on_start(self, context: Dict[str, Any]):
        """Agent 开始工作前调用"""
        logger.info(f"[{self.name}] 启动")

    def on_finish(self, result: Any):
        """Agent 完成工作后调用"""
        logger.info(f"[{self.name}] 完成")

    def on_error(self, error: Exception):
        """Agent 发生错误时调用"""
        logger.error(f"[{self.name}] 错误: {error}")
        self._errors.append({"time": time.time(), "error": str(error)})

    # ---- 核心接口 ----

    @abstractmethod
    def execute(self, input_data: Any, context: Dict[str, Any] = None) -> Any:
        """
        Agent 的核心执行方法

        Args:
            input_data: 输入数据
            context: 共享上下文 (由 Orchestrator 注入)

        Returns:
            执行结果
        """
        pass

    def run(self, input_data: Any, context: Dict[str, Any] = None) -> Any:
        """
        带生命周期钩子的执行入口
        """
        context = context or {}
        self.on_start(context)
        try:
            result = self.execute(input_data, context)
            self.on_finish(result)
            return result
        except Exception as e:
            self.on_error(e)
            raise

    # ---- LLM 调用 ----

    def call_llm(self, system_prompt: str, user_prompt: str,
                 temperature: float = 0.7) -> str:
        """调用 LLM，自动处理无 client 的情况"""
        if not self.llm_client:
            return ""
        return self.llm_client.chat(system_prompt, user_prompt, temperature)

    def call_llm_json(self, system_prompt: str, user_prompt: str,
                      temperature: float = 0.7) -> Dict:
        """调用 LLM 并解析 JSON 响应"""
        result = self.call_llm(system_prompt, user_prompt, temperature)
        return self._parse_json(result)

    # ---- 工具方法 ----

    def log(self, msg: str):
        """统一日志输出"""
        logger.info(f"[{self.name}] {msg}")

    def _parse_json(self, text: str) -> Dict:
        """从 LLM 输出中提取 JSON"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                start = text.find("{")
                end = text.rfind("}") + 1
                if start != -1 and end > start:
                    return json.loads(text[start:end])
            except (json.JSONDecodeError, ValueError):
                pass
            logger.warning(f"[{self.name}] JSON 解析失败，返回原始文本")
            return {"raw_result": text, "parse_error": True}

    def _retry(self, fn, max_retries: int = 3, delay: float = 1.0):
        """带重试的函数执行"""
        last_error = None
        for attempt in range(max_retries):
            try:
                return fn()
            except Exception as e:
                last_error = e
                logger.warning(f"[{self.name}] 重试 {attempt + 1}/{max_retries}: {e}")
                time.sleep(delay * (attempt + 1))
        raise last_error

    def send_message(self, receiver: str, msg_type: str, payload: Any) -> AgentMessage:
        """构造消息（实际传递由 Orchestrator 负责）"""
        return AgentMessage(self.name, receiver, msg_type, payload)

    @property
    def errors(self) -> list:
        return self._errors.copy()
