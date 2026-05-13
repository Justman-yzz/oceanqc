"""시각화 모듈."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import DOMAIN_BOUNDS, STATION_COLORS
from src.preprocessor import detect_all_outliers


GRADE_COLORS = {
    "A": "#639922",  # 초록
    "B": "#378ADD",  # 파랑
    "C": "#EF9F27",  # 주황
    "D": "#D85A30",  # 주황빨강
    "F": "#A32D2D",  # 빨강
}

STATION_SHORT_NAMES = {
    "모의 관측소 A": "obs-A",
    "모의 관측소 B": "obs-B",
    "모의 관측소 C": "obs-C",
}


def _require_columns(df: pd.DataFrame, required: list[str]) -> None:
    """필수 컬럼 존재 여부를 확인한다."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")


def _ordered_station_names(station_names: list[str]) -> list[str]:
    """관측소 이름을 STATION_COLORS 기준 순서로 정렬한다."""
    base_order = [name for name in STATION_COLORS.keys() if name in station_names]
    others = [name for name in station_names if name not in base_order]
    return base_order + sorted(others)


def _station_color(station_name: str) -> str:
    """관측소별 고정 색상을 반환한다."""
    return STATION_COLORS.get(station_name, "#8A8A8A")


def _station_label(station_name: str) -> str:
    """차트 범례용 축약 관측소명을 반환한다."""
    return STATION_SHORT_NAMES.get(station_name, station_name)


