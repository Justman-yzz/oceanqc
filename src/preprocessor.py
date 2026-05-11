"""결측치 요약 및 이상치 탐지 모듈."""

from __future__ import annotations

import pandas as pd

from config import DOMAIN_BOUNDS


def summarize_missing(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼별 결측치 수/비율(%)을 반환한다. 결측치 0인 컬럼은 제외한다."""
    if df.empty:
        return pd.DataFrame(columns=["column", "missing_count", "missing_rate"])

    missing_count = df.isna().sum()
    missing_rate = (missing_count / len(df) * 100).round(2)

    result = pd.DataFrame(
        {
            "column": missing_count.index,
            "missing_count": missing_count.values,
            "missing_rate": missing_rate.values,
        }
    )
    result = result[result["missing_count"] > 0].reset_index(drop=True)
    return result


def detect_outliers_domain(df: pd.DataFrame) -> pd.DataFrame:
    """DOMAIN_BOUNDS 기준 1차 이상치를 탐지한다. (True=이상치)"""
    outliers = pd.DataFrame(False, index=df.index, columns=df.columns)

    for col, (lower, upper) in DOMAIN_BOUNDS.items():
        if col not in df.columns:
            continue
        series = df[col]
        mask = series.notna() & ((series < lower) | (series > upper))
        outliers[col] = mask

    return outliers


def detect_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """IQR(1.5배) 기준 2차 이상치를 탐지한다. (True=이상치)"""
    outliers = pd.DataFrame(False, index=df.index, columns=df.columns)

    for col in DOMAIN_BOUNDS:
        if col not in df.columns:
            continue

        valid = df[col].dropna()
        if valid.empty:
            continue

        q1 = valid.quantile(0.25)
        q3 = valid.quantile(0.75)
        iqr = q3 - q1

        if pd.isna(iqr) or iqr == 0:
            continue

        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        series = df[col]
        mask = series.notna() & ((series < lower) | (series > upper))
        outliers[col] = mask

    return outliers


def detect_all_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """도메인 + IQR 이상치를 OR로 합산한다. (True=이상치)"""
    domain_outliers = detect_outliers_domain(df)
    iqr_outliers = detect_outliers_iqr(df)
    return domain_outliers | iqr_outliers
