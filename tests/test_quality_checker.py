import pandas as pd

from src.quality_checker import calc_availability_rate, grade_station


# 1) 가용률 96.0은 A 등급이어야 한다.
def test_grade_station_96_is_a() -> None:
    assert grade_station(96.0) == "A"


# 2) 가용률 75.0은 D 등급이어야 한다.
def test_grade_station_75_is_d() -> None:
    assert grade_station(75.0) == "D"


# 3) 가용률 60.0은 F 등급이어야 한다.
def test_grade_station_60_is_f() -> None:
    assert grade_station(60.0) == "F"


# 4) 경계값 95.0은 A 등급이어야 한다.
def test_grade_station_95_is_a_boundary() -> None:
    assert grade_station(95.0) == "A"


# 5) 결측치가 포함되면 가용률은 100.0 미만이어야 한다.
def test_calc_availability_rate_with_missing_is_less_than_100() -> None:
    df = pd.DataFrame(
        {
            "station_name": ["모의 관측소 A", "모의 관측소 A"],
            "wind_speed": [5.0, None],
        }
    )

    result = calc_availability_rate(df)
    assert result.loc[0, "availability_rate"] < 100.0
