"""OceanQC 공통 설정값.

도메인 임계값, 품질 등급 기준, 알림 조건, 관측소 색상을 한곳에서 관리한다.
"""

from __future__ import annotations

DOMAIN_BOUNDS = {
    "wind_speed": (0, 50),
    "wave_height": (0, 15),
    "air_temperature": (-20, 45),
    "water_temperature": (-2, 35),
    "humidity": (0, 100),
    "pressure": (950, 1050),
    "wind_direction": (0, 360),
}

GRADE_THRESHOLDS = {
    "A": 95.0,
    "B": 90.0,
    "C": 80.0,
    "D": 70.0,
    # 70% 미만은 F
}

ALERT_CONDITION = {
    "min_availability": 80.0,
    "consecutive_missing_days": 3,
}

STATION_COLORS = {
    "모의 관측소 01": "#1f77b4",
    "모의 관측소 02": "#ff7f0e",
    "모의 관측소 03": "#7b9e4a",
    "모의 관측소 04": "#9467bd",
    "모의 관측소 05": "#2ca02c",
    "모의 관측소 06": "#17becf",
    "모의 관측소 07": "#8c564b",
    "모의 관측소 08": "#e377c2",
    "모의 관측소 09": "#bcbd22",
    "모의 관측소 10": "#7f7f7f",
}

WIND_LINE_GAP_THRESHOLDS = {
    "safe_max_missing_ratio": 0.10,  # 10% 미만: 실선
    "warn_max_missing_ratio": 0.50,  # 10~50%: 점선, 50% 이상: 끊김
}
