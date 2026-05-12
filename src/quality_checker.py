"""관측소별 품질 지표 계산 모듈."""

from __future__ import annotations

import pandas as pd

from config import ALERT_CONDITION, DOMAIN_BOUNDS, GRADE_THRESHOLDS
from src.preprocessor import detect_all_outliers


def calc_availability_rate(df: pd.DataFrame) -> pd.DataFrame:
    """관측소별 데이터 가용률(%)을 계산한다.

    가용률(%) = (전체 셀 - 결측 셀 - 이상치 셀) / 전체 셀 * 100
    계산 대상은 DOMAIN_BOUNDS 키에 해당하는 수치 컬럼이다.
    """
    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("가용률 계산 대상 수치 컬럼이 없습니다.")

    if "station_name" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: station_name")

    outlier_mask = detect_all_outliers(df)

    rows = []
    for station_name, station_df in df.groupby("station_name", dropna=False):
        station_idx = station_df.index
        total_cells = len(station_df) * len(metric_cols)

        missing_cells = int(station_df[metric_cols].isna().sum().sum())
        outlier_cells = int(outlier_mask.loc[station_idx, metric_cols].sum().sum())

        valid_cells = total_cells - missing_cells - outlier_cells
        availability_rate = (valid_cells / total_cells * 100) if total_cells > 0 else 0.0

        rows.append(
            {
                "station_name": station_name,
                "availability_rate": round(float(availability_rate), 2),
            }
        )

    return pd.DataFrame(rows).sort_values("station_name").reset_index(drop=True)


def grade_station(availability_rate: float) -> str:
    """가용률 기준으로 품질 등급(A~F)을 반환한다."""
    if availability_rate >= GRADE_THRESHOLDS["A"]:
        return "A"
    if availability_rate >= GRADE_THRESHOLDS["B"]:
        return "B"
    if availability_rate >= GRADE_THRESHOLDS["C"]:
        return "C"
    if availability_rate >= GRADE_THRESHOLDS["D"]:
        return "D"
    return "F"


def check_alert(station_df: pd.DataFrame, availability_rate: float) -> bool:
    """주의 필요 관측소 여부를 반환한다.

    조건:
    1) 가용률 < ALERT_CONDITION["min_availability"]
    2) 연속 결측 일수 >= ALERT_CONDITION["consecutive_missing_days"]
    둘 중 하나라도 만족하면 True
    """
    min_availability = ALERT_CONDITION["min_availability"]
    required_days = ALERT_CONDITION["consecutive_missing_days"]

    if availability_rate < min_availability:
        return True

    if "datetime" not in station_df.columns:
        raise ValueError("필수 컬럼이 없습니다: datetime")

    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in station_df.columns]
    if not metric_cols:
        return False

    temp = station_df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date

    # 하루라도 수치 컬럼이 하나 이상 결측이면 해당 날짜를 결측일로 간주
    daily_missing = (
        temp.groupby("date")[metric_cols]
        .apply(lambda x: x.isna().any(axis=1).any())
        .reset_index(name="is_missing_day")
    )

    streak = 0
    for is_missing in daily_missing["is_missing_day"]:
        if is_missing:
            streak += 1
            if streak >= required_days:
                return True
        else:
            streak = 0

    return False


def build_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    """관측소별 품질 요약 테이블을 생성한다."""
    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("품질 요약 대상 수치 컬럼이 없습니다.")

    if "station_name" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: station_name")

    outlier_mask = detect_all_outliers(df)
    availability_df = calc_availability_rate(df).set_index("station_name")

    rows = []
    for station_name, station_df in df.groupby("station_name", dropna=False):
        station_idx = station_df.index
        total_records = int(len(station_df))
        total_cells = total_records * len(metric_cols)

        missing_cells = int(station_df[metric_cols].isna().sum().sum())
        outlier_cells = int(outlier_mask.loc[station_idx, metric_cols].sum().sum())

        missing_rate = (missing_cells / total_cells * 100) if total_cells > 0 else 0.0
        outlier_rate = (outlier_cells / total_cells * 100) if total_cells > 0 else 0.0

        availability_rate = float(availability_df.loc[station_name, "availability_rate"])
        grade = grade_station(availability_rate)
        is_alert = check_alert(station_df, availability_rate)

        rows.append(
            {
                "station_name": station_name,
                "total_records": total_records,
                "missing_rate": round(missing_rate, 2),
                "outlier_rate": round(outlier_rate, 2),
                "availability_rate": round(availability_rate, 2),
                "grade": grade,
                "is_alert": is_alert,
            }
        )

    result = pd.DataFrame(rows)
    return result.sort_values("availability_rate", ascending=False).reset_index(drop=True)
