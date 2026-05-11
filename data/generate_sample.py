"""OceanQC 샘플 데이터 생성 스크립트.

실행:
    python data/generate_sample.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# `python data/generate_sample.py` 실행 시에도 프로젝트 루트 import가 되도록 보정
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import DOMAIN_BOUNDS

SEED = 42
N_DAYS = 90
HOURS_PER_DAY = 24

STATIONS = [
    {
        "station_id": "OBS_A",
        "station_name": "모의 관측소 A",
        "region": "동해",
        "latitude": 37.5,
        "longitude": 129.3,
    },
    {
        "station_id": "OBS_B",
        "station_name": "모의 관측소 B",
        "region": "남해",
        "latitude": 34.7,
        "longitude": 128.1,
    },
    {
        "station_id": "OBS_C",
        "station_name": "모의 관측소 C",
        "region": "서해",
        "latitude": 36.1,
        "longitude": 125.9,
    },
]

MEASURE_COLS = [
    "wind_speed",
    "wind_direction",
    "wave_height",
    "air_temperature",
    "water_temperature",
    "humidity",
    "pressure",
]


def _base_station_frame(station: dict, datetimes: pd.DatetimeIndex, rng: np.random.Generator) -> pd.DataFrame:
    """관측소 1곳의 시간별 기초 데이터를 생성한다."""
    n = len(datetimes)

    # 계절/일주기 변동을 단순하게 표현하기 위한 파형
    day_cycle = np.sin(np.linspace(0, 8 * np.pi, n))

    wind_speed = np.clip(rng.normal(loc=6.5, scale=2.0, size=n), 0, None)
    wind_direction = rng.uniform(0, 360, size=n)
    wave_height = np.clip(rng.normal(loc=1.2, scale=0.5, size=n), 0, None)
    air_temperature = rng.normal(loc=14.0, scale=6.0, size=n) + day_cycle
    water_temperature = rng.normal(loc=13.0, scale=4.0, size=n) + 0.5 * day_cycle
    humidity = np.clip(rng.normal(loc=72.0, scale=12.0, size=n), 0, 100)
    pressure = rng.normal(loc=1012.0, scale=6.5, size=n)

    return pd.DataFrame(
        {
            "datetime": datetimes,
            "station_id": station["station_id"],
            "station_name": station["station_name"],
            "region": station["region"],
            "latitude": station["latitude"],
            "longitude": station["longitude"],
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "wave_height": wave_height,
            "air_temperature": air_temperature,
            "water_temperature": water_temperature,
            "humidity": humidity,
            "pressure": pressure,
        }
    )


def _inject_missing(df: pd.DataFrame, rng: np.random.Generator, frac: float = 0.08) -> pd.DataFrame:
    """수치 관측 컬럼에 결측치를 주입한다."""
    out = df.copy()
    for col in MEASURE_COLS:
        idx = out.sample(frac=frac, random_state=int(rng.integers(0, 1_000_000))).index
        out.loc[idx, col] = np.nan
    return out


def _inject_outliers(df: pd.DataFrame, rng: np.random.Generator, frac: float = 0.02) -> pd.DataFrame:
    """도메인 임계값을 벗어나는 이상치를 주입한다."""
    out = df.copy()
    n_outliers = max(1, int(len(out) * frac))

    for col, (lower, upper) in DOMAIN_BOUNDS.items():
        valid_idx = out.index[out[col].notna()]
        if len(valid_idx) == 0:
            continue

        sampled_idx = rng.choice(valid_idx.to_numpy(), size=min(n_outliers, len(valid_idx)), replace=False)
        half = len(sampled_idx) // 2
        lower_idx = sampled_idx[:half]
        upper_idx = sampled_idx[half:]

        lower_gap = (upper - lower) * 0.2 + 1
        upper_gap = (upper - lower) * 0.2 + 1

        if len(lower_idx) > 0:
            out.loc[lower_idx, col] = lower - rng.uniform(1, lower_gap, size=len(lower_idx))
        if len(upper_idx) > 0:
            out.loc[upper_idx, col] = upper + rng.uniform(1, upper_gap, size=len(upper_idx))

    return out


def generate_sample() -> pd.DataFrame:
    """OceanQC 기본 샘플 데이터를 생성한다."""
    rng = np.random.default_rng(SEED)
    periods = N_DAYS * HOURS_PER_DAY
    datetimes = pd.date_range("2024-01-01 00:00:00", periods=periods, freq="h")

    frames = [_base_station_frame(station, datetimes, rng) for station in STATIONS]
    df = pd.concat(frames, ignore_index=True)

    df = _inject_missing(df, rng=rng, frac=0.08)
    df = _inject_outliers(df, rng=rng, frac=0.02)

    df = df.sort_values(["station_id", "datetime"]).reset_index(drop=True)
    return df


def main() -> None:
    """CSV 파일로 샘플 데이터를 저장한다."""
    output_path = Path(__file__).resolve().parent / "sample.csv"
    df = generate_sample()
    df.to_csv(output_path, index=False, encoding="utf-8")

    print("샘플 데이터 생성 완료 ✅")
    print(f"저장 경로: {output_path}")
    print(f"총 행 수: {len(df):,}")
    print(f"총 열 수: {len(df.columns)}")


if __name__ == "__main__":
    main()
