# ============== config.py ==============
"""
配置管理
"""
from pydantic_settings import BaseSettings
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()  # 可选，Pydantic BaseSettings 通常也会自动加载 .env

class Settings(BaseSettings):
    """应用配置"""

    # 基础配置
    APP_NAME: str = "UMe Bot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # API 配置
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # OpenAI 配置
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str = ""
    OPENAI_MODEL: str = ""

    # ClickHouse 配置
    CLICKHOUSE_HOST: str
    CLICKHOUSE_PORT: int
    CLICKHOUSE_DB: str
    CLICKHOUSE_USER: str
    CLICKHOUSE_PASSWORD: str

    # 缓存配置
    CACHE_TTL: int = 3600  # 1小时

    # 会话配置
    SESSION_TIMEOUT: int = 7200  # 2小时
    SESSION_CLEANUP_INTERVAL: int = 3600  # 1小时

    # 安全配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @property
    def CLICKHOUSE_CONFIG(self) -> Dict[str, Any]:
        return {
            "host": self.CLICKHOUSE_HOST,
            "port": self.CLICKHOUSE_PORT,
            "database": self.CLICKHOUSE_DB,
            "user": self.CLICKHOUSE_USER,
            "password": self.CLICKHOUSE_PASSWORD,
            "verify": False
        }

    class Config:
        env_file = ".env"
        extra = "forbid"

settings = Settings()
