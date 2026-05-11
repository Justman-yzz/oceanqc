"""CSV 로딩 및 컬럼 검증 모듈."""

from __future__ import annotations

import pandas as pd

REQUIRED_COLUMNS = [
    "datetime",
    "station_id",
    "station_name",
    "region",
    "latitude",
    "longitude",
    "wind_speed",
    "wind_direction",
    "wave_height",
    "air_temperature",
    "water_temperature",
    "humidity",
    "pressure",
]


def validate_columns(df: pd.DataFrame, required: list[str]) -> None:
    """필수 컬럼 존재 여부를 확인한다."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"누락된 컬럼: {missing}")


def load_csv(filepath: str) -> pd.DataFrame:
    """CSV를 로드하고 datetime 기준 오름차순으로 정렬해 반환한다."""
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError as exc:
        raise ValueError(f"입력 파일을 찾을 수 없습니다: {filepath}") from exc
    except Exception as exc:
        raise ValueError(f"CSV 파일 로드 중 오류가 발생했습니다: {exc}") from exc

    validate_columns(df, REQUIRED_COLUMNS)

    try:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="raise")
    except Exception as exc:
        raise ValueError("datetime 컬럼 변환에 실패했습니다. 형식을 확인해주세요.") from exc

    return df.sort_values("datetime").reset_index(drop=True)
