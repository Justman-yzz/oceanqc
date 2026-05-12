"""관측소별 품질 지표 계산 모듈."""

from __future__ import annotations

import pandas as pd

from config import DOMAIN_BOUNDS
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
