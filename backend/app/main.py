# backend/app/main.py
"""
UMe Bot 后端主应用 - 修复WebSocket连接问题
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
import uuid
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.chat_manager import ChatManager
from app.llm_service import LLMService
from app.analysis_service import AnalysisService
from app.models import ChatMessage, AnalysisRequest, DataQuery

from backend.app.sql_generator import SQLGeneratorService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 全局管理器
chat_manager = ChatManager()
llm_service = LLMService()
analysis_service = AnalysisService()
sql_generator = SQLGeneratorService(llm_service)

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        logger.info(f"WebSocket connected: {session_id}")

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
            logger.info(f"WebSocket disconnected: {session_id}")

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Starting UMe Bot Backend...")
    await analysis_service.initialize()
    yield
    logger.info("👋 Shutting down UMe Bot Backend...")
    await analysis_service.cleanup()


app = FastAPI(
    title="UMe Bot API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置 - 更宽松的配置以支持WebSocket
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，生产环境应该指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


# API路由
@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "running",
        "service": "UMe Bot API",
        "timestamp": datetime.now().isoformat(),
        "websocket_endpoint": "/ws/{session_id}"
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/daily-report")
async def get_daily_report():
    """获取日报数据"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        report = await analysis_service.get_daily_report(yesterday, today)

        return JSONResponse(content=report)
    except Exception as e:
        logger.error(f"Error getting daily report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze(request: AnalysisRequest):
    """运行分析"""
    try:
        result = await analysis_service.run_analysis(
            request.start_date,
            request.end_date,
            request.analysis_type
        )
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Error running analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def query_data(query: DataQuery):
    """查询数据"""
    try:
        intent = await llm_service.parse_query_intent(query.question)

        data = await analysis_service.get_data_by_intent(intent)

        response = await llm_service.generate_response(
            query.question,
            data,
            query.context or []
        )

        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecast/{days}")
async def get_forecast(days: int = 7):
    """获取销售预测"""
    try:
        forecast = await analysis_service.get_forecast(days)
        return JSONResponse(content=forecast)
    except Exception as e:
        logger.error(f"Error getting forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/details")
async def get_details(request: Dict[str, Any]):
    """获取详细数据"""
    try:
        detail_type = request.get("detail_type")
        params = request.get("params", {})

        details = await analysis_service.get_detail_data(detail_type, params)

        return JSONResponse(content=details)
    except Exception as e:
        logger.error(f"Error getting details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# WebSocket路由 - 修复版本
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    session_id: str
):
    """WebSocket连接处理"""
    try:
        # 接受连接
        await manager.connect(websocket, session_id)

        # 创建或获取会话
        session = await chat_manager.create_or_get_session(session_id)

        # 发送欢迎消息
        welcome_message = {
            "type": "bot_message",
            "message": "你好！我是 UMe 数据助手。我可以帮你分析销售数据、查看因果关系、预测未来趋势。请问有什么可以帮助你的？",
            "timestamp": datetime.now().isoformat(),
            "data": None
        }
        await websocket.send_json(welcome_message)

        # 延迟后发送日报
        await asyncio.sleep(1)

        try:
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
        except Exception as e:
            logger.warning(f"Could not send daily report: {e}")

        # 消息处理循环
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message_data = json.loads(data)

                logger.info(f"Received message from {session_id}: {message_data.get('type', 'unknown')}")

                # 保存用户消息
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
                    # if intent.get("needs_data"):
                    analysis_data = await analysis_service.get_data_by_intent(intent)
                    exData = await sql_generator.process_question(intent.get("query"))
                    if exData.get("success"):
                        analysis_data["additional_data"] = exData.get("data")
                        logging.info(exData["sql"])

                    # 生成回复
                    bot_response = await llm_service.generate_response(
                        user_message,
                        analysis_data,
                        history
                    )

                    # 保存机器人回复
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

                elif message_data.get("type") == "ping":
                    # 处理心跳包
                    pong_message = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }
                    await websocket.send_json(pong_message)

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON from {session_id}: {e}")
                error_message = {
                    "type": "error",
                    "message": "消息格式错误",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(error_message)
            except Exception as e:
                logger.error(f"Error processing message from {session_id}: {e}")
                error_message = {
                    "type": "error",
                    "message": f"处理消息时出错：{str(e)}",
                    "timestamp": datetime.now().isoformat()
                }
                await websocket.send_json(error_message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
        manager.disconnect(session_id)
        await chat_manager.cleanup_session(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        manager.disconnect(session_id)
        await chat_manager.cleanup_session(session_id)
        # 不要重新抛出异常，让连接正常关闭


# 添加一个测试WebSocket的简单端点
@app.get("/test-ws")
async def test_websocket():
    """测试WebSocket连接的HTML页面"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>WebSocket Test</title>
    </head>
    <body>
        <h1>WebSocket Test</h1>
        <div id="messages"></div>
        <input type="text" id="messageText" autocomplete="off"/>
        <button onclick="sendMessage()">Send</button>
        <script>
            const sessionId = 'test_' + Date.now();
            const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
            
            ws.onopen = function(event) {
                console.log('WebSocket Connected');
                document.getElementById('messages').innerHTML += '<p>Connected!</p>';
            };
            
            ws.onmessage = function(event) {
                console.log('Message received:', event.data);
                document.getElementById('messages').innerHTML += '<p>Received: ' + event.data + '</p>';
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket Error:', error);
                document.getElementById('messages').innerHTML += '<p>Error: ' + error + '</p>';
            };
            
            ws.onclose = function(event) {
                console.log('WebSocket Closed');
                document.getElementById('messages').innerHTML += '<p>Connection closed</p>';
            };
            
            function sendMessage() {
                const input = document.getElementById('messageText');
                const message = {
                    type: 'chat',
                    message: input.value
                };
                ws.send(JSON.stringify(message));
                input.value = '';
            }
        </script>
    </body>
    </html>
    """
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn

    # 使用更详细的日志配置
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )