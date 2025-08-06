"""
聊天会话管理器
管理对话历史和会话状态
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import asyncio
from collections import defaultdict


class ChatSession:
    """聊天会话"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.messages: List[Dict[str, Any]] = []
        self.context: Dict[str, Any] = {}
        self.analysis_cache: Dict[str, Any] = {}

    def add_message(self, role: str, content: str, data: Any = None):
        """添加消息到历史"""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.messages.append(message)
        self.last_activity = datetime.now()

        # 保持历史记录在合理范围内（最多50条）
        if len(self.messages) > 50:
            self.messages = self.messages[-50:]

    def get_history(self, max_messages: int = 10) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return self.messages[-max_messages:]

    def update_context(self, key: str, value: Any):
        """更新会话上下文"""
        self.context[key] = value
        self.last_activity = datetime.now()

    def cache_analysis(self, key: str, data: Any, ttl: int = 3600):
        """缓存分析结果"""
        self.analysis_cache[key] = {
            "data": data,
            "cached_at": datetime.now(),
            "ttl": ttl
        }

    def get_cached_analysis(self, key: str) -> Optional[Any]:
        """获取缓存的分析结果"""
        if key in self.analysis_cache:
            cache_entry = self.analysis_cache[key]
            cached_at = cache_entry["cached_at"]
            ttl = cache_entry["ttl"]

            # 检查是否过期
            if datetime.now() - cached_at < timedelta(seconds=ttl):
                return cache_entry["data"]
            else:
                # 过期则删除
                del self.analysis_cache[key]

        return None


class ChatManager:
    """聊天管理器"""

    def __init__(self):
        self.sessions: Dict[str, ChatSession] = {}
        self.cleanup_interval = 3600  # 1小时清理一次
        self.session_timeout = 7200  # 2小时会话超时
        self._cleanup_task = None

    async def initialize(self):
        """初始化管理器"""
        # 启动清理任务
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def cleanup(self):
        """清理管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def _cleanup_loop(self):
        """定期清理过期会话"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")

    async def _cleanup_expired_sessions(self):
        """清理过期的会话"""
        now = datetime.now()
        expired_sessions = []

        for session_id, session in self.sessions.items():
            if now - session.last_activity > timedelta(seconds=self.session_timeout):
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            print(f"Cleaning up expired session: {session_id}")
            del self.sessions[session_id]

    async def create_or_get_session(self, session_id: str) -> ChatSession:
        """创建或获取会话"""
        if session_id not in self.sessions:
            self.sessions[session_id] = ChatSession(session_id)
            print(f"Created new session: {session_id}")
        else:
            print(f"Retrieved existing session: {session_id}")

        return self.sessions[session_id]

    async def add_message(self, session_id: str, role: str, content: str, data: Any = None):
        """添加消息到会话"""
        session = await self.create_or_get_session(session_id)
        session.add_message(role, content, data)

    async def get_history(self, session_id: str, max_messages: int = 10) -> List[Dict[str, Any]]:
        """获取会话历史"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_history(max_messages)
        return []

    async def update_context(self, session_id: str, key: str, value: Any):
        """更新会话上下文"""
        session = await self.create_or_get_session(session_id)
        session.update_context(key, value)

    async def get_context(self, session_id: str) -> Dict[str, Any]:
        """获取会话上下文"""
        if session_id in self.sessions:
            return self.sessions[session_id].context
        return {}

    async def cache_analysis(self, session_id: str, key: str, data: Any, ttl: int = 3600):
        """缓存分析结果到会话"""
        session = await self.create_or_get_session(session_id)
        session.cache_analysis(key, data, ttl)

    async def get_cached_analysis(self, session_id: str, key: str) -> Optional[Any]:
        """从会话获取缓存的分析结果"""
        if session_id in self.sessions:
            return self.sessions[session_id].get_cached_analysis(key)
        return None

    async def cleanup_session(self, session_id: str):
        """清理特定会话"""
        if session_id in self.sessions:
            print(f"Cleaning up session: {session_id}")
            # 可以在这里保存会话历史到数据库
            del self.sessions[session_id]

    def get_active_sessions_count(self) -> int:
        """获取活跃会话数"""
        return len(self.sessions)

    def get_sessions_info(self) -> List[Dict[str, Any]]:
        """获取所有会话信息"""
        sessions_info = []
        for session_id, session in self.sessions.items():
            sessions_info.append({
                "session_id": session_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "message_count": len(session.messages),
                "has_context": bool(session.context),
                "cached_analyses": list(session.analysis_cache.keys())
            })
        return sessions_info