# backend/app/llm_service.py
"""
LLM服务 - 修复意图识别，支持预测和数据查询
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
import logging

from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM服务管理"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        self.model = settings.OPENAI_MODEL
    
    async def parse_query_intent(self, query: str) -> Dict[str, Any]:
        """解析用户查询意图（增强版）"""
        query_lower = query.lower()
        
        # 预测相关关键词
        forecast_keywords = ['预测', '预估', '预计', '未来', '明天', '下周', '接下来', 
                           'forecast', 'predict', 'estimate', 'future', 'tomorrow']
        
        # 查询相关关键词
        query_keywords = ['查询', '查', '多少', '几个', '统计', '总共', '目前', '现在',
                         'query', 'how many', 'count', 'total', 'current', 'now']
        
        # 分析相关关键词
        analysis_keywords = ['分析', '因果', '影响', '效果', '趋势', '对比',
                           'analyze', 'analysis', 'effect', 'trend', 'compare']
        
        # 日报相关关键词
        report_keywords = ['日报', '报告', '报表', '概览', '总结', '数据',
                          'report', 'summary', 'overview', 'dashboard']
        
        intent = {
            "query": query,
            "intent_type": "general",
            "needs_data": False,
            "entities": {},
            "time_range": None
        }
        
        # 1. 检测预测意图
        if any(keyword in query_lower for keyword in forecast_keywords):
            intent["intent_type"] = "forecast"
            intent["needs_data"] = True
            
            # 提取预测天数
            days_match = re.search(r'(\d+)[天日]|未来(\d+)', query)
            if days_match:
                days = int(days_match.group(1) or days_match.group(2))
                intent["forecast_days"] = days
            else:
                intent["forecast_days"] = 7  # 默认7天
            
            intent["entities"]["forecast_type"] = "sales"
            logger.info(f"识别为预测意图: {intent['forecast_days']}天")
            return intent
        
        # 2. 检测数据查询意图
        if any(keyword in query_lower for keyword in query_keywords):
            intent["intent_type"] = "data_query"
            intent["needs_data"] = True
            
            # 识别查询目标
            if '用户' in query or '客户' in query or 'customer' in query_lower:
                intent["entities"]["query_target"] = "customers"
                intent["entities"]["metric"] = "total_count"
            elif '订单' in query or 'order' in query_lower:
                intent["entities"]["query_target"] = "orders"
                intent["entities"]["metric"] = "total_count"
            elif '销售' in query or '营收' in query or 'revenue' in query_lower:
                intent["entities"]["query_target"] = "revenue"
                intent["entities"]["metric"] = "total_amount"
            elif '产品' in query or '商品' in query or 'product' in query_lower:
                intent["entities"]["query_target"] = "products"
                intent["entities"]["metric"] = "total_count"
            
            # 时间范围
            if '今天' in query or 'today' in query_lower:
                intent["time_range"] = {"type": "today"}
            elif '昨天' in query or 'yesterday' in query_lower:
                intent["time_range"] = {"type": "yesterday"}
            elif '本周' in query or 'this week' in query_lower:
                intent["time_range"] = {"type": "this_week"}
            elif '本月' in query or 'this month' in query_lower:
                intent["time_range"] = {"type": "this_month"}
            else:
                # 默认查询所有时间
                intent["time_range"] = {"type": "all_time"}
            
            logger.info(f"识别为数据查询意图: {intent['entities']}")
            return intent
        
        # 3. 检测分析意图
        if any(keyword in query_lower for keyword in analysis_keywords):
            intent["intent_type"] = "analysis"
            intent["needs_data"] = True
            
            if '因果' in query or 'causal' in query_lower:
                intent["entities"]["analysis_type"] = "causal"
            elif '趋势' in query or 'trend' in query_lower:
                intent["entities"]["analysis_type"] = "trend"
            else:
                intent["entities"]["analysis_type"] = "general"
            
            logger.info(f"识别为分析意图: {intent['entities']}")
            return intent
        
        # 4. 检测日报意图
        if any(keyword in query_lower for keyword in report_keywords):
            intent["intent_type"] = "daily_report"
            intent["needs_data"] = True
            logger.info("识别为日报意图")
            return intent
        
        # 5. 默认：尝试理解查询
        if '销售' in query or '销量' in query:
            intent["intent_type"] = "metrics"
            intent["needs_data"] = True
            intent["entities"]["focus"] = "sales"
        
        logger.info(f"意图识别结果: {intent}")
        return intent
    
    async def generate_response(self, 
                               user_message: str,
                               data: Optional[Dict[str, Any]] = None,
                               history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """生成回复（增强版）"""
        
        # 解析意图
        intent = await self.parse_query_intent(user_message)
        
        # 根据意图类型生成不同的响应
        if intent["intent_type"] == "forecast":
            return await self._generate_forecast_response(data)
        elif intent["intent_type"] == "data_query":
            return await self._generate_query_response(data, intent)
        elif intent["intent_type"] == "analysis":
            return await self._generate_analysis_response(data)
        elif intent["intent_type"] == "daily_report":
            return await self._generate_report_response(data)
        else:
            return await self._generate_general_response(user_message, data, history)
    
    async def _generate_forecast_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成预测响应"""
        if not data or "error" in data:
            return {
                "message": "正在为您生成销售预测...",
                "data": None
            }
        
        # 提取预测信息
        forecast_summary = data.get("forecast", {})
        chart_data = data.get("chart_data", [])
        
        # 生成描述
        if forecast_summary:
            total = forecast_summary.get("total_forecast", 0)
            avg = forecast_summary.get("avg_daily_forecast", 0)
            days = forecast_summary.get("forecast_days", 7)
            
            message = f"""📈 根据历史数据分析，未来{days}天的销售预测如下：

• **预测总销售额**: ${total:,.2f}
• **日均销售额**: ${avg:,.2f}
• **预测方法**: {data.get('method', '移动平均')}

图表中蓝色线条展示历史实际销售额，绿色虚线展示预测销售额，浅蓝色区域表示置信区间。

💡 **建议**：
- 关注预测中的高峰期，提前准备库存
- 在预测低谷期可以考虑促销活动
- 持续监控实际销售与预测的偏差"""
        else:
            message = "销售预测已生成，请查看图表了解详细趋势。"
        
        return {
            "message": message,
            "data": {
                "type": "forecast",
                "content": data,
                "display_type": "forecast"
            }
        }
    
    async def _generate_query_response(self, data: Dict[str, Any], intent: Dict[str, Any]) -> Dict[str, Any]:
        """生成查询响应"""
        if not data:
            return {
                "message": "正在查询数据...",
                "data": None
            }
        
        target = intent.get("entities", {}).get("query_target", "data")
        
        # 根据查询目标生成响应
        if target == "customers":
            count = data.get("customer_count", data.get("unique_customers", 0))
            message = f"""👥 **客户数据统计**

目前总共有 **{count:,}** 位客户。

这包括所有在系统中有过购买记录的客户。如需了解更详细的客户分群信息，可以问我"分析客户分群"或"显示客户画像"。"""
        
        elif target == "orders":
            count = data.get("total_orders", 0)
            message = f"""📦 **订单数据统计**

目前总共有 **{count:,}** 个订单。

这是所有已完成的订单总数。需要了解更多订单相关信息，可以询问"今日订单情况"或"订单趋势分析"。"""
        
        elif target == "revenue":
            amount = data.get("total_revenue", 0)
            message = f"""💰 **营收数据统计**

总营收为 **${amount:,.2f}**

这是所有已完成订单的总销售额。如需了解营收趋势或详细分析，可以询问"营收趋势"或"销售分析"。"""
        
        else:
            # 通用查询响应
            message = "查询结果如下："
            if isinstance(data, dict):
                for key, value in data.items():
                    if key != "display_type":
                        message += f"\n• {key}: {value}"
        
        return {
            "message": message,
            "data": {
                "type": "metrics_cards",
                "content": {"metrics": data},
                "display_type": "metrics_cards"
            } if data else None
        }
    
    async def _generate_analysis_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成分析响应"""
        if not data:
            return {
                "message": "正在进行数据分析...",
                "data": None
            }
        
        message = """📊 **数据分析完成**

