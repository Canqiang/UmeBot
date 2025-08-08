# backend/app/llm_service.py
"""
优化后的LLM服务 - 更智能的响应生成
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from openai import AzureOpenAI
from decimal import Decimal

from app.config import settings
from app.utils import get_weather_summary

logger = logging.getLogger(__name__)


def convert_decimal_to_str(obj):
    """递归转换Decimal类型为字符串"""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimal_to_str(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimal_to_str(item) for item in obj]
    else:
        return obj


class LLMService:
    """增强版LLM服务 - 更智能的意图识别和响应生成"""

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.OPENAI_API_KEY,
            azure_endpoint=settings.OPENAI_BASE_URL,
            api_version=settings.OPENAI_API_VERSION
        )
        self.model = settings.OPENAI_MODEL

    async def parse_query_intent(self, query: str) -> Dict[str, Any]:
        """使用LLM进行意图识别"""
        try:
            # 获取当前时间和天气信息
            time_weather = get_weather_summary(40.71, -74.01, timezone="America/New_York")

            prompt = f"""
            分析用户查询的意图并提取关键信息。

            当前环境信息：
            {time_weather}

            用户查询：{query}

            请返回JSON格式的意图分析结果，包含以下字段：
            - intent_type: 意图类型，可选值：
              * forecast: 预测类查询
              * data_query: 数据查询（查看具体数据）
              * analysis: 分析类查询（因果分析、趋势分析等）
              * daily_report: 日报类查询
              * recommendation: 建议类查询
              * general: 一般对话
            - entities: 提取的实体信息，如：
              * time_range: 时间范围
              * metrics: 涉及的指标
              * dimensions: 维度（如产品、客户等）
              * query_target: 查询目标
            - needs_data: 是否需要查询数据（布尔值）
            - confidence: 置信度（0-1）
            - query: 清理后的查询语句
            - parameters: 其他参数

            示例：
            - "预测明天的销售" -> intent_type: "forecast", time_range: "明天"
            - "为什么今天销售下降" -> intent_type: "analysis", time_range: "今天"
            - "查看本周订单数" -> intent_type: "data_query", time_range: "本周", metrics: ["订单数"]
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            intent = json.loads(response.choices[0].message.content)
            logger.info(f"LLM意图识别结果: {intent}")
            return intent

        except Exception as e:
            logger.error(f"LLM意图识别失败: {e}")
            # 返回默认意图
            return {
                "intent_type": "general",
                "entities": {},
                "needs_data": False,
                "confidence": 0.0,
                "query": query
            }

    async def generate_response(self,
                                user_message: str,
                                data: Optional[Dict[str, Any]] = None,
                                history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """生成智能响应 - 充分利用LLM能力"""

        # 解析意图
        intent = await self.parse_query_intent(user_message)

        # 构建增强的系统提示词
        system_prompt = self._build_enhanced_system_prompt()

        # 准备数据上下文
        data_context = self._prepare_data_context(data, intent) if data else None

        # 使用LLM生成响应
        try:
            messages = [
                {"role": "system", "content": system_prompt}
            ]

            # 添加历史对话（只保留最近5条）
            if history:
                for msg in history[-5:]:
                    messages.append({
                        "role": "user" if msg["role"] == "user" else "assistant",
                        "content": msg["content"]
                    })

            # 构建当前消息
            current_message = self._build_current_message(user_message, data_context, intent)
            messages.append({"role": "user", "content": current_message})

            # 调用LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2048
            )

            # 解析响应
            bot_message = response.choices[0].message.content

            # 根据意图类型包装数据
            response_data = self._wrap_response_data(data, intent) if data else None

            return {
                "message": bot_message,
                "data": response_data,
                "intent": intent
            }

        except Exception as e:
            logger.error(f"LLM响应生成失败: {e}")
            return self._generate_fallback_response(user_message, data, intent)

    def _build_enhanced_system_prompt(self) -> str:
        """构建增强的系统提示词"""
        time_weather = get_weather_summary(40.71, -74.01, timezone="America/New_York")

        return f"""
        你是UMe数据助手，一个专业的零售数据分析AI助理。你的目标是帮助商家理解数据、发现洞察、优化运营。

        当前环境信息：
        {time_weather}

        促销信息：7月29到7月31日，Ume-Tea商家开始售卖代金券，面额100美元

        ## 你的核心能力：
        1. **数据分析**：深入分析销售数据，发现趋势和模式
        2. **因果推理**：识别影响业务的关键因素
        3. **预测建模**：基于历史数据预测未来趋势
        4. **智能建议**：提供可操作的优化建议
        5. **自然对话**：用简单易懂的语言解释复杂数据

        ## 回答原则：
        1. **数据驱动**：所有结论都基于实际数据
        2. **洞察优先**：不只是展示数据，要提供洞察
        3. **行动导向**：每个分析都要有可执行的建议
        4. **简洁明了**：避免冗长，突出重点
        5. **情境感知**：考虑时间、天气、节假日等因素

        ## 因果分析框架：
        当分析销售波动时，考虑以下因素及其影响：

        ### 主效应（平均影响）：
        - 周末效应：+$2,088
        - 节假日效应：+$369
        - 促销效应：+$193
        - 高温天气：+$23
        - 雨天：-$118

        ### 交互效应（组合影响）：
        - 周末 + 促销：额外+$765
        - 高温 + 促销：额外-$1,426
        - 雨天 + 促销：额外-$448

        ## 回答格式指南：

        ### 对于数据查询：
        - 先给出核心数字
        - 解释数据含义
        - 提供对比或趋势
        - 给出优化建议

        ### 对于预测请求：
        - 说明预测结果
        - 解释预测依据
        - 指出关键假设
        - 提供置信区间

        ### 对于分析请求：
        - 识别关键发现
        - 解释因果关系
        - 量化影响程度
        - 提供改进方案

        ## 语言风格：
        - 专业但友好
        - 使用数据支撑观点
        - 适当使用emoji增加可读性
        - 分点说明，结构清晰
        - 避免过度技术化的术语

        记住：你的目标是让商家能够快速理解数据、做出决策、改善业绩。
        """

    def _prepare_data_context(self, data: Dict[str, Any], intent: Dict[str, Any]) -> str:
        """准备数据上下文"""
        if not data:
            return ""

        # 转换Decimal类型
        data = convert_decimal_to_str(data)

        context_parts = []

        # 根据意图类型准备不同的上下文
        if intent["intent_type"] == "forecast":
            if "forecast" in data:
                context_parts.append(f"预测数据：{json.dumps(data['forecast'], ensure_ascii=False)}")
            if "chart_data" in data:
                context_parts.append(f"历史趋势：最近7天平均销售${data.get('avg_sales', 0):.2f}")

        elif intent["intent_type"] == "analysis":
            if "causal_effects" in data:
                context_parts.append(f"因果分析结果：{json.dumps(data['causal_effects'], ensure_ascii=False)}")
            if "trends" in data:
                context_parts.append(f"趋势分析：{json.dumps(data['trends'], ensure_ascii=False)}")

        elif intent["intent_type"] == "data_query":
            # 提取关键指标
            metrics = {}
            for key in ["total_revenue", "total_orders", "unique_customers", "avg_order_value"]:
                if key in data:
                    metrics[key] = data[key]
            if metrics:
                context_parts.append(f"查询结果：{json.dumps(metrics, ensure_ascii=False)}")

            # 添加额外数据
            if "additional_data" in data:
                context_parts.append(f"详细数据：{json.dumps(data['additional_data'], ensure_ascii=False)}")

        return "\n".join(context_parts)

    def _build_current_message(self, user_message: str, data_context: str, intent: Dict[str, Any]) -> str:
        """构建当前消息"""
        message_parts = [f"用户问题：{user_message}"]

        if data_context:
            message_parts.append(f"\n相关数据：\n{data_context}")

        message_parts.append(f"\n意图类型：{intent['intent_type']}")

        # 添加特定指令
        if intent["intent_type"] == "forecast":
            message_parts.append("\n请基于数据生成销售预测分析，包括：预测结果解读、关键假设、风险提示、优化建议。")
        elif intent["intent_type"] == "analysis":
            message_parts.append("\n请进行深度分析，识别关键影响因素，量化各因素的影响程度，并提供具体的改进建议。")
        elif intent["intent_type"] == "data_query":
            message_parts.append("\n请清晰展示查询结果，解释数据含义，提供相关洞察和建议。")
        else:
            message_parts.append("\n请提供专业、有洞察力的回答，确保内容对商家决策有帮助。")

        return "\n".join(message_parts)

    def _wrap_response_data(self, data: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图类型包装响应数据"""
        if not data:
            return None

        # 根据意图类型确定展示类型
        display_type_map = {
            "forecast": "forecast",
            "analysis": "causal_analysis",
            "data_query": "metrics_cards",
            "daily_report": "daily_report"
        }

        display_type = display_type_map.get(intent["intent_type"], "general")

        return {
            "type": display_type,
            "content": data,
            "display_type": display_type
        }

    def _generate_fallback_response(self, user_message: str, data: Optional[Dict[str, Any]], intent: Dict[str, Any]) -> \
    Dict[str, Any]:
        """生成降级响应"""
        fallback_messages = {
            "forecast": "正在为您生成销售预测，这可能需要几秒钟...",
            "analysis": "正在分析数据中，马上为您呈现结果...",
            "data_query": "正在查询数据，请稍候...",
            "daily_report": "正在生成今日报告...",
            "general": """我理解您的问题。让我为您提供一些帮助：
            
            如果您想要：
            • 📈 预测销售：可以说"预测未来7天的销售"
            • 📊 查询数据：可以说"查询总用户数"或"今天的订单数"
            • 📉 分析趋势：可以说"分析本周销售趋势"
            • 📋 查看报告：可以说"显示今日数据报告"
            
            请问您具体想了解什么？"""
        }

        return {
            "message": fallback_messages.get(intent["intent_type"], fallback_messages["general"]),
            "data": self._wrap_response_data(data, intent) if data else None,
            "intent": intent
        }

    async def generate_smart_insights(self, data: Dict[str, Any]) -> List[str]:
        """生成智能洞察 - 使用LLM分析数据模式"""
        try:
            data_str = json.dumps(convert_decimal_to_str(data), ensure_ascii=False)

            prompt = f"""
            基于以下数据，生成3-5个关键业务洞察：

            数据：{data_str}

            要求：
            1. 每个洞察都要有数据支撑
            2. 突出异常和机会
            3. 提供可执行的建议
            4. 用简洁的语言表达

            返回JSON格式：{{"insights": ["洞察1", "洞察2", ...]}}
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个数据分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("insights", [])

        except Exception as e:
            logger.error(f"生成洞察失败: {e}")
            return []

    async def generate_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成智能建议 - 基于分析结果"""
        try:
            data_str = json.dumps(convert_decimal_to_str(analysis_results), ensure_ascii=False)

            prompt = f"""
            基于以下分析结果，生成具体的业务优化建议：

            分析结果：{data_str}

            要求：
            1. 每个建议都要具体可执行
            2. 包含预期效果
            3. 标明优先级（高/中/低）
            4. 考虑实施难度

            返回JSON格式：
            {{
                "recommendations": [
                    {{
                        "title": "建议标题",
                        "description": "具体描述",
                        "expected_impact": "预期效果",
                        "priority": "高/中/低",
                        "difficulty": "易/中/难"
                    }}
                ]
            }}
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个零售业务顾问。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("recommendations", [])

        except Exception as e:
            logger.error(f"生成建议失败: {e}")
            return []