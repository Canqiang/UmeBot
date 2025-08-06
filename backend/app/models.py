# ============== config.py ==============
"""
数据模型定义
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    """聊天消息"""
    message: str
    timestamp: Optional[datetime] = None
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AnalysisRequest(BaseModel):
    """分析请求"""
    start_date: str
    end_date: str
    analysis_type: str = "full"  # full, sales, forecast, attribution
    include_forecast: bool = False
    parameters: Optional[Dict[str, Any]] = None


class DataQuery(BaseModel):
    """数据查询"""
    question: str
    context: Optional[List[Dict[str, Any]]] = None
    session_id: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None


class MetricsData(BaseModel):
    """指标数据"""
    total_revenue: float
    total_orders: int
    unique_customers: int
    avg_order_value: float
    conversion_rate: Optional[float] = None
    changes: Optional[Dict[str, float]] = None


class ChartData(BaseModel):
    """图表数据"""
    type: str  # line, bar, pie, scatter
    title: str
    x_axis: List[Any]
    y_axis: List[Any]
    series: Optional[List[Dict[str, Any]]] = None
    options: Optional[Dict[str, Any]] = None


class TableData(BaseModel):
    """表格数据"""
    columns: List[Dict[str, str]]  # [{key: 'id', title: 'ID', type: 'string'}]
    rows: List[Dict[str, Any]]
    total: Optional[int] = None
    page: Optional[int] = 1
    page_size: Optional[int] = 20


class CausalEffect(BaseModel):
    """因果效应"""
    factor: str
    effect: float
    confidence_interval: List[float]
    significant: bool
    sample_size: int


class ForecastData(BaseModel):
    """预测数据"""
    dates: List[str]
    values: List[float]
    confidence_lower: Optional[List[float]] = None
    confidence_upper: Optional[List[float]] = None
    method: str = "Prophet"


class DetailRequest(BaseModel):
    """详情请求"""
    detail_type: str  # store_performance, product_analysis, etc.
    params: Dict[str, Any]
    session_id: Optional[str] = None


class BotResponse(BaseModel):
    """机器人响应"""
    message: str
    data: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    related_questions: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)