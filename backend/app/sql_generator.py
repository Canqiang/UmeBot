from typing import Dict, List, Any, Optional, Tuple
import re
import json
from datetime import datetime, timedelta
from app.config import settings
from app.database import get_db
import pandas as pd


class SQLGeneratorService:
    """SQL生成服务"""

    def __init__(self, llm_service=None):
        self.llm_service = llm_service

        # 数据库表结构信息
        self.table_schemas = {
            "dw.fact_order_item_variations": {
                "description": "订单商品变体事实表",
                "columns": {
                    "order_id": "订单ID",
                    "item_name": "商品名称",
                    "item_total_amt": "商品总金额",
                    "item_qty": "商品数量",
                    "category_name": "类别名称",
                    "location_id": "店铺ID",
                    "location_name": "店铺名称",
                    "customer_id": "客户ID",
                    "created_at_pt": "创建时间(PT)",
                    "pay_status": "支付状态",
                    "is_loyalty": "是否忠诚客户",
                    "item_discount": "商品折扣",
                    "campaign_names": "活动名称"
                }
            },
            "ads.customer_profile": {
                "description": "客户画像表",
                "columns": {
                    "customer_id": "客户ID",
                    "given_name": "名",
                    "family_name": "姓",
                    "phone_number": "电话号码",
                    "order_final_total_cnt": "总订单数",
                    "order_final_total_amt": "总消费金额",
                    "order_final_avg_amt": "平均订单金额",
                    "order_first_date": "首次订单日期",
                    "order_last_date": "最后订单日期",
                    "high_value_customer": "高价值客户",
                    "loyal": "忠诚客户",
                    "churned": "流失客户"
                }
            },
            "ads.promotion_sales": {
                "description": "促销销售表",
                "columns": {
                    "order_date": "订单日期",
                    "weekdays": "星期",
                    "location_id": "店铺ID",
                    "location_name": "店铺名称",
                    "item_name": "商品名称",
                    "category_name": "类别名称",
                    "item_amt": "商品金额",
                    "item_qty": "商品数量",
                    "order_qty": "订单数量",
                    "order_amt": "订单金额"
                }
            },
            "dw.dim_catalog_categories": {
                "description": "目录分类维度表",
                "columns": {
                    "category_id": "分类 ID",
                    "category_name": "分类名称",
                    "category_type": "分类类型",
                    "parent_category_id": "父分类 ID",
                    "root_category": "根分类",
                    "is_top_level": "是否顶级分类",
                    "channels": "渠道",
                    "merchant_id": "商家 ID",
                    "image_ids": "图片 ID 集合",
                    "present_at_all_locations": "是否在所有门店可用",
                    "present_at_location_ids": "可用门店 ID 集合",
                    "absent_at_location_ids": "不可用门店 ID 集合",
                    "availability_period_ids": "可用时段 ID 集合",
                    "path_to_root": "到根分类的路径",
                    "version": "版本号",
                    "is_deleted": "是否删除",
                    "updated_at": "更新时间",
                    "synced_time": "同步时间"
                }
            },
            "dw.dim_catalog_items": {
                "description": "商品项维度表",
                "columns": {
                    "item_id": "商品 ID",
                    "item_name": "商品名称",
                    "original_item_name": "原始商品名称",
                    "description_plaintext": "商品描述（纯文本）",
                    "channels": "渠道",
                    "product_type": "产品类型",
                    "modifier_list_ids": "修饰符列表 ID 集合",
                    "category_ids": "分类 ID 集合",
                    "category_names": "分类名称集合",
                    "reporting_category_id": "报表分类 ID",
                    "reporting_category_name": "报表分类名称",
                    "is_archived": "是否归档",
                    "merchant_id": "商家 ID",
                    "abbreviation": "缩写",
                    "tax_ids": "税务 ID 集合",
                    "skip_modifier_screen": "是否跳过修饰符界面",
                    "item_options": "商品选项",
                    "image_ids": "图片 ID 集合",
                    "sort_name": "排序名称",
                    "present_at_all_locations": "是否在所有门店可用",
                    "present_at_location_ids": "可用门店 ID 集合",
                    "absent_at_location_ids": "不可用门店 ID 集合",
                    "version": "版本号",
                    "is_deleted": "是否删除",
                    "source": "来源",
                    "updated_at": "更新时间",
                    "synced_time": "同步时间"
                }
            },
            "dw.dim_locations": {
                "description": "门店维度表",
                "columns": {
                    "location_id": "门店 ID",
                    "location_name": "门店名称",
                    "address_line": "地址行",
                    "locality": "所在地区",
                    "locality_population": "地区人口",
                    "administrative_district_level_1": "一级行政区",
                    "postal_code": "邮政编码",
                    "country": "国家",
                    "status": "状态",
                    "created_at": "创建时间",
                    "created_at_pt": "洛杉矶时区创建时间",
                    "phone_number": "电话号码",
                    "business_name": "商户名称",
                    "type": "类型",
                    "coordinates": "坐标",
                    "mcc": "商户类别码",
                    "merchant_id": "商家 ID",
                    "synced_time": "同步时间"
                }
            },
            "dw.fact_orders": {
                "description": "订单事实表",
                "columns": {
                    "order_id": "订单 ID",
                    "location_id": "门店 ID",
                    "location_name": "门店名称",
                    "locality": "所在地区",
                    "source": "订单来源",
                    "source_type": "来源类型",
                    "status": "订单状态",
                    "pay_status": "支付状态",
                    "customer_id": "客户 ID",
                    "original_customer_id": "原始客户 ID",
                    "customer_created_at_pt": "客户创建时间（PT 时区）",
                    "loyalty_created_at_pt": "会员创建时间（PT 时区）",
                    "is_loyalty": "是否为会员订单",
                    "is_new_users": "是否为新用户数组",
                    "is_reactives": "是否为回头客数组",
                    "is_text_subscriber": "是否为短信订阅用户",
                    "is_email_subscriber": "是否为邮件订阅用户",
                    "customer_race": "客户种族",
                    "total_amount": "订单总金额",
                    "subtotal": "订单小计金额",
                    "tax": "税费金额",
                    "discount": "折扣金额",
                    "tip": "小费金额",
                    "service_charge": "服务费金额",
                    "item_names": "商品名称数组",
                    "campaign_names": "活动名称数组",
                    "merchant_id": "商家 ID",
                    "tenders": "支付方式",
                    "created_at": "订单创建时间",
                    "created_at_pt": "订单创建时间（PT 时区）",
                    "updated_at": "订单更新时间"
                }
            }
        }

        # 常用查询模板
        self.query_templates = {
            "daily_sales": """
                SELECT 
                    toDate(created_at_pt) as date,
                    COUNT(DISTINCT order_id) as order_count,
                    SUM(item_total_amt) as total_revenue,
                    COUNT(DISTINCT customer_id) as unique_customers,
                    AVG(item_total_amt) as avg_order_value
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED'  -- 仅考虑已完成订单
                    {date_filter}
                GROUP BY date
                ORDER BY date DESC
            """,

            "product_performance": """
                SELECT 
                    category_name,
                    item_name,
                    COUNT(*) as sales_count,
                    SUM(item_total_amt) as total_revenue,
                    AVG(item_total_amt) as avg_price
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED'
                    {date_filter}
                GROUP BY category_name, item_name
                ORDER BY total_revenue DESC
                LIMIT {limit}
            """,

            "customer_analysis": """
                SELECT 
                    CASE
                        WHEN high_value_customer = 1 THEN 'High Value'
                        WHEN loyal = 1 THEN 'Loyal'
                        WHEN churned = 1 THEN 'Churned'
                        ELSE 'Regular'
                    END as customer_segment,
                    COUNT(*) as customer_count,
                    AVG(order_final_total_amt) as avg_lifetime_value,
                    AVG(order_final_total_cnt) as avg_order_count
                FROM ads.customer_profile
                {where_clause}
                GROUP BY customer_segment
                ORDER BY customer_count DESC
            """,

            "store_comparison": """
                SELECT 
                    location_name,
                    COUNT(DISTINCT order_id) as order_count,
                    SUM(item_total_amt) as total_revenue,
                    COUNT(DISTINCT customer_id) as unique_customers,
                    AVG(item_total_amt) as avg_order_value
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED'
                    {date_filter}
                GROUP BY location_name
                ORDER BY total_revenue DESC
            """,

            "time_series": """
                SELECT 
                    toDate(created_at_pt) as date,
                    toHour(created_at_pt) as hour,
                    COUNT(DISTINCT order_id) as order_count,
                    SUM(item_total_amt) as revenue
                FROM dw.fact_order_item_variations
                WHERE pay_status = 'COMPLETED'
                    {date_filter}
                GROUP BY date, hour
                ORDER BY date, hour
            """,

            "new_customers": """
                WITH first_orders AS (
                    SELECT 
                        customer_id,
                        MIN(toDate(created_at_pt)) as first_order_date
                    FROM dw.fact_order_item_variations
                    WHERE pay_status = 'COMPLETED'
                    GROUP BY customer_id
                )
                SELECT 
                    first_order_date as date,
                    COUNT(*) as new_customers
                FROM first_orders
                WHERE {date_filter}
                GROUP BY date
                ORDER BY date DESC
            """,
            "group_item_sales": """
                        WITH group_item_sales AS (
                                   SELECT
        				 arrayStringConcat(arraySort(arrayDistinct(groupArray(item_name))), ',') AS item_list,
                            COUNT(*) as sales_count,    -- 订单中包含的item数量
                            SUM(item_total_amt) as total_revenue,
                            AVG(item_total_amt) as avg_price
                        FROM dw.fact_order_item_variations
                        WHERE pay_status = 'COMPLETED'
                            AND {date_filter}
                        GROUP BY order_id
                        order by item_list
                                )
                                SELECT 
                                	item_list,
                                      SUM(total_revenue) as group_total_revenue, -- 订单的总销售额
                                      count(*) as group_order_count, -- 订单数量
                            		AVG(avg_price) as group_avg_price  -- 订单平均价格
                                FROM group_item_sales
                                WHERE  sales_count>1 -- 订单中包含的item数量大于1，排除非组合订单，选出多商品订单
                                GROUP BY item_list
                                ORDER BY group_order_count DESC
                            """
        }

    async def generate_sql_from_question(self, question: str, context: Dict[str, Any] = None) -> Tuple[
        str, Dict[str, Any]]:
        """根据用户问题生成SQL"""

        # 1. 分析问题意图
        intent = self._analyze_question_intent(question)

        # 2. 提取关键信息
        entities = self._extract_entities(question)

        # 3. 选择合适的查询模板或生成自定义SQL
        # sql = self._generate_sql(intent, entities, context)
        sql = await self._generate_sql_llm(question, intent, entities, context)
        # 4. 返回SQL和元数据
        metadata = {
            "intent": intent,
            "entities": entities,
            "query_type": self._determine_query_type(intent),
            "visualization_type": self._suggest_visualization(intent)
        }

        return sql, metadata

    def _analyze_question_intent(self, question: str) -> Dict[str, Any]:
        """分析问题意图"""
        question_lower = question.lower()

        intent = {
            "type": "general",
            "metrics": [],
            "dimensions": [],
            "filters": [],
            "aggregation": None,
            "time_range": None
        }

        # 识别指标
        if any(word in question_lower for word in ["销售", "营收", "收入", "销售额"]):
            intent["metrics"].append("revenue")
        if any(word in question_lower for word in ["订单", "单量", "订单数"]):
            intent["metrics"].append("order_count")
        if any(word in question_lower for word in ["客户", "用户", "顾客"]):
            intent["metrics"].append("customers")
        if any(word in question_lower for word in ["客单价", "aov", "平均"]):
            intent["metrics"].append("aov")
        if any(word in question_lower for word in ["商品", "产品", "item"]):
            intent["metrics"].append("items")
        if any(word in question_lower for word in ["新增", "新客", "新用户"]):
            intent["metrics"].append("new_customers")

        # 识别维度
        if any(word in question_lower for word in ["店铺", "门店", "location"]):
            intent["dimensions"].append("location")
        if any(word in question_lower for word in ["产品", "商品", "类别", "category"]):
            intent["dimensions"].append("product")
        if any(word in question_lower for word in ["时间", "趋势", "走势", "变化"]):
            intent["dimensions"].append("time")
        if any(word in question_lower for word in ["小时", "时段"]):
            intent["dimensions"].append("hour")

        # 识别时间范围
        if "今天" in question_lower or "今日" in question_lower:
            intent["time_range"] = "today"
        elif "昨天" in question_lower or "昨日" in question_lower:
            intent["time_range"] = "yesterday"
        elif "本周" in question_lower or "这周" in question_lower:
            intent["time_range"] = "this_week"
        elif "上周" in question_lower:
            intent["time_range"] = "last_week"
        elif "本月" in question_lower or "这个月" in question_lower:
            intent["time_range"] = "this_month"
        elif "上月" in question_lower or "上个月" in question_lower:
            intent["time_range"] = "last_month"
        elif "最近" in question_lower:
            # 提取天数
            import re
            days_match = re.search(r'最近(\d+)天', question_lower)
            if days_match:
                intent["time_range"] = f"last_{days_match.group(1)}_days"
            else:
                intent["time_range"] = "last_7_days"

        # 识别聚合类型
        if any(word in question_lower for word in ["对比", "比较", "排名"]):
            intent["aggregation"] = "comparison"
        elif any(word in question_lower for word in ["趋势", "走势", "变化"]):
            intent["aggregation"] = "trend"
        elif any(word in question_lower for word in ["分布", "构成", "占比"]):
            intent["aggregation"] = "distribution"
        elif any(word in question_lower for word in ["top", "前", "最高", "最多"]):
            intent["aggregation"] = "top"

        return intent

    def _extract_entities(self, question: str) -> Dict[str, Any]:
        """提取实体信息"""
        entities = {}

        # 提取数字
        import re
        numbers = re.findall(r'\d+', question)
        if numbers:
            entities["numbers"] = [int(n) for n in numbers]

        # 提取日期
        date_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        dates = re.findall(date_pattern, question)
        if dates:
            entities["dates"] = dates

        # 提取店铺名称（简单匹配）
        if "CA-" in question or "IL-" in question or "TX-" in question or "AZ-" in question:
            store_pattern = r'((?:CA|IL|TX|AZ)-[\w-]+)'
            stores = re.findall(store_pattern, question)
            if stores:
                entities["stores"] = stores

        # 提取产品类别
        categories = ["Milk Tea", "Coffee", "Fruit Tea", "Snacks", "奶茶", "咖啡", "果茶", "小食"]
        found_categories = [cat for cat in categories if cat.lower() in question.lower()]
        if found_categories:
            entities["categories"] = found_categories

        return entities

    def _generate_sql(self, intent: Dict[str, Any], entities: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """生成SQL查询"""

        # 根据意图选择模板
        if "revenue" in intent["metrics"] and "time" in intent["dimensions"]:
            template = self.query_templates["time_series"]
        elif "new_customers" in intent["metrics"]:
            template = self.query_templates["new_customers"]
        elif "product" in intent["dimensions"]:
            template = self.query_templates["product_performance"]
        elif "location" in intent["dimensions"]:
            template = self.query_templates["store_comparison"]
        elif "customers" in intent["metrics"] and not intent["dimensions"]:
            template = self.query_templates["customer_analysis"]
        else:
            template = self.query_templates["daily_sales"]

        # 生成日期过滤条件
        date_filter = self._generate_date_filter(intent["time_range"], entities.get("dates"))

        # 替换模板中的占位符
        sql = template.format(
            date_filter=date_filter,
            limit=entities.get("numbers", [10])[0] if entities.get("numbers") else 10,
            where_clause=""
        )

        # 添加额外的过滤条件
        if entities.get("stores"):
            stores_str = "', '".join(entities["stores"])
            sql = sql.replace("WHERE", f"WHERE location_name IN ('{stores_str}') AND")

        if entities.get("categories"):
            categories_str = "', '".join(entities["categories"])
            sql = sql.replace("WHERE", f"WHERE category_name IN ('{categories_str}') AND")

        return sql.strip()

    def _generate_date_filter(self, time_range: str, specific_dates: List[str] = None) -> str:
        """生成日期过滤条件"""

        if specific_dates:
            # 使用具体日期
            if len(specific_dates) == 1:
                return f"AND toDate(created_at_pt) = '{specific_dates[0]}'"
            elif len(specific_dates) == 2:
                return f"AND toDate(created_at_pt) BETWEEN '{specific_dates[0]}' AND '{specific_dates[1]}'"

        # 根据时间范围生成
        today = datetime.now()

        if time_range == "today":
            date = today.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) = '{date}'"
        elif time_range == "yesterday":
            date = (today - timedelta(days=1)).strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) = '{date}'"
        elif time_range == "this_week":
            start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"
        elif time_range == "last_week":
            start = (today - timedelta(days=today.weekday() + 7)).strftime('%Y-%m-%d')
            end = (today - timedelta(days=today.weekday() + 1)).strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"
        elif time_range == "this_month":
            start = today.replace(day=1).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"
        elif time_range == "last_month":
            first_day = today.replace(day=1)
            last_month = first_day - timedelta(days=1)
            start = last_month.replace(day=1).strftime('%Y-%m-%d')
            end = last_month.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"
        elif time_range and time_range.startswith("last_") and "_days" in time_range:
            # 最近N天
            days = int(time_range.replace("last_", "").replace("_days", ""))
            start = (today - timedelta(days=days)).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"
        else:
            # 默认最近7天
            start = (today - timedelta(days=7)).strftime('%Y-%m-%d')
            end = today.strftime('%Y-%m-%d')
            return f"AND toDate(created_at_pt) BETWEEN '{start}' AND '{end}'"

    def _determine_query_type(self, intent: Dict[str, Any]) -> str:
        """确定查询类型"""
        if intent["aggregation"] == "trend":
            return "time_series"
        elif intent["aggregation"] == "comparison":
            return "comparison"
        elif intent["aggregation"] == "distribution":
            return "distribution"
        elif intent["aggregation"] == "top":
            return "ranking"
        else:
            return "summary"

    def _suggest_visualization(self, intent: Dict[str, Any]) -> str:
        """建议可视化类型"""
        if intent["aggregation"] == "trend" or "time" in intent["dimensions"]:
            return "line"
        elif intent["aggregation"] == "comparison":
            return "bar"
        elif intent["aggregation"] == "distribution":
            return "pie"
        elif intent["aggregation"] == "top":
            return "bar"
        else:
            return "table"

    async def execute_sql(self, sql: str) -> pd.DataFrame:
        """执行SQL查询"""
        try:
            df = await get_db().execute_query_async(sql)
            return df
        except Exception as e:
            print(f"SQL execution error: {e}")
            raise

    async def process_question(self, question: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户问题并返回结果"""
        try:
            # 生成SQL
            sql, metadata = await self.generate_sql_from_question(question, context)

            # 执行查询
            df = await self.execute_sql(sql)

            # 格式化结果
            result = self._format_results(df, metadata)

            return {
                "success": True,
                "sql": sql,
                "metadata": metadata,
                "data": result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "sql": None,
                "data": None
            }

    def _format_results(self, df: pd.DataFrame, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """格式化查询结果"""

        if df.empty:
            return {"type": "empty", "message": "没有找到相关数据"}

        viz_type = metadata.get("visualization_type", "table")

        if viz_type == "line":
            # 格式化为线图数据
            return {
                "type": "chart",
                "chart_type": "line",
                "data": {
                    "x": df.iloc[:, 0].tolist(),  # 第一列作为X轴
                    "series": [
                        {
                            "name": col,
                            "data": df[col].tolist()
                        }
                        for col in df.columns[1:]
                    ]
                }
            }
        elif viz_type == "bar":
            # 格式化为柱状图数据
            return {
                "type": "chart",
                "chart_type": "bar",
                "data": {
                    "categories": df.iloc[:, 0].tolist(),
                    "series": [
                        {
                            "name": col,
                            "data": df[col].tolist()
                        }
                        for col in df.columns[1:]
                    ]
                }
            }
        elif viz_type == "pie":
            # 格式化为饼图数据
            return {
                "type": "chart",
                "chart_type": "pie",
                "data": {
                    "labels": df.iloc[:, 0].tolist(),
                    "values": df.iloc[:, 1].tolist()
                }
            }
        else:
            # 格式化为表格数据
            return {
                "type": "table",
                "columns": [{"key": col, "title": col} for col in df.columns],
                "rows": df.to_dict('records')
            }

    async def _generate_sql_llm(self, question: str, intent: Dict[str, Any], entities: Dict[str, Any],
                                context: Dict[str, Any] = None) -> str:
        """生成SQL查询"""

        # 根据意图选择模板
        # if "revenue" in intent["metrics"] and "time" in intent["dimensions"]:
        #     template = self.query_templates["time_series"]
        # elif "new_customers" in intent["metrics"]:
        #     template = self.query_templates["new_customers"]
        # elif "product" in intent["dimensions"]:
        #     template = self.query_templates["product_performance"]
        # elif "location" in intent["dimensions"]:
        #     template = self.query_templates["store_comparison"]
        # elif "customers" in intent["metrics"] and not intent["dimensions"]:
        #     template = self.query_templates["customer_analysis"]
        # else:
        #     template = self.query_templates["daily_sales"]

        # 生成日期过滤条件
        date_filter = self._generate_date_filter(intent["time_range"], entities.get("dates"))
        # 添加额外的过滤条件



        prompt = f"""
              你是一个clickhouse 数据库 sql编写工具。根据问题分析需要获取的数据，并输出sql查询语句
              问题：{question}
              要求：
              1. 只输出sql 不输出任何其他信息
              2. 不需要对sql进行解释说明
              3. 时间条件使用具体时间，比如 toDate(created_at_pt) = '2025-08-06'
              4. 适当限制最终返回数据行数，最高取关键前100条数据
              5. 注意订单表fact_order_item_variations是fact_orders表的明细表是根据订单每个商品进行分行，注意和fact_orders区分
              6. 模板只是举例，生成sql可以不局限于模版内容
              7. 一般情况下只统计已完成的订单需要添加 WHERE pay_status = 'COMPLETED'
              8. 未明确要求查询深度时不要直接查询明细信息，优先查询统计信息，数据汇总到问题包含的维度
              ==============clickhouse数据结构信息=======
              -- ads.customer_profile definition
CREATE TABLE ads.customer_profile
(
    `customer_id` String,
    `given_name` Nullable(String),
    `family_name` Nullable(String),
    `company_name` Nullable(String),
    `email_address` Nullable(String),
    `address_line` Nullable(String),
    `locality` Nullable(String),
    `country` Nullable(String),
    `phone_number` Nullable(String),
    `birthday` Nullable(String),
    `creation_source` Nullable(String),
    `merchant_id` Nullable(String),
    `location_id` Nullable(String),
    `location_name` Nullable(String),
    `customer_created_date` Nullable(Date),
    `customer_created_months` Nullable(Int64),
    `first_order_from_register_days` Nullable(Int64),
    `loyalty_created_date` Nullable(Date),
    `order_final_total_cnt` UInt64,
    `order_final_total_amt` Decimal(38,
 2),
    `order_final_avg_amt` Float64,
    `order_first_date` Nullable(DateTime),
    `order_last_date` Nullable(DateTime),
    `offline` Bool,
    `dormant` Bool,
    `ultra_low_frequency` Bool,
    `hardcore` Bool,
    `silent` Bool,
    `loyal` Bool,
    `regular` Bool,
    `potential` Bool,
    `high_spending` Bool,
    `medium_spending` Bool,
    `low_spending` Bool,
    `highly_active` Bool,
    `moderately_active` Bool,
    `low_active` Bool,
    `churned` Bool,
    `high_value_customer` Bool,
    `high_potential_customer` Bool,
    `key_development_customer` Bool,
    `regular_customer` Bool,
    `critical_win_back_customer` Bool,
    `general_value_customer` Bool,
    `general_win_back_customer` Bool,
    `inactive_customer` Bool,
    `rfm_labels` Array(Nullable(String)),
    `loyalty_labels` Array(Nullable(String)),
    `consumption_labels` Array(Nullable(String))
)
-- dw.dim_catalog_categories definition
CREATE TABLE dw.dim_catalog_categories
(
    `category_id` String,
    `category_name` Nullable(String),
    `category_type` Nullable(String),
    `parent_category_id` Nullable(String),
    `root_category` Nullable(String),
    `is_top_level` Nullable(UInt8),
    `channels` Nullable(String),
    `merchant_id` Nullable(String),
    `image_ids` Nullable(String),
    `present_at_all_locations` Nullable(UInt8),
    `present_at_location_ids` Nullable(String),
    `absent_at_location_ids` Nullable(String),
    `availability_period_ids` Nullable(String),
    `path_to_root` Nullable(String),
    `version` Nullable(Int64),
    `is_deleted` Nullable(UInt8),
    `updated_at` DateTime,
    `synced_time` Nullable(DateTime)
)
-- dw.dim_catalog_items definition
CREATE TABLE dw.dim_catalog_items
(
    `item_id` String,
    `item_name` Nullable(String),
    `original_item_name` String,
    `description_plaintext` Nullable(String),
    `channels` Nullable(String),
    `product_type` Nullable(String),
    `modifier_list_ids` Array(String),
    `category_ids` Array(String),
    `category_names` Array(String),
    `reporting_category_id` Nullable(String),
    `reporting_category_name` String,
    `is_archived` Nullable(UInt8),
    `merchant_id` Nullable(String),
    `abbreviation` Nullable(String),
    `tax_ids` Nullable(String),
    `skip_modifier_screen` Nullable(UInt8),
    `item_options` Nullable(String),
    `image_ids` Nullable(String),
    `sort_name` Nullable(String),
    `present_at_all_locations` Nullable(UInt8),
    `present_at_location_ids` Nullable(String),
    `absent_at_location_ids` Nullable(String),
    `version` Nullable(Int64),
    `is_deleted` Nullable(UInt8),
    `source` String,
    `updated_at` DateTime,
    `synced_time` Nullable(DateTime)
)
-- dw.dim_customers definition
CREATE TABLE dw.dim_customers
(
    `customer_id` String,
    `account_id` Nullable(String),
    `given_name` Nullable(String),
    `family_name` Nullable(String),
    `nickname` Nullable(String),
    `customer_race` String,
    `company_name` Nullable(String),
    `email_address` Nullable(String),
    `address_line` Nullable(String),
    `locality` Nullable(String),
    `administrative_district_level_1` Nullable(String),
    `postal_code` Nullable(String),
    `country` Nullable(String),
    `phone_number` Nullable(String),
    `birthday` Nullable(String),
    `reference_id` Nullable(String),
    `note` Nullable(String),
    `creation_source` Nullable(String),
    `data_source` String,
    `segment_ids` Array(String),
    `is_text_subscriber` UInt8,
    `is_email_subscriber` UInt8,
    `version` Nullable(Int64),
    `merchant_id` Nullable(String),
    `created_at` DateTime64(3),
    `created_at_pt` DateTime,
    `customer_created_at_pt` Nullable(DateTime),
    `loyalty_created_at_pt` Nullable(DateTime),
    `updated_at` DateTime64(3),
    `synced_time` Nullable(DateTime)
)
-- dw.dim_locations definition
CREATE TABLE dw.dim_locations
(
    `location_id` String,
    `location_name` Nullable(String),
    `address_line` Nullable(String),
    `locality` Nullable(String),
    `locality_population` Int64,
    `administrative_district_level_1` Nullable(String),
    `postal_code` Nullable(String),
    `country` Nullable(String),
    `status` Nullable(String),
    `created_at` DateTime,
    `created_at_pt` DateTime('America/Los_Angeles'),
    `phone_number` Nullable(String),
    `business_name` Nullable(String),
    `type` Nullable(String),
    `coordinates` Nullable(String),
    `mcc` Nullable(String),
    `merchant_id` Nullable(String),
    `synced_time` Nullable(DateTime)
)
-- dw.fact_orders definition
CREATE TABLE dw.fact_orders
(
    `order_id` String,
    `location_id` Nullable(String),
    `location_name` Nullable(String),
    `locality` Nullable(String),
    `source` Nullable(String),
    `source_type` String,
    `status` Nullable(String),
    `pay_status` String,
    `customer_id` Nullable(String),
    `original_customer_id` Nullable(String),
    `customer_created_at_pt` Nullable(DateTime),
    `loyalty_created_at_pt` Nullable(DateTime),
    `is_loyalty` UInt8,
    `is_new_users` Array(UInt8),
    `is_reactives` Array(UInt8),
    `is_text_subscriber` UInt8,
    `is_email_subscriber` UInt8,
    `customer_race` String,
    `total_amount` Nullable(Decimal(9,
 2)),
    `subtotal` Nullable(Decimal(9,
 2)),
    `tax` Nullable(Decimal(9,
 2)),
    `discount` Nullable(Decimal(9,
 2)),
    `tip` Nullable(Decimal(9,
 2)),
    `service_charge` Nullable(Decimal(9,
 2)),
    `item_names` Array(String),
    `campaign_names` Array(String),
    `merchant_id` Nullable(String),
    `tenders` Nullable(String),
    `created_at` DateTime64(3),
    `created_at_pt` DateTime,
    `updated_at` DateTime64(3)
)
-- dw.fact_order_item_variations definition
CREATE TABLE dw.fact_order_item_variations
(
    `order_id` String,
    `order_item_variation_id` String,
    `item_variation_id` Nullable(String),
    `item_variation_name` Nullable(String),
    `item_id` Nullable(String),
    `item_name` Nullable(String),
    `original_item_name` Nullable(String),
    `category_name` String,
    `location_id` Nullable(String),
    `location_name` Nullable(String),
    `status` Nullable(String),
    `pay_status` String,
    `source_type` String,
    `source` Nullable(String),
    `merchant_id` Nullable(String),
    `customer_id` Nullable(String),
    `is_loyalty` UInt8,
    `is_new_users` Array(UInt8),
    `is_reactives` Array(UInt8),
    `item_names` Array(String),
    `campaign_names` Array(String),
    `item_qty` Int16,
    `item_amt` Decimal(9,
 2),
    `item_total_amt` Decimal(9,
 2),
    `item_tax` Decimal(9,
 2),
    `item_discount` Decimal(9,
 2),
    `service_charge` Decimal(9,
 2),
    `total_modifier` Decimal(38,
 2),
    `created_at` DateTime64(3),
    `created_at_pt` DateTime64(3)
)
 =====表说明=====
 {self.table_schemas}
 ====根据问题转换的部分过滤条件=====
   时间：{date_filter}
   {
    f"商品类目名词:'{entities.get("categories")}')" if entities.get("categories") else ""
   }
   {
       f"门店名词:'{entities.get("stores")}')" if entities.get("stores") else ""
   }
 ====查询参考模板=====
 {self.query_templates}
              """

        response = self.llm_service.client.chat.completions.create(
            model=self.llm_service.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        sql = response.choices[0].message.content
        sql = sql.strip('```sql').strip('```').strip(";").strip()
        return sql.strip()
