import sys
import types
from pathlib import Path

import asyncio
import pytest

# Ensure backend package importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub config
config_stub = types.ModuleType("app.config")
config_stub.settings = types.SimpleNamespace(
    OPENAI_API_KEY="key",
    OPENAI_BASE_URL="https://example.com",
    OPENAI_MODEL="gpt-test",
    OPENAI_API_VERSION="v1",
)
sys.modules["app.config"] = config_stub

# Stub openai
openai_stub = types.ModuleType("openai")
class AzureOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **k: None))
openai_stub.AzureOpenAI = AzureOpenAI
sys.modules["openai"] = openai_stub

from app.llm_service import LLMService


def test_llm_intent_parsing_high_confidence(monkeypatch):
    service = LLMService()

    async def mock_llm(query: str):
        return {"intent_type": "data_query", "entities": {"query_target": "orders"}, "confidence": 0.9}

    monkeypatch.setattr(service, "_parse_intent_with_llm", mock_llm)
    intent = asyncio.run(service.parse_query_intent("查询订单数量"))
    assert intent["intent_type"] == "data_query"
    assert intent["entities"]["query_target"] == "orders"
    assert intent["confidence"] == 0.9


def test_llm_intent_parsing_low_confidence_fallback(monkeypatch):
    service = LLMService()

    async def mock_llm(query: str):
        return {"intent_type": "data_query", "entities": {}, "confidence": 0.2}

    monkeypatch.setattr(service, "_parse_intent_with_llm", mock_llm)
    intent = asyncio.run(service.parse_query_intent("预测明天的销量"))
    assert intent["intent_type"] == "forecast"
    assert intent["confidence"] == 0.2
    assert intent["entities"]["forecast_type"] == "sales"


def test_generate_response_includes_intent(monkeypatch):
    service = LLMService()

    async def mock_parse(query: str):
        return {
            "query": query,
            "intent_type": "general",
            "needs_data": False,
            "entities": {},
            "time_range": None,
            "confidence": 0.8,
        }

    async def mock_general(user_message, data, history):
        return {"message": "ok", "data": None}

    monkeypatch.setattr(service, "parse_query_intent", mock_parse)
    monkeypatch.setattr(service, "_generate_general_response", mock_general)

    result = asyncio.run(service.generate_response("hello"))
    assert result["intent"]["confidence"] == 0.8