已为您生成详细的分析报告，包括：
• 因果效应分析
• 关键影响因素
• 趋势变化
• 优化建议

请查看下方的分析结果。"""
        
        return {
            "message": message,
            "data": {
                "type": "analysis",
                "content": data,
                "display_type": "causal_analysis"
            }
        }
    
    async def _generate_report_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """生成日报响应"""
        if not data:
            return {
                "message": "正在生成日报...",
                "data": None
            }
        
        return {
            "message": "这是今天的数据概览：",
            "data": {
                "type": "daily_report",
                "content": data,
                "display_type": "daily_report"
            }
        }
    
    async def _generate_general_response(self, 
                                        user_message: str,
                                        data: Optional[Dict[str, Any]] = None,
                                        history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """生成通用响应（使用GPT）"""
        try:
            # 构建上下文
            messages = [
                {
                    "role": "system",
                    "content": """你是UMe智能数据助手，专门帮助用户分析销售数据、预测趋势、提供业务洞察。

你的能力包括：
1. 查询和展示各类业务数据（用户数、订单数、销售额等）
2. 预测未来销售趋势（支持7-30天预测）
3. 分析数据间的因果关系
4. 生成数据报告和可视化图表
5. 提供业务优化建议

回答用户问题时：
- 如果用户询问数据查询，直接给出数据
- 如果用户要求预测，生成预测图表
- 保持专业、友好、简洁
- 使用数据支持你的观点"""
                }
            ]
            
            # 添加历史对话
            if history:
                for msg in history[-5:]:  # 只保留最近5条
                    messages.append({
                        "role": "user" if msg["role"] == "user" else "assistant",
                        "content": msg["content"]
                    })
            
            # 添加当前消息
            current_msg = {"role": "user", "content": user_message}
            if data:
                current_msg["content"] += f"\n\n相关数据：{json.dumps(data, ensure_ascii=False)[:500]}"
            messages.append(current_msg)
            
            # 调用GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )
            
            return {
                "message": response.choices[0].message.content,
                "data": {
                    "type": "general",
                    "content": data
                } if data else None
            }
            
        except Exception as e:
            logger.error(f"GPT response generation failed: {e}")
            
            # 降级响应
            return {
                "message": """我理解您的问题。让我为您提供一些帮助：

如果您想要：
• 📈 预测销售：可以说"预测未来7天的销售"
• 📊 查询数据：可以说"查询总用户数"或"今天的订单数"
• 📉 分析趋势：可以说"分析本周销售趋势"
• 📋 查看报告：可以说"显示今日数据报告"

请问您具体想了解什么？""",
                "data": None
            }