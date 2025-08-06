import sys
import types
from pathlib import Path

import pandas as pd
import pytest

# Ensure backend package is importable
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Stub heavy dependency to avoid import errors
stub = types.ModuleType("app.fixed_causal_inference")
class UMeCausalInferenceEngine:
    pass
stub.UMeCausalInferenceEngine = UMeCausalInferenceEngine
sys.modules["app.fixed_causal_inference"] = stub

# Stub config module
config_stub = types.ModuleType("app.config")
config_stub.settings = types.SimpleNamespace(CLICKHOUSE_CONFIG={})
sys.modules["app.config"] = config_stub

from app.analysis_service import AnalysisService


@pytest.mark.parametrize("date_col", ["order_date", "ds"])
def test_calculate_trends_with_alternate_date_column(date_col):
    df = pd.DataFrame({
        date_col: ["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"],
        "total_revenue": [100, 200, 300, 400],
        "order_count": [10, 20, 30, 40],
        "unique_customers": [1, 2, 3, 4],
    })
    service = AnalysisService()
    trends = service._calculate_trends(df)
    assert trends["total_revenue"] == 133.33


def test_calculate_trends_with_index_dates():
    df = pd.DataFrame({
        "total_revenue": [100, 200, 300, 400],
        "order_count": [10, 20, 30, 40],
        "unique_customers": [1, 2, 3, 4],
    }, index=pd.date_range("2023-01-01", periods=4, freq="D"))
    service = AnalysisService()
    trends = service._calculate_trends(df)
    assert trends["total_revenue"] == 133.33
