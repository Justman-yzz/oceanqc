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
        "station_id": "OBS_01",
        "station_name": "모의 관측소 01",
        "region": "동해",
        "latitude": 37.5,
        "longitude": 129.3,
        "quality_tier": "A",
    },
    {
        "station_id": "OBS_02",
        "station_name": "모의 관측소 02",
        "region": "남해",
        "latitude": 34.7,
        "longitude": 128.1,
        "quality_tier": "B",
    },
    {
        "station_id": "OBS_03",
        "station_name": "모의 관측소 03",
        "region": "서해",
        "latitude": 36.1,
        "longitude": 125.9,
        "quality_tier": "C",
    },
    {
        "station_id": "OBS_04",
        "station_name": "모의 관측소 04",
        "region": "제주해역",
        "latitude": 33.4,
        "longitude": 126.5,
        "quality_tier": "C",
    },
    {
        "station_id": "OBS_05",
        "station_name": "모의 관측소 05",
        "region": "울릉해역",
        "latitude": 37.5,
        "longitude": 130.9,
        "quality_tier": "C",
    },
    {
        "station_id": "OBS_06",
        "station_name": "모의 관측소 06",
        "region": "남동해",
        "latitude": 35.2,
        "longitude": 129.8,
        "quality_tier": "D",
    },
    {
        "station_id": "OBS_07",
        "station_name": "모의 관측소 07",
        "region": "대한해협",
        "latitude": 34.0,
        "longitude": 129.0,
        "quality_tier": "D",
    },
    {
        "station_id": "OBS_08",
        "station_name": "모의 관측소 08",
        "region": "황해북부",
        "latitude": 37.8,
        "longitude": 124.5,
        "quality_tier": "D",
    },
    {
        "station_id": "OBS_09",
        "station_name": "모의 관측소 09",
        "region": "남해중부",
        "latitude": 34.4,
        "longitude": 127.2,
        "quality_tier": "F",
    },
    {
        "station_id": "OBS_10",
        "station_name": "모의 관측소 10",
        "region": "제주남부",
        "latitude": 32.5,
        "longitude": 126.8,
        "quality_tier": "F",
    },
]

# 티어별 품질 분포 범위: 값은 범위에서 샘플링되어 자연스럽게 변동한다.
TIER_QUALITY_RANGES = {
    "A": {
        "missing_rate": (0.018, 0.032),
        "outlier_rate": (0.009, 0.018),
        "missing_days": (2, 8),
        "burst_days": (0, 0),
    },
    "B": {
        "missing_rate": (0.035, 0.055),
        "outlier_rate": (0.018, 0.030),
        "missing_days": (5, 12),
        "burst_days": (0, 1),
    },
    "C": {
        "missing_rate": (0.070, 0.110),
        "outlier_rate": (0.030, 0.055),
        "missing_days": (10, 25),
        "burst_days": (0, 2),
    },
    "D": {
        "missing_rate": (0.120, 0.185),
        "outlier_rate": (0.060, 0.095),
        "missing_days": (20, 40),
        "burst_days": (2, 4),
    },
    "F": {
        "missing_rate": (0.205, 0.285),
        "outlier_rate": (0.105, 0.165),
        "missing_days": (32, 60),
        "burst_days": (3, 6),
    },
}

MEASURE_COLS = [
    "wind_speed",
    "wind_direction",
    "wave_height",
    "air_temperature",
    "water_temperature",
    "humidity",
    "pressure",
]


