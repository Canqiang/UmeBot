import decimal
from typing import Any, Dict, List, Union
import requests
from datetime import datetime, timedelta


def get_weather_summary(latitude: float, longitude: float, timezone: str = "UTC"):
    """
    获取当前日期、实时天气，以及过去7天和未来7天的天气数据。

    返回:
    {
        "date": "YYYY-MM-DD",
        "current_weather": {
            "temperature": float,
            "windspeed": float,
            "winddirection": float,
            "weathercode": int
        },
        "past_7_days": [
            {"date": "YYYY-MM-DD", "temp_max": float, "temp_min": float, "precipitation": float, "weathercode": int},
            ...
        ],
        "next_7_days": [
            {"date": "YYYY-MM-DD", "temp_max": float, "temp_min": float, "precipitation": float, "weathercode": int},
            ...
        ]
    }
    """
    # 当前日期
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")

    # 调用 Open-Meteo 实时及日数据接口
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weathercode",
        "timezone": timezone,
        "start_date": (now.date() - timedelta(days=7)).isoformat(),
        "end_date": (now.date() + timedelta(days=7)).isoformat()
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    data = resp.json()

    # 实时天气
    cw = data.get("current_weather", {})
    current = {
        "temperature": cw.get("temperature"),
        "windspeed": cw.get("windspeed"),
        "winddirection": cw.get("winddirection"),
        "weathercode": cw.get("weathercode")
    }

    # 日数据
    times = data["daily"]["time"]
    tmax = data["daily"]["temperature_2m_max"]
    tmin = data["daily"]["temperature_2m_min"]
    precip = data["daily"]["precipitation_sum"]
    codes = data["daily"]["weathercode"]

    past = []
    future = []
    for d, mx, mn, pr, wc in zip(times, tmax, tmin, precip, codes):
        entry = {"date": d, "temp_max": mx, "temp_min": mn, "precipitation": pr, "weathercode": wc}
        if d < date_str:
            past.append(entry)
        else:
            future.append(entry)

    return {
        "date": date_str,
        "current_weather": current,
        "past_7_days": past,
        "next_7_days": future
    }

def convert_to_json_serializable(obj: Any) -> Any:
    """递归转换对象为 JSON 可序列化格式"""
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_to_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_json_serializable(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_to_json_serializable(item) for item in obj)
    elif hasattr(obj, '__dict__'):
        return convert_to_json_serializable(obj.__dict__)
    else:
        return obj