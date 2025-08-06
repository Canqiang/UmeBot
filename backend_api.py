"""
UMe Bot 后端API服务
集成LLM和数据分析功能
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
import pandas as pd
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv

# 导入我们的分析引擎
from fixed_causal_inference import UMeCausalInferenceEngine

load_dotenv()

app = FastAPI(title="UMe Bot API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI客户端初始化
client = OpenAI(api_key='sk-Fmiw2WNajQ7fkU6thUpMqKEUCTk2D1r1JGmRWfv8k7p8s1pu',base_url='https://api.openai-proxy.org/v1')

# ClickHouse配置
CLICKHOUSE_CONFIG = {
    "host": os.getenv("CLICKHOUSE_HOST", "clickhouse-0-0.umetea.net"),
    "port": int(os.getenv("CLICKHOUSE_PORT", 443)),
    "database": os.getenv("CLICKHOUSE_DB", "dw"),
    "user": os.getenv("CLICKHOUSE_USER", "ml_ume"),
    "password": os.getenv("CLICKHOUSE_PASSWORD", "hDAoDvg8x552bH"),
    "verify": False,
}

# 初始化分析引擎
analysis_engine = UMeCausalInferenceEngine(CLICKHOUSE_CONFIG)


# 数据模型
class ChatMessage(BaseModel):
    message: str
    timestamp: Optional[datetime] = None


class AnalysisRequest(BaseModel):
    start_date: str
    end_date: str
    analysis_type: str = "full"  # full, sales, forecast, attribution


class DataMetrics(BaseModel):
    total_revenue: float
    active_users: int
    conversion_rate: float
    avg_session_time: float
    changes: Dict[str, float]


# 模拟数据（实际应从数据库获取）
def get_mock_metrics() -> DataMetrics:
    """获取模拟指标数据"""
    return DataMetrics(
        total_revenue=942876,
        active_users=2143,
        conversion_rate=15.8,
        avg_session_time=870,  # 秒
        changes={
            "total_revenue": 7.15,
            "active_users": 8.3,
            "conversion_rate": 2.1,
            "avg_session_time": -1.2
        }
    )


def get_real_metrics(start_date: str, end_date: str) -> Dict[str, Any]:
    """从真实数据获取指标"""
    try:
        # 运行完整分析
        results = analysis_engine.run_complete_analysis(start_date, end_date, include_forecast=True)

        # 提取关键指标
        enhanced_data = results.get('enhanced_data')
        if enhanced_data is None:
            return None

        # 计算指标
        total_revenue = enhanced_data['total_revenue'].sum()
        unique_customers = enhanced_data['unique_customers'].sum()
        total_orders = enhanced_data['order_count'].sum()
        conversion_rate = (total_orders / unique_customers * 100) if unique_customers > 0 else 0

        # 计算环比变化
        mid_date = pd.to_datetime(start_date) + (pd.to_datetime(end_date) - pd.to_datetime(start_date)) / 2
        first_half = enhanced_data[enhanced_data['date'] < mid_date]
        second_half = enhanced_data[enhanced_data['date'] >= mid_date]

        revenue_change = ((second_half['total_revenue'].sum() - first_half['total_revenue'].sum()) /
                          first_half['total_revenue'].sum() * 100) if first_half['total_revenue'].sum() > 0 else 0

        return {
            'metrics': {
                'total_revenue': float(total_revenue),
                'unique_customers': int(unique_customers),
                'total_orders': int(total_orders),
                'conversion_rate': float(conversion_rate),
                'avg_order_value': float(total_revenue / total_orders) if total_orders > 0 else 0
            },
            'changes': {
                'revenue': float(revenue_change),
                'customers': float(np.random.uniform(-5, 10)),  # 模拟数据
                'orders': float(np.random.uniform(-5, 10)),
                'conversion': float(np.random.uniform(-2, 5))
            },
            'analysis_results': results.get('analysis_results', {}),
            'forecast_results': results.get('forecast_results', {})
        }
    except Exception as e:
        print(f"获取真实数据失败: {e}")
        return None


def generate_trend_data(days: int = 30) -> List[Dict[str, Any]]:
    """生成趋势数据"""
    base_value = 1000
    dates = []
    values = []

    for i in range(days):
        date = (datetime.now() - timedelta(days=days - i - 1)).strftime('%m/%d')
        value = base_value + np.random.randint(-100, 200) + i * 10
        dates.append(date)
        values.append(value)

    return {
        'dates': dates,
        'values': values
    }


def analyze_with_llm(question: str, context: Dict[str, Any]) -> str:
    """使用LLM分析数据并回答问题"""
    try:
        # 构建上下文
        system_prompt = """
        你是UMe茶饮的数据分析助手。你需要基于提供的数据分析结果，用专业但易懂的方式回答用户问题。

        回答要求：
        1. 使用数据支撑观点
        2. 提供可行的建议
        3. 语言简洁明了
        4. 适当使用表情符号使回答更友好
        """

        context_str = f"""
        当前数据概览：
        - 总营收: ${context.get('total_revenue', 0):,.0f}
        - 活跃用户: {context.get('active_users', 0):,}
        - 转化率: {context.get('conversion_rate', 0):.1f}%
        - 主要发现: {json.dumps(context.get('key_findings', {}), ensure_ascii=False)}
        """

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_str}\n\n用户问题：{question}"}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"LLM分析失败: {e}")
        return "抱歉，我暂时无法分析这个问题。请稍后再试。"


# API路由
@app.get("/")
async def root():
    return {"message": "UMe Bot API is running"}


@app.get("/api/metrics")
async def get_metrics(start_date: Optional[str] = None, end_date: Optional[str] = None):
    """获取数据指标"""
    if start_date and end_date:
        real_data = get_real_metrics(start_date, end_date)
        if real_data:
            return {
                "status": "success",
                "data": real_data['metrics'],
                "changes": real_data['changes'],
                "analysis": real_data.get('analysis_results', {})
            }

    # 返回模拟数据
    metrics = get_mock_metrics()
    return {
        "status": "success",
        "data": metrics.dict(),
        "changes": metrics.changes
    }


@app.get("/api/trends/{metric}")
async def get_trends(metric: str, days: int = 30):
    """获取趋势数据"""
    trend_data = generate_trend_data(days)
    return {
        "status": "success",
        "metric": metric,
        "data": trend_data
    }


@app.post("/api/analyze")
async def analyze_data(request: AnalysisRequest):
    """运行数据分析"""
    try:
        results = analysis_engine.run_complete_analysis(
            request.start_date,
            request.end_date,
            include_forecast=True
        )

        # 提取关键结果
        summary = {
            "period": results.get('analysis_period', {}),
            "data_summary": results.get('data_summary', {}),
            "key_findings": {},
            "forecast": results.get('forecast_results', {}).get('summary', {})
        }

        # 提取主要发现
        analysis_results = results.get('analysis_results', {})
        for factor, result in analysis_results.items():
            if isinstance(result, dict) and 'ate' in result and result.get('significant'):
                summary['key_findings'][factor] = {
                    'effect': result['ate'],
                    'confidence': [result.get('ci_lower', 0), result.get('ci_upper', 0)]
                }

        return {
            "status": "success",
            "data": summary
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """聊天接口"""
    # 获取当前数据上下文
    context = {
        "total_revenue": 942876,
        "active_users": 2143,
        "conversion_rate": 15.8,
        "key_findings": {
            "promotion_effect": "促销活动带来了15%的营收提升",
            "weekend_effect": "周末销售额比平日高30%"
        }
    }

    # 使用LLM生成回复
    response = analyze_with_llm(message.message, context)

    return {
        "status": "success",
        "reply": response,
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """WebSocket聊天接口（实时通信）"""
    await websocket.accept()

    try:
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 处理消息
            if message_data.get("type") == "chat":
                # 获取数据上下文
                context = {
                    "total_revenue": 942876,
                    "active_users": 2143,
                    "conversion_rate": 15.8
                }

                # 生成回复
                response = analyze_with_llm(message_data.get("message", ""), context)

                # 发送回复
                await websocket.send_json({
                    "type": "reply",
                    "message": response,
                    "timestamp": datetime.now().isoformat()
                })

            elif message_data.get("type") == "get_metrics":
                # 发送实时指标
                metrics = get_mock_metrics()
                await websocket.send_json({
                    "type": "metrics",
                    "data": metrics.dict()
                })

    except Exception as e:
        print(f"WebSocket错误: {e}")
    finally:
        await websocket.close()


# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)