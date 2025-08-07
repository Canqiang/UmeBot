"""
UMe Bot 后端主应用
提供聊天API、数据分析和WebSocket服务
"""
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
import uuid
from contextlib import asynccontextmanager

from app.config import settings
from app.chat_manager import ChatManager
from app.llm_service import LLMService
from app.analysis_service import AnalysisService
from app.models import ChatMessage, AnalysisRequest, DataQuery

from backend.app.sql_generator import SQLGeneratorService

# 全局管理器
chat_manager = ChatManager()
llm_service = LLMService()
analysis_service = AnalysisService()
sql_generator = SQLGeneratorService(llm_service)
logging.basicConfig(
    level=logging.INFO,  # 日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
    format="%(asctime)s - %(levelname)s - %(message)s",  # 日志格式
    datefmt="%Y-%m-%d %H:%M:%S"  # 时间格式
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    print("🚀 Starting UMe Bot Backend...")
    await analysis_service.initialize()
    yield
    # 关闭时清理
    print("👋 Shutting down UMe Bot Backend...")
    await analysis_service.cleanup()


app = FastAPI(
    title="UMe Bot API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# API路由
@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "running",
        "service": "UMe Bot API",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/daily-report")
async def get_daily_report():
    """获取日报数据"""
    try:
        # 获取今日数据
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # 运行分析
        report = await analysis_service.get_daily_report(yesterday, today)

        return JSONResponse(content={
            "status": "success",
            "data": report
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_data(request: AnalysisRequest):
    """运行数据分析"""
    try:
        # 运行因果分析
        results = await analysis_service.run_causal_analysis(
            request.start_date,
            request.end_date,
            request.analysis_type
        )

        return JSONResponse(content={
            "status": "success",
            "data": results
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def query_data(query: DataQuery):
    """查询数据"""
    try:
        # 解析用户查询意图
        intent = await llm_service.parse_query_intent(query.question)

        # 根据意图获取数据
        data = await analysis_service.get_data_by_intent(intent)

        # 生成回复
        response = await llm_service.generate_response(
            query.question,
            data,
            query.context
        )

        return JSONResponse(content={
            "status": "success",
            "response": response,
            "data": data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/{days}")
async def get_forecast(days: int = 7):
    """获取销售预测"""
    try:
        forecast = await analysis_service.get_sales_forecast(days)

        return JSONResponse(content={
            "status": "success",
            "data": forecast
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket聊天连接"""
    await websocket.accept()

    # 创建或获取会话
    session = await chat_manager.create_or_get_session(session_id)

    try:
        # 发送欢迎消息
        welcome_message = {
            "type": "bot_message",
            "message": "你好！我是 UMe 数据助手。我可以帮你分析销售数据、查看因果关系、预测未来趋势。请问有什么可以帮助你的？",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }
        await websocket.send_json(welcome_message)

        # 自动发送日报
        await asyncio.sleep(1)
        daily_report = await analysis_service.get_daily_report_summary()
        if daily_report:
            report_message = {
                "type": "bot_message",
                "message": "这是今天的数据概览：",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "type": "daily_report",
                    "content": daily_report
                }
            }
            await websocket.send_json(report_message)

        # 消息循环
        while True:
            # 接收消息
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # 保存用户消息到历史
            await chat_manager.add_message(
                session_id,
                "user",
                message_data.get("message", "")
            )

            # 处理消息
            if message_data.get("type") == "chat":
                user_message = message_data.get("message", "")

                # 获取对话历史
                history = await chat_manager.get_history(session_id)

                # 解析意图
                intent = await llm_service.parse_query_intent(user_message)

                # 根据意图获取数据
                analysis_data = None
                if intent.get("needs_data"):
                    analysis_data = await analysis_service.get_data_by_intent(intent)
                    exData = await sql_generator.process_question(intent.get("query"))
                    if exData.get("success"):
                        analysis_data["exData"] = exData.get("data")
                        logging.info(exData["sql"])

                # 生成回复
                bot_response = await llm_service.generate_response(
                    user_message,
                    analysis_data,
                    history
                )

                # 保存机器人回复到历史
                await chat_manager.add_message(
                    session_id,
                    "bot",
                    bot_response["message"]
                )

                # 发送回复
                response_message = {
                    "type": "bot_message",
                    "message": bot_response["message"],
                    "timestamp": datetime.now().isoformat(),
                    "data": bot_response.get("data")
                }
                await websocket.send_json(response_message)

            elif message_data.get("type") == "get_details":
                # 获取详细数据
                detail_type = message_data.get("detail_type")
                detail_params = message_data.get("params", {})

                details = await analysis_service.get_detail_data(
                    detail_type,
                    detail_params
                )

                detail_message = {
                    "type": "data_details",
                    "data": details,
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(detail_message)

    except WebSocketDisconnect:
        print(f"Session {session_id} disconnected")
    except Exception as e:
        print(f"Error in websocket: {e}")
        error_message = {
            "type": "error",
            "message": f"抱歉，出现了错误：{str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send_json(error_message)
    finally:
        await chat_manager.cleanup_session(session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )