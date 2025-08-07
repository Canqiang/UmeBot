# backend/app/database.py
"""
ClickHouse数据库连接管理 - 修复并发查询问题
使用连接池和线程安全的连接管理
"""

import asyncio
import pandas as pd
from typing import Dict, Any, List, Optional
import clickhouse_connect
from clickhouse_connect.driver import Client
from contextlib import contextmanager
import threading
from queue import Queue
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ClickHouseDB:
    """ClickHouse数据库连接管理器（支持并发）"""

    def __init__(self):
        self.config = settings.CLICKHOUSE_CONFIG

        # self._local = threading.local()
        # self._connection_pool = Queue(maxsize=1)
        # self._lock = threading.Lock()
        # self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        # 创建初始连接
        for _ in range(1):
            try:
                client = self._create_client()
                # self._connection_pool.put(client)
            except Exception as e:
                logger.warning(f"Failed to create initial connection: {e}")

    def _create_client(self) -> Client:
        """创建新的ClickHouse客户端"""
        return clickhouse_connect.get_client(
            **self.config,
            # settings={
            #     'use_numpy': True,
            #     'max_execution_time': 60,
            #     'connect_timeout': 10,
            #     'send_receive_timeout': 30,
            #     'max_threads': 4
            # }
        )

    @contextmanager
    def get_client(self):
        """获取客户端连接（上下文管理器）"""
        client = None
        try:
            # 尝试从连接池获取
            try:
                client = self._connection_pool.get(timeout=1)
            except:
                # 如果池为空，创建新连接
                client = self._create_client()

            # 测试连接是否有效
            try:
                client.query("SELECT 1")
            except:
                # 连接无效，创建新的
                client = self._create_client()

            yield client

        finally:
            # 归还连接到池
            if client:
                try:
                    if self._connection_pool.full():
                        # 如果池满了，关闭连接
                        client.close()
                    else:
                        self._connection_pool.put(client)
                except:
                    # 如果归还失败，关闭连接
                    try:
                        client.close()
                    except:
                        pass

    def execute_query(self, query: str) -> pd.DataFrame:
        """执行查询（同步）"""
        with self.get_client() as client:
            try:
                result = client.query_df(query)
                return result
            except Exception as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query[:200]}...")
                raise

    async def execute_query_async(self, query: str) -> pd.DataFrame:
        """执行查询（异步）- 使用独立的客户端实例"""
        loop = asyncio.get_event_loop()

        # 在线程池中执行，每次使用新的客户端
        def run_query():
            with self.get_client() as client:
                return client.query_df(query)

        try:
            return await loop.run_in_executor(None, run_query)
        except Exception as e:
            logger.error(f"Async query execution failed: {e}")
            logger.error(f"Query: {query[:200]}...")
            # 返回空DataFrame而不是抛出异常
            return pd.DataFrame()

    async def execute_query_with_retry(self, query: str, max_retries: int = 3) -> pd.DataFrame:
        """执行查询，带重试机制"""
        for attempt in range(max_retries):
            try:
                return await self.execute_query_async(query)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Query failed after {max_retries} attempts: {e}")
                    return pd.DataFrame()
                await asyncio.sleep(0.5 * (attempt + 1))  # 递增延迟

    async def execute_multiple_queries(self, queries: List[str]) -> List[pd.DataFrame]:
        """并发执行多个查询"""
        tasks = [self.execute_query_async(query) for query in queries]
        return await asyncio.gather(*tasks, return_exceptions=True)

    async def get_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """获取指标数据（优化版）"""
        # 使用单个查询获取所有指标，避免并发问题
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
            SUM(f.item_total_amt) AS total_revenue,
            COUNT(DISTINCT f.order_id) AS total_orders,
            COUNT(DISTINCT f.customer_id) AS total_customers,
            COUNT(DISTINCT f.item_name) AS total_items,
            COUNT(DISTINCT IF(fp.first_purchase_date = toDate(f.created_at_pt), f.customer_id, NULL)) AS total_new_users,
            SUM(f.item_total_amt) / NULLIF(COUNT(DISTINCT f.order_id), 0) AS avg_order_value
        FROM dw.fact_order_item_variations f
        LEFT JOIN first_purchase fp ON f.customer_id = fp.customer_id
        WHERE
            f.created_at_pt >= '{start_date}' and f.created_at_pt <= '{end_date}'
            AND f.pay_status = 'COMPLETED'
        GROUP BY date
        ORDER BY date
        """

        df = await self.execute_query_async(query)

        if df.empty:
            return {
                'total_revenue': 0,
                'total_orders': 0,
                'unique_customers': 0,
                'item_count': 0,
                'new_users': 0,
                'avg_order_value': 0
            }

        row = df.iloc[0]
        return {
            'total_revenue': float(row.get('total_revenue', 0)),
            'total_orders': int(row.get('total_orders', 0)),
            'unique_customers': int(row.get('total_customers', 0)),
            'item_count': int(row.get('total_items', 0)),
            'new_users': int(row.get('total_new_users', 0)),
            'avg_order_value': float(row.get('avg_order_value', 0))
        }

    async def get_daily_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取每日数据"""
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

        return await self.execute_query_async(query)

    async def get_customer_count(self) -> int:
        """获取总用户数"""
        query = """
                SELECT COUNT(DISTINCT customer_id) as total_customers
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED' \
                """

        df = await self.execute_query_async(query)
        if df.empty:
            return 0
        return int(df.iloc[0]['total_customers'])

    async def get_customer_segments(self) -> List[Dict[str, Any]]:
        """获取客户分群"""
        query = """
                SELECT CASE \
                           WHEN high_value_customer = 1 THEN '高价值客户' \
                           WHEN loyal = 1 THEN '忠诚客户' \
                           WHEN regular = 1 THEN '常规客户' \
                           WHEN dormant = 1 THEN '休眠客户' \
                           ELSE '其他' \
                           END AS segment, \
                       COUNT(*) AS count,
            AVG(order_final_avg_amt) AS avg_order_value
                FROM ads.customer_profile
                WHERE order_final_total_cnt > 0
                GROUP BY segment
                ORDER BY count DESC \
                """

        try:
            df = await self.execute_query_async(query)
            if df.empty:
                return []
            return df.to_dict('records')
        except Exception as e:
            logger.warning(f"Customer segments query failed: {e}")
            return []

    def close(self):
        """关闭所有连接"""
        while not self._connection_pool.empty():
            try:
                client = self._connection_pool.get_nowait()
                client.close()
            except:
                pass

    def __del__(self):
        """析构函数，确保连接关闭"""
        self.close()


# 全局数据库实例
db_instance = None


def get_db() -> ClickHouseDB:
    """获取数据库实例（单例）"""
    global db_instance
    if db_instance is None:
        db_instance = ClickHouseDB()
    return db_instance