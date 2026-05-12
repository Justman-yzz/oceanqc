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


def fill_missing(df: pd.DataFrame, strategy: str = "ffill") -> pd.DataFrame:
    """결측치를 전략에 따라 처리한다."""
    # 이전 시점의 값을 앞으로 채움
    if strategy == "ffill":  # 운영 관점에서 시계열 연속성이 필요할 때(짧은 공백 메우기)
        return df.ffill()
    # 앞뒤 값을 직선으로 연결해 중간 결측을 보정
    if strategy == "linear":  # 추세선이 부드럽게 이어지길 원할 때(짧은 간격 보간)
        return df.interpolate(method="linear")
    # 원본 그대로 반환(결측 보정 안 함)
    if strategy == "none":  # 품질 진단 원본 기준으로 결측률/가용률/알림 판단할 때
        return df
    # 그 외 값. 잘못된 CLI 입력을 초기에 명확히 막기 위함
    raise ValueError("지원하지 않는 결측치 처리 전략입니다. (ffill, linear, none)")
