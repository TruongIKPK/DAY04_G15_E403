from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

WEEKDAYS_VI = [
    "Thứ Hai",
    "Thứ Ba",
    "Thứ Tư",
    "Thứ Năm",
    "Thứ Sáu",
    "Thứ Bảy",
    "Chủ Nhật",
]

WEEKDAYS_EN = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def get_time(offset_days: int = 0, query: str = "") -> dict[str, Any]:
    """
    Tra cứu thời gian, ngày tháng hiện tại hoặc tính toán ngày theo offset/query.
    """
    q = (query or "").lower().strip()
    if q and offset_days == 0:
        if "hôm qua" in q or "yesterday" in q:
            offset_days = -1
        elif "ngày mai" in q or "tomorrow" in q:
            offset_days = 1
        elif "hôm kia" in q:
            offset_days = -2
        elif "ngày kia" in q:
            offset_days = 2

    now = datetime.now()
    today_dt = now.date()
    yesterday_dt = today_dt - timedelta(days=1)
    tomorrow_dt = today_dt + timedelta(days=1)
    target_dt = today_dt + timedelta(days=offset_days)

    target_weekday_vi = WEEKDAYS_VI[target_dt.weekday()]
    target_weekday_en = WEEKDAYS_EN[target_dt.weekday()]

    formatted_vi = f"{target_weekday_vi}, ngày {target_dt.strftime('%d/%m/%Y')}"

    return {
        "tool": "get_time",
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "today": today_dt.strftime("%Y-%m-%d"),
        "today_vi": f"{WEEKDAYS_VI[today_dt.weekday()]}, ngày {today_dt.strftime('%d/%m/%Y')}",
        "yesterday": yesterday_dt.strftime("%Y-%m-%d"),
        "yesterday_vi": f"{WEEKDAYS_VI[yesterday_dt.weekday()]}, ngày {yesterday_dt.strftime('%d/%m/%Y')}",
        "tomorrow": tomorrow_dt.strftime("%Y-%m-%d"),
        "tomorrow_vi": f"{WEEKDAYS_VI[tomorrow_dt.weekday()]}, ngày {tomorrow_dt.strftime('%d/%m/%Y')}",
        "target_date": target_dt.strftime("%Y-%m-%d"),
        "target_date_vi": formatted_vi,
        "day_of_week": target_weekday_vi,
        "day_of_week_en": target_weekday_en,
        "offset_days": offset_days,
        "query": query,
    }
