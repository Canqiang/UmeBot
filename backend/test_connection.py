
# ============== backend/test_connection.py ==============
"""
测试数据库连接和基础功能
"""

import asyncio
from app.database import db_manager
from app.config import settings
import pandas as pd


async def test_database():
    """测试数据库功能"""
    print("🔧 Testing database connection...")

    # 测试连接
    if db_manager.connect():
        print("✅ Database connection successful")
    else:
        print("❌ Database connection failed")
        return

    # 测试查询
    try:
        print("\n📊 Testing sales summary query...")
        summary = await db_manager.get_sales_summary("2025-01-01", "2025-01-31")
        if summary:
            print(f"  Total Revenue: ${summary.get('total_revenue', 0):,.2f}")
            print(f"  Total Orders: {summary.get('total_orders', 0):,}")
            print(f"  Unique Customers: {summary.get('unique_customers', 0):,}")
            print("✅ Sales query successful")
        else:
            print("⚠️ No data returned")

        print("\n👥 Testing customer segments query...")
        segments = await db_manager.get_customer_segments()
        if segments:
            print(f"  Found {len(segments)} customer segments")
            for segment in segments[:3]:
                print(f"  - {segment['segment']}: {segment['customer_count']} customers")
            print("✅ Customer query successful")

        print("\n📦 Testing product performance query...")
        products = await db_manager.get_product_performance("2025-01-01", "2025-01-31")
        if products:
            print(f"  Found {len(products)} product categories")
            for product in products[:3]:
                print(f"  - {product['category_name']}: ${product['revenue']:,.2f}")
            print("✅ Product query successful")

    except Exception as e:
        print(f"❌ Query failed: {e}")

    finally:
        db_manager.disconnect()


if __name__ == "__main__":
    asyncio.run(test_database())