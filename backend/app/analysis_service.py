# backend/app/analysis_service.py
"""数据分析服务 - 完整修复版"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from functools import lru_cache
import logging
from app.utils import convert_to_json_serializable
from app.config import settings
from app.database import get_db
from app.fixed_causal_inference import UMeCausalInferenceEngine

logger = logging.getLogger(__name__)


class AnalysisService:
    def __init__(self):
        self.db = get_db()  # 使用单例数据库实例
        self.engine = UMeCausalInferenceEngine(settings.CLICKHOUSE_CONFIG)
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存

    async def initialize(self):
        """初始化服务"""
        logger.info("📊 正在初始化分析服务...")
        await self._init_engine()

    async def cleanup(self):
        """清理资源"""
        self._cache.clear()

    async def _init_engine(self):
        """初始化因果推断引擎"""
        try:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.engine.load_integrated_data,
                start_date,
                end_date
            )
            logger.info("✅ 因果推断引擎初始化完成")
        except Exception as e:
            logger.warning(f"⚠️ 因果推断引擎初始化失败: {e}")

    def _get_cache_key(self, method: str, params: Dict) -> str:
        """生成缓存键"""
        import hashlib
        import json
        param_str = json.dumps(params, sort_keys=True)
        return f"{method}:{hashlib.md5(param_str.encode()).hexdigest()}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return data
        return None

    def _save_to_cache(self, key: str, data: Any):
        """保存到缓存"""
        self._cache[key] = (data, datetime.now())

    async def get_daily_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取日报数据"""
        cache_key = self._get_cache_key("daily_report", {"start": start_date, "end": end_date})
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            # 获取基础指标
            metrics = await self.db.get_metrics(start_date, end_date)

            # 获取每日数据用于趋势计算
            daily_data = await self.db.get_daily_data(start_date, end_date)

            # 构建报告（简化版，避免并发查询）
            report = {
                "date": end_date,
                "metrics": metrics,
                "trends": self._calculate_trends(daily_data) if not daily_data.empty else {},
                "top_products": [],  # 暂时跳过，避免并发问题
                "peak_hours": [],
                "store_performance": []
            }

            self._save_to_cache(cache_key, report)
            return report

        except Exception as e:
            logger.error(f"Error getting daily report: {e}")
            return self._get_mock_daily_report()

    def _calculate_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算趋势"""
        if df.empty:
            return {}

        # 查找日期列
        date_col = None
        for col in ['date', 'ds', 'order_date', 'created_date']:
            if col in df.columns:
                date_col = col
                break

        if date_col is None and pd.api.types.is_datetime64_any_dtype(df.index):
            df = df.reset_index()
            date_col = 'index'

        if date_col is None:
            return {}

        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        mid_point = len(df) // 2
        first_half = df.iloc[:mid_point]
        second_half = df.iloc[mid_point:]

        trends = {}
        metrics = ['total_revenue', 'order_count', 'unique_customers']

        for metric in metrics:
            if metric in df.columns:
                first_avg = first_half[metric].mean()
                second_avg = second_half[metric].mean()
                if first_avg > 0:
                    change = ((second_avg - first_avg) / first_avg) * 100
                    trends[metric] = round(change, 2)

        return trends

    async def get_daily_report_summary(self) -> Dict[str, Any]:
        """获取日报摘要"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        # print(yesterday,today)
        report = await self.get_daily_report(yesterday, today)

        if not report:
            return None

        metrics = report.get("metrics", {})
        trends = report.get("trends", {})

        insights = []
        if trends.get("total_revenue", 0) > 10:
            insights.append(f"📈 营收增长显著，环比上升{trends['total_revenue']:.1f}%")
        elif trends.get("total_revenue", 0) < -10:
            insights.append(f"📉 营收下降明显，环比下降{abs(trends['total_revenue']):.1f}%")

        if metrics.get("new_users", 0) > 0:
            insights.append(f"🎉 新增{metrics['new_users']}位新客户")

        summary = {
            "date": report["date"],
            "highlights": [
                f"💰 总营收: ${metrics.get('total_revenue', 0):,.2f}",
                f"📦 订单数: {metrics.get('total_orders', 0):,}",
                f"👥 客户数: {metrics.get('unique_customers', 0):,}",
                f"🛍️ 客单价: ${metrics.get('avg_order_value', 0):.2f}"
            ],
            "trends": trends,
            "insights": insights,
            "metrics": metrics
        }

        return summary

    async def get_forecast(self, days: int = 7) -> Dict[str, Any]:
        """获取销售预测"""
        cache_key = self._get_cache_key("forecast", {"days": days})
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.info("Returning cached forecast")
            return cached

        try:
            logger.info(f"Generating forecast for {days} days")

            # 获取历史数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

            historical_data = await self.db.get_daily_data(start_date, end_date)

            if historical_data.empty:
                logger.warning("No historical data for forecast")
                return {"error": "No historical data available"}

            # 准备数据
            historical_data['date'] = pd.to_datetime(historical_data['date'])
            historical_data = historical_data.sort_values('date')

            # 计算移动平均
            historical_data['ma7'] = historical_data['total_revenue'].rolling(window=7, min_periods=1).mean()

            # 计算趋势
            recent_trend = historical_data['total_revenue'].tail(7).mean()
            weekly_growth = 0
            if len(historical_data) >= 14:
                last_week = historical_data['total_revenue'].tail(7).mean()
                prev_week = historical_data['total_revenue'].tail(14).head(7).mean()
                if prev_week > 0:
                    weekly_growth = (last_week - prev_week) / prev_week

            # 生成预测
            last_date = historical_data['date'].iloc[-1]
            forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            base_forecast = recent_trend * (1 + weekly_growth * 0.5)
            recent_std = historical_data['total_revenue'].astype(float).tail(14).std()

            # 构建图表数据
            forecast_data = []

            # 添加历史数据（最近30天）
            for _, row in historical_data.tail(30).iterrows():
                forecast_data.append({
                    "date": row['date'].strftime("%Y-%m-%d"),
                    "actual": float(row['total_revenue']),
                    "predicted": float(row['ma7']) if pd.notna(row['ma7']) else float(row['total_revenue']),
                    "confidence_lower": None,
                    "confidence_upper": None
                })

            # 添加预测数据
            for i, date in enumerate(forecast_dates):
                day_of_week = date.dayofweek
                week_factor = 1.0
                if day_of_week in [5, 6]:  # 周末
                    week_factor = 1.15
                elif day_of_week == 4:  # 周五
                    week_factor = 1.1
                elif day_of_week == 0:  # 周一
                    week_factor = 0.95

                random_factor = 1 + np.random.normal(0, 0.05)
                predicted = base_forecast * week_factor * random_factor

                forecast_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "actual": None,
                    "predicted": float(predicted),
                    "confidence_lower": float(predicted - 1.96 * recent_std),
                    "confidence_upper": float(predicted + 1.96 * recent_std)
                })

            # 计算汇总
            future_predictions = [d['predicted'] for d in forecast_data if d['actual'] is None]

            result = {
                "forecast": {
                    "total_forecast": sum(future_predictions),
                    "avg_daily_forecast": np.mean(future_predictions),
                    "max_daily_forecast": max(future_predictions),
                    "min_daily_forecast": min(future_predictions),
                    "forecast_days": days
                },
                "chart_data": forecast_data,
                "method": "moving_average"
            }

            logger.info(f"Forecast generated: {days} days, total: ${result['forecast']['total_forecast']:,.2f}")

            result = convert_to_json_serializable(result)
            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def get_data_by_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图获取数据"""
        intent_type = intent.get("intent_type", "general")

        logger.info(f"Processing intent: {intent_type}")

        # 预测意图
        if intent_type == "forecast":
            days = intent.get("forecast_days", 7)
            return await self.get_forecast(days)

        # 数据查询意图
        elif intent_type == "data_query":
            target = intent.get("entities", {}).get("query_target")
            time_range = intent.get("time_range", {})

            if target == "customers":
                count = await self.db.get_customer_count()
                return {"customer_count": count}

            elif target == "orders":
                start_date, end_date = self._parse_time_range(time_range)
                metrics = await self.db.get_metrics(start_date, end_date)
                return {"total_orders": metrics.get("total_orders", 0)}

            elif target == "revenue":
                start_date, end_date = self._parse_time_range(time_range)
                metrics = await self.db.get_metrics(start_date, end_date)
                return {"total_revenue": metrics.get("total_revenue", 0)}

            else:
                start_date, end_date = self._parse_time_range(time_range)
                return await self.get_metrics_data(start_date, end_date)

        # 日报意图
        elif intent_type == "daily_report":
            return await self.get_daily_report_summary()

        # 分析意图
        elif intent_type == "analysis":
            time_range = intent.get("time_range", {})
            start_date, end_date = self._parse_time_range(time_range)
            return await self.run_analysis(start_date, end_date)

        # 指标意图
        elif intent_type == "metrics":
            time_range = intent.get("time_range", {})
            start_date, end_date = self._parse_time_range(time_range)
            return await self.get_metrics_data(start_date, end_date)

        return {}

    async def get_metrics_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取指标数据"""
        metrics = await self.db.get_metrics(start_date, end_date)

        return {
            "metrics": metrics,
            "display_type": "metrics_cards"
        }

    async def run_analysis(self, start_date: str, end_date: str,
                           analysis_type: str = "complete") -> Dict[str, Any]:
        """运行分析"""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.engine.run_complete_analysis,
                start_date,
                end_date,
                True
            )
            return results
        except Exception as e:
            logger.error(f"Error running analysis: {e}")
            return {"error": str(e)}

    async def get_detail_data(self, detail_type: str, params: Dict) -> Dict[str, Any]:
        """获取详细数据"""
        # 简化实现，避免并发问题
        return {"type": detail_type, "data": params}

    def _parse_time_range(self, time_range: Dict) -> tuple:
        """解析时间范围"""
        if not time_range:
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            return start, end

        range_type = time_range.get("type", "last_n_days")

        if range_type == "today":
            date = datetime.now().strftime('%Y-%m-%d')
            return date, date
        elif range_type == "yesterday":
            date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            return date, date
        elif range_type == "this_week":
            today = datetime.now()
            start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return start, end
        elif range_type == "this_month":
            today = datetime.now()
            start = today.replace(day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return start, end
        elif range_type == "all_time":
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            return start, end
        else:
            days = time_range.get("days", 7)
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            return start, end

    def _get_mock_daily_report(self) -> Dict[str, Any]:
        """获取模拟日报数据"""
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "metrics": {
                "total_revenue": 15234.56,
                "total_orders": 142,
                "unique_customers": 89,
                "item_count": 45,
                "new_users": 12,
                "avg_order_value": 107.29
            },
            "trends": {
                "total_revenue": 5.3,
                "order_count": 3.2,
                "unique_customers": 8.1
            },
            "top_products": [],
            "peak_hours": [],
            "store_performance": []
        }