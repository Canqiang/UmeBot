# ============== backend/app/database.py ==============
"""
数据库连接和管理
"""

import clickhouse_connect
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from app.config import settings


class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.client = None
        self.executor = ThreadPoolExecutor(max_workers=3)

    def connect(self):
        """建立数据库连接"""
        try:
            self.client = clickhouse_connect.get_client(**settings.CLICKHOUSE_CONFIG)
            print("✅ Connected to ClickHouse")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to ClickHouse: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.client:
            self.client.close()
            print("👋 Disconnected from ClickHouse")

    async def execute_query_async(self, query: str) -> pd.DataFrame:
        """异步执行查询"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self.execute_query,
            query
        )

    def execute_query(self, query: str) -> pd.DataFrame:
        """同步执行查询"""
        if not self.client:
            self.connect()

        try:
            return self.client.query_df(query)
        except Exception as e:
            print(f"Query execution failed: {e}")
            raise

    async def get_sales_summary(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取销售摘要"""
        query = f"""
        SELECT
            toDate(created_at_pt) AS date,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(item_total_amt) AS total_revenue,
            COUNT(DISTINCT customer_id) AS unique_customers,
            AVG(item_total_amt) AS avg_order_value
        FROM dw.fact_order_item_variations
        WHERE
            created_at_pt >= '{start_date}'
            AND created_at_pt <= '{end_date}'
            AND pay_status = 'COMPLETED'
        GROUP BY date
        ORDER BY date
        """

        df = await self.execute_query_async(query)

        if df.empty:
            return {}

        return {
            'total_revenue': float(df['total_revenue'].sum()),
            'total_orders': int(df['order_count'].sum()),
            'unique_customers': int(df['unique_customers'].sum()),
            'avg_order_value': float(df['avg_order_value'].mean()),
            'daily_data': df.to_dict('records')
        }

    async def get_customer_segments(self) -> List[Dict[str, Any]]:
        """获取客户细分"""
        query = """
                SELECT CASE \
                           WHEN high_value_customer = 1 THEN 'High Value' \
                           WHEN loyal = 1 THEN 'Loyal' \
                           WHEN potential = 1 THEN 'Potential' \
                           WHEN churned = 1 THEN 'Churned' \
                           ELSE 'Regular' \
                           END                    AS segment, \
                       COUNT(*)                   AS customer_count, \
                       AVG(order_final_total_amt) AS avg_lifetime_value, \
                       AVG(order_final_total_cnt) AS avg_order_count
                FROM ads.customer_profile
                GROUP BY segment
                ORDER BY customer_count DESC \
                """

        df = await self.execute_query_async(query)
        return df.to_dict('records')

    async def get_product_performance(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """获取产品表现"""
        query = f"""
        SELECT
            category_name,
            COUNT(DISTINCT order_id) AS order_count,
            SUM(item_total_amt) AS revenue,
            AVG(item_total_amt) AS avg_price
        FROM dw.fact_order_item_variations
        WHERE
            created_at_pt >= '{start_date}'
            AND created_at_pt <= '{end_date}'
            AND pay_status = 'COMPLETED'
        GROUP BY category_name
        ORDER BY revenue DESC
        LIMIT 10
        """

        df = await self.execute_query_async(query)
        return df.to_dict('records')

    async def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            query = "SELECT 1"
            await self.execute_query_async(query)
            return True
        except:
            return False

# 单例实例
db_manager = DatabaseManager()
