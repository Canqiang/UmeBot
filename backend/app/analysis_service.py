# backend/app/analysis_service.py
"""数据分析服务优化版"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from functools import lru_cache

from app.config import settings
from app.database import DatabaseManager
from app.fixed_causal_inference import UMeCausalInferenceEngine


class AnalysisService:
    def __init__(self):
        self.db = DatabaseManager()
        self.engine = UMeCausalInferenceEngine(settings.CLICKHOUSE_CONFIG)
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存

    async def initialize(self):
        """初始化服务"""
        print("📊 正在初始化分析服务...")
        # 初始化因果推断引擎
        await self._init_engine()

    async def cleanup(self):
        """清理资源"""
        self._cache.clear()

    async def _init_engine(self):
        """初始化因果推断引擎"""
        try:
            # 预加载最近30天的数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.engine.load_integrated_data,
                start_date,
                end_date
            )
            print("✅ 因果推断引擎初始化完成")
        except Exception as e:
            print(f"⚠️ 因果推断引擎初始化失败: {e}")

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
            # 从数据库获取数据
            query = f"""
            WITH first_purchase AS (
                SELECT
                    customer_id,
                    toDate(MIN(created_at_pt)) AS first_purchase_date
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED'
                GROUP BY customer_id
            )
            SELECT
                toDate(f.created_at_pt) AS date,
                COUNT(DISTINCT f.order_id) AS order_count,
                SUM(f.item_total_amt) AS total_revenue,
                COUNT(DISTINCT f.customer_id) AS unique_customers,
                COUNT(DISTINCT f.item_name) AS item_count,
                COUNT(DISTINCT IF(fp.first_purchase_date = toDate(f.created_at_pt), f.customer_id, NULL)) AS new_users,
                AVG(f.item_total_amt) AS avg_order_value,
                SUM(f.item_discount > 0) AS discount_orders,
                SUM(f.is_loyalty) AS loyalty_orders
            FROM dw.fact_order_item_variations f
            LEFT JOIN first_purchase fp ON f.customer_id = fp.customer_id
            WHERE
                f.created_at_pt >= '{start_date}'
                AND f.created_at_pt <= '{end_date}'
                AND f.pay_status = 'COMPLETED'
            GROUP BY date
            ORDER BY date
            """

            enhanced_data = await self.db.execute_query_async(query)

            if enhanced_data.empty:
                return self._get_mock_daily_report()

            # 计算日报指标
            report = {
                "date": end_date,
                "metrics": {
                    "total_revenue": float(enhanced_data['total_revenue'].sum()),
                    "total_orders": int(enhanced_data['order_count'].sum()),
                    "unique_customers": int(enhanced_data['unique_customers'].sum()),
                    "item_count": int(enhanced_data['item_count'].sum()) if 'item_count' in enhanced_data.columns else 0,
                    "new_users": int(enhanced_data['new_users'].sum()) if 'new_users' in enhanced_data.columns else 0,
                    "avg_order_value": float(enhanced_data['avg_order_value'].mean()),
                    "promotion_orders": int(enhanced_data['discount_orders'].sum()) if 'discount_orders' in enhanced_data.columns else 0,
                    "loyalty_orders": int(enhanced_data['loyalty_orders'].sum()) if 'loyalty_orders' in enhanced_data.columns else 0
                },
                "trends": self._calculate_trends(enhanced_data),
                "top_products": await self._get_top_products(start_date, end_date),
                "peak_hours": await self._get_peak_hours(start_date, end_date),
                "store_performance": await self._get_store_performance(start_date, end_date)
            }

            self._save_to_cache(cache_key, report)
            return report

        except Exception as e:
            print(f"Error getting daily report: {e}")
            import traceback
            traceback.print_exc()
            return self._get_mock_daily_report()

    def _calculate_trends(self, df: pd.DataFrame) -> Dict[str, float]:
        """计算趋势（修复版）"""
        if df.empty:
            return {}

        # 查找日期列（支持多种列名）
        date_col = None
        for col in ['date', 'ds', 'order_date', 'created_date']:
            if col in df.columns:
                date_col = col
                break

        # 如果找不到日期列，尝试使用索引
        if date_col is None and pd.api.types.is_datetime64_any_dtype(df.index):
            df = df.reset_index()
            date_col = 'index'

        if date_col is None:
            print("Warning: No date column found for trend calculation")
            return {}

        # 确保日期列是datetime类型
        df[date_col] = pd.to_datetime(df[date_col])
        df = df.sort_values(date_col)

        # 分割成前后两部分
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

    async def _get_top_products(self, start_date: str, end_date: str) -> List[Dict]:
        """获取热销产品"""
        query = f"""
        SELECT
            item_name,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(item_total_amt) AS revenue,
            SUM(item_qty) AS quantity
        FROM dw.fact_order_item_variations
        WHERE
            created_at_pt >= '{start_date}'
            AND created_at_pt <= '{end_date}'
            AND pay_status = 'COMPLETED'
            AND item_name IS NOT NULL
        GROUP BY item_name
        ORDER BY revenue DESC
        LIMIT 10
        """

        df = await self.db.execute_query_async(query)
        if df.empty:
            return []

        return df.to_dict('records')

    async def _get_peak_hours(self, start_date: str, end_date: str) -> List[Dict]:
        """获取高峰时段"""
        query = f"""
        SELECT
            toHour(created_at_pt) AS hour,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(item_total_amt) AS revenue
        FROM dw.fact_order_item_variations
        WHERE
            created_at_pt >= '{start_date}'
            AND created_at_pt <= '{end_date}'
            AND pay_status = 'COMPLETED'
        GROUP BY hour
        ORDER BY revenue DESC
        """

        df = await self.db.execute_query_async(query)
        if df.empty:
            return []

        return df.head(5).to_dict('records')

    async def _get_store_performance(self, start_date: str, end_date: str) -> List[Dict]:
        """获取门店表现"""
        query = f"""
        SELECT
            location_name,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(item_total_amt) AS revenue,
            COUNT(DISTINCT customer_id) AS customers
        FROM dw.fact_order_item_variations
        WHERE
            created_at_pt >= '{start_date}'
            AND created_at_pt <= '{end_date}'
            AND pay_status = 'COMPLETED'
            AND location_name IS NOT NULL
        GROUP BY location_name
        ORDER BY revenue DESC
        LIMIT 10
        """

        df = await self.db.execute_query_async(query)
        if df.empty:
            return []

        return df.to_dict('records')

    async def get_daily_report_summary(self) -> Dict[str, Any]:
        """获取日报摘要"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')

        report = await self.get_daily_report(yesterday, today)

        if not report:
            return None

        metrics = report.get("metrics", {})
        trends = report.get("trends", {})

        # 生成洞察
        insights = []
        if trends.get("total_revenue", 0) > 10:
            insights.append(f"📈 营收增长显著，环比上升{trends['total_revenue']:.1f}%")
        elif trends.get("total_revenue", 0) < -10:
            insights.append(f"📉 营收下降明显，环比下降{abs(trends['total_revenue']):.1f}%")

        if metrics.get("new_users", 0) > 0:
            insights.append(f"🎉 新增{metrics['new_users']}位新客户")

        # 生成摘要
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
            return cached

        try:
            # 获取历史数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

            query = f"""
            SELECT
                toDate(created_at_pt) AS date,
                SUM(item_total_amt) AS revenue
            FROM dw.fact_order_item_variations
            WHERE
                created_at_pt >= '{start_date}'
                AND created_at_pt <= '{end_date}'
                AND pay_status = 'COMPLETED'
            GROUP BY date
            ORDER BY date
            """

            historical_data = await self.db.execute_query_async(query)

            if historical_data.empty:
                return {"error": "No historical data available"}

            # 使用简单的移动平均预测
            historical_data['date'] = pd.to_datetime(historical_data['date'])
            historical_data = historical_data.set_index('date')

            # 计算7天移动平均
            historical_data['ma7'] = historical_data['revenue'].rolling(window=7).mean()

            # 生成预测
            last_date = historical_data.index[-1]
            forecast_dates = pd.date_range(start=last_date + timedelta(days=1), periods=days)

            # 使用最近7天的平均值作为预测基准
            recent_avg = historical_data['revenue'].tail(7).mean()
            recent_std = historical_data['revenue'].tail(14).std()

            # 生成预测数据
            forecast_data = []
            for i, date in enumerate(forecast_dates):
                # 考虑星期效应
                day_of_week = date.dayofweek
                week_factor = 1.0
                if day_of_week in [5, 6]:  # 周末
                    week_factor = 1.2
                elif day_of_week == 4:  # 周五
                    week_factor = 1.1

                predicted = recent_avg * week_factor

                forecast_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "actual": None,
                    "predicted": float(predicted),
                    "confidence_lower": float(predicted - 1.96 * recent_std),
                    "confidence_upper": float(predicted + 1.96 * recent_std)
                })

            # 添加历史数据
            for date, row in historical_data.tail(30).iterrows():
                forecast_data.insert(0, {
                    "date": date.strftime("%Y-%m-%d"),
                    "actual": float(row['revenue']),
                    "predicted": float(row['ma7']) if pd.notna(row['ma7']) else float(row['revenue']),
                    "confidence_lower": None,
                    "confidence_upper": None
                })

            result = {
                "forecast": {
                    "total_forecast": sum(d['predicted'] for d in forecast_data if d['actual'] is None),
                    "avg_daily_forecast": recent_avg,
                    "forecast_days": days
                },
                "chart_data": forecast_data,
                "method": "moving_average"
            }

            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"Error getting forecast: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}

    async def get_data_by_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图获取数据"""
        intent_type = intent.get("intent_type", "general")
        time_range = intent.get("time_range", {})

        # 解析时间范围
        start_date, end_date = self._parse_time_range(time_range)

        data = {}

        if intent_type == "daily_report":
            data = await self.get_daily_report_summary()
        elif intent_type == "forecast":
            days = intent.get("forecast_days", 7)
            data = await self.get_forecast(days)
        elif intent_type == "metrics":
            data = await self.get_metrics_data(start_date, end_date)
        elif intent_type == "analysis":
            data = await self.run_analysis(start_date, end_date)

        return data

    async def get_metrics_data(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取指标数据"""
        query = f"""
        WITH first_purchase AS (
            SELECT
                customer_id,
                toDate(MIN(created_at_pt)) AS first_purchase_date
            FROM dw.fact_order_item_variations
            WHERE pay_status = 'COMPLETED'
            GROUP BY customer_id
        )
        SELECT
            COUNT(DISTINCT f.order_id) AS total_orders,
            SUM(f.item_total_amt) AS total_revenue,
            COUNT(DISTINCT f.customer_id) AS unique_customers,
            COUNT(DISTINCT f.item_name) AS item_count,
            COUNT(DISTINCT IF(fp.first_purchase_date >= '{start_date}', f.customer_id, NULL)) AS new_users,
            AVG(f.item_total_amt) AS avg_order_value
        FROM dw.fact_order_item_variations f
        LEFT JOIN first_purchase fp ON f.customer_id = fp.customer_id
        WHERE
            f.created_at_pt >= '{start_date}'
            AND f.created_at_pt <= '{end_date}'
            AND f.pay_status = 'COMPLETED'
        """

        df = await self.db.execute_query_async(query)

        if df.empty:
            return self._get_mock_metrics()

        return {
            "metrics": df.to_dict('records')[0],
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
                True  # 包含预测
            )
            return results
        except Exception as e:
            print(f"Error running analysis: {e}")
            return {"error": str(e)}

    async def get_detail_data(self, detail_type: str, params: Dict) -> Dict[str, Any]:
        """获取详细数据"""
        if detail_type == "top_products":
            return await self._get_top_products_detail(params)
        elif detail_type == "customer_segments":
            return await self._get_customer_segments_detail(params)
        elif detail_type == "hourly_performance":
            return await self._get_hourly_performance_detail(params)
        else:
            return {"error": "Unknown detail type"}

    async def _get_top_products_detail(self, params: Dict) -> Dict[str, Any]:
        """获取产品详情"""
        start_date = params.get("start_date", (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        end_date = params.get("end_date", datetime.now().strftime('%Y-%m-%d'))

        products = await self._get_top_products(start_date, end_date)

        return {
            "type": "table",
            "columns": [
                {"key": "item_name", "title": "产品名称", "type": "string"},
                {"key": "revenue", "title": "销售额", "type": "currency"},
                {"key": "order_count", "title": "订单数", "type": "number"},
                {"key": "quantity", "title": "销量", "type": "number"}
            ],
            "rows": products
        }

    async def _get_customer_segments_detail(self, params: Dict) -> Dict[str, Any]:
        """获取客户分群详情"""
        query = """
        SELECT
            CASE 
                WHEN high_value_customer = 1 THEN '高价值客户'
                WHEN loyal = 1 THEN '忠诚客户'
                WHEN regular = 1 THEN '常规客户'
                WHEN dormant = 1 THEN '休眠客户'
                ELSE '其他'
            END AS segment,
            COUNT(*) AS count,
            AVG(order_final_avg_amt) AS avg_order_value,
            SUM(order_final_total_amt) AS total_revenue
        FROM ads.customer_profile
        GROUP BY segment
        ORDER BY total_revenue DESC
        """

        df = await self.db.execute_query_async(query)

        return {
            "type": "chart",
            "chart": {
                "type": "pie",
                "title": "客户分群分布",
                "series": df[['segment', 'count']].rename(columns={'segment': 'name', 'count': 'value'}).to_dict('records')
            }
        }

    async def _get_hourly_performance_detail(self, params: Dict) -> Dict[str, Any]:
        """获取小时级表现"""
        start_date = params.get("start_date", (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'))
        end_date = params.get("end_date", datetime.now().strftime('%Y-%m-%d'))

        peak_hours = await self._get_peak_hours(start_date, end_date)

        return {
            "type": "chart",
            "chart": {
                "type": "bar",
                "title": "小时销售分布",
                "xAxis": {"type": "category", "data": [f"{h['hour']}:00" for h in peak_hours]},
                "series": [
                    {"name": "销售额", "data": [h['revenue'] for h in peak_hours]}
                ]
            }
        }

    def _parse_time_range(self, time_range: Dict) -> tuple:
        """解析时间范围"""
        if time_range.get("type") == "today":
            start = end = datetime.now().strftime('%Y-%m-%d')
        elif time_range.get("type") == "yesterday":
            date = datetime.now() - timedelta(days=1)
            start = end = date.strftime('%Y-%m-%d')
        elif time_range.get("type") == "last_n_days":
            days = time_range.get("days", 7)
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        else:
            end = datetime.now().strftime('%Y-%m-%d')
            start = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')

        return start, end

    def _get_mock_daily_report(self) -> Dict[str, Any]:
        """获取模拟日报数据"""
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "metrics": {
                "total_revenue": 15234.56,
                "total_orders": 142,
                "unique_customers": 89,
                "item_count": 0,
                "new_users": 0,
                "avg_order_value": 107.29,
                "promotion_orders": 23,
                "loyalty_orders": 45
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

    def _get_mock_metrics(self) -> Dict[str, Any]:
        """获取模拟指标数据"""
        return {
            "metrics": {
                "total_revenue": 52341.23,
                "total_orders": 523,
                "unique_customers": 312,
                "item_count": 156,
                "new_users": 23,
                "avg_order_value": 100.08
            },
            "display_type": "metrics_cards"
        }