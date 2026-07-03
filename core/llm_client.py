"""
通义千问 API 客户端封装
"""
import json
from typing import Optional

from config import DASHSCOPE_API_KEY, QWEN_MODEL


class QwenClient:
    """通义千问 API 客户端"""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model or QWEN_MODEL
        self._client = None
        self.using_api = False  # 标记是否真正使用了 API
        self.last_error = ""    # 记录最后一次错误

    def _get_client(self):
        """懒加载 dashscope 客户端"""
        if self._client is None:
            try:
                import dashscope
                dashscope.api_key = self.api_key
                self._client = dashscope
            except ImportError:
                raise ImportError(
                    "请安装 dashscope: pip install dashscope"
                )
        return self._client

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """
        调用通义千问进行对话

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数，控制随机性

        Returns:
            模型回复文本
        """
        # 检查 API Key 是否有效
        if not self.api_key or len(self.api_key.strip()) < 10:
            self.using_api = False
            self.last_error = "未填写有效的 API Key"
            return self._mock_response(system_prompt, user_prompt)

        try:
            from dashscope import Generation
            import dashscope
            dashscope.api_key = self.api_key

            response = Generation.call(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                result_format="message"
            )

            if response.status_code == 200:
                self.using_api = True
                self.last_error = ""
                return response.output.choices[0].message.content
            else:
                self.using_api = False
                self.last_error = f"API 返回错误: {response.code} - {response.message}"
                return self._mock_response(system_prompt, user_prompt)

        except ImportError:
            self.using_api = False
            self.last_error = "未安装 dashscope 库"
            return self._mock_response(system_prompt, user_prompt)
        except Exception as e:
            self.using_api = False
            self.last_error = f"{type(e).__name__}: {str(e)}"
            return self._mock_response(system_prompt, user_prompt)

    def _detect_category(self, text: str) -> str:
        """从 prompt 文本中检测品类"""
        category_map = {
            "无线蓝牙耳机": "wireless_earbuds",
            "Wireless": "wireless_earbuds",
            "便携式榨汁机": "portable_blender",
            "Blender": "portable_blender",
            "LED 灯带": "led_strip_lights",
            "LED": "led_strip_lights",
            "瑜伽垫": "yoga_mat",
            "Yoga": "yoga_mat",
            "手机支架": "phone_stand",
            "Phone Stand": "phone_stand",
        }
        for keyword, cat_id in category_map.items():
            if keyword in text:
                return cat_id
        return "wireless_earbuds"  # 默认

    def _mock_response(self, system_prompt: str, user_prompt: str) -> str:
        """
        模拟响应（当未安装 dashscope 或未配置 API Key 时使用）
        用于 Demo 展示，返回基于品类的差异化分析结果
        """
        category = self._detect_category(user_prompt)
        if "情感" in system_prompt or "sentiment" in system_prompt.lower():
            return self._mock_sentiment_analysis(user_prompt, category)
        elif "痛点" in system_prompt or "pain" in system_prompt.lower():
            return self._mock_pain_point_analysis(user_prompt, category)
        elif "需求" in system_prompt or "demand" in system_prompt.lower():
            return self._mock_demand_analysis(user_prompt, category)
        elif "报告" in system_prompt or "report" in system_prompt.lower():
            return self._mock_report(user_prompt, category)
        else:
            return "分析完成。请配置 API Key 以获取更精准的 LLM 分析结果。"

    # ==================== 品类专属模拟数据 ====================

    _SENTIMENT_DATA = {
        "wireless_earbuds": {
            "overall_sentiment": "mixed",
            "positive_keywords": ["sound quality", "comfortable", "noise cancellation", "value", "battery life"],
            "negative_keywords": ["broke", "uncomfortable", "Bluetooth range", "microphone", "charging case"],
            "summary": "用户对音质和性价比认可度较高，但产品耐用性和麦克风质量是主要槽点。40%用户给出好评，30%给出差评，整体口碑两极分化。运动场景和通话场景的用户满意度差异明显。"
        },
        "portable_blender": {
            "overall_sentiment": "mixed",
            "positive_keywords": ["smoothies", "portable", "easy to clean", "compact", "baby food"],
            "negative_keywords": ["leaked", "weak motor", "battery", "blade broke", "cheap"],
            "summary": "便携性和易清洗是最大卖点，但密封性和电机动力不足引发大量投诉。产品安全性（刀片破裂）是严重隐患。适合软质水果，不适合冰块和硬质食材。"
        },
        "led_strip_lights": {
            "overall_sentiment": "positive",
            "positive_keywords": ["ambiance", "easy installation", "color options", "value", "app control"],
            "negative_keywords": ["adhesive", "colors don't match", "WiFi issues", "overheated", "fire hazard"],
            "summary": "用户对灯光效果和安装便捷性满意度很高，性价比突出。但粘贴力不足、颜色偏差和WiFi连接不稳定是常见问题。安全问题（过热）虽然频次低但严重程度高。"
        },
        "yoga_mat": {
            "overall_sentiment": "mixed",
            "positive_keywords": ["thickness", "grip", "durable", "beautiful design", "alignment marks"],
            "negative_keywords": ["chemical smell", "peeling", "slippery when sweaty", "heavy", "poor quality"],
            "summary": "防滑性和厚度获得好评，图案设计也是加分项。但化学气味和表面脱落是两个最突出的负面反馈。出汗后防滑性能下降，不适合高温瑜伽。"
        },
        "phone_stand": {
            "overall_sentiment": "positive",
            "positive_keywords": ["sturdy", "adjustable", "minimalist design", "video calls", "portable"],
            "negative_keywords": ["not compatible", "wobbles with tablet", "expensive", "thick cases"],
            "summary": "做工扎实、设计简约、角度可调是核心优势，视频通话场景表现优秀。但对厚手机壳和平板的兼容性不足，部分用户认为定价偏高。"
        },
    }

    _PAIN_POINT_DATA = {
        "wireless_earbuds": {
            "pain_points": [
                {"issue": "产品耐用性差，短期内损坏", "severity": "high", "frequency": 4,
                 "example": "左耳耳机2周后无法充电，联系卖家无回复，浪费钱。"},
                {"issue": "佩戴舒适度不足", "severity": "high", "frequency": 3,
                 "example": "耳塞太硬，佩戴30分钟后耳朵开始疼痛，希望配有记忆海绵耳塞。"},
                {"issue": "麦克风通话质量极差", "severity": "high", "frequency": 2,
                 "example": "对方说我的声音像在隧道里，麦克风完全不能用于工作通话。"},
                {"issue": "充电盒质量低劣", "severity": "medium", "frequency": 2,
                 "example": "充电盒铰链一个月就坏了，只能用橡皮筋固定。"},
                {"issue": "蓝牙连接距离有限", "severity": "medium", "frequency": 2,
                 "example": "离开手机超过3米就断连，蓝牙范围太小。"},
            ],
            "recommendation": "建议优先解决产品耐用性问题（耳塞和充电盒），其次是佩戴舒适度（更换耳塞材质）和麦克风质量。这三个问题占据了80%的差评原因。"
        },
        "portable_blender": {
            "pain_points": [
                {"issue": "密封性差导致液体泄漏", "severity": "high", "frequency": 3,
                 "example": "第一次使用 smoothie 就漏满了整个包，盖子根本锁不紧，立即退货。"},
                {"issue": "刀片组件破裂（安全隐患）", "severity": "high", "frequency": 2,
                 "example": "搅拌草莓时刀片组件裂开，廉价塑料构造，差点伤到人。"},
                {"issue": "电机动力不足", "severity": "medium", "frequency": 3,
                 "example": "软水果可以，但冰块和冷冻浆果完全不行，电机会卡住发出研磨声。"},
                {"issue": "电池续航太短", "severity": "medium", "frequency": 2,
                 "example": "只能做3-4杯就需要充电，充满要3小时，出行不实用。"},
                {"issue": "容量偏小", "severity": "low", "frequency": 1,
                 "example": "380ml 容量只够一杯，希望能更大一些。"},
            ],
            "recommendation": "密封性和刀片安全性是必须优先解决的致命问题，直接影响用户安全和基本使用。电机动力和电池续航是第二优先级。"
        },
        "led_strip_lights": {
            "pain_points": [
                {"issue": "电源适配器过热（火灾隐患）", "severity": "high", "frequency": 2,
                 "example": "运行4小时后电源适配器烫得无法触摸，闻到烧焦味，立即拔掉。这是安全隐患。"},
                {"issue": "粘贴背胶不牢固", "severity": "medium", "frequency": 3,
                 "example": "灯本身很好但背胶一周后就开始脱落，不得不额外购买安装夹。"},
                {"issue": "颜色与APP显示不一致", "severity": "medium", "frequency": 2,
                 "example": "APP选蓝色显示紫色，绿色偏黄，颜色准确度很差。"},
                {"issue": "WiFi连接不稳定", "severity": "low", "frequency": 2,
                 "example": "遥控器可以用但WiFi APP不断断连，重置了好几次，智能功能体验很差。"},
            ],
            "recommendation": "过热安全问题必须立即解决（可能涉及电源适配器规格升级）。背胶质量需要提升（建议改用3M胶或增加安装夹）。颜色校准和WiFi稳定性也需要优化。"
        },
        "yoga_mat": {
            "pain_points": [
                {"issue": "强烈的化学气味", "severity": "high", "frequency": 3,
                 "example": "垫子有严重的化学气味，通风两周后仍未消散，练习时头痛。质量控制不可接受。"},
                {"issue": "表面材质脱落", "severity": "high", "frequency": 2,
                 "example": "使用一个月后表面开始剥落，练习后到处都是小碎片，材料质量明显很差。"},
                {"issue": "出汗后打滑", "severity": "medium", "frequency": 2,
                 "example": "干燥时防滑可以，但高强度练习出汗后就打滑，需要在上面铺毛巾。不应该叫'防滑垫'。"},
                {"issue": "重量偏大不便携", "severity": "low", "frequency": 1,
                 "example": "2.5磅太重了，带去瑜伽馆不方便，适合在家使用。"},
            ],
            "recommendation": "化学气味和表面脱落是材质和工艺问题，需要更换原材料或改进生产流程。出汗打滑需要增加湿态防滑涂层。"
        },
        "phone_stand": {
            "pain_points": [
                {"issue": "不兼容厚手机壳", "severity": "high", "frequency": 2,
                 "example": "带 OtterBox 手机壳放不进支架，每次都要拆壳，非常不方便。应该标注最大壳厚度。"},
                {"issue": "放平板时晃动", "severity": "medium", "frequency": 2,
                 "example": "手机没问题但放 iPad Mini 会晃，底座不够重，应该标注仅限手机使用。"},
                {"issue": "高度调节范围有限", "severity": "low", "frequency": 1,
                 "example": "设计很好但希望能更高一些，调节范围再大点就完美了。"},
                {"issue": "价格偏高", "severity": "low", "frequency": 1,
                 "example": "质量不错但$15感觉有点贵，类似产品$8就能买到。不过做工确实好一些。"},
            ],
            "recommendation": "兼容性是最大痛点，建议扩大支架开合范围或提供不同尺寸版本。平板支撑需要加固底座。"
        },
    }

    _DEMAND_DATA = {
        "wireless_earbuds": {
            "demands": [
                {"demand": "提升产品耐用性（耳塞+充电盒）", "priority": "high", "market_gap": True},
                {"demand": "改善佩戴舒适度（记忆海绵耳塞）", "priority": "high", "market_gap": True},
                {"demand": "提升麦克风通话质量", "priority": "high", "market_gap": True},
                {"demand": "增加蓝牙连接距离", "priority": "medium", "market_gap": False},
                {"demand": "提供个性化EQ调节功能", "priority": "low", "market_gap": False},
            ],
            "unmet_needs": "市场上缺乏同时满足'耐用+舒适+通话清晰'三个条件的平价耳机。大部分竞品在音质上已经足够好，但在耐用性和通话质量上仍有明显短板。"
        },
        "portable_blender": {
            "demands": [
                {"demand": "改进密封设计防止泄漏", "priority": "high", "market_gap": True},
                {"demand": "使用更安全耐用的刀片材料", "priority": "high", "market_gap": True},
                {"demand": "提升电机功率支持冰块搅拌", "priority": "medium", "market_gap": True},
                {"demand": "延长电池续航（至少6杯）", "priority": "medium", "market_gap": False},
                {"demand": "增大容量至500ml+", "priority": "low", "market_gap": False},
            ],
            "unmet_needs": "市场急需一款'不漏+安全+能打冰'的便携榨汁机。现有产品基本都存在密封或动力问题，安全问题更是行业痛点。"
        },
        "led_strip_lights": {
            "demands": [
                {"demand": "解决电源适配器过热问题", "priority": "high", "market_gap": True},
                {"demand": "使用更强粘性的背胶", "priority": "high", "market_gap": True},
                {"demand": "改善颜色准确度校准", "priority": "medium", "market_gap": False},
                {"demand": "优化WiFi连接稳定性", "priority": "medium", "market_gap": False},
                {"demand": "增加音乐律动等氛围功能", "priority": "low", "market_gap": False},
            ],
            "unmet_needs": "用户对'安全+牢固+颜色准'的LED灯带有刚性需求。过热问题虽然发生率低但影响极大，解决后可形成显著竞争优势。"
        },
        "yoga_mat": {
            "demands": [
                {"demand": "消除化学气味（环保材料）", "priority": "high", "market_gap": True},
                {"demand": "提升表面材质耐久性", "priority": "high", "market_gap": True},
                {"demand": "增加湿态防滑性能", "priority": "medium", "market_gap": True},
                {"demand": "减轻重量方便携带", "priority": "medium", "market_gap": False},
                {"demand": "增加更多图案和配色", "priority": "low", "market_gap": False},
            ],
            "unmet_needs": "环保无味+耐用不脱皮+湿态防滑的瑜伽垫在市场上几乎空白。用户愿意为环保和品质付溢价。"
        },
        "phone_stand": {
            "demands": [
                {"demand": "兼容厚手机壳（加大开合范围）", "priority": "high", "market_gap": True},
                {"demand": "加固底座支持平板", "priority": "medium", "market_gap": True},
                {"demand": "增加高度和角度调节范围", "priority": "medium", "market_gap": False},
                {"demand": "增加折叠便携设计", "priority": "low", "market_gap": False},
            ],
            "unmet_needs": "市场需要一款'手机+平板通用'的支架，兼容厚壳且稳固不晃。现有产品普遍只针对裸机设计。"
        },
    }

    _REPORT_DATA = {
        "wireless_earbuds": """
# 无线蓝牙耳机 — 跨境电商选品分析报告

## 一、市场概况
- **品类**：无线蓝牙耳机（Wireless Bluetooth Earbuds）
- **平台**：Amazon
- **平均评分**：3.8/5.0
- **评论样本**：25条
- **价格区间**：$15-45
- **竞争程度**：★★★★☆（高度竞争，但差异化空间存在）

## 二、用户情感分析

| 指标 | 占比 |
|------|------|
| 正面评价 | 40% |
| 中性评价 | 30% |
| 负面评价 | 30% |

**正面关键词**：sound quality（音质好）、comfortable（舒适）、noise cancellation（降噪）、value（性价比）、battery life（续航）

**负面关键词**：broke（易坏）、uncomfortable（不舒服）、Bluetooth range（蓝牙距离）、microphone（麦克风差）、charging case（充电盒质量差）

**总结**：用户对音质和性价比认可度较高，但产品耐用性和麦克风质量是主要槽点。口碑两极分化，运动场景好评率明显高于通话场景。

## 三、核心痛点

| # | 痛点 | 严重程度 | 出现频次 |
|---|------|----------|----------|
| 1 | 产品耐用性差，短期内损坏 | 🔴 高 | 4次 |
| 2 | 佩戴舒适度不足 | 🔴 高 | 3次 |
| 3 | 麦克风通话质量极差 | 🔴 高 | 2次 |
| 4 | 充电盒质量低劣 | 🟡 中 | 2次 |
| 5 | 蓝牙连接距离有限 | 🟡 中 | 2次 |

> "左耳耳机2周后无法充电，联系卖家无回复，浪费钱。"

**改进建议**：建议优先解决产品耐用性问题（耳塞和充电盒），其次是佩戴舒适度（更换耳塞材质）和麦克风质量。这三个问题占据了80%的差评原因。

## 四、未满足需求

| # | 需求 | 优先级 | 市场缺口 |
|---|------|--------|----------|
| 1 | 提升产品耐用性（耳塞+充电盒） | 高 | ✅ 存在 |
| 2 | 改善佩戴舒适度（记忆海绵耳塞） | 高 | ✅ 存在 |
| 3 | 提升麦克风通话质量 | 高 | ✅ 存在 |
| 4 | 增加蓝牙连接距离 | 中 | ❌ 已满足 |
| 5 | 提供个性化EQ调节功能 | 低 | ❌ 已满足 |

**市场机会**：市场上缺乏同时满足"耐用+舒适+通话清晰"三个条件的平价耳机。大部分竞品在音质上已经足够好，但在耐用性和通话质量上仍有明显短板。

## 五、选品建议

1. **推荐指数**：★★★☆☆（中等推荐）
2. **差异化方向**：主打"耐用+舒适+清晰通话"三大卖点，与竞品形成差异
3. **定价策略**：中端价位 $25-35，强调综合性价比而非最低价
4. **目标人群**：上班族（通话需求）+ 健身人群（舒适+防水）
5. **风险提示**：
   - 供应链质量控制是核心，耳塞和充电盒的材质必须严格把关
   - 麦克风方案选型需要投入测试成本
   - 市场竞争激烈，需要在营销上突出差异化卖点
""",
        "portable_blender": """
# 便携式榨汁机 — 跨境电商选品分析报告

## 一、市场概况
- **品类**：便携式榨汁机（Portable Blender）
- **平台**：Amazon
- **平均评分**：3.5/5.0
- **评论样本**：20条
- **价格区间**：$20-40
- **竞争程度**：★★★☆☆（中等竞争，产品同质化严重）

## 二、用户情感分析

| 指标 | 占比 |
|------|------|
| 正面评价 | 38% |
| 中性评价 | 13% |
| 负面评价 | 50% |

**正面关键词**：smoothies（好做奶昔）、portable（便携）、easy to clean（易清洗）、compact（小巧）、baby food（辅食）

**负面关键词**：leaked（泄漏）、weak motor（电机弱）、battery（电池差）、blade broke（刀片破裂）、cheap（廉价）

**总结**：便携性和易清洗是最大卖点，但密封性和电机动力不足引发大量投诉。产品安全性（刀片破裂）是严重隐患，50%差评率表明产品质量需要大幅提升。

## 三、核心痛点

| # | 痛点 | 严重程度 | 出现频次 |
|---|------|----------|----------|
| 1 | 密封性差导致液体泄漏 | 🔴 高 | 3次 |
| 2 | 刀片组件破裂（安全隐患） | 🔴 高 | 2次 |
| 3 | 电机动力不足 | 🟡 中 | 3次 |
| 4 | 电池续航太短 | 🟡 中 | 2次 |
| 5 | 容量偏小 | 🟢 低 | 1次 |

> "第一次使用 smoothie 就漏满了整个包，盖子根本锁不紧，立即退货。"

**改进建议**：密封性和刀片安全性是必须优先解决的致命问题，直接影响用户安全和基本使用。电机动力和电池续航是第二优先级。

## 四、未满足需求

| # | 需求 | 优先级 | 市场缺口 |
|---|------|--------|----------|
| 1 | 改进密封设计防止泄漏 | 高 | ✅ 存在 |
| 2 | 使用更安全耐用的刀片材料 | 高 | ✅ 存在 |
| 3 | 提升电机功率支持冰块搅拌 | 中 | ✅ 存在 |
| 4 | 延长电池续航（至少6杯） | 中 | ❌ 已满足 |
| 5 | 增大容量至500ml+ | 低 | ❌ 已满足 |

**市场机会**：市场急需一款"不漏+安全+能打冰"的便携榨汁机。现有产品基本都存在密封或动力问题，安全问题更是行业痛点。

## 五、选品建议

1. **推荐指数**：★★☆☆☆（谨慎推荐）
2. **差异化方向**：主打"防漏+安全刀片+强动力"三重保障
3. **定价策略**：$25-35，中高端定位，强调安全和品质
4. **目标人群**：健身人群（蛋白奶昔）、宝妈（婴儿辅食）、上班族（早餐代餐）
5. **风险提示**：
   - 密封和刀片问题如果不能彻底解决，不建议进入此品类
   - 电池和电机方案需要经过严格的可靠性测试
   - 差评率高达50%，说明市场对现有产品非常不满，是机会也是挑战
""",
        "led_strip_lights": """
# LED 灯带 — 跨境电商选品分析报告

## 一、市场概况
- **品类**：LED 灯带（LED Strip Lights）
- **平台**：Amazon
- **平均评分**：4.2/5.0
- **评论样本**：20条
- **价格区间**：$10-25
- **竞争程度**：★★★☆☆（竞争激烈但利润率可观）

## 二、用户情感分析

| 指标 | 占比 |
|------|------|
| 正面评价 | 63% |
| 中性评价 | 13% |
| 负面评价 | 25% |

**正面关键词**：ambiance（氛围感）、easy installation（安装简单）、color options（颜色丰富）、value（性价比）、app control（APP控制）

**负面关键词**：adhesive（背胶差）、colors don't match（颜色偏差）、WiFi issues（WiFi问题）、overheated（过热）、fire hazard（火灾隐患）

**总结**：用户对灯光效果和安装便捷性满意度很高，性价比突出。但粘贴力不足、颜色偏差和WiFi连接不稳定是常见问题。安全问题（过热）虽然频次低但严重程度高。

## 三、核心痛点

| # | 痛点 | 严重程度 | 出现频次 |
|---|------|----------|----------|
| 1 | 电源适配器过热（火灾隐患） | 🔴 高 | 2次 |
| 2 | 粘贴背胶不牢固 | 🟡 中 | 3次 |
| 3 | 颜色与APP显示不一致 | 🟡 中 | 2次 |
| 4 | WiFi连接不稳定 | 🟢 低 | 2次 |

> "运行4小时后电源适配器烫得无法触摸，闻到烧焦味，立即拔掉。这是安全隐患。"

**改进建议**：过热安全问题必须立即解决（可能涉及电源适配器规格升级）。背胶质量需要提升（建议改用3M胶或增加安装夹）。颜色校准和WiFi稳定性也需要优化。

## 四、未满足需求

| # | 需求 | 优先级 | 市场缺口 |
|---|------|--------|----------|
| 1 | 解决电源适配器过热问题 | 高 | ✅ 存在 |
| 2 | 使用更强粘性的背胶 | 高 | ✅ 存在 |
| 3 | 改善颜色准确度校准 | 中 | ❌ 已满足 |
| 4 | 优化WiFi连接稳定性 | 中 | ❌ 已满足 |
| 5 | 增加音乐律动等氛围功能 | 低 | ❌ 已满足 |

**市场机会**：用户对"安全+牢固+颜色准"的LED灯带有刚性需求。过热问题虽然发生率低但影响极大，解决后可形成显著竞争优势。

## 五、选品建议

1. **推荐指数**：★★★★☆（推荐进入）
2. **差异化方向**：主打"安全不发热+强粘胶+颜色精准"三大卖点
3. **定价策略**：$12-18，保持高性价比同时体现品质差异
4. **目标人群**：游戏玩家（桌面氛围）、租房族（房间装饰）、影视爱好者（电视背光）
5. **风险提示**：
   - 电源适配器安全认证（UL/CE）是必须的
   - 背胶质量直接影响退货率
   - 颜色校准需要投入研发成本
""",
        "yoga_mat": """
# 瑜伽垫 — 跨境电商选品分析报告

## 一、市场概况
- **品类**：瑜伽垫（Yoga Mat）
- **平台**：Amazon
- **平均评分**：4.0/5.0
- **评论样本**：20条
- **价格区间**：$18-35
- **竞争程度**：★★★☆☆（中等竞争，品牌忠诚度高）

## 二、用户情感分析

| 指标 | 占比 |
|------|------|
| 正面评价 | 50% |
| 中性评价 | 25% |
| 负面评价 | 25% |

**正面关键词**：thickness（厚度好）、grip（防滑）、durable（耐用）、beautiful design（图案好看）、alignment marks（对齐线）

**负面关键词**：chemical smell（化学味）、peeling（脱落）、slippery when sweaty（出汗打滑）、heavy（太重）、poor quality（质量差）

**总结**：防滑性和厚度获得好评，图案设计也是加分项。但化学气味和表面脱落是两个最突出的负面反馈。出汗后防滑性能下降，不适合高温瑜伽。

## 三、核心痛点

| # | 痛点 | 严重程度 | 出现频次 |
|---|------|----------|----------|
| 1 | 强烈的化学气味 | 🔴 高 | 3次 |
| 2 | 表面材质脱落 | 🔴 高 | 2次 |
| 3 | 出汗后打滑 | 🟡 中 | 2次 |
| 4 | 重量偏大不便携 | 🟢 低 | 1次 |

> "垫子有严重的化学气味，通风两周后仍未消散，练习时头痛。质量控制不可接受。"

**改进建议**：化学气味和表面脱落是材质和工艺问题，需要更换原材料或改进生产流程。出汗打滑需要增加湿态防滑涂层。

## 四、未满足需求

| # | 需求 | 优先级 | 市场缺口 |
|---|------|--------|----------|
| 1 | 消除化学气味（环保材料） | 高 | ✅ 存在 |
| 2 | 提升表面材质耐久性 | 高 | ✅ 存在 |
| 3 | 增加湿态防滑性能 | 中 | ✅ 存在 |
| 4 | 减轻重量方便携带 | 中 | ❌ 已满足 |
| 5 | 增加更多图案和配色 | 低 | ❌ 已满足 |

**市场机会**：环保无味+耐用不脱皮+湿态防滑的瑜伽垫在市场上几乎空白。用户愿意为环保和品质付溢价。

## 五、选品建议

1. **推荐指数**：★★★☆☆（中等推荐）
2. **差异化方向**：主打"环保无味+耐用不脱皮+湿态防滑"
3. **定价策略**：$22-30，中高端定位，强调环保和品质
4. **目标人群**：瑜伽爱好者、健身人群、环保意识消费者
5. **风险提示**：
   - 环保材料成本较高，需要平衡价格和利润
   - 湿态防滑涂层技术门槛较高
   - 品牌忠诚度在此品类中较高，新进入者需要差异化营销
""",
        "phone_stand": """
# 手机支架 — 跨境电商选品分析报告

## 一、市场概况
- **品类**：手机支架（Phone Stand）
- **平台**：Amazon
- **平均评分**：4.3/5.0
- **评论样本**：15条
- **价格区间**：$8-20
- **竞争程度**：★★★★☆（高度竞争，产品差异小）

## 二、用户情感分析

| 指标 | 占比 |
|------|------|
| 正面评价 | 71% |
| 中性评价 | 14% |
| 负面评价 | 14% |

**正面关键词**：sturdy（结实）、adjustable（可调）、minimalist design（简约设计）、video calls（视频通话）、portable（便携）

**负面关键词**：not compatible（不兼容）、wobbles with tablet（平板晃动）、expensive（太贵）、thick cases（厚壳不兼容）

**总结**：做工扎实、设计简约、角度可调是核心优势，视频通话场景表现优秀。但对厚手机壳和平板的兼容性不足，部分用户认为定价偏高。

## 三、核心痛点

| # | 痛点 | 严重程度 | 出现频次 |
|---|------|----------|----------|
| 1 | 不兼容厚手机壳 | 🔴 高 | 2次 |
| 2 | 放平板时晃动 | 🟡 中 | 2次 |
| 3 | 高度调节范围有限 | 🟢 低 | 1次 |
| 4 | 价格偏高 | 🟢 低 | 1次 |

> "带 OtterBox 手机壳放不进支架，每次都要拆壳，非常不方便。应该标注最大壳厚度。"

**改进建议**：兼容性是最大痛点，建议扩大支架开合范围或提供不同尺寸版本。平板支撑需要加固底座。

## 四、未满足需求

| # | 需求 | 优先级 | 市场缺口 |
|---|------|--------|----------|
| 1 | 兼容厚手机壳（加大开合范围） | 高 | ✅ 存在 |
| 2 | 加固底座支持平板 | 中 | ✅ 存在 |
| 3 | 增加高度和角度调节范围 | 中 | ❌ 已满足 |
| 4 | 增加折叠便携设计 | 低 | ❌ 已满足 |

**市场机会**：市场需要一款"手机+平板通用"的支架，兼容厚壳且稳固不晃。现有产品普遍只针对裸机设计。

## 五、选品建议

1. **推荐指数**：★★★★☆（推荐进入）
2. **差异化方向**：主打"厚壳兼容+手机平板通用+稳固不晃"
3. **定价策略**：$10-15，保持性价比优势
4. **目标人群**：上班族（视频通话）、学生（网课）、内容创作者（拍摄支架）
5. **风险提示**：
   - 兼容厚壳需要更大的模具开合范围，可能增加成本
   - 平板支撑需要加固底座，会增加重量
   - 市场上同类产品众多，需要在营销上突出差异化
""",
    }

    def _mock_sentiment_analysis(self, text: str, category: str = "") -> str:
        """模拟情感分析结果（按品类差异化）"""
        data = self._SENTIMENT_DATA.get(category, self._SENTIMENT_DATA["wireless_earbuds"])
        return json.dumps({
            "overall_sentiment": data["overall_sentiment"],
            "positive_ratio": 0.55,  # 会被 analyzer 用实际评分覆盖
            "negative_ratio": 0.30,
            "neutral_ratio": 0.15,
            "positive_keywords": data["positive_keywords"],
            "negative_keywords": data["negative_keywords"],
            "summary": data["summary"],
        }, ensure_ascii=False, indent=2)

    def _mock_pain_point_analysis(self, text: str, category: str = "") -> str:
        """模拟痛点分析结果（按品类差异化）"""
        data = self._PAIN_POINT_DATA.get(category, self._PAIN_POINT_DATA["wireless_earbuds"])
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _mock_demand_analysis(self, text: str, category: str = "") -> str:
        """模拟需求分析结果（按品类差异化）"""
        data = self._DEMAND_DATA.get(category, self._DEMAND_DATA["wireless_earbuds"])
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _mock_report(self, text: str, category: str = "") -> str:
        """模拟选品报告（按品类差异化）"""
        return self._REPORT_DATA.get(category, self._REPORT_DATA["wireless_earbuds"])


# 单例
_client = None

def get_client() -> QwenClient:
    """获取 QwenClient 单例"""
    global _client
    if _client is None:
        _client = QwenClient()
    return _client