def chart_quality_grade(quality_df: pd.DataFrame) -> go.Figure:
    """관측소별 데이터 가용률 및 품질 등급 수평 막대 차트를 생성한다."""
    _require_columns(quality_df, ["station_name", "availability_rate", "grade"])

    plot_df = quality_df.sort_values("availability_rate", ascending=True).reset_index(
        drop=True
    )
    bar_colors = [GRADE_COLORS.get(g, "#8A8A8A") for g in plot_df["grade"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=plot_df["availability_rate"],
                y=plot_df["station_name"],
                orientation="h",
                marker={"color": bar_colors},
                text=plot_df["grade"],
                textposition="outside",
                hovertemplate=(
                    "관측소: %{y}<br>"
                    "가용률: %{x:.2f}%<br>"
                    "등급: %{text}<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="관측소별 데이터 가용률 및 품질 등급",
        xaxis_title="데이터 가용률(%)",
        yaxis_title="관측소",
        xaxis=dict(range=[0, 100]),
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig


def chart_missing_heatmap(df: pd.DataFrame) -> go.Figure:
    """날짜(행) × 관측소(열) 결측률 히트맵을 생성한다."""
    _require_columns(df, ["datetime", "station_name"])

    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("결측률 계산 대상 수치 컬럼이 없습니다.")

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date"])

    grouped = temp.groupby(["date", "station_name"], dropna=False)

    total_cells = grouped.size() * len(metric_cols)
    missing_cells = grouped[metric_cols].apply(lambda x: x.isna().sum().sum())
    missing_rate = (
        (missing_cells / total_cells * 100).rename("missing_rate").reset_index()
    )

    pivot = (
        missing_rate.pivot_table(
            index="date",
            columns="station_name",
            values="missing_rate",
            aggfunc="mean",
        )
        .fillna(0.0)
        .round(2)
    )

    ordered_cols = _ordered_station_names(pivot.columns.tolist())
    pivot = pivot.reindex(columns=ordered_cols)

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=pivot.values,
                x=[_station_label(col) for col in pivot.columns.tolist()],
                y=pivot.index.astype(str).tolist(),
                zmin=0,
                zmax=30,
                colorscale=[
                    [0.0, "#67B66B"],  # 초록 (0%)
                    [0.5, "#EF9F27"],  # 주황
                    [1.0, "#F3B5B5"],  # 연빨강 (30%+)
                ],
                colorbar={"title": "결측률(%)"},
                hovertemplate=(
                    "날짜: %{y}<br>"
                    "관측소: %{x}<br>"
                    "결측률: %{z:.2f}%<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="날짜별 관측소 결측률 히트맵",
        xaxis_title="관측소",
        yaxis_title="날짜",
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig


def chart_daily_wind_speed(df: pd.DataFrame) -> go.Figure:
    """일별 평균 풍속 라인 차트를 생성한다."""
    _require_columns(df, ["datetime", "station_name", "wind_speed"])

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date", "wind_speed"])

    daily = (
        temp.groupby(["date", "station_name"], dropna=False)["wind_speed"]
        .mean()
        .reset_index()
    )

    ordered_stations = _ordered_station_names(
        daily["station_name"].dropna().unique().tolist()
    )

    fig = go.Figure()
    for station_name in ordered_stations:
        station_df = daily[daily["station_name"] == station_name]
        if station_df.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=station_df["date"],
                y=station_df["wind_speed"],
                mode="lines",
                name=_station_label(station_name),
                line=dict(color=_station_color(station_name), width=2),
                hovertemplate=(
                    "날짜: %{x}<br>"
                    "관측소: %{fullData.name}<br>"
                    "평균 풍속: %{y:.2f} m/s<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="일별 평균 풍속 추이 (관측소별)",
        xaxis_title="날짜",
        yaxis_title="풍속(m/s)",
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig


def chart_wind_wave_scatter(df: pd.DataFrame) -> go.Figure:
    """풍속(x) × 파고(y) 산점도를 생성한다."""
    _require_columns(df, ["station_name", "wind_speed", "wave_height"])

    outlier_mask = detect_all_outliers(df)
    pair_outlier = outlier_mask[["wind_speed", "wave_height"]].any(axis=1)

    temp = df.copy()
    temp["is_outlier"] = pair_outlier
    plot_df = temp.dropna(subset=["wind_speed", "wave_height"])

    normal_df = plot_df[~plot_df["is_outlier"]]
    outlier_df = plot_df[plot_df["is_outlier"]]

    fig = go.Figure()

    ordered_stations = _ordered_station_names(
        normal_df["station_name"].dropna().unique().tolist()
    )
    for station_name in ordered_stations:
        station_df = normal_df[normal_df["station_name"] == station_name]
        if station_df.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=station_df["wind_speed"],
                y=station_df["wave_height"],
                mode="markers",
                name=_station_label(station_name),
                marker=dict(
                    size=6,
                    opacity=0.75,
                    color=_station_color(station_name),
                ),
                hovertemplate=(
                    "관측소: %{fullData.name}<br>"
                    "풍속: %{x:.2f} m/s<br>"
                    "파고: %{y:.2f} m<extra></extra>"
                ),
            )
        )

    if not outlier_df.empty:
        fig.add_trace(
            go.Scatter(
                x=outlier_df["wind_speed"],
                y=outlier_df["wave_height"],
                mode="markers",
                name="이상치",
                marker=dict(
                    size=8,
                    color="#EF9F27",
                    line=dict(color="#854F0B", width=1.5),
                    symbol="diamond",
                ),
                hovertemplate=(
                    "구분: 이상치<br>"
                    "풍속: %{x:.2f} m/s<br>"
                    "파고: %{y:.2f} m<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        title="풍속 × 파고 상관관계",
        xaxis_title="풍속(m/s)",
        yaxis_title="파고(m)",
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig


def build_all_charts(
    df: pd.DataFrame, quality_df: pd.DataFrame
) -> dict[str, go.Figure]:
    """리포트 출력 순서대로 차트 4개를 묶어 반환한다."""
    return {
        "관측소별 데이터 가용률 및 품질 등급": chart_quality_grade(quality_df),
        "날짜별 관측소 결측률 히트맵": chart_missing_heatmap(df),
        "일별 평균 풍속 추이 (관측소별)": chart_daily_wind_speed(df),
        "풍속 × 파고 상관관계": chart_wind_wave_scatter(df),
    }