def _sample_station_profile(station: dict, rng: np.random.Generator) -> dict:
    """관측소의 기후/품질 프로파일을 티어 기반으로 샘플링한다."""
    lat = float(station["latitude"])
    lon = float(station["longitude"])

    # 위도/경도 기반으로 기후 기준값을 자연스럽게 변형
    southness = (37.5 - lat) / 6.0
    offshore = abs(lon - 127.0) / 4.0

    climate = {
        "wind_mean": float(np.clip(rng.normal(6.1 + 1.1 * offshore, 0.35), 4.8, 8.4)),
        "wave_mean": float(np.clip(rng.normal(1.0 + 0.45 * offshore, 0.14), 0.7, 2.3)),
        "air_temp_mean": float(
            np.clip(rng.normal(13.6 + 3.1 * southness, 0.6), 10.0, 18.8)
        ),
        "water_temp_mean": float(
            np.clip(rng.normal(13.0 + 3.5 * southness, 0.5), 9.5, 19.2)
        ),
        "humidity_mean": float(
            np.clip(rng.normal(72.0 + 2.8 * max(0.0, southness), 2.0), 66.0, 82.0)
        ),
        "pressure_mean": float(
            np.clip(rng.normal(1012.0 - 1.4 * southness, 1.2), 1008.5, 1015.2)
        ),
    }

    tier = station["quality_tier"]
    q = TIER_QUALITY_RANGES[tier]

    quality = {
        "missing_rate": float(rng.uniform(*q["missing_rate"])),
        "outlier_rate": float(rng.uniform(*q["outlier_rate"])),
        "missing_days": int(
            rng.integers(q["missing_days"][0], q["missing_days"][1] + 1)
        ),
        "burst_days": int(rng.integers(q["burst_days"][0], q["burst_days"][1] + 1)),
    }

    sampled = station.copy()
    sampled["climate"] = climate
    sampled["quality"] = quality
    return sampled


def _base_station_frame(
    station: dict, datetimes: pd.DatetimeIndex, rng: np.random.Generator
) -> pd.DataFrame:
    """관측소 1곳의 시간별 기초 데이터를 생성한다."""
    climate = station["climate"]
    n = len(datetimes)

    # 계절/일주기 변동을 단순하게 표현하기 위한 파형
    day_cycle = np.sin(np.linspace(0, 8 * np.pi, n))
    season_cycle = np.sin(np.linspace(0, 2 * np.pi, n))

    wind_speed = np.clip(
        rng.normal(loc=climate["wind_mean"], scale=2.0, size=n) + 0.8 * day_cycle,
        0,
        None,
    )
    wind_direction = rng.uniform(0, 360, size=n)
    wave_height = np.clip(
        rng.normal(loc=climate["wave_mean"], scale=0.55, size=n) + 0.25 * day_cycle,
        0,
        None,
    )
    air_temperature = (
        rng.normal(loc=climate["air_temp_mean"], scale=5.5, size=n)
        + 1.2 * season_cycle
        + 0.6 * day_cycle
    )
    water_temperature = (
        rng.normal(loc=climate["water_temp_mean"], scale=3.8, size=n)
        + 0.8 * season_cycle
        + 0.3 * day_cycle
    )
    humidity = np.clip(
        rng.normal(loc=climate["humidity_mean"], scale=11.0, size=n), 0, 100
    )
    pressure = rng.normal(loc=climate["pressure_mean"], scale=6.0, size=n)

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


def _inject_missing_by_station(
    df: pd.DataFrame, station: dict, rng: np.random.Generator
) -> pd.DataFrame:
    """관측소별 결측치 비율/연속 결측 구간을 주입한다."""
    out = df.copy()
    station_id = station["station_id"]
    quality = station["quality"]

    station_idx = out.index[out["station_id"] == station_id]
    if len(station_idx) == 0:
        return out

    missing_rate = quality["missing_rate"]
    missing_days = int(quality.get("missing_days", N_DAYS))

    station_dates = (
        out.loc[station_idx, "datetime"].dt.floor("D").sort_values().unique()
    )
    day_count = max(1, min(missing_days, len(station_dates)))
    chosen_days = rng.choice(station_dates, size=day_count, replace=False)
    chosen_days = pd.to_datetime(chosen_days)

    candidate_idx = out.index[
        (out["station_id"] == station_id)
        & (out["datetime"].dt.floor("D").isin(chosen_days))
    ]
    if len(candidate_idx) == 0:
        return out

    for col in MEASURE_COLS:
        n_missing = max(1, int(len(station_idx) * missing_rate))
        chosen = rng.choice(
            candidate_idx.to_numpy(),
            size=min(n_missing, len(candidate_idx)),
            replace=False,
        )
        out.loc[chosen, col] = np.nan

    # 일부 관측소는 연속 결측일을 강제로 삽입해 경보 조건 재현
    burst_days = int(quality.get("burst_days", 0))
    if burst_days > 0 and len(station_dates) >= burst_days:
        start_idx = int(rng.integers(0, len(station_dates) - burst_days + 1))
        burst_start = pd.Timestamp(station_dates[start_idx])
        burst_end = burst_start + pd.Timedelta(days=burst_days)

        burst_mask = (
            (out["station_id"] == station_id)
            & (out["datetime"] >= burst_start)
            & (out["datetime"] < burst_end)
        )
        burst_idx = out.index[burst_mask]
        if len(burst_idx) > 0:
            # 연속 결측일(alert) 재현을 위해 기준 컬럼은 burst 기간 전체 결측
            out.loc[burst_idx, "wind_speed"] = np.nan

            # 나머지 컬럼은 부분/시간대 결측으로 완화해 과도한 100% 결측 스파이크 방지
            extra_cols_pool = [c for c in MEASURE_COLS if c != "wind_speed"]
            extra_col_count = int(rng.integers(1, min(3, len(extra_cols_pool)) + 1))
            extra_cols = rng.choice(
                extra_cols_pool, size=extra_col_count, replace=False
            )

            for col in extra_cols:
                burst_hours = int(len(burst_idx))
                pick_hours = max(1, int(burst_hours * 0.35))
                chosen_hours = rng.choice(
                    burst_idx.to_numpy(),
                    size=min(pick_hours, burst_hours),
                    replace=False,
                )
                out.loc[chosen_hours, col] = np.nan

    return out


def _inject_outliers_by_station(
    df: pd.DataFrame, station: dict, rng: np.random.Generator
) -> pd.DataFrame:
    """관측소별 이상치 비율에 따라 도메인 초과값을 주입한다."""
    out = df.copy()
    station_id = station["station_id"]
    outlier_rate = station["quality"]["outlier_rate"]

    station_mask = out["station_id"] == station_id
    station_idx = out.index[station_mask]
    if len(station_idx) == 0:
        return out

    n_outliers = max(1, int(len(station_idx) * outlier_rate))

    for col, (lower, upper) in DOMAIN_BOUNDS.items():
        valid_idx = out.index[station_mask & out[col].notna()]
        if len(valid_idx) == 0:
            continue

        sampled_idx = rng.choice(
            valid_idx.to_numpy(), size=min(n_outliers, len(valid_idx)), replace=False
        )
        half = len(sampled_idx) // 2
        lower_idx = sampled_idx[:half]
        upper_idx = sampled_idx[half:]

        lower_gap = (upper - lower) * 0.2 + 1
        upper_gap = (upper - lower) * 0.2 + 1

        if len(lower_idx) > 0:
            out.loc[lower_idx, col] = lower - rng.uniform(
                1, lower_gap, size=len(lower_idx)
            )
        if len(upper_idx) > 0:
            out.loc[upper_idx, col] = upper + rng.uniform(
                1, upper_gap, size=len(upper_idx)
            )

    return out


def generate_sample() -> pd.DataFrame:
    """OceanQC 샘플 데이터를 생성한다."""
    rng = np.random.default_rng(SEED)
    periods = N_DAYS * HOURS_PER_DAY
    datetimes = pd.date_range("2024-01-01 00:00:00", periods=periods, freq="h")

    sampled_stations = [_sample_station_profile(station, rng) for station in STATIONS]

    frames = [
        _base_station_frame(station, datetimes, rng) for station in sampled_stations
    ]
    df = pd.concat(frames, ignore_index=True)

    for station in sampled_stations:
        df = _inject_missing_by_station(df, station=station, rng=rng)

    for station in sampled_stations:
        df = _inject_outliers_by_station(df, station=station, rng=rng)

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
