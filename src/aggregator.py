"""집계 모듈."""

from __future__ import annotations

import pandas as pd

from config import DOMAIN_BOUNDS


def daily_mean(df: pd.DataFrame) -> pd.DataFrame:
    """날짜별 × 관측소별 수치 컬럼 평균을 계산한다."""
    if "datetime" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: datetime")
    if "station_name" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: station_name")

    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("집계 대상 수치 컬럼이 없습니다.")

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date"])

    grouped = (
        temp.groupby(["date", "station_name"], dropna=False)[metric_cols]
        .mean()
        .reset_index()
    )
    return grouped


def station_pivot(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """행=날짜, 열=관측소명, 값=value_col 평균 형태의 피벗 테이블을 반환한다."""
    if "datetime" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: datetime")
    if "station_name" not in df.columns:
        raise ValueError("필수 컬럼이 없습니다: station_name")
    if value_col not in df.columns:
        raise ValueError(f"요청한 컬럼이 없습니다: {value_col}")

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date"])

    pivot = temp.pivot_table(
        index="date",
        columns="station_name",
        values=value_col,
        aggfunc="mean",
    )
    return pivot.round(2)
