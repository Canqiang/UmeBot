"""
数据分析服务
集成因果分析引擎，提供各种数据分析功能
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import asyncio
from app.config import settings

# 导入因果分析引擎（假设已经在项目中）
import sys

sys.path.append('../')
from app.fixed_causal_inference import UMeCausalInferenceEngine


class AnalysisService:
    """分析服务类"""

    def __init__(self):
        self.engine = None
        self.cache = {}
        self.cache_ttl = 3600  # 1小时缓存

    async def initialize(self):
        """初始化分析引擎"""
        try:
            self.engine = UMeCausalInferenceEngine(settings.CLICKHOUSE_CONFIG)
            print("✅ Analysis engine initialized")
        except Exception as e:
            print(f"❌ Failed to initialize analysis engine: {e}")

    async def cleanup(self):
        """清理资源"""
        self.cache.clear()

    def _get_cache_key(self, method: str, params: Dict) -> str:
        """生成缓存键"""
        import hashlib
        import json
        param_str = json.dumps(params, sort_keys=True)
        return f"{method}:{hashlib.md5(param_str.encode()).hexdigest()}"

    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() - entry["time"] < timedelta(seconds=self.cache_ttl):
                return entry["data"]
            else:
                del self.cache[key]
        return None

    def _save_to_cache(self, key: str, data: Any):
        """保存到缓存"""
        self.cache[key] = {
            "data": data,
            "time": datetime.now()
        }

    def _format_forecast(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """格式化预测结果以便序列化"""
        forecast_df = result.get("forecast")
        if isinstance(forecast_df, pd.DataFrame):
            forecast_data = {
                "dates": forecast_df["ds"].dt.strftime("%Y-%m-%d").tolist(),
                "values": forecast_df["yhat"].tolist(),
            }
            if "yhat_lower" in forecast_df.columns:
                forecast_data["confidence_lower"] = forecast_df["yhat_lower"].tolist()
            if "yhat_upper" in forecast_df.columns:
                forecast_data["confidence_upper"] = forecast_df["yhat_upper"].tolist()
        else:
            forecast_data = {}

        if "summary" in result:
            forecast_data["summary"] = result["summary"]
        if "method" in result:
            forecast_data["method"] = result["method"]

        return forecast_data

    async def get_daily_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取日报数据"""
        cache_key = self._get_cache_key("daily_report", {"start": start_date, "end": end_date})
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            # 运行分析（在线程池中执行同步代码）
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.engine.run_complete_analysis,
                start_date,
                end_date,
                False  # 不包含预测
            )

            # 提取关键指标
            enhanced_data = results.get('enhanced_data')
            if enhanced_data is None:
                return self._get_mock_daily_report()

            # 计算日报指标
            report = {
                "date": end_date,
                "metrics": {
                    "total_revenue": float(enhanced_data['total_revenue'].sum()),
                    "total_orders": int(enhanced_data['order_count'].sum()),
                    "unique_customers": int(enhanced_data['unique_customers'].sum()),
                    "item_count": int(enhanced_data['item_count'].sum()) if 'item_count' in enhanced_data else 0,
                    "new_users": int(enhanced_data['new_users'].sum()) if 'new_users' in enhanced_data else 0,
                    "avg_order_value": float(enhanced_data['avg_order_value'].mean()),
                    "promotion_orders": int(enhanced_data['discount_orders'].sum()),
                    "loyalty_orders": int(enhanced_data['loyalty_orders'].sum())
                },
                "trends": self._calculate_trends(enhanced_data),
                "top_products": self._get_top_products(enhanced_data),
                "peak_hours": self._get_peak_hours(enhanced_data),
                "store_performance": self._get_store_performance(enhanced_data)
            }

            self._save_to_cache(cache_key, report)
            return report

        except Exception as e:
            print(f"Error getting daily report: {e}")
            return self._get_mock_daily_report()

    async def get_daily_report_summary(self) -> Dict[str, Any]:
        """获取日报摘要（用于自动推送）"""
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')

        report = await self.get_daily_report(yesterday, today)

        # 生成摘要
        summary = {
            "date": today,
            "highlights": [
                f"📊 总营收: ${report['metrics']['total_revenue']:,.0f}",
                f"📦 订单数: {report['metrics']['total_orders']:,}",
                f"👥 客户数: {report['metrics']['unique_customers']:,}",
                f"💰 客单价: ${report['metrics']['avg_order_value']:.2f}"
            ],
            "trends": report.get("trends", {}),
            "insights": self._generate_insights(report)
        }

        return summary

    async def run_causal_analysis(
            self,
            start_date: str,
            end_date: str,
            analysis_type: str = "full"
    ) -> Dict[str, Any]:
        """运行因果分析"""
        cache_key = self._get_cache_key(
            "causal_analysis",
            {"start": start_date, "end": end_date, "type": analysis_type}
        )
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                self.engine.run_complete_analysis,
                start_date,
                end_date,
                True  # 包含预测
            )

            # 格式化结果
            forecast_data = None
            forecast_results = results.get("forecast_results")
            if forecast_results:
                if isinstance(forecast_results, dict) and "error" not in forecast_results:
                    forecast_data = self._format_forecast(forecast_results)
                else:
                    forecast_data = forecast_results
            analysis = {
                "period": {"start": start_date, "end": end_date},
                "causal_effects": self._format_causal_effects(results.get("analysis_results", {})),
                "interactions": self._format_interactions(results.get("analysis_results", {}).get("interactions", {})),
                "heterogeneity": self._format_heterogeneity(
                    results.get("analysis_results", {}).get("heterogeneity", {})),
                "forecast": forecast_data,
                "recommendations": self._generate_recommendations(results)
            }

            self._save_to_cache(cache_key, analysis)
            return analysis

        except Exception as e:
            print(f"Error running causal analysis: {e}")
            return {"error": str(e)}

    async def get_sales_forecast(self, days: int = 7) -> Dict[str, Any]:
        """获取销售预测"""
        cache_key = self._get_cache_key("forecast", {"days": days})
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached

        try:
            # 先获取最近的数据
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')

            # 加载数据
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self.engine.load_integrated_data,
                start_date,
                end_date
            )

            # 创建特征
            weather_df = await loop.run_in_executor(
                None,
                self.engine.get_weather_data,
                start_date,
                end_date,
                self.engine.raw_data
            )

            await loop.run_in_executor(
                None,
                self.engine.create_all_features,
                self.engine.raw_data,
                weather_df
            )

            # 生成预测
            forecast_result = await loop.run_in_executor(
                None,
                self.engine.create_sales_forecast,
                days
            )

            # 预测失败则直接返回错误
            if "error" in forecast_result:
                return forecast_result

            # 转换预测结果为图表数据
            forecast_df = forecast_result.get("forecast")
            chart_data = []
            if isinstance(forecast_df, pd.DataFrame):
                chart_data = [
                    {
                        "date": row["ds"].strftime("%Y-%m-%d"),
                        "actual": float(row["y"]) if not pd.isna(row["y"]) else None,
                        "predicted": float(row["yhat"])
                    }
                    for _, row in forecast_df.iterrows()
                ]

            result = {
                "forecast": forecast_result.get("summary", {}),
                "chart_data": chart_data,
                "method": forecast_result.get("method")
            }


            self._save_to_cache(cache_key, result)
            return result

        except Exception as e:
            print(f"Error getting forecast: {e}")
            return {"error": str(e)}

    async def get_data_by_intent(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """根据意图获取数据"""
        intent_type = intent.get("intent_type", "general")
        time_range = intent.get("time_range", {})

        # 解析时间范围
        start_date, end_date = self._parse_time_range(time_range)

        data = {}

        if intent_type == "daily_report":
            data = await self.get_daily_report(start_date, end_date)

        elif intent_type == "sales_analysis":
            data = await self._get_sales_analysis(start_date, end_date, intent)

        elif intent_type == "customer_analysis":
            data = await self._get_customer_analysis(start_date, end_date)

        elif intent_type == "promotion_analysis":
            data = await self._get_promotion_analysis(start_date, end_date)

        elif intent_type == "causal_analysis":
            data = await self.run_causal_analysis(start_date, end_date)

        elif intent_type == "forecast":
            days = intent.get("forecast_days", 7)
            data = await self.get_sales_forecast(days)

        elif intent_type == "comparison":
            data = await self._get_comparison_data(start_date, end_date, intent)

        return data

    async def get_detail_data(self, detail_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取详细数据"""
        if detail_type == "store_performance":
            return await self._get_store_details(params)
        elif detail_type == "product_analysis":
            return await self._get_product_details(params)
        elif detail_type == "customer_segment":
            return await self._get_customer_segment_details(params)
        elif detail_type == "promotion_effect":
            return await self._get_promotion_effect_details(params)
        else:
            return {"error": "Unknown detail type"}

    # ========== 辅助方法 ==========

    def _parse_time_range(self, time_range: Dict[str, Any]) -> tuple:
        """解析时间范围"""
        today = datetime.now()

        if time_range.get("type") == "absolute":
            return time_range.get("start"), time_range.get("end")

        value = time_range.get("value", "today")

        if value == "today":
            date = today.strftime('%Y-%m-%d')
            return date, date
        elif value == "yesterday":
            date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            return date, date
        elif value == "this_week":
            start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return start, end
        elif value == "last_week":
            start = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
            end = (today - timedelta(days=today.weekday() + 1)).strftime('%Y-%m-%d')
            return start, end
        elif value == "this_month":
            start = today.replace(day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return start, end
        elif value == "last_month":
            first_day = today.replace(day=1)
            last_month = first_day - timedelta(days=1)
            start = last_month.replace(day=1).strftime('%Y-%m-%d')
            end = last_month.strftime('%Y-%m-%d')
            return start, end
        else:
            # 默认返回今天
            date = today.strftime('%Y-%m-%d')
            return date, date

    def _calculate_trends(self, data: pd.DataFrame) -> Dict[str, float]:
        """计算趋势"""
        if len(data) < 2:
            return {}

        # 确保存在日期列并标准化为"date"
        date_col = None
        for col in ["date", "order_date", "ds"]:
            if col in data.columns:
                date_col = col
                break

        if date_col is None:
            if isinstance(data.index, pd.DatetimeIndex):
                idx_name = data.index.name or "index"
                data = data.reset_index().rename(columns={idx_name: "date"})
            elif not pd.api.types.is_numeric_dtype(data.index):
                try:
                    data = data.copy()
                    data["date"] = pd.to_datetime(data.index)
                except Exception:
                    return {}
            else:
                return {}
        else:
            if date_col != "date":
                data = data.rename(columns={date_col: "date"})

        try:
            data["date"] = pd.to_datetime(data["date"])
        except Exception:
            return {}

        data = data.sort_values("date")

        # 计算最近两个时期的对比
        mid_point = len(data) // 2
        first_half = data.iloc[:mid_point]
        second_half = data.iloc[mid_point:]

        trends = {}

        for metric in ['total_revenue', 'order_count', 'unique_customers']:
            if metric in data.columns:
                first_avg = first_half[metric].mean()
                second_avg = second_half[metric].mean()
                if first_avg > 0:
                    change = ((second_avg - first_avg) / first_avg) * 100
                    trends[metric] = round(change, 2)

        return trends

    def _get_top_products(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """获取热销产品"""
        products = []

        # 按产品类别聚合
        category_cols = ['tea_drinks_orders', 'coffee_orders', 'food_orders',
                         'caffeine_free_orders', 'new_product_orders']

        for col in category_cols:
            if col in data.columns:
                category_name = col.replace('_orders', '').replace('_', ' ').title()
                total = data[col].sum()
                products.append({
                    "name": category_name,
                    "orders": int(total),
                    "rank": 0
                })

        # 排序
        products.sort(key=lambda x: x['orders'], reverse=True)
        for i, product in enumerate(products[:5]):
            product['rank'] = i + 1

        return products[:5]

    def _get_peak_hours(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """获取高峰时段"""
        hours = []

        hour_cols = ['morning_orders', 'lunch_orders', 'afternoon_orders', 'evening_orders']
        hour_names = ['早餐时段(7-10)', '午餐时段(11-14)', '下午茶(15-17)', '晚餐时段(18-21)']

        for col, name in zip(hour_cols, hour_names):
            if col in data.columns:
                total = data[col].sum()
                hours.append({
                    "period": name,
                    "orders": int(total)
                })

        hours.sort(key=lambda x: x['orders'], reverse=True)
        return hours

    def _get_store_performance(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """获取店铺表现"""
        if 'location_id' not in data.columns:
            return []

        # 按店铺聚合
        store_data = data.groupby('location_id').agg({
            'total_revenue': 'sum',
            'order_count': 'sum',
            'unique_customers': 'sum'
        }).reset_index()

        stores = []
        for _, row in store_data.iterrows():
            stores.append({
                "store_id": row['location_id'],
                "revenue": float(row['total_revenue']),
                "orders": int(row['order_count']),
                "customers": int(row['unique_customers'])
            })

        stores.sort(key=lambda x: x['revenue'], reverse=True)
        return stores[:10]  # 返回前10家店铺

    def _generate_insights(self, report: Dict[str, Any]) -> List[str]:
        """生成洞察"""
        insights = []

        # 基于趋势生成洞察
        trends = report.get("trends", {})
        for metric, change in trends.items():
            if change > 10:
                insights.append(f"📈 {metric} 显著增长 {change:.1f}%")
            elif change < -10:
                insights.append(f"📉 {metric} 下降 {abs(change):.1f}%，需要关注")

        # 基于热销产品
        top_products = report.get("top_products", [])
        if top_products:
            insights.append(f"🔥 今日热销: {top_products[0]['name']}")

        return insights[:3]  # 最多返回3条洞察

    def _format_causal_effects(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化因果效应"""
        effects = []

        factor_names = {
            'has_promotion': '促销活动',
            'is_weekend': '周末效应',
            'is_holiday': '节假日效应',
            'is_hot': '高温天气',
            'is_rainy': '雨天天气'
        }

        for factor, result in analysis_results.items():
            if factor in factor_names and isinstance(result, dict) and 'ate' in result:
                effects.append({
                    "factor": factor_names[factor],
                    "effect": result['ate'],
                    "confidence_interval": [result.get('ci_lower', 0), result.get('ci_upper', 0)],
                    "significant": result.get('significant', False),
                    "sample_size": result.get('sample_size', 0)
                })

        return effects

    def _format_interactions(self, interactions: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化交互效应"""
        formatted = []

        for key, value in interactions.items():
            if isinstance(value, dict) and 'interaction_effect' in value:
                formatted.append({
                    "factors": key.split('_x_'),
                    "interaction_effect": value['interaction_effect'],
                    "combined_effect": value.get('combined_effect', 0)
                })

        return formatted

    def _format_heterogeneity(self, heterogeneity: Dict[str, Any]) -> Dict[str, Any]:
        """格式化异质性分析"""
        return heterogeneity  # 暂时直接返回

    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """生成推荐"""
        recommendations = []

        # 基于因果分析结果生成推荐
        analysis_results = results.get("analysis_results", {})

        for factor, result in analysis_results.items():
            if isinstance(result, dict) and 'ate' in result and result.get('significant'):
                ate = result['ate']
                if factor == 'has_promotion' and ate < -50:
                    recommendations.append("🎯 当前促销策略效果不佳，建议优化促销方案")
                elif factor == 'is_weekend' and ate > 100:
                    recommendations.append("📈 周末效应显著，建议增加周末营销投入")
                elif factor == 'is_hot' and ate > 50:
                    recommendations.append("☀️ 高温天气销售增长，建议推出夏季特饮")

        return recommendations[:5]

    def _get_mock_daily_report(self) -> Dict[str, Any]:
        """获取模拟日报数据"""
        return {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "metrics": {
                "total_revenue": 25000.0,
                "total_orders": 500,
                "unique_customers": 350,
                "avg_order_value": 50.0,
                "promotion_orders": 100,
                "loyalty_orders": 150
            },
            "trends": {
                "total_revenue": 5.5,
                "order_count": 3.2,
                "unique_customers": 2.8
            },
            "top_products": [
                {"name": "Milk Tea", "orders": 150, "rank": 1},
                {"name": "Coffee", "orders": 120, "rank": 2},
                {"name": "Fruit Tea", "orders": 100, "rank": 3}
            ],
            "peak_hours": [
                {"period": "午餐时段(11-14)", "orders": 200},
                {"period": "晚餐时段(18-21)", "orders": 150}
            ],
            "store_performance": []
        }

    async def _get_sales_analysis(self, start_date: str, end_date: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """获取销售分析"""
        # 实现销售分析逻辑
        return await self.get_daily_report(start_date, end_date)

    async def _get_customer_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取客户分析"""
        # 实现客户分析逻辑
        return {"message": "客户分析功能开发中"}

    async def _get_promotion_analysis(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取促销分析"""
        # 实现促销分析逻辑
        return {"message": "促销分析功能开发中"}

    async def _get_comparison_data(self, start_date: str, end_date: str, intent: Dict[str, Any]) -> Dict[str, Any]:
        """获取对比数据"""
        # 实现对比分析逻辑
        return {"message": "对比分析功能开发中"}

    async def _get_store_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取店铺详情"""
        return {"store_id": params.get("store_id"), "details": "店铺详情数据"}

    async def _get_product_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取产品详情"""
        return {"product": params.get("product"), "details": "产品详情数据"}

    async def _get_customer_segment_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取客户细分详情"""
        return {"segment": params.get("segment"), "details": "客户细分详情"}

    async def _get_promotion_effect_details(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """获取促销效果详情"""
        return {"promotion": params.get("promotion"), "details": "促销效果详情"}