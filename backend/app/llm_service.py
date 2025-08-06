"""
LLM服务
处理自然语言理解和生成
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import re
from openai import AsyncOpenAI
from app.config import settings


class LLMService:
    """LLM服务类"""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.OPENAI_MODEL

        # 系统提示词
        self.system_prompt = """
        你是UMe茶饮的智能数据助手，专门帮助用户分析和理解业务数据。

        你的职责：
        1. 解答关于销售、客户、促销等业务数据的问题
        2. 提供数据洞察和业务建议
        3. 解释因果分析结果
        4. 预测未来趋势

        回答原则：
        1. 基于数据说话，用数字支撑观点
        2. 语言专业但易懂，避免过于技术化
        3. 主动提供可行的业务建议
        4. 适当使用emoji让对话更友好
        5. 结构化展示复杂信息（使用列表、表格等）

        数据说明：
        - 营收数据：日营收、店铺营收、产品类别营收
        - 客户数据：客户画像、忠诚度、消费行为
        - 促销数据：促销效果、ROI分析
        - 因果分析：促销、天气、节假日等因素的因果效应
        - 预测数据：未来7-15天的销售预测
        """

        # 意图识别模板
        self.intent_patterns = {
            "daily_report": ["日报", "今天", "今日", "数据概览", "概览"],
            "sales_analysis": ["销售", "营收", "收入", "销量", "业绩"],
            "customer_analysis": ["客户", "用户", "顾客", "会员", "忠诚度"],
            "promotion_analysis": ["促销", "活动", "优惠", "折扣", "营销"],
            "causal_analysis": ["因果", "影响", "效应", "原因", "为什么"],
            "forecast": ["预测", "预估", "未来", "趋势", "展望"],
            "comparison": ["对比", "比较", "环比", "同比", "差异"],
            "detail": ["详细", "具体", "明细", "详情", "展开"],
            "suggestion": ["建议", "怎么办", "如何", "优化", "改进"]
        }

    async def parse_query_intent(self, query: str) -> Dict[str, Any]:
        """解析用户查询意图"""
        query_lower = query.lower()

        intent = {
            "query": query,
            "intent_type": "general",
            "entities": {},
            "needs_data": False,
            "time_range": self._extract_time_range(query),
            "metrics": self._extract_metrics(query)
        }

        # 识别主要意图
        for intent_type, patterns in self.intent_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                intent["intent_type"] = intent_type
                intent["needs_data"] = True
                break

        # 提取实体
        intent["entities"] = self._extract_entities(query)

        # 使用LLM增强意图理解
        if intent["intent_type"] == "general":
            intent = await self._enhance_intent_with_llm(query, intent)

        return intent

    def _extract_time_range(self, query: str) -> Dict[str, Any]:
        """提取时间范围"""
        time_range = {
            "type": "relative",
            "value": "today"
        }

        query_lower = query.lower()

        # 相对时间
        if "今天" in query or "今日" in query:
            time_range = {"type": "relative", "value": "today"}
        elif "昨天" in query or "昨日" in query:
            time_range = {"type": "relative", "value": "yesterday"}
        elif "本周" in query or "这周" in query:
            time_range = {"type": "relative", "value": "this_week"}
        elif "上周" in query:
            time_range = {"type": "relative", "value": "last_week"}
        elif "本月" in query or "这个月" in query:
            time_range = {"type": "relative", "value": "this_month"}
        elif "上月" in query or "上个月" in query:
            time_range = {"type": "relative", "value": "last_month"}

        # 具体日期（简单正则匹配）
        date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        dates = re.findall(date_pattern, query)
        if dates:
            if len(dates) == 1:
                time_range = {"type": "absolute", "start": dates[0], "end": dates[0]}
            elif len(dates) >= 2:
                time_range = {"type": "absolute", "start": dates[0], "end": dates[1]}

        return time_range

    def _extract_metrics(self, query: str) -> List[str]:
        """提取指标关键词"""
        metrics = []
        query_lower = query.lower()

        metric_keywords = {
            "revenue": ["营收", "收入", "销售额", "流水"],
            "orders": ["订单", "单量", "交易"],
            "customers": ["客户", "用户", "顾客", "客流"],
            "aov": ["客单价", "平均订单", "单价"],
            "conversion": ["转化率", "转化", "成交率"],
            "loyalty": ["忠诚度", "复购", "回购", "留存"]
        }

        for metric, keywords in metric_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                metrics.append(metric)

        return metrics

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """提取实体（店铺、产品等）"""
        entities = {}

        # 店铺提取
        store_pattern = r'(CA|IL|AZ|TX)[-\w]*'
        stores = re.findall(store_pattern, query.upper())
        if stores:
            entities["stores"] = stores

        # 产品类别提取
        categories = ["奶茶", "咖啡", "果茶", "小食", "新品"]
        found_categories = [cat for cat in categories if cat in query]
        if found_categories:
            entities["categories"] = found_categories

        return entities

    async def _enhance_intent_with_llm(self, query: str, initial_intent: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM增强意图理解"""
        try:
            prompt = f"""
            分析用户查询意图：
            查询：{query}

            请识别：
            1. 主要意图类型（daily_report/sales_analysis/customer_analysis/promotion_analysis/causal_analysis/forecast/comparison/suggestion）
            2. 是否需要数据支持
            3. 关注的关键指标

            返回JSON格式。
            """

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个查询意图分析专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )

            # 尝试解析JSON响应
            content = response.choices[0].message.content
            # 简单处理，实际可能需要更复杂的解析
            if "sales_analysis" in content:
                initial_intent["intent_type"] = "sales_analysis"
                initial_intent["needs_data"] = True
            elif "forecast" in content:
                initial_intent["intent_type"] = "forecast"
                initial_intent["needs_data"] = True

        except Exception as e:
            print(f"LLM intent enhancement failed: {e}")

        return initial_intent

    async def generate_response(
            self,
            query: str,
            data: Optional[Dict[str, Any]] = None,
            context: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """生成回复"""

        # 构建消息历史
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]

        # 添加历史上下文
        if context:
            for msg in context[-5:]:  # 最多5条历史
                if msg['role'] not in {"system", "assistant", "user", "function", "tool", "developer"}:
                    msg['role'] = "assistant"
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        # 构建当前查询的上下文
        current_context = f"用户查询：{query}\n"

        if data:
            current_context += "\n相关数据：\n"
            current_context += self._format_data_for_llm(data)

        messages.append({"role": "user", "content": current_context})

        try:
            # 调用LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )

            bot_message = response.choices[0].message.content

            # 构建响应
            result = {
                "message": bot_message,
                "data": None
            }

            # 如果有数据，格式化为前端可用的格式
            if data:
                result["data"] = self._format_data_for_frontend(data)

            return result

        except Exception as e:
            print(f"LLM generation failed: {e}")
            return {
                "message": "抱歉，我遇到了一些问题。请稍后再试。",
                "data": None
            }

    def _format_data_for_llm(self, data: Dict[str, Any]) -> str:
        """格式化数据供LLM理解"""
        formatted = []

        if "metrics" in data:
            formatted.append("📊 关键指标：")
            for key, value in data["metrics"].items():
                formatted.append(f"- {key}: {value}")

        if "analysis" in data:
            formatted.append("\n🎯 分析结果：")
            for key, value in data["analysis"].items():
                if isinstance(value, dict) and "ate" in value:
                    formatted.append(f"- {key}: 效应值={value['ate']:.2f}, 显著性={value.get('significant', False)}")

        if "forecast" in data:
            formatted.append("\n📈 预测数据：")
            forecast = data["forecast"]
            formatted.append(
                f"- 未来{forecast.get('forecast_days', 0)}天总预测: ${forecast.get('total_forecast', 0):,.0f}"
            )
            formatted.append(
                f"- 日均预测: ${forecast.get('avg_daily_forecast', 0):,.0f}"
            )
            method = data.get("method")
            if method:
                formatted.append(f"- 预测方法: {method}")

        return "\n".join(formatted)

    def _format_data_for_frontend(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化数据供前端展示"""
        formatted = {
            "type": "data_display",
            "content": {}
        }

        # 添加所有可用内容
        if "metrics" in data:
            formatted["content"]["metrics"] = data["metrics"]

        if "forecast" in data:
            formatted["content"]["chart"] = data["forecast"]["chart_data"]
            formatted["display_type"] = "chart"

        if "chart_data" in data:
            formatted["content"]["chart"] = data["chart_data"]

        if "table_data" in data:
            formatted["content"]["table"] = data["table_data"]

        if "analysis" in data:
            formatted["content"]["analysis"] = data["analysis"]

        # 按优先级确定展示类型，确保稳定
        type_priority = ["analysis", "chart_data", "table_data", "metrics"]
        type_map = {
            "analysis": lambda: "causal_analysis" if "causal" in str(data.get("analysis_type", "")) else "analysis",
            "chart_data": lambda: "chart",
            "table_data": lambda: "table",
            "metrics": lambda: "metrics_cards",
        }

        for key in type_priority:
            if key in data:
                formatted["display_type"] = type_map[key]()
                break

        return formatted

    async def generate_suggestions(self, analysis_results: Dict[str, Any]) -> List[str]:
        """基于分析结果生成建议"""
        suggestions = []

        prompt = f"""
        基于以下分析结果，生成3-5条具体可行的业务建议：
        {json.dumps(analysis_results, ensure_ascii=False, indent=2)}

        要求：
        1. 每条建议要具体可执行
        2. 包含预期效果
        3. 按优先级排序
        """

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个业务策略专家。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            content = response.choices[0].message.content
            # 解析建议（简单按行分割）
            suggestions = [line.strip() for line in content.split('\n') if line.strip() and not line.startswith('#')]

        except Exception as e:
            print(f"Generate suggestions failed: {e}")
            suggestions = ["建议1: 优化促销策略", "建议2: 关注客户留存", "建议3: 提升运营效率"]

        return suggestions[:5]  # 最多返回5条